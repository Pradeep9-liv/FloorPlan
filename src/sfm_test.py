import sys, shutil
from pathlib import Path
import pycolmap

def main():
    folder = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    name = "_".join(Path(folder).parts[-2:])
    src = Path("cache") / f"sharp_{name}"
    work = Path("cache") / f"sfm_{name}"
    imgs = work / "images"
    if work.exists():
        shutil.rmtree(work)
    imgs.mkdir(parents=True)

    files = sorted(src.glob("*.jpg"))[:n]
    for f in files:
        shutil.copy(f, imgs)
    print(f"using {len(files)} frames: {files[0].name} to {files[-1].name}")

    db = work / "database.db"
    pycolmap.extract_features(db, imgs)
    pycolmap.match_sequential(db)
    maps = pycolmap.incremental_mapping(db, imgs, work)

    print(f"\nreconstructions found: {len(maps)}")
    for i, m in maps.items():
        print(f"--- model {i} ---")
        print(m.summary())

if __name__ == "__main__":
    main()