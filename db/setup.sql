-- SQL-Skript zur Einrichtung der PostGIS-Datenbank für Wetterdaten

-- HINWEIS: Führen Sie dieses Skript als Superuser oder als Benutzer mit den
-- entsprechenden Rechten zum Erstellen von Erweiterungen und Tabellen aus.

-- 1. Aktivieren Sie die PostGIS-Erweiterung (falls noch nicht geschehen)
-- Dies fügt Unterstützung für geografische Objekte, Abfragen und Analysen hinzu.
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Erstellen Sie eine Tabelle zur Speicherung der Gitterkoordinaten
-- Diese Tabelle enthält die Referenz für jeden Punkt im 1x1 km Raster.
-- Sie wird einmal vom Importer-Skript befüllt.
CREATE TABLE IF NOT EXISTS grid_coordinates (
    x_coord INT NOT NULL, -- X-Index aus der netCDF-Datei
    y_coord INT NOT NULL, -- Y-Index aus der netCDF-Datei
    longitude DOUBLE PRECISION NOT NULL, -- Geografische Länge (WGS84)
    latitude DOUBLE PRECISION NOT NULL,  -- Geografische Breite (WGS84)
    
    -- Geometrie-Spalte zur Speicherung des Punktes im WGS84-Format (EPSG:4326)
    geom GEOMETRY(Point, 4326), 

    PRIMARY KEY (x_coord, y_coord)
);

-- Erstellen Sie einen räumlichen Index für die Geometrie-Spalte, um die
-- Suche nach dem nächstgelegenen Punkt extrem zu beschleunigen.
CREATE INDEX IF NOT EXISTS idx_grid_coordinates_geom ON grid_coordinates USING GIST (geom);


-- 3. Erstellen Sie die Haupttabelle für die täglichen Wetterdaten
-- Diese Tabelle wird die riesige Menge an Zeitreihendaten enthalten.
CREATE TABLE IF NOT EXISTS weather_data (
    -- Zeitstempel des Datensatzes
    data_date DATE NOT NULL,
    -- Fremdschlüssel zu den Gitterkoordinaten
    x_coord INT NOT NULL,
    y_coord INT NOT NULL,

    -- Die eigentlichen Wetterparameter.
    -- Verwendung von REAL (4-Byte-Fließkommazahl) ist für diese Daten ausreichend und spart Speicherplatz.
    tas REAL,     -- Durchschnittliche Lufttemperatur
    tasmax REAL,  -- Maximale Lufttemperatur
    tasmin REAL,  -- Minimale Lufttemperatur
    pr REAL,      -- Niederschlag
    hurs REAL,    -- Luftfeuchtigkeit
    rsds REAL,    -- Globale Sonneneinstrahlung

    -- Zusammengesetzter Primärschlüssel, um die Eindeutigkeit für jeden Punkt und Tag zu gewährleisten.
    PRIMARY KEY (data_date, x_coord, y_coord)
);

-- Erstellen Sie einen Index für das Datum, da die meisten Abfragen nach Zeiträumen filtern werden.
CREATE INDEX IF NOT EXISTS idx_weather_data_date ON weather_data (data_date);

-- Erstellen Sie einen Index für die Koordinaten, um Abfragen für einen bestimmten Ort zu beschleunigen.
CREATE INDEX IF NOT EXISTS idx_weather_data_coords ON weather_data (x_coord, y_coord);

-- Optional: Geben Sie dem Benutzer, der die API ausführt, die erforderlichen Berechtigungen.
-- Ersetzen Sie 'your_api_user' durch den tatsächlichen Benutzernamen.
-- GRANT SELECT ON grid_coordinates TO your_api_user;
-- GRANT SELECT ON weather_data TO your_api_user;
