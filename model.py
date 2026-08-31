"""Core rent-vs-buy financial model engine.

All simulation, break-even, and metric helper logic lives here so both the
CLI (rent_vs_buy_model.py) and the interactive page (index.html via the
standalone JS port) can stay in sync.  Public API:

    simulate(params, house_growth) -> dict
    metric_buyer(result, basis)      -> float
    metric_renter(result, basis)     -> float
    break_even(params, basis="net")  -> float
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Parameter dataclass
# ---------------------------------------------------------------------------
def make_params(
    price: float = 600.0,
    down_pct: float = 30.0,
    years: int = 30,
    loan_rate: float = 3.0,
    rent0: float = 10.0,
    rent_growth: float = 0.0,
    invest_return: float = 5.0,
    invest_tax: float = 20.0,
    inflation: float = 3.0,
    print_speed: float = 4.0,
    holding_cost: float = 2.5,
    property_tax: float = 0.0,
    buy_cost_pct: float = 3.5,
    sell_cost_pct: float = 2.0,
    house_growth: float = 3.0,
):
    """Factory that returns a simple namespace compatible with simulate()."""
    class _P:
        pass
    p = _P()
    for k, v in {
        "price": price, "down_pct": down_pct, "years": years,
        "loan_rate": loan_rate, "rent0": rent0, "rent_growth": rent_growth,
        "invest_return": invest_return, "invest_tax": invest_tax,
        "inflation": inflation, "print_speed": print_speed,
        "holding_cost": holding_cost, "property_tax": property_tax,
        "buy_cost_pct": buy_cost_pct, "sell_cost_pct": sell_cost_pct,
        "house_growth": house_growth,
    }.items():
        setattr(p, k, v)
    return p


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def simulate(p, house_g: float) -> dict:
    """Month-by-month simulation for both strategies.

    Parameters
    ----------
    p : namespace-like object carrying all Params fields.
    house_g : assumed annual house appreciation in percent (e.g. 3.0 = 3%/yr).

    Returns
    -------
    dict with all intermediate and terminal metrics (see README §4 for field
    meanings).
    """
    D = p.price * p.down_pct / 100.0
    L = p.price - D
    n = p.years * 12
    mr = p.loan_rate / 100.0 / 12.0
    M = L * mr * (1 + mr) ** n / ((1 + mr) ** n - 1) if mr > 0 else L / n
    mrg = (1 + p.rent_growth / 100.0) ** (1 / 12.0) - 1
    mir = p.invest_return / 100.0 / 12.0
    pmt = p.print_speed / 100.0
    inf = p.inflation / 100.0
    buy_cost = p.price * p.buy_cost_pct / 100.0

    port = D
    rent_month = p.rent0 / 12.0
    contrib = D
    total_rent = 0.0
    total_buy_nom = D
    buyer_real_out = D
    renter_real_out = 0.0
    hold_tot = 0.0
    prop_tot = 0.0
    buyer_y1 = renter_y1 = buyer_y15 = renter_y15 = 0.0

    for t in range(1, n + 1):
        y_idx = (t - 1) // 12
        hm = p.holding_cost * (1 + inf) ** y_idx / 12.0
        cur_val = p.price * (1 + house_g / 100.0) ** y_idx
        ptm = cur_val * (p.property_tax / 100.0) / 12.0
        hold_tot += hm
        prop_tot += ptm
        buyer_real_out += (M + hm + ptm) / (1 + pmt) ** (t / 12.0)
        total_buy_nom += M
        total_rent += rent_month
        renter_real_out += rent_month / (1 + inf) ** (t / 12.0)
        contrib += (M - rent_month)
        port = port * (1 + mir) + (M - rent_month)
        rent_month *= (1 + mrg)
        if t == 12:
            buyer_y1 = M + hm + ptm
            renter_y1 = p.rent0 / 12.0
        if t == min(180, n):
            buyer_y15 = M + hm + ptm
            renter_y15 = p.rent0 / 12.0 * (1 + p.rent_growth / 100.0) ** 15

    house_val = p.price * (1 + house_g / 100.0) ** p.years
    sell_cost = house_val * p.sell_cost_pct / 100.0
    buyer_gross = house_val
    buyer_net = house_val - buy_cost - hold_tot - prop_tot - sell_cost
    gains = max(0.0, port - contrib)
    inv_tax = gains * p.invest_tax / 100.0
    renter_net = port - inv_tax
    rent_yield = p.rent0 / p.price * 100.0

    return {
        "down": D,
        "loan": L,
        "monthly_payment": M,
        "total_buy_nominal": total_buy_nom,
        "interest": total_buy_nom - D - L,
        "buy_cost": buy_cost,
        "holding_total": hold_tot,
        "property_tax_total": prop_tot,
        "house_value": house_val,
        "sell_cost": sell_cost,
        "buyer_gross": buyer_gross,
        "buyer_net": buyer_net,
        "rent_total": total_rent,
        "portfolio": port,
        "contributions": contrib,
        "gains": gains,
        "invest_tax": inv_tax,
        "renter_net": renter_net,
        "rent_yield": rent_yield,
        "buyer_real_out": buyer_real_out,
        "renter_real_out": renter_real_out,
        "buyer_y1": buyer_y1,
        "renter_y1": renter_y1,
        "buyer_y15": buyer_y15,
        "renter_y15": renter_y15,
    }


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------
def metric_buyer(r: dict, basis: str) -> float:
    return r["buyer_net"] if basis == "net" else r["buyer_gross"]


def metric_renter(r: dict, basis: str) -> float:
    return r["renter_net"] if basis == "net" else r["portfolio"]


# ---------------------------------------------------------------------------
# Break-even (bisection)
# ---------------------------------------------------------------------------
def break_even(p, basis: str = "net") -> float:
    """Annual house appreciation g* (percent) where buyer == renter wealth."""
    s0 = simulate(p, 0.0)
    target = s0["renter_net"] if basis == "net" else s0["portfolio"]
    lo, hi = -0.10, 0.30
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if basis == "net":
            bv = simulate(p, mid * 100.0)["buyer_net"]
        else:
            bv = p.price * (1 + mid) ** p.years
        if bv > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0 * 100.0
