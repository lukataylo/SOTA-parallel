"""Build the narrated presentation (docs/story.html) from the Blackfriars atlas page's model data and fill/story_template.html.
python3 fill/story_build.py <path to Blackfriars.html> ["text appended to the 75 m line"]"""
import sys, json, pathlib, numpy as np
sys.path.insert(0, "fill"); from inlets import inlets
t = np.load("shared/terrain_512.npz"); cells, _ = inlets(t["road"], t["z"], t["open"], 12.0); rc = np.load("shared/receptors.npz")["rc"]
g = np.load("results/air/green/s1.npz", allow_pickle=True); arm = [str(x) for x in g["arm"]]; pk = g["peak"].astype(float); ch = pk[arm.index("trees targeted")] - pk[0]
GREEN = {"trees": [[int(c), int(r)] for r, c in np.load("results/air/green/placement.npz")["trees_targeted"]], "drains": [[int(c), int(r)] for r, c in cells],
         "fell": [[int(rc[q][1]), int(rc[q][0]), round(float(-100 * ch[q]), 1)] for q in np.flatnonzero(ch <= -0.01)]}
s = pathlib.Path(sys.argv[1]).read_text(); a = s.index("const D={"); b = s.index("\nconst el=", a); c = s.index("const STORM={"); d = s.index(";\nconst nav=", c)
js = s[a:b] + "\n" + s[c:d] + ";"
out = pathlib.Path("fill/story_template.html").read_text().replace("__DATA_JS__", js).replace("__PLACES__", json.dumps([[274, 268, "Southwark Underground station", "closed by a burst water main flood, Jan 2020"], [152, -41, "1–2 Paris Garden", "40 m beyond the model's north edge"]], ensure_ascii=False)).replace("__GREEN__", json.dumps(GREEN)).replace("__RAISED__", json.dumps(sys.argv[2] if len(sys.argv) > 2 else ""))
pathlib.Path("docs/story.html").write_text(out); print("%.1f MB" % (len(out) / 1e6), len(GREEN["trees"]), "trees", len(GREEN["drains"]), "drains", len(GREEN["fell"]), "fell")
