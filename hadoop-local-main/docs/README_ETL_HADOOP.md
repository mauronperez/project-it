# ETL con Hadoop: Postgres → HDFS → Agregación → Postgres

Flujo completo: exportamos `Venta_incremental.csv`,lo subimos a HDFS, corremos un job de Hadoop
Streaming que calcula el total vendido por producto, y traemos el
resultado de vuelta a Postgres, en una tabla nueva.

## Por qué Hadoop Streaming, y no un jar de Java

`hadoop jar ... WordCount` (ejemplo de la Odisea )viene compilado
en Java. Streaming te permite escribir el mapper/reducer en **Python**,
sin compilar nada — Hadoop simplemente les pasa datos por `stdin`/`stdout`

## 0. Confirmar que los archivos están donde el cluster los espera

Gracias a los volúmenes ya definidos en tu `docker-compose.yml`:

```yaml
volumes:
  - ./scripts:/scripts
  - ./data:/data
```

No hace falta copiar nada a mano — solo asegurarse de que:

```
tu-proyecto/
├── docker-compose.yml
├── scripts/
│   ├── mapper.py
│   └── reducer.py
└── data/
    └── Venta_incremental.csv
```

## 1. Levantar el cluster de hadoop

```bash
docker compose up -d
docker exec -it hadoop-master bash
```

Ya **dentro** del contenedor `hadoop-master`, iniciar los servicios:

```bash
start-dfs.sh
start-yarn.sh
```

## 2. Subir Venta.csv a HDFS

```bash
hdfs dfs -mkdir -p /user/data
hdfs dfs -put /data/Venta_incremental.csv /user/data/Venta_incremental.csv
hdfs dfs -ls /user/data
```

## 3. Correr el job de Hadoop Streaming

```bash
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming*.jar \
  -input /user/data/Venta_incremental.csv \
  -output /user/data/output_ventas_por_producto \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -file /scripts/mapper.py \
  -file /scripts/reducer.py
```

**El** `-file` **es importante:** los slaves (`hadoop-slave1`-`4`) **no** tienen
montado `./scripts`, así que Hadoop necesita "empaquetar y enviar" tus
scripts junto con el job — eso es justo lo que hace `-file`.

## 4. Ver el resultado dentro de HDFS

```bash
hdfs dfs -cat /user/data/output_ventas_por_producto/part-00000 | head -20
```

## 5. Traer el resultado de HDFS a la carpeta compartida (`/data`)

```bash
hdfs dfs -get /user/data/output_ventas_por_producto/part-00000 \
  /data/resultado_ventas_por_producto.tsv
```

## 6. Salir del contenedor, y cargar el resultado en Postgres

```bash
exit
```

Con el contenedor encendido de Postgres, ejecutar:

```bash
python load_resultado_hadoop.py
```

## 7. Verificar en Postgres

```bash
docker exec -it pg_container psql -U postgres -d playground -c \
  "SELECT * FROM resumen_ventas_hadoop ORDER BY total_vendido DESC LIMIT 10;"
```

## El círculo completo

```
Postgres (venta)
    → Venta_incremental.csv
    → HDFS (/user/data/Venta_incremental.csv)
    → Hadoop Streaming (mapper + reducer, corriendo distribuido entre los 4 slaves)
    → resultado_ventas_por_producto.tsv (de vuelta a tu disco, vía /data)
    → Postgres (resumen_ventas_hadoop) -- una tabla NUEVA, resultado del cluster
```

## Punto de discusión para la clase

```
Sería interesante probar cómo se distribuyen los recursos
ante un incremento considerable en los registros (1M). 
Observar el comportamiento en http://localhost:8088 para
observar su distribución. 
```