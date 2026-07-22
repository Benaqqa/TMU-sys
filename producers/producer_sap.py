"""
Producteur simule (version corrigee) - transactions de vente SAP.
Publie sur le topic 'sap.ventes.raw' au format Avro, valide par le Schema Registry.
FIX IMPORTANT: gestion de signal + flush() a l'arret pour eviter la perte de messages en buffer.
"""
import os
import time
import uuid
import random
from datetime import datetime, timezone

from producer_common import make_avro_serializer, make_producer, delivery_report, GracefulShutdown
from confluent_kafka.serialization import SerializationContext, MessageField

TOPIC = "sap.ventes.raw"
SCHEMA_PATH = os.getenv("SCHEMA_PATH", "/schemas/sap_vente.avsc")
INTERVAL_SECONDS = float(os.getenv("PRODUCE_INTERVAL_SECONDS", "3"))

CLIENTS_VALIDES = ["CLI-0001", "CLI-0002"]
CONTRATS_VALIDES = ["CTR042", "CTR018"]
CLIENTS_INVALIDES = ["CLI-9999", "CLI-0000"]


def generer_transaction(injecter_erreur: bool = False) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    client = random.choice(CLIENTS_INVALIDES) if injecter_erreur else random.choice(CLIENTS_VALIDES)
    return {
        "transaction_id": str(uuid.uuid4()),
        "source_system": "SAP",
        "client_code": client,
        "contrat_code": random.choice(CONTRATS_VALIDES),
        "montant": round(random.uniform(1000, 50000), 2),
        "devise": "MAD",
        "date_vente": now,
        "emitted_at": now,
    }


def main():
    serializer = make_avro_serializer(SCHEMA_PATH)
    producer = make_producer()
    shutdown = GracefulShutdown()
    compteur = 0
    print(f"[producer-sap] Demarrage. Publication sur '{TOPIC}' toutes les {INTERVAL_SECONDS}s.")

    while not shutdown.should_stop:
        injecter_erreur = (compteur % 10 == 0 and compteur > 0)
        transaction = generer_transaction(injecter_erreur)
        value_bytes = serializer(
            transaction, SerializationContext(TOPIC, MessageField.VALUE)
        )
        producer.produce(
            topic=TOPIC,
            key=transaction["client_code"].encode("utf-8"),
            value=value_bytes,
            callback=delivery_report,
        )
        producer.poll(0)
        compteur += 1
        time.sleep(INTERVAL_SECONDS)

    print("[producer-sap] Flush final avant arret...")
    producer.flush(timeout=10)
    print("[producer-sap] Arret propre termine.")


if __name__ == "__main__":
    main()
