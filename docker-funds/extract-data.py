"""
Extract + Load: lee los standings del Mundial 2022 desde el archivo local
data-wc-2022.json e inserta en la tabla "standings" de tu Postgres
(el que levantaste con docker-compose).


Correr con:
    python extract.py

Requisito: tu contenedor de Postgres debe estar corriendo
(docker compose up -d) antes de ejecutar este script, y el archivo
data-wc-2022.json debe estar en la misma carpeta.
"""

import json
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data-wc-2022.json")

# Mismas variables que usa tu docker-compose.yml (archivo .env)
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def extract_standings(json_path: str) -> list[dict]:
    """Lee el JSON y devuelve una lista de filas: pais, puntos, mundial, grupo."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if data.get("errors"):
        raise RuntimeError(f"El JSON contiene errores: {data['errors']}")

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
    print(f"Leyendo datos de {JSON_PATH}...")
    rows = extract_standings(JSON_PATH)
    print(f"Se extrajeron {len(rows)} filas.")

    print("Insertando en Postgres...")
    load_to_postgres(rows)
    print("¡Listo! Datos insertados en la tabla 'standings'.")