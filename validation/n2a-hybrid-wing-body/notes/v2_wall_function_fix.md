# v2 — k wall function correction

The two k-ω SST runs in `results/` are **not converged**. They are oscillating
in a limit cycle. This note records what was wrong, how it was found, and the
corrected values. The v1 results are kept rather than deleted — the error is
part of the record.

---

## The symptom

Vedang flagged it from the pushed plots: SA converges cleanly, both SST cases
oscillate, and the 6° SST run especially does not look properly converged.
Crucially he noted the residuals looked healthy — small and decaying smoothly —
which is what made it hard to spot.

Checking the coefficient history rather than the final value confirms it. Last
eight iterations of the v1 6° SST run:

```
   552  Cd  0.0196255  Cl  0.3022155
   553  Cd  0.0194454  Cl  0.3013424
   554  Cd  0.0193246  Cl  0.3006607
   555  Cd  0.0192319  Cl  0.3000222     <- minimum
   556  Cd  0.0192975  Cl  0.3001952
   557  Cd  0.0194734  Cl  0.3009600
   558  Cd  0.0197324  Cl  0.3021557
   559  Cd  0.0199443  Cl  0.3032309
```

That is a turning point mid-cycle, not convergence. Amplitude about 1% in C_L
and 4% in C_D, with a period of roughly ten iterations.

Compare the SA run over the same span, where C_L drifts only in the seventh
decimal:

```
  1997  Cd  0.0201793  Cl  0.3041713
  1998  Cd  0.0201809  Cl  0.3041678
  1999  Cd  0.0201815  Cl  0.3041674
  2000  Cd  0.0201811  Cl  0.3041696
```

---

## Why it was missed

Four failures stacked.

**SST was never tested locally.** The smoke test and the 2000-iteration local
run were both SA. The `kLowReWallFunction` choice went straight to production
without ever being exercised.

**The BC was chosen for a mesh that did not materialise.**
`kLowReWallFunction` is correct for a wall-resolved mesh, and the design target
was y+ < 1. By the time the runs happened the measured y+ was 0.5 to 684 with a
mean of 33, so the premise had changed — but the boundary condition was never
revisited.

**`residualControl` cannot detect a limit cycle.** Raising the threshold from
1e-5 to 1e-7 after an earlier false convergence felt like a fix. It was not. In
a bounded oscillation the change per iteration genuinely is small, so the
residuals are small, while the solution never settles. Tightening the threshold
only moves where the run stops, not whether it has converged.

**The check was on the last value, not the last fifty.** For SA the final
iterations agreed to five figures, so the same check on SST was reported as
converged without looking at the shape of the history. Reading one number
rather than a window is exactly what hides a limit cycle.

**General rule: residuals cannot detect a limit cycle. Only the history of the
integrated quantity can.** Same principle as the constant C_s that revealed the
missing `pRef` — the shape over many iterations is the diagnostic, never a
single number.

---

## The cause

`kLowReWallFunction` sets k at the wall from the low-Reynolds asymptotic
behaviour, valid when the first cell centre sits inside the viscous sublayer.

On this mesh y+ ranges from 0.5 to 684, and 1.55% of faces have no prism layers
at all. So over most of the surface the boundary condition was being applied
where its underlying assumption does not hold, and the mismatch varies
patchily face to face. That inconsistency is what fed the oscillation.

`nutUSpaldingWallFunction` was already handling the y+ variation gracefully for
the eddy viscosity — it blends across all three near-wall regions. The k
boundary condition was not.

---

## The fix

```
    n2a
    {
        type            kqRWallFunction;      // was kLowReWallFunction
        value           uniform 1.042e-03;    // was 1e-12
    }
```

`kqRWallFunction` is the zero-gradient high-Re form and makes no assumption
about where the first cell sits. The `value` entry is only an initial guess
under a zero-gradient condition, so it is set to the freestream k rather than
the near-zero value appropriate to the low-Re form.

`residualControl` was also removed entirely for the reruns and a fixed 3000
iterations used instead, so the full history is visible and convergence is
judged from the coefficients rather than delegated to the solver.

---

## Result — α = 6°, k-ω SST

| | v1 `kLowReWallFunction` | v2 `kqRWallFunction` |
|---|---|---|
| C_L oscillation, last 100 iter | **1.07%** | **0.0099%** |
| C_D oscillation, last 100 iter | ~4% | 0.053% |
| C_L | 0.303231 *(mid-cycle)* | **0.307588** |
| C_D | 0.019944 *(mid-cycle)* | **0.018951** |
| y+ mean | 34.13 | 33.10 |
| Iterations | 559 (stopped on residualControl) | 3000 (fixed) |
| Wall clock | 2981 s | 7995 s |

