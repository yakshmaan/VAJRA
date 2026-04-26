import json
import uuid
from datetime import datetime
from confluent_kafka import Producer

BOOTSTRAP = 'localhost:9092'

def get_producer():
    return Producer({'bootstrap.servers': BOOTSTRAP})

def emit_payment_intent(amount: float, currency: str, corridor: str, entity_id: str):
    p = get_producer()
    payload = {
        "tx_id": str(uuid.uuid4()),
        "amount": amount,
        "currency": currency,
        "corridor": corridor,
        "entity_id": entity_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "INITIATED",
        "purpose": "TRADE"
    }
    p.produce(
        topic='vajra.payment.initiated',
        key=payload['tx_id'].encode(),
        value=json.dumps(payload).encode()
    )
    p.flush()
    print(f"⚡ [VAJRA] Emitted: {payload['tx_id']} | {corridor} | {amount} {currency} | {entity_id}")
    return payload['tx_id']

if __name__ == "__main__":
    emit_payment_intent(500000, "INR-e", "IN-UAE", "HDFC_BANK_001")
    emit_payment_intent(1200000, "INR-e", "IN-RU", "ROSNEFT_RU_007")