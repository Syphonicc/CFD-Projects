#!/usr/bin/env python3
"""
Generate the four N2A compressible RANS cases.

  case_alpha6_SA     case_alpha6_SST
  case_alpha10_SA    case_alpha10_SST

All four share the mesh in mesh/constant/polyMesh, symlinked rather than
copied. Only the freestream vector, lift/drag directions and turbulence model
differ between them.

Conditions (5.8% wind tunnel scale, matching Aprovitola et al. 2022):
    M     0.2000        a     340.263 m/s
    Re    6.599e6       L_ref 1.53816 m
    T     288.15 K      p     93290 Pa
    U     68.05 m/s     rho   1.1281 kg/m3
    mu    1.7893e-5     nu    1.5861e-5 m2/s
    Pr    0.7438        cp    1006 J/kgK

Reference values for force coefficients:
    Aref  1.55619 m2   <- HALF of S_ref (3.11237), because this is a half
                          model. Using half the area with half the force
                          gives full-model coefficients directly, with no
                          post-hoc doubling.
    lRef  1.53816 m
    CofR  (1.41510 0 0)  = 53.94% of body length aft of nose

Usage:
    python3 make_cases.py
    python3 make_cases.py --mesh /path/to/mesh
"""

import os
import math
import sys
import shutil

MESH = "mesh"
for i, a in enumerate(sys.argv):
    if a == "--mesh":
        MESH = sys.argv[i + 1]

# ---------------------------------------------------------------------------
T_INF   = 288.15
P_INF   = 93290.0
RHO_INF = 1.1281
MU_INF  = 1.7893e-5
U_INF   = 68.05
NU_INF  = MU_INF / RHO_INF
A_INF   = 340.263

AREF = 1.55619        # half of S_ref
LREF = 1.53816
COFR = "(1.41510 0 0)"

# SA freestream: nuTilda = 3*nu, nut = nuTilda*fv1 with chi = 3
NUTILDA_INF = 3 * NU_INF
FV1         = 27.0 / (27.0 + 7.1**3)
NUT_SA      = NUTILDA_INF * FV1

# k-omega SST freestream, TMR convention
K_INF   = 9e-9 * A_INF**2
OMG_INF = 1e-6 * RHO_INF * A_INF**2 / MU_INF
NUT_SST = K_INF / OMG_INF

HDR = """/*--------------------------------*- C++ -*----------------------------------*\\
| N2A Hybrid Wing-Body - compressible RANS, rhoSimpleFoam                      |
| M = 0.2, Re = 6.60e6, L_ref = 1.53816 m, 5.8% wind tunnel scale              |
\\*---------------------------------------------------------------------------*/
"""

def foamfile(cls, obj, loc=None):
    s = HDR + "\nFoamFile\n{\n    version     2.0;\n    format      ascii;\n"
    s += f"    class       {cls};\n"
    if loc:
        s += f'    location    "{loc}";\n'
    s += f"    object      {obj};\n}}\n"
    s += "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n\n"
    return s

END = "\n// ************************************************************************* //\n"


# ---------------------------------------------------------------------------
# constant/
# ---------------------------------------------------------------------------
THERMO = foamfile("dictionary", "thermophysicalProperties") + """thermoType
{
    type            hePsiThermo;
    mixture         pureMixture;
    transport       sutherland;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie
    {
        molWeight   28.96;          // R = 287.1 J/kgK
    }
    thermodynamics
    {
        Cp          1006;           // paper value
        Hf          0;
    }
    transport
    {
        // Sutherland  mu = As*T^1.5/(T + Ts)
        // at T = 288.15 K gives mu = 1.78938e-5 Pa.s
        As          1.458e-06;
        Ts          110.4;
    }
}
""" + END

TURB = {
    "SA":  foamfile("dictionary", "turbulenceProperties") +
           "simulationType  RAS;\n\nRAS\n{\n    RASModel        SpalartAllmaras;\n"
           "    turbulence      on;\n    printCoeffs     on;\n}\n" + END,
    "SST": foamfile("dictionary", "turbulenceProperties") +
           "simulationType  RAS;\n\nRAS\n{\n    RASModel        kOmegaSST;\n"
           "    turbulence      on;\n    printCoeffs     on;\n}\n" + END,
}


