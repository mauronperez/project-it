# Monitorización de Apache Airflow con Prometheus y Grafana

## 1. Introducción

Este documento explica cómo configurar un sistema de monitorización para **Apache Airflow** utilizando:

- **Apache Airflow**: plataforma de orquestación de workflows.
- **StatsD**: protocolo utilizado por Airflow para enviar métricas.
- **StatsD Exporter**: convierte las métricas StatsD a un formato compatible con Prometheus.
- **Prometheus**: sistema de recopilación y almacenamiento de métricas.
- **Grafana**: herramienta de visualización y creación de dashboards.

La arquitectura utilizada es:

```text
                    MÉTRICAS
                      │
                      ▼
                 ┌─────────┐
                 │ Airflow │
                 └────┬────┘
                      │
                      │ StatsD
                      ▼
              ┌─────────────────┐
              │ StatsD Exporter │
              └────────┬────────┘
                       │
                       │ Prometheus format
                       ▼
                ┌──────────────┐
                │  Prometheus  │
                └───────┬──────┘
                        │
                        │ PromQL
                        ▼
                  ┌───────────┐
                  │  Grafana  │
                  └───────────┘
```

---



# 2. ¿Qué es Prometheus?

**Prometheus** es un sistema de monitorización y almacenamiento de métricas.

Su función principal es:

> Recopilar métricas de diferentes servicios y almacenarlas para poder consultarlas posteriormente.

Por ejemplo, Airflow puede generar una métrica:

```text
airflow_executor_open_slots = 32
```

Prometheus recopila periódicamente esa información y la almacena.

Posteriormente podemos consultarla mediante **PromQL**, el lenguaje de consultas de Prometheus.

Por ejemplo:

```promql
airflow_executor_open_slots
```

Esto devolvería:

```text
32
```

---



# 3. ¿Qué es Grafana?

**Grafana** es una herramienta de visualización y observabilidad.

Grafana no es, principalmente, el lugar donde se almacenan las métricas.

Su función es:

> Conectarse a fuentes de datos como Prometheus y representar la información mediante gráficos, estadísticas, tablas y dashboards.

Por ejemplo, Prometheus puede tener:

```text
airflow_executor_open_slots = 32
airflow_executor_queued_tasks = 0
airflow_executor_running_tasks = 0
```

Grafana puede convertir esos valores en:

```text
┌──────────────────────────────────────────┐
│           AIRFLOW MONITORING              │
├──────────────┬──────────────┬─────────────┤
│ Open Slots   │ Queued Tasks │ Running     │
│      32      │      0       │      0      │
└──────────────┴──────────────┴─────────────┘
```

También permite representar valores a lo largo del tiempo mediante gráficas.

---



# 4. ¿Qué es StatsD?

**StatsD** es un protocolo sencillo para enviar métricas.

Airflow puede utilizar StatsD para publicar métricas de funcionamiento.

Por ejemplo:

```text
airflow.executor.running_tasks
airflow.executor.queued_tasks
airflow.executor.open_slots
```

StatsD permite que una aplicación envíe estas métricas sin tener que conocer directamente cómo se almacenarán o visualizarán posteriormente.

En nuestra arquitectura, Airflow envía las métricas al **StatsD Exporter**.

---



# 5. ¿Qué es StatsD Exporter?

Prometheus normalmente funciona de una manera diferente a StatsD.

StatsD utiliza un modelo en el que la aplicación **envía** las métricas.

Prometheus utiliza principalmente un modelo en el que **consulta** periódicamente un endpoint para obtener las métricas.

Por este motivo utilizamos:

**StatsD Exporter**

Su función es actuar como puente:

```text
Airflow
   │
   │ StatsD
   ▼
StatsD Exporter
   │
   │ HTTP /metrics
   ▼
Prometheus
```

El exporter recibe las métricas de Airflow y las expone en un endpoint HTTP, por ejemplo:

```text
http://statsd-exporter:9102/metrics
```

Prometheus consulta periódicamente ese endpoint.

---



# 6. Arquitectura completa

En nuestro entorno Docker Compose tenemos:

