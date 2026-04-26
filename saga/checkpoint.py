import json
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'dbname': 'vajra',
    'user': 'apple',
    'password': '',
    'host': 'localhost',
    'port': 5432
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saga_state (
            tx_id TEXT PRIMARY KEY,
            corridor TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            fx_rate NUMERIC,
            converted_amount NUMERIC,
            compliance_proof TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            payload JSONB
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ [CHECKPOINT] DB initialized")

def save(tx: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO saga_state (
            tx_id, corridor, amount, currency, status,
            fx_rate, converted_amount, compliance_proof, updated_at, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tx_id) DO UPDATE SET
            status = EXCLUDED.status,
            fx_rate = EXCLUDED.fx_rate,
            converted_amount = EXCLUDED.converted_amount,
            updated_at = NOW(),
            payload = EXCLUDED.payload
    """, (
        tx['tx_id'],
        tx['corridor'],
        tx['amount'],
        tx['currency'],
        tx['status'],
        tx.get('fx_rate'),
        tx.get('converted_amount'),
        tx.get('compliance_proof'),
        datetime.utcnow(),
        json.dumps(tx)
    ))
    conn.commit()
    cur.close()
    conn.close()
    print(f"💾 [CHECKPOINT] Saved: {tx['tx_id']} | {tx['status']}")

def get(tx_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT payload FROM saga_state WHERE tx_id = %s", (tx_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    init_db()