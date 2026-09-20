# Restaurar la base de datos `dvdrental` en un contenedor Docker con PostgreSQL

Esta guía asume que:
- Tenés un contenedor Docker corriendo PostgreSQL llamado **`postgres_container`**.
- Ya descomprimiste `dvdrental.zip` y tenés una carpeta con `toc.dat`, varios archivos `.dat` numerados y `restore.sql`.
- Estás en la terminal de tu Mac (host), no dentro del contenedor.

---

## 1. Copiar la carpeta descomprimida al contenedor

Reemplazá la ruta de origen por la tuya. Si el path tiene espacios, ponelo entre comillas dobles.

```bash
docker cp "/ruta/a/tu/carpeta/dvdrental" postgres_container:/tmp/dvdrental_restore
```

**Ejemplo real:**
```bash
docker cp "/Users/mauroperez/Desktop/***"/dvdrental" postgres_container:/tmp/dvdrental_restore
```

---

## 2. Entrar al contenedor

```bash
docker exec -it postgres_container bash
```

A partir de acá, todos los comandos se ejecutan **dentro** del contenedor.

---

## 3. Verificar que los archivos llegaron bien

```bash
ls /tmp/dvdrental_restore
```

Deberías ver `toc.dat`, varios archivos `NNNN.dat` y `restore.sql`.

---

## 4. Crear la base de datos destino

```bash
psql -U postgres -d  -c "CREATE DATABASE dvdrental;"
```

> Si ya la habías creado antes desde DBeaver, este comando va a tirar un error de "already exists" — no pasa nada, es esperable.

---

## 5. Ejecutar la restauración

```bash
pg_restore -U postgres -d dvdrental -v --no-owner --no-privileges /tmp/dvdrental_restore
```

Vas a ver un montón de líneas de log (creación de esquema, tablas, secuencias, copia de datos tabla por tabla). Algunas líneas tipo `already exists, skipping` para cosas como la extensión `plpgsql` son normales y no indican un problema real.

---

## 6. Salir del contenedor y limpiar los archivos temporales

```bash
exit
```


```bash
docker exec postgres_container rm -rf /tmp/dvdrental_restore
```

Este paso es opcional, pero es buena práctica no dejar basura acumulada dentro del contenedor.

---

## 7. Verificar en DBeaver

1. Click derecho sobre la base `dvdrental` en el navegador de DBeaver.
2. Elegí **Refresh** (o **Invalidate/Reconnect** si no ves los cambios).
3. Expandí la base y confirmá que aparecen las tablas: `actor`, `film`, `customer`, `rental`, `payment`, etc., con datos cargados.

---

## Resumen rápido (todos los comandos juntos)

```bash

docker cp "/ruta/a/tu/carpeta/dvdrental" postgres_container:/tmp/dvdrental_restore
docker exec -it postgres_container bash

# Dentro del contenedor
ls /tmp/dvdrental_restore
psql -U postgres -c "CREATE DATABASE dvdrental;"
pg_restore -U postgres -d dvdrental -v --no-owner --no-privileges /tmp/dvdrental_restore
exit


docker exec postgres_container rm -rf /tmp/dvdrental_restore
```
