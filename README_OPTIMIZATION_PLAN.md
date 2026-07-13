# DibsDataSourceCSV Optimization Plan

## Ziel

Dieser Plan beschreibt konkrete Verbesserungen fuer `DibsDataSourceCSV`. Die
fachlichen Simulationsergebnisse und der bestehende zustandsbasierte
`DataSource`-Vertrag sollen erhalten bleiben.

Nach jeder Optimierung muessen Unit-Tests, ein realer `DIBS.multi()`-Lauf und
der Vergleich aller Summary-Felder ausgefuehrt werden.

## Gemessene Baseline

Input:

```text
SimulationData_Breitenerhebung.csv
9 Gebaeude
din18599 | mid | sia2024 | 2004-2018 | GEG
```

| Phase | Laufzeit |
|---|---:|
| `DataSourceCSV(...)` | 1,772 s |
| 9 Gebaeude lesen und mappen | 0,017 s |
| Primaerenergie- und Emissionsfaktoren | 0,005 s |
| EPW-Auswahl fuer 9 Gebaeude | 0,494 s |
| Wetter lesen und mappen | 3,409 s |
| Zeitplaene lesen und mappen | 1,984 s |

Die neun Gebaeude verwendeten drei unterschiedliche EPW-Dateien.

## Wichtige Einordnung

Die folgenden vier Referenztabellen werden im Konstruktor einmal pro
`DataSourceCSV`-Instanz geladen und danach als Attribute wiederverwendet:

- `occupancy_schedules_assignments`
- `vergleichswerte_zuweisung`
- `tek_nwg_comparative_values`
- `profiles_zuweisungen_data`

Innerhalb eines einzelnen `DIBS.multi()`-Laufs werden sie nicht pro Gebaeude
erneut von der Festplatte gelesen. Ein prozessweiter Cache hilft deshalb nur,
wenn im selben Prozess mehrere `DataSourceCSV`-Instanzen erzeugt werden.

## P1: HK-/UK-Paar korrekt aufloesen

### Problem

`hk_and_uk_in_zuweisungen()` prueft HK und UK unabhaengig. `find_row()` filtert
anschliessend nur nach UK. Dadurch kann eine Kombination akzeptiert werden,
obwohl HK und UK nicht in derselben Tabellenzeile stehen.

### Umsetzung

1. Eine gemeinsame Funktion fuer die Paarauflosung einfuehren.
2. Gleichzeitig nach `hk_geb` und `uk_geb` filtern.
3. Genau eine gefundene Zeile verlangen.
4. Bei null oder mehreren Treffern eine typisierte DataSource-Exception
   ausloesen.
5. `get_schedule()`, `get_tek()`, `get_usage_time()` und `get_gains()` auf die
   gemeinsame Aufloesung umstellen.

### Effekt

- verhindert falsche Norm-, Schedule- und TEK-Zuordnungen;
- entfernt doppelte Suchlogik;
- verbessert die fachliche Nachvollziehbarkeit.

### Risiko

Mittel: Bisher unbemerkte mehrdeutige oder inkonsistente Referenzdaten werden
anschliessend als Fehler sichtbar.

### Status

Umgesetzt. Die HK-/UK-Aufloesung filtert jetzt immer auf das exakte Paar `(hk_geb, uk_geb)` und akzeptiert genau eine Zeile.

Geaendert:

- `src/dibs_datasource_csv/utils/utils_hkgeb.py`
- `src/dibs_datasource_csv/datasource_csv.py`
- `tests/test_error_handling_contract.py`

Abgesicherte Faelle:

- HK und UK existieren getrennt, aber nicht als Paar: typed error;
- doppeltes HK-/UK-Paar: `DIBSInputError` mit `matches` im Kontext;
- `get_schedule()`, `get_tek()`, `get_usage_time()` und `get_gains()` verwenden dieselbe zentrale Paaraufloesung.

## P2: Golden-Test fuer CSV-Mapping einfuehren

### Problem

Die vorhandenen Tests pruefen den Fehlervertrag, aber nicht das reale Mapping
von CSV-Zeilen zu `Building`-Objekten.

### Umsetzung

