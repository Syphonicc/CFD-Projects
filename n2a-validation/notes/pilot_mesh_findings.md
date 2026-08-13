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
