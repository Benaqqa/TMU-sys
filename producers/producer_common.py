"""
Producteurs communs (version corrigee) - configuration Kafka + Schema Registry (Confluent).
FIX IMPORTANT: ajout d'un gestionnaire de signal partage pour flush propre a l'arret.
"""
import os
import signal
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import Producer

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})


def make_avro_serializer(schema_path: str) -> AvroSerializer:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_str = f.read()
    return AvroSerializer(schema_registry_client, schema_str)


def make_producer() -> Producer:
    return Producer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "acks": "all",
        "enable.idempotence": True,
    })


def delivery_report(err, msg):
    if err is not None:
        print(f"[producer] ERREUR livraison: {err}")
    else:
        print(f"[producer] OK -> topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")


class GracefulShutdown:
    """FIX IMPORTANT: intercepte SIGTERM/SIGINT pour permettre un producer.flush() propre."""
    def __init__(self):
        self.should_stop = False
        signal.signal(signal.SIGTERM, self._handle)
        signal.signal(signal.SIGINT, self._handle)

    def _handle(self, *_):
        print("[producer] Signal d'arret recu, flush en cours avant sortie...")
        self.should_stop = True
