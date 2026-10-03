import sys, os, glob, shutil
import numpy as np
import cv2

folder = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
end = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9

name = "_".join(os.path.normpath(folder).split(os.sep)[-2:])
src = os.path.join("cache", f"frames_{name}")
dst = os.path.join("cache", f"sharp_{name}")
os.makedirs(dst, exist_ok=True)
for f in glob.glob(os.path.join(dst, "*.jpg")):
    os.remove(f)

files = sorted(glob.glob(os.path.join(src, "*.jpg")))
files = [f for f in files if start <= int(os.path.basename(f)[:-4]) <= end]
scores = []
for f in files:
    g = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (640, 480))
    scores.append(cv2.Laplacian(g, cv2.CV_64F).var())
scores = np.array(scores)
cut = np.percentile(scores, 25)
print(f"frames in range: {len(files)}")
print(f"sharpness  min {scores.min():.1f}  median {np.median(scores):.1f}  max {scores.max():.1f}")
keep = [f for f, s in zip(files, scores) if s >= cut]
for f in keep:
    shutil.copy(f, dst)
print(f"kept {len(keep)} frames (dropped the blurriest quarter) -> {dst}")

def upright(path, out):
    im = cv2.rotate(cv2.imread(path), cv2.ROTATE_90_CLOCKWISE)
    cv2.imwrite(out, im)

upright(files[int(np.argmax(scores))], "preview_sharpest.jpg")
upright(files[int(np.argmin(scores))], "preview_blurriest.jpg")
print("saved preview_sharpest.jpg and preview_blurriest.jpg (upright)")