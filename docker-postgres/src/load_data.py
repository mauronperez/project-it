import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from transform_data import get_dataframes, DATA_DIR
import os

DB_CONFIG = {
    'host': 'db',
    'port': 5432,
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

PROCESSED_DIR = DATA_DIR / "processed"


def archive_source_files(source_files):
    """Mueve los archivos crudos ya cargados a data/processed/, con un
    timestamp agregado al nombre -- así no se vuelven a procesar en la
    próxima corrida, y queda un registro histórico de cuándo se cargó
    cada archivo."""
    PROCESSED_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for archivo in source_files:
        destino = PROCESSED_DIR / f"{archivo.stem}_{timestamp}{archivo.suffix}"
        shutil.move(str(archivo), str(destino))
        print(f"  archivado: {destino.relative_to(DATA_DIR.parent)}")


def load_data():

    engine = create_engine(
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

    dataframes = get_dataframes()

    if not dataframes:
        print("No hay archivos nuevos pendientes de cargar.")
        engine.dispose()
        return

    for table_name, info in dataframes.items():

        df = info["df"]
        source_files = info["source_files"]

        print(f"Cargando {table_name} ({len(df)} filas)")

        df.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False
        )

        print(f"{table_name} cargada")

        # Solo se archiva SI el to_sql anterior no tiro excepcion --
        # si algo falla, el archivo crudo se queda en data/ para
        # reintentarlo en la proxima corrida, en vez de perderse.
        print(source_files)
        print(type(source_files))
        archive_source_files(source_files)

    engine.dispose()
