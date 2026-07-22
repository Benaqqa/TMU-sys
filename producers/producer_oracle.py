"""
Producteur simule (version corrigee) - charges/achats Oracle.
Publie sur le topic 'oracle.charges.raw' au format Avro, valide par le Schema Registry.
FIX IMPORTANT: gestion de signal + flush() a l'arret pour eviter la perte de messages en buffer.
"""
import os
import time
import uuid
import random
from datetime import datetime, timezone

from producer_common import make_avro_serializer, make_producer, delivery_report, GracefulShutdown
from confluent_kafka.serialization import SerializationContext, MessageField

TOPIC = "oracle.charges.raw"
SCHEMA_PATH = os.getenv("SCHEMA_PATH", "/schemas/oracle_charge.avsc")
INTERVAL_SECONDS = float(os.getenv("PRODUCE_INTERVAL_SECONDS", "4"))

COMPTES_VALIDES = ["601100", "602200", "604100", "641100", "681100"]
FOURNISSEURS = ["ONEE", "SRM", "Fournisseur Technique SARL", "PPA EnR Partner"]


def generer_charge() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "transaction_id": str(uuid.uuid4()),
        "source_system": "ORACLE",
        "fournisseur": random.choice(FOURNISSEURS),
        "compte_general": random.choice(COMPTES_VALIDES),
        "montant": round(random.uniform(500, 20000), 2),
        "devise": "MAD",
        "date_charge": now,
        "emitted_at": now,
    }


def main():
    serializer = make_avro_serializer(SCHEMA_PATH)
    producer = make_producer()
    shutdown = GracefulShutdown()
    print(f"[producer-oracle] Demarrage. Publication sur '{TOPIC}' toutes les {INTERVAL_SECONDS}s.")

    while not shutdown.should_stop:
        charge = generer_charge()
        value_bytes = serializer(
            charge, SerializationContext(TOPIC, MessageField.VALUE)
        )
        producer.produce(
            topic=TOPIC,
            key=charge["compte_general"].encode("utf-8"),
            value=value_bytes,
            callback=delivery_report,
        )
        producer.poll(0)
        time.sleep(INTERVAL_SECONDS)

    print("[producer-oracle] Flush final avant arret...")
    producer.flush(timeout=10)
    print("[producer-oracle] Arret propre termine.")


if __name__ == "__main__":
    main()
