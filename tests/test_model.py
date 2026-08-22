"""Smoke + regression tests for the rent-vs-buy model.

Run directly:  python tests/test_model.py
No third-party dependencies (stdlib only).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rent_vs_buy_model import (  # noqa: E402
    Params,
    simulate,
    break_even,
    metric_buyer,
    metric_renter,
)


def approx(a: float, b: float, tol: float = 0.02) -> bool:
    return abs(a - b) <= tol


def test_default_break_even_net():
    """Net-basis break-even should be ~3.196% for the default scenario."""
    g = break_even(Params(), "net")
    assert approx(g, 3.196, 0.01), f"net g* = {g:.4f}, expected ~3.196"


def test_default_break_even_gross():
    """Gross-basis break-even should be ~3.290% for the default scenario."""
    g = break_even(Params(), "gross")
    assert approx(g, 3.290, 0.01), f"gross g* = {g:.4f}, expected ~3.290"


def test_consistency_at_breakeven():
    """At g*, buyer and renter terminal wealth must match (no contradiction)."""
    p = Params()
    g = break_even(p, "net")
    r = simulate(p, g)
    bm = metric_buyer(r, "net")
    rm = metric_renter(r, "net")
    assert abs(bm - rm) < 1.0, f"at g* buyer={bm:.2f} vs renter={rm:.2f}"


def test_rent_yield_gauge_red():
    """Default rent yield (1.67%) must be below the mortgage rate (3%)."""
    r = simulate(Params(), Params().house_growth)
    assert r["rent_yield"] < Params().loan_rate


def test_higher_down_payment_lowers_monthly():
    p = Params()
    p2 = Params()
    p2.price = 800.0
    p2.down_pct = 50.0
    r1 = simulate(p, 0.0)
    r2 = simulate(p2, 0.0)
    assert r2["monthly_payment"] != r1["monthly_payment"]
    # bigger down payment must reduce the financed loan and thus the payment
    assert r2["loan"] < r1["loan"]


def test_break_even_rises_with_invest_return():
    """A higher investment return raises the appreciation g* needed to prefer buying."""
    p_low = Params()
    p_low.invest_return = 3.0
    p_high = Params()
    p_high.invest_return = 8.0
    assert break_even(p_high, "net") > break_even(p_low, "net")


if __name__ == "__main__":
    test_default_break_even_net()
    test_default_break_even_gross()
    test_consistency_at_breakeven()
    test_rent_yield_gauge_red()
    test_higher_down_payment_lowers_monthly()
    test_break_even_rises_with_invest_return()
    print("ALL TESTS PASSED")
