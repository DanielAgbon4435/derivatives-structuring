"""Discount factors, forward rates, and a simple zero curve."""

from __future__ import annotations

import numpy as np


def discount_factor(interest_rate: float, maturity: float) -> float:
    if maturity < 0:
        raise ValueError("Maturity must be at least 0")
    return float(np.exp(-interest_rate * maturity))


def forward_rate(rate_1: float, mat_1: float, rate_2: float, mat_2: float) -> float:
    if mat_1 < 0 or mat_2 < 0:
        raise ValueError("Maturities must be positive")
    if mat_1 == mat_2:
        raise ValueError("Maturities must be different")
    if mat_1 > mat_2:
        raise ValueError("Maturity 2 must be bigger than Maturity 1")
    return (rate_2 * mat_2 - rate_1 * mat_1) / (mat_2 - mat_1)


def interpolate_zero_rate(maturities: np.ndarray, zero_rates: np.ndarray, t: float) -> float:
    """Linear interpolation in zero rates; flat extrapolation beyond the ends."""
    mats = np.asarray(maturities, dtype=float)
    zs = np.asarray(zero_rates, dtype=float)
    if mats.ndim != 1 or zs.ndim != 1 or len(mats) != len(zs) or len(mats) < 2:
        raise ValueError("Need matching 1-d maturity and zero-rate arrays of length >= 2")
    if np.any(np.diff(mats) <= 0):
        raise ValueError("Maturities must be strictly increasing")
    if t <= mats[0]:
        return float(zs[0])
    if t >= mats[-1]:
        return float(zs[-1])
    return float(np.interp(t, mats, zs))


def df_from_curve(maturities: np.ndarray, zero_rates: np.ndarray, t: float) -> float:
    return discount_factor(interpolate_zero_rate(maturities, zero_rates, t), t)


def forward_from_curve(
    maturities: np.ndarray, zero_rates: np.ndarray, t1: float, t2: float
) -> float:
    z1 = interpolate_zero_rate(maturities, zero_rates, t1)
    z2 = interpolate_zero_rate(maturities, zero_rates, t2)
    return forward_rate(z1, t1, z2, t2)
