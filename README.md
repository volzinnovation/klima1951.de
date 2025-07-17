# klima1915.de - Open Source Browser für DWD HYRAS Daten

Der Deutsche Wetterdienst (DWD) stellt [HYRAS-Datensätze bereit – hydrometeorologische Rasterdaten](https://www.dwd.de/DE/leistungen/hyras/hyras.html), die folgende Messwerte tagesgenau enthalten:

- Temperatur (Minimum, Maximum, Mittelwert)
- Niederschlag
- Luftfeuchte

Diese Werte gibt es für jeden Tag seit dem **1. Januar 1951**, *flächendeckend für ganz Deutschland*.

Die HYRAS-Daten liegen im Format NetCDF-4 vor. Die Python Programme im Verzeichnis [etl](https://github.com/volzinnovation/klima1951.de/tree/main/etl) transformieren diese Daten in Orts-bezogene JSON Dateien.
Die Ortsauswahl wird über [misc/cities.json](https://github.com/volzinnovation/klima1951.de/blob/main/misc/cities.json) gesteuert, diese kann über eine Excel-Tabelle der deutschen Städte und Gemeinden und deren Koordinaten und Einwohnerzahl neu generiert werden.

Das Verzeichnis frontend wird auf [https://klima1951.de/](https://klima1951.de/) gehostet.

Die Daten werden täglich aktualisiert, dies erledigt der Workflow [daily.yml](https://github.com/volzinnovation/klima1951.de/blob/main/.github/workflows/daily.yml).

[Mehr zur Motivation auf meinem Blog.](https://www.volz-fw.de/p/es-ist-sommer)

--

Vibe Coded im Juni/Juli 2025
