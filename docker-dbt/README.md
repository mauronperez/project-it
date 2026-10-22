# Guía paso a paso: dbt + DuckDB + Docker + Streamlit

Pipeline de analítica con datos reales de crímenes de Chicago (2026). 

## Qué vamos a construir

```
CSV (Chicago Data Portal)
        │  carga (Python + DuckDB)
        ▼
  tabla raw: chicago_crimes          ← fuente (source)
        │  dbt
        ▼
  silver_crimes (vista)              ← limpieza y renombrado
  silver_crimes_type (vista)         ← catálogo de tipos de delito
        │  dbt
        ▼
  gold_crimes_by_month_type (tabla)  ← agregados para analizar
  gold_crimes_by_district (tabla)
        │
        ├──► dbt docs  (documentación y linaje)
        └──► Streamlit (dashboard)
```

**DuckDB no necesita servidor.** La base de datos es un único fichero (`data/chicago_crimes.db`) que se abre desde Python o dbt.

## 1. Estructura del proyecto

Crea la carpeta y las subcarpetas:

```bash
mkdir -p docker-dbt && cd docker-dbt
mkdir -p data/raw scripts streamlit_app
mkdir -p chicago_crimes/models/silver chicago_crimes/models/gold
```

Resultado:

```
docker-dbt/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── data/
│   └── raw/                 # aquí va el CSV descargado
├── scripts/
│   └── load_raw.py          # carga el CSV en DuckDB
├── streamlit_app/
│   └── app.py               # dashboard
└── chicago_crimes/          # proyecto dbt
    ├── dbt_project.yml
    ├── profiles.yml
    └── models/
        ├── sources.yml
        ├── silver/
        └── gold/
```



## 2. Entorno Docker



### `requirements.txt`

```
requests>=2.28
dbt-core==1.6.1
dbt-duckdb==1.6.0
duckdb==0.9.0
pandas==2.1.1
numpy==1.26.4
streamlit
```



### `Dockerfile`

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt jupyterlab

CMD ["bash"]
```



### `docker-compose.yml`

Dos servicios con la misma imagen: `dbt` (para trabajar) y `streamlit` (dashboard siempre disponible).

```yaml
services:
  dbt:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace/chicago_crimes
    environment:
      DBT_PROFILES_DIR: /workspace/chicago_crimes
    ports:
      - "8888:8888"   # Jupyter
      - "8080:8080"   # dbt docs
    stdin_open: true
    tty: true

  streamlit:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace/streamlit_app
    ports:
      - "8501:8501"
    command: streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```



### `.gitignore`

```
*.db
*.db.wal
target/
logs/
dbt_packages/
.venv/
.env
```



## 3. Arrancar y verificar el entorno

```bash
docker compose up -d --build
docker compose ps
```

Comprueba las versiones instaladas:

```bash
docker compose exec dbt dbt --version
docker compose exec dbt pip check
```

Deberías ver `dbt-core 1.6.1` y el plugin `duckdb 1.6.0`. `pip check` debe responder `No broken requirements found.`

> Si `pip check` avisa de conflictos entre `streamlit` y `dbt-core` (por ejemplo, con `protobuf`), la salida limpia es darle a Streamlit su propia imagen con sus propios requisitos.



## 4. Datos: descarga y carga en DuckDB



### 4.1 Descargar el CSV

Dataset: *Crimes - 2026*, del Chicago Data Portal (`f6bk-yv3r`). Es una vista del dataset "Crimes 2001 to Present", se actualiza a diario y tiene unas 155.000 filas.

Desde tu terminal, en la carpeta `docker-dbt`:

```bash
curl -L -o data/raw/crimes_2026.csv \
  'https://data.cityofchicago.org/api/views/f6bk-yv3r/rows.csv?accessType=DOWNLOAD'
```

> Las columnas de este CSV tienen espacios y mayúsculas (`Case Number`, `Primary Type`...). Los modelos de esta guía asumen esos nombres. Si descargas con otro endpoint y vienen en `snake_case`, hay que ajustar el `silver_crimes`.



### 4.2 Cargar el CSV en DuckDB

```python
import duckdb

CSV = "data/raw/chicago_crimes_2026.csv"

with duckdb.connect("data/chicago_crimes.db") as con:
    con.sql(f"""
        create or replace table chicago_crimes as
        select *
        from read_csv_auto('{CSV}', header = true)
    """)
    con.sql("select * as filas from chicago_crimes").show()
```



## 5. Proyecto dbt

Todos los ficheros van dentro de `chicago_crimes/`.

### `dbt_project.yml`

```yaml
name: 'chicago_crimes'
version: '1.0.0'
config-version: 2
profile: 'chicago_crimes'

