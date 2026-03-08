# Lid-Driven Cavity Flow -> OpenFOAM Tutorial

A complete study of incompressible laminar and turbulent flow in a two-dimensional square cavity using OpenFOAM v2512 on Fedora Linux. This covers mesh refinement, mesh grading, Reynolds number effects, and turbulence modelling using the k-ε model.

---

## Physical Problem

A square cavity of side length 0.1 m with all four boundaries treated as walls. The top wall (lid) moves horizontally at 1 m/s while the remaining three walls are stationary. The moving lid drags fluid through viscosity, generating a large recirculating vortex inside the cavity.

```
        U = 1 m/s →  (moving lid)
    ┌─────────────────────┐
    │                     │
    │    recirculating    │
    │       vortex        │  walls (no-slip)
    │                     │
    └─────────────────────┘
         stationary wall
```

**Why this case matters:** The lid-driven cavity is one of the most studied problems in computational fluid dynamics. It has well-documented benchmark data (Ghia et al. 1982) for vortex centre location and velocity profiles at various Reynolds numbers, making it ideal for solver validation.

---

## Cases Studied

This repository contains five progressively complex cases:

| Case | Mesh | Re | Solver | Key Concept |
|---|---|---|---|---|
| cavity | 20×20 uniform | 10 | icoFoam | Baseline laminar flow |
| cavityFine | 40×40 uniform | 10 | icoFoam | Mesh refinement study |
| cavityGrade | 10×10 graded | 10 | icoFoam | Wall-graded mesh |
| cavityHighRe | 20×20 uniform | 100 | icoFoam | Reynolds number effects |
| cavityTurbulent | 20×20 with wall functions | 10,000 | pisoFoam | RANS k-ε turbulence model |

---

## Case Setup

### Geometry and Boundary Conditions

Defined in `constant/polyMesh/blockMeshDict` and `0/U`, `0/p`.

| Boundary | Velocity | Pressure |
|---|---|---|
| movingWall (top) | fixedValue (1 0 0) m/s | zeroGradient |
| fixedWalls (sides + bottom) | noSlip (0 0 0) | zeroGradient |
| frontAndBack | empty (2D case) | empty |

### Fluid Properties

Defined in `constant/transportProperties`:

| Case | Kinematic Viscosity ν (m²/s) | Reynolds Number |
|---|---|---|
| cavity, cavityFine, cavityGrade | 0.01 | 10 |
| cavityHighRe | 0.001 | 100 |
| cavityTurbulent | 0.0001 | 10,000 |

### Solver Settings

**icoFoam** -> incompressible laminar solver using the PISO (Pressure Implicit with Splitting of Operators) algorithm. Solves momentum and pressure equations iteratively at each time step.

**pisoFoam** -> incompressible solver for laminar and turbulent flow. Solves the same PISO loop but additionally solves transport equations for k (turbulent kinetic energy) and ε (turbulent dissipation rate) at each time step.

---

## Mesh Design

### Uniform Mesh (cavity, cavityFine)

All cells identical in size. Simple to generate, easy to understand. Higher cell count required to achieve accuracy near walls.

```
blockMeshDict — cavity (20×20):
simpleGrading (1 1 1)   // uniform spacing

blockMeshDict — cavityFine (40×40):
simpleGrading (1 1 1)   // uniform spacing, double resolutionupdate
```

### Graded Mesh (cavityGrade)

Cells are smallest near walls where velocity gradients are steepest, and largest in the smooth interior. Same total cell count as cavityFine but better accuracy near walls.

```
blockMeshDict — cavityGrade (10×10 per block with grading):
simpleGrading (4 4 1)   // last cell 4x larger than first cell
```

**Smallest cell size calculation** using geometric progression formula:

Given: N = 10 cells, R = 4 (grading ratio), L = 0.05 m (block length)

```
r = R^(1/(N-1)) = 4^(1/9) ≈ 1.167       (ratio between consecutive cells)
δ = L × (r-1) / (r^N - 1) ≈ 3.45 × 10⁻³ m    (smallest cell size)
```

Maximum safe time step from Courant condition (Co < 1):

```
ΔT < δ / U_max = 0.00345 / 1 = 0.00345 s
→ deltaT set to 0.0025 s (safely below limit)
```

**Why mesh grading matters:** Numerical error is largest where the solution deviates most from the linear variation assumed by the finite-volume scheme -> i.e. where the second derivative is large. Near walls in the cavity, velocity changes sharply from the bulk flow to zero (no-slip). Grading concentrates resolution exactly where it's needed without increasing total cell count.

---

## Solution Workflow

### mapFields -> Solution Interpolation Between Meshes

Used to transfer converged results from a coarser mesh onto a finer mesh as initial conditions, avoiding cold-start computation.

```bash
# From inside target case directory
mapFields ../sourceCaseName -consistent
```

The `-consistent` flag indicates identical geometry and boundary condition types between source and target. The target `controlDict` `startTime` determines which time directory is read from the source.

**Sequence used:**
1. cavity (coarse) → converged at t=0.5s
2. mapFields cavity→cavityFine, run to t=0.7s
3. mapFields cavityFine→cavityGrade, run to t=0.8s

### Running in Background with Log File

```bash
icoFoam > log &      # run solver in background, redirect output to log file
tail -f log          # monitor log file in real time (Ctrl+C to stop watching)
```

### Post-Processing Field Data

```bash
postProcess -funcs '(components(U) mag(U))'
```

