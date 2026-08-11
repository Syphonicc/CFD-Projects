#!/usr/bin/env python3
"""
NASA TMR PLOT3D 2D NACA 0012 C-grid → Gmsh .msh v2.2 (for gmshToFoam)
=====================================================================
Reads the 2D formatted PLOT3D grid from
    https://tmbwg.github.io/turbmodels/naca0012_grids.html
and writes a Gmsh ASCII .msh file ready for `gmshToFoam`.

Handles:
  - Wake-cut node deduplication (i,1) ↔ (imax+1-i, 1) merging
  - Sharp TE point merging
  - Extrusion to single-cell-thick 3D slab for OpenFOAM 2D simulations
  - Correct physical groups matching your existing 0/ folder patch names:
       inlet, outlet, walls, frontAndBack, fluid

Usage:
    python3 plot3d_to_msh.py n0012_897-257.p2dfmt n0012_TMR.msh
"""

import numpy as np
import sys
import time

# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
if len(sys.argv) >= 3:
    plot3d_file, output_file = sys.argv[1], sys.argv[2]
else:
    plot3d_file = "n0012_897-257.p2dfmt"
    output_file = "n0012_TMR.msh"

z_thickness = 0.1     # OpenFOAM 2D slab thickness
tol         = 1e-12   # node-merging tolerance

# ------------------------------------------------------------------
# READ PLOT3D 2D (formatted, single block, no iblank)
# ------------------------------------------------------------------
print(f"Reading {plot3d_file} ...")
t0 = time.time()
with open(plot3d_file) as f:
    tokens = f.read().split()

idx = 0
nbl  = int(tokens[idx]); idx += 1
assert nbl == 1, "Only single-block grids are supported"
idim = int(tokens[idx]); idx += 1
jdim = int(tokens[idx]); idx += 1
n    = idim * jdim
x = np.array(tokens[idx:idx+n], dtype=float).reshape(jdim, idim); idx += n
y = np.array(tokens[idx:idx+n], dtype=float).reshape(jdim, idim); idx += n
print(f"  Grid:        {idim} x {jdim}")
print(f"  x extent:    {x.min():.3f}  to  {x.max():.3f}")
print(f"  y extent:    {y.min():.3f}  to  {y.max():.3f}")

# ------------------------------------------------------------------
# DEDUPLICATE 2D NODES (handles C-mesh wake cut + sharp TE)
# ------------------------------------------------------------------
# Flatten in row-major order: ij_flat = j*idim + i
xy = np.column_stack([x.ravel(), y.ravel()])
key = np.round(xy / tol).astype(np.int64)
unique_keys = {}
node_map_2d = np.empty(idim*jdim, dtype=np.int32)
unique_coords = []
for flat, k in enumerate(map(tuple, key)):
    u = unique_keys.get(k)
    if u is None:
        u = len(unique_coords)
        unique_keys[k] = u
        unique_coords.append(xy[flat])
    node_map_2d[flat] = u
n_unique_2d = len(unique_coords)
print(f"  Unique 2D nodes: {n_unique_2d}  (from {idim*jdim} raw, "
      f"merged {idim*jdim - n_unique_2d} duplicates at wake-cut + TE)")

def n2d(i, j):
    return node_map_2d[j*idim + i]

def n3d(i, j, k):
    """k=0 -> z=0 plane, k=1 -> z=z_thickness plane."""
    return n2d(i, j) + k * n_unique_2d

# ------------------------------------------------------------------
# 3D POINTS
# ------------------------------------------------------------------
points_3d = np.empty((2*n_unique_2d, 3), dtype=float)
uc = np.array(unique_coords)
points_3d[:n_unique_2d, 0:2]   = uc;  points_3d[:n_unique_2d, 2]   = 0.0
points_3d[n_unique_2d:, 0:2]   = uc;  points_3d[n_unique_2d:, 2]   = z_thickness
n_total = len(points_3d)

# ------------------------------------------------------------------
# AIRFOIL i-RANGE on j=0 (used to label "walls" vs. wake-cut)
# Airfoil surface: x ∈ [0, 1].  Wake nodes are at x > 1, y = 0.
# ------------------------------------------------------------------
on_airfoil = (x[0, :] >= -1e-6) & (x[0, :] <= 1.0 + 1e-6)
i_air_idx  = np.where(on_airfoil)[0]
i_air_lo, i_air_hi = int(i_air_idx[0]), int(i_air_idx[-1])
print(f"  Airfoil i-range: {i_air_lo} .. {i_air_hi}  "
      f"({i_air_hi - i_air_lo + 1} surface points)")

# ------------------------------------------------------------------
# HEX CELLS  ( (idim-1) * (jdim-1) hexes, 1 z-layer )
# ------------------------------------------------------------------
print("Building cells & faces ...")
ii, jj = np.meshgrid(np.arange(idim-1), np.arange(jdim-1), indexing='xy')
ii = ii.ravel(); jj = jj.ravel()
cells = np.column_stack([
    n3d(ii,   jj,   0), n3d(ii+1, jj,   0),
    n3d(ii+1, jj+1, 0), n3d(ii,   jj+1, 0),
    n3d(ii,   jj,   1), n3d(ii+1, jj,   1),
    n3d(ii+1, jj+1, 1), n3d(ii,   jj+1, 1),
])
n_cells = len(cells)