model-paths: ["models"]
clean-targets: ["target", "dbt_packages"]

models:
  chicago_crimes:
    silver:
      +materialized: view
    gold:
      +materialized: table
```

Convención: **silver = vistas** (solo guardan la consulta), **gold = tablas** (guardan el resultado calculado).

### `profiles.yml`

```yaml
chicago_crimes:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '../data/chicago_crimes.db'
```

La clave de primer nivel debe coincidir exactamente con `profile:` del `dbt_project.yml`. La ruta es relativa a `chicago_crimes/`.

### `models/sources.yml`

Declara la tabla cruda que dbt **no** crea, solo lee:

```yaml
version: 2

sources:
  - name: raw
    schema: main
    tables:
      - name: chicago_crimes
        description: "Crímenes de Chicago 2026 cargados desde el CSV original."
        columns:
          - name: ID
            quote: true
            tests:
              - unique
              - not_null
```



### `models/silver/silver_crimes.sql`

Renombra a `snake_case` y se queda con las columnas útiles:

```sql
select
    "ID"                    as crime_id,
    "Case Number"           as case_number,
    "Date"                  as occurred_at,
    "Block"                 as block,
    "IUCR"                  as iucr,
    "Primary Type"          as primary_type,
    "Description"           as description,
    "Location Description"  as location_description,
    "Arrest"                as is_arrest,
    "Domestic"              as is_domestic,
    "Beat"                  as beat,
    "District"              as district,
    "Ward"                  as ward,
    "Community Area"        as community_area,
    "FBI Code"              as fbi_code,
    "Latitude"              as latitude,
    "Longitude"             as longitude,
    "Updated On"            as updated_on
from {{ source('raw', 'chicago_crimes') }}
```



### `models/silver/silver_crimes_type.sql`

Catálogo de tipos de delito:

```sql
select distinct
    iucr,
    primary_type,
    description,
    fbi_code
from {{ ref('silver_crimes') }}
```



### `models/silver/schema.yml`

```yaml
version: 2

models:
  - name: silver_crimes
    description: "Crímenes de Chicago 2026, limpios y con nombres en snake_case."
    columns:
      - name: crime_id
        tests:
          - unique
          - not_null
      - name: occurred_at
        tests:
          - not_null

  - name: silver_crimes_type
    description: "Catálogo de tipos de delito (código IUCR, tipo y descripción)."
    columns:
      - name: iucr
        tests:
          - unique:
              config:
                severity: warn
          - not_null
```



### `models/gold/gold_crimes_by_month_type.sql`

```sql
select
    cast(date_trunc('month', occurred_at) as date)                  as month,
    primary_type,
    count(*)                                                        as total_crimes,
    cast(sum(case when is_arrest then 1 else 0 end) as integer)     as total_arrests,
    round(avg(case when is_arrest then 1.0 else 0 end), 3)          as arrest_rate
from {{ ref('silver_crimes') }}
group by 1, 2
```



### `models/gold/gold_crimes_by_district.sql`

```sql
select
    district,
    count(*)                                                        as total_crimes,
    cast(sum(case when is_arrest then 1 else 0 end) as integer)     as total_arrests,
    round(avg(case when is_arrest then 1.0 else 0 end), 3)          as arrest_rate,
    cast(sum(case when is_domestic then 1 else 0 end) as integer)   as domestic_crimes
from {{ ref('silver_crimes') }}
group by district
order by total_crimes desc
```



### `models/gold/schema.yml`

```yaml
version: 2

models:
  - name: gold_crimes_by_month_type
    description: "Crímenes, arrestos y tasa de arresto por mes y tipo de delito."

  - name: gold_crimes_by_district
    description: "Crímenes, arrestos y delitos domésticos por distrito policial."
    columns:
      - name: district
        tests:
          - unique
          - not_null
```



## 6. Ejecutar dbt

```bash
docker compose exec dbt dbt debug    # comprueba configuración y conexión
docker compose exec dbt dbt build    # construye modelos y ejecuta tests
```


| Comando       | Qué hace                                                                |
| ------------- | ----------------------------------------------------------------------- |
| `dbt debug`   | Valida configuración y conexión. Se usa al empezar o cuando algo falla. |
| `dbt compile` | Genera el SQL final sin ejecutarlo. Sirve para depurar.                 |
| `dbt run`     | Construye los modelos (ya compila internamente).                        |
| `dbt test`    | Ejecuta los tests.                                                      |
| `dbt build`   | `run` + `test` en orden de dependencias. Es el más usado.               |


Para ejecutar solo una parte:

```bash
docker compose exec dbt dbt build --select silver_crimes
docker compose exec dbt dbt build --select +gold_crimes_by_district   # ese modelo y sus dependencias
```



## 7. Explorar los datos con Jupyter

En una terminal aparte (ocupa la ventana mientras corre):

```bash
docker compose exec dbt jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/workspace
```

Copia la URL con el token que imprime (`http://127.0.0.1:8888/lab?token=...`) y ábrela en el navegador. Si pierdes la URL: `docker compose exec dbt jupyter server list`.

