import sys
import numpy as np
from fuse import fuse

folder, step = sys.argv[1], int(sys.argv[2])
for mc in (2, 1, 0):
    p = fuse(folder, step=step, flip=False, rot_k=0, min_conf=mc)
    y = p[:, 1]
    lo = np.percentile(y, 20)
    h, e = np.histogram(y[y < lo], bins=np.arange(y.min(), lo + 0.01, 0.01))
    floor = e[np.argmax(h)] + 0.005
    up = y - floor
    print(f"min_conf={mc}: points={len(p):,}  above 1.8 m: {(up > 1.8).sum():,}"
          f"  above 2.2 m: {(up > 2.2).sum():,}  highest point: {up.max():.2f} m")