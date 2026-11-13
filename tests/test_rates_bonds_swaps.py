import numpy as np
import pytest

from bonds import coupon_times, dv01, price_coupon_bond
from rates import discount_factor, forward_from_curve, forward_rate, interpolate_zero_rate
from structure import TENORS, ZEROS, liability_dv01, run_case_study
from swaps import annuity, par_swap_rate, swap_pv


def test_discount_factor_matches_starter():
    assert discount_factor(0.04, 2.0) == pytest.approx(np.exp(-0.08))


def test_discount_factor_rejects_negative_maturity():
    with pytest.raises(ValueError):
        discount_factor(0.04, -1.0)


def test_forward_rate_matches_starter_formula():
    assert forward_rate(0.04, 2.0, 0.045, 3.0) == pytest.approx(
        (0.045 * 3 - 0.04 * 2) / 1.0
    )


def test_forward_rate_rejects_equal_mats():
    with pytest.raises(ValueError):
        forward_rate(0.04, 2.0, 0.045, 2.0)


def test_zero_interpolation_and_curve_forward():
    z = interpolate_zero_rate(TENORS, ZEROS, 7.5)
    assert ZEROS[3] < z < ZEROS[4]
    fwd = forward_from_curve(TENORS, ZEROS, 2.0, 3.0)
    assert fwd > 0


def test_flat_curve_bond_price():
    mats = np.array([1.0, 5.0, 10.0])
    zs = np.array([0.05, 0.05, 0.05])
    times = coupon_times(5.0, frequency=1)
    assert list(times) == [1.0, 2.0, 3.0, 4.0, 5.0]
    # Continuous zeros: annual 5% coupon on a flat 5% continuous curve is not par.
    expected = sum(5.0 * np.exp(-0.05 * t) for t in times) + 100.0 * np.exp(-0.05 * 5.0)
    px = price_coupon_bond(mats, zs, maturity=5.0, coupon_rate=0.05, frequency=1)
    assert px == pytest.approx(expected, abs=1e-8)


def test_bond_dv01_negative_for_long_bond():
    assert dv01(TENORS, ZEROS, 10.0, 0.04) < 0


def test_par_swap_has_near_zero_pv():
    K = par_swap_rate(TENORS, ZEROS, 10.0)
    assert swap_pv(TENORS, ZEROS, 10.0, K, notional=1_000_000, pay_fixed=True) == pytest.approx(
        0.0, abs=1e-6
    )
    assert annuity(TENORS, ZEROS, 10.0) > 0


def test_case_study_hedges_reduce_rate_gap():
    case = run_case_study()
    # Unhedged liability loss when rates fall is large and negative for surplus:
    # surplus change = -liability_pnl; liability_pnl_down > 0 so surplus falls.
    unhedged_down = -case["liability_pnl_down_100bp"]
    assert unhedged_down < 0
    # Hedged net surplus moves should be much smaller in magnitude.
    assert abs(case["net_surplus_a_down"]) < 0.15 * abs(unhedged_down)
    assert abs(case["net_surplus_b_down"]) < 0.15 * abs(unhedged_down)
    assert liability_dv01(ZEROS) < 0
