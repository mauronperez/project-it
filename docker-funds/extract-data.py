"""
Extract + Load: trae standings del Mundial 2022 desde API-Football
e inserta en la tabla "standings" de tu Postgres (el que levantaste
con docker-compose).


Correr con:
    python extract-data.py

Requisito: tu contenedor de Postgres debe estar corriendo
(docker compose up -d) antes de ejecutar este script.
"""

import requests
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
LEAGUE_ID = 1        # 1 = World Cup
SEASON = 2022    

API_URL = "https://v3.football.api-sports.io/standings"

# Mismos datos que en tu docker-compose.yml
PG_CONFIG = {
    "host": "localhost",     
    "port": 5432,
    "dbname": "wc_standings",
    "user": "db_user",
    "password": "db_password",
}


def extract_standings(league_id: int, season: int) -> list[dict]:
    """Pega a la API y devuelve una lista de filas: pais, puntos, mundial, grupo."""
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"league": league_id, "season": season}

    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("errors"):
        raise RuntimeError(f"La API devolvió errores: {data['errors']}")

    rows = []
    for standings_response in data["response"]:
        league = standings_response["league"]
        for group in league["standings"]:
            for team_row in group:
                rows.append({
                    "pais": team_row["team"]["name"],
                    "puntos": team_row["points"],
                    "mundial": league["season"],
                    "grupo": team_row["group"],
                })
    return rows


def load_to_postgres(rows: list[dict]) -> None:
    """Crea la tabla si no existe, e inserta las filas extraídas."""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS standings (
            id       SERIAL PRIMARY KEY,
            pais     VARCHAR(100) NOT NULL,
            puntos   INTEGER NOT NULL,
            mundial  INTEGER NOT NULL,
            grupo    VARCHAR(20)
        );
    """)

    for row in rows:
        cur.execute("""
            INSERT INTO standings (pais, puntos, mundial, grupo)
            VALUES (%(pais)s, %(puntos)s, %(mundial)s, %(grupo)s)
        """, row)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    print("Extrayendo datos de la API...")
    rows = extract_standings(LEAGUE_ID, SEASON)
    print(f"Se extrajeron {len(rows)} filas.")

    print("Insertando en Postgres...")
    load_to_postgres(rows)
    print("¡Listo! Datos insertados en la tabla 'standings'.")