Writes scalar fields `Ux`, `Uy`, `Uz`, and `magU` to each time directory for easier visualisation and analysis in ParaView.

---

## Physics and Results

### Laminar Flow (Re = 10) -> cavity

The flow is dominated by viscosity. A single large recirculating vortex occupies the cavity. The vortex centre is slightly offset from the geometric centre due to inertial effects -> the lid drags fluid along and its momentum carries it further before turning, shifting the vortex upward.

**Key observations:**
- Single primary vortex, clean and symmetric
- Highest velocity near the moving lid
- Pressure builds up on the right wall where fast flow impinges
- No-slip condition forces velocity to zero at all walls

### Mesh Refinement Study (Re = 10) -> cavity vs cavityFine vs cavityGrade

Comparing velocity profiles along the vertical centreline across three meshes demonstrates mesh convergence -> the solution approaches a grid-independent result as resolution increases. The graded mesh achieves comparable accuracy to cavityFine at lower total cell count by concentrating resolution near walls.

### Reynolds Number Effects -> cavityHighRe (Re = 100)

Reducing ν by a factor of 10 increases Re tenfold. Inertia now plays a more significant role:

- **Primary vortex centre shifts upward and rightward** -> inertia carries the lid-driven flow further before it turns, breaking symmetry
- **Corner vortices appear** -> small secondary vortices in the bottom corners (Moffatt eddies) that viscosity suppressed at Re=10 now survive
- **Longer convergence time** -> reduced viscous damping means perturbations persist longer before reaching steady state

As Re increases further the corner vortices grow, more secondary structures appear, and the flow eventually transitions to turbulence where it becomes unsteady and chaotic.

### Turbulence Modelling (Re = 10,000) -> cavityTurbulent

At Re = 10,000 direct numerical simulation is infeasible -> the cell count would need to scale as Re^(9/4) to resolve all turbulent scales down to the Kolmogorov microscale.

**Reynolds-Averaged Simulation (RAS) approach:**
Split velocity into mean and fluctuating components: **U = Ū + u'**

Solve equations for the mean flow Ū only. The effect of turbulent fluctuations on the mean flow is modelled through the **turbulent viscosity** νt rather than resolved directly.

**Standard k-ε model solves two additional equations:**

| Variable | Physical meaning |
|---|---|
| k | Turbulent kinetic energy -> energy contained in fluctuations |
| ε | Turbulent dissipation rate -> rate at which k is converted to heat |

Turbulent viscosity: **νt = Cμ × k² / ε**

**Wall functions** bridge the near-wall region analytically using the log law, placing the first cell in the logarithmic layer (y+ 30-300) rather than resolving the viscous sublayer directly. This makes the turbulent simulation computationally feasible.

---

## How to Run

**Prerequisites:** OpenFOAM v2512 installed, sourced in terminal.

```bash
# Clone repository
git clone https://github.com/Syphonicc/CFD-Projects
cd CFD-Projects

# Run baseline cavity case
cd cavity
blockMesh
icoFoam > log &
tail -f log

# Visualise results
touch cavity.OpenFOAM
paraFoam
```

For cavityFine, cavityGrade, cavityHighRe, and cavityTurbulent -> follow the same pattern with appropriate mapFields steps as described in the workflow section above.

---

## Results

*ParaView screenshots to be added*

- [ ] Velocity magnitude -> cavity (Re=10, coarse uniform mesh)
- [ ] Velocity vectors -> cavity (showing primary vortex and centre offset)
- [ ] Mesh comparison -> cavity vs cavityFine vs cavityGrade
- [ ] Corner vortices -> cavityHighRe (Re=100)
- [ ] Turbulent k field -> cavityTurbulent (Re=10,000)

---

## Key Learnings

**Courant number** -> stability requires Co = U·ΔT/Δx < 1 everywhere. The most restrictive constraint is at the smallest cell with the highest velocity -> always at the wall in a graded mesh.

**Mesh design is a physics skill** -> you cannot grade a mesh intelligently without first understanding where gradients will be large. The mesh must follow the physics.

**mapFields enables incremental refinement** -> starting a fine mesh simulation from a converged coarse solution is always faster than starting from rest. Standard practice for mesh convergence studies.

**RANS is a compromise** -> turbulence models solve the closure problem empirically. They work well for the flows they were calibrated on and can fail badly outside those conditions. Understanding what a model assumes is as important as knowing how to run it.

**Reynolds number is a force ratio** -> Re = inertial forces / viscous forces. Low Re: viscosity damps everything, smooth organised flow. High Re: inertia amplifies disturbances, complex structures, eventually turbulence. Turbulence is what happens when inertia wins over viscosity completely.

---

## References

- Ghia, U., Ghia, K.N., Shin, C.T. (1982). High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method. *Journal of Computational Physics*, 48, 387-411.
- OpenFOAM v2512 Tutorial Guide -> Section 2.1: Lid-Driven Cavity Flow
- Anderson, J.D. -> *Computational Fluid Dynamics: The Basics with Applications*

---

## Tools Used

| Tool | Purpose |
|---|---|
| OpenFOAM v2512 | CFD solver framework |
| blockMesh | Mesh generation |
| mapFields | Solution interpolation between meshes |
| icoFoam | Laminar incompressible solver |
| pisoFoam | Turbulent incompressible solver |
| ParaView 5.12.1 | Post-processing and visualisation |
| Fedora Linux | Operating system |

---

*Part of ongoing CFD learning — github.com/Syphonicc/CFD-Projects*
*Next case: motorBike external aerodynamics using snappyHexMesh*
