# klima1915.de - Open Source Browser für DWD HYRAS Daten

Der Deutsche Wetterdienst (DWD) stellt HYRAS-Datensätze bereit – hydrometeorologische Rasterdaten, die u.a. folgende Werte tagesgenau enthalten:

- Temperatur (Minimum, Maximum, Mittelwert)
- Niederschlag
- Luftfeuchte

Diese Werte gibt es für jeden Tag seit dem 1. Januar 1951, flächendeckend für ganz Deutschland.

Die HYRAS-Daten liegen im Format NetCDF-4 vor. Die Python Programme im Verzeichnis [https://github.com/volzinnovation/klima1951.de/tree/main/etl](etl) transformieren diese Daten in Orts-bezogene JSON Dateien.
Die Ortsauswahl wird über misc/cities.json gesteuert. 

Das Verzeichnis frontend wird auf [https://klima1951.de/](https://klima1951.de/) gehostet.

Die Daten werden täglich aktualisiert, dies erledigt der Workflow daily.yml.
