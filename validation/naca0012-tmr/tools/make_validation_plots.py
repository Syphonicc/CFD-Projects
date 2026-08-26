#!/usr/bin/env python3
"""
NACA 0012 TMR Validation — Figure Generation (v2, polished)
===========================================================
Generates:
  fig1_convergence.png   Cl/Cd convergence history, iteration 2 vs iteration 3
  fig2_validation.png    Converged Cl/Cd vs NASA CFL3D-SA reference
  fig3_convergence_zoom.png  Zoomed view of iteration 3 approaching the reference

Run from the parent directory containing both case folders:
    python3 make_validation_plots_v2.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys

# ----------------------------------------------------------------------
# PATHS — edit if your directory names differ
# ----------------------------------------------------------------------
ITER2 = "naca0012_case_iter2_ARCHIVE"
ITER3 = "naca0012_iter3"
OUTDIR = "validation_figures"

# NASA CFL3D-SA reference, 897x257 grid, alpha = 10 deg, Re = 6e6
REF_CL = 1.0909146672
REF_CD = 0.012310544747

# TMR code-to-code spread across the 7 reference codes (CL)
SPREAD_CL = (1.0891, 1.1000)
SPREAD_CD = (0.01225, 0.01245)

C_ITER2 = '#c0392b'
C_ITER3 = '#1f77b4'
C_REF = '#2c3e50'

os.makedirs(OUTDIR, exist_ok=True)


def read_coeffs(path):
    """Read OpenFOAM forceCoeffs coefficient.dat -> (time, Cd, Cl, CmPitch)."""
    if not os.path.exists(path):
        return None
    t, cd, cl, cm = [], [], [], []
    with open(path) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            p = line.split()
            if len(p) < 8:
                continue
            try:
                t.append(float(p[0]))
                cd.append(float(p[1]))
                cl.append(float(p[4]))
                cm.append(float(p[7]))
            except ValueError:
                continue
    if not t:
        return None
    return np.array(t), np.array(cd), np.array(cl), np.array(cm)


def find_coeff_files(case):
    """Concatenate all coefficient.dat under a case, ordered by iteration."""
    base = os.path.join(case, "postProcessing", "forceCoeffs1")
    if not os.path.isdir(base):
        print(f"  MISSING: {base}")
        return None
    def _key(s):
        try:
            return float(s)
        except ValueError:
            return 0.0
    runs = sorted(os.listdir(base), key=_key)
    segs = []
    for r in runs:
        d = read_coeffs(os.path.join(base, r, "coefficient.dat"))
        if d:
            segs.append(d)
            print(f"    read {case}/postProcessing/forceCoeffs1/{r}  ({len(d[0])} iterations)")
    if not segs:
        return None
    t = np.concatenate([s[0] for s in segs])
    cd = np.concatenate([s[1] for s in segs])
    cl = np.concatenate([s[2] for s in segs])
    cm = np.concatenate([s[3] for s in segs])
    order = np.argsort(t)
    # de-duplicate overlapping restart ranges, keeping the later value
    t, idx = np.unique(t[order], return_index=True)
    return t, cd[order][idx], cl[order][idx], cm[order][idx]


print("Reading iteration 2 (uncorrected nut) ...")
d2 = find_coeff_files(ITER2)
print("Reading iteration 3 (corrected nut) ...")
d3 = find_coeff_files(ITER3)

if d3 is None:
    sys.exit("ERROR: could not read iteration 3 data — check the ITER3 path.")

cl3, cd3, cm3 = d3[2][-1], d3[1][-1], d3[3][-1]
cl2, cd2, cm2 = (d2[2][-1], d2[1][-1], d2[3][-1]) if d2 else (np.nan, np.nan, np.nan)

# ======================================================================
# FIGURE 1 — Convergence history
# ======================================================================
fig, ax = plt.subplots(2, 1, figsize=(9.5, 7.5), sharex=True,
                       gridspec_kw={'hspace': 0.08})

# --- CL ---
ax[0].axhspan(SPREAD_CL[0], SPREAD_CL[1], color=C_REF, alpha=0.12, zorder=0,
              label='TMR code-to-code spread (7 codes)')
if d2:
    ax[0].plot(d2[0], d2[2], color=C_ITER2, lw=1.3, zorder=2,
               label=r'Iteration 2 — $\nu_{t\infty}/\nu = 8.4\times10^{5}$')
ax[0].plot(d3[0], d3[2], color=C_ITER3, lw=1.3, zorder=3,
           label=r'Iteration 3 — $\nu_{t\infty}/\nu = 0.21$ (corrected)')
ax[0].axhline(REF_CL, color=C_REF, ls='--', lw=1.3, zorder=1,
              label=f'NASA CFL3D-SA   $C_L$ = {REF_CL:.4f}')
ax[0].set_ylabel(r'$C_L$', fontsize=12)
ax[0].set_ylim(-0.25, 1.25)
ax[0].legend(fontsize=8.5, loc='lower right', framealpha=0.95)
ax[0].grid(alpha=0.25)
ax[0].set_title(r'NACA 0012   $Re = 6\times10^{6}$,  $\alpha = 10^\circ$   —   convergence history',
                fontsize=12, pad=10)

ax[0].annotate(f'{cl3:.4f}\n({100*(cl3-REF_CL)/REF_CL:+.2f}%)',
               xy=(d3[0][-1], cl3), xytext=(-70, -42), textcoords='offset points',
               fontsize=8.5, color=C_ITER3, ha='center',
               arrowprops=dict(arrowstyle='-', color=C_ITER3, lw=0.8))
if d2:
    ax[0].annotate(f'{cl2:.4f}\n({100*(cl2-REF_CL)/REF_CL:+.1f}%)',
                   xy=(d2[0][-1], cl2), xytext=(-20, -45), textcoords='offset points',
                   fontsize=8.5, color=C_ITER2, ha='center',
                   arrowprops=dict(arrowstyle='-', color=C_ITER2, lw=0.8))

# --- CD ---
ax[1].axhspan(SPREAD_CD[0], SPREAD_CD[1], color=C_REF, alpha=0.12, zorder=0)
if d2:
    ax[1].plot(d2[0], d2[1], color=C_ITER2, lw=1.3, zorder=2)
ax[1].plot(d3[0], d3[1], color=C_ITER3, lw=1.3, zorder=3)
ax[1].axhline(REF_CD, color=C_REF, ls='--', lw=1.3, zorder=1)
ax[1].axhline(0.0, color='gray', lw=0.9, zorder=1)
ax[1].set_ylabel(r'$C_D$', fontsize=12)
ax[1].set_xlabel('SIMPLE iteration', fontsize=11)
ax[1].grid(alpha=0.25)
ax[1].set_ylim(-0.030, 0.055)

ax[1].text(0.015, 0.10, 'unphysical: negative drag',
           transform=ax[1].transAxes, fontsize=8, color=C_ITER2, style='italic')

plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig1_convergence.png', dpi=200, bbox_inches='tight')
print(f"\n  wrote {OUTDIR}/fig1_convergence.png")

# ======================================================================
# FIGURE 2 — Converged values vs reference
# ======================================================================
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.8))

labels = ['Iteration 2\n(uncorrected)', 'Iteration 3\n(corrected)', 'NASA\nCFL3D-SA']
colors = [C_ITER2, C_ITER3, '#95a5a6']

# --- CL ---
vals_cl = [cl2, cl3, REF_CL]
bars = ax[0].bar(labels, vals_cl, color=colors, width=0.58, edgecolor='none')
ax[0].axhline(REF_CL, color=C_REF, ls='--', lw=1.1, zorder=3)
ax[0].set_ylabel(r'$C_L$', fontsize=12)
ax[0].set_title('Lift coefficient', fontsize=11)
ax[0].grid(alpha=0.25, axis='y')
ax[0].set_axisbelow(True)
ax[0].set_ylim(0, 1.32)
for i, v in enumerate(vals_cl):
    if not np.isnan(v):
        err = '' if i == 2 else f'\n{100*(v-REF_CL)/REF_CL:+.2f}%'
        ax[0].text(i, v + 0.025, f'{v:.4f}{err}', ha='center',
                   fontsize=9, linespacing=1.4)

# --- CD ---
vals_cd = [cd2, cd3, REF_CD]
ax[1].bar(labels, vals_cd, color=colors, width=0.58, edgecolor='none')
ax[1].axhline(REF_CD, color=C_REF, ls='--', lw=1.1, zorder=3)
ax[1].axhline(0, color='k', lw=0.9, zorder=3)
ax[1].set_ylabel(r'$C_D$', fontsize=12)
ax[1].set_title('Drag coefficient', fontsize=11)
ax[1].grid(alpha=0.25, axis='y')
ax[1].set_axisbelow(True)
ax[1].set_ylim(-0.026, 0.019)
for i, v in enumerate(vals_cd):
    if np.isnan(v):
        continue
    err = '' if i == 2 else f'\n{100*(v-REF_CD)/REF_CD:+.1f}%'
    if v > 0:
        ax[1].text(i, v + 0.0011, f'{v:.5f}{err}', ha='center',
                   va='bottom', fontsize=9, linespacing=1.4)
    else:
        ax[1].text(i, v - 0.0011, f'{v:.5f}{err}', ha='center',
                   va='top', fontsize=9, linespacing=1.4)

plt.suptitle(r'NACA 0012   $Re = 6\times10^{6}$,  $\alpha = 10^\circ$   —   validation against NASA TMR',
             fontsize=12, y=0.99)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f'{OUTDIR}/fig2_validation.png', dpi=200, bbox_inches='tight')
print(f"  wrote {OUTDIR}/fig2_validation.png")

# ======================================================================
# FIGURE 3 — Zoom on iteration 3 approach to reference
# ======================================================================
fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True,
                       gridspec_kw={'hspace': 0.08})

m = d3[0] > 1500
ax[0].axhspan(SPREAD_CL[0], SPREAD_CL[1], color=C_REF, alpha=0.12,
              label='TMR code-to-code spread')
ax[0].plot(d3[0][m], d3[2][m], color=C_ITER3, lw=1.5, label='Iteration 3')
ax[0].axhline(REF_CL, color=C_REF, ls='--', lw=1.2,
              label=f'CFL3D-SA  {REF_CL:.4f}')
ax[0].set_ylabel(r'$C_L$', fontsize=12)
ax[0].legend(fontsize=8.5, loc='lower right')
ax[0].grid(alpha=0.25)
ax[0].set_title('Iteration 3 — approach to converged state', fontsize=12, pad=10)

ax[1].axhspan(SPREAD_CD[0], SPREAD_CD[1], color=C_REF, alpha=0.12)
ax[1].plot(d3[0][m], d3[1][m], color=C_ITER3, lw=1.5)
ax[1].axhline(REF_CD, color=C_REF, ls='--', lw=1.2)
ax[1].set_ylabel(r'$C_D$', fontsize=12)
ax[1].set_xlabel('SIMPLE iteration', fontsize=11)
ax[1].grid(alpha=0.25)

plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig3_convergence_zoom.png', dpi=200, bbox_inches='tight')
print(f"  wrote {OUTDIR}/fig3_convergence_zoom.png")

# ======================================================================
# SUMMARY TABLE  (markdown, ready to paste into README)
# ======================================================================
print("\n" + "=" * 68)
print("CONVERGED RESULTS — NACA 0012, alpha = 10 deg, Re = 6e6")
print("=" * 68)
print(f"{'':24s} {'C_L':>11s} {'err':>9s} {'C_D':>11s} {'err':>9s}")
print("-" * 68)
print(f"{'NASA CFL3D-SA':24s} {REF_CL:11.5f} {'—':>9s} {REF_CD:11.5f} {'—':>9s}")
if d2:
    print(f"{'Iteration 2 (uncorr.)':24s} {cl2:11.5f} "
          f"{100*(cl2-REF_CL)/REF_CL:8.2f}% {cd2:11.5f} "
          f"{100*(cd2-REF_CD)/REF_CD:8.1f}%")
print(f"{'Iteration 3 (corrected)':24s} {cl3:11.5f} "
      f"{100*(cl3-REF_CL)/REF_CL:8.2f}% {cd3:11.5f} "
      f"{100*(cd3-REF_CD)/REF_CD:8.1f}%")
print("=" * 68)
print(f"\nCm_pitch (quarter chord):  iteration 3 = {cm3:.5f}"
      "   [expected ~0 for a symmetric section]")
print(f"Final iteration:           iteration 3 = {int(d3[0][-1])}")

print("\n\nMARKDOWN TABLE FOR README\n" + "-" * 68)
print("| Case | C_L | error | C_D | error |")
print("|---|---|---|---|---|")
print(f"| NASA CFL3D-SA (reference) | {REF_CL:.4f} | — | {REF_CD:.5f} | — |")
if d2:
    print(f"| Iteration 2 (uncorrected) | {cl2:.4f} | "
          f"{100*(cl2-REF_CL)/REF_CL:+.1f}% | {cd2:.5f} | "
          f"{100*(cd2-REF_CD)/REF_CD:+.1f}% |")
print(f"| Iteration 3 (corrected) | {cl3:.4f} | "
      f"{100*(cl3-REF_CL)/REF_CL:+.2f}% | {cd3:.5f} | "
      f"{100*(cd3-REF_CD)/REF_CD:+.1f}% |")
print("-" * 68)
