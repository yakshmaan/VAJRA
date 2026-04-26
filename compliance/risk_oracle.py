import random
import hashlib
from datetime import datetime

# Scoring weights
WEIGHTS = {
    'transaction_history': 0.30,
    'customs_compliance':  0.25,
    'gst_score':          0.20,
    'corridor_risk':      0.15,
    'account_age':        0.10,
}

# Corridor risk multipliers (lower = riskier)
CORRIDOR_RISK = {
    'IN-UAE': 0.95,
    'IN-SA':  0.90,
    'IN-BR':  0.80,
    'IN-ZA':  0.78,
    'IN-CN':  0.72,
    'IN-RU':  0.65,
}

# Trust tiers
TIERS = [
    (90, 'SOVEREIGN',  '🟢'),
    (75, 'TRUSTED',    '🔵'),
    (60, 'VERIFIED',   '🟡'),
    (40, 'MONITORED',  '🟠'),
    (0,  'RESTRICTED', '🔴'),
]

def get_tier(score: float) -> tuple:
    for threshold, label, icon in TIERS:
        if score >= threshold:
            return label, icon
    return 'RESTRICTED', '🔴'

def simulate_gstn_score(entity_id: str) -> float:
    """Simulate GSTN compliance score 0-100"""
    seed = int(hashlib.md5(entity_id.encode()).hexdigest(), 16) % 1000
    random.seed(seed)
    return round(random.uniform(55, 98), 2)

def simulate_customs_score(entity_id: str) -> float:
    """Simulate ICEGATE customs compliance score"""
    seed = int(hashlib.md5((entity_id + 'customs').encode()).hexdigest(), 16) % 1000
    random.seed(seed)
    return round(random.uniform(60, 99), 2)

def simulate_tx_history_score(entity_id: str) -> float:
    """Simulate transaction history score"""
    seed = int(hashlib.md5((entity_id + 'tx').encode()).hexdigest(), 16) % 1000
    random.seed(seed)
    return round(random.uniform(50, 100), 2)

def simulate_account_age_score(entity_id: str) -> float:
    """Simulate account age score (older = more trusted)"""
    seed = int(hashlib.md5((entity_id + 'age').encode()).hexdigest(), 16) % 1000
    random.seed(seed)
    return round(random.uniform(40, 100), 2)

def calculate_trust_score(entity_id: str, corridor: str) -> dict:
    """
    Calculate Vajra Trust Score for a trading entity.
    Replaces Moody's/S&P ratings with India-native data.
    """
    tx_score       = simulate_tx_history_score(entity_id)
    customs_score  = simulate_customs_score(entity_id)
    gst_score      = simulate_gstn_score(entity_id)
    corridor_mult  = CORRIDOR_RISK.get(corridor, 0.70)
    account_score  = simulate_account_age_score(entity_id)

    # Weighted score
    raw_score = (
        tx_score      * WEIGHTS['transaction_history'] +
        customs_score * WEIGHTS['customs_compliance'] +
        gst_score     * WEIGHTS['gst_score'] +
        account_score * WEIGHTS['account_age']
    )

    # Apply corridor risk multiplier
    final_score = round(raw_score * corridor_mult, 2)
    tier, icon = get_tier(final_score)

    return {
        "entity_id": entity_id,
        "corridor": corridor,
        "vajra_trust_score": final_score,
        "tier": tier,
        "tier_icon": icon,
        "components": {
            "transaction_history": tx_score,
            "customs_compliance": customs_score,
            "gst_score": gst_score,
            "account_age": account_score,
            "corridor_risk_multiplier": corridor_mult
        },
        "weights": WEIGHTS,
        "payment_limit_inr": _get_limit(final_score),
        "requires_manual_review": final_score < 60,
        "calculated_at": datetime.utcnow().isoformat()
    }

def _get_limit(score: float) -> int:
    if score >= 90: return 100_000_000   # 10 Cr
    if score >= 75: return 50_000_000    # 5 Cr
    if score >= 60: return 10_000_000    # 1 Cr
    if score >= 40: return 1_000_000     # 10 L
    return 0                              # BLOCKED

if __name__ == "__main__":
    entities = [
        ("HDFC_BANK_001", "IN-UAE"),
        ("ROSNEFT_RU_007", "IN-RU"),
        ("PETROBRAS_BR_042", "IN-BR"),
        ("UNKNOWN_ENTITY_999", "IN-RU"),
    ]

    for entity_id, corridor in entities:
        r = calculate_trust_score(entity_id, corridor)
        print(f"\n{r['tier_icon']} [{r['tier']}] {entity_id}")
        print(f"   Vajra Score:  {r['vajra_trust_score']}/100")
        print(f"   Corridor:     {corridor}")
        print(f"   Limit:        ₹{r['payment_limit_inr']:,}")
        print(f"   Manual:       {'YES' if r['requires_manual_review'] else 'NO'}")
        print(f"   GST:          {r['components']['gst_score']}")
        print(f"   Customs:      {r['components']['customs_compliance']}")
        print(f"   TX History:   {r['components']['transaction_history']}")