# ---------------------------------------------------------------------------
# 0/  field templates
# ---------------------------------------------------------------------------
def field_U(ux, uy):
    return foamfile("volVectorField", "U", "0") + f"""dimensions      [0 1 -1 0 0 0 0];

internalField   uniform ({ux:.5f} 0 {uy:.5f});

boundaryField
{{
    inlet
    {{
        type            freestreamVelocity;
        freestreamValue uniform ({ux:.5f} 0 {uy:.5f});
    }}
    outlet
    {{
        type            freestreamVelocity;
        freestreamValue uniform ({ux:.5f} 0 {uy:.5f});
    }}
    farfield
    {{
        type            freestreamVelocity;
        freestreamValue uniform ({ux:.5f} 0 {uy:.5f});
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            noSlip;
    }}
}}
""" + END


FIELD_P = foamfile("volScalarField", "p", "0") + f"""dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform {P_INF:.1f};

boundaryField
{{
    inlet
    {{
        type            freestreamPressure;
        freestreamValue uniform {P_INF:.1f};
    }}
    outlet
    {{
        type            freestreamPressure;
        freestreamValue uniform {P_INF:.1f};
    }}
    farfield
    {{
        type            freestreamPressure;
        freestreamValue uniform {P_INF:.1f};
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            zeroGradient;
    }}
}}
""" + END


FIELD_T = foamfile("volScalarField", "T", "0") + f"""dimensions      [0 0 0 1 0 0 0];

internalField   uniform {T_INF};

boundaryField
{{
    inlet
    {{
        type            inletOutlet;
        inletValue      uniform {T_INF};
        value           uniform {T_INF};
    }}
    outlet
    {{
        type            inletOutlet;
        inletValue      uniform {T_INF};
        value           uniform {T_INF};
    }}
    farfield
    {{
        type            inletOutlet;
        inletValue      uniform {T_INF};
        value           uniform {T_INF};
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            zeroGradient;      // adiabatic wall
    }}
}}
""" + END


FIELD_ALPHAT = foamfile("volScalarField", "alphat", "0") + """dimensions      [1 -1 -1 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet       { type calculated; value uniform 0; }
    outlet      { type calculated; value uniform 0; }
    farfield    { type calculated; value uniform 0; }
    symmetry    { type symmetry; }
    n2a
    {
        type            compressible::alphatWallFunction;
        Prt             0.85;
        value           uniform 0;
    }
}
""" + END


def field_nut(model):
    val = NUT_SA if model == "SA" else NUT_SST
    return foamfile("volScalarField", "nut", "0") + f"""dimensions      [0 2 -1 0 0 0 0];

internalField   uniform {val:.6e};

boundaryField
{{
    inlet       {{ type calculated; value uniform {val:.6e}; }}
    outlet      {{ type calculated; value uniform {val:.6e}; }}
    farfield    {{ type calculated; value uniform {val:.6e}; }}
    symmetry    {{ type symmetry; }}
    n2a
    {{
        // y+ < 1 on this mesh. Spalding is valid across all y+ so it
        // degrades gracefully on the 1.55% of faces without prism layers.
        type            nutUSpaldingWallFunction;
        value           uniform 0;
    }}
}}
""" + END


FIELD_NUTILDA = foamfile("volScalarField", "nuTilda", "0") + f"""dimensions      [0 2 -1 0 0 0 0];

// freestream nuTilda = 3 nu   (TMR convention)
internalField   uniform {NUTILDA_INF:.6e};

boundaryField
{{
    inlet
    {{
        type            freestream;
        freestreamValue uniform {NUTILDA_INF:.6e};
    }}
    outlet
    {{
        type            freestream;
        freestreamValue uniform {NUTILDA_INF:.6e};
    }}
    farfield
    {{
        type            freestream;
        freestreamValue uniform {NUTILDA_INF:.6e};
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            fixedValue;
        value           uniform 0;
    }}
}}
""" + END


FIELD_K = foamfile("volScalarField", "k", "0") + f"""dimensions      [0 2 -2 0 0 0 0];

// TMR convention: k_inf = 9e-9 * a_inf^2
internalField   uniform {K_INF:.6e};

boundaryField
{{
    inlet
    {{
        type            freestream;
        freestreamValue uniform {K_INF:.6e};
    }}
    outlet
    {{
        type            freestream;
        freestreamValue uniform {K_INF:.6e};
    }}
    farfield
    {{
        type            freestream;
        freestreamValue uniform {K_INF:.6e};
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            kLowReWallFunction;
        value           uniform 1e-12;
    }}
}}
""" + END