1. Eine kleine feste CSV-Fixture mit mindestens zwei Gebaeuden anlegen.
2. Ausgewaehlte `Building`-Attribute exakt pruefen.
3. HK-/UK-, PLZ- und Dezimalwert-Mapping abdecken.
4. Einen realen Integrationstest mit `DIBS.multi()` ergaenzen.
5. Summary-Ergebnisse als versionierten Snapshot vergleichen.

### Effekt

Die folgenden Refactorings koennen sicher umgesetzt werden, ohne stille
fachliche Aenderungen zu riskieren.

### Risiko

Niedrig.

### Status

Umgesetzt als manuelles Golden-Regression-Skript:

```text
scripts/regression_csv_golden.py
scripts/README_GOLDEN_REGRESSION.md
```

Das Skript nutzt `DataSourceCSV` aus diesem Repository und `DIBS.multi()` aus dem lokalen `DibsComputingCore`-Repository. Standardmaessig wird geprueft, dass `DibsComputingCore` auf Branch `dibscc_error_handling` steht.

Es vergleicht:

- alle `SummaryResult`-Felder fuer 9 Gebaeude;
- ausgewaehlte Stundenwerte fuer dieselben 9 Gebaeude.

## P3: Wetterdaten pro EPW-Datei cachen

### Problem

Eine EPW-Datei wird fuer jedes Gebaeude erneut gelesen und in etwa 8760
`WeatherData`-Objekte umgewandelt. In der Baseline wurden neun Ladevorgaenge
ausgefuehrt, obwohl nur drei EPW-Dateien vorkamen.

### Umsetzung

1. Cache-Key aus `weather_period` und `epw_file.file_name` bilden.
2. Gemappte Wetterdaten als unveraenderliche Sequenz speichern.
3. Nur vollstaendig geladene Daten in den Cache schreiben.
4. Cache-Groesse begrenzen oder eine explizite Clear-Funktion anbieten.
5. Sicherstellen, dass die Simulation Wetterobjekte nicht mutiert.

### Erwarteter Effekt

Bei der gemessenen Datei koennen sechs von neun EPW-Ladevorgaengen entfallen.
Das theoretische Einsparpotenzial liegt in der Groessenordnung von etwa zwei
Sekunden fuer die DataSource-Phasen.

### Risiko

Mittel: Das Teilen mutierbarer Wetterobjekte zwischen Simulationen muss
ausgeschlossen werden.

### Status

Umgesetzt als Instanz-Cache in `DataSourceCSV`.

Cache-Key:

```text
(weather_period, epw_file.file_name)
```

Verhalten:

- erster Zugriff: Wetterdatei lesen und in `WeatherData`-Objekte mappen;
- weiterer Zugriff mit gleichem Key: gecachte Objekte verwenden;
- anderer Wetterzeitraum oder andere EPW-Datei: neuer Cache-Miss;
- intern wird ein Tuple gespeichert, zurueckgegeben wird eine neue Liste.

Geaendert:

- `src/dibs_datasource_csv/datasource_csv.py`
- `tests/test_weather_cache.py`

## P4: Zeitplaene nach Schedule-Name cachen

### Problem

Schedule-Dateien werden fuer jedes Gebaeude erneut gelesen und in
`ScheduleName`-Objekte umgewandelt.

### Umsetzung

1. `schedule_name` als Cache-Key verwenden.
2. Zeitplanobjekte und Personensumme gemeinsam cachen.
3. Nur unveraenderliche Daten teilen.
4. Cache-Hit und Cache-Miss in Tests abdecken.

### Erwarteter Effekt

Reduktion der gemessenen Zeitplanphase von insgesamt etwa 1,98 Sekunden,
abhaengig von der Zahl unterschiedlicher Schedule-Dateien.

### Risiko

Niedrig bis mittel.

### Status

Umgesetzt als Instanz-Cache in `DataSourceCSV`.

Cache-Key:

```text
schedule_name
```

Verhalten:

- erster Zugriff: Schedule-Datei lesen und `ScheduleName`-Objekte bauen;
- weiterer Zugriff mit gleichem Schedule-Namen: gecachte Objekte verwenden;
- anderer Schedule-Name: neuer Cache-Miss;
- intern wird ein Tuple gespeichert, zurueckgegeben wird eine neue Liste.

