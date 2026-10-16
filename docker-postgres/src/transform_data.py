import os
from pathlib import Path
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))

TABLE_RULES = {

    "clientes": {

        "fillna": {
            "nombre_y_apellido": "CLIENTE SIN NOMBRE"
        }

    },

    "venta": {

        "dropna": [
            "precio",
            "cantidad"
        ]

    }

}

# "pattern" en vez de "file": permite que aparezcan archivos nuevos con
# sufijo de fecha (ej. "Venta_2026-08-01.csv"), no solo el nombre original.
FILES = {
    "clientes": {
        "pattern": "Clientes*.csv",
        "kwargs": {"sep": ";"}
    },
    "venta": {
        "pattern": "Venta*.csv",
        "kwargs": {}
    },
    "productos": {
        "pattern": "Productos*.csv",
        "kwargs": {}
    },
    "sucursales": {
        "pattern": "Sucursales*.csv",
        "kwargs": {"sep": ";"}
    },
    "calendario": {
        "pattern": "Calendario*.csv",
        "kwargs": {}
    },
    "canaldeventa": {
        "pattern": "CanalDeVenta*.csv",
        "kwargs": {}
    }
}


def apply_rules(df, table):

    rules = TABLE_RULES.get(table)

    if not rules:
        return df

    if "fillna" in rules:

        for col, value in rules["fillna"].items():

            df[col] = df[col].fillna(value)

    if "dropna" in rules:

        df = df.dropna(subset=rules["dropna"])

    return df


def transform_dataframe(df, table_name):

    # nombres de columnas
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
    )

    # comas decimales
    for col in ["x", "y"]:

        if col in df.columns:

            df[col] = (
                df[col]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
            )

            df[col] = pd.to_numeric(df[col])

    # reglas específicas
    df = apply_rules(df, table_name)

    return df


def load_csv_files(table_name, pattern, **kwargs):
    """Busca TODOS los archivos que matcheen el patrón (puede ser uno
    solo, como en la carga inicial, o varios si hay más de un archivo
    incremental pendiente), los transforma, y los concatena en un único
    DataFrame. Devuelve también las rutas originales, para que
    load_data.py sepa qué archivos archivar después de cargarlos con éxito.
    """
    archivos_encontrados = sorted(DATA_DIR.glob(pattern))

    if not archivos_encontrados:
        return None, []

    dfs = []
    for csv_path in archivos_encontrados:
        df = pd.read_csv(csv_path, **kwargs)
        df = transform_dataframe(df, table_name)
        dfs.append(df)
        print(f"  {csv_path.name}: {len(df)} filas")

    df_combinado = pd.concat(dfs, ignore_index=True)
    return df_combinado, archivos_encontrados


def get_dataframes():
    """Devuelve, para cada tabla, el DataFrame ya transformado (o None si
    no hay ningún archivo nuevo pendiente para esa tabla) junto con la
    lista de archivos crudos que lo generaron -- necesarios para que
    load_data.py los archive después de una carga exitosa."""
    resultado = {}

    for table_name, config in FILES.items():
        print(f"Buscando archivos para '{table_name}' ({config['pattern']})")

        df, source_files = load_csv_files(
            table_name=table_name,
            pattern=config["pattern"],
            **config["kwargs"]
        )

        if df is None:
            print(f"  sin archivos pendientes para '{table_name}'")
            continue

        resultado[table_name] = {
            "df": df,
            "source_files": source_files,
        }

    return resultado