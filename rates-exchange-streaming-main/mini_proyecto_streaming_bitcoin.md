# Mini proyecto — Streaming de cotizaciones Bitcoin

## 1. Objetivo

Pipeline de streaming:

```text
Bitcoin API
    ↓
🐍 Producer (Python)
    ↓
📨 Kafka
    ↓
 ┌──────────────┬────────────────┬────────────────┐
 ↓              ↓                ↓
MinIO        PostgreSQL        MongoDB
                                  ↓
                            Mongo Express

PostgreSQL
    ↓
Grafana
```

La idea principal es demostrar cómo un mismo evento publicado en Kafka puede ser procesado por **varios consumers independientes**, cada uno con una responsabilidad diferente.

---

## 2. Componentes

### Producer

Aplicación Python que obtiene cotizaciones y las publica en Kafka.

> El Producer no necesita saber quién consumirá los mensajes.

### Kafka

Sistema central de distribución de eventos.

```text
Producer → Kafka → Consumers
```

En simple:

> Kafka transporta y mantiene los mensajes; los consumers deciden qué hacer con ellos.

### Consumers

```text
Kafka
  │
  ├──→ Consumer PostgreSQL → PostgreSQL
  ├──→ Consumer MongoDB → MongoDB
  └──→ Consumer MinIO → MinIO
```

Esto demuestra desacoplamiento: se puede añadir un nuevo consumer sin modificar el Producer.

---

## 3. Consumer Groups

Ejemplos utilizados:

```text
postgres-saver
mongodb-saver
minio-saver
```

Al tener grupos diferentes, los consumers pueden recibir el mismo flujo de eventos de forma independiente.

```text
                    Kafka
                      │
             bitcoin-data
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
postgres-saver   mongodb-saver   minio-saver
       ↓              ↓              ↓
 PostgreSQL         MongoDB          MinIO
```

---

## 4. PostgreSQL

Representa datos estructurados y consultables mediante SQL.

Comprobar filas:

```bash
docker exec -it postgres_database psql -U postgres -d rates -c "SELECT COUNT(*) FROM bitcoin;"
```

Para verificar que sigue entrando información, ejecutar dos veces separadas por unos segundos. Si el contador aumenta, el pipeline está funcionando.

Ver últimas filas:

```bash
docker exec -it postgres_database psql -U postgres -d rates -c "SELECT * FROM bitcoin ORDER BY created_at DESC LIMIT 5;"
```

---

## 5. MongoDB

Representa una base documental. En este proyecto los eventos conservan una estructura anidada por exchange.

Ejemplo:

```javascript
{
  ripio: {
    ask: 66899.17,
    totalAsk: 66899.17,
    bid: 64203.21,
    totalBid: 64203.21,
    time: 1786867644
  },
  satoshitango: {
    ask: 67110.66,
    totalAsk: 67446.22,
    bid: 64503.70,
    totalBid: 64181.19,
    time: 1786867691
  },
  decrypto: {
    ask: 65770.22,
    totalAsk: 66000.42,
    bid: 63689.29,
    time: 1786867660
  }
}
```

Cada documento representa una fotografía/evento con información de varios exchanges.

### ¿Por qué PostgreSQL y MongoDB?

**PostgreSQL**
- Datos estructurados
- SQL
- Agregaciones
- Análisis
- Integración con Grafana

**MongoDB**
- Documentos
- Estructuras anidadas
- Esquema flexible
- Conservación del evento en formato cercano al JSON original

No se trata simplemente de guardar lo mismo dos veces: se pueden mostrar como dos modelos de persistencia con objetivos diferentes.

### Consultas útiles

Entrar:

```bash
docker exec -it mongodb mongosh
```

Seleccionar base:

```javascript
use bitcoin
```

Colecciones:

```javascript
show collections
```

Contar documentos:

```javascript
db.prices.countDocuments()
```

Ver documentos:

```javascript
db.prices.find().limit(5).pretty()
```

Ripio con ask > 66000:

```javascript
{
  "ripio.ask": {
    "$gt": 66000
  }
}
```

Comparar Ripio y SatoshiTango:

```javascript
{
  "$expr": {
    "$lt": [
      "$ripio.ask",
      "$satoshitango.ask"
    ]
  }
}
```

Diferencia superior a 1000:

```javascript
{
  "$expr": {
    "$gt": [
      {
        "$subtract": [
          "$satoshitango.ask",
          "$ripio.ask"
        ]
      },
      1000
    ]
  }
}
```

Esta última puede servir como ejemplo de detección de diferencias de precio entre exchanges.

