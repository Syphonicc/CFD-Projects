# N2A Hybrid Wing–Body — Compressible RANS Study

**Status: in progress.** This README is written before results exist and is updated as work proceeds. Sections marked *pending* have not been done yet.

---

## Objective

Steady compressible RANS of the NASA N2A hybrid wing–body at low speed, using `rhoSimpleFoam` in OpenFOAM, at two angles of attack with two turbulence models.

The deliverable is the **comparison**, not the coefficients on their own. Two axes:

1. **Compressible vs incompressible treatment.** M∞ = 0.2 is often treated as effectively incompressible, but local acceleration over the upper surface can push past that. Whether it does — and where — is part of what this study reports.
2. **Spalart–Allmaras vs k-ω SST** at identical conditions. Where they agree, where they diverge, and why.

**Reference:** Aprovitola, A.; Aurisicchio, F.; Di Nuzzo, P.E.; Pezzella, G.; Viviani, A. *Low Speed Aerodynamic Analysis of the N2A Hybrid Wing–Body.* Aerospace 2022, 9(2), 89. [doi:10.3390/aerospace9020089](https://doi.org/10.3390/aerospace9020089) (open access)

Secondary: Almosnino, D. *A Low Subsonic Study of the NASA N2A Hybrid Wing-Body Using an Inviscid Euler-Adjoint Solver*, AIAA 2016-3267.

---

## Run matrix

Four runs.

| Run | α | Turbulence model | Status |
|---|---|---|---|
| 1 | 6° | Spalart–Allmaras | pending |
| 2 | 6° | k-ω SST | pending |
| 3 | 10° | Spalart–Allmaras | pending |
| 4 | 10° | k-ω SST | pending |

**Why these angles.** The reference reports attached flow up to about 10°, with a leading-edge vortex emanating from the inboard wing and rolling up at around α = 10°, and linear C_L from −5° to 13°. So 6° sits in clean attached flow where the two models should broadly agree, and 10° sits at vortex onset where they are expected to diverge. The divergence is the interesting result.

---

## Flow conditions

| Parameter | Value |
|---|---|
| Mach number | 0.20 |
| Reynolds number (L_ref) | 6.60 × 10⁶ |
| Solver | `rhoSimpleFoam` (compressible, steady) |
| Turbulence models | Spalart–Allmaras and k-ω SST |
| Near-wall treatment | **Wall-resolved, y⁺ < 1** |
| Configuration | Cruise: wing–body, no nacelles, no landing gear, no LE droop, control surfaces undeflected |

---

## Geometry

Source: OpenVSP model *NASA N2A Hybrid Wing Body* (author Farhan Malik, file ID 349), obtained via VSP Airshow. Same watertight aeroshape used by the reference paper. Licensed CC0.

> **Note on the reference link.** The paper cites `hangar.openvsp.org/vspfiles/349`. That host now returns HTTP 500 — the OpenVSP model repository has migrated to VSP Airshow. Same model, same author, same file ID.

### Scale check — mandatory before meshing

The Hangar listing states the model units are **feet**. The paper's dimensions are metric. A scale factor of 0.3048 is therefore expected, and must be verified rather than assumed: mismatched scale would silently invalidate every non-dimensional coefficient downstream.

| Quantity | Paper value | Model as-downloaded | Verified |
|---|---|---|---|
| Wing span | 64.92 m | *pending* | ☐ |
| Body length | 45.10 m | *pending* | ☐ |
| Reference area S_ref | 925.2 m² | *pending* | ☐ |
| Reference length L_ref | 26.52 m | *pending* | ☐ |

### Reference geometry parameters

| Parameter | Value |
|---|---|
| Wing span | 64.92 m |
| Body length | 45.10 m |
| Reference area S_ref | 925.2 m² |
| Reference length L_ref | 26.52 m |
| Moment reference centre | 24.33 m aft of nose (53.94% body length) |
| Quarter-chord sweep (outboard) | 24.2° |
| Wing twist at tip | −8.87° (linear variation, washout) |
| Thickness taper t/c | ~8% |
| Vertical tail cant | 10°, aft location |

The Hangar model uses 34 wing sections for CAD fidelity, so the STL export is expected to be dense and may need cleanup before meshing.

---

## Fluid properties

Air as a perfect gas.

| Property | Value |
|---|---|
| c_p | 1006 J/kg·K |
| Thermal conductivity k | 0.0242 W/m·K (constant) |
| Viscosity | Sutherland law |

---

## Boundary conditions

| Patch | Condition |
|---|---|
| Aircraft surface | No-slip, adiabatic wall |
| Farfield inlet | Pressure farfield |
| Outlet | Pressure outlet |
| Symmetry plane | `symmetryPlane` |

Farfield placed at ~50 body lengths upstream and downstream, matching the reference.

---

## Method

Angle of attack is imposed by **rotating the freestream vector**, not the mesh — one mesh serves both angles:

```
U∞      = |U| (cos α, sin α, 0)
dragDir =     (cos α, sin α, 0)
liftDir =     (−sin α, cos α, 0)
```

The same mesh is used for all four runs, so any difference between them is attributable to the turbulence model or the angle, not to discretisation.

---

## Post-processing

For each run:

- Integrated coefficients: C_L, C_D, C_m
- Surface C_p and C_f distributions at spanwise stations (13.4%, 30.5%, 51.0%, 90.6% semi-span, matching the reference)
- **Mach number field**, to identify local regions exceeding the freestream value of 0.2 — central to the compressibility question, not optional
- y⁺ distribution on the aircraft surface, to verify the wall-resolved requirement was met
- Convergence history of residuals and force coefficients

---

## Scope and stated limitations

Stated up front rather than discovered later.

**Mesh resolution.** The reference used 15–17 M cells (half body) with a convergence study spanning coarse (~7 M), medium (~14.4 M) and fine (~17 M), reporting <2% change in C_L and <3% in C_D beyond the medium grid. The mesh here is built to satisfy the y⁺ < 1 requirement first; the resulting cell count determines the compute route and is reported once known. No grid-independence claim is made unless a convergence study is actually run.

**Cell topology.** The reference used polyhedral cells converted from tet/prism in ICEM-CFD. This study uses `snappyHexMesh` (hex-dominant with prism layers). Different discretisation error characteristics.

**Half-model symmetry.** Valid at zero sideslip. Cannot represent asymmetric flow phenomena, which is a real consideration at 10° where vortex rollup begins. Side force, rolling and yawing moments are zero by construction and are not reported.

**Configuration mismatch (inherited from the reference).** The reference notes that experimental C_p data are for the *baseline* configuration (with LE droop and nacelles) while the CFD is the *cruise* configuration (without). Discrepancies near the leading edge at the outboard stations are attributable to the droop. This study inherits the same mismatch.

---

## Comparison targets

Populated as results arrive. Values read from figures rather than tables are labelled as such, and carry their own extraction error.

| Source | α | C_L | C_D | C_m |
|---|---|---|---|---|
| Experiment (Langley 14×22, T597/T612) | 6° | *pending* | *pending* | *pending* |
| Reference CFD — FLUENT | 6° | *pending* | *pending* | *pending* |
| Reference CFD — SU2 | 6° | *pending* | *pending* | *pending* |
| **This study — SA** | 6° | *pending* | *pending* | *pending* |
| **This study — SST** | 6° | *pending* | *pending* | *pending* |
| Experiment | 10° | *pending* | *pending* | *pending* |
| Reference CFD — FLUENT | 10° | *pending* | *pending* | *pending* |
| Reference CFD — SU2 | 10° | *pending* | *pending* | *pending* |
| **This study — SA** | 10° | *pending* | *pending* | *pending* |
| **This study — SST** | 10° | *pending* | *pending* | *pending* |

Note that the reference CFD and the experimental data do not agree with each other. Both are reported rather than one being selected as *the* target.

---

## Compute environment

| | |
|---|---|
| CPU | AMD Ryzen 7 4800H (8 cores) |
| RAM | 16 GB |
| OS | Fedora Linux |
| OpenFOAM | v2512 (ESI) |
| Geometry | OpenVSP 3.51.2 |

Mesh generation is being done locally. Solve compute is to be determined once the mesh size is known.

---

## Progress log

| Date | Step | Status |
|---|---|---|
| 2026-08-12 | OpenVSP 3.51.2 installed on Fedora | done |
| 2026-08-12 | Geometry obtained (VSP Airshow, file 349) | done |
| — | Scale verification against reference dimensions | pending |
| — | STL export and surface cleanup | pending |
| — | Reference value extraction from paper | pending |
| — | Domain sizing and background mesh | pending |
| — | `snappyHexMesh` generation | pending |
| — | Mesh quality check and y⁺ estimate | pending |
| — | Case setup: `rhoSimpleFoam`, thermophysical properties | pending |
| — | Run 1: α = 6°, SA | pending |
| — | Run 2: α = 6°, SST | pending |
| — | Run 3: α = 10°, SA | pending |
| — | Run 4: α = 10°, SST | pending |
| — | Post-processing and comparison | pending |

---

## Repository structure

```
n2a-validation/
├── README.md
├── geometry/            OpenVSP source, STL export, scale-check notes
├── reference_data/      Values extracted from the papers, with provenance
├── mesh/                snappyHexMesh dictionaries, quality reports
├── case_alpha6_SA/
├── case_alpha6_SST/
├── case_alpha10_SA/
├── case_alpha10_SST/
├── tools/               Post-processing and plotting scripts
├── figures/             Mesh views, flow fields, comparison plots
└── notes/               Running log of decisions and problems
```

Meshes and time directories are not committed (size). Dictionaries, scripts and the geometry are, so the mesh is regenerable.

---

## Provenance

Every reference number here is labelled with where it came from: tabulated in a paper, digitised from a figure, or computed in this study. Figure-digitised values are not treated as exact.

---

## AI assistance

Script generation and drafting in this repository were done with AI assistance. Setup decisions, diagnosis and interpretation are the author's, and every committed file is understood and defensible by the author.
