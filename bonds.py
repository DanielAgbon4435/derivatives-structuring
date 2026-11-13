"""Coupon bond pricing and DV01 from a zero curve."""

from __future__ import annotations

import numpy as np

from rates import df_from_curve, interpolate_zero_rate


def coupon_times(maturity: float, frequency: int = 2) -> np.ndarray:
    if maturity <= 0:
        raise ValueError("Maturity must be positive")
    if frequency < 1:
        raise ValueError("Frequency must be at least 1")
    n = int(round(maturity * frequency))
    if n < 1:
        raise ValueError("Maturity too short for the coupon frequency")
    return np.arange(1, n + 1) / frequency


def price_coupon_bond(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    coupon_rate: float,
    face: float = 100.0,
    frequency: int = 2,
) -> float:
    """Clean price as discounted coupons plus principal (no accrued interest)."""
    times = coupon_times(maturity, frequency)
    cpn = face * coupon_rate / frequency
    dfs = np.array([df_from_curve(maturities, zero_rates, t) for t in times])
    return float(cpn * dfs.sum() + face * dfs[-1])


def bond_yield(
    price: float,
    maturity: float,
    coupon_rate: float,
    face: float = 100.0,
    frequency: int = 2,
    guess: float = 0.03,
) -> float:
    """Solve YTM under the same coupon schedule used for pricing."""
    times = coupon_times(maturity, frequency)
    cpn = face * coupon_rate / frequency

    def model(y: float) -> float:
        dfs = np.exp(-y * times)
        return float(cpn * dfs.sum() + face * dfs[-1] - price)

    y_lo, y_hi = -0.05, 0.5
    f_lo, f_hi = model(y_lo), model(y_hi)
    if f_lo * f_hi > 0:
        # Fall back around the guess if the wide bracket fails.
        y_lo, y_hi = guess - 0.2, guess + 0.2
        f_lo, f_hi = model(y_lo), model(y_hi)
        if f_lo * f_hi > 0:
            raise ValueError("Could not bracket a yield for this price")

    for _ in range(80):
        y_mid = 0.5 * (y_lo + y_hi)
        f_mid = model(y_mid)
        if abs(f_mid) < 1e-12:
            return float(y_mid)
        if f_lo * f_mid <= 0:
            y_hi, f_hi = y_mid, f_mid
        else:
            y_lo, f_lo = y_mid, f_mid
    return float(0.5 * (y_lo + y_hi))


def modified_duration(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    coupon_rate: float,
    face: float = 100.0,
    frequency: int = 2,
    bump: float = 1e-4,
) -> float:
    """−(1/P) dP/dy using a parallel bump of the zero curve."""
    p0 = price_coupon_bond(maturities, zero_rates, maturity, coupon_rate, face, frequency)
    bumped = np.asarray(zero_rates, dtype=float) + bump
    p_up = price_coupon_bond(maturities, bumped, maturity, coupon_rate, face, frequency)
    return float(-(p_up - p0) / (bump * p0))


def dv01(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    coupon_rate: float,
    face: float = 100.0,
    frequency: int = 2,
    bump: float = 1e-4,
) -> float:
    """Price change for a 1 bp parallel rise in zeros (negative for a long bond)."""
    p0 = price_coupon_bond(maturities, zero_rates, maturity, coupon_rate, face, frequency)
    bumped = np.asarray(zero_rates, dtype=float) + bump
    p_up = price_coupon_bond(maturities, bumped, maturity, coupon_rate, face, frequency)
    return float(p_up - p0)


def zero_rate_at(maturities: np.ndarray, zero_rates: np.ndarray, t: float) -> float:
    return interpolate_zero_rate(maturities, zero_rates, t)
