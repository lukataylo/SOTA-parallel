"""Where on the real street are the squares of the map-drawn design, and the strongest squares overall? Prints latitude, longitude and a map link.
uv run --with numpy --with pyproj python fill/where.py"""
import json, glob, numpy as np
from pyproj import Transformer
meta = json.load(open(glob.glob("data/*512*.json")[0])); b = meta["bounds_osgb"]; tf = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
def ll(r, c): lon, lat = tf.transform(b["left"] + c + 0.5, b["top"] - r - 0.5); return lat, lon
G = np.load("shared/map_design.npz"); rc = np.load("shared/receptors.npz")["rc"]
print("the five squares of the design taken from the map (section 3.5 of the README):")
for (k, i, j), q, s in zip(G["blocks"], G["target"], G["single"]):
    la, lo = ll(5 * i + 2, 5 * j + 2); lb, lob = ll(*rc[q]); print("  %s 5 cm at %.6f, %.6f  https://www.google.com/maps?q=%.6f,%.6f  -> building point %.6f, %.6f falls %.1f cm" % (("raise", "lower")[k], la, lo, la, lo, lb, lob, -100 * s[q]))