FIELD_OMEGA = foamfile("volScalarField", "omega", "0") + f"""dimensions      [0 0 -1 0 0 0 0];

// TMR convention: omega_inf = 1e-6 * rho_inf * a_inf^2 / mu_inf
internalField   uniform {OMG_INF:.6e};

boundaryField
{{
    inlet
    {{
        type            freestream;
        freestreamValue uniform {OMG_INF:.6e};
    }}
    outlet
    {{
        type            freestream;
        freestreamValue uniform {OMG_INF:.6e};
    }}
    farfield
    {{
        type            freestream;
        freestreamValue uniform {OMG_INF:.6e};
    }}
    symmetry
    {{
        type            symmetry;
    }}
    n2a
    {{
        type            omegaWallFunction;
        value           uniform {OMG_INF:.6e};
    }}
}}
""" + END


# ---------------------------------------------------------------------------
# system/
# ---------------------------------------------------------------------------
def controldict(alpha, ux, uy):
    r  = math.radians(alpha)
    lx, ly = -math.sin(r), math.cos(r)
    dx, dy =  math.cos(r), math.sin(r)
    return foamfile("dictionary", "controlDict", "system") + f"""application     rhoSimpleFoam;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         20000;
deltaT          1;

writeControl    timeStep;
writeInterval   2000;
purgeWrite      2;
writeFormat     binary;
writePrecision  8;
writeCompression on;
timeFormat      general;
timePrecision   6;
runTimeModifiable yes;

functions
{{
    forceCoeffs1
    {{
        type            forceCoeffs;
        libs            (forces);
        writeControl    timeStep;
        writeInterval   1;
        patches         (n2a);

        // Compressible: rho is read from the solved field, not supplied
        rho             rho;
        rhoInf          {RHO_INF};
        pRef            {P_INF};

        // Wind frame at alpha = {alpha} deg
        liftDir         ({lx:.6f} 0 {ly:.6f});
        dragDir         ({dx:.6f} 0 {dy:.6f});
        pitchAxis       (0 1 0);
        CofR            {COFR};

        magUInf         {U_INF};
        lRef            {LREF};

        // HALF of full S_ref (3.11237). Half model gives half the force, so
        // half the area returns full-model coefficients directly.
        Aref            {AREF};
    }}

    yPlus1
    {{
        type            yPlus;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        patches         (n2a);
    }}

    MachNo1
    {{
        type            MachNo;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
    }}

    wallShearStress1
    {{
        type            wallShearStress;
        libs            (fieldFunctionObjects);
        writeControl    writeTime;
        patches         (n2a);
    }}

    residuals1
    {{
        type            solverInfo;
        libs            (utilityFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        fields          (".*");
    }}
}}
""" + END


def fvschemes(model):
    turb = ("div(phi,nuTilda) bounded Gauss upwind;"
            if model == "SA" else
            "div(phi,k)      bounded Gauss upwind;\n"
            "    div(phi,omega)  bounded Gauss upwind;")
    return foamfile("dictionary", "fvSchemes", "system") + f"""ddtSchemes
{{
    default         steadyState;
}}

gradSchemes
{{
    default         cellLimited Gauss linear 1;
    grad(U)         cellLimited Gauss linear 1;
}}

divSchemes
{{
    default         none;

    div(phi,U)      bounded Gauss linearUpwindV grad(U);
    div(phi,h)      bounded Gauss upwind;
    div(phi,K)      bounded Gauss linearUpwind grad(U);
    div(phid,p)     Gauss linearUpwind grad(p);
    div(phi,Ekp)    bounded Gauss linearUpwind grad(Ekp);
    {turb}

    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}}

laplacianSchemes
{{
    default         Gauss linear corrected;
}}

interpolationSchemes
{{
    default         linear;
}}

snGradSchemes
{{
    default         corrected;
}}

wallDist
{{
    method          meshWave;
}}
""" + END


