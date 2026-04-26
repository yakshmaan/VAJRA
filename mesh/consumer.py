import json
from confluent_kafka import Consumer

BOOTSTRAP = 'localhost:9092'

def get_consumer():
    return Consumer({
        'bootstrap.servers': BOOTSTRAP,
        'group.id': 'vajra-saga-engine',
        'auto.offset.reset': 'earliest'
    })

def listen():
    c = get_consumer()
    c.subscribe(['vajra.payment.initiated'])
    print("⚡ [VAJRA] Saga Engine listening...")

    try:
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}")
                continue
            
            tx = json.loads(msg.value().decode())
            print(f"📥 [SAGA] Received: {tx['tx_id']} | {tx['corridor']} | {tx['amount']} {tx['currency']}")
            # Saga logic goes here next
            
    except KeyboardInterrupt:
        pass
    finally:
        c.close()

if __name__ == "__main__":
    listen()