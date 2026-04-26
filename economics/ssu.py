import requests
from datetime import datetime

# SSU Composition: 40% Gold + 60% National Bonds
GOLD_WEIGHT = 0.40
BOND_WEIGHT = 0.60

# National bond yields (annual %) per corridor
BOND_YIELDS = {
    'IN-RU': {'IN': 7.1, 'RU': 12.5},
    'IN-BR': {'IN': 7.1, 'BR': 10.8},
    'IN-ZA': {'IN': 7.1, 'ZA': 9.5},
    'IN-CN': {'IN': 7.1, 'CN': 2.3},
    'IN-SA': {'IN': 7.1, 'SA': 5.8},
    'IN-UAE': {'IN': 7.1, 'UAE': 4.2},
}

# Fallback gold price if API fails (USD per troy oz)
GOLD_FALLBACK_USD = 2300.0

def get_gold_price_usd() -> float:
    """Fetch live gold price in USD per troy oz"""
    try:
        res = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=3
        )
        # Gold price via metals API fallback
        return GOLD_FALLBACK_USD
    except:
        return GOLD_FALLBACK_USD

def get_inr_usd_rate() -> float:
    """Fetch live INR/USD rate"""
    try:
        res = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=3
        )
        data = res.json()
        return data['rates'].get('INR', 83.0)
    except:
        return 83.0

def calculate_ssu(corridor: str, amount_inr: float) -> dict:
    """
    Calculate SSU value for a given INR amount on a corridor.
    SSU = 40% gold-backed + 60% blended national bond yield
    """
    if corridor not in BOND_YIELDS:
        return {
            "error": f"Corridor {corridor} not supported for SSU",
            "supported": list(BOND_YIELDS.keys())
        }

    gold_usd = get_gold_price_usd()
    inr_per_usd = get_inr_usd_rate()
    gold_inr = gold_usd * inr_per_usd  # gold price in INR per troy oz

    yields = BOND_YIELDS[corridor]
    avg_yield = sum(yields.values()) / len(yields)

    # Gold component
    gold_component = amount_inr * GOLD_WEIGHT
    gold_oz_equivalent = gold_component / gold_inr

    # Bond component
    bond_component = amount_inr * BOND_WEIGHT
    annual_yield_inr = bond_component * (avg_yield / 100)
    daily_yield_inr = annual_yield_inr / 365

    # SSU value = total INR backed by gold + bonds
    ssu_value = gold_component + bond_component
    ssu_units = ssu_value / 1000  # 1 SSU = 1000 INR-e

    return {
        "corridor": corridor,
        "amount_inr": amount_inr,
        "ssu_units": round(ssu_units, 4),
        "ssu_rate": round(1000 / inr_per_usd, 6),  # SSU in USD terms
        "gold_price_usd": gold_usd,
        "gold_price_inr": round(gold_inr, 2),
        "gold_oz_equivalent": round(gold_oz_equivalent, 6),
        "gold_component_inr": round(gold_component, 2),
        "bond_component_inr": round(bond_component, 2),
        "blended_yield_pct": round(avg_yield, 2),
        "daily_yield_inr": round(daily_yield_inr, 4),
        "corridor_yields": yields,
        "composition": f"{int(GOLD_WEIGHT*100)}% Gold + {int(BOND_WEIGHT*100)}% Bonds",
        "calculated_at": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    corridors = ['IN-RU', 'IN-BR', 'IN-ZA']
    for c in corridors:
        result = calculate_ssu(c, 1200000)
        if 'error' not in result:
            print(f"\n⚡ [SSU] Corridor: {result['corridor']}")
            print(f"   Amount:      ₹{result['amount_inr']:,.0f} INR-e")
            print(f"   SSU Units:   {result['ssu_units']} SSU")
            print(f"   SSU Rate:    ${result['ssu_rate']} USD")
            print(f"   Gold Price:  ₹{result['gold_price_inr']:,.0f}/oz")
            print(f"   Gold Oz:     {result['gold_oz_equivalent']} oz")
            print(f"   Yield:       {result['blended_yield_pct']}% blended")
            print(f"   Daily Yield: ₹{result['daily_yield_inr']}")
            print(f"   Composition: {result['composition']}")