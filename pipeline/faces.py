"""Cut small square face crops for every scatter subject that has a pol-face
roster headshot. Saves 96px JPGs to static/faces/ and a subject→file manifest.
The scatter clips them to circles in canvas at draw time.
"""
import json
import re
from pathlib import Path
from PIL import Image

WL = Path("/Users/wongpeiting/Desktop/CU/python-work/pol-face/watchlist")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "faces"
DATA = ROOT / "src" / "lib" / "data"

slugify = lambda n: re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def main():
    pts = json.load(open(DATA / "attention_points.json"))
    subjects = sorted({p["s"] for p in pts})
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    covered_pts = 0
    per_subj = {}
    for p in pts:
        per_subj[p["s"]] = per_subj.get(p["s"], 0) + 1
    for name in subjects:
        slug = slugify(name)
        src = WL / slug / "01.jpg"
        if not src.exists():
            continue
        im = Image.open(src).convert("RGB")
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((96, 96))
        im.save(OUT / f"{slug}.jpg", quality=82)
        manifest[name] = f"faces/{slug}.jpg"
        covered_pts += per_subj[name]
    json.dump(manifest, open(DATA / "faces_manifest.json", "w"), indent=0)
    print(f"{len(manifest)} faces → static/faces/ · cover {covered_pts}/{len(pts)} points ({covered_pts/len(pts)*100:.0f}%)")


if __name__ == "__main__":
    main()
