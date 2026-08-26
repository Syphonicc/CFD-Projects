#!/usr/bin/env python3
"""
Comparison of the present results against the five datasets in
Aprovitola et al. (2022), digitised from Figures 12, 13 and 15.

Every percentage difference is stated against a named dataset.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/claude/figs"
DAT = "/home/claude/refdata"
os.makedirs(OUT, exist_ok=True)
os.makedirs(DAT, exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.dpi": 160})

f12 = np.load("/home/claude/fig12_series.npy", allow_pickle=True).item()
f1315 = np.load("/home/claude/fig1315.npy", allow_pickle=True).item()

REF = {
    "C_L": {"T597 closed tunnel": f12["T597 closed tunnel"],
            "T612 open tunnel":   f12["T612 open tunnel"],
            "Cart3D":             f12["Cart3D"],
            "FLUENT":             f12["FLUENT"],
            "SU2":                f12["SU2"]},
    "C_D": {"T597 closed tunnel": f1315["fig13_Cd"]["T597"],
            "T612 open tunnel":   f1315["fig13_Cd"]["T612"],
            "FLUENT":             f1315["fig13_Cd"]["FLUENT"],
            "SU2":                f1315["fig13_Cd"]["SU2"]},
    "C_m": {"T597 closed tunnel": f1315["fig15_Cm"]["T597"],
            "T612 open tunnel":   f1315["fig15_Cm"]["T612"],
            "Cart3D":             f1315["fig15_Cm"]["Cart3D"],
            "FLUENT":             f1315["fig15_Cm"]["FLUENT"],
            "SU2":                f1315["fig15_Cm"]["SU2"]},
}

OURS = {
    "C_L": {"SA": {6: 0.304170, 10: 0.492868},
            "SST": {6: 0.307588, 10: 0.481590}},
    "C_D": {"SA": {6: 0.020181, 10: 0.041671},
            "SST": {6: 0.018951, 10: 0.041378}},
    "C_m": {"SA": {6: 0.000259, 10: -0.001498},
            "SST": {6: 0.001050, 10: -0.002860}},
}

STY = {
    "T597 closed tunnel": dict(color="#d62728", ls="-",  marker="o", ms=3, lw=1.1),
    "T612 open tunnel":   dict(color="#000000", ls="-",  marker="o", ms=3, lw=1.1),
    "Cart3D":             dict(color="#2ca02c", ls="none", marker="s", ms=5),
    "FLUENT":             dict(color="#1f77b4", ls="none", marker="^", ms=6),
    "SU2":                dict(color="#ff9900", ls="none", marker="D", ms=5),
}


def at(pts, a, tol=0.6):
    if len(pts) == 0:
        return None
    if len(pts) > 40:
        if a < pts[:, 0].min() or a > pts[:, 0].max():
            return None
        return float(np.interp(a, pts[:, 0], pts[:, 1]))
    d = np.abs(pts[:, 0] - a)
    return float(pts[np.argmin(d)][1]) if d.min() <= tol else None


# ------------------------------------------------------------------ export
for q, sets in REF.items():
    for nm, p in sets.items():
        if len(p) == 0:
            continue
        fn = f"{DAT}/{q}_{nm.split()[0]}.dat".replace(" ", "")
        np.savetxt(fn, p, fmt="%.5f",
                   header=f"Aprovitola et al. 2022, digitised\n{q} vs alpha [deg]\n"
                          f"dataset: {nm}\nalpha  {q}")

# ------------------------------------------------------------------ figure
LBL = {"C_L": "$C_L$", "C_D": "$C_D$", "C_m": "$C_m$"}
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0))

for ax, q in zip(axes, ("C_L", "C_D", "C_m")):
    for nm, p in REF[q].items():
        if len(p) == 0:
            continue
        m = (p[:, 0] >= -6) & (p[:, 0] <= 16)
        if m.sum() == 0:
            continue
        ax.plot(p[m, 0], p[m, 1], label=nm, alpha=0.85, **STY[nm])
    for mod, mk, col in (("SA", "*", "#7b3fa0"), ("SST", "P", "#00868b")):
        xs = [6, 10]
        ys = [OURS[q][mod][6], OURS[q][mod][10]]
        ax.plot(xs, ys, mk, color=col, ms=13, mec="k", mew=0.6,
                ls="--", lw=1.0, label=f"present, {mod}", zorder=6)
    ax.set_xlabel("angle of attack, deg")
    ax.set_ylabel(LBL[q])
    ax.set_xlim(-6, 16)
    if q == "C_m":
        ax.axhline(0, color="k", lw=0.6)

axes[0].legend(fontsize=6.8, loc="upper left", framealpha=0.9)
fig.suptitle("Present results against the five datasets of Aprovitola et al. (2022), "
             "digitised from Figures 12, 13 and 15", fontsize=9.5, y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/fig7_reference_comparison.png", bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ tables
print("=" * 78)
print("REFERENCE VALUES  (digitised, uncertainty approx +/-0.005 lines, "
      "+/-0.008 markers)")
print("=" * 78)
for q in ("C_L", "C_D", "C_m"):
    print(f"\n{q}")
    print(f"  {'dataset':22s} {'alpha=6':>10s} {'alpha=10':>10s}")
    for nm, p in REF[q].items():
        v6, v10 = at(p, 6.0), at(p, 10.0)
        s6 = f"{v6:10.5f}" if v6 is not None else f"{'no point':>10s}"
        s10 = f"{v10:10.5f}" if v10 is not None else f"{'no point':>10s}"
        print(f"  {nm:22s} {s6} {s10}")
    for mod in ("SA", "SST"):
        print(f"  {'present, '+mod:22s} {OURS[q][mod][6]:10.5f} "
              f"{OURS[q][mod][10]:10.5f}")

print("\n" + "=" * 78)
print("DIFFERENCES  (present minus reference, as % of the named reference)")
print("=" * 78)
for q in ("C_L", "C_D"):
    print(f"\n{q}")
    print(f"  {'against':22s} {'a=6 SA':>9s} {'a=6 SST':>9s} "
          f"{'a=10 SA':>9s} {'a=10 SST':>9s}")
    for nm, p in REF[q].items():
        row = []
        for a in (6, 10):
            r = at(p, float(a))
            for mod in ("SA", "SST"):
                if r is None or abs(r) < 1e-9:
                    row.append(f"{'-':>9s}")
                else:
                    row.append(f"{100*(OURS[q][mod][a]-r)/r:+8.1f}%")
        print(f"  {nm:22s} {row[0]} {row[1]} {row[2]} {row[3]}")

print("\nC_m  (absolute difference; values straddle zero so percentages are "
      "not meaningful)")
print(f"  {'against':22s} {'a=6 SA':>10s} {'a=6 SST':>10s} "
      f"{'a=10 SA':>10s} {'a=10 SST':>10s}")
for nm, p in REF["C_m"].items():
    row = []
    for a in (6, 10):
        r = at(p, float(a))
        for mod in ("SA", "SST"):
            row.append(f"{'-':>10s}" if r is None
                       else f"{OURS['C_m'][mod][a]-r:+10.5f}")
    print(f"  {nm:22s} {row[0]} {row[1]} {row[2]} {row[3]}")

print("\n" + "=" * 78)
print("LIFT CURVE SLOPE between 6 and 10 deg, per degree")
print("=" * 78)
for nm, p in REF["C_L"].items():
    a, b = at(p, 6.0), at(p, 10.0)
    if a is not None and b is not None:
        print(f"  {nm:22s} {(b-a)/4:.4f}")
for mod in ("SA", "SST"):
    print(f"  {'present, '+mod:22s} "
          f"{(OURS['C_L'][mod][10]-OURS['C_L'][mod][6])/4:.4f}")

print("\nL/D")
for nm in REF["C_L"]:
    if nm not in REF["C_D"]:
        continue
    for a in (6, 10):
        l, d = at(REF["C_L"][nm], float(a)), at(REF["C_D"][nm], float(a))
        if l is not None and d is not None and d > 0:
            print(f"  {nm:22s} alpha={a:2d}  {l/d:5.1f}")
for mod in ("SA", "SST"):
    for a in (6, 10):
        print(f"  {'present, '+mod:22s} alpha={a:2d}  "
              f"{OURS['C_L'][mod][a]/OURS['C_D'][mod][a]:5.1f}")