Oscillation amplitude fell by a factor of **108**. The v2 run is converged.

Runtime per iteration also improved, 5.33 s to 2.66 s — the solver is no longer
fighting the oscillation.

---

## What this changes about the SA/SST comparison

The earlier finding was that the two models agree to within 1% at both angles,
contrary to the study design, which predicted divergence at 10° where the
leading-edge vortex forms.

That comparison was against an SST value sampled mid-oscillation. With SST
properly converged at 6°:

| | SA | SST v2 | difference |
|---|---|---|---|
| C_L | 0.304170 | 0.307588 | **+1.12%** |
| C_D | 0.020181 | 0.018951 | **−6.1%** |

Previously this read as 0.31% in C_L and 1.2% in C_D. The models differ
considerably more than the invalid comparison suggested.

So the "SA and SST agree unexpectedly" result was partly an artifact. The 10°
comparison needs the same treatment before anything is concluded from it.

---

## Status

| Case | v1 | v2 |
|---|---|---|
| 6° SA | converged, valid | not rerun (SA unaffected) |
| 6° SST | **oscillating, invalid** | converged |
| 10° SA | converged, valid | not rerun (SA unaffected) |
| 10° SST | **oscillating, invalid** | pending |

The SA runs use `nuTilda` with a `fixedValue 0` wall condition and are not
affected by this — their convergence histories are clean and the v1 values
stand.

---

## Result — alpha = 10 deg, k-omega SST

| | v1 kLowReWallFunction | v2 kqRWallFunction |
|---|---|---|
| C_L range over last 100 iter | ~0.6% | **0.31%** |
| C_D range over last 100 iter | ~2.6% | **0.57%** |
| C_L | 0.495996 *(mid-cycle)* | 0.481590 *(provisional)* |
| C_D | 0.040844 *(mid-cycle)* | 0.041378 *(provisional)* |
| y+ mean | 32.12 | 31.79 |
| Iterations | 792 (stopped on residualControl) | 3000 (fixed) |
| Wall clock | 4003 s | 8437 s |

**Improved but not fully converged.** The oscillation is largely gone, but C_L
is now drifting monotonically upward at approximately 1.5e-5 per iteration and
is still climbing at iteration 3000:

```
  2996  Cd  0.0413660  Cl  0.4815156
  2997  Cd  0.0413689  Cl  0.4815329
  2998  Cd  0.0413737  Cl  0.4815514
  2999  Cd  0.0413768  Cl  0.4815710
  3000  Cd  0.0413779  Cl  0.4815905
```

That is a steady drift, not a limit cycle - the 0.31% range over the last 100
iterations is almost entirely this monotonic rise. Compare the 6 deg case,
which settled to 0.0099% over the same window.

**The value is reported as provisional.** Extending the run would need roughly
3000 further iterations; the CloudHPC free trial is exhausted at 289.5 of 300
vCPU-hours, leaving about 420 iterations of headroom - not enough.

---

## Corrected SA vs SST comparison

| | SA | SST v2 | difference |
|---|---|---|---|
| 6 deg  C_L | 0.304170 | 0.307588 | **+1.12%** |
| 6 deg  C_D | 0.020181 | 0.018951 | **-6.10%** |
| 10 deg C_L | 0.492868 | 0.481590* | **-2.29%** |
| 10 deg C_D | 0.041671 | 0.041378* | -0.70% |

*provisional, still drifting

**The models cross over.** At 6 degrees SST predicts more lift than SA; at 10
degrees it predicts less. That is a more interesting result than the apparent
agreement in v1, and it is consistent with SST's shear stress transport limiter
capping eddy viscosity in adverse pressure gradient - which suppresses lift
where separation begins, and is what the model is designed to do.

Caveat: the 10 degree SST value is provisional, so the crossover should not be
over-interpreted until that run is converged.

## Final status

| Case | v1 | v2 | Reported value |
|---|---|---|---|
| 6 deg SA | converged | not rerun | v1 |
| 6 deg SST | oscillating, invalid | **converged** | v2 |
| 10 deg SA | converged | not rerun | v1 |
| 10 deg SST | oscillating, invalid | drifting, provisional | v2, flagged |
