# N2A mesh study — findings

Fifteen snappyHexMesh runs. Final mesh passes checkMesh with no failed checks.

## Final mesh

| | |
|---|---|
| Cells | 2,114,068 |
| Surface faces on aircraft | 93,447 |
| Layer coverage | 93.6% |
| Layers achieved | 14.1 of 25 requested |
| First layer thickness | 1.25e-5 m |
| Max skewness | 3.997 (limit 4) |
| Max aspect ratio | 623 (OK) |
| Non-orthogonality | 75.0 max, 6.88 average |
| checkMesh | **Mesh OK**, no failed checks |
| Surface resolution | ~6.5 mm average |

Estimated y+ approximately 0.6-0.7 from first cell height. To be confirmed
against the solved field on the first run.

## The actual limiter: meshQualityControls

Layer coverage sat at 60-80% with only 1-3.6 layers surviving across many
attempts, regardless of layer thickness (12.5 micron to 0.5 mm, a factor of
40), layer count (5 to 33), expansion ratio, refinement level, or surface
quality.

The diagnostic was in the extrusion log: 87% of faces were extruding but only
69% thickness was achieved. Faces were not being rejected, they were being
truncated - which points at quality limits rather than at the geometry or the
shrinking algorithm.

Relaxing minTetQuality, minDeterminant, minFaceWeight, minVolRatio and
minTwist took coverage from 69% to 90%, and made the 12.5 micron first layer
achievable where it had previously given 27-39%.

## Refinement level

Once quality controls stopped being the constraint, the relationship between
refinement and coverage inverted. Under the restrictive settings coverage fell
monotonically with refinement; afterwards it rose.

| Level | Cells | Surface faces | Coverage | Layers | Max skewness |
|---|---|---|---|---|---|
| 8 | 416,698 | 9,537 | 83.2% | 5.47 | 3.87 |
| 9 | 1,756,961 | 30,247 | 90.1% | 8.93 | 4.50 (3 faces) |
| 10 | 2,118,703 | 93,449 | 94.0% | 14.1 | 10.84 (40 faces) |

## Skewness tuning

The 40 skewed faces at level 10 were on the aircraft surface, not internal.
Tightening maxBoundarySkewness cost almost nothing in coverage:

| maxBoundarySkewness | maxInternalSkewness | Max skewness | Bad faces | Coverage |
|---|---|---|---|---|
| 25 | 6 | 10.84 | 40 | 94.0% |
| 8 | 4 | 7.97 | 11 | 93.8% |
| **4** | **3** | **3.997** | **0** | **93.6%** |

The skewed faces were not the price of coverage - snappy was taking slack it
did not need.

## Memory and parallel meshing

Level 10 in serial peaked at 10.58 GB and was killed at 711 MB available on a
16 GB machine. Running with decomposePar and 4 MPI ranks completed
comfortably, peaking around 8 GB available remaining.

Also required trimming the volume refinement regions: refineNear at level 8
was generating 8.29 million cells on its own, most of the mesh, for volume
refinement rather than surface resolution. Dropping refineNear to 6 and
refineWake to 5 kept surface level 10 while cutting the cell count that had
caused the memory failure.

## Geometry

Surface generated with OpenVSP's own CFD Mesh tool rather than the raw STL
export. CFD Mesh intersects the components before tessellating, so the
wing/tail junctions resolve properly: single connected watertight part
(previously 3 separate), 171,858 triangles, OpenVSP reports "Is Water Tight".

This did not by itself improve layer coverage (70.3% against 71.1% for the raw
STL under the same settings) but it is better geometry and is what the final
mesh uses.

## Tested and ruled out

**Ben Malin's published best-of layer settings** (featureAngle 180,
maxFaceThicknessRatio 1, maxThicknessToMedialRatio 1, minMedialAxisAngle 30,
minThickness 0.1, nSmoothNormals 1, nSmoothSurfaceNormals 3, nSmoothThickness
0): 70.1%, no better than the baseline. His test geometry has acute corners and
90 degree features; this is a smooth blended body, so the tuning does not
transfer.

**ESI displacementMotionSolver / Laplacian shrinker** as an alternative to the
default medial axis algorithm: 69.2%. A completely different algorithm
arriving at the same number, which is what pointed at the quality controls.
Requires a cellDisplacement entry in fvSolution/solvers.

**nGrow 1**: collapses coverage to 0.05%. Isolated by reverting and testing
individually after an earlier five-parameter change produced the same collapse
with no attributable cause.

**minMedialAxisAngle 130**: raised from 90 on the basis of a single test
showing 73.9% to 79.9%. Ben Malin's systematic sweep says 30 is better. In
this case neither mattered once quality controls were relaxed.

## Meshing tools that did not work

**cfMesh (open source)** - cartesianMesh rejects the .fms that surfaceToFMS
writes, failing at line 1 regardless of patch naming, leading blank line
removal, or patch type. The free version also reportedly lacks boundary layer
meshing.

**gmsh** - STL reparametrisation fails with "Wrong topology of boundary mesh
for parametrization" due to degenerate triangles. Disabling reparametrisation
lets classification succeed but leaves the input triangles unremeshed and
gives the boundary layer field nothing to extrude from. STEP imports as 4
shells and 0 solids in OpenCASCADE, so no boolean subtraction is possible.

**SALOME** - download repeatedly cancelled, server too slow to complete.

**enGrid** - depends on Qt4 and VTK 6, both obsolete on Fedora 42.

**SimScale** - CAD kernel does close the geometry into 4 solid bodies (0 sheet
bodies) and successfully builds the external flow region, which OpenCASCADE
could not. However it flags two degenerate trailing-edge edges, restricting
the model to Incompressible LBM, Pedestrian Wind Comfort and CHT-IBM. None is
compressible RANS. Fix interferences and Gaps both report nothing to repair,
so the fault is within surfaces rather than between bodies.

**cfMesh+** - Creative Fields do not issue trial licences to students.

## Operational notes

**snappyHexMesh -overwrite requires blockMesh to be re-run first.** The flag
writes into constant/polyMesh, replacing the background mesh. A second run
then starts from a snapped mesh and hexRef8 fails with "cell N of level M does
not seem to have 8 points of equal or lower level" - refinement needs an
intact octree hierarchy, which snapping destroys.

**symmetryPlane planarity.** blockMesh's symmetryPlane patch failed its
planarity check after a polyMesh removal, with the average normal off by
2.5e-4. Switched to the tolerant `symmetry` type, physically equivalent for a
flat patch.

**OpenVSP STEP export writes milli-feet** while declaring metres in the
header. Scale factor to the 5.8% wind tunnel model is 1.76784e-5 from STEP,
or 0.0176784 from the STL export which is in plain feet.

**OpenVSP patch names are digit-prefixed** (1_Wing_Body_S_Surf0), and
OpenFOAM's word type rejects names starting with a numeral.