Ejemplo de consulta:

```python
import duckdb

with duckdb.connect('/workspace/data/chicago_crimes.db', read_only=True) as con:
    df = con.sql("select * from gold_crimes_by_district order by total_crimes desc").df()

df.head(10)
```

Para ver qué es tabla y qué es vista:

```python
with duckdb.connect('/workspace/data/chicago_crimes.db', read_only=True) as con:
    display(con.sql("""
        select table_name, table_type
        from information_schema.tables
        where table_schema = 'main'
        order by table_type, table_name
    """).df())
```



## 8. Documentación y linaje (data lineage)

```bash
docker compose exec dbt dbt docs generate
docker compose exec -w /workspace/chicago_crimes/target dbt python -m http.server 8080 --bind 0.0.0.0
```

Qué mirar:

- En la columna izquierda, `Projects → chicago_crimes → models`, entra en un modelo para ver su descripción, columnas, tests y SQL.
- Pulsa el icono del **grafo de linaje** (abajo a la derecha) para ver de dónde viene cada modelo y qué depende de él.

```
source: raw.chicago_crimes → silver_crimes → gold_crimes_by_month_type
                                   │       → gold_crimes_by_district
                                   └→ silver_crimes_type
```

Cuanto más completos sean los `description:` de los `.yml`, más rica sale la documentación. Tras cambiar modelos, repite `dbt docs generate` y recarga la página.

## 9. Dashboard con Streamlit

`streamlit_app/app.py`:

```python
import duckdb
import streamlit as st

DB_PATH = "/workspace/data/chicago_crimes.db"

st.set_page_config(page_title="Crímenes en Chicago 2026", layout="wide")
st.title("Crímenes en Chicago 2026")


@st.cache_data(ttl=60)
def query(sql: str):
    # Conexión corta: se abre y se cierra en cada consulta para no bloquear a dbt
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.sql(sql).df()


by_month = query("select * from gold_crimes_by_month_type")
by_district = query("select * from gold_crimes_by_district")

tipos = sorted(by_month["primary_type"].unique())
elegidos = st.multiselect("Tipo de delito", tipos, default=tipos[:5])
filtrado = by_month[by_month["primary_type"].isin(elegidos)]

col1, col2 = st.columns(2)
col1.metric("Crímenes (selección)", f"{filtrado['total_crimes'].sum():,}")
col2.metric("Arrestos (selección)", f"{int(filtrado['total_arrests'].sum()):,}")

st.subheader("Crímenes por mes")
st.line_chart(
    filtrado.pivot(index="month", columns="primary_type", values="total_crimes")
)

st.subheader("Crímenes por distrito")
st.bar_chart(by_district.set_index("district")["total_crimes"])

st.subheader("Datos por distrito")
st.dataframe(by_district, use_container_width=True)
```

El servicio `streamlit` del compose ya lo arranca solo. Si lo habías levantado antes de crear `app.py`:

```bash
docker compose restart streamlit
```

Abre `http://localhost:8501`. Logs si algo falla: `docker compose logs streamlit`.

## 10. Empezar desde cero

Para repetir toda la demostración limpia (el CSV se conserva):

```bash
docker compose down
rm -f data/chicago_crimes.db data/chicago_crimes.db.wal
rm -rf chicago_crimes/target chicago_crimes/logs
docker compose up -d --build
docker compose exec dbt python /workspace/scripts/load_raw.py
docker compose exec dbt dbt build
```

Cambiar de versión del dataset es tan simple como volver a descargar el CSV y repetir los dos últimos comandos.

## Comandos

```bash
docker compose up -d --build                  # levantar todo
docker compose ps                             # estado de los contenedores
docker compose logs streamlit                 # logs de un servicio
docker compose exec dbt bash                  # entrar al contenedor
docker compose exec dbt dbt build             # construir y testear
docker compose down                           # apagar todo
```



## Servicios y puertos


| Servicio            | URL                                            | Cómo se arranca                                     |
| ------------------- | ---------------------------------------------- | --------------------------------------------------- |
| Dashboard Streamlit | [http://localhost:8501](http://localhost:8501) | Automático con `docker compose up -d`               |
| Documentación dbt   | [http://localhost:8080](http://localhost:8080) | `python -m http.server` sobre `target/` (sección 8) |
| Jupyter Lab         | [http://localhost:8888](http://localhost:8888) | `jupyter lab` dentro del contenedor (sección 7)     |


