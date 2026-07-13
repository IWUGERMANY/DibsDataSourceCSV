# DataSourceCSV Golden Regression

Dieses Skript prueft `DibsDataSourceCSV` mit der realen Datei:

```text
C:\Users\wail\Desktop\Projects\Stand dibs\SimulationData_Breitenerhebung.csv
```

Es nutzt `DataSourceCSV` aus diesem Repository und `DIBS.multi()` aus dem lokalen Schwester-Repository:

```text
C:\Users\wail\Desktop\Projects\Stand dibs\DibsComputingCore
```

Standardmaessig erwartet das Skript, dass `DibsComputingCore` auf Branch `dibscc_error_handling` steht. Der Branch wird direkt aus `.git/HEAD` gelesen, nicht per `git`-Befehl.

## Golden-Dateien erstellen oder bewusst aktualisieren

Vom Root-Verzeichnis `DibsDataSourceCSV` aus:

```powershell
python scripts\regression_csv_golden.py --update-golden
```

Das schreibt:

```text
tests\golden\datasourcecsv_summary_9_buildings.csv
tests\golden\datasourcecsv_hourly_sample_9_buildings.csv
```

Nur ausfuehren, wenn die aktuellen Ergebnisse fachlich korrekt sind und als neue Referenz gelten sollen.

## Nach jeder Optimierung vergleichen

```powershell
python scripts\regression_csv_golden.py
```

Erwartung:

```text
differences=0
summary_differences=0 hourly_differences=0
```

Das Skript schreibt zusaetzlich:

```text
regression_results\datasourcecsv_9_buildings_comparison.xlsx
```

Die Excel-Datei enthaelt:

- `Metadata`: Anzahl Gebaeude, Felder, Differenzen und Laufzeit;
- `Current`: aktuelle SummaryResult-Werte;
- `Diff`: nur abweichende Summary-Felder;
- `HourlyCurrent`: aktuelle ausgewaehlte Stundenwerte;
- `HourlyDiff`: nur abweichende Stundenwerte.

## Cache-Wirkung messen

Nach Cache-Optimierungen kannst du Cold-Run und Warm-Run direkt vergleichen:

```powershell
python scripts\regression_csv_golden.py --benchmark-cache
```

Das Skript verwendet dabei dieselbe `DataSourceCSV`-Instanz zweimal:

```text
Run 1: Cold, Cache wird aufgebaut
Run 2: Warm, Weather/Schedule/EPW-Auswahl koennen aus dem Cache kommen
```

Beispielausgabe:

```text
cache_benchmark cold_wall_time_s=4.120000 warm_wall_time_s=2.950000 delta_s=1.170000 speedup=1.397
cache_benchmark differences=0 summary_differences=0 hourly_differences=0
```

Wichtig:

- `differences=0` bedeutet: Cold- und Warm-Ergebnisse sind fachlich gleich.
- `delta_s` zeigt, wie viel Laufzeit der Warm-Run gegenueber dem Cold-Run spart.
- Die Datei `regression_results\datasourcecsv_cache_benchmark.xlsx` enthaelt Cold/Warm-Sheets und Diff-Sheets.
- Das ist kein Ersatz fuer den Golden-Vergleich, sondern eine Zusatzmessung fuer Cache-Effekte.
## Branch-Pruefung

Wenn der Core-Branch falsch ist, bricht das Skript ab:

```text
core_branch_expected=dibscc_error_handling
core_branch_current=<anderer-branch>
```

Nur wenn du bewusst gegen einen anderen Core testen willst:

```powershell
python scripts\regression_csv_golden.py --skip-core-branch-check
```

## Exit Codes

- `0`: Vergleich erfolgreich, keine Unterschiede.
- `1`: Unterschiede gefunden.
- `2`: Golden-Datei fehlt.
- `3`: `DibsComputingCore` steht nicht auf dem erwarteten Branch.

## Warum dieses Skript existiert

Die Unit-Tests pruefen einzelne Fehler- und Mapping-Vertraege. Dieses Skript prueft den realen End-to-End-Pfad:

```text
SimulationData_Breitenerhebung.csv
-> DataSourceCSV
-> DIBS.multi()
-> SummaryResult + ausgewaehlte Stundenwerte
-> Golden-Vergleich
```

Damit koennen Optimierungen in `DibsDataSourceCSV` sicher umgesetzt werden, ohne stille fachliche Aenderungen in den Simulationsergebnissen zu riskieren.
