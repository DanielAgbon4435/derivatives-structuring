"""Plain-vanilla fixed-for-floating interest-rate swap."""

from __future__ import annotations

import numpy as np

from rates import df_from_curve


def _schedule(maturity: float, frequency: int) -> np.ndarray:
    n = int(round(maturity * frequency))
    if n < 1:
        raise ValueError("Maturity too short for the payment frequency")
    return np.arange(1, n + 1) / frequency


def annuity(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    frequency: int = 2,
) -> float:
    times = _schedule(maturity, frequency)
    delta = 1.0 / frequency
    return float(sum(delta * df_from_curve(maturities, zero_rates, t) for t in times))


def par_swap_rate(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    frequency: int = 2,
) -> float:
    """Annualised par fixed rate for a spot-starting fixed-vs-float swap."""
    times = _schedule(maturity, frequency)
    df_T = df_from_curve(maturities, zero_rates, times[-1])
    a = annuity(maturities, zero_rates, maturity, frequency)
    return float((1.0 - df_T) / a)


def swap_pv(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    fixed_rate: float,
    notional: float = 1.0,
    pay_fixed: bool = True,
    frequency: int = 2,
) -> float:
    """
    PV of a spot-starting IRS.
    Floating leg valued as 1 - DF(T) under the usual telescoping argument.
    """
    times = _schedule(maturity, frequency)
    delta = 1.0 / frequency
    df_T = df_from_curve(maturities, zero_rates, times[-1])
    fixed_pv = fixed_rate * sum(
        delta * df_from_curve(maturities, zero_rates, t) for t in times
    )
    float_pv = 1.0 - df_T
    # Receive float, pay fixed when pay_fixed=True.
    unit_pv = float_pv - fixed_pv if pay_fixed else fixed_pv - float_pv
    return float(notional * unit_pv)


def swap_dv01(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    fixed_rate: float,
    notional: float = 1.0,
    pay_fixed: bool = True,
    frequency: int = 2,
    bump: float = 1e-4,
) -> float:
    """PV change for a 1 bp parallel rise in zeros."""
    pv0 = swap_pv(
        maturities, zero_rates, maturity, fixed_rate, notional, pay_fixed, frequency
    )
    bumped = np.asarray(zero_rates, dtype=float) + bump
    pv_up = swap_pv(
        maturities, bumped, maturity, fixed_rate, notional, pay_fixed, frequency
    )
    return float(pv_up - pv0)


def forward_float_cashflows(
    maturities: np.ndarray,
    zero_rates: np.ndarray,
    maturity: float,
    frequency: int = 2,
) -> list[tuple[float, float, float]]:
    """Return (pay_time, forward_rate, df) for each float period."""
    times = _schedule(maturity, frequency)
    out = []
    t_prev = 0.0
    for t in times:
        # Simply-compounded period forward from DFs.
        df0 = 1.0 if t_prev == 0 else df_from_curve(maturities, zero_rates, t_prev)
        df1 = df_from_curve(maturities, zero_rates, t)
        simple_fwd = (df0 / df1 - 1.0) / (t - t_prev)
        out.append((float(t), float(simple_fwd), float(df1)))
        t_prev = float(t)
    return out
