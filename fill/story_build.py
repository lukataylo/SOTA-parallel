"""Build the narrated presentation (docs/story.html) from the Blackfriars atlas page's model data and fill/story_template.html.
python3 fill/story_build.py <path to Blackfriars.html> ["text appended to the 75 m line"]"""
import sys, json, pathlib
s = pathlib.Path(sys.argv[1]).read_text(); a = s.index("const D={"); b = s.index("\nconst el=", a); c = s.index("const STORM={"); d = s.index(";\nconst nav=", c)
js = s[a:b] + "\n" + s[c:d] + ";"
out = pathlib.Path("fill/story_template.html").read_text().replace("__DATA_JS__", js).replace("__RAISED__", json.dumps(sys.argv[2] if len(sys.argv) > 2 else ""))
pathlib.Path("docs/story.html").write_text(out); print("%.1f MB" % (len(out) / 1e6))