Geaendert:

- `src/dibs_datasource_csv/datasource_csv.py`
- `tests/test_schedule_cache.py`

## P5: EPW-Auswahl pro PLZ und Wetterperiode cachen

### Problem

`get_epw_file()` liest PLZ- und Stationsdaten fuer jedes Gebaeude erneut und
berechnet die Entfernung zu allen Stationen ueber `DataFrame.apply()` und
`geopy.geodesic`.

### Umsetzung

1. PLZ-Tabelle einmal indexieren.
2. Stationsdaten je Wetterperiode wiederverwenden.
3. Cache-Key `(weather_period, plz)` verwenden.
4. Naechste Station in einem Durchlauf bestimmen.
5. Optional die Distanzberechnung vektorisieren.

### Erwarteter Effekt

Die gemessenen 0,49 Sekunden fuer neun Gebaeude koennen bei wiederkehrenden
PLZ deutlich reduziert werden.

### Risiko

Mittel: Die bisherige Stationsauswahl muss bitgenau oder innerhalb einer klaren
Distanz-Toleranz erhalten bleiben.

### Status

Umgesetzt als Instanz-Cache in `DataSourceCSV`.

Caches:

```text
_plz_codes_data
_weather_stations_cache[weather_period]
_epw_file_cache[(weather_period, plz)]
```

Verhalten:

- PLZ-Tabelle wird pro `DataSourceCSV`-Instanz nur einmal gelesen;
- Stationsdaten werden pro Wetterperiode nur einmal gelesen;
- fertige EPW-Auswahl wird pro `(weather_period, plz)` gecacht;
- bei Cache-Hit wird ein neues `EPWFile` aus den gecachten Werten gebaut;
- Stationsdaten werden vor Distanzberechnung kopiert, damit der Cache nicht durch gebaeudespezifische Spalten veraendert wird.

Geaendert:

- `src/dibs_datasource_csv/datasource_csv.py`
- `src/dibs_datasource_csv/utils/utils_epwfile.py`
- `tests/test_epw_file_cache.py`
- `tests/test_epw_utils.py`

Zusaetzliche Utility-Optimierung:

- `calculate_minimum_distance_to_next_weather_station()` nutzt weiterhin `geopy.geodesic`, aber ohne `DataFrame.apply(axis=1)`.
- Der Index der naechsten Station wird pro Stations-DataFrame einmal berechnet und in `DataFrame.attrs` wiederverwendet.
- `get_filename_with_minimum_distance()`, `get_coordinates_station()` und `get_distance()` teilen sich damit dieselbe `idxmin()`-Bestimmung.
- Die Distanzformel wurde nicht geaendert, damit die EPW-Auswahl stabil bleibt.

## P6: Positional Building-Mapping absichern

### Problem

Das Mapping verwendet `Building(*row.values)` und haengt damit vollstaendig von
der CSV-Spaltenreihenfolge ab.

### Umsetzung

1. Erwartete Spalten zentral definieren.
2. Fehlende, zusaetzliche und doppelte Spalten validieren.
3. Mapping-Reihenfolge explizit herstellen.
4. Fehlermeldung mit fehlenden Spalten und Zeilennummer ausgeben.
5. Erst spaeter optional auf benannte DTOs umstellen.

### Effekt

Verhindert stille Fehlzuordnungen bei geaenderten CSV-Dateien.

### Risiko

Mittel: Bestehende Dateien mit unerwarteten Zusatzspalten koennen erstmals
abgelehnt werden.

### Status

Umgesetzt. Die erwartete Spaltenliste wird direkt aus `Building.__init__` abgeleitet und vor dem Mapping validiert.

Verhalten:

- fehlende Spalten werden als `DIBSInputError` gemeldet;
- zusaetzliche Spalten werden als `DIBSInputError` gemeldet;
- doppelte Spalten werden als `DIBSInputError` gemeldet;
- die Zuordnung zu `Building` erfolgt explizit nach der erwarteten Spaltenreihenfolge, nicht nach der zufaelligen DataFrame-Reihenfolge.

Geaendert:

