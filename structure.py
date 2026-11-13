"""
Structuring case study: UK pension fund duration hedge.

Client concern: a defined-benefit scheme with long-dated sterling liabilities.
Falling rates lift the present value of those liabilities. Two hedges are
compared under parallel curve scenarios:

  A — receive-fixed interest-rate swap sized to the liability DV01
  B — long position in a 15y coupon gilt sized to the same DV01
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bonds import dv01 as bond_dv01
from bonds import price_coupon_bond
from rates import df_from_curve
from swaps import par_swap_rate, swap_dv01, swap_pv


# Flat-ish illustrative GBP zero curve (continuous).
TENORS = np.array([0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0])
ZEROS = np.array([0.038, 0.039, 0.040, 0.041, 0.042, 0.0425, 0.043, 0.0435])


@dataclass
class HedgeResult:
    name: str
    instrument: str
    size: float
    base_pv: float
    dv01: float
    pnl_down_100bp: float
    pnl_up_100bp: float
    note: str


def liability_pv(zeros: np.ndarray, notional: float = 100_000_000.0, maturity: float = 15.0) -> float:
    """Zero-coupon liability proxy: one payment of `notional` at `maturity`."""
    return float(notional * df_from_curve(TENORS, zeros, maturity))


def liability_dv01(zeros: np.ndarray, notional: float = 100_000_000.0, maturity: float = 15.0) -> float:
    bump = 1e-4
    p0 = liability_pv(zeros, notional, maturity)
    p_up = liability_pv(zeros + bump, notional, maturity)
    return float(p_up - p0)


def receive_fixed_swap_hedge(zeros: np.ndarray, target_dv01: float) -> HedgeResult:
    """
    Receive fixed / pay float 15y swap.
    Receive-fixed gains when rates fall (same sign as the liability mark).
    Size so swap DV01 ≈ liability DV01 (both negative for a +1bp shock).
    """
    maturity = 15.0
    K = par_swap_rate(TENORS, zeros, maturity)
    unit = 1_000_000.0
    unit_dv01 = swap_dv01(TENORS, zeros, maturity, K, notional=unit, pay_fixed=False)
    # Liability DV01 < 0; receive-fixed DV01 < 0. Need positive notional.
    notional = target_dv01 / unit_dv01 * unit
    base = swap_pv(TENORS, zeros, maturity, K, notional=notional, pay_fixed=False)
    down = swap_pv(TENORS, zeros - 0.01, maturity, K, notional=notional, pay_fixed=False)
    up = swap_pv(TENORS, zeros + 0.01, maturity, K, notional=notional, pay_fixed=False)
    return HedgeResult(
        name="Solution A",
        instrument=f"Receive-fixed 15y IRS @ {K:.2%} par",
        size=notional,
        base_pv=base,
        dv01=swap_dv01(TENORS, zeros, maturity, K, notional=notional, pay_fixed=False),
        pnl_down_100bp=down - base,
        pnl_up_100bp=up - base,
        note="Low upfront cash; mark-to-market hedge. Counterparty / CSA risk remains.",
    )


def long_gilt_hedge(zeros: np.ndarray, target_dv01: float) -> HedgeResult:
    """Long 15y 4% semi-annual gilt sized to the liability DV01."""
    maturity = 15.0
    coupon = 0.04
    face_unit = 100.0
    unit_dv01 = bond_dv01(TENORS, zeros, maturity, coupon, face=face_unit)
    # Both DV01s negative for +1bp. Face amount > 0.
    face = target_dv01 / unit_dv01 * face_unit
    p0 = price_coupon_bond(TENORS, zeros, maturity, coupon, face=face)
    p_down = price_coupon_bond(TENORS, zeros - 0.01, maturity, coupon, face=face)
    p_up = price_coupon_bond(TENORS, zeros + 0.01, maturity, coupon, face=face)
    return HedgeResult(
        name="Solution B",
        instrument="Long 15y 4% semi-annual gilt",
        size=face,
        base_pv=p0,
        dv01=bond_dv01(TENORS, zeros, maturity, coupon, face=face),
        pnl_down_100bp=p_down - p0,
        pnl_up_100bp=p_up - p0,
        note="Requires cash / balance-sheet to buy bonds. No swap counterparty risk.",
    )


def run_case_study() -> dict:
    liab0 = liability_pv(ZEROS)
    liab_dv = liability_dv01(ZEROS)
    liab_down = liability_pv(ZEROS - 0.01) - liab0
    liab_up = liability_pv(ZEROS + 0.01) - liab0

    hedge_a = receive_fixed_swap_hedge(ZEROS, liab_dv)
    hedge_b = long_gilt_hedge(ZEROS, liab_dv)

    # Net surplus change ≈ −Δ liability + Δ hedge
    net_a_down = -liab_down + hedge_a.pnl_down_100bp
    net_a_up = -liab_up + hedge_a.pnl_up_100bp
    net_b_down = -liab_down + hedge_b.pnl_down_100bp
    net_b_up = -liab_up + hedge_b.pnl_up_100bp

    recommendation = (
        "Prefer Solution A (receive-fixed swap) when the fund wants duration "
        "with minimal cash outlay and can manage CSA/counterparty terms. "
        "Prefer Solution B (physical gilts) when the mandate forbids derivatives "
        "or when collateral and counterparty risk dominate. Both are sized to "
        "the same DV01, so parallel ±100 bp P&L is close; the commercial choice "
        "is about cash, credit, and governance—not the first-order rate hedge."
    )

    return {
        "liability_pv": liab0,
        "liability_dv01": liab_dv,
        "liability_pnl_down_100bp": liab_down,
        "liability_pnl_up_100bp": liab_up,
        "hedge_a": hedge_a,
        "hedge_b": hedge_b,
        "net_surplus_a_down": net_a_down,
        "net_surplus_a_up": net_a_up,
        "net_surplus_b_down": net_b_down,
        "net_surplus_b_up": net_b_up,
        "recommendation": recommendation,
    }
