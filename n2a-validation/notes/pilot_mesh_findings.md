# Pilot mesh findings

Level 6-7 surface refinement, 5 prism layers. ~197k cells, ~90 s per run.
Purpose was to validate the pipeline, not to produce a solution mesh.

## Layer coverage experiments

One parameter changed at a time from the baseline dict.

| Configuration | wing_body_0 | vertical_tails_0 |
|---|---|---|
| Baseline | 73.9% | 31.8% |
| maxThicknessToMedialRatio 0.3 -> 0.6 | 73.9% | 33.4% |
| + nGrow 0 -> 1 | 0.05% | 0% |
| minMedialAxisAngle 90 -> 130, nLayerIter 50 -> 80, nRelaxedIter 20 -> 50 | 79.9% | 33.4% |
| + vertical tails level (7 8) -> (8 9) | 79.9% | 33.4% |

## Findings

**nGrow 1 collapses layer coverage on this geometry.** Isolated by reverting
and testing individually. Body coverage fell from 73.9% to 0.05%, tails to
zero. Inferred mechanism: growing layers from points where extrusion had
already stopped propagates poor normals, the resulting cells fail quality
checks, and the stack is discarded. Inference from the result, not verified
against source.

**minMedialAxisAngle 130 plus more iterations is the only change that helped**
- 73.9% to 79.9% on the main body.

**maxThicknessToMedialRatio 0.6 is roughly neutral here** - within noise on the
body, marginal on the tails.

**The vertical tails do not respond to refinement.** Surface face count stayed
at exactly 189 despite requesting level (8 9) rather than (7 8), indicating the
nCellsBetweenLevels buffer constraint blocks it or the feature is too thin to
subdivide. Tail coverage is 33.4% and is documented as a limitation rather
than resolved: the tails are 189 of 3182 surface faces, 6% of wetted area.

**snappyHexMesh -overwrite requires blockMesh to be re-run first.** The flag
writes into constant/polyMesh, replacing the background mesh. A second run
then starts from a snapped mesh and hexRef8 fails with "cell N of level M does
not seem to have 8 points of equal or lower level" - refinement needs an
intact octree hierarchy, which snapping destroys.

## Mesh quality

Zero violations at every check: non-orthogonality, skewness, tet quality,
concavity, face twist, determinant, volume ratio, interpolation weights.

## Half-model confirmation

wing_body_1 and vertical_tails_1 have zero faces - the port half of the STL
lies outside the domain (y < 0), as intended. Symmetry plane 6604 faces.

## Not yet established

Whether the layer stack survives at the production 33 layers. Coverage at 5
layers does not predict coverage at 33: more total thickness can help on open
surfaces and hurt at junctions. This needs a level-8, 33-layer test.

---

# Production layer study (level 8 and 9, absolute sizing)

| Run | Refinement | Layers requested | Stack | Body coverage | Layers achieved |
|---|---|---|---|---|---|
| Pilot | level 7 | 5 (relative) | ~40 mm | 79.9% | 3.53 |
| L8 | level 8 | 33 (absolute) | 26 mm | 61.9% | 3.12 |
| L9 | level 9 | 33 (absolute) | 26 mm | 38.7% | 2.16 |
| L9-20 | level 9 | 20, ratio 1.25 | 4.3 mm | 27.1% | 1.10 |

First layer 12.5 micron throughout (y+ ~ 1 target).

## Mechanism

Extrusion is rejected before thickness is considered:

    Extruding 9791 out of 19527 faces (50.1%). Removed extrusion at 5596 faces.
    displacementMedialAxis : Number of isolated points extrusion stopped : 105

Half the surface refuses layers from iteration one, degrading to 43.9%.

## Hypotheses tested and rejected

**Total stack thickness.** Varied from ~40 mm to 4.3 mm, a factor of 10.
Coverage got worse as the stack got thinner, opposite to the prediction.

**Surface refinement level.** Coverage falls monotonically as cells get finer,
also opposite to the prediction that finer cells would let thinner layers fit.

**STL quality.** surfaceCheck reports the surface closed with no illegal
triangles. One sliver triangle at quality 1.5e-4 and a 33 micron edge at the
trailing edge, but surfaceClean collapsed nothing at sensible thresholds.

## cfMesh attempt

Tried as an alternative because cfMesh generates layers during mesh
construction rather than inserting them afterwards by shrinking the volume
mesh, so the extrusion-rejection failure mode should not arise.

Blocked at file conversion. surfaceToFMS produces an .fms that cartesianMesh
rejects with an IOstream error at line 1. Attempted fixes, none successful:
removing a leading blank line, renaming the digit-prefixed OpenVSP patch names
(OpenFOAM word type rejects leading numerals), changing patch type from empty
to wall.

## Other findings

**symmetryPlane planarity.** After removing constant/polyMesh and rebuilding,
blockMesh's symmetryPlane patch failed its planarity check (average normal
off by 2.5e-4). Switched to the tolerant `symmetry` type, which is physically
equivalent for a flat patch.

## Status

Raised with Othrys: whether a standard snappy fix exists for this pattern, and
whether wall functions at y+ 30-100 would be acceptable as a documented
deviation from the brief's wall-resolved requirement.
