# N2A Hybrid Wing–Body — Compressible RANS Study

Steady compressible RANS of the NASA N2A hybrid wing–body at low speed using
`rhoSimpleFoam`, at two angles of attack with two turbulence models.

**Status: four production runs complete and converged.** Reference values from
the source paper's figures are not yet digitised, so the comparison column is
outstanding.

**Primary reference:** Aprovitola, A.; Aurisicchio, F.; Di Nuzzo, P.E.;
Pezzella, G.; Viviani, A. *Low Speed Aerodynamic Analysis of the N2A Hybrid
Wing–Body.* Aerospace 2022, 9(2), 89.
[doi:10.3390/aerospace9020089](https://doi.org/10.3390/aerospace9020089)

---

## Results

All four converged on `residualControl` at 1e-7, coefficients flat to five
figures over the final iterations.

| | C_L | C_D | C_D press | C_D visc | C_m | L/D | iter |
|---|---|---|---|---|---|---|---|
| 6° SA | 0.304170 | 0.020181 | 0.012158 | 0.008023 | 0.000259 | 15.07 | 2000 |
| 6° SST | 0.303231 | 0.019944 | 0.012257 | 0.007687 | 0.001050 | 15.20 | 559 |
| 10° SA | 0.492868 | 0.041671 | 0.033762 | 0.007909 | −0.001498 | 11.83 | 767 |
| 10° SST | 0.495996 | 0.040844 | 0.034274 | 0.006570 | −0.002860 | 12.14 | 792 |

Lift slope between the two angles: **0.0472/deg (SA)**, **0.0482/deg (SST)** —
consistent with the linear range the reference describes (−5° to 13°).

Side force, rolling and yawing moments are zero by construction on a half model
at zero sideslip and are not reported.

---

## Mesh independence

α = 6°, SA, run on both meshes:

| | 2.11 M | 6.00 M | change |
|---|---|---|---|
| C_L | 0.302633 | 0.304170 | **+0.5%** |
| C_D | 0.020129 | 0.020181 | +0.26% |
| y+ mean | 32.36 | 33.04 | +2% |

Nearly 3× the cells for half a percent in lift. Tighter than the reference's own
convergence study, which reported under 2% in C_L and under 3% in C_D between
its medium (14.4 M) and fine (17 M) grids.

**Consequence:** any remaining discrepancy against the reference is not grid
resolution. Further refinement will not change the answer.

---

## Compressibility

The brief asked whether M∞ = 0.2 can be treated as effectively incompressible.
Maximum local Mach number, sampled on cutting planes at the four span stations:

| | 13.4% | 30.5% | 51.0% | 90.6% |
|---|---|---|---|---|
| 6° SA | 0.233 | 0.293 | 0.271 | 0.238 |
| 6° SST | 0.233 | 0.291 | 0.269 | 0.237 |
| 10° SA | 0.251 | **0.369** | 0.299 | 0.275 |
| 10° SST | 0.253 | **0.371** | 0.298 | 0.275 |

Freestream is 0.200. Local flow reaches **1.46× freestream at 6°** and
**1.85× at 10°**, peaking at the 30.5% station in both cases. At M = 0.37 the
density variation is around 6–7%.

The compressible treatment was warranted, and this is measured rather than
assumed.

---

## Spalart–Allmaras vs k-ω SST

The study was designed on the premise that the two models would agree at 6°
(attached flow) and diverge at 10°, where the reference describes a leading-edge
vortex rolling up. **They do not diverge.**

| | C_L difference | C_D difference |
|---|---|---|
| 6° | −0.31% | −1.2% |
| 10° | +0.63% | −2.0% |

Where they do differ is **viscous drag**, and the gap grows with incidence:

| | SA | SST | difference |
|---|---|---|---|
| 6° | 0.008023 | 0.007687 | −4.2% |
| 10° | 0.007909 | 0.006570 | **−16.9%** |

So the models are behaving differently in the boundary layer, and increasingly
so. It does not reach the total because pressure drag dominates — 81% of C_D at
10°.

**Two candidate explanations, neither tested:**

1. **Wall functions may mask the difference.** At y+ ≈ 33 both models take their
   near-wall behaviour from `nutUSpaldingWallFunction` rather than from their own
   near-wall formulations — which is precisely where SA and SST differ most.
2. **The vortex may not be resolved.** Near-field cells are 15.6 mm.

A genuine y+ < 1 mesh would distinguish these.

---

## Pressure distributions

C_p extracted at the reference's four span stations (13.4%, 30.5%, 51.0%,
90.6% semi-span) for all four cases. Plot: `figures/cp_stations.png`.
Sectional data: `analysis/*/cp_*.dat`.

Suction peaks deepen with incidence as expected — at the 30.5% station C_p,min
goes from −1.63 at 6° to −3.74 at 10°.

The **51% station shows a secondary suction bump at x/c ≈ 0.22**, present at 10°
and absent at 6°, in both turbulence models. This is consistent with the
leading-edge vortex the reference describes, though not positively confirmed —
that would need a Q-criterion visualisation.

**Known artifact:** C_p,min at the 90.6% station reads −10.6. It comes from three
faces at x/c = 0.98, which is the degenerate trailing-edge sliver documented in
`notes/mesh_study_findings.md`. Not physics.

---

## Flow conditions

Freestream reconstructed from M and Re, per instruction from Othrys: match Re
and M, do not chase density or viscosity. The reference reports only M and Re,
which is normal for an open-circuit tunnel where ambient state drifts.