def fvsolution(model):
    turbfields = "nuTilda" if model == "SA" else "k|omega"
    return foamfile("dictionary", "fvSolution", "system") + f"""solvers
{{
    Phi
    {{
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
    }}

    p
    {{
        solver          GAMG;
        tolerance       1e-8;
        relTol          0.05;
        smoother        GaussSeidel;
    }}

    "(U|h|{turbfields})"
    {{
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-9;
        relTol          0.1;
    }}
}}

SIMPLE
{{
    nNonOrthogonalCorrectors 1;

    pRefCell        0;
    pRefValue       93290.0;
    pMinFactor      0.1;
    pMaxFactor      4.0;

    residualControl
    {{
        p               1e-5;
        U               1e-5;
        h               1e-5;
        "({turbfields})" 1e-5;
    }}
}}

relaxationFactors
{{
    fields
    {{
        p               0.2;
        rho             0.1;
    }}
    equations
    {{
        U               0.3;
        h               0.2;
        p               0.4;
        "({turbfields})" 0.5;
    }}
}}
""" + END


DECOMPOSE = foamfile("dictionary", "decomposeParDict", "system") + """numberOfSubdomains 32;

method          scotch;
""" + END


# ---------------------------------------------------------------------------
CASES = [
    (6.0,  "SA"),
    (6.0,  "SST"),
    (10.0, "SA"),
    (10.0, "SST"),
]

print("=" * 66)
print("Generating N2A compressible RANS cases")
print("=" * 66)
print(f"  U_inf   {U_INF} m/s      p_inf {P_INF} Pa    T_inf {T_INF} K")
print(f"  rho_inf {RHO_INF}        mu    {MU_INF:.4e}   nu {NU_INF:.4e}")
print(f"  Aref    {AREF} m2 (half of {2*AREF:.5f})")
print(f"  lRef    {LREF} m         CofR {COFR}")
print(f"  SA      nuTilda {NUTILDA_INF:.4e}   nut {NUT_SA:.4e}")
print(f"  SST     k {K_INF:.4e}   omega {OMG_INF:.4e}   nut {NUT_SST:.4e}")
print()

for alpha, model in CASES:
    tag  = f"{alpha:g}".replace(".", "p")
    name = f"case_alpha{tag}_{model}"
    r    = math.radians(alpha)
    ux, uy = U_INF * math.cos(r), U_INF * math.sin(r)

    if os.path.exists(name):
        shutil.rmtree(name)
    os.makedirs(f"{name}/0")
    os.makedirs(f"{name}/constant")
    os.makedirs(f"{name}/system")

    open(f"{name}/0/U", "w").write(field_U(ux, uy))
    open(f"{name}/0/p", "w").write(FIELD_P)
    open(f"{name}/0/T", "w").write(FIELD_T)
    open(f"{name}/0/alphat", "w").write(FIELD_ALPHAT)
    open(f"{name}/0/nut", "w").write(field_nut(model))
    if model == "SA":
        open(f"{name}/0/nuTilda", "w").write(FIELD_NUTILDA)
    else:
        open(f"{name}/0/k", "w").write(FIELD_K)
        open(f"{name}/0/omega", "w").write(FIELD_OMEGA)

    open(f"{name}/constant/thermophysicalProperties", "w").write(THERMO)
    open(f"{name}/constant/turbulenceProperties", "w").write(TURB[model])

    open(f"{name}/system/controlDict", "w").write(controldict(alpha, ux, uy))
    open(f"{name}/system/fvSchemes", "w").write(fvschemes(model))
    open(f"{name}/system/fvSolution", "w").write(fvsolution(model))
    open(f"{name}/system/decomposeParDict", "w").write(DECOMPOSE)

    # symlink the mesh rather than copying it four times
    src = os.path.abspath(f"{MESH}/constant/polyMesh")
    dst = f"{name}/constant/polyMesh"
    if os.path.isdir(src):
        os.symlink(src, dst)
        note = "mesh linked"
    else:
        note = f"MESH NOT FOUND at {src}"

    print(f"  {name:24s}  U ({ux:8.4f} {uy:7.4f} 0)   {note}")

print()
print("Run one with:")
print("    cd case_alpha6_SA")
print("    source /usr/lib/openfoam/openfoam2512/etc/bashrc")
print("    decomposePar && mpirun -np 8 rhoSimpleFoam -parallel > log.run 2>&1")
