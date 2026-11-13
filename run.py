"""Run the fixed-income engine and the pension structuring case study."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from bonds import dv01, modified_duration, price_coupon_bond
from rates import discount_factor, forward_from_curve, forward_rate
from structure import TENORS, ZEROS, run_case_study
from swaps import par_swap_rate, swap_dv01, swap_pv


def gbp(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}£{abs(x):,.0f}"


def main() -> None:
    print("=== Rates (from starter functions) ===")
    print(f"discount_factor(4%, 2y) = {discount_factor(0.04, 2.0):.6f}")
    print(f"forward_rate(4%@2y, 4.5%@3y) = {forward_rate(0.04, 2.0, 0.045, 3.0):.6%}")
    print(f"curve forward 2y–3y = {forward_from_curve(TENORS, ZEROS, 2.0, 3.0):.6%}")

    print("\n=== Coupon bond ===")
    px = price_coupon_bond(TENORS, ZEROS, maturity=10.0, coupon_rate=0.04)
    print(f"10y 4% semi-annual bond price = {px:.4f}")
    print(f"DV01 (per 100 face) = {dv01(TENORS, ZEROS, 10.0, 0.04):.6f}")
    print(f"Modified duration = {modified_duration(TENORS, ZEROS, 10.0, 0.04):.3f}")

    print("\n=== Interest-rate swap ===")
    K = par_swap_rate(TENORS, ZEROS, 10.0)
    print(f"10y par swap rate = {K:.4%}")
    print(f"Pay-fixed PV @ par (1mm) = {swap_pv(TENORS, ZEROS, 10.0, K, 1_000_000):.2f}")
    print(
        f"Pay-fixed DV01 @ par (1mm) = "
        f"{swap_dv01(TENORS, ZEROS, 10.0, K, 1_000_000):,.2f}"
    )

    print("\n=== Structuring case study: UK pension liability hedge ===")
    case = run_case_study()
    print(f"Liability PV (15y ZCB proxy, £100m) = {gbp(case['liability_pv'])}")
    print(f"Liability DV01 = {gbp(case['liability_dv01'])}")
    print(f"Liability P&L if rates −100bp = {gbp(case['liability_pnl_down_100bp'])}")
    print(f"Liability P&L if rates +100bp = {gbp(case['liability_pnl_up_100bp'])}")

    for key in ("hedge_a", "hedge_b"):
        h = case[key]
        print(f"\n{h.name}: {h.instrument}")
        print(f"  Size = {gbp(h.size)}")
        print(f"  DV01 = {gbp(h.dv01)}")
        print(f"  Hedge P&L −100bp / +100bp = {gbp(h.pnl_down_100bp)} / {gbp(h.pnl_up_100bp)}")
        print(f"  Note: {h.note}")

    print("\nNet surplus change ( −Δ liability + Δ hedge )")
    print(f"  A −100bp / +100bp = {gbp(case['net_surplus_a_down'])} / {gbp(case['net_surplus_a_up'])}")
    print(f"  B −100bp / +100bp = {gbp(case['net_surplus_b_down'])} / {gbp(case['net_surplus_b_up'])}")
    print(f"\nRecommendation: {case['recommendation']}")

    out = {
        "discount_factor_4pct_2y": discount_factor(0.04, 2.0),
        "forward_2y_3y": forward_rate(0.04, 2.0, 0.045, 3.0),
        "bond_10y_4pct_price": px,
        "par_swap_10y": K,
        "liability_pv": case["liability_pv"],
        "liability_dv01": case["liability_dv01"],
        "hedge_a_size": case["hedge_a"].size,
        "hedge_b_size": case["hedge_b"].size,
        "net_surplus_a_down": case["net_surplus_a_down"],
        "net_surplus_a_up": case["net_surplus_a_up"],
        "net_surplus_b_down": case["net_surplus_b_down"],
        "net_surplus_b_up": case["net_surplus_b_up"],
        "recommendation": case["recommendation"],
    }
    path = Path("results") / "case_study.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