| Parameter | Value |
|---|---|
| Mach number | 0.20 |
| Reynolds number (L_ref) | 6.60 × 10⁶ |
| Reference length L_ref | 1.53816 m |
| Freestream velocity U | 68.05 m/s |
| Temperature T | 288.15 K |
| Pressure p | 93,290 Pa |
| Density ρ | 1.1281 kg/m³ |
| Dynamic viscosity μ | 1.7893 × 10⁻⁵ Pa·s |
| Solver | `rhoSimpleFoam` |
| Turbulence models | Spalart–Allmaras, k-ω SST |
| Configuration | cruise: wing–body, no nacelles, no landing gear, no LE droop |

Angle of attack imposed by rotating the freestream vector in the **x–z plane**
(this geometry has span along y, vertical along z):

```
U∞      = |U| (cos α, 0, sin α)
liftDir =     (−sin α, 0, cos α)
dragDir =     (cos α,  0, sin α)
```

Reference values for force coefficients: `Aref` = 1.55619 m² (**half** of
S_ref = 3.11237, because this is a half model — half the area with half the
force gives full-model coefficients directly), `lRef` = 1.53816 m,
`CofR` = (1.41510, 0, 0).

---

## Mesh

| | |
|---|---|
| Cells | 6,006,252 (5.68 M hex, 317 k poly) |
| Surface faces | 93,457 (~6.5 mm) |
| Layer coverage | 93.2%, 14.0 of 25 layers |
| Faces with layers | 98.45% (1,447 without, at tail root and TEs) |
| First layer thickness | 1.25 × 10⁻⁵ m |
| y+ | min 0.51, mean 33.0, max 684 |
| Max skewness | 2.4996 |
| Max aspect ratio | 623 |
| Non-orthogonality | 74.9 max, 4.69 average |
| `checkMesh` | **Mesh OK** |

Domain at 50 body lengths, matching the reference. Half model, symmetry plane at
y = 0.

Surface generated with OpenVSP's own CFD Mesh tool, which intersects components
before tessellating: single connected watertight part, 171,858 triangles.

**Fifteen meshing runs.** The limiter was `meshQualityControls` truncating layer
growth, not the geometry, layer thickness, refinement level, or shrinking
algorithm. Full parameter study, tested-and-rejected settings, and the six
meshing tools that did not work: `notes/mesh_study_findings.md`.

---

## Stated limitations

**y+ is not below 1.** Mean 33, max 684. Despite a 12.5 µm design first layer,
snappyHexMesh achieves 14 of 25 layers and compresses the stack when it
truncates, and 1.55% of faces have no layers at all. Thresholding the y+ field
shows everything above 100 confined to the wing and tail leading edges and the
wing-body junction — narrow bands where wall shear peaks, not spread over the
surface. `nutUSpaldingWallFunction` is valid across all y+, so the solution is
legitimate, but the mesh is effectively wall-function over most of the surface.

**Refining the mesh does not fix y+.** 2.11 M → 6 M changed it by 2%, because
y+ depends on wall-normal spacing and surface refinement changes tangential
resolution. Only a thinner first layer would.

**Half-model symmetry.** Valid at zero sideslip. Cannot represent asymmetric
flow phenomena, a real consideration at 10° where vortex rollup begins.

**Cell topology.** The reference used polyhedral cells converted from tet/prism
in ICEM-CFD. This study uses `snappyHexMesh` (hex-dominant with prism layers).

**Configuration mismatch, inherited from the reference.** Experimental C_p data
are for the *baseline* configuration (with LE droop and nacelles) while the CFD
is *cruise* (without). Discrepancies near the leading edge at outboard stations
are attributable to the droop.

**Upper/lower surface split in the C_p extraction** is geometric — about the
local mid-z at each chordwise position — because a blended body has no camber
line to work from. Reliable on the outboard wing sections, approximate near the
thick centrebody.

---

## Compute

Meshing local (Fedora, Ryzen 7 4800H, 16 GB). The 6 M mesh needs 32 GB swap and
`scotch` decomposition to build; ~14 M does not complete on this machine.

Solver runs on CloudHPC: 32 vCPU `highcore`, `openFoam-v2512` — an exact match
for the local build, so cases ran unchanged. **~31 vCPU-hours per run**, 49 min
wall clock at 6 M cells. Roughly 130 of the 300 free trial used.

---

## Outstanding

- **Digitise Figures 12–15** for verified reference values. No comparison
  column exists yet; reading the figures by eye is not sufficient for a
  validation table.
- Q-criterion visualisation to confirm the leading-edge vortex at 10°.
- Optional: a y+ < 1 mesh to test whether the SA/SST agreement is physical or a
  wall-function artifact.

---

## Repository structure

```
n2a-validation/
├── README.md
├── geometry/          OpenVSP source, STL exports, scale-check notes
├── mesh/system/       all snappyHexMesh dictionaries incl. PRODUCTION
├── case_alpha6_SA/    case definitions (0/, constant/, system/)
├── case_alpha6_SST/
├── case_alpha10_SA/
├── case_alpha10_SST/
├── results/           coefficient histories, y+ data, solver logs
├── analysis/          sectional Cp data at the four span stations
├── figures/           cp_stations.png
├── tools/             make_cases.py, extract.sh, cp_plot.py, memguard.sh
└── notes/             mesh study findings, solver setup findings
```

Meshes and solution fields are not committed (1.1 GB and 3.9 GB respectively);
both are regenerable from the committed dictionaries.

---

## Provenance

Every reference number here is labelled with where it came from: tabulated in a
paper, digitised from a figure, or computed in this study. No figure-digitised
values are currently included, because none have been extracted yet.

## AI assistance

Script generation and drafting in this repository were done with AI assistance.
Setup decisions, diagnosis and interpretation are the author's, and every
committed file is understood and defensible by the author.