- `src/dibs_datasource_csv/datasource_csv.py`
- `tests/test_building_column_mapping.py`

## P7: Datei-, Parser- und PLZ-Fehler vereinheitlichen

### Problem

Mehrere Fehler verlassen die DataSource derzeit als rohe Exceptions, unter
anderem `FileNotFoundError`, `UnicodeDecodeError`, `ParserError`, `KeyError`
oder `IndexError` bei unbekannter PLZ.

### Umsetzung

1. Erwartete I/O- und Parserfehler an der DataSource-Grenze abfangen.
2. Mit `raise ... from error` in `DIBSDataSourceError` uebersetzen.
3. Unbekannte PLZ als `PLZNotFoundError` melden.
4. `phase`, Dateityp und fachlichen Schluessel in `context` aufnehmen.
5. Keine absoluten Dateipfade an API-Nutzer weitergeben.
6. Programmierfehler weiterhin unveraendert propagieren.

### Risiko

Niedrig, sofern nur erwartete externe Fehler uebersetzt werden.

### Status

Umgesetzt. Erwartete externe Datei-, Parser- und PLZ-Fehler werden jetzt in DIBS-typisierte Fehler uebersetzt.

Verhalten:

- CSV-/EPW-I/O-Fehler werden zu `DIBSDataSourceError`;
- Parser- und Encoding-Fehler werden zu `DIBSDataSourceError`;
- unbekannte PLZ wird zu `PLZNotFoundError`;
- Error-Kontext enthaelt nur sichere Informationen wie `file_type`, `file_name`, `error_type`, `weather_period` oder `plz`;
- absolute Pfade werden nicht in den Kontext uebernommen;
- unerwartete Programmierfehler werden nicht breit abgefangen.

Geaendert:

- `src/dibs_datasource_csv/utils/utils_readcsv.py`
- `src/dibs_datasource_csv/utils/utils_epwfile.py`
- `tests/test_datasource_error_translation.py`

## P8: Input-Optionen frueh validieren

### Problem

Ungueltige Gain-Gruppen koennen in den `match`-Bloecken still `None` liefern.
Ein ungueltiger Wetterzeitraum wird in Teilen der EPW-Auswahl implizit wie
`2004-2018` behandelt.

### Umsetzung

Beim Erzeugen der DataSource folgende Werte validieren:

- `profile_from_norm`
- `gains_from_group_values`
- `usage_from_norm`
- `weather_period`
- `primary_energy_factor`

Ungueltige Werte als `DIBSInputError` mit Feldname und Wert melden.

### Risiko

Niedrig.

### Status

Umgesetzt. `DataSourceCSV.__init__()` validiert die oeffentlichen Optionen jetzt vor dem Laden der Referenzdaten.

Erlaubte Werte:

```text
profile_from_norm: din18599, sia2024, mza
gains_from_group_values: low, mid, max
usage_from_norm: din18599, sia2024, mza
weather_period: 2004-2018, 2007-2021
primary_energy_factor: GEG, EPBD2020, EPBD2030
```

Verhalten:

- ungueltige Optionen werfen `DIBSInputError` mit `phase="datasource.init"`;
- der Kontext enthaelt `field`, `value` und `allowed_values`;
- bei ungueltigen Optionen werden keine Referenzdateien geladen.

Geaendert:

- `src/dibs_datasource_csv/datasource_csv.py`
- `tests/test_datasource_options.py`

## P9: CSV-Leselogik vereinfachen

### Problem

`read_user_building()` und `read_user_buildings()` enthalten dieselbe Logik.
Die numerische Konvertierung verwendet ein nacktes `except`.

### Umsetzung

1. Eine gemeinsame Lesefunktion einfuehren.
2. Fuer das Einzelgebaeude `nrows=1` verwenden.
3. Numerische Spalten gezielt oder ueber ein Schema konvertieren.
4. Keine unbekannten Exceptions verschlucken.
5. Rueckgabetypen von optional auf tatsaechliches Verhalten korrigieren.

### Risiko

Mittel: Pandas-Dtype-Aenderungen koennen Konstruktorwerte beeinflussen und
muessen ueber Golden-Tests abgesichert werden.

### Status

