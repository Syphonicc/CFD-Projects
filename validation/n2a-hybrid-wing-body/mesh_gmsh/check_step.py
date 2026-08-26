#!/usr/bin/env python3
"""
STEP import check.

Reports bounding box, entity counts and units so we know what we actually
have before setting up a mesh.

Usage:
    python3 check_step.py n2a.stp
    python3 check_step.py n2a.stp --gui
"""

import gmsh
import sys

fn  = sys.argv[1] if len(sys.argv) > 1 else "n2a.stp"
gui = "--gui" in sys.argv

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)

print(f"Importing {fn} ...")
gmsh.model.occ.importShapes(fn)
gmsh.model.occ.synchronize()

vols  = gmsh.model.getEntities(3)
surfs = gmsh.model.getEntities(2)
curvs = gmsh.model.getEntities(1)
pts   = gmsh.model.getEntities(0)

print(f"\nEntities:")
print(f"  volumes  : {len(vols)}")
print(f"  surfaces : {len(surfs)}")
print(f"  curves   : {len(curvs)}")
print(f"  points   : {len(pts)}")

bb = gmsh.model.getBoundingBox(-1, -1)
xmin, ymin, zmin, xmax, ymax, zmax = bb
print(f"\nBounding box:")
print(f"  x : {xmin:12.5f}  ..  {xmax:12.5f}   extent {xmax-xmin:.5f}")
print(f"  y : {ymin:12.5f}  ..  {ymax:12.5f}   extent {ymax-ymin:.5f}")
print(f"  z : {zmin:12.5f}  ..  {zmax:12.5f}   extent {zmax-zmin:.5f}")

span = ymax - ymin
body = xmax - xmin

print(f"\nUnit inference:")
print(f"  span   {span:10.4f}")
print(f"  body   {body:10.4f}")
print(f"    full scale metres would be : span 64.92,  body 45.10")
print(f"    full scale feet   would be : span 213.0,  body 148.0")
print(f"    WT model metres   would be : span 3.766,  body 2.616")

for name, ref in (("full-scale m", 64.92), ("full-scale ft", 213.0),
                  ("WT model m", 3.766)):
    if abs(span - ref) / ref < 0.02:
        print(f"  -> matches {name}")

# scale factor needed to reach the 5.8% wind tunnel model in metres
target_span = 3.7655
print(f"\n  scale factor to WT model (span {target_span}): {target_span/span:.10f}")

if surfs:
    print(f"\nFirst 10 surfaces (tag, area):")
    for d, t in surfs[:10]:
        m = gmsh.model.occ.getMass(d, t)
        print(f"  {t:5d}  {m:14.6e}")

if gui:
    gmsh.fltk.run()

gmsh.finalize()
