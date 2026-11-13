# Derivatives pricing & structuring toolkit

Python + C++ toolkit for interest-rate pricing and a client structuring case study.
Built from continuous discount factors and simply-compounded forwards, then extended to
coupon bonds, DV01, interest-rate swaps, and a UK pension-fund hedge comparison.

## What works now (rates / fixed income)

| Piece | Status |
| --- | --- |
| Discount factor, instantaneous forward between two zeros | Done (Python + C++) |
| Linear zero-curve interpolation | Done |
| Coupon bond price, YTM, modified duration, DV01 | Done |
| Par swap rate, IRS PV, swap DV01 | Done |
| Structuring case: receive-fixed IRS vs long gilt for a DB pension liability | Done |
| Equity Black–Scholes / Greeks / delta hedge | Planned |
| Credit spreads / intro CVA | Planned |

## Structuring case study

Fictional UK defined-benefit pension fund with a £100m 15y liability proxy.
Falling rates raise liability PV. Two hedges are DV01-matched:

- **Solution A** — receive-fixed 15y IRS (low cash outlay; counterparty / CSA risk)
- **Solution B** — long 15y 4% gilt (cash intensive; no swap counterparty risk)

`python run.py` prints parallel ±100 bp P&L for the liability, each hedge, and the
net surplus, then writes `results/case_study.json`.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python run.py
```

C++ starter (discount factor, forward, coupon bond):

```bash
c++ -std=c++17 -O2 cpp/rates.cpp -o cpp/rates && ./cpp/rates
```

## Layout

- `rates.py` — discount factors, forwards, curve interpolation
- `bonds.py` — coupon bonds, duration, DV01
- `swaps.py` — vanilla IRS
- `structure.py` — pension hedge case study
- `cpp/rates.cpp` — same core rates + bond price in C++
- `run.py` — demo + case-study output
