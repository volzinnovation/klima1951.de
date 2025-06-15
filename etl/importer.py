# importer.py
# Dieses Skript lädt Wetterdaten vom DWD, verarbeitet sie und fügt sie in eine PostGIS-DB ein.

import os
import requests
import xarray as xr
import psycopg2
import psycopg2.extras
import pandas as pd
from pyproj import Proj, transform
import logging
from pathlib import Path
from tqdm import tqdm

# --- Konfiguration ---
# Passen Sie diese Werte an Ihre Umgebung an.
DB_CONFIG = {
    "dbname": "wetter_db",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": "5432"
}

# Verzeichnis zum Speichern der heruntergeladenen netCDF-Dateien
DOWNLOAD_DIR = Path("./dwd_data")

# Definieren Sie den zu importierenden Zeitraum. Für einen vollständigen Import: range(1951, datetime.now().year)
YEAR_RANGE = range(2020, 2024) # Beispiel: Nur die Jahre 2020-2023 importieren

# DWD-Server-Basis-URL und Parameter-Definitionen
DWD_BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/raw/{param}/"
PARAMS_TO_IMPORT = {
    "tas": "air_temperature_mean",      # tas
    "tasmax": "air_temperature_max",    # tasmax
    "tasmin": "air_temperature_min",    # tasmin
    "pr": "precipitation",              # pr
    "hurs": "relative_humidity",        # hurs
    "rsds": "global_radiation"          # rad_global
}

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Hauptfunktionen ---

def setup_database_connection():
    """Stellt die Verbindung zur PostgreSQL-Datenbank her."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("Erfolgreich mit der Datenbank verbunden.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Fehler bei der Datenbankverbindung: {e}")
        return None

def download_file(url, target_path):
    """Lädt eine Datei herunter und zeigt einen Fortschrittsbalken an."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(target_path, 'wb') as f, tqdm(
        desc=target_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)
    logging.info(f"Datei heruntergeladen: {target_path}")

def setup_grid_coordinates(conn):
    """
    Liest Gitterkoordinaten aus einer Beispieldatei, transformiert sie nach WGS84
    und speichert sie in der 'grid_coordinates'-Tabelle.
    Dies muss nur einmal ausgeführt werden.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM grid_coordinates")
    if cursor.fetchone()[0] > 0:
        logging.info("Tabelle 'grid_coordinates' ist bereits befüllt. Überspringe Setup.")
        return

    logging.info("Richte 'grid_coordinates' ein. Dies kann einige Minuten dauern...")
    
    # Lade eine beliebige Datei als Referenz für das Gitter
    param_folder = list(PARAMS_TO_IMPORT.values())[0]
    year = list(YEAR_RANGE)[0]
    file_name = f"hyras_de-daily-raw_{param_folder}_{year}.nc"
    url = DWD_BASE_URL.format(param=param_folder) + file_name
    
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    ref_file_path = DOWNLOAD_DIR / file_name
    if not ref_file_path.exists():
        download_file(url, ref_file_path)

    ds = xr.open_dataset(ref_file_path)
    
    # ETRS89-LAEA (EPSG:3035) und WGS84 (EPSG:4326) Projektionen
    in_proj = Proj('epsg:3035')
    out_proj = Proj('epsg:4326')

    x_coords, y_coords = ds['x'].values, ds['y'].values
    grid_data = []

    logging.info("Transformiere Koordinaten von EPSG:3035 nach EPSG:4326...")
    for y_idx, y in enumerate(tqdm(y_coords, desc="Y-Koordinaten")):
        for x_idx, x in enumerate(x_coords):
            lon, lat = transform(in_proj, out_proj, x, y, always_xy=True)
            grid_data.append((x_idx, y_idx, lon, lat, f'SRID=4326;POINT({lon} {lat})'))
    
    logging.info(f"Füge {len(grid_data)} Koordinatenpunkte in die Datenbank ein...")
    psycopg2.extras.execute_values(
        cursor,
        "INSERT INTO grid_coordinates (x_coord, y_coord, longitude, latitude, geom) VALUES %s",
        grid_data
    )
    conn.commit()
    cursor.close()
    logging.info("Einrichtung der 'grid_coordinates' abgeschlossen.")


def process_and_import_year(conn, year):
    """Lädt alle Parameter für ein bestimmtes Jahr und importiert sie."""
    logging.info(f"--- Beginne Verarbeitung für das Jahr {year} ---")
    
    yearly_datasets = {}
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    # 1. Alle Dateien für das Jahr herunterladen und laden
    for param_short, param_folder in PARAMS_TO_IMPORT.items():
        file_name = f"hyras_de-daily-raw_{param_folder}_{year}.nc"
        url = DWD_BASE_URL.format(param=param_folder) + file_name
        file_path = DOWNLOAD_DIR / file_name
        
        try:
            if not file_path.exists():
                logging.info(f"Lade {file_name} herunter...")
                download_file(url, file_path)
            
            logging.info(f"Öffne {file_name} mit xarray...")
            ds = xr.open_dataset(file_path)
            yearly_datasets[param_short] = ds[param_short]
        except Exception as e:
            logging.error(f"Konnte Datei für {param_short} im Jahr {year} nicht verarbeiten: {e}")
            return

    # 2. Daten für den Import vorbereiten
    logging.info(f"Bereite Daten für den Import vor (Jahr: {year})...")
    
    time_values = yearly_datasets['tas'].time.values
    x_len = len(yearly_datasets['tas'].x)
    y_len = len(yearly_datasets['tas'].y)
    
    all_data_for_import = []
    
    # Iteriere über jeden Tag des Jahres
    for t_idx, timestamp in enumerate(tqdm(time_values, desc=f"Verarbeite Tage für {year}")):
        date = pd.to_datetime(timestamp).date()
        daily_data = []
        # Iteriere über jede Zelle des Rasters
        for y_idx in range(y_len):
            for x_idx in range(x_len):
                row = [date, x_idx, y_idx]
                for param_short in PARAMS_TO_IMPORT.keys():
                    # xarray gibt einen numpy-Typ zurück, in Python-Typ konvertieren
                    value = yearly_datasets[param_short].values[t_idx, y_idx, x_idx]
                    # -999 ist der Füllwert für fehlende Daten
                    row.append(float(value) if value != -999 else None)
                daily_data.append(tuple(row))
        all_data_for_import.extend(daily_data)
        
    # 3. In Datenbank importieren
    logging.info(f"Importiere {len(all_data_for_import)} Datensätze für {year} in die Datenbank...")
    cursor = conn.cursor()
    
    # Verwende ON CONFLICT, um Duplikate zu ignorieren, falls das Skript erneut läuft
    query = """
        INSERT INTO weather_data (data_date, x_coord, y_coord, tas, tasmax, tasmin, pr, hurs, rsds)
        VALUES %s
        ON CONFLICT (data_date, x_coord, y_coord) DO NOTHING
    """
    
    psycopg2.extras.execute_values(
        cursor, query, all_data_for_import, page_size=1000
    )
    conn.commit()
    cursor.close()
    
    # Datasets schließen, um Speicher freizugeben
    for ds in yearly_datasets.values():
        ds.close()
        
    logging.info(f"--- Verarbeitung für das Jahr {year} abgeschlossen ---")


if __name__ == "__main__":
    conn = setup_database_connection()
    if conn:
        # Einmaliges Setup der Koordinatentabelle
        setup_grid_coordinates(conn)
        
        # Jährlichen Datenimport durchführen
        for year in YEAR_RANGE:
            process_and_import_year(conn, year)
            
        conn.close()
        logging.info("Alle Importvorgänge abgeschlossen.")
