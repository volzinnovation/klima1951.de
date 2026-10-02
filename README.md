# klima1951.de - Web-Frontend für DWD HYRAS Wetterdaten

Der Deutsche Wetterdienst (DWD) veröffentlicht [HYRAS-Datensätze – hydrometeorologische Rasterdaten](https://www.dwd.de/DE/leistungen/hyras/hyras.html), die folgende Messwerte tagesgenau enthalten:

- Temperatur (Minimum, Maximum, Mittelwert)
- Niederschlag
- Luftfeuchte

Diese Werte gibt es für jeden Tag seit dem **1. Januar 1951**, *flächendeckend für ganz Deutschland*.

Die HYRAS-Daten liegen im Format NetCDF-4 vor. Die Python Programme im Verzeichnis [etl](https://github.com/volzinnovation/klima1951.de/tree/main/etl) transformieren diese Daten in Orts-bezogene JSON Dateien.
Die Ortsauswahl wird über [misc/cities.json](https://github.com/volzinnovation/klima1951.de/blob/main/misc/cities.json) gesteuert, diese kann über eine Excel-Tabelle der deutschen Städte und Gemeinden und deren Koordinaten und Einwohnerzahl neu generiert werden.

Das Verzeichnis frontend wird auf [https://klima1951.de/](https://klima1951.de/) gehostet.
Der öffentliche Datenstatus ist unter [https://klima1951.de/status.html](https://klima1951.de/status.html) verfügbar.

Die Daten werden täglich aktualisiert, dies erledigt der Workflow [daily.yml](https://github.com/volzinnovation/klima1951.de/blob/main/.github/workflows/daily.yml).

Die Veröffentlichung des Frontends übernimmt [static.yml](https://github.com/volzinnovation/klima1951.de/blob/main/.github/workflows/static.yml).
Sie läuft bei Pushes auf `main`, auf manuelle Anforderung und nach einem
erfolgreichen täglichen oder manuell gestarteten ETL-Lauf auf `main` im selben
Repository. Der Abschluss-Trigger ist nötig, weil Pushes mit `GITHUB_TOKEN`
keinen weiteren Push-Workflow auslösen. Dabei wird der Stand des Default-Branches
zum Abschluss des ETL-Laufs veröffentlicht, einschließlich des neuen Daten-Commits.
Der `head_sha` des ETL-Laufs wäre dafür zu alt, da er den Stand vor dem ETL-Commit bezeichnet.

Nach einer Veröffentlichung lässt sich `generated_at_utc` in
[data-status.json](https://klima1951.de/data-status.json) mit dem veröffentlichten
Commit unter `frontend/data-status.json` vergleichen. Ein erfolgreicher ETL-Lauf
allein bestätigt noch nicht, dass der neue Status öffentlich erreichbar ist.

## Lokaler Datenstatus

Der aktuelle Stand der lokalen HYRAS-Dateien und der generierten Orts-JSONs kann
ohne ETL-Neulauf geprueft werden:

```bash
python etl/data_status.py
python etl/data_status.py --format json
python etl/data_status.py --format json --public > frontend/data-status.json
python etl/data_status.py --format json --public --require-fresh > frontend/data-status.json
```

Der Bericht zaehlt konfigurierte Orte, vorhandene `all-years.json`- und
`stats.csv`-Dateien, den Statistik-Jahresbereich und die vorhandenen NetCDF-
Quellen je Messgroesse. Die Frischepruefung erwartet, dass alle Stadt-
Statistiken und alle HYRAS-Metriken mindestens bis zum letzten vollstaendig
abgeschlossenen Kalenderjahr reichen. In den ersten 45 Tagen eines neuen Jahres
gilt noch eine Schonfrist, damit der Jahreswechsel nicht faelschlich als
Pipeline-Fehler gemeldet wird.

[Mehr zur Motivation auf meinem Blog.](https://www.volz-fw.de/p/es-ist-sommer)

--

Vibe Coded im Juni/Juli 2025
