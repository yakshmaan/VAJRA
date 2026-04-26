import uuid
import random
from datetime import datetime, timedelta

# Simulated ICEGATE customs event types
LEO_STATUSES = ['GRANTED', 'PENDING', 'REJECTED', 'UNDER_INSPECTION']

# Simulated port codes
PORTS = {
    'IN-UAE': 'INNSA1',   # Nhava Sheva
    'IN-RU':  'INCHE1',   # Chennai
    'IN-BR':  'INMUN1',   # Mumbai
    'IN-ZA':  'INKOC1',   # Kochi
    'IN-CN':  'INKAL1',   # Kolkata
    'IN-SA':  'INKAN1',   # Kandla
}

def generate_bill_of_entry(corridor: str, amount: float) -> dict:
    """Simulate a Bill of Entry from ICEGATE"""
    return {
        "be_number": f"BE{uuid.uuid4().hex[:8].upper()}",
        "port_code": PORTS.get(corridor, 'INNSA1'),
        "corridor": corridor,
        "declared_value_inr": amount,
        "importer_iec": f"IEC{random.randint(1000000000, 9999999999)}",
        "goods_description": random.choice([
            "Industrial Machinery",
            "Electronic Components",
            "Pharmaceutical Raw Materials",
            "Textile Machinery",
            "Chemical Compounds"
        ]),
        "filing_date": datetime.utcnow().isoformat(),
        "assessed": True
    }

def generate_leo(corridor: str, amount: float, force_status: str = None) -> dict:
    """
    Simulate a Let Export Order (LEO) from ICEGATE.
    LEO is issued when goods are cleared for export.
    """
    # 80% chance of GRANTED in simulation
    weights = [80, 10, 5, 5]
    status = force_status or random.choices(LEO_STATUSES, weights=weights)[0]

    leo = {
        "leo_number": f"LEO{uuid.uuid4().hex[:8].upper()}",
        "shipping_bill_number": f"SB{random.randint(1000000, 9999999)}",
        "port_code": PORTS.get(corridor, 'INNSA1'),
        "corridor": corridor,
        "declared_value_inr": amount,
        "exporter_iec": f"IEC{random.randint(1000000000, 9999999999)}",
        "leo_status": status,
        "leo_granted": status == 'GRANTED',
        "customs_duty_paid": status == 'GRANTED',
        "goods_loaded": status == 'GRANTED',
        "clearance_timestamp": datetime.utcnow().isoformat(),
        "estimated_departure": (datetime.utcnow() + timedelta(hours=random.randint(2, 24))).isoformat()
    }

    return leo

def icegate_trigger(tx_id: str, corridor: str, amount: float) -> dict:
    """
    Main ICEGATE trigger — simulates customs clearance event.
    In production this would call real ICEGATE API.
    Returns whether payment should be released.
    """
    be = generate_bill_of_entry(corridor, amount)
    leo = generate_leo(corridor, amount)

    result = {
        "tx_id": tx_id,
        "corridor": corridor,
        "amount": amount,
        "bill_of_entry": be,
        "leo": leo,
        "payment_release_approved": leo['leo_granted'],
        "release_reason": "LEO GRANTED — Goods cleared by customs" if leo['leo_granted'] else f"HOLD — LEO Status: {leo['leo_status']}",
        "checked_at": datetime.utcnow().isoformat()
    }

    return result

if __name__ == "__main__":
    test_corridors = ['IN-UAE', 'IN-RU', 'IN-BR']
    for corridor in test_corridors:
        result = icegate_trigger("TX_TEST_001", corridor, 1200000)
        leo = result['leo']
        status = "✅ RELEASE" if result['payment_release_approved'] else "⏳ HOLD"
        print(f"\n{status} [{corridor}]")
        print(f"   LEO:     {leo['leo_number']}")
        print(f"   Port:    {leo['port_code']}")
        print(f"   Status:  {leo['leo_status']}")
        print(f"   Reason:  {result['release_reason']}")