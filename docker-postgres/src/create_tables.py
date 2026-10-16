import psycopg2
from pathlib import Path
import os

DB_CONFIG = {
    'host': 'db',
    'port': 5432,
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

SQL_SCRIPTS = [
    '01_create_calendario.sql',
    '02_create_canal_venta.sql', 
    '03_create_clientes.sql',
    '04_create_productos.sql',
    '05_create_sucursales.sql',
    '06_create_venta.sql'
]

def create_tables():
    """Ejecuta todos los scripts SQL para crear las tablas"""
    ddl_dir = Path(__file__).parent / 'queries' / 'DDL'
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    
    for script_name in SQL_SCRIPTS:
        script_path = ddl_dir / script_name
        print(f"Ejecutando: {script_name}")
        
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
            
        cursor = conn.cursor()
        cursor.execute(sql_content)
        cursor.close()
        print(f"{script_name} completado")
    
    conn.close()
    print("Todas las tablas creadas")

if __name__ == "__main__":
    create_tables()