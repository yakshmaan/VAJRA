from datetime import datetime

# FEMA LRS limit: $250,000 per year per person
# Equivalent in INR at ~83 INR/USD
LRS_LIMIT_INR = 250000 * 83  # 20,750,000 INR

# Approved VAJRA corridors under FEMA
APPROVED_CORRIDORS = {'IN-UAE', 'IN-RU', 'IN-BR', 'IN-ZA', 'IN-CN', 'IN-SA'}

# Blocked purpose codes (FEMA restricted)
BLOCKED_PURPOSES = {'GAMBLING', 'ARMS', 'NARCOTICS'}

def validate(tx: dict) -> dict:
    """
    Runs FEMA compliance checks on a transaction.
    Returns the tx with compliance fields added.
    """
    errors = []

    # Check 1: Corridor approved
    if tx.get('corridor') not in APPROVED_CORRIDORS:
        errors.append(f"Corridor {tx.get('corridor')} not approved under FEMA")

    # Check 2: LRS limit
    if tx.get('amount', 0) > LRS_LIMIT_INR:
        errors.append(f"Amount {tx['amount']} exceeds FEMA LRS limit of {LRS_LIMIT_INR}")

    # Check 3: Purpose code
    purpose = tx.get('purpose', 'TRADE').upper()
    if purpose in BLOCKED_PURPOSES:
        errors.append(f"Purpose '{purpose}' is blocked under FEMA")

    # Check 4: Amount must be positive
    if tx.get('amount', 0) <= 0:
        errors.append("Amount must be positive")

    passed = len(errors) == 0

    return {
        **tx,
        'fema_cleared': passed,
        'fema_errors': errors,
        'fema_checked_at': datetime.utcnow().isoformat(),
        'compliance_proof': 'FEMA_CLEARED' if passed else 'FEMA_BLOCKED'
    }

if __name__ == "__main__":
    # Test cases
    tests = [
        {"tx_id": "T1", "corridor": "IN-UAE", "amount": 500000, "purpose": "TRADE"},
        {"tx_id": "T2", "corridor": "IN-US", "amount": 500000, "purpose": "TRADE"},
        {"tx_id": "T3", "corridor": "IN-RU", "amount": 25000000, "purpose": "TRADE"},
        {"tx_id": "T4", "corridor": "IN-UAE", "amount": 500000, "purpose": "GAMBLING"},
    ]

    for t in tests:
        result = validate(t)
        status = "✅ CLEARED" if result['fema_cleared'] else f"❌ BLOCKED: {result['fema_errors']}"
        print(f"[FEMA] {t['tx_id']} | {status}")