Umgesetzt. `read_user_building()` und `read_user_buildings()` verwenden jetzt dieselbe interne Lesefunktion.

Verhalten:

- `read_user_building()` liest mit `nrows=1` nur das erste Gebaeude;
- `read_user_buildings()` liest alle Gebaeude;
- CSV-Parameter und Fehleruebersetzung laufen ueber dieselbe Funktion;
- numerische Konvertierung faengt nur erwartete `TypeError`/`ValueError` ab;
- unerwartete Programmierfehler werden nicht mehr durch ein nacktes `except` verschluckt;
- Rueckgabetypen sind jetzt `pd.DataFrame` statt optional.

Geaendert:

- `src/dibs_datasource_csv/utils/utils_readcsv.py`
- `tests/test_user_building_csv_reader.py`

## P10: Struktur und Packaging bereinigen

### Umsetzung

1. Nicht verwendetes `location_utils.py` pruefen und gegebenenfalls entfernen.
2. Globale `sys.path`-Manipulation aus `utils_hkgeb.py` entfernen.
3. Doppelte `find_row()`-Implementierungen zusammenfuehren.
4. Docstrings und Rueckgabetypen an den zustandsbasierten Core-Vertrag
   anpassen.
5. Alte `dist/`-Artefakte nicht versionieren.
6. Abhaengigkeiten auf Tags oder Commit-SHAs statt bewegliche Branches pinnen.
7. Black- und Testpruefung in CI ausfuehren.

### Risiko

Niedrig, wenn historische Importpfade beruecksichtigt werden.

### Status

Teilweise umgesetzt und fuer PyPI vorbereitet.

Umgesetzt:

- ungenutztes `src/dibs_datasource_csv/utils/location_utils.py` entfernt;
- globale `sys.path`-Manipulation aus `utils_hkgeb.py` entfernt;
- ungenutzte doppelte `find_row()`-Helper aus `utils_schedule.py` und `utils_normreader.py` entfernt;
- `.gitignore` fuer Python-Cache, Build-Artefakte, lokale Regressionsergebnisse, virtuelle Umgebungen und IDE-Dateien angelegt;
- P10-Status im Optimierungsplan dokumentiert.

Bewusst noch nicht automatisch geaendert:

- `pyproject.toml` enthaelt noch Branch-Dependencies auf `dibscc_error_handling` und `dd101copy`.
- Fuer einen echten PyPI-Release sollten diese Abhaengigkeiten auf veroeffentlichte Versionen, Tags oder stabile Commit-SHAs umgestellt werden.
- Ich habe hier keine Versionsnummern erfunden, damit der Release nicht gegen falsche oder nicht veroeffentlichte Artefakte zeigt.

Geaendert:

- `.gitignore`
- `src/dibs_datasource_csv/utils/utils_hkgeb.py`
- `src/dibs_datasource_csv/utils/utils_schedule.py`
- `src/dibs_datasource_csv/utils/utils_normreader.py`
- `README_OPTIMIZATION_PLAN.md`
- entfernt: `src/dibs_datasource_csv/utils/location_utils.py`

## Verbindliches Pruefverfahren

Nach jedem Schritt:

1. Unit-Tests ausfuehren.
2. Syntax und Formatierung pruefen.
3. `SimulationData_Breitenerhebung.csv` ueber `DIBS.multi()` simulieren.
4. Alle Gebaeude-IDs und Summary-Felder vergleichen.
5. Numerische Ergebnisse mit definierter Toleranz vergleichen.
6. Laufzeit mindestens zehnmal unter gleichen Bedingungen messen.
7. Nur Optimierungen behalten, die Ergebnisse erhalten und einen messbaren
   Vorteil oder eine klare Korrektheitsverbesserung liefern.

## Empfohlene Reihenfolge

```text
P1  HK-/UK-Paar korrigieren
P2  Golden-Tests aufbauen
P3  Wetter-Cache
P4  Schedule-Cache
P5  EPW-Auswahl-Cache
P6  Building-Mapping absichern
P7  I/O- und PLZ-Fehlervertrag
P8  Optionen validieren
P9  CSV-Leselogik vereinfachen
P10 Struktur und Packaging bereinigen
```
