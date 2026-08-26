#!/usr/bin/env python3
"""
Step 2: scale the STEP geometry and try to sew it into a closed solid.

The STEP import gives 4 unconnected surface patches (Wing_Body port/starboard,
two vertical tails) and 0 volumes. gmsh needs a closed volume to mesh, so the
patches must be sewn.

Units: OpenVSP wrote milli-feet. Scale factor to the 5.8% wind tunnel model:
    1 mft -> m          0.0003048
    full scale -> 5.8%  0.058
    combined            1.76784e-5

Verification target after scaling:
    span (y extent)  3.7655 m
    body (x extent)  2.6235 m

Usage:
    python3 sew_step.py                 # report only
    python3 sew_step.py --gui           # report and open GUI
    python3 sew_step.py --write         # write n2a_solid.brep if sewing works
"""

import gmsh
import sys

STEP  = "../geometry/n2a_split.stp"
SCALE = 1.76784e-5

GUI   = "--gui" in sys.argv
WRITE = "--write" in sys.argv

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Geometry.OCCSewFaces", 1)      # sew on import
gmsh.option.setNumber("Geometry.OCCMakeSolids", 1)    # try to build solids
gmsh.option.setNumber("Geometry.Tolerance", 1e-6)
gmsh.option.setNumber("Geometry.ToleranceBoolean", 1e-6)

print("=" * 62)
print("Importing with OCCSewFaces and OCCMakeSolids enabled")
print("=" * 62)
gmsh.model.occ.importShapes(STEP)
gmsh.model.occ.synchronize()

def report(label):
    v = gmsh.model.getEntities(3)
    s = gmsh.model.getEntities(2)
    c = gmsh.model.getEntities(1)
    p = gmsh.model.getEntities(0)
    print(f"\n{label}")
    print(f"  volumes {len(v):5d}   surfaces {len(s):5d}"
          f"   curves {len(c):5d}   points {len(p):5d}")
    return v, s, c, p

vols, surfs, curvs, pts = report("After import:")

# ---------------------------------------------------------------------------
# Scale to wind tunnel model size
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print(f"Scaling by {SCALE:.6e}")
print("=" * 62)

all_ents = gmsh.model.getEntities()
gmsh.model.occ.dilate(all_ents, 0, 0, 0, SCALE, SCALE, SCALE)
gmsh.model.occ.synchronize()

bb = gmsh.model.getBoundingBox(-1, -1)
xmin, ymin, zmin, xmax, ymax, zmax = bb
span = ymax - ymin
body = xmax - xmin

print(f"  x : {xmin:10.5f} .. {xmax:10.5f}   extent {body:.5f}")
print(f"  y : {ymin:10.5f} .. {ymax:10.5f}   extent {span:.5f}")
print(f"  z : {zmin:10.5f} .. {zmax:10.5f}   extent {zmax-zmin:.5f}")
print(f"\n  span target 3.76550   got {span:.5f}   "
      f"error {100*abs(span-3.7655)/3.7655:.4f}%")
print(f"  body target 2.62350   got {body:.5f}   "
      f"error {100*abs(body-2.6235)/2.6235:.4f}%")

# ---------------------------------------------------------------------------
# Try to sew explicitly
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("Attempting explicit sew / solid construction")
print("=" * 62)

surf_tags = [t for (d, t) in gmsh.model.getEntities(2)]
print(f"  surface tags: {surf_tags}")

made_solid = False
try:
    sl = gmsh.model.occ.addSurfaceLoop(surf_tags, sewing=True)
    gmsh.model.occ.synchronize()
    print(f"  surface loop created: tag {sl}")
    try:
        v = gmsh.model.occ.addVolume([sl])
        gmsh.model.occ.synchronize()
        print(f"  VOLUME CREATED: tag {v}")
        made_solid = True
    except Exception as e:
        print(f"  volume creation FAILED: {e}")
except Exception as e:
    print(f"  surface loop FAILED: {e}")

vols, surfs, curvs, pts = report("After sewing attempt:")

# ---------------------------------------------------------------------------
# Closedness check via volume/area
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("Geometry measures")
print("=" * 62)

total_area = 0.0
for d, t in gmsh.model.getEntities(2):
    a = gmsh.model.occ.getMass(d, t)
    total_area += a
    print(f"  surface {t:4d}   area {a:12.6f} m2")
print(f"  total surface area {total_area:.6f} m2")

for d, t in gmsh.model.getEntities(3):
    vol = gmsh.model.occ.getMass(d, t)
    print(f"  volume  {t:4d}   {vol:12.6f} m3")

if not gmsh.model.getEntities(3):
    print("\n  NO VOLUME. The patches are not sewing into a closed solid.")
    print("  Likely because untrimmed surfaces overlap at the wing/tail")
    print("  junction rather than meeting cleanly.")
else:
    print("\n  Solid formed. Ready for boolean subtraction from a farfield box.")

if WRITE and made_solid:
    gmsh.write("n2a_solid.brep")
    print("\n  wrote n2a_solid.brep")

if GUI:
    gmsh.fltk.run()

gmsh.finalize()
