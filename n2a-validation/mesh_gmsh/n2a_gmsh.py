#!/usr/bin/env python3
"""
N2A Hybrid Wing-Body - gmsh mesh with boundary layers
=====================================================

Half-model, symmetry plane at y = 0, farfield at 50 body lengths.

Approach differs from snappyHexMesh: gmsh builds a tetrahedral volume mesh
from the surface outward, with the BoundaryLayer field extruding prisms from
the wall. Layers are created as part of meshing rather than inserted into an
existing mesh by shrinking it, which is the failure mode snappy hit.

Targets:
    first layer   1.25e-5 m   (y+ ~ 1 at Re = 6.6e6)
    ratio         1.25
    20 layers  -> 4.3 mm stack

Usage:
    python3 n2a_gmsh.py            # generate, write n2a.msh
    python3 n2a_gmsh.py --gui      # generate and open the GUI
    python3 n2a_gmsh.py --surface  # surface mesh only, fast sanity check

Then:
    gmshToFoam n2a.msh
"""

import gmsh
import sys
import math

GUI       = "--gui" in sys.argv
SURF_ONLY = "--surface" in sys.argv

STL = "n2a_wt.stl"

# ---------------------------------------------------------------------------
# Geometry extents (metres, 5.8% wind tunnel model)
# ---------------------------------------------------------------------------
BODY_LEN = 2.6235
SPAN     = 3.7655
HALF_SPAN = SPAN / 2

FAR = 50 * BODY_LEN          # 131.2 m

X_MIN, X_MAX = -FAR,  FAR + BODY_LEN
Y_MIN, Y_MAX =  0.0,  FAR
Z_MIN, Z_MAX = -FAR,  FAR

# ---------------------------------------------------------------------------
# Mesh sizing
# ---------------------------------------------------------------------------
LC_SURF   = 0.0078      # 7.8 mm on the aircraft, matching the snappy level-9 target
LC_TAIL   = 0.0039      # finer on the tails
LC_NEAR   = 0.08        # near-field volume
LC_WAKE   = 0.25
LC_FAR    = 15.0        # farfield

# Boundary layer
BL_FIRST  = 1.25e-5
BL_RATIO  = 1.25
BL_NLAYER = 20
BL_THICK  = BL_FIRST * (BL_RATIO**BL_NLAYER - 1) / (BL_RATIO - 1)

print(f"Boundary layer: {BL_NLAYER} layers, first {BL_FIRST*1e6:.1f} um, "
      f"ratio {BL_RATIO}, total {BL_THICK*1000:.2f} mm")

# ---------------------------------------------------------------------------
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("General.Verbosity", 5)
gmsh.model.add("n2a")

# ---------------------------------------------------------------------------
# Import the STL as a discrete surface
# ---------------------------------------------------------------------------
print(f"Merging {STL} ...")
gmsh.merge(STL)

surfs = gmsh.model.getEntities(2)
print(f"  imported {len(surfs)} discrete surfaces")
for d, t in surfs:
    n = gmsh.model.mesh.getElements(d, t)[1]
    ntri = len(n[0]) if n else 0
    print(f"    surface {t}: {ntri} triangles")

# Classify the discrete surface so gmsh can treat it as geometry.
# angle: feature angle for splitting into separate surfaces
# forceParametrizablePatches: allow reparametrisation of awkward patches
print("Classifying surface ...")
gmsh.model.mesh.classifySurfaces(
    angle=40 * math.pi / 180,
    boundary=True,
    forReparametrization=False,
    curveAngle=180 * math.pi / 180,
)

aircraft_surfs = [t for (d, t) in gmsh.model.getEntities(2)]
print(f"  {len(aircraft_surfs)} surfaces after classification")

if SURF_ONLY:
    gmsh.model.mesh.field.add("Constant", 1)
    gmsh.model.mesh.field.setNumbers(1, "SurfacesList", aircraft_surfs)
    gmsh.model.mesh.field.setNumber(1, "VIn", LC_SURF)
    gmsh.model.mesh.field.setNumber(1, "VOut", LC_SURF)
    gmsh.model.mesh.field.setAsBackgroundMesh(1)
    gmsh.model.mesh.generate(2)
    gmsh.write("n2a_surface.msh")
    print("Wrote n2a_surface.msh")
    if GUI:
        gmsh.fltk.run()
    gmsh.finalize()
    sys.exit(0)

# ---------------------------------------------------------------------------
# Build the farfield box and subtract the aircraft
# ---------------------------------------------------------------------------
print("Building farfield box ...")
gmsh.model.occ.synchronize()

box = gmsh.model.occ.addBox(
    X_MIN, Y_MIN, Z_MIN,
    X_MAX - X_MIN, Y_MAX - Y_MIN, Z_MAX - Z_MIN
)
gmsh.model.occ.synchronize()

# Surface loop from the classified aircraft surfaces
sl_air = gmsh.model.geo.addSurfaceLoop(aircraft_surfs)
gmsh.model.geo.synchronize()

print("Note: OCC box and discrete aircraft surface must be combined manually.")
print("      Using the geo kernel volume with both surface loops.")

box_surfs = [t for (d, t) in gmsh.model.getEntities(2) if t not in aircraft_surfs]
sl_box = gmsh.model.geo.addSurfaceLoop(box_surfs)
vol = gmsh.model.geo.addVolume([sl_box, sl_air])
gmsh.model.geo.synchronize()

