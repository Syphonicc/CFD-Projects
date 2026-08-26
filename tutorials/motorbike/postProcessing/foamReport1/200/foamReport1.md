---
marp: true
paginate: true
---

<style>
:root {
    font-size: 20px;
}
td {
    width: 1000px;
}
table {
    width: 100%;
}
img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    width: 60%;
}
</style>

# simpleFoam : motorBike tutorial

- Case: /home/syphonic/OpenFOAM/run/motorBike
- Submission: 23:17:35 on Mar 20 2026
- Report time: 23:21:50 on Mar 20 2026

---

## Run information

| Property       | Value              |
|----------------|--------------------|
| Host           | fedora        |
| Processors     | 1      |
| Time steps     | 200  |
| Initial deltaT | 1 |
| Current deltaT | 1 |
| Execution time | {{EXECUTIONTIME}}  |

---

## OpenFOAM information

| Property       | Value              |
|----------------|--------------------|
| Version        | 2512     |
| API            | 2512         |
| Patch          | 0       |
| Build          | _87ed40d2-20251219       |
| Architecture   | LSB;label=32;scalar=64  |

---

## Mesh statistics

| Property          | Value                |
|-------------------|----------------------|
| Bounds            | (-5 -4 0)(15 4 8) |
| Number of cells   | 353578   |
| Number of faces   | 1107965   |
| Number of points  | 406167  |
| Number of patches | 72 |

---

## Linear solvers

| Property | Value          | tolerance(rel)   | Tolerance(abs)      |
|----------|----------------|------------------|---------------------|
| p        | `GAMG` | 1e-07 | 0.01 |
| U        | `smoothSolver` | 1e-08 | 0.1 |

---

## Numerical scehemes

The chosen divergence schemes comprised:

~~~
divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwindV grad(U);
    turbulence      bounded Gauss upwind;
    div(phi,k)      bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

~~~

---

## Graphs

Residuals

![](/home/syphonic/OpenFOAM/run/motorBike/postProcessing/residualGraph1/200/residualGraph1.svg)

---

## Results

Forces

![](/home/syphonic/OpenFOAM/run/motorBike/postProcessing/forceCoeffsGraph1/200/forceCoeffsGraph1.svg)

---

Made using Open&nabla;FOAM v2412 from https://openfoam.com