```text
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                  airflow-network                         │
│                                                         │
│  ┌───────────────┐                                      │
│  │    Airflow    │                                      │
│  │               │                                      │
│  │ Scheduler     │                                      │
│  │ DAG Processor │                                      │
│  │ Worker        │                                      │
│  │ Triggerer     │                                      │
│  └───────┬───────┘                                      │
│          │                                               │
│          │ StatsD                                        │
│          ▼                                               │
│  ┌───────────────────┐                                  │
│  │  StatsD Exporter  │                                  │
│  │                   │                                  │
│  │ UDP 9125           │                                  │
│  │ HTTP 9102          │                                  │
│  └─────────┬─────────┘                                  │
│            │                                             │
│            │ /metrics                                   │
│            ▼                                             │
│  ┌───────────────────┐                                  │
│  │    Prometheus     │                                  │
│  │                   │                                  │
│  │       :9090       │                                  │
│  └─────────┬─────────┘                                  │
│            │                                             │
│            │ PromQL                                      │
│            ▼                                             │
│  ┌───────────────────┐                                  │
│  │      Grafana      │                                  │
│  │                   │                                  │
│  │       :3000       │                                  │
│  └───────────────────┘                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---



# 7. Configuración de Airflow

En el `docker-compose.yml` se habilitan las métricas de StatsD mediante las siguientes variables:

```yaml
AIRFLOW__METRICS__STATSD_ON: 'true'
AIRFLOW__METRICS__STATSD_HOST: statsd-exporter
AIRFLOW__METRICS__STATSD_PORT: '9125'
AIRFLOW__METRICS__STATSD_PREFIX: airflow
```

Estas variables indican a Airflow:

- Activar StatsD.
- Utilizar el servicio Docker llamado `statsd-exporter`.
- Utilizar el puerto UDP `9125`.
- Utilizar `airflow` como prefijo de las métricas.

Por ejemplo, una métrica interna de Airflow puede terminar expuesta como:

```text
airflow_executor_open_slots
```

---



# 8. Configuración de StatsD Exporter

El servicio Docker utilizado es:

```yaml
statsd-exporter:
  image: prom/statsd-exporter:latest

  command:
    - "--statsd.listen-udp=:9125"
    - "--web.listen-address=:9102"

  ports:
    - "9102:9102"

  networks:
    - airflow-network
```

El exporter utiliza:

```text
9125 UDP
```

para recibir las métricas StatsD.

Y expone:

```text
9102 HTTP
```

para que Prometheus pueda consultarlas.

---



# 9. Configuración de Prometheus

Prometheus utiliza un archivo:

```text
prometheus/prometheus.yml
```

Ejemplo:

```yaml
global:
  scrape_interval: 15s

  evaluation_interval: 15s

scrape_configs:

  - job_name: airflow

    static_configs:
      - targets:
          - statsd-exporter:9102
```



## ¿Qué significa esto?

```yaml
scrape_interval: 15s
```

Significa que Prometheus consulta las métricas cada 15 segundos.

El siguiente bloque:

```yaml
scrape_configs:
  - job_name: airflow
```

define un trabajo de monitorización llamado:

```text
airflow
```

Y:

```yaml
targets:
  - statsd-exporter:9102
```

indica a Prometheus dónde obtener las métricas.

---



# 10. Comprobar Prometheus

Después de iniciar Docker Compose:

```bash
docker compose up -d
```

podemos comprobar los servicios:

```bash
docker compose ps
```

Prometheus estará disponible en:

```text
http://localhost:9090
```

También podemos comprobar los targets:

```text
http://localhost:9090/targets
```

Deberíamos ver:

```text
airflow

statsd-exporter:9102

