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
# marker positions: the centre of the open cells of each 5 m block, moved clear of any drawn building outline
Dj = json.loads(s[a + 8:s.index(',"textures"', a)] + "}"); op = t["open"]
def inpoly(x, y, ring):
    c = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def covered(x, y): return any(inpoly(x + dx, y + dy, loops[0]) for h, loops in Dj["build"] for dx in (-1.8, 0, 1.8) for dy in (-1.8, 0, 1.8))
def place(x, y):
    r0, c0 = int(y) - 2, int(x) - 2; rr, cc = np.nonzero(op[r0:r0 + 5, c0:c0 + 5]); px, py = (c0 + cc.mean(), r0 + rr.mean()) if len(rr) else (x, y)
    if not covered(px, py): return [round(float(px), 1), round(float(py), 1)]
    best = None
    for R in np.arange(1, 9, 0.5):
        for a_ in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            qx, qy = px + R * np.cos(a_), py + R * np.sin(a_)
            if 0 <= qx < 512 and 0 <= qy < 512 and op[int(qy), int(qx)] and not covered(qx, qy): best = [round(float(qx), 1), round(float(qy), 1)]; break
        if best: break
    return best or [round(float(px), 1), round(float(py), 1)]
POS = {"moves": [place(m[0], m[1]) for m in Dj["moves"]], "design": [place(m[0], m[1]) for m in Dj["design"]], "kb": place(147, 302)}
print("markers moved:", sum(abs(p[0] - m[0]) + abs(p[1] - m[1]) > 1 for p, m in zip(POS["moves"] + POS["design"], Dj["moves"] + Dj["design"])), "of", len(Dj["moves"]) + 5, POS["design"], POS["kb"])
out = pathlib.Path("fill/story_template.html").read_text().replace("__DATA_JS__", js).replace("__PLACES__", json.dumps([[274, 268, "Southwark Underground station", "closed by a burst water main flood, Jan 2020"], [152, -41, "1–2 Paris Garden", "40 m beyond the model's north edge"]], ensure_ascii=False)).replace("__POS__", json.dumps(POS)).replace("__GREEN__", json.dumps(GREEN)).replace("__RAISED__", json.dumps(sys.argv[2] if len(sys.argv) > 2 else ""))
pathlib.Path("docs/story.html").write_text(out); print("%.1f MB" % (len(out) / 1e6), len(GREEN["trees"]), "trees", len(GREEN["drains"]), "drains", len(GREEN["fell"]), "fell")
