#!/usr/bin/env python3
"""
Step 3: build the CFD domain.

  1. import STEP, scale to the 5.8% wind tunnel model
  2. sew the four patches into a solid
  3. build the farfield box (50 body lengths), half-model, y >= 0
  4. subtract the aircraft from the box
  5. identify and tag the boundary surfaces
  6. write the geometry (no mesh yet)

The negative volume reported by getMass indicates inward-facing normals.
OCC's boolean cut handles orientation internally, so it is reported but not
corrected manually - the check is that the resulting fluid volume comes out
positive and roughly equal to (box volume - aircraft volume).

Usage:
    python3 build_domain.py
    python3 build_domain.py --gui
    python3 build_domain.py --write     # write n2a_domain.brep
"""

import gmsh
import sys

STEP  = "../geometry/n2a.stp"
SCALE = 1.76784e-5

GUI   = "--gui" in sys.argv
WRITE = "--write" in sys.argv

# Wind tunnel model dimensions after scaling
BODY_LEN = 2.62348
SPAN     = 3.76552

FAR = 50 * BODY_LEN          # 131.17 m

X_MIN, X_MAX = -FAR, FAR + BODY_LEN
Y_MIN, Y_MAX = 0.0,  FAR
Z_MIN, Z_MAX = -FAR, FAR

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
gmsh.option.setNumber("Geometry.Tolerance", 1e-6)
gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-6)
gmsh.model.add("n2a")

# ---------------------------------------------------------------------------
print("=" * 64)
print("1. Import and scale")
print("=" * 64)
gmsh.model.occ.importShapes(STEP)
gmsh.model.occ.synchronize()
gmsh.model.occ.dilate(gmsh.model.getEntities(), 0, 0, 0, SCALE, SCALE, SCALE)
gmsh.model.occ.synchronize()

bb = gmsh.model.getBoundingBox(-1, -1)
print(f"  span {bb[4]-bb[1]:.5f}   body {bb[3]-bb[0]:.5f}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 64)
print("2. Sew into a solid")
print("=" * 64)
surf_tags = [t for (d, t) in gmsh.model.getEntities(2)]
sl = gmsh.model.occ.addSurfaceLoop(surf_tags, sewing=True)
air = gmsh.model.occ.addVolume([sl])
gmsh.model.occ.synchronize()
v_air = gmsh.model.occ.getMass(3, air)
print(f"  aircraft volume tag {air}, mass {v_air:.6f} m3"
      f"  ({'inward normals' if v_air < 0 else 'outward normals'})")

# ---------------------------------------------------------------------------
print("\n" + "=" * 64)
print("3. Farfield box (half model)")
print("=" * 64)
box = gmsh.model.occ.addBox(
    X_MIN, Y_MIN, Z_MIN,
    X_MAX - X_MIN, Y_MAX - Y_MIN, Z_MAX - Z_MIN
)
gmsh.model.occ.synchronize()
v_box = gmsh.model.occ.getMass(3, box)
print(f"  box tag {box}, volume {v_box:.3e} m3")
print(f"  x {X_MIN:.2f} .. {X_MAX:.2f}")
print(f"  y {Y_MIN:.2f} .. {Y_MAX:.2f}   (symmetry plane at y = 0)")
print(f"  z {Z_MIN:.2f} .. {Z_MAX:.2f}")

# ---------------------------------------------------------------------------
print("\n" + "=" * 64)
print("4. Boolean cut: box minus aircraft")
print("=" * 64)
out, _ = gmsh.model.occ.fragment([(3, box)], [(3, air)])
gmsh.model.occ.synchronize()

vols_after = [t for (d, t) in gmsh.model.getEntities(3)]
masses = {t: abs(gmsh.model.occ.getMass(3, t)) for t in vols_after}
print(f"  volumes after fragment: {masses}")

keep = max(masses, key=masses.get)
drop = [t for t in vols_after if t != keep]
print(f"  keeping {keep} (largest), removing {drop}")
if drop:
    gmsh.model.occ.remove([(3, t) for t in drop], recursive=False)
    gmsh.model.occ.synchronize()

fluid = [keep]
print(f"  resulting volume(s): {fluid}")
v_fluid = sum(gmsh.model.occ.getMass(3, t) for t in fluid)
print(f"  fluid volume {v_fluid:.6e} m3")
print(f"  box volume   {v_box:.6e} m3")
print(f"  difference   {v_box - v_fluid:.6f} m3")
print(f"  aircraft half-volume expected ~ {abs(v_air)/2:.6f} m3")

# ---------------------------------------------------------------------------
print("\n" + "=" * 64)
print("5. Identify boundary surfaces")
print("=" * 64)

tol = 1e-3
inlet, outlet, symmetry, farfield, aircraft = [], [], [], [], []

for d, t in gmsh.model.getEntities(2):
    b = gmsh.model.getBoundingBox(d, t)
    xlo, ylo, zlo, xhi, yhi, zhi = b

    if abs(xlo - X_MIN) < tol and abs(xhi - X_MIN) < tol:
        inlet.append(t)
    elif abs(xlo - X_MAX) < tol and abs(xhi - X_MAX) < tol:
        outlet.append(t)
    elif abs(ylo - Y_MIN) < tol and abs(yhi - Y_MIN) < tol:
        symmetry.append(t)
    elif (abs(ylo - Y_MAX) < tol and abs(yhi - Y_MAX) < tol) or \
         (abs(zlo - Z_MIN) < tol and abs(zhi - Z_MIN) < tol) or \
         (abs(zlo - Z_MAX) < tol and abs(zhi - Z_MAX) < tol):
        farfield.append(t)
    else:
        aircraft.append(t)

print(f"  inlet     {len(inlet):4d}  {inlet}")
print(f"  outlet    {len(outlet):4d}  {outlet}")
print(f"  symmetry  {len(symmetry):4d}  {symmetry}")
print(f"  farfield  {len(farfield):4d}  {farfield}")
print(f"  aircraft  {len(aircraft):4d}  {aircraft}")

area_air = sum(gmsh.model.occ.getMass(2, t) for t in aircraft)
print(f"\n  aircraft wetted area (half model) {area_air:.4f} m2")

if not aircraft:
    print("\n  WARNING: no aircraft surfaces identified")
if len(symmetry) == 0:
    print("\n  WARNING: no symmetry plane identified")

# ---------------------------------------------------------------------------
print("\n" + "=" * 64)
print("6. Physical groups")
print("=" * 64)
if aircraft: gmsh.model.addPhysicalGroup(2, aircraft, name="aircraft")
if inlet:    gmsh.model.addPhysicalGroup(2, inlet,    name="inlet")
if outlet:   gmsh.model.addPhysicalGroup(2, outlet,   name="outlet")
if symmetry: gmsh.model.addPhysicalGroup(2, symmetry, name="symmetry")
if farfield: gmsh.model.addPhysicalGroup(2, farfield, name="farfield")
gmsh.model.addPhysicalGroup(3, fluid, name="internal")
gmsh.model.occ.synchronize()
print("  assigned")

if WRITE:
    gmsh.write("n2a_domain.brep")
    print("\n  wrote n2a_domain.brep")

print("\nDomain built. Next: size fields, boundary layer, mesh generation.")

if GUI:
    gmsh.fltk.run()

gmsh.finalize()
