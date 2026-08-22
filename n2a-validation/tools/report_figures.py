#!/usr/bin/env python3
"""Generate figures for the N2A technical report."""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

OUT = "/home/claude/figs"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 160,
})

C_SA  = "#1f77b4"
C_SST = "#d62728"

# ---------------------------------------------------------------- data
alpha = np.array([6.0, 10.0])
cl_sa  = np.array([0.304170, 0.492868])
cl_sst = np.array([0.307588, 0.481590])
cd_sa  = np.array([0.020181, 0.041671])
cd_sst = np.array([0.018951, 0.041378])
cm_sa  = np.array([0.000259, -0.001498])
cm_sst = np.array([0.001050, -0.002860])

cdp_sa  = np.array([0.012158, 0.033762])
cdv_sa  = np.array([0.008023, 0.007909])
cdp_sst = np.array([0.012257, 0.034274])
cdv_sst = np.array([0.007687, 0.006570])

# ---------------------------------------------------------------- fig 1
fig, ax = plt.subplots(1, 3, figsize=(9.5, 3.0))

ax[0].plot(alpha, cl_sa,  "o-", color=C_SA,  label="Spalart-Allmaras")
ax[0].plot(alpha, cl_sst, "s--", color=C_SST, label="k-$\\omega$ SST")
ax[0].plot(10.0, cl_sst[1], "s", color=C_SST, mfc="white", ms=9, zorder=5)
ax[0].set_xlabel("angle of attack, deg")
ax[0].set_ylabel("$C_L$")
ax[0].set_title("Lift coefficient")
ax[0].legend(fontsize=7.5)
ax[0].set_xlim(4, 12)

ax[1].plot(alpha, cd_sa,  "o-", color=C_SA)
ax[1].plot(alpha, cd_sst, "s--", color=C_SST)
ax[1].plot(10.0, cd_sst[1], "s", color=C_SST, mfc="white", ms=9, zorder=5)
ax[1].set_xlabel("angle of attack, deg")
ax[1].set_ylabel("$C_D$")
ax[1].set_title("Drag coefficient")
ax[1].set_xlim(4, 12)

ax[2].plot(alpha, cm_sa,  "o-", color=C_SA)
ax[2].plot(alpha, cm_sst, "s--", color=C_SST)
ax[2].plot(10.0, cm_sst[1], "s", color=C_SST, mfc="white", ms=9, zorder=5)
ax[2].axhline(0, color="k", lw=0.6)
ax[2].set_xlabel("angle of attack, deg")
ax[2].set_ylabel("$C_m$")
ax[2].set_title("Pitching moment")
ax[2].set_xlim(4, 12)

fig.suptitle("Integrated coefficients. Open symbol: provisional (not fully converged)",
             fontsize=8.5, y=1.02)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_coefficients.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- fig 2
fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.2))

w = 0.35
x = np.arange(2)
ax[0].bar(x - w/2, cdp_sa,  w, color=C_SA,  label="SA")
ax[0].bar(x + w/2, cdp_sst, w, color=C_SST, label="SST")
ax[0].set_xticks(x); ax[0].set_xticklabels(["6 deg", "10 deg"])
ax[0].set_ylabel("$C_{D,pressure}$")
ax[0].set_title("Pressure drag")
ax[0].legend(fontsize=8)

ax[1].bar(x - w/2, cdv_sa,  w, color=C_SA,  label="SA")
ax[1].bar(x + w/2, cdv_sst, w, color=C_SST, label="SST")
ax[1].set_xticks(x); ax[1].set_xticklabels(["6 deg", "10 deg"])
ax[1].set_ylabel("$C_{D,viscous}$")
ax[1].set_title("Viscous drag")
for i, (a, b) in enumerate(zip(cdv_sa, cdv_sst)):
    ax[1].text(i, max(a, b)*1.04, f"{100*(b-a)/a:+.1f}%",
               ha="center", fontsize=8)
ax[1].set_ylim(0, 0.0098)

fig.suptitle("Drag breakdown. Pressure drag triples with incidence; viscous drag is flat,\n"
             "but the SA/SST difference in viscous drag grows from 4.2% to 16.9%.",
             fontsize=8.5, y=1.06)
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_drag_breakdown.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- fig 3
stations = np.array([13.4, 30.5, 51.0, 90.6])
ma = {
    "6 deg SA":   [0.233, 0.293, 0.271, 0.238],
    "6 deg SST":  [0.233, 0.291, 0.269, 0.237],
    "10 deg SA":  [0.251, 0.369, 0.299, 0.275],
    "10 deg SST": [0.253, 0.371, 0.298, 0.275],
}
fig, ax = plt.subplots(figsize=(6.2, 3.4))
sty = {"6 deg SA": ("o-", C_SA), "6 deg SST": ("s--", C_SA),
       "10 deg SA": ("o-", C_SST), "10 deg SST": ("s--", C_SST)}
