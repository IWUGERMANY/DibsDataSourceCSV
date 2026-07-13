# DataSourceCSV Split Plan

## Ziel

`datasource_csv.py` soll als schlanke Fassade erhalten bleiben, weil `DibsComputingCore` gegen die `DataSource`-Schnittstelle arbeitet. Die fachlichen Teilaufgaben sollen aber in kleinere Module ausgelagert werden, damit Mapping, Weather, Profiles, TEK und Faktoren separat wartbar und testbar sind.

Die oeffentliche API bleibt stabil:

```python
DataSourceCSV(...)
get_user_building()
get_user_buildings()
get_epw_pe_factors()
get_schedule()
get_tek()
choose_and_get_the_right_weather_data_from_path()
get_epw_file()
get_usage_time()
get_gains()
```

## Aktuelle Verantwortlichkeiten in datasource_csv.py

- Konstruktor-Optionen validieren
- Building-CSV-Spalten validieren und zu `Building` mappen
- statische Assignment-Tabellen laden
- Primary-Energy-/Emission-Faktoren mappen
- HK-/UK-Paare aufloesen
- Schedule-Dateien laden und cachen
- TEK-Zuordnung und TEK-DHW-Wert lesen
- EPW-Datei anhand PLZ und Wetterperiode aufloesen
- WeatherData aus EPW-Datei laden und cachen
- Usage-Time und Gains aus Normprofilen lesen

## Zielstruktur

```text
src/dibs_datasource_csv/
  datasource_csv.py              # Fassade / DataSource-Interface
  datasource_options.py          # erlaubte Konstruktoroptionen + Validierung
  building_mapper.py             # Building-Spaltenvalidierung und Building-Erzeugung
  providers/
    __init__.py
    factor_provider.py           # PrimaryEnergyAndEmissionFactor Mapping
    profile_provider.py          # HK/UK, Schedule, Usage-Time, Gains
    tek_provider.py              # TEK-Auswahl und DHW-Wert
    weather_provider.py          # EPW-Auswahl, PLZ, WeatherData-Cache
  utils/
    ...                          # reine CSV-/Norm-/EPW-Helfer
```

## S1: Optionsvalidierung auslagern - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/datasource_options.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- `ALLOWED_DATASOURCE_OPTIONS` verschieben.
- `_validate_datasource_options()` verschieben.
- `DataSourceCSV.__init__()` importiert und nutzt die Funktion.

Warum zuerst:

- Sehr kleiner Schnitt.
- Keine Abhaengigkeit zu Building, Weather oder Normprofilen.
- Risiko niedrig.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_datasource_options.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
```

Status:

- DONE: `datasource_options.py` erstellt.
- DONE: `ALLOWED_DATASOURCE_OPTIONS` und `validate_datasource_options()` ausgelagert.
- DONE: `DataSourceCSV.__init__()` delegiert an `validate_datasource_options()`.

## S2: Building-Mapping auslagern - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/building_mapper.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- `EXPECTED_BUILDING_COLUMNS` verschieben.
- `_duplicate_columns()` verschieben.
- `_prepare_building_dataframe()` verschieben.
- `_build_building_from_row()` verschieben.
- `get_user_building()` und `get_user_buildings()` nutzen den neuen Mapper.

Warum:

- Building-Mapping ist eigenstaendig.
- Die Logik ist sicherheitsrelevant, weil Spaltenreihenfolge und fehlende Spalten sonst falsche Building-Objekte erzeugen koennen.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_building_column_mapping.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
```

Status:

- DONE: `building_mapper.py` erstellt.
- DONE: `EXPECTED_BUILDING_COLUMNS`, Spaltenvalidierung und `Building`-Erzeugung ausgelagert.
- DONE: `DataSourceCSV.get_user_building()` und `get_user_buildings()` delegieren an den Mapper.
- DONE: Kompatibilitaet fuer Tests/Monkeypatching erhalten: `build_building_from_row(..., building_class=Building)`.

## S3: FactorProvider extrahieren - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/providers/factor_provider.py`
- Neu falls noetig: `src/dibs_datasource_csv/providers/__init__.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- Mapping `primary_energy_factor -> CSV-Spalte` aus `get_epw_pe_factors()` auslagern.
- Erzeugung von `PrimaryEnergyAndEmissionFactor` auslagern.
- `DataSourceCSV.get_epw_pe_factors()` bleibt als Interface-Methode und ruft Provider auf.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_factor_provider.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
```

Status:

- DONE: `providers/` und `providers/__init__.py` erstellt.
- DONE: `providers/factor_provider.py` erstellt.
- DONE: Mapping `primary_energy_factor -> CSV-Spalte` ausgelagert.
- DONE: Erzeugung von `PrimaryEnergyAndEmissionFactor` ausgelagert.
- DONE: `DataSourceCSV.get_epw_pe_factors()` delegiert an den Provider.
- DONE: `tests/test_factor_provider.py` ergaenzt.