UP
```

El estado `UP` significa que Prometheus puede acceder correctamente al endpoint de métricas.

---



# 11. Consultar métricas con PromQL

Prometheus utiliza **PromQL**.

Por ejemplo:

```promql
airflow_executor_open_slots
```

permite consultar los slots libres del executor.

Otra métrica:

```promql
airflow_executor_queued_tasks
```

muestra las tareas que están esperando.

Y:

```promql
airflow_executor_running_tasks
```

muestra las tareas que están ejecutándose.

También podemos consultar errores de procesamiento de DAGs:

```promql
airflow_dag_processing_import_errors
```

---



# 12. Métricas disponibles

Algunas de las métricas observadas en nuestro entorno son:

## Executor

```text
airflow_executor_open_slots
airflow_executor_queued_tasks
airflow_executor_running_tasks
```

Estas métricas permiten conocer la actividad del executor.

---



## Procesamiento de DAGs

```text
airflow_dag_processing_file_path_queue_size
airflow_dag_processing_file_path_queue_update_count
airflow_dag_processing_import_errors
airflow_dag_processing_processes
airflow_dag_processing_total_parse_time
```

Estas métricas permiten monitorizar el procesamiento y parsing de los DAGs.

Por ejemplo:

```promql
airflow_dag_processing_import_errors
```

puede utilizarse para detectar errores al importar DAGs.

---



## Scheduler

También tenemos métricas como:

```text
airflow_scheduler_critical_section_duration
airflow_scheduler_critical_section_query_duration
```

Estas permiten analizar el comportamiento del scheduler.

---



## DAG Runs

Tenemos métricas como:

```text
airflow_dagrun_duration_success
airflow_dagrun_dependency_check
```

Estas permiten analizar el rendimiento de las ejecuciones de DAGs.

---



## Tasks

También existen métricas como:

```text
airflow_task_duration
airflow_task_instance_created
airflow_task_scheduled_duration
```

Estas son útiles para analizar el rendimiento de las tareas.

---



# 13. ¿Qué son los quantiles?

Algunas métricas de duración aparecen con:

```text
quantile="0.5"
quantile="0.9"
quantile="0.99"
```

Estos valores representan percentiles.

Por ejemplo:

```text
P50 = 4.6 segundos
P90 = 60 segundos
P99 = 60 segundos
```

Significa aproximadamente:

- **P50**: el 50% de las ejecuciones está por debajo de ese valor.
- **P90**: el 90% está por debajo de ese valor.
- **P99**: el 99% está por debajo de ese valor.

Los quantiles son especialmente útiles cuando tenemos muchas ejecuciones y queremos detectar comportamientos anómalos o ejecuciones lentas.

Para un dashboard inicial puede ser más sencillo utilizar valores medios o valores actuales.

---



# 14. Configuración de Grafana

Grafana se ejecuta mediante:

```yaml
grafana:
  image: grafana/grafana:latest

  ports:
    - "3000:3000"

  volumes:
    - grafana_data:/var/lib/grafana

  networks:
    - airflow-network
```

Grafana estará disponible en:

```text
http://localhost:3000
```

---



# 15. Añadir Prometheus como Data Source

En Grafana:

```text
Connections
    ↓
Data sources
    ↓
Add data source
    ↓
Prometheus
```

La URL debe ser:

```text
http://prometheus:9090
```

No debemos utilizar:

```text
http://localhost:9090
```

porque Grafana está ejecutándose dentro de un contenedor Docker.

Desde el punto de vista del contenedor de Grafana:

```text
localhost
```

significa:

```text
el propio contenedor de Grafana
```

Mientras que:

```text
prometheus:9090
```

hace referencia al contenedor de Prometheus dentro de la red Docker.

---



# 16. Crear un dashboard

Una vez configurado Prometheus como Data Source:

```text
Dashboards
    ↓
New
    ↓
New dashboard
    ↓
Add visualization
```

Seleccionamos:

```text
Prometheus
```

como fuente de datos.

---



# 17. Ejemplo de panel: Executor Open Slots

Query:

```promql
airflow_executor_open_slots
```

Tipo de visualización:

```text
Stat
```

Título:

```text
Executor Open Slots
```

Este panel muestra cuántos slots tiene disponibles el executor.

---



# 18. Ejemplo: Tasks en cola

Query:

```promql
airflow_executor_queued_tasks
```

Visualización:

```text
Stat
```

Título:

```text
Queued Tasks
```

Permite detectar si se están acumulando tareas esperando para ejecutarse.

---



# 19. Ejemplo: Tasks ejecutándose

Query:

```promql
airflow_executor_running_tasks
```

Visualización:

```text
Stat
```

Título:

```text
Running Tasks
```

---



# 20. Ejemplo: Errores de importación

Query:

```promql
airflow_dag_processing_import_errors
```

Visualización:

```text
Stat
```

Título:

```text
DAG Import Errors
```

Un valor superior a cero puede indicar que Airflow tiene problemas al cargar uno o varios DAGs.

---



# 21. Ejemplo de dashboard

Una primera versión del dashboard puede tener esta estructura:

```text
┌──────────────────────────────────────────────────────┐
│                  AIRFLOW MONITORING                  │
├────────────────┬────────────────┬────────────────────┤
│ Open Slots     │ Queued Tasks   │ Running Tasks      │
│      32        │       0        │        0           │
├────────────────┴────────────────┴────────────────────┤
│                                                      │
│              DAG Processing                          │
│                                                      │
│ Import Errors: 0                                     │
│ Queue Size: 0                                        │
│ Parse Time                                           │
│                                                      │
├─────────────────────────┬────────────────────────────┤
│ DAG Run Duration        │ Task Duration              │
│                         │                            │
│         6.13s           │         4.66s              │
│                         │                            │
├─────────────────────────┴────────────────────────────┤
│                                                      │
│                 Scheduler                            │
│                                                      │
│       Critical Section Duration                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---



