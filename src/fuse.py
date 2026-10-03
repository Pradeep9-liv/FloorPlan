import numpy as np, pandas as pd, glob, os, sys, itertools
from scipy.spatial.transform import Rotation as R

def load_depth(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".npy":
        d = np.load(path).astype(np.float32)
    elif ext in (".png", ".tiff", ".tif"):
        import cv2
        d = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
    elif ext == ".bin":
        d = np.fromfile(path, dtype=np.float32).reshape(192, 256)
    elif ext == ".exr":
        import cv2
        os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
        d = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
    else:
        raise ValueError(ext)
    return d

def load_conf(path):
    import cv2
    return cv2.imread(path, cv2.IMREAD_UNCHANGED)

def inspect(folder):
    d = sorted(glob.glob(f"{folder}/depth/*"))
    c = sorted(glob.glob(f"{folder}/confidence/*"))
    print("n depth", len(d), "n conf", len(c), "ext", os.path.splitext(d[0])[1])
    dep = load_depth(d[len(d)//2])
    print("depth shape", dep.shape, "dtype", dep.dtype,
          "min/max", dep.min(), dep.max(), "median", np.median(dep))
    cf = load_conf(c[len(c)//2])
    print("conf shape", cf.shape, "unique", np.unique(cf))
    odo = pd.read_csv(f"{folder}/odometry.csv", skipinitialspace=True)
    print(odo[["fx", "fy", "cx", "cy"]].describe().loc[["min", "max"]])
    print("frames in odometry", len(odo))

def backproject(depth, fx, fy, cx, cy, conf=None, min_conf=2, max_z=6.0):
    h, w = depth.shape
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    z = depth
    ok = (z > 0.1) & (z < max_z) & np.isfinite(z)
    if conf is not None:
        ok &= conf >= min_conf
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    return np.stack([x, y, z], -1)[ok]

def to_world(pts_cv, row, flip, rot_k):
    # flip: True -> ARKit/OpenGL camera axes (x right, y up, z back)
    p = pts_cv.copy()
    if flip:
        p[:, 1] *= -1
        p[:, 2] *= -1
    if rot_k:
        rz = R.from_euler("z", 90 * rot_k, degrees=True).as_matrix()
        p = p @ rz.T
    Rw = R.from_quat([row.qx, row.qy, row.qz, row.qw]).as_matrix()
    t = np.array([row.x, row.y, row.z])
    return p @ Rw.T + t

def fuse(folder, step=8, flip=True, rot_k=0, min_conf=2, scale=7.5):
    odo = pd.read_csv(f"{folder}/odometry.csv", skipinitialspace=True)
    dfiles = sorted(glob.glob(f"{folder}/depth/*"))
    cfiles = sorted(glob.glob(f"{folder}/confidence/*"))
    clouds = []
    for i in range(0, min(len(dfiles), len(odo)), step):
        row = odo.iloc[i]
        dep = load_depth(dfiles[i])
        cf = load_conf(cfiles[i])
        pts = backproject(dep, row.fx/scale, row.fy/scale,
                          row.cx/scale, row.cy/scale, cf, min_conf)
        clouds.append(to_world(pts, row, flip, rot_k))
    return np.vstack(clouds)

def score(cloud, vox=0.03):
    # lower = surfaces overlap more consistently
    q = np.floor(cloud / vox).astype(np.int64)
    return len(np.unique(q, axis=0)) / len(cloud)

if __name__ == "__main__":
    folder = sys.argv[1]
    inspect(folder)
    res = []
    for flip, k in itertools.product([False, True], range(4)):
        c = fuse(folder, step=20, flip=flip, rot_k=k)
        res.append((score(c), flip, k))
        print("flip", flip, "rot", k, "score", round(res[-1][0], 4))
    print("best:", min(res))