# ------------------------------------------------------------------
# BOUNDARY FACES
# ------------------------------------------------------------------
# walls = j=0 quads where the edge (i,i+1) lies on the airfoil
i_all = np.arange(idim-1)
on_wall = (i_all >= i_air_lo) & (i_all+1 <= i_air_hi)
iw = i_all[on_wall]
walls_faces = np.column_stack([
    n3d(iw,   0, 0), n3d(iw+1, 0, 0),
    n3d(iw+1, 0, 1), n3d(iw,   0, 1),
])

# inlet (= far-field C-arc) = j=jmax for all i
inlet_faces = np.column_stack([
    n3d(i_all,   jdim-1, 0), n3d(i_all+1, jdim-1, 0),
    n3d(i_all+1, jdim-1, 1), n3d(i_all,   jdim-1, 1),
])

# outlet = downstream face at i=0 (lower wake exit) and i=idim-1 (upper wake exit),
# both for j=0..jmax-1
j_all = np.arange(jdim-1)
outlet_lo = np.column_stack([
    n3d(0, j_all,   0), n3d(0, j_all+1, 0),
    n3d(0, j_all+1, 1), n3d(0, j_all,   1),
])
outlet_hi = np.column_stack([
    n3d(idim-1, j_all,   0), n3d(idim-1, j_all+1, 0),
    n3d(idim-1, j_all+1, 1), n3d(idim-1, j_all,   1),
])
outlet_faces = np.vstack([outlet_lo, outlet_hi])

# frontAndBack = all k=0 and k=1 faces  (z-normal "empty" pair)
II, JJ = np.meshgrid(np.arange(idim-1), np.arange(jdim-1), indexing='xy')
II = II.ravel(); JJ = JJ.ravel()
fb_k0 = np.column_stack([
    n3d(II,   JJ,   0), n3d(II+1, JJ,   0),
    n3d(II+1, JJ+1, 0), n3d(II,   JJ+1, 0),
])
fb_k1 = np.column_stack([
    n3d(II,   JJ,   1), n3d(II+1, JJ,   1),
    n3d(II+1, JJ+1, 1), n3d(II,   JJ+1, 1),
])
frontBack_faces = np.vstack([fb_k0, fb_k1])

print(f"  hex cells   : {n_cells}")
print(f"  walls       : {len(walls_faces)}")
print(f"  inlet       : {len(inlet_faces)}")
print(f"  outlet      : {len(outlet_faces)}")
print(f"  frontAndBack: {len(frontBack_faces)}")

# ------------------------------------------------------------------
# WRITE GMSH v2.2 ASCII  (read by OpenFOAM `gmshToFoam`)
# ------------------------------------------------------------------
# Physical groups -> patch names in OpenFOAM
#   tag 1 = inlet,   tag 2 = outlet,   tag 3 = walls,
#   tag 4 = frontAndBack,   tag 5 = fluid (3D volume)
# Element types: 5 = 8-node hex,  3 = 4-node quad
# Element line: id type ntags physTag elemTag <nodes...>  (1-indexed nodes)
print(f"Writing {output_file} ...")
with open(output_file, 'w') as f:
    f.write("$MeshFormat\n2.2 0 8\n$EndMeshFormat\n")
    f.write('$PhysicalNames\n5\n')
    f.write('2 1 "inlet"\n')
    f.write('2 2 "outlet"\n')
    f.write('2 3 "walls"\n')
    f.write('2 4 "frontAndBack"\n')
    f.write('3 5 "fluid"\n')
    f.write('$EndPhysicalNames\n')

    # Nodes
    f.write(f"$Nodes\n{n_total}\n")
    lines = [f"{i+1} {p[0]:.16e} {p[1]:.16e} {p[2]:.16e}\n"
             for i, p in enumerate(points_3d)]
    f.writelines(lines)
    f.write("$EndNodes\n")

    # Elements
    n_elem = (n_cells + len(walls_faces) + len(inlet_faces)
              + len(outlet_faces) + len(frontBack_faces))
    f.write(f"$Elements\n{n_elem}\n")
    eid = 1

    # Hex volume (physical = 5 = fluid)
    for nodes in cells:
        f.write(f"{eid} 5 2 5 1 " + " ".join(str(n+1) for n in nodes) + "\n")
        eid += 1
    # Quad boundary faces
    for nodes in walls_faces:
        f.write(f"{eid} 3 2 3 1 " + " ".join(str(n+1) for n in nodes) + "\n")
        eid += 1
    for nodes in inlet_faces:
        f.write(f"{eid} 3 2 1 1 " + " ".join(str(n+1) for n in nodes) + "\n")
        eid += 1
    for nodes in outlet_faces:
        f.write(f"{eid} 3 2 2 1 " + " ".join(str(n+1) for n in nodes) + "\n")
        eid += 1
    for nodes in frontBack_faces:
        f.write(f"{eid} 3 2 4 1 " + " ".join(str(n+1) for n in nodes) + "\n")
        eid += 1
    f.write("$EndElements\n")

print(f"\nDone in {time.time()-t0:.1f}s.")
print(f"  Nodes (3D): {n_total}")
print(f"  Cells     : {n_cells}")
print(f"\nNext:")
print(f"  source /usr/lib/openfoam/openfoam2512/etc/bashrc")
print(f"  gmshToFoam {output_file}")
print(f"  # Edit constant/polyMesh/boundary: frontAndBack -> type empty")
print(f"  checkMesh")
