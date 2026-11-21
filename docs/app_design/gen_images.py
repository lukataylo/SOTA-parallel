"""Generate the four recommendation visuals with OpenAI's image model, from the selected building's inputs.
uv run --with openai --with pillow python gen_images.py <env file> <appdata json> <out json>
Only generic street descriptions and model numbers are sent. No personal details."""
import sys, os, io, json, base64, pathlib
from openai import OpenAI
from PIL import Image
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    if line.startswith("OPENAI_API_KEY="): os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
client = OpenAI(); data = json.load(open(sys.argv[2])); out = pathlib.Path(sys.argv[3])
d = next(r for r in data["recs"] if r.get("site")); depth = (d.get("solpk") or d["depth"])[1]; dist = d["patches"][0]["dist"]
STYLE = ("Editorial cut-away diorama, like a museum specimen: one small slice of a London street lifted out and shown in section on a seamless near-black wet-asphalt background. "
         "Matte physical-model look, soft studio light from the upper left, crisp edges, no people, no cars, no text, no logos, no labels. "
         "Palette limited to asphalt black, chalk off-white, one saturated cobalt blue used only for water, and one fluorescent survey-paint pink used only for the highlighted intervention. Portrait composition, subject centred with generous margin.")
PROMPTS = {
    "barrier": f"A Victorian brick terrace doorway with a removable flood barrier fitted across the lower door opening, painted fluorescent pink. Cobalt blue floodwater about {depth:.0f} cm deep stands on the pavement outside and is held back by the barrier; the hallway floor behind it is dry. {STYLE}",
    "garden": f"A strip of paving slabs lifted from a London pavement and replaced by a sunken rain garden with grasses and reeds. The section shows a lined storage layer beneath the planting, half filled with cobalt blue water flowing in from a kerb inlet. The rain garden's edge is outlined in fluorescent pink. {STYLE}",
    "tree": f"A young street tree in an engineered tree pit. The section below the pavement shows four stacked storage cells around the roots, partly filled with cobalt blue water entering through a kerb inlet. The pit cover is outlined in fluorescent pink. The canopy is small and plain. {STYLE}",
    "kerb": f"A dropped kerb where the pavement dips to the road, with a 5 by 5 metre square of ground marked out in fluorescent pink survey spray paint and corner ticks, and a pink arrow painted on the tarmac pointing toward a doorway {dist} metres away. A thin sheet of cobalt blue water spills over the dropped kerb. {STYLE}",
}
imgs = json.loads(out.read_text()) if out.exists() else {}
for k, p in PROMPTS.items():
    if k in imgs: continue
    last = None
    for model in ("gpt-image-1.5", "gpt-image-1"):
        try:
            r = client.images.generate(model=model, prompt=p, size="1024x1536", quality="medium", n=1); break
        except Exception as e: last = e; r = None
    if r is None: print(k, "FAILED:", repr(last)[:300]); continue
    im = Image.open(io.BytesIO(base64.b64decode(r.data[0].b64_json))).convert("RGB").resize((640, 960), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=78, optimize=True); imgs[k] = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    out.write_text(json.dumps(imgs)); print(k, "ok with", model, len(b.getvalue()) // 1024, "KB", flush=True)
print("done:", list(imgs))
