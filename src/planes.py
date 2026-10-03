import sys
import numpy as np
import open3d as o3d
from fuse import fuse

def find_planes(pts, n_planes=6, thresh=0.02):
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
    pcd = pcd.voxel_down_sample(0.01)   # 1 cm grid: far fewer points, same shape
    print("points after downsampling:", len(pcd.points))
    planes = []
    for _ in range(n_planes):
        if len(pcd.points) < 5000:
            break
        model, inliers = pcd.segment_plane(thresh, 3, 2000)
        n = np.array(model[:3])
        s = np.linalg.norm(n)
        planes.append((n / s, model[3] / s, len(inliers)))
        pcd = pcd.select_by_index(inliers, invert=True)
    return planes

if __name__ == "__main__":
    folder = sys.argv[1]
    flip = sys.argv[2] == "1"
    rot_k = int(sys.argv[3])
    step = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    cloud = fuse(folder, step=step, flip=flip, rot_k=rot_k)
    print("fused points:", len(cloud))
    planes = find_planes(cloud)

    print("\nPLANES (normal x, y, z | offset d | inliers)")
    for i, (n, d, c) in enumerate(planes):
        print(i, np.round(n, 3), round(d, 3), c)

    print("\nPARALLEL PAIRS (gap in metres)")
    for i in range(len(planes)):
        for j in range(i + 1, len(planes)):
            ni, di, _ = planes[i]
            nj, dj, _ = planes[j]
            dot = ni @ nj
            if abs(dot) > 0.97:
                gap = abs(di - np.sign(dot) * dj)
                print(f"plane {i} and plane {j}: gap = {gap:.3f} m")