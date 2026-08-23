#!/usr/bin/env python3
"""
Digitise Figures 13 (C_D) and 15 (C_m) of Aprovitola et al. (2022).

Calibration from detected gridlines, cross-checked against the zero lines:
  Fig 13   x: px 151 -> -15 deg, px 451 -> 0 deg
           y: px  44 -> C_D 0.30, px 660 -> C_D 0.00
  Fig 15   x: px 136 -> -15 deg, px 421 -> 0 deg
           y: px  48 -> C_m 0.025, px 687 -> C_m -0.025

Figure 13 has no Cart3D series; Figure 15 does.
"""

import numpy as np
from PIL import Image

FIGS = {
    "fig13_Cd": dict(
        path="/mnt/user-data/uploads/1787473144709_image.png",
        xpx=(151.0, 451.0), xval=(-15.0, 0.0),
        ypx=(44.0, 660.0),  yval=(0.30, 0.00),
        box=((140, 900), (35, 670)),
        excl=[((810, 1179), (240, 746))],
        series=("T597", "T612", "FLUENT", "SU2"),
    ),
    "fig15_Cm": dict(
        path="/mnt/user-data/uploads/1787473191387_image.png",
        xpx=(136.0, 421.0), xval=(-15.0, 0.0),
        ypx=(48.0, 687.0),  yval=(0.025, -0.025),
        box=((125, 960), (40, 700)),
        excl=[((760, 1179), (520, 746)), ((680, 1179), (0, 235))],
        series=("T597", "T612", "Cart3D", "FLUENT", "SU2"),
    ),
}

TARGETS = (6.0, 10.0)


def masks(a):
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mx, mn = a.max(2), a.min(2)
    return {
        "T597":   ((R > 150) & (G < 90) & (B < 90), "line"),
        "T612":   ((mx < 70) & (mx - mn < 40), "line"),
        "Cart3D": ((G > 110) & (R < 150) & (B < 130) &
                   (G - R > 40) & (G - B > 40), "marker"),
        "FLUENT": ((B > 110) & (R < 110) & (G < 150) & (B - R > 50), "marker"),
        "SU2":    ((R > 190) & (G > 130) & (G < 215) & (B < 110), "marker"),
    }


def extract(cfg):
    a = np.array(Image.open(cfg["path"]).convert("RGB")).astype(int)
    h, w, _ = a.shape

    def px2x(p):
        (x0, x1), (v0, v1) = cfg["xpx"], cfg["xval"]
        return v0 + (p - x0) * (v1 - v0) / (x1 - x0)

    def px2y(p):
        (y0, y1), (v0, v1) = cfg["ypx"], cfg["yval"]
        return v0 + (p - y0) * (v1 - v0) / (y1 - y0)

    keep = np.zeros((h, w), bool)
    (bx0, bx1), (by0, by1) = cfg["box"]
    keep[by0:by1, bx0:bx1] = True
    for (ex0, ex1), (ey0, ey1) in cfg["excl"]:
        keep[ey0:ey1, ex0:ex1] = False

    out = {}
    for name, (m, kind) in masks(a).items():
        if name not in cfg["series"]:
            continue
        m = m & keep
        ys, xs = np.where(m)
        if len(xs) < 20:
            out[name] = np.empty((0, 2))
            continue
        if kind == "line":
            pts = []
            for xp in range(xs.min(), xs.max() + 1):
                col = ys[xs == xp]
                if len(col):
                    pts.append((px2x(xp), px2y(np.median(col))))
            out[name] = np.array(pts)
        else:
            o = np.argsort(xs)
            xs2, ys2 = xs[o], ys[o]
            cl, cur = [], [(xs2[0], ys2[0])]
            for xp, yp in zip(xs2[1:], ys2[1:]):
                if xp - cur[-1][0] <= 6:
                    cur.append((xp, yp))
                else:
                    cl.append(cur); cur = [(xp, yp)]
            cl.append(cur)
            pts = [(px2x(np.mean([p[0] for p in c])),
                    px2y(np.mean([p[1] for p in c])))
                   for c in cl if len(c) >= 12]
            out[name] = np.array(sorted(pts)) if pts else np.empty((0, 2))
    return out


def at(pts, alpha, tol=0.6):
    if len(pts) == 0:
        return None
    if len(pts) > 40:
        if alpha < pts[:, 0].min() or alpha > pts[:, 0].max():
            return None
        return float(np.interp(alpha, pts[:, 0], pts[:, 1]))
    d = np.abs(pts[:, 0] - alpha)
    return float(pts[np.argmin(d)][1]) if d.min() <= tol else None


allres = {}
for tag, cfg in FIGS.items():
    r = extract(cfg)
    allres[tag] = r
    print(f"\n=== {tag}")
    for n in cfg["series"]:
        p = r[n]
        if len(p) == 0:
            print(f"  {n:8s} none"); continue
        v6, v10 = at(p, 6.0), at(p, 10.0)
        s6 = f"{v6:9.5f}" if v6 is not None else f"{'-':>9s}"
        s10 = f"{v10:9.5f}" if v10 is not None else f"{'-':>9s}"
        print(f"  {n:8s} n={len(p):4d}  a=6: {s6}   a=10: {s10}")

# sanity: C_m should cross zero near alpha = 3 for the tunnel curves
print("\nsanity")
for n in ("T597", "T612"):
    p = allres["fig15_Cm"][n]
    if len(p):
        print(f"  Cm {n} at a=0: {at(p,0.0):.5f}   at a=8.36: {at(p,8.36):.5f}")
for n in ("T597", "T612"):
    p = allres["fig13_Cd"][n]
    if len(p):
        print(f"  Cd {n} at a=0: {at(p,0.0):.5f}   at a=8.36: {at(p,8.36):.5f}")

np.save("/home/claude/fig1315.npy", allres, allow_pickle=True)