# 22. Persistencia

Es importante utilizar volúmenes Docker para que los datos no desaparezcan al eliminar los contenedores.

Para Prometheus:

```yaml
volumes:
  - prometheus_data:/prometheus
```

Para Grafana:

```yaml
volumes:
  - grafana_data:/var/lib/grafana
```

Y en la sección global:

```yaml
volumes:
  prometheus_data:
  grafana_data:
```

De esta manera, los datos de Prometheus y la configuración de Grafana permanecen aunque los contenedores se reinicien.

---



# 23. Comandos habituales



## Iniciar todos los servicios

```bash
docker compose up -d
```



## Ver el estado

```bash
docker compose ps
```



## Ver logs de Prometheus

```bash
docker compose logs -f prometheus
```



## Ver logs de Grafana

```bash
docker compose logs -f grafana
```



## Ver logs del StatsD Exporter

```bash
docker compose logs -f statsd-exporter
```



## Detener los servicios

```bash
docker compose down
```



## Reiniciar un servicio

```bash
docker compose restart grafana
```

---



# 24. Flujo completo de una métrica

Por ejemplo, imaginemos que Airflow tiene:

```text
32 slots disponibles
```

El proceso completo es:

### Paso 1 — Airflow

Airflow genera:

```text
airflow.executor.open_slots = 32
```



### Paso 2 — StatsD

Airflow envía esa métrica al:

```text
statsd-exporter:9125
```



### Paso 3 — StatsD Exporter

El exporter convierte la métrica al formato de Prometheus.

### Paso 4 — Prometheus

Prometheus consulta:

```text
http://statsd-exporter:9102/metrics
```

y obtiene:

```text
airflow_executor_open_slots 32
```



### Paso 5 — Grafana

Grafana consulta Prometheus mediante:

```promql
airflow_executor_open_slots
```

y representa:

```text
32
```

en un panel.

---



# 25. Diferencia entre las herramientas

Es importante entender que cada componente tiene una función diferente:


| Herramienta     | Función                                  |
| --------------- | ---------------------------------------- |
| Airflow         | Ejecuta y orquesta workflows             |
| StatsD          | Protocolo para enviar métricas           |
| StatsD Exporter | Convierte StatsD a métricas Prometheus   |
| Prometheus      | Recopila y almacena métricas             |
| PromQL          | Lenguaje para consultar Prometheus       |
| Grafana         | Visualiza las métricas y crea dashboards |


En resumen:

```text
Airflow
  │
  │ genera métricas
  ▼
StatsD
  │
  │ transporte
  ▼
StatsD Exporter
  │
  │ expone /metrics
  ▼
Prometheus
  │
  │ almacena
  ▼
PromQL
  │
  │ consulta
  ▼
Grafana
  │
  │ visualiza
  ▼
Dashboard
```

---



# 26. Monitorización futura

Una vez que la configuración básica funciona, se pueden añadir dashboards y alertas para detectar:

- DAGs que tardan demasiado.
- Aumento de tareas en cola.
- Workers saturados.
- Falta de slots disponibles.
- Errores al importar DAGs.
- Problemas con el scheduler.
- Aumento de la duración de las tareas.
- Problemas de rendimiento.
- Problemas con el DAG processor.
- Problemas con los pools de Airflow.

También se pueden configurar alertas en Grafana para enviar notificaciones cuando determinadas métricas superen un umbral.

---



# 27. Resumen

La arquitectura implementada utiliza:

```text
┌──────────┐
│ Airflow  │
└────┬─────┘
     │
     │ StatsD
     ▼
┌─────────────────┐
│ StatsD Exporter │
└────────┬────────┘
         │
         │ Prometheus metrics
         ▼
┌──────────────┐
│  Prometheus  │
└──────┬───────┘
       │
       │ PromQL
       ▼
┌──────────────┐
│    Grafana   │
└──────┬───────┘
       │
       ▼
   Dashboards
```

El objetivo es separar claramente las responsabilidades:

**Airflow genera las métricas → StatsD Exporter las transforma → Prometheus las almacena → Grafana las visualiza.**

Esta arquitectura permite disponer de una capa de observabilidad independiente de Airflow y facilita la creación de dashboards, análisis históricos y alertas sobre el estado y rendimiento de los workflows.