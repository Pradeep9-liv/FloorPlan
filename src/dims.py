import os
import numpy as np

METHOD = os.environ.get("DIMS_METHOD", "rays")   # "bbox" reproduces the before run


def _first_hit(walls, a0, b0, cell, start, axis, sign, max_m=12.0):
    for k in range(1, int(max_m / cell)):
        q = np.array(start, float)
        q[axis] += sign * k * cell
        i = int(np.floor((q[0] - a0) / cell))
        j = int(np.floor((q[1] - b0) / cell))
        if 0 <= i < walls.shape[0] and 0 <= j < walls.shape[1] and walls[i, j]:
            return k * cell
    return None


def wall_to_wall(walls, a0, b0, cell, wa, wb, p0, axis,
                 lat_offsets=np.arange(-0.5, 0.51, 0.1), min_rays=5):
    """Distance between the two walls on either side of p0 along `axis`.
    Median over parallel rays; each ray is refined to a 1 cm density peak."""
    if METHOD == "bbox":
        return None
    along = (wa, wb)[axis]
    lateral = (wb, wa)[axis]
    side = {}
    for sign in (-1, +1):
        ds = []
        for off in lat_offsets:
            start = list(p0)
            start[1 - axis] += off
            d0 = _first_hit(walls, a0, b0, cell, start, axis, sign)
            if d0 is None:
                continue
            hit = start[axis] + sign * d0
            sel = ((np.abs(lateral - start[1 - axis]) < 0.05)
                   & (along > hit - 0.07) & (along < hit + 0.07))
            x = along[sel]
            if len(x) < 30:
                continue
            edges = np.arange(hit - 0.07, hit + 0.0701, 0.01)
            cnt, e = np.histogram(x, bins=edges)
            sm = np.convolve(cnt, np.ones(3), mode="same")
            k = int(np.argmax(sm))
            lo, hi = max(0, k - 1), min(len(cnt), k + 2)
            ctr = (e[:-1] + e[1:]) / 2
            pk = float((cnt[lo:hi] * ctr[lo:hi]).sum() / max(1, cnt[lo:hi].sum()))
            ds.append(sign * (pk - start[axis]))
        if len(ds) < min_rays:
            return None
        side[sign] = float(np.median(ds))
    return side[-1] + side[+1]