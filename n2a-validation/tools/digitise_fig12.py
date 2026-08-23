#!/usr/bin/env python3
"""
Digitise Figure 12 of Aprovitola et al. (2022) by colour separation.

Calibration is derived from the detected gridlines:
    x:  px 246 -> -15 deg,   px 1169 -> +30 deg
    y:  px  55 -> C_L 0.8,   px  689 -> C_L -0.6

Both anchors cross-check against independently detected gridlines
(x = 0 at px 554, C_L = 0 at px 417).

Series are separated by colour:
    T597 closed tunnel   red line + markers
    T612 open tunnel     black line + markers
    Cart3D               green squares
    FLUENT               blue triangles
    SU2                  orange diamonds

Regions excluded: the legend box (x 895-1210, y > 705) and the aircraft
sketch (x > 1180, y 300-600), both of which contain series colours.
"""

import numpy as np
from PIL import Image

IMG = "/mnt/user-data/uploads/1787130834692_image.png"

# ---- calibration -----------------------------------------------------------
X_PX, X_VAL = (246.0, 1169.0), (-15.0, 30.0)
Y_PX, Y_VAL = (55.0, 689.0), (0.8, -0.6)


def px2x(px):
    return X_VAL[0] + (px - X_PX[0]) * (X_VAL[1] - X_VAL[0]) / (X_PX[1] - X_PX[0])


def px2y(py):
    return Y_VAL[0] + (py - Y_PX[0]) * (Y_VAL[1] - Y_VAL[0]) / (Y_PX[1] - Y_PX[0])


a = np.array(Image.open(IMG).convert("RGB")).astype(int)
h, w, _ = a.shape
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
mx, mn = a.max(2), a.min(2)

# Restrict everything to the plot box. Axis tick labels, the x-axis title,
# the legend and the aircraft sketch all lie outside it, and all of them
# contain series colours (the tick labels in particular are black, which
# otherwise swamps the T612 series).
excl = np.ones((h, w), bool)
excl[int(Y_PX[0]) - 4:int(Y_PX[1]) + 4,
     int(X_PX[0]) - 4:int(X_PX[1]) + 4] = False
# the legend box sits inside the lower right of the plot area and its key
# markers are picked up as data; real data in that x range lies far higher
excl[590:, 900:] = True

SERIES = {
    "T597 closed tunnel": ((R > 150) & (G < 90) & (B < 90), "line"),
    "T612 open tunnel":   ((mx < 70) & (mx - mn < 40), "line"),
    "Cart3D":             ((G > 110) & (R < 150) & (B < 130) &
                           (G - R > 40) & (G - B > 40), "marker"),
    "FLUENT":             ((B > 110) & (R < 110) & (G < 150) & (B - R > 50), "marker"),
    "SU2":                ((R > 190) & (G > 130) & (G < 215) & (B < 110), "marker"),
}

results = {}

for name, (m, kind) in SERIES.items():
    m = m & ~excl
    ys, xs = np.where(m)
    if len(xs) == 0:
        print(f"{name}: no pixels")
        continue

    if kind == "line":
        # one value per pixel column, median of the column's pixels
        pts = []
        for xp in range(xs.min(), xs.max() + 1):
            col = ys[xs == xp]
            if len(col) == 0:
                continue
            pts.append((px2x(xp), px2y(np.median(col))))
        pts = np.array(pts)
    else:
        # cluster marker blobs
        order = np.argsort(xs)
        xs2, ys2 = xs[order], ys[order]
        clusters, cur = [], [(xs2[0], ys2[0])]
        for xp, yp in zip(xs2[1:], ys2[1:]):
            if xp - cur[-1][0] <= 6:
                cur.append((xp, yp))
            else:
                clusters.append(cur)
                cur = [(xp, yp)]
        clusters.append(cur)
        pts = []
        for c in clusters:
            if len(c) < 12:
                continue
            cx = np.mean([p[0] for p in c])
            cy = np.mean([p[1] for p in c])
            pts.append((px2x(cx), px2y(cy)))
        pts = np.array(sorted(pts))

    results[name] = pts
    print(f"{name:22s} {len(pts):4d} points   "
          f"alpha {pts[:,0].min():6.2f} to {pts[:,0].max():6.2f}")


def value_at(pts, alpha, tol=0.6):
    """Interpolate a line series, or take the nearest marker within tol."""
    if pts is None or len(pts) == 0:
        return None
    d = np.abs(pts[:, 0] - alpha)
    if len(pts) > 40:                      # dense -> line, interpolate
        return float(np.interp(alpha, pts[:, 0], pts[:, 1]))
    if d.min() <= tol:
        return float(pts[np.argmin(d)][1])
    return None


print("\n" + "=" * 58)
print("C_L from Figure 12")
print("=" * 58)
print(f"{'dataset':24s} {'alpha=6':>10s} {'alpha=10':>10s}")
print("-" * 58)
for name in SERIES:
    if name not in results:
        continue
    v6 = value_at(results[name], 6.0)
    v10 = value_at(results[name], 10.0)
    s6 = f"{v6:10.4f}" if v6 is not None else f"{'-':>10s}"
    s10 = f"{v10:10.4f}" if v10 is not None else f"{'-':>10s}"
    print(f"{name:24s} {s6} {s10}")

# sanity checks against features that can be read by eye
print("\nsanity checks")
for nm in ("T597 closed tunnel", "T612 open tunnel"):
    if nm in results:
        p = results[nm]
        print(f"  {nm:22s} C_L at alpha=0: {value_at(p,0.0):.4f}   "
              f"at alpha=8.36: {value_at(p,8.36):.4f}")

np.save("/home/claude/fig12_series.npy", results, allow_pickle=True)
