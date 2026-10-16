# Pipeline ETL con Python y PostgreSQL (Docker)

Proyecto de práctica: extrae datos de ficheros CSV, los transforma con pandas y los carga en una base de datos PostgreSQL. Todo corre en contenedores con Docker Compose, así que se levanta igual en cualquier máquina.

## Qué hace

1. **Extract**: lee los CSV de la carpeta `data/` (Calendario, CanalDeVenta, Clientes, Productos, Sucursales y Venta).
2. **Transform**: limpia y estandariza los datos con pandas (`transform_data.py`).
3. **Load**: carga los DataFrames en PostgreSQL con SQLAlchemy.
4. **Carga incremental**: un generador de ventas ficticias crea nuevos registros para simular la llegada de datos nuevos y probar que solo se cargan los que faltan.

```
 data/*.csv ──► transform_data.py ──► script de carga ──► PostgreSQL
                  (pandas)             (SQLAlchemy)         (contenedor db)
                       ▲
        generador de ventas ficticias (para la carga incremental)
```



## Estructura del proyecto

```
.
├── docker-compose.yml     # servicios: db (PostgreSQL) y src (Python)
├── .env                   # credenciales (no se versiona)
├── src/
│   ├── Dockerfile         # imagen de Python 3.13
│   ├── requirements.txt   # dependencias
│   ├── eda.py             # análisis exploratorio de los CSV
│   ├── transform_data.py  # limpieza y transformación
│   └── <script_de_carga>.py        # TODO: nombre de tu script de carga
├── data/                  # CSV de origen (y data/processed/ tras la carga)
├── queries/               # consultas SQL
└── postgres/data/         # datos de PostgreSQL (no se versiona)
```



## Puesta en marcha

1. Crea un fichero `.env` en la raíz con las credenciales de la base de datos:

```bash
cat > .env <<'EOF'
POSTGRES_USER=postgres
POSTGRES_PASSWORD=cambia_esta_clave
POSTGRES_DB=cambiar_esta_clave
EOF
```

1. Levanta los contenedores:

```bash
docker compose up -d --build
```

El servicio `src` espera a que PostgreSQL esté listo (healthcheck) antes de arrancar.

## Cómo ejecutarlo

Los scripts se lanzan dentro del contenedor `src`, que se mantiene encendido:

```bash
# 1. Exploración de los datos
docker compose exec src python eda.py

# 2. ETL: transformar y cargar en PostgreSQL
docker compose exec src python main.py        # TODO: nombre real

# 3. Generar ventas ficticias para probar la carga incremental
docker compose exec src python generate_sales.py    # TODO: nombre real


```



## Comprobar el resultado

```bash
# Tablas creadas
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'

# Filas en una tabla (cambia el nombre)
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from venta"'
```

También puedes conectarte con un cliente como DBeaver usando `localhost`, puerto `5432` y las credenciales del `.env`.

## Empezar desde cero

Para borrar todo y repetir la demostración limpia:

```bash
# 1. Parar y eliminar los contenedores y la red
docker compose down

# 2. Borrar los datos de PostgreSQL
rm -rf postgres/data

# 3. Dejar los CSV en su estado inicial
mv data/processed/* data/ 2>/dev/null

# 4. Volver a levantar
docker compose up -d --build
```

