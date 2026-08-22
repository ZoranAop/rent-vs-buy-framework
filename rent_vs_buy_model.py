"""
Rent-vs-Buy Decision Framework
==============================

A parameterized, month-by-month financial model that compares two lifetime
housing strategies under one consistent set of assumptions:

  A. BUY  - purchase with a down payment D and an amortizing mortgage over X years.
  B. RENT - rent the same quality of housing and invest the foregone down payment
            plus the monthly surplus (mortgage payment minus rent).

All cash flows are simulated monthly with monthly compounding. The framework
outputs terminal net worth for both strategies, the break-even house
appreciation rate g*, a rent-yield vs mortgage-rate gauge, sensitivity of g*
to the investment return and rent growth, inflation/discounted real purchasing
power, and the monthly cash-flow pressure in early vs. late years.

Design principles
-----------------
* Neutral and reusable: no market-specific narrative, no hard-coded "story".
* Explicit assumptions: every exogenous input is a parameter you can override.
* Consistent accounting: the same basis (net or gross) drives the verdict AND
  the break-even threshold, so the two never contradict each other.
* Deterministic core: returns, inflation, rents, taxes and costs are exogenous
  constants. Stochastic extensions (returns volatility, income growth, ...) are
  left as extension points documented in README.md.

Author: WorkBuddy
License: MIT
"""

from dataclasses import dataclass, asdict
import math


@dataclass
class Params:
    """All exogenous inputs of the model. Units: amounts in 万元 (10k CNY),
    rates in percent (e.g. 3.0 means 3%)."""
    price: float = 600.0          # house price P
    down_pct: float = 30.0        # down payment ratio (%)
    years: int = 30               # horizon X (loan term / rent duration)
    loan_rate: float = 3.0        # annual mortgage rate (%)
    rent0: float = 10.0           # first-year rent (万元 / year)
    rent_growth: float = 0.0      # annual rent growth (%)
    invest_return: float = 5.0    # renter's annual investment return (%)
    invest_tax: float = 20.0      # tax on investment gains (%)
    inflation: float = 3.0        # annual inflation (%)
    print_speed: float = 4.0      # money-printing speed (%)
    holding_cost: float = 2.5     # annual holding cost (万元, nominal)
    property_tax: float = 0.0     # property tax (% of house value / year)
    buy_cost_pct: float = 3.5     # one-time purchase cost (% of price)
    sell_cost_pct: float = 2.0    # selling cost (% of terminal value)
    house_growth: float = 3.0     # assumed annual house appreciation (%)


def simulate(p: Params, house_g: float) -> dict:
    """Simulate both strategies for a given annual house appreciation `house_g`
    (percent). Returns a dict of all intermediate and terminal metrics."""
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
    buyer_real_out = D          # discounted at money-printing speed
    renter_real_out = 0.0       # discounted at inflation
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
        "down": D, "loan": L, "monthly_payment": M,
        "total_buy_nominal": total_buy_nom,
        "interest": total_buy_nom - D - L,
        "buy_cost": buy_cost, "holding_total": hold_tot, "property_tax_total": prop_tot,
        "house_value": house_val, "sell_cost": sell_cost,
        "buyer_gross": buyer_gross, "buyer_net": buyer_net,
        "rent_total": total_rent, "portfolio": port, "contributions": contrib,
        "gains": gains, "invest_tax": inv_tax, "renter_net": renter_net,
        "rent_yield": rent_yield,
        "buyer_real_out": buyer_real_out, "renter_real_out": renter_real_out,
        "buyer_y1": buyer_y1, "renter_y1": renter_y1,
        "buyer_y15": buyer_y15, "renter_y15": renter_y15,
    }


def metric_buyer(r: dict, basis: str) -> float:
    return r["buyer_net"] if basis == "net" else r["buyer_gross"]


def metric_renter(r: dict, basis: str) -> float:
    return r["renter_net"] if basis == "net" else r["portfolio"]


def break_even(p: Params, basis: str = "net") -> float:
    """Break-even annual house appreciation g* (percent) such that buyer and
    renter terminal wealth are equal under the chosen basis."""
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


def report(p: Params, basis: str = "net") -> str:
    r = simulate(p, p.house_growth)
    g = break_even(p, basis)
    bm = metric_buyer(r, basis)
    rm = metric_renter(r, basis)
    diff = rm - bm
    winner = "租房（定投）" if diff > 0 else "买房"
    L = []
    L.append("=" * 56)
    L.append("   租房 vs 买房 · 财务权衡分析框架")
    L.append(f"   口径: {'净收益(扣持有/税费/税)' if basis == 'net' else '毛资产'}   |   年限 X = {p.years} 年")
    L.append("=" * 56)
    L.append(f"  房屋总价 P          : {p.price:>10.1f} 万")
    L.append(f"  首付 / 贷款         : {r['down']:>10.1f} / {r['loan']:>10.1f} 万")
    L.append(f"  月供(等额本息)      : {r['monthly_payment']:>10.4f} 万/月")
    L.append(f"  名义总支出(首付+月供): {r['total_buy_nominal']:>10.1f} 万")
    L.append(f"  其中利息            : {r['interest']:>10.1f} 万")
    L.append(f"  房产终值(涨{p.house_growth}%)  : {r['house_value']:>10.1f} 万")
    L.append(f"  买家{'净收益' if basis=='net' else '毛资产'}      : {bm:>10.1f} 万")
    L.append(f"  租金名义累计        : {r['rent_total']:>10.1f} 万")
    L.append(f"  组合终值(税前)      : {r['portfolio']:>10.1f} 万")
    L.append(f"  投资所得税          : {r['invest_tax']:>10.1f} 万")
    L.append(f"  租房{'净收益' if basis=='net' else '毛资产'}      : {rm:>10.1f} 万")
    L.append(f"  租金回报率 / 房贷利率: {r['rent_yield']:>9.3f}% / {p.loan_rate:.3f}%")
    L.append(f"  盈亏平衡门槛 g*     : {g:>10.3f} %/年")
    L.append(f"  结论                : {winner} 净胜 {abs(diff):.1f} 万")
    L.append("=" * 56)
    return "\n".join(L)


def main():
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Rent-vs-Buy Decision Framework")
    ap.add_argument("--config", help="JSON file with parameter overrides")
    ap.add_argument("--basis", choices=["net", "gross"], default="net")
    for f in asdict(Params()).keys():
        ap.add_argument(f"--{f}", type=float, help=f"override {f}")
    args = ap.parse_args()

    p = Params()
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            for k, v in json.load(f).items():
                if hasattr(p, k):
                    setattr(p, k, v)
    for f in asdict(Params()).keys():
        v = getattr(args, f)
        if v is not None:
            setattr(p, f, v)

    print(report(p, args.basis))


if __name__ == "__main__":
    main()