## S4: TekProvider extrahieren - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/providers/tek_provider.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- `get_tek()`-Logik in Provider verschieben.
- Provider bekommt `vergleichswerte_zuweisung`, `tek_nwg_comparative_values` und die aktuelle HK/UK-Information.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_tekreader.py
python -m pytest -q -p no:cacheprovider tests/test_tek_provider.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
```

Status:

- DONE: `providers/tek_provider.py` erstellt.
- DONE: TEK-HK/UK-Zuordnung in den Provider verschoben.
- DONE: TEK-Kategorie und DHW-Wert-Ermittlung in den Provider delegiert.
- DONE: `DataSourceCSV.get_tek()` delegiert an `load_tek(...)`.
- DONE: `tests/test_tek_provider.py` ergaenzt.

## S5: ProfileProvider extrahieren - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/providers/profile_provider.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- `_resolve_hk_uk_row()` verschieben oder als Helper in Provider integrieren.
- `get_schedule()` verschieben.
- `get_usage_time()` verschieben.
- `get_gains()` verschieben.
- `_schedule_cache` in den Provider verschieben.

Wichtig:

- `DataSourceCSV.get_schedule()` bleibt bestehen und delegiert nur.
- Rueckgabeformat bleibt exakt gleich.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_schedule_cache.py
python -m pytest -q -p no:cacheprovider tests/test_profile_provider.py
python -m pytest -q -p no:cacheprovider tests/test_normreader_gains_group.py
python -m pytest -q -p no:cacheprovider tests/test_error_handling_contract.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
```

Status:

- DONE: `providers/profile_provider.py` erstellt.
- DONE: HK-/UK-Aufloesung als `resolve_hk_uk_row()` ausgelagert.
- DONE: `get_schedule()`, `get_usage_time()` und `get_gains()` in `ProfileProvider` verschoben.
- DONE: Schedule-Cache wird vom Provider gehalten und durch `DataSourceCSV` weiterverwendet.
- DONE: `DataSourceCSV` bleibt als Fassade kompatibel und delegiert nur.
- DONE: `tests/test_profile_provider.py` ergaenzt.


## S6: WeatherProvider extrahieren - DONE

Dateien:

- Neu: `src/dibs_datasource_csv/providers/weather_provider.py`
- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- `get_epw_file()`-Logik verschieben.
- `choose_and_get_the_right_weather_data_from_path()`-Logik verschieben.
- Caches verschieben:
  - `_weather_data_cache`
  - `_epw_file_cache`
  - `_weather_stations_cache`
  - `_plz_codes_data`

Warum:

- Weather/EPW/PLZ ist eigener Bereich und war der groesste Cache-Block.
- Nach Entfernen der fremden Cache-Resets kann dieser Provider sauber alleine arbeiten.

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests/test_epw_file_cache.py
python -m pytest -q -p no:cacheprovider tests/test_weather_cache.py
python -m pytest -q -p no:cacheprovider tests/test_weather_provider.py
python -m pytest -q -p no:cacheprovider tests/test_datasource_error_translation.py
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
python scripts/regression_csv_golden.py --benchmark-cache
```

Status:

- DONE: `providers/weather_provider.py` erstellt.
- DONE: `choose_and_get_the_right_weather_data_from_path()` in `WeatherProvider.choose_weather_data_from_path()` verschoben.
- DONE: `get_epw_file()` in `WeatherProvider.get_epw_file()` verschoben.
- DONE: WeatherData-, EPW-Datei-, Wetterstations- und PLZ-Caches werden vom Provider gehalten.
- DONE: `DataSourceCSV` bleibt als Fassade kompatibel und delegiert nur.
- DONE: Bestehende Monkeypatch-Tests bleiben kompatibel, weil `DataSourceCSV` die bisherigen Reader/Helper als Dependencies weiterreicht.
- DONE: `tests/test_weather_provider.py` ergaenzt.


## S7: DataSourceCSV final aufraeumen - DONE

Dateien:

- Aendern: `src/dibs_datasource_csv/datasource_csv.py`

Was passiert:

- unbenutzte Imports entfernen.
- Docstrings aktualisieren.
- Konstruktor klar strukturieren:
  - Optionen setzen
  - statische Tabellen laden
  - Provider initialisieren
  - Interface-Methoden delegieren

Zielbild:

```python
class DataSourceCSV(DataSource):
    def get_schedule(self):
        return self.profile_provider.get_schedule(self.building)

    def get_epw_file(self):
        self.epw_file = self.weather_provider.get_epw_file(self.building)
```

Tests danach:

```powershell
python -m pytest -q -p no:cacheprovider tests
python scripts/regression_csv_golden.py
python scripts/regression_csv_golden.py --benchmark-cache
```

Status:

- DONE: Konstruktor in klare Initialisierungsschritte aufgeteilt: Optionen, Result-State, statische Tabellen, Provider.
- DONE: `profile_provider` und `weather_provider` als explizite Provider-Attribute ergaenzt.
- DONE: Private `_get_*_provider()`-Fallbacks fuer Tests mit `DataSourceCSV.__new__()` erhalten.
- DONE: alte Re-Export-Kompatibilitaet fuer `EXPECTED_BUILDING_COLUMNS` bewusst erhalten.
- DONE: Docstrings in `datasource_csv.py` auf Fassaden-Verantwortung gekuerzt.
- DONE: Fachlogik bleibt in Mappern/Providern, `DataSourceCSV` delegiert nur noch.


## Nicht-Ziele

- Keine Aenderung der `DataSource`-Schnittstelle aus `DibsComputingCore`.
- Keine Aenderung der CSV-Dateiformate.
- Keine Aenderung der Golden-Ergebnisse.
- Keine Parallelisierung.
- Kein globaler Prozesscache.
- Keine PyPI-Versionierung in diesem Split.

## Akzeptanzkriterien

Nach jedem Schritt gilt:

- Unit Tests gruen.
- Golden Regression `differences=0`.
- Keine Veraenderung der oeffentlichen `DataSourceCSV`-Methoden.
- `datasource_csv.py` wird kleiner und enthaelt weniger Fachlogik.
- Provider haben klare Verantwortung und keine gegenseitigen Cache-Seiteneffekte.
