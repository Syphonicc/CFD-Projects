#!/usr/bin/env python3
"""
N2A: Cp at four spanwise stations from sampled aircraft-patch data.

Reads p_aircraft.raw produced by the OpenFOAM `surfaces` function object
(columns: x y z p, face-centre data on the n2a patch), takes a thin band of
faces around each station, converts to Cp, splits upper and lower surface,
and plots against normalised chord.

Stations follow Aprovitola et al., as fractions of semi-span (1.88275 m):
    13.4%  ->  y = 0.25229
    30.5%  ->  y = 0.57424
    51.0%  ->  y = 0.96020
    90.6%  ->  y = 1.70577

Cp = (p - p_inf) / q_inf,  p_inf = 93290 Pa,  q_inf = 2612.00 Pa

Upper/lower split: at each chordwise position the section is split about the
local mid-z of the points at that x. On a blended body there is no camber
line to work from, so this is a geometric split rather than an aerodynamic
one, and it is approximate near the blunt centrebody.

Usage:
    python3 cp_plot.py                    # all cases found
    python3 cp_plot.py a10_SA a6_SA       # named cases
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANALYSIS = os.path.expanduser("~/CFD-Projects/n2a-validation/analysis")
FIGS     = os.path.expanduser("~/CFD-Projects/n2a-validation/figures")

P_INF = 93290.0
Q_INF = 2612.00
HALF_SPAN = 1.88275

STATIONS = [
    (0.134, 0.25229, "13.4%"),
    (0.305, 0.57424, "30.5%"),
    (0.510, 0.96020, "51.0%"),
    (0.906, 1.70577, "90.6%"),
]

BAND = 0.015          # +/- metres about the station plane

CASES = sys.argv[1:] or ["a6_SA", "a6_SST", "a10_SA", "a10_SST"]

STYLE = {
    "a6_SA":   dict(color="#1f77b4", ls="-",  label="6 deg  SA"),
    "a6_SST":  dict(color="#1f77b4", ls="--", label="6 deg  SST"),
    "a10_SA":  dict(color="#d62728", ls="-",  label="10 deg SA"),
    "a10_SST": dict(color="#d62728", ls="--", label="10 deg SST"),
}


def load(case):
    f = os.path.join(ANALYSIS, case, "p_aircraft.raw")
    if not os.path.exists(f):
        return None
    d = np.loadtxt(f, comments="#")
    return d           # x y z p


def section(d, ystation, band=BAND):
    m = np.abs(d[:, 1] - ystation) < band
    s = d[m]
    if len(s) < 20:
        return None
    x, z, p = s[:, 0], s[:, 2], s[:, 3]
    cp = (p - P_INF) / Q_INF
    c0, c1 = x.min(), x.max()
    chord = c1 - c0
    xc = (x - c0) / chord

    # split upper/lower about the local mid-z in chordwise bins
    upper = np.zeros(len(x), dtype=bool)
    bins = np.linspace(0, 1, 41)
    for i in range(len(bins) - 1):
        b = (xc >= bins[i]) & (xc < bins[i + 1])
        if b.sum() < 2:
            continue
        upper[b] = z[b] > z[b].mean()

    return dict(xc=xc, cp=cp, upper=upper, chord=chord, x0=c0, x1=c1)


def main():
    os.makedirs(FIGS, exist_ok=True)
    data = {c: load(c) for c in CASES}
    data = {k: v for k, v in data.items() if v is not None}
    if not data:
        print("no p_aircraft.raw found - run extract.sh first")
        return

    print(f"cases: {', '.join(data)}")
    print(f"q_inf = {Q_INF} Pa\n")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    summary = []
    for ax, (frac, ystn, lab) in zip(axes.ravel(), STATIONS):
        for case, d in data.items():
            s = section(d, ystn)
            if s is None:
                print(f"  {case} {lab}: too few points")
                continue
            st = STYLE.get(case, dict(label=case))
            for mask, mk in ((s["upper"], "o"), (~s["upper"], "s")):
                if mask.sum() == 0:
                    continue
                idx = np.argsort(s["xc"][mask])
                ax.plot(s["xc"][mask][idx], s["cp"][mask][idx],
                        marker=mk, ms=1.6, lw=0.7, alpha=0.85,
                        color=st.get("color"), ls=st.get("ls", "-"),
                        label=st.get("label", case) if mk == "o" else None)
            summary.append((case, lab, s["chord"], s["cp"].min(), s["cp"].max()))

        ax.set_title(f"{lab} semi-span   (y = {ystn:.4f} m)")
        ax.set_xlabel("x/c")
        ax.set_ylabel("$C_p$")
        ax.invert_yaxis()
        ax.grid(alpha=0.3)
        ax.axhline(0, color="k", lw=0.5)

    axes[0, 0].legend(fontsize=8, loc="lower right")
    fig.suptitle("N2A hybrid wing-body: surface pressure at four spanwise stations\n"
                 "M = 0.2, Re = 6.6e6, 6.0M cell half model  "
                 "(circles upper surface, squares lower)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIGS, "cp_stations.png")
    fig.savefig(out, dpi=160)
    print(f"wrote {out}\n")

    print(f"{'case':10s} {'station':8s} {'chord':>8s} {'Cp min':>9s} {'Cp max':>9s}")
    print("-" * 48)
    for c, l, ch, lo, hi in summary:
        print(f"{c:10s} {l:8s} {ch:8.4f} {lo:9.3f} {hi:9.3f}")

    # write the sectional data out for reuse
    for case, d in data.items():
        for frac, ystn, lab in STATIONS:
            s = section(d, ystn)
            if s is None:
                continue
            o = os.path.join(ANALYSIS, case, f"cp_{lab.replace('.','p').replace('%','')}.dat")
            idx = np.argsort(s["xc"])
            with open(o, "w") as fh:
                fh.write(f"# {case} station {lab}  y={ystn}  chord={s['chord']:.5f}\n")
                fh.write("# x/c  Cp  upper(1)/lower(0)\n")
                for i in idx:
                    fh.write(f"{s['xc'][i]:.6f} {s['cp'][i]:.6f} {int(s['upper'][i])}\n")


if __name__ == "__main__":
    main()