# ---------------------------------------------------------------------------
# Size fields
# ---------------------------------------------------------------------------
print("Setting size fields ...")

gmsh.model.mesh.field.add("Distance", 1)
gmsh.model.mesh.field.setNumbers(1, "SurfacesList", aircraft_surfs)
gmsh.model.mesh.field.setNumber(1, "Sampling", 200)

gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "InField", 1)
gmsh.model.mesh.field.setNumber(2, "SizeMin", LC_SURF)
gmsh.model.mesh.field.setNumber(2, "SizeMax", LC_FAR)
gmsh.model.mesh.field.setNumber(2, "DistMin", 0.1)
gmsh.model.mesh.field.setNumber(2, "DistMax", 20.0)

gmsh.model.mesh.field.add("Box", 3)
gmsh.model.mesh.field.setNumber(3, "VIn", LC_NEAR)
gmsh.model.mesh.field.setNumber(3, "VOut", LC_FAR)
gmsh.model.mesh.field.setNumber(3, "XMin", -1.0)
gmsh.model.mesh.field.setNumber(3, "XMax",  4.5)
gmsh.model.mesh.field.setNumber(3, "YMin",  0.0)
gmsh.model.mesh.field.setNumber(3, "YMax",  2.6)
gmsh.model.mesh.field.setNumber(3, "ZMin", -1.0)
gmsh.model.mesh.field.setNumber(3, "ZMax",  1.2)

gmsh.model.mesh.field.add("Box", 4)
gmsh.model.mesh.field.setNumber(4, "VIn", LC_WAKE)
gmsh.model.mesh.field.setNumber(4, "VOut", LC_FAR)
gmsh.model.mesh.field.setNumber(4, "XMin",  2.0)
gmsh.model.mesh.field.setNumber(4, "XMax", 15.0)
gmsh.model.mesh.field.setNumber(4, "YMin",  0.0)
gmsh.model.mesh.field.setNumber(4, "YMax",  2.6)
gmsh.model.mesh.field.setNumber(4, "ZMin", -1.0)
gmsh.model.mesh.field.setNumber(4, "ZMax",  1.0)

gmsh.model.mesh.field.add("Min", 5)
gmsh.model.mesh.field.setNumbers(5, "FieldsList", [2, 3, 4])
gmsh.model.mesh.field.setAsBackgroundMesh(5)

gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

# ---------------------------------------------------------------------------
# Boundary layer
# ---------------------------------------------------------------------------
print("Setting boundary layer field ...")
bl = gmsh.model.mesh.field.add("BoundaryLayer")
gmsh.model.mesh.field.setNumbers(bl, "SurfacesList", aircraft_surfs)
gmsh.model.mesh.field.setNumber(bl, "Size", BL_FIRST)
gmsh.model.mesh.field.setNumber(bl, "Ratio", BL_RATIO)
gmsh.model.mesh.field.setNumber(bl, "Thickness", BL_THICK)
gmsh.model.mesh.field.setNumber(bl, "Quads", 0)
gmsh.model.mesh.field.setAsBoundaryLayer(bl)

# ---------------------------------------------------------------------------
# Physical groups -> OpenFOAM patches
# ---------------------------------------------------------------------------
print("Assigning physical groups ...")

tol = 1e-3
def surfs_at(axis, value):
    out = []
    for (d, t) in gmsh.model.getEntities(2):
        if t in aircraft_surfs:
            continue
        bb = gmsh.model.getBoundingBox(d, t)   # xmin ymin zmin xmax ymax zmax
        lo, hi = bb[axis], bb[axis + 3]
        if abs(lo - value) < tol and abs(hi - value) < tol:
            out.append(t)
    return out

inlet    = surfs_at(0, X_MIN)
outlet   = surfs_at(0, X_MAX)
symmetry = surfs_at(1, Y_MIN)
farfield = [t for t in box_surfs
            if t not in inlet + outlet + symmetry]

gmsh.model.addPhysicalGroup(2, aircraft_surfs, name="aircraft")
gmsh.model.addPhysicalGroup(2, inlet,    name="inlet")
gmsh.model.addPhysicalGroup(2, outlet,   name="outlet")
gmsh.model.addPhysicalGroup(2, symmetry, name="symmetry")
gmsh.model.addPhysicalGroup(2, farfield, name="farfield")
gmsh.model.addPhysicalGroup(3, [vol],    name="internal")

print(f"  aircraft {len(aircraft_surfs)}, inlet {len(inlet)}, "
      f"outlet {len(outlet)}, symmetry {len(symmetry)}, farfield {len(farfield)}")

# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
gmsh.option.setNumber("Mesh.Algorithm", 6)      # 2D: frontal-delaunay
gmsh.option.setNumber("Mesh.Algorithm3D", 10)   # 3D: HXT, fast and parallel
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)

print("Generating 2D ...")
gmsh.model.mesh.generate(2)
print("Generating 3D ...")
gmsh.model.mesh.generate(3)

nodes = gmsh.model.mesh.getNodes()[0]
_, elems = gmsh.model.mesh.getElementsByType(4)[0:2] if True else (None, None)
print(f"\nNodes: {len(nodes)}")

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.option.setNumber("Mesh.Binary", 0)
gmsh.write("n2a.msh")
print("Wrote n2a.msh")
print("\nNext: gmshToFoam n2a.msh")

if GUI:
    gmsh.fltk.run()

gmsh.finalize()