### Comandos rápidos

Contar documentos:

```bash
docker exec -it mongodb mongosh bitcoin --eval "db.prices.countDocuments()"
```

Ver últimos documentos:

```bash
docker exec -it mongodb mongosh bitcoin --eval "db.prices.find().sort({_id:-1}).limit(3).pretty()"
```

Ver solo Ripio:

```bash
docker exec -it mongodb mongosh bitcoin --eval "db.prices.find({}, {'ripio.ask':1, 'ripio.bid':1, 'ripio.time':1}).sort({_id:-1}).limit(5).pretty()"
```

---

## 6. Mongo Express

Mongo Express es una interfaz web para MongoDB.

Analogía:

```text
PostgreSQL  ↔  pgAdmin
MongoDB     ↔  Mongo Express
```

MongoDB usa normalmente el puerto `27017`.

Mongo Express está expuesto en:

```text
http://localhost:8082
```

Arquitectura:

```text
Navegador
    ↓ HTTP
Mongo Express
    ↓
MongoDB
```

Mongo Express no es la base de datos: es una interfaz para visualizar/administrar MongoDB.

---

## 7. MinIO

MinIO representa almacenamiento de objetos.

```text
PostgreSQL → tablas
MongoDB    → documentos
MinIO      → objetos/archivos
```

El consumer de MinIO recibe los eventos y los almacena como objetos.

Puede explicarse como una capa de Object Storage / Data Lake.

---

## 8. Grafana

Grafana es la parte de visualización.

> Grafana consulta fuentes de datos y las convierte en gráficos, tablas y dashboards.

```text
Kafka
  ↓
PostgreSQL
  ↓
Grafana
  ↓
📊 Dashboard
```

Grafana no es necesariamente quien almacena los datos.

### ¿Grafana o Power BI?

Ambos pueden utilizarse para visualización y análisis, pero Grafana encaja especialmente bien en este proyecto por su orientación a dashboards/monitorización y su integración sencilla con un entorno Docker y fuentes técnicas como PostgreSQL.

---

## 9. Docker Compose

Levantar:

```bash
docker compose up -d
```

Ver servicios:

```bash
docker compose ps
```

Logs:

```bash
docker compose logs --tail=50 <servicio>
```

Ejemplos:

```bash
docker compose logs --tail=50 kafka
docker compose logs --tail=50 kafka-postgres-consumer
docker compose logs --tail=50 kafka-mongodb-consumer
docker compose logs --tail=50 kafka-producer
```

### `stop` vs `down`

Detener:

```bash
docker compose stop
```

Después:

```bash
docker compose start
```

`stop` detiene containers pero conserva containers y datos.

Eliminar containers del proyecto:

```bash
docker compose down
```

Los volúmenes normalmente se conservan.

Para volver a levantar:

```bash
docker compose up -d
```

**Evitar si se quieren conservar datos:**

```bash
docker compose down -v
```

---

## 10. Volúmenes

Los volúmenes permiten conservar datos aunque los containers se detengan o se vuelvan a crear.

Conceptualmente:

```text
PostgreSQL → postgres_data
MongoDB    → mongodb_data
Grafana    → grafana_data
MinIO      → minio_data
```

---

## 11. Dependencias Python y Docker

Si aparece:

```text
ModuleNotFoundError: No module named 'pymongo'
```

significa que `pymongo` no está instalado dentro de la imagen Docker.

Añadir al `requirements.txt`:

```text
pymongo
```

Y reconstruir:

```bash
docker compose up -d --build
```

Idea importante:

> Que una librería esté instalada en el ordenador no significa que esté instalada dentro del container.

---

## 12. Diagnóstico de Kafka

Durante el arranque puede aparecer:

```text
Connection refused
```

o:

```text
Failed to resolve 'kafka:9092'
```

Una prueba de DNS desde el consumer:

```bash
docker exec -it bitcoin-rdbs-consumer getent hosts kafka
```

Ejemplo:

```text
172.22.0.6 kafka
```

Comprobar conexión TCP con Python:

```bash
docker exec -it bitcoin-rdbs-consumer python -c "import socket; s=socket.create_connection(('kafka',9092),5); print('CONEXION OK'); s.close()"
```

Si aparece:

```text
CONEXION OK
```

el consumer puede alcanzar Kafka.

Los errores históricos de conexión no necesariamente significan que el pipeline esté fallando: hay que comprobar si los datos siguen llegando a los destinos.

---

## 13. Health check completo

### Containers

```bash
docker compose ps
```

### Producer

```bash
docker compose logs --tail=50 kafka-producer
```

