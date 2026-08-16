import json
from confluent_kafka import Consumer, KafkaException
from pymongo import MongoClient


KAFKA_BROKER = "kafka:9092"
KAFKA_TOPIC = "bitcoin-data"
KAFKA_GROUP_ID = "mongodb-saver"

MONGO_HOST = "mongodb"
MONGO_PORT = 27017
MONGO_DB = "bitcoin"
MONGO_COLLECTION = "prices"


consumer = Consumer({
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": KAFKA_GROUP_ID,
    "auto.offset.reset": "earliest"
})

consumer.subscribe([KAFKA_TOPIC])


def get_db_connection():
    client = MongoClient(
        host=MONGO_HOST,
        port=MONGO_PORT
    )

    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    return client, collection


def save_to_mongodb(data):
    client = None

    try:
        client, collection = get_db_connection()

        collection.insert_one(data)

        print(f"Guardado en MongoDB: {data.get('time', 'unknown')}")

    except Exception as e:
        print(f"Error al guardar en MongoDB: {e}")

    finally:
        if client:
            client.close()


if __name__ == "__main__":
    print("Esperando mensajes de Kafka para MongoDB")

    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaException._PARTITION_EOF:
                continue
            else:
                print(f"Error en Kafka: {msg.error()}")
                break

        data = json.loads(msg.value().decode("utf-8"))

        save_to_mongodb(data)