"""Build the one-minute film pages (docs/film.html, and docs/film-type.html whose first three beats are type only) from the built presentation (docs/story.html) and fill/video_template.html.
The street model, its data and its drawing code are taken from the presentation unchanged; only the timeline and the type are new.
python3 fill/video_build.py"""
import pathlib, re
s = pathlib.Path("docs/story.html").read_text()
a = s.index("'use strict';"); b = s.index("// ---- sketch of the kerb ----"); eng = s[a:b]
kb = re.search(r"const d0 = .*?\n", s).group(0); f = s.index("function faceAngle"); g = s.index("// ---- playing a scene ----")
tpl = pathlib.Path("fill/video_template.html").read_text().replace("__ENGINE__", eng + kb + s[f:g])
for name, intro in (("film", "false"), ("film-type", "true")): pathlib.Path("docs/%s.html" % name).write_text(tpl.replace("__INTRO__", intro))
print("%.1f MB each" % (len(tpl) / 1e6))
