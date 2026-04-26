import json
import sys
from datetime import datetime
from confluent_kafka import Producer, Consumer

sys.path.append('/Users/apple/Documents/VAJRA')
from compliance.fema import validate as fema_validate
from compliance.icegate import icegate_trigger
from compliance.risk_oracle import calculate_trust_score
from security.pqc import secure_tx
from checkpoint import save
from economics.ssu import calculate_ssu

BOOTSTRAP = 'localhost:9092'

TOPICS = {
    'initiated': 'vajra.payment.initiated',
    'fx_locked': 'vajra.payment.fx_locked',
    'settled':   'vajra.payment.settled',
    'failed':    'vajra.payment.failed',
    'saga_state':'vajra.saga.state'
}

SSU_CORRIDORS = {'IN-RU', 'IN-BR', 'IN-ZA', 'IN-CN'}
FX_RATES = {'IN-UAE': 0.011, 'IN-SA': 0.012}

def get_producer():
    return Producer({'bootstrap.servers': BOOTSTRAP})

def emit(producer, topic, tx_id, payload):
    producer.produce(
        topic=topic,
        key=tx_id.encode(),
        value=json.dumps(payload).encode()
    )
    producer.flush()

def pqc_handshake(tx: dict) -> dict:
    print(f"🔐 [PQC] Securing handshake for {tx['tx_id']}...")
    secured = secure_tx(tx)
    print(f"✅ [PQC] Kyber-768 + Dilithium3 | Latency: {secured['pqc_latency_ms']}ms | Quantum Safe: True")
    return secured

def risk_check(tx: dict, producer) -> dict:
    entity_id = tx.get('entity_id', f"ENTITY_{tx['tx_id'][:8]}")
    corridor = tx['corridor']
    amount = tx['amount']

    print(f"🧠 [RISK] Calculating Vajra Trust Score for {entity_id}...")
    risk = calculate_trust_score(entity_id, corridor)

    if risk['tier'] == 'RESTRICTED':
        raise Exception(f"RISK BLOCKED: {entity_id} is RESTRICTED | Score: {risk['vajra_trust_score']}")

    if amount > risk['payment_limit_inr']:
        raise Exception(f"RISK BLOCKED: ₹{amount:,} exceeds limit ₹{risk['payment_limit_inr']:,} for {risk['tier']} tier")

    updated = {
        **tx,
        'entity_id': entity_id,
        'vajra_trust_score': risk['vajra_trust_score'],
        'trust_tier': risk['tier'],
        'payment_limit_inr': risk['payment_limit_inr'],
        'risk_checked_at': datetime.utcnow().isoformat()
    }

    print(f"✅ [RISK] {risk['tier_icon']} {entity_id} | Score: {risk['vajra_trust_score']} | Tier: {risk['tier']}")
    return updated

def lock_fx(tx: dict, producer) -> dict:
    corridor = tx['corridor']
    amount = tx['amount']

    if corridor in SSU_CORRIDORS:
        ssu = calculate_ssu(corridor, amount)
        updated = {
            **tx,
            'status': 'FX_LOCKED',
            'settlement_type': 'SSU',
            'ssu_units': ssu['ssu_units'],
            'ssu_rate': ssu['ssu_rate'],
            'blended_yield': ssu['blended_yield_pct'],
            'gold_oz': ssu['gold_oz_equivalent'],
            'fx_locked_at': datetime.utcnow().isoformat()
        }
        emit(producer, TOPICS['fx_locked'], tx['tx_id'], updated)
        save(updated)
        print(f"🔒 [SAGA] SSU Locked: {tx['tx_id']} | {ssu['ssu_units']} SSU | Yield: {ssu['blended_yield_pct']}%")
    else:
        rate = FX_RATES.get(corridor, 0.011)
        converted = amount * rate
        updated = {
            **tx,
            'status': 'FX_LOCKED',
            'settlement_type': 'FX',
            'fx_rate': rate,
            'converted_amount': round(converted, 4),
            'fx_locked_at': datetime.utcnow().isoformat()
        }
        emit(producer, TOPICS['fx_locked'], tx['tx_id'], updated)
        save(updated)
        print(f"🔒 [SAGA] FX Locked: {tx['tx_id']} | Rate: {rate} | Converted: {converted:.4f}")

    return updated

def icegate_check(tx: dict, producer) -> dict:
    print(f"🛃 [ICEGATE] Checking customs clearance for {tx['tx_id']}...")
    result = icegate_trigger(tx['tx_id'], tx['corridor'], tx['amount'])
    leo = result['leo']

    if not result['payment_release_approved']:
        raise Exception(f"ICEGATE HOLD: {result['release_reason']}")

    updated = {
        **tx,
        'icegate_cleared': True,
        'leo_number': leo['leo_number'],
        'leo_status': leo['leo_status'],
        'port_code': leo['port_code'],
        'icegate_checked_at': datetime.utcnow().isoformat()
    }
    print(f"✅ [ICEGATE] Cleared: {leo['leo_number']} | Port: {leo['port_code']}")
    return updated

def settle(tx: dict, producer) -> dict:
    updated = {
        **tx,
        'status': 'SETTLED',
        'settled_at': datetime.utcnow().isoformat()
    }
    emit(producer, TOPICS['settled'], tx['tx_id'], updated)
    save(updated)
    print(f"✅ [SAGA] Settled: {tx['tx_id']} | {tx['corridor']} | {tx['amount']} INR-e")
    return updated

def compensate(tx: dict, producer, reason: str) -> dict:
    updated = {
        **tx,
        'status': 'COMPENSATED',
        'reason': reason,
        'compensated_at': datetime.utcnow().isoformat()
    }
    emit(producer, TOPICS['failed'], tx['tx_id'], updated)
    save(updated)
    print(f"❌ [SAGA] Compensated: {tx['tx_id']} | Reason: {reason}")
    return updated

def process(tx: dict, producer):
    print(f"\n⚡ [SAGA] Processing: {tx['tx_id']} | {tx['corridor']} | {tx['amount']} INR-e")

    tx = fema_validate(tx)
    save({**tx, 'status': 'INITIATED'})

    if not tx['fema_cleared']:
        compensate(tx, producer, f"FEMA BLOCKED: {tx['fema_errors']}")
        return

    try:
        tx = pqc_handshake(tx)
        tx = risk_check(tx, producer)
        tx = lock_fx(tx, producer)
        tx = icegate_check(tx, producer)
        tx = settle(tx, producer)
    except Exception as e:
        compensate(tx, producer, str(e))

def run():
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP,
        'group.id': 'vajra-saga-processor-v7',
        'auto.offset.reset': 'latest'
    })
    producer = get_producer()
    consumer.subscribe([TOPICS['initiated']])
    print("⚡ [VAJRA SAGA ENGINE] Full Stack — PQC + Risk + ICEGATE + SSU + FEMA + Postgres...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}")
                continue
            tx = json.loads(msg.value().decode())
            process(tx, producer)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    run()