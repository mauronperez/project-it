import csv
import random
from datetime import date, timedelta
from pathlib import Path
import os


DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))


def generate_sales(
    num_rows=100,
    start_id=60000,
    output_file="Venta_incremental.csv"
):
    DATA_DIR.mkdir(exist_ok=True)

    output_path = DATA_DIR / output_file

    today = date.today()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "IdVenta",
            "Fecha",
            "Fecha_Entrega",
            "IdCanal",
            "IdCliente",
            "IdSucursal",
            "IdEmpleado",
            "IdProducto",
            "Precio",
            "Cantidad"
        ])

        for i in range(num_rows):

            fecha = today - timedelta(days=random.randint(0, 30))
            fecha_entrega = fecha + timedelta(days=random.randint(1, 7))

            writer.writerow([
                start_id + i,
                fecha.isoformat(),
                fecha_entrega.isoformat(),
                random.randint(1, 3),        # IdCanal
                random.randint(1, 500),      # IdCliente
                random.randint(1, 20),       # IdSucursal
                random.randint(1, 50),       # IdEmpleado
                random.randint(1, 200),      # IdProducto
                round(random.uniform(5, 500), 2),
                random.randint(1, 10)
            ])

    print(f"Generadas {num_rows} ventas en {output_path}")


if __name__ == "__main__":
    generate_sales()