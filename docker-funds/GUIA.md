# Paso a paso: cargar standings del Mundial 2022 en Postgres

## 1. Levantar Postgres

Desde la carpeta donde está el `docker-compose.yml`:

```bash
docker compose up -d
```

Comprobar que el contenedor está corriendo:

```bash
docker compose ps
```

## 2. Crear y activar el entorno virtual de Python

### 2.1 Crear el entorno (solo la primera vez)

Desde la carpeta del proyecto, donde está el `requirements.txt`:

```bash
python -m venv venv
```

> En macOS/Linux, si `python` no funciona, usa `python3 -m venv venv`.

### 2.2 Activarlo

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
venv\Scripts\activate.bat
```

Sabrás que está activo porque aparece `(venv)` al inicio de la línea de la terminal.

### 2.3 Instalar las dependencias (solo la primera vez)

```bash
pip install -r requirements.txt
```

Comprobar que se instalaron:

```bash
pip list
```

> Debe incluir `psycopg2-binary` y `python-dotenv`. Si tu `requirements.txt` tiene `psycopg2` a secas y falla al instalar, cámbialo por `psycopg2-binary`.



### 2.4 Desactivarlo (cuando termines)

```bash
deactivate
```



## 3. Correr el script

Con `data-wc-2022.json` y el `.env` en la misma carpeta:

```bash
python extract.py
```

Debería imprimir que se extrajeron 32 filas y que se insertaron en Postgres.

## 4. Entrar a Postgres

```bash
docker exec -it postgres_container psql -U db_user -d wc_standings
```



## 5. Comprobar la tabla

Dentro de `psql`:

```sql
-- Cantidad de filas (debería ser 32)
SELECT COUNT(*) FROM standings;

-- Ver las primeras filas
SELECT * FROM standings LIMIT 10;

-- Ver un grupo completo ordenado por puntos
SELECT pais, puntos, grupo
FROM standings
WHERE grupo = 'Group A'
ORDER BY puntos DESC;

-- Top 5 países con más puntos
SELECT pais, puntos
FROM standings
ORDER BY puntos DESC
LIMIT 5;
```

Para salir de `psql`:

```
\q
```



## Extras

**Vaciar la tabla** (si corriste el script más de una vez y hay duplicados):

```sql
TRUNCATE standings RESTART IDENTITY;
```

**Apagar el contenedor del proyecto:**

```bash
docker compose down
```

**Detener todos los contenedores activos:**

```bash
docker stop $(docker ps -q)
```

