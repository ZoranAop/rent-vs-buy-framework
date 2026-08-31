"""Smoke + regression tests for the rent-vs-buy model.

Run directly:  python tests/test_model.py
Run via pytest: pytest tests/ -v
No third-party dependencies (stdlib only).
"""

import math
import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import simulate, break_even, metric_buyer, metric_renter, make_params


def approx(a: float, b: float, tol: float = 0.02) -> bool:
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Default scenario regression
# ---------------------------------------------------------------------------
def test_default_break_even_net():
    """Net-basis break-even should be ~3.196% for the default scenario."""
    p = make_params()
    g = break_even(p, "net")
    assert approx(g, 3.196, 0.01), f"net g* = {g:.4f}, expected ~3.196"


def test_default_break_even_gross():
    """Gross-basis break-even should be ~3.290% for the default scenario."""
    p = make_params()
    g = break_even(p, "gross")
    assert approx(g, 3.290, 0.01), f"gross g* = {g:.4f}, expected ~3.290"


def test_consistency_at_breakeven():
    """At g*, buyer and renter terminal wealth must match (no contradiction)."""
    p = make_params()
    g = break_even(p, "net")
    r = simulate(p, g)
    bm = metric_buyer(r, "net")
    rm = metric_renter(r, "net")
    assert abs(bm - rm) < 1.0, f"at g* buyer={bm:.2f} vs renter={rm:.2f}"


def test_rent_yield_gauge_red():
    """Default rent yield (1.67%) must be below the mortgage rate (3%)."""
    p = make_params()
    r = simulate(p, p.house_growth)
    assert r["rent_yield"] < p.loan_rate


def test_higher_down_payment_lowers_monthly():
    p1 = make_params(price=600.0, down_pct=30.0)
    p2 = make_params(price=800.0, down_pct=50.0)
    r1 = simulate(p1, 0.0)
    r2 = simulate(p2, 0.0)
    assert r2["monthly_payment"] != r1["monthly_payment"]
    assert r2["loan"] < r1["loan"]


def test_break_even_rises_with_invest_return():
    """A higher investment return raises the appreciation g* needed to prefer buying."""
    p_low = make_params(invest_return=3.0)
    p_high = make_params(invest_return=8.0)
    assert break_even(p_high, "net") > break_even(p_low, "net")


# ---------------------------------------------------------------------------
# Boundary conditions
# ---------------------------------------------------------------------------
def test_zero_loan_rate():
    """Zero mortgage rate: monthly payment should equal loan/n, interest≈0."""
    p = make_params(loan_rate=0.0)
    r = simulate(p, 0.0)
    expected_M = r["loan"] / (p.years * 12)
    assert approx(r["monthly_payment"], expected_M, 0.01)
    assert approx(r["interest"], 0.0, 0.01)  # floating-point near-zero ok


def test_property_tax_deducts_from_net():
    """Non-zero property tax should reduce buyer_net compared to zero tax."""
    p_zero = make_params(property_tax=0.0)
    p_tax = make_params(property_tax=1.0)
    r_zero = simulate(p_zero, 3.0)
    r_tax = simulate(p_tax, 3.0)
    assert r_tax["property_tax_total"] > 0.0
    assert r_tax["buyer_net"] < r_zero["buyer_net"]


def test_zero_investment_gain_no_tax():
    """When portfolio gain is zero or negative, invest_tax should be 0."""
    # Very low invest return → portfolio grows less than contributions
    p = make_params(invest_return=0.1, rent0=100.0)  # high rent, low return
    r = simulate(p, 0.0)
    assert r["invest_tax"] == 0.0
    assert r["gains"] == 0.0


def test_short_horizon():
    """1-year horizon should produce meaningful results without errors."""
    p = make_params(years=1, house_growth=2.0)
    r = simulate(p, 2.0)
    assert r["house_value"] > 0
    assert r["portfolio"] > 0
    assert r["buyer_net"] != 0


def test_very_small_price():
    """Tiny house price should still compute without NaN or Inf."""
    p = make_params(price=10.0, down_pct=20.0, years=5)
    r = simulate(p, 1.0)
    assert math.isfinite(r["buyer_net"])
    assert math.isfinite(r["renter_net"])
    assert math.isfinite(r["monthly_payment"])


def test_break_even_gross_at_zero_growth():
    """g* at gross basis should be monotonically consistent with definition."""
    p = make_params()
    g = break_even(p, "gross")
    r = simulate(p, g)
    bm = metric_buyer(r, "gross")
    rm = metric_renter(r, "gross")
    assert abs(bm - rm) < 1.0, f"gross at g*: buyer={bm:.2f} vs renter={rm:.2f}"


# ---------------------------------------------------------------------------
# CLI config loading (integration)
# ---------------------------------------------------------------------------
def test_cli_config_file():
    """--config should override defaults correctly."""
    import subprocess
    cfg = {"price": 500.0, "years": 20, "invest_return": 7.0}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(cfg, f)
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, "rent_vs_buy_model.py", "--config", path, "--basis", "net"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        output = result.stdout.decode("utf-8", errors="replace")
        assert "500.0" in output   # price override applied
        assert "20" in output      # years override applied (contains "20 年" after decode)
    finally:
        os.unlink(path)


if __name__ == "__main__":
    test_default_break_even_net()
    test_default_break_even_gross()
    test_consistency_at_breakeven()
    test_rent_yield_gauge_red()
    test_higher_down_payment_lowers_monthly()
    test_break_even_rises_with_invest_return()
    test_zero_loan_rate()
    test_property_tax_deducts_from_net()
    test_zero_investment_gain_no_tax()
    test_short_horizon()
    test_very_small_price()
    test_break_even_gross_at_zero_growth()
    test_cli_config_file()
    print("ALL TESTS PASSED")
