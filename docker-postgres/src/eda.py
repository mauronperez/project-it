import os
from pathlib import Path
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))

FILES = {
    "Clientes": ("Clientes.csv", {"sep": ";"}),
    "Venta": ("Venta.csv", {}),
    "Productos": ("Productos.csv", {}),
    "Sucursal": ("Sucursales.csv", {"sep": ";"}),
    "Calendario": ("Calendario.csv", {}),
    "CanalVenta": ("CanalDeVenta.csv", {})
}

def analyze_dataframe(df, name):

    print("=" * 60)
    print(name.upper())
    print("=" * 60)

    print(f"Filas    : {len(df)}")
    print(f"Columnas : {len(df.columns)}")

    print("\nValores nulos")

    nulls = df.isnull().sum()

    if nulls.sum() == 0:

        print("✔ No se encontraron nulos")

    else:

        for columna, cantidad in nulls.items():

            if cantidad > 0:

                print(f" - {columna}: {cantidad}")

    print("\nDuplicados")

    id_col = df.columns[0]

    duplicados = df[id_col].duplicated().sum()

    print(f"{id_col}: {duplicados}")

    print("\nResumen numérico")

    print(df.describe())

def run_eda():

    for nombre, (archivo, kwargs) in FILES.items():

        df = pd.read_csv(DATA_DIR / archivo, **kwargs)

        analyze_dataframe(df, nombre)

if __name__ == "__main__":
    run_eda()