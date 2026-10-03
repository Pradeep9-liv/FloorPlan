import sys, shutil
from pathlib import Path
import numpy as np
import cv2
import pycolmap

def extract(db, imgs, fx, cx, cy):
    ro = pycolmap.ImageReaderOptions()
    ro.camera_model = "PINHOLE"
    ro.camera_params = f"{fx},{fx},{cx},{cy}"
    kw = dict(camera_mode=pycolmap.CameraMode.SINGLE, reader_options=ro)
    try:
        eo = pycolmap.FeatureExtractionOptions()
        eo.num_threads = 4
        kw["extraction_options"] = eo
    except AttributeError:
        so = pycolmap.SiftExtractionOptions()
        so.num_threads = 4
        kw["sift_options"] = so
    pycolmap.extract_features(db, imgs, **kw)

def main():
    folder = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    name = "_".join(Path(folder).parts[-2:])
    src = Path("cache") / f"sharp_{name}"
    work = Path("cache") / f"sfm_{name}"
    imgs = work / "images"
    if work.exists():
        shutil.rmtree(work)
    imgs.mkdir(parents=True)

    K = np.loadtxt(Path(folder) / "camera_matrix.csv", delimiter=",")
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    fx, cx, cy = K[0, 0] * s, K[0, 2] * s, K[1, 2] * s
    print(f"intrinsics at half size: fx={fx:.1f} cx={cx:.1f} cy={cy:.1f}")

    files = sorted(src.glob("*.jpg"))[:n]
    for f in files:
        im = cv2.imread(str(f))
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(imgs / f.name), im)
    print(f"using {len(files)} frames: {files[0].name} to {files[-1].name}")

    db = work / "database.db"
    extract(db, imgs, fx, cx, cy)
    pycolmap.match_exhaustive(db)
    maps = pycolmap.incremental_mapping(db, imgs, work)

    print(f"\nreconstructions found: {len(maps)}")
    for i, m in maps.items():
        print(f"--- model {i}: {m.num_reg_images()} of {len(files)} images registered ---")
        print(m.summary())

if __name__ == "__main__":
    main()