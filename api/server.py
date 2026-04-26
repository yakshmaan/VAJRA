import json
import sys
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from confluent_kafka import Producer

sys.path.append('/Users/apple/Documents/VAJRA')
from compliance.fema import validate as fema_validate
from saga.checkpoint import get, init_db
from economics.ssu import calculate_ssu

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

BOOTSTRAP = 'localhost:9092'

def get_producer():
    return Producer({'bootstrap.servers': BOOTSTRAP})

def emit(corridor, amount, currency='INR-e', purpose='TRADE'):
    p = get_producer()
    payload = {
        "tx_id": str(uuid.uuid4()),
        "amount": amount,
        "currency": currency,
        "corridor": corridor,
        "purpose": purpose,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "INITIATED"
    }
    p.produce(
        topic='vajra.payment.initiated',
        key=payload['tx_id'].encode(),
        value=json.dumps(payload).encode()
    )
    p.flush()
    return payload

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "VAJRA ONLINE", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    if not data:
        return jsonify({"error": "No payload"}), 400

    required = ['corridor', 'amount']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    check = fema_validate({
        "tx_id": "preflight",
        "corridor": data['corridor'],
        "amount": data['amount'],
        "purpose": data.get('purpose', 'TRADE')
    })

    if not check['fema_cleared']:
        return jsonify({
            "status": "REJECTED",
            "reason": check['fema_errors']
        }), 403

    tx = emit(
        corridor=data['corridor'],
        amount=data['amount'],
        currency=data.get('currency', 'INR-e'),
        purpose=data.get('purpose', 'TRADE')
    )

    return jsonify({
        "status": "ACCEPTED",
        "tx_id": tx['tx_id'],
        "corridor": tx['corridor'],
        "amount": tx['amount'],
        "currency": tx['currency']
    }), 202

@app.route('/api/status/<tx_id>', methods=['GET'])
def status(tx_id):
    tx = get(tx_id)
    if not tx:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(tx), 200

@app.route('/api/corridors', methods=['GET'])
def corridors():
    return jsonify({
        "approved_corridors": [
            "IN-UAE", "IN-RU", "IN-BR", "IN-ZA", "IN-CN", "IN-SA"
        ]
    })

@app.route('/api/ssu/<corridor>', methods=['GET'])
def ssu_rate(corridor):
    amount = request.args.get('amount', 1000000, type=float)
    result = calculate_ssu(corridor, amount)
    return jsonify(result), 200 if 'error' not in result else 400

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=8000, debug=True)