for k, v in ma.items():
    m, c = sty[k]
    ax.plot(stations, v, m, color=c, label=k, ms=5)
ax.axhline(0.2, color="k", ls=":", lw=1.2)
ax.text(88, 0.204, "freestream $M_\\infty = 0.20$", ha="right", fontsize=8)
ax.set_xlabel("spanwise station, % semi-span")
ax.set_ylabel("maximum local Mach number")
ax.set_title("Local Mach number by spanwise station")
ax.legend(fontsize=8)
ax.set_ylim(0.19, 0.40)
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_mach.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- fig 4
it_v1  = np.arange(552, 560)
cl_v1  = np.array([0.3022155, 0.3013424, 0.3006607, 0.3000222,
                   0.3001952, 0.3009600, 0.3021557, 0.3032309])
it_v2  = np.arange(2993, 3001)
cl_v2  = np.array([0.3075890, 0.3075901, 0.3075913, 0.3075925,
                   0.3075938, 0.3075949, 0.3075958, 0.3075965])

fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.0))

ax[0].plot(it_v1, cl_v1, "o-", color=C_SST, ms=4)
ax[0].set_title("v1  kLowReWallFunction\noscillating, 1.07% amplitude", fontsize=9)
ax[0].set_xlabel("iteration"); ax[0].set_ylabel("$C_L$")
ax[0].xaxis.set_major_locator(MaxNLocator(integer=True))
ax[0].annotate("turning point", xy=(555, 0.3000222), xytext=(556.2, 0.30045),
               arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=7.5)

ax[1].plot(it_v2, cl_v2, "o-", color="#2ca02c", ms=4)
ax[1].set_title("v2  kqRWallFunction\nconverged, 0.0099% over 100 iterations", fontsize=9)
ax[1].set_xlabel("iteration"); ax[1].set_ylabel("$C_L$")
ax[1].xaxis.set_major_locator(MaxNLocator(integer=True))
ax[1].ticklabel_format(useOffset=False, axis="y")

fig.suptitle("k-$\\omega$ SST at 6 deg: effect of the k wall boundary condition",
             fontsize=9.5, y=1.04)
fig.tight_layout()
fig.savefig(f"{OUT}/fig4_oscillation.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- fig 5
cells = np.array([2.114, 6.006])
cl_m  = np.array([0.302633, 0.304170])
cd_m  = np.array([0.020129, 0.020181])

fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.0))
ax[0].plot(cells, cl_m, "o-", color=C_SA, ms=6)
ax[0].set_xlabel("cells, millions"); ax[0].set_ylabel("$C_L$")
ax[0].set_title("Lift, +0.5% for 2.8x cells")
ax[0].ticklabel_format(useOffset=False, axis="y")
ax[0].set_xlim(1.5, 6.6)

ax[1].plot(cells, cd_m, "o-", color=C_SA, ms=6)
ax[1].set_xlabel("cells, millions"); ax[1].set_ylabel("$C_D$")
ax[1].set_title("Drag, +0.26%")
ax[1].ticklabel_format(useOffset=False, axis="y")
ax[1].set_xlim(1.5, 6.6)

fig.suptitle("Grid sensitivity, 6 deg Spalart-Allmaras", fontsize=9.5, y=1.03)
fig.tight_layout()
fig.savefig(f"{OUT}/fig5_mesh_independence.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- fig 6
cpmin = {
    "6 deg SA":   [-0.541, -1.626, -1.623],
    "10 deg SA":  [-0.853, -3.737, -3.429],
}
st3 = np.array([13.4, 30.5, 51.0])
fig, ax = plt.subplots(figsize=(5.6, 3.2))
ax.plot(st3, cpmin["6 deg SA"],  "o-", color=C_SA,  label="6 deg SA", ms=5)
ax.plot(st3, cpmin["10 deg SA"], "o-", color=C_SST, label="10 deg SA", ms=5)
ax.set_xlabel("spanwise station, % semi-span")
ax.set_ylabel("$C_{p,min}$")
ax.set_title("Suction peak by station")
ax.invert_yaxis()
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f"{OUT}/fig6_cpmin.png", bbox_inches="tight")
plt.close(fig)

print("figures written:")
for f in sorted(os.listdir(OUT)):
    print("  ", f)
