# main.py
# FastAPI-Backend für die Wetterdaten-Anwendung.

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from typing import List, Optional
from datetime import date
import logging
import uvicorn
from contextlib import asynccontextmanager
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# --- Konfiguration ---
DB_CONFIG = {
    "database": "wetter_db",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}
DATABASE_POOL = None

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Lifespan-Manager für Datenbankverbindung ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verwaltet den Datenbank-Connection-Pool während der Lebensdauer der App."""
    global DATABASE_POOL
    logging.info("Erstelle Datenbank-Connection-Pool...")
    try:
        DATABASE_POOL = await asyncpg.create_pool(**DB_CONFIG)
        yield
    finally:
        if DATABASE_POOL:
            logging.info("Schließe Datenbank-Connection-Pool...")
            await DATABASE_POOL.close()
            
app = FastAPI(lifespan=lifespan, title="Wetterdaten API")

# CORS-Middleware, damit Ihr Frontend auf die API zugreifen kann
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Für die Entwicklung, in Produktion einschränken!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API-Endpunkte ---

@app.get("/api/geocode")
async def geocode_location(q: str = Query(..., min_length=2)):
    """
    Konvertiert einen Ortsnamen in geografische Koordinaten (Längen- und Breitengrad).
    """
    logging.info(f"Geokodierungsanfrage für: {q}")
    geolocator = Nominatim(user_agent="wetter_app_v1")
    try:
        location = geolocator.geocode(q, country_codes="DE")
        if location:
            return {"location": q, "latitude": location.latitude, "longitude": location.longitude}
        else:
            raise HTTPException(status_code=404, detail="Ort nicht gefunden")
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        raise HTTPException(status_code=503, detail=f"Geokodierungsdienst nicht verfügbar: {e}")


@app.get("/api/weather")
async def get_weather_data(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    params: List[str] = Query(..., alias="params"),
    aggregation: str = Query("daily", enum=["daily", "weekly", "monthly", "yearly"])
):
    """
    Holt Wetterdaten für einen gegebenen Standort und Zeitraum.
    """
    if not DATABASE_POOL:
        raise HTTPException(status_code=503, detail="Datenbankverbindung nicht verfügbar")
        
    async with DATABASE_POOL.acquire() as conn:
        try:
            # 1. Nächstgelegene Gitterzelle finden
            # ST_SetSRID erstellt einen Punkt, ST_Distance findet den Abstand
            nearest_point_query = """
                SELECT x_coord, y_coord FROM grid_coordinates
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)
                LIMIT 1;
            """
            nearest = await conn.fetchrow(nearest_point_query, lon, lat)
            if not nearest:
                raise HTTPException(status_code=404, detail="Keine Wetterdaten für diesen Standort gefunden.")
            
            x_coord, y_coord = nearest['x_coord'], nearest['y_coord']
            
            # 2. Query basierend auf der Aggregation zusammenbauen
            # `to_char` formatiert das Datum für die Gruppierung
            # `date_trunc` schneidet das Datum auf die gewünschte Ebene ab
            if aggregation == 'daily':
                group_by_clause = "data_date"
                select_date_clause = "data_date as date"
            else:
                group_by_clause = f"date_trunc('{aggregation}', data_date)"
                select_date_clause = f"{group_by_clause} as date"
            
            # Dynamisches Erstellen der AVG/SUM/MAX/MIN-Klauseln für die ausgewählten Parameter
            select_params_clause = []
            for p in params:
                if p == 'pr':
                    select_params_clause.append(f"SUM({p}) as {p}") # Niederschlag wird summiert
                elif p == 'tasmax':
                    select_params_clause.append(f"MAX({p}) as {p}")
                elif p == 'tasmin':
                    select_params_clause.append(f"MIN({p}) as {p}")
                else: # tas, hurs, rsds
                    select_params_clause.append(f"AVG({p}) as {p}")

            weather_query = f"""
                SELECT
                    {select_date_clause},
                    {', '.join(select_params_clause)}
                FROM weather_data
                WHERE x_coord = $1 AND y_coord = $2
                  AND data_date BETWEEN $3 AND $4
                GROUP BY {group_by_clause}
                ORDER BY date;
            """
            
            results = await conn.fetch(weather_query, x_coord, y_coord, from_date, to_date)
            
            # Ergebnisse in ein sauberes JSON-Format umwandeln
            return [{key: (value.isoformat() if isinstance(value, date) else (round(value, 2) if isinstance(value, float) else value)) for key, value in record.items()} for record in results]

        except Exception as e:
            logging.error(f"Fehler bei der Wetterdatenabfrage: {e}")
            raise HTTPException(status_code=500, detail="Interner Serverfehler bei der Datenabfrage.")


if __name__ == "__main__":
    # Startet den Server. Ideal für die lokale Entwicklung.
    # In Produktion sollten Sie einen Prozessmanager wie Gunicorn oder Uvicorn direkt verwenden.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)