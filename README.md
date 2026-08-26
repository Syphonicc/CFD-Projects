# CFD Projects

OpenFOAM work by Suvam Samanta. Two validation studies against published
reference data, and a set of tutorial cases kept for reference.

---

## Validation studies

These reproduce published experimental or computational results and report
where they agree and where they do not.

### [N2A hybrid wing–body](validation/n2a-hybrid-wing-body/) — compressible RANS

Steady compressible RANS of the NASA N2A hybrid wing–body at M = 0.20 and
Re = 6.60 × 10⁶ on a 6.0 million cell half model, at two angles of attack with
two turbulence models. Carried out for Othrys Aviation.

| | C_L | C_D | L/D |
|---|---|---|---|
| 6° Spalart–Allmaras | 0.3042 | 0.0202 | 15.1 |
| 6° k-ω SST | 0.3076 | 0.0190 | 16.2 |
| 10° Spalart–Allmaras | 0.4929 | 0.0417 | 11.8 |
| 10° k-ω SST | 0.4816* | 0.0414* | 11.6 |

<sub>*provisional, still drifting at 3000 iterations</sub>

**Grid independent.** Refining from 2.11 to 6.01 million cells changes C_L by
0.5%, a tighter convergence statement than the reference study makes about its
own grids.

**Compressible treatment justified by measurement.** Local Mach number reaches
0.37 against a freestream of 0.20, so density varies by 6–7%.

**Compared against all five reference datasets** from Aprovitola et al. (2022),
digitised from the published figures so that every difference is stated against
a named source rather than against "the reference". Lift sits 10–13% below both
wind tunnel campaigns and within 1% of Cart3D. That grouping is reported as an
observation; no explanation for it has been established.

[Technical report (PDF, 16 pages)](validation/n2a-hybrid-wing-body/report/) ·
[mesh study](validation/n2a-hybrid-wing-body/notes/mesh_study_findings.md) ·
[solver setup findings](validation/n2a-hybrid-wing-body/notes/solver_setup_findings.md)

---

### [NACA 0012](validation/naca0012-tmr/) — Turbulence Modeling Resource

Validation against the NASA Langley TMR case at Re = 6 × 10⁶, α = 10°, using
the NASA-supplied 897 × 257 grid and Spalart–Allmaras.

| | This work | CFL3D (SA) | Difference |
|---|---|---|---|
| C_L | 1.0835 | 1.0909 | −0.68% |
| C_D | 0.01023 | 0.01231 | −16.9% |

Lift agrees to within the spread of the seven TMR reference codes. Drag is not
claimed as validated: the reference applies a farfield point-vortex correction
that this setup does not, and the turbulence convection scheme is first order.

The repository keeps all three iterations rather than only the working one.
[Iteration 2](validation/naca0012-tmr/iteration2_nasa_grid/) converged cleanly
to a physically impossible answer — negative drag — because the freestream eddy
viscosity had been inherited from a tutorial at a different Reynolds number,
giving ν_t/ν of 8.4 × 10⁵ instead of 0.21. It is kept because a converged wrong
answer is more instructive than a right one.

---

## Tutorial cases

Standard OpenFOAM tutorials worked through while learning the toolchain. Kept
for reference; no validation is claimed.

| Case | Description |
|---|---|
| [lid-driven-cavity](tutorials/lid-driven-cavity/) | Incompressible flow in a 2D square cavity. Five variants: base, fine, graded, clipped, high Re |
| [elbow](tutorials/elbow/) | Incompressible viscous flow through a 90° bend, Fluent mesh import |
| [motorbike](tutorials/motorbike/) | External aerodynamics using snappyHexMesh and simpleFoam, steady RANS with k-ω SST, ~353k cells |

---

## Environment

OpenFOAM v2512 (ESI) on Fedora Linux. Meshing with snappyHexMesh; geometry from
OpenVSP. Post-processing in Python with NumPy and matplotlib, and in ParaView.
Larger solver runs on CloudHPC.

Meshes and solution fields are not committed on account of size. Every case is
reproducible from the committed dictionaries and scripts.

## A note on AI assistance

Script generation and drafting in this repository were done with AI assistance.
Setup decisions, diagnosis and interpretation are mine, and every committed file
is one I understand and can defend.