### PostgreSQL Consumer

```bash
docker compose logs --tail=50 kafka-postgres-consumer
```

### PostgreSQL

```bash
docker exec -it postgres_database psql -U postgres -d rates -c "SELECT COUNT(*) FROM bitcoin;"
```

Ejecutar dos veces y comprobar que aumenta.

### MongoDB Consumer

```bash
docker compose logs --tail=50 kafka-mongodb-consumer
```

### MongoDB

```bash
docker exec -it mongodb mongosh bitcoin --eval "db.prices.countDocuments()"
```

Ejecutar dos veces y comprobar que aumenta.

### MinIO

```bash
docker compose logs --tail=50 kafka-consumer
```

Comprobar también los objetos en la interfaz de MinIO.

### Grafana

Abrir:

```text
http://localhost:3000
```

Comprobar que PostgreSQL funciona como Data Source y que el dashboard muestra datos recientes.

### Mongo Express

Abrir:

```text
http://localhost:8082
```

Comprobar:

```text
bitcoin
└── prices
    ├── documento
    ├── documento
    └── ...
```

---

## 14. Checklist final

```text
[ ] Docker Compose levanta todos los servicios
[ ] Producer obtiene datos
[ ] Producer publica en Kafka
[ ] Kafka está operativo
[ ] Consumer PostgreSQL está conectado
[ ] PostgreSQL recibe nuevas filas
[ ] Consumer MongoDB está conectado
[ ] MongoDB recibe nuevos documentos
[ ] Consumer MinIO está conectado
[ ] MinIO recibe nuevos objetos
[ ] Grafana conecta con PostgreSQL
[ ] Grafana muestra datos
[ ] Mongo Express permite visualizar MongoDB
```

---

## 15. Conceptos que conviene poder explicar

**Producer**

> Aplicación que produce y publica eventos.

**Consumer**

> Aplicación que consume eventos desde Kafka y realiza alguna acción con ellos.

**Kafka**

> Sistema que recibe, almacena y distribuye eventos entre productores y consumidores.

**Consumer Group**

> Grupo que permite a Kafka gestionar qué consumidores reciben qué mensajes.

**PostgreSQL**

> Base de datos relacional orientada a datos estructurados y consultas SQL.

**MongoDB**

> Base de datos documental que permite almacenar estructuras JSON-like flexibles y anidadas.

**MinIO**

> Almacenamiento de objetos que puede utilizarse como Object Storage / Data Lake.

**Grafana**

> Herramienta para consultar datos y crear dashboards y visualizaciones.

**Mongo Express**

> Interfaz web para visualizar y administrar MongoDB.

**Docker**

> Permite ejecutar cada componente en containers aislados y reproducibles.

**Docker Compose**

> Permite definir y ejecutar todos los containers del proyecto conjuntamente.

---

## 16. Explicación de arquitectura en 30 segundos

> Tengo un Producer en Python que obtiene cotizaciones de Bitcoin y las publica en Kafka. Kafka desacopla al productor de los consumidores. A partir de ahí tengo varios consumers independientes: uno almacena los datos en PostgreSQL para análisis SQL y visualización con Grafana, otro conserva los eventos como documentos en MongoDB y otro los almacena en MinIO como objetos. Mongo Express me permite inspeccionar MongoDB. Todo el entorno está orquestado con Docker Compose.

---

## 17. Flujo completo

```text
                     ┌─────────────────┐
                     │   Bitcoin API   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Python Producer │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │      Kafka      │
                     │  bitcoin-data   │
                     └────────┬────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      ┌────────────┐   ┌─────────────┐  ┌─────────────┐
      │   MinIO    │   │ PostgreSQL  │  │   MongoDB   │
      │  Consumer  │   │  Consumer   │  │  Consumer   │
      └─────┬──────┘   └──────┬──────┘  └──────┬──────┘
            │                 │                 │
            ▼                 ▼                 ▼
         MinIO            PostgreSQL        MongoDB
                              │                 │
                              ▼                 ▼
                           Grafana        Mongo Express
                              │                 │
                              ▼                 ▼
                         📊 Dashboard       🌐 Web UI
```

---

## 18. Idea central

> **El Producer produce una vez. Kafka desacopla. Los distintos consumers pueden procesar el mismo flujo de eventos de maneras diferentes.**

Añadir MongoDB, por ejemplo, no requiere modificar el Producer:

```text
Producer → Kafka
```

Simplemente se añade:

```text
Kafka → nuevo Consumer → MongoDB
```

Ese desacoplamiento es una de las ideas fundamentales de una arquitectura basada en eventos.
