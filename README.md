# VAJRA ⚡ — Sovereign Settlement Rail

> A post-dollar, quantum-resistant payment infrastructure for BRICS+ trade corridors.

## What is VAJRA?

VAJRA is an open-source sovereign settlement rail built to enable trade between India and BRICS+ nations (UAE, Russia, Brazil, South Africa, China, Saudi Arabia) without routing through the US Dollar or SWIFT.

Every transaction on VAJRA goes through a 5-layer verification pipeline:

```
FEMA Oracle → PQC Handshake → Risk Oracle → SSU/FX Lock → ICEGATE → Settlement
```

## Architecture

### 1. Redpanda Mesh (Persistence Layer)
- Raft-native Kafka alternative as the global Write-Ahead Log
- Every payment intent is persisted before execution
- Crash-safe — no transaction is ever lost

### 2. Saga Choreography Engine (Orchestration Layer)
- Replaces 2-phase commit with optimistic execution
- Automatic compensating transactions on failure
- Full state checkpointed to Postgres at every step

### 3. FEMA Oracle (Compliance Layer)
- Programmable law engine
- Validates every transaction against India's Foreign Exchange Management Act in real-time
- Blocks unauthorized corridors, purpose codes, and LRS limit breaches

### 4. AI Risk Oracle (Trust Layer)
- Replaces Moody's/S&P with India-native Vajra Trust Score
- Scores entities using GST compliance, customs history, transaction history
- 5 tiers: SOVEREIGN → TRUSTED → VERIFIED → MONITORED → RESTRICTED
- Dynamic payment limits per tier

### 5. SSU Mint (Settlement Layer)
- Synthetic Settlement Unit: 40% Gold + 60% National Bonds
- Used for disconnected corridors (IN-RU, IN-BR, IN-ZA, IN-CN)
- Eliminates dollar dependency for BRICS+ trade
- Live blended yield calculation per corridor

### 6. ICEGATE Integration (Trade Finance Layer)
- Payment released only on customs clearance event
- Simulates real ICEGATE LEO (Let Export Order) and Bill of Entry
- Turns VAJRA into smart trade finance, not just a payment system

### 7. Post-Quantum Cryptography (Security Layer)
- CRYSTALS-Kyber-768 for key encapsulation
- CRYSTALS-Dilithium3 for digital signatures
- Sub-millisecond handshake latency
- Quantum-computer resistant by design

### 8. Flask REST API

| Endpoint | Method | Description |
|---|---|---|
| /api/health | GET | System status |
| /api/send | POST | Initiate a payment |
| /api/status/\<tx_id\> | GET | Transaction status |
| /api/corridors | GET | Approved corridors |
| /api/ssu/\<corridor\> | GET | SSU rate for corridor |

### 9. Live Operations Dashboard
- Real-time transaction feed
- FEMA Oracle log
- Corridor activity heatmap
- KPIs: settled count, volume, blocked transactions

## Transaction Flow

```
Producer emits intent
       ↓
Redpanda WAL (persisted)
       ↓
FEMA Oracle — is this corridor/purpose legal?
       ↓
PQC Handshake — Kyber + Dilithium encryption
       ↓
Risk Oracle — what is the entity's Vajra Trust Score?
       ↓
SSU/FX Lock — settle in SSU (BRICS) or FX (Gulf)
       ↓
ICEGATE — are goods cleared by Indian Customs?
       ↓
SETTLED (checkpointed to Postgres)
```

## Supported Corridors

| Corridor | Settlement | Yield |
|---|---|---|
| IN-UAE | FX (AED) | — |
| IN-SA | FX (SAR) | — |
| IN-RU | SSU | 9.8% blended |
| IN-BR | SSU | 8.95% blended |
| IN-ZA | SSU | 8.3% blended |
| IN-CN | SSU | 4.7% blended |

## Tech Stack

- **Messaging**: Redpanda (Raft-native Kafka)
- **Orchestration**: Python Saga pattern
- **Database**: PostgreSQL 15
- **API**: Flask
- **Crypto**: SHA3-256/512 (PQC simulation, production uses liboqs)
- **Compliance**: FEMA, ISO 20022 compatible

## Running Locally

### Prerequisites
- Docker Desktop
- Python 3.10+
- PostgreSQL 15

### Setup

```bash
# 1. Start Redpanda
docker run -d --name VAJRA_CORE \
  -p 9092:9092 -p 9644:9644 \
  docker.redpanda.com/redpandadata/redpanda:latest \
  redpanda start --overprovisioned --smp 1 --memory 1G \
  --reserve-memory 0M --node-id 0 --check=false

# 2. Create topics
docker exec VAJRA_CORE rpk topic create \
  vajra.payment.initiated vajra.payment.fx_locked \
  vajra.payment.settled vajra.payment.failed \
  vajra.saga.state --partitions 3 --replicas 1

# 3. Create Postgres database
psql postgres -c "CREATE DATABASE vajra;"

# 4. Install dependencies
pip3 install confluent-kafka flask flask-cors psycopg2-binary requests

# 5. Start API
python3 api/server.py

# 6. Start Saga Engine
python3 saga/engine.py

# 7. Send a test transaction
curl -X POST http://localhost:8000/api/send \
  -H "Content-Type: application/json" \
  -d '{"corridor": "IN-UAE", "amount": 500000, "entity_id": "HDFC_BANK_001"}'

# 8. Open dashboard
open dashboard/index.html
```

## Project Structure

```
VAJRA/
├── mesh/
│   ├── producer.py          # Payment intent emitter
│   └── consumer.py          # Basic mesh consumer
├── saga/
│   ├── engine.py            # Main saga orchestrator
│   └── checkpoint.py        # Postgres persistence
├── compliance/
│   ├── fema.py              # FEMA Oracle
│   ├── icegate.py           # Customs clearance mock
│   └── risk_oracle.py       # Vajra Trust Score engine
├── economics/
│   └── ssu.py               # SSU Mint (gold+bond)
├── security/
│   └── pqc.py               # PQC simulation (Kyber+Dilithium)
├── api/
│   └── server.py            # Flask REST API
├── dashboard/
│   └── index.html           # Live operations dashboard
└── README.md
```

## Built By

Yaksh — 2nd semester BTech CS student, Ludhiana, India.
Built as a portfolio project and proof-of-concept for sovereign financial infrastructure.

> *"We aren't building a fast payment app. We are building the digital backbone of a multipolar financial world."*
