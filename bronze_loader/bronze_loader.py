"""
Bronze Loader (version corrigee) - consomme les topics Avro Kafka (via Schema Registry)
et ecrit les messages bruts, sans transformation, en Parquet dans le Data Lake (couche Bronze).

Corrections appliquees suite a l'audit technique:
  - FIX CRITIQUE: enable.auto.commit=False, commit manuel uniquement apres ecriture Parquet confirmee
  - FIX IMPORTANT: gestion des erreurs de deserialisation Avro -> Dead Letter Queue (DLQ) locale
  - FIX MINEUR: minuteur de flush independant par topic (au lieu d'un minuteur global partage)
"""
import os
import json
import signal
from datetime import datetime, timezone
from collections import defaultdict

import pandas as pd
from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPICS = ["sap.ventes.raw", "oracle.charges.raw"]
BRONZE_ROOT = os.getenv("BRONZE_ROOT", "/data/bronze")
DLQ_ROOT = os.getenv("DLQ_ROOT", "/data/dlq")
FLUSH_INTERVAL_MESSAGES = int(os.getenv("FLUSH_INTERVAL_MESSAGES", "5"))
FLUSH_INTERVAL_SECONDS = int(os.getenv("FLUSH_INTERVAL_SECONDS", "15"))

schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
avro_deserializer = AvroDeserializer(schema_registry_client)

running = True


def handle_sigterm(*_):
    global running
    print("[bronze-loader] Signal d'arret recu, fermeture propre...")
    running = False


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


def topic_to_folder(topic: str) -> str:
    return topic.replace(".raw", "").replace(".", "_")


def write_batch_to_bronze(topic: str, records: list) -> bool:
    """Ecrit un lot en Parquet. Retourne True si l'ecriture a reussi (donc commit-able)."""
    if not records:
        return True
    try:
        folder = topic_to_folder(topic)
        now = datetime.now(timezone.utc)
        partition_path = os.path.join(
            BRONZE_ROOT, folder,
            f"annee={now.year}", f"mois={now.month:02d}", f"jour={now.day:02d}"
        )
        os.makedirs(partition_path, exist_ok=True)

        df = pd.DataFrame(records)
        filename = f"batch_{now.strftime('%Y%m%dT%H%M%S')}_{len(records)}rows.parquet"
        filepath = os.path.join(partition_path, filename)
        df.to_parquet(filepath, engine="pyarrow", index=False)
        print(f"[bronze-loader] Ecrit {len(records)} lignes -> {filepath}")
        return True
    except Exception as e:
        print(f"[bronze-loader] ERREUR ecriture Parquet pour {topic}: {e}")
        return False


def write_to_dlq(topic: str, raw_bytes: bytes, error: str, kafka_offset: int, kafka_partition: int):
    """FIX IMPORTANT: isole les messages non deserialisables au lieu de crasher le pipeline."""
    try:
        now = datetime.now(timezone.utc)
        dlq_path = os.path.join(DLQ_ROOT, topic_to_folder(topic))
        os.makedirs(dlq_path, exist_ok=True)
        filename = f"dlq_{now.strftime('%Y%m%dT%H%M%S%f')}_offset{kafka_offset}.json"
        record = {
            "topic": topic,
            "partition": kafka_partition,
            "offset": kafka_offset,
            "error": error,
            "raw_bytes_hex": raw_bytes.hex() if raw_bytes else None,
            "dlq_written_at": now.isoformat(),
        }
        with open(os.path.join(dlq_path, filename), "w", encoding="utf-8") as f:
            json.dump(record, f)
        print(f"[bronze-loader] Message illisible isole en DLQ -> {filename} (motif: {error})")
    except Exception as e:
        print(f"[bronze-loader] ERREUR CRITIQUE: impossible d'ecrire en DLQ: {e}")


def main():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": "bronze-loader-group",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe(TOPICS)
    print(f"[bronze-loader] Abonne aux topics: {TOPICS} (commit manuel active)")

    buffers = defaultdict(list)
    pending_offsets = defaultdict(list)
    last_flush_per_topic = {t: datetime.now(timezone.utc) for t in TOPICS}

    def flush_topic(topic: str):
        success = write_batch_to_bronze(topic, buffers[topic])
        if success:
            for partition, offset in pending_offsets[topic]:
                consumer.commit(offsets=[TopicPartition(topic, partition, offset + 1)], asynchronous=False)
            buffers[topic] = []
            pending_offsets[topic] = []
            last_flush_per_topic[topic] = datetime.now(timezone.utc)
        else:
            print(f"[bronze-loader] Flush {topic} echoue, offsets NON commites, nouvel essai au prochain cycle.")

    try:
        while running:
            msg = consumer.poll(1.0)

            if msg is not None and msg.error() is None:
                topic = msg.topic()
                try:
                    value = avro_deserializer(
                        msg.value(), SerializationContext(topic, MessageField.VALUE)
                    )
                except Exception as e:
                    write_to_dlq(topic, msg.value(), str(e), msg.offset(), msg.partition())
                    consumer.commit(offsets=[TopicPartition(topic, msg.partition(), msg.offset() + 1)], asynchronous=False)
                    continue

                if value is not None:
                    now = datetime.now(timezone.utc)
                    value["_kafka_offset"] = msg.offset()
                    value["_kafka_partition"] = msg.partition()
                    value["_kafka_topic"] = topic
                    value["_ingested_at_bronze"] = now.isoformat()
                    buffers[topic].append(value)
                    pending_offsets[topic].append((msg.partition(), msg.offset()))

            elif msg is not None and msg.error():
                print(f"[bronze-loader] Erreur consumer: {msg.error()}")

            now = datetime.now(timezone.utc)
            for topic in TOPICS:
                elapsed = (now - last_flush_per_topic[topic]).total_seconds()
                if len(buffers[topic]) >= FLUSH_INTERVAL_MESSAGES or (elapsed >= FLUSH_INTERVAL_SECONDS and buffers[topic]):
                    flush_topic(topic)

    finally:
        for topic in TOPICS:
            flush_topic(topic)
        consumer.close()
        print("[bronze-loader] Arret propre termine.")


if __name__ == "__main__":
    main()
