# N2A Hybrid Wing–Body — Compressible RANS Study

**Status: in progress.** Written before results exist, updated as work proceeds. Sections marked *pending* have not been done yet.

---

## Objective

Steady compressible RANS of the NASA N2A hybrid wing–body at low speed using `rhoSimpleFoam`, at two angles of attack with two turbulence models.

The deliverable is the **comparison**, not the coefficients alone. Two axes:

1. **Compressible vs incompressible treatment.** M∞ = 0.2 is often treated as effectively incompressible, but local acceleration over the upper surface can push past that. Whether it does, and where, is part of what this study reports.
2. **Spalart–Allmaras vs k-ω SST** at identical conditions — where they agree, where they diverge, and why.

**Primary reference:** Aprovitola, A.; Aurisicchio, F.; Di Nuzzo, P.E.; Pezzella, G.; Viviani, A. *Low Speed Aerodynamic Analysis of the N2A Hybrid Wing–Body.* Aerospace 2022, 9(2), 89. [doi:10.3390/aerospace9020089](https://doi.org/10.3390/aerospace9020089)

**Secondary:** Almosnino, D. *A Low Subsonic Study of the NASA N2A Hybrid Wing-Body Using an Inviscid Euler-Adjoint Solver*, AIAA 2016-3267.

Comparison data are taken from Aprovitola et al.

---

## Run matrix

| Run | α | Turbulence model | Status |
|---|---|---|---|
| 1 | 6° | Spalart–Allmaras | pending |
| 2 | 6° | k-ω SST | pending |
| 3 | 10° | Spalart–Allmaras | pending |
| 4 | 10° | k-ω SST | pending |

All four on a common mesh, so any difference between runs is attributable to the model or the angle, not to discretisation.

**Why these angles.** The reference reports attached flow to about 10°, with a leading-edge vortex emanating from the inboard wing and rolling up at around α = 10°, and linear C_L from −5° to 13°. So 6° is clean attached flow where the two models should broadly agree; 10° is at vortex onset where they are expected to diverge.

---

## Scale — resolved

The reference runs two Reynolds numbers: **6.60 × 10⁶** for the Langley 14×22 wind tunnel campaign, and **1.27 × 10⁸** for free flight. This study targets the wind tunnel condition, so the geometry is the **5.8% scale tunnel model**, not the full-scale aircraft.

### Conversion chain

The OpenVSP model is dimensioned in **feet** at **full scale**. Two factors apply:

```
feet → metres        0.3048
full scale → 5.8%    0.058
combined             0.0176784
```

### Verification

Full-scale check, read from the OpenVSP Plan tab before scaling:

| Quantity | Model (ft) | × 0.3048 (m) | Paper | Agreement |
|---|---|---|---|---|
| Projected span | 212.99992 | 64.922 | 64.92 | exact |
| MAC | 86.94289 | 26.500 | 26.52 (L_ref) | 0.08% |
| Curved area | 9992.70833 | 928.39 | 925.2 (S_ref) | 0.34% |

Note it is the **projected** span that matches, not the total span of 213.24 ft; the difference is dihedral.

Wind-tunnel scale check, from `surfaceCheck` on the exported STL:

| Quantity | Target | Measured | Status |
|---|---|---|---|
| Span (y-extent) | 3.7655 m | 3.7655 m | ✅ exact |
| Body length (x-extent) | 2.616 m | 2.6235 m | ✅ 0.28% |
| Centreline | y = 0 | −1.88275 to +1.88275 | ✅ symmetric |
| Watertight | closed | closed, all edges connected to two faces | ✅ |
| Parts | 3 | 3 (Wing_Body + 2 vertical tails) | ✅ |

### Reference dimensions at wind-tunnel scale

| Quantity | Full scale | × 0.058 |
|---|---|---|
| Span | 64.92 m | 3.766 m |
| Body length | 45.10 m | 2.616 m |
| Reference length L_ref | 26.52 m | 1.538 m |
| Reference area S_ref | 925.2 m² | 3.112 m² |
| Moment reference centre | 24.33 m aft of nose | 1.411 m |

S_ref scales by 0.058², not 0.058.

### Why scaling was done on the STL, not in OpenVSP

OpenVSP has no units setting — the developers state the tool is unit-agnostic and that scaling is the mechanism for unit conversion. Per-component scaling is documented to leave positional offsets unscaled, which would silently displace the vertical tails relative to the body. `surfaceTransformPoints` applies a single uniform factor to every vertex of the triangulated surface, with no parametric relationships to go wrong:

```bash
surfaceTransformPoints -scale '(0.0176784 0.0176784 0.0176784)' n2a_feet.stl n2a_wt.stl
```

Both the unscaled (`n2a_feet.stl`) and scaled (`n2a_wt.stl`) surfaces are committed so the conversion is auditable.

---

## Flow conditions

Freestream state reconstructed from M and Re, per instruction from Othrys:
**match Re and M, do not chase density or viscosity.**

The reference reports only M and Re, not the raw freestream state. This is
normal for an open-circuit tunnel such as the Langley 14x22, where ambient
density and viscosity drift day-to-day with conditions, so M and Re are the
invariants and the dimensional state is reconstructed rather than quoted.

Fixing T = 288.15 K sets both the speed of sound and the Sutherland
viscosity; density then follows from the target Reynolds number:

| Parameter | Value |
|---|---|
| Mach number | 0.20 |
| Reynolds number (L_ref) | 6.60 x 10^6 |
| Reference length L_ref | 1.5382 m |
| Freestream velocity U | 68.05 m/s |
| Freestream temperature T | 288.15 K |
| Freestream pressure p | 93,290 Pa |
| Freestream density rho | 1.1281 kg/m3 |
| Dynamic viscosity mu | 1.7893 x 10^-5 Pa.s |
| Solver | `rhoSimpleFoam` (compressible, steady) |
| Turbulence models | Spalart-Allmaras, k-omega SST |
| Near-wall treatment | wall-resolved, y+ < 1 |
| Configuration | cruise: wing-body, no nacelles, no landing gear, no LE droop, controls undeflected |

Note the resulting pressure is below atmospheric. This is a consequence of
reconstructing from Re at fixed T and M, not a claim about the tunnel's
actual operating state.



### Fluid properties

Air as a perfect gas.

| Property | Value |
|---|---|
| c_p | 1006 J/kg·K |
| Thermal conductivity k | 0.0242 W/m·K (constant) |
| Viscosity | Sutherland law |

---

## Geometry

Source: OpenVSP model *NASA N2A Hybrid Wing Body* (author Farhan Malik, file ID 349), obtained via VSP Airshow. Same watertight aeroshape used by the reference. Licensed CC0.

> **Note on the reference link.** The paper cites `hangar.openvsp.org/vspfiles/349`, which now returns HTTP 500 — the repository has migrated to VSP Airshow. Same model, same author, same file ID. The `.vsp3` is committed here so the study is self-contained.

The model comprises `Wing_Body` and `Vertical_Tails` only — no nacelles or landing gear — matching the reference's cruise configuration. It uses 34 wing sections for CAD fidelity, so the STL export is dense (5.6 MB, ~19,000 triangles).

STL exported as a **tagged multi-solid** file, giving four named solids (`Wing_Body_S_Surf0/1`, `Vertical_Tails_S_Surf0/1` — port and starboard halves of each). This allows per-region refinement control in `snappyHexMesh` and automatic patch naming.

---

## Boundary conditions

| Patch | Condition |
|---|---|
| Aircraft surface | no-slip, adiabatic wall |
| Farfield inlet | pressure farfield |
| Outlet | pressure outlet |
| Symmetry plane | `symmetryPlane` at y = 0 |

Farfield at ~50 body lengths upstream and downstream, matching the reference.

Angle of attack is imposed by rotating the freestream vector, not the mesh:

```
U∞      = |U| (cos α, sin α, 0)
dragDir =     (cos α, sin α, 0)
liftDir =     (−sin α, cos α, 0)
```

---

## Post-processing

Per run:

- Integrated coefficients C_L, C_D, C_m
- Surface C_p and C_f at 13.4%, 30.5%, 51.0% and 90.6% semi-span, matching the reference
- **Mach number field**, to identify local regions exceeding the freestream 0.2 — central to the compressibility question
- y⁺ distribution on the surface, verifying the wall-resolved requirement was met
- Convergence history of residuals and force coefficients

---

## Scope and stated limitations

**Mesh resolution.** The reference used 15–17 M cells (half body) with a convergence study across coarse (~7 M), medium (~14.4 M) and fine (~17 M), reporting <2% change in C_L and <3% in C_D beyond the medium grid. The mesh here is built to satisfy y⁺ < 1 first; the resulting cell count determines the compute route and is reported once known. No grid-independence claim is made unless a convergence study is actually run.

**Cell topology.** The reference used polyhedral cells converted from tet/prism in ICEM-CFD. This study uses `snappyHexMesh` (hex-dominant with prism layers) — different discretisation error characteristics.

**Half-model symmetry.** Valid at zero sideslip. Cannot represent asymmetric flow phenomena, a real consideration at 10° where vortex rollup begins. Side force, rolling and yawing moments are zero by construction and are not reported.

**Configuration mismatch (inherited from the reference).** The reference notes that experimental C_p data are for the *baseline* configuration (with LE droop and nacelles) while its CFD is the *cruise* configuration (without). Discrepancies near the leading edge at outboard stations are attributable to the droop. This study inherits the same mismatch.

---

## Comparison targets

Populated as results arrive. Values read from figures rather than tables are labelled, and carry their own extraction error.

| Source | α | C_L | C_D | C_m |
|---|---|---|---|---|
| Reference CFD — FLUENT | 6° | *pending* | *pending* | *pending* |
| Reference CFD — SU2 | 6° | *pending* | *pending* | *pending* |
| **This study — SA** | 6° | *pending* | *pending* | *pending* |
| **This study — SST** | 6° | *pending* | *pending* | *pending* |
| Reference CFD — FLUENT | 10° | *pending* | *pending* | *pending* |
| Reference CFD — SU2 | 10° | *pending* | *pending* | *pending* |
| **This study — SA** | 10° | *pending* | *pending* | *pending* |
| **This study — SST** | 10° | *pending* | *pending* | *pending* |

---

## Compute environment

| | |
|---|---|
| CPU | AMD Ryzen 7 4800H (8 cores) |
| RAM | 16 GB |
| OS | Fedora Linux |
| OpenFOAM | v2512 (ESI) |
| Geometry | OpenVSP 3.51.2 |

Mesh generation local. Solve compute to be determined once mesh size is known.

---

## Progress log

| Date | Step | Status |
|---|---|---|
| 2026-08-12 | OpenVSP 3.51.2 installed on Fedora | done |
| 2026-08-12 | Geometry obtained (VSP Airshow, file 349) | done |
| 2026-08-13 | Full-scale verification against reference dimensions | done |
| 2026-08-13 | Tagged multi-solid STL export | done |
| 2026-08-13 | Scaled to 5.8% wind tunnel model, watertight verified | done |
| 2026-08-13 | Freestream state resolved (match Re and M) | done |
| — | Reference value extraction from paper | pending |
| — | Domain sizing and background mesh | pending |
| — | `snappyHexMesh` generation | pending |
| — | Mesh quality check and y⁺ verification | pending |
| — | Case setup: `rhoSimpleFoam`, thermophysical properties | pending |
| — | Runs 1–4 | pending |
| — | Post-processing and comparison | pending |

---

## Repository structure

```
n2a-validation/
├── README.md
├── geometry/
│   ├── nasan2ahybridwingbody.vsp3    OpenVSP source (feet, full scale)
│   ├── n2a_feet.stl                  tagged multi-solid export, unscaled
│   └── n2a_wt.stl                    scaled to 5.8% WT model, metres
├── reference_data/
├── mesh/
├── case_alpha6_SA/  case_alpha6_SST/
├── case_alpha10_SA/ case_alpha10_SST/
├── tools/
├── figures/
└── notes/
```

Meshes and time directories are not committed (size). Dictionaries, scripts and geometry are, so the mesh is regenerable.

---

## Provenance

Every reference number here is labelled with where it came from: tabulated in a paper, digitised from a figure, or computed in this study. Figure-digitised values are not treated as exact.

---

## AI assistance

Script generation and drafting in this repository were done with AI assistance. Setup decisions, diagnosis and interpretation are the author's, and every committed file is understood and defensible by the author.
