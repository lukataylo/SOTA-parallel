# App design: what to build

For the app agent on the MacBook Pro. This replaces the screen list in `docs/IPHONE_APP.md` task 3 and adds the splat, the server tier and the recommendations the human asked for. The kernel, bundle, golden test and scan-import tasks in that file stand. `docs/IPHONE_APP_REVIEW.md` has the reasoning.

**Look at it first:** open `docs/app_design/prototype.html` in a browser (or https://claude.ai/artifact/Hp51P47Qe2F1JWCo3qNzoB, private to the human). It is a working mock on real results. Build the app to match it. The human approved this direction on Saturday at 18:55: high design, very little copy, picture-led recommendations.

## Files here

| File | What it is |
|---|---|
| `prototype.html` | The clickable mock, self-contained |
| `prototype_template.html` | Its source: all layout, colours, type and drawing code, with `__DATA__` and `__IMGS__` placeholders |
| `prototype_data.json` | The data it runs on: a dark map image, 207 receptors with class, critical rain, range, depth curve, solver peaks, and up to three deciding patches each with the exact response at every centimetre from -20 to +20 |
| `gen_images.py` | Generates the four recommendation pictures with OpenAI's image model from a building's inputs |

## The look

One dark look only. No light mode.

| Token | Value | Used for |
|---|---|---|
| Asphalt | `#0e0f11` | Background |
| Tar | `#17191d` | Cards, panels |
| Seam | `#2a2d33` | Hairlines, slider track |
| Chalk | `#f2efe6` | Text |
| Dust | `#9a9da3` | Labels |
| Water | `#2f6bff` | Water, and anything computed on the phone |
| Paint | `#ff3d8b` | The deciding ground, and harm |
| Go | `#3ddc97` | Server-checked, and "no one worse" |

- **Type:** Big Shoulders Display 900 for numerals and one-line headings, in capitals. DM Mono 400/500 for small labels in capitals with wide tracking. Instrument Sans for the rare sentence. Bundle the fonts; do not fall back to the system face for numerals.
- **One huge numeral per screen** (190 pt on the Rain screen). Everything else is a label of two or three words.
- **Colour means source.** Blue chip: computed on the phone. Green chip: from the server. Outline chip: not yet known. Never show a number without one of these.
- **Motion:** water level and the door colour ease over about 0.25 s as the rain slider moves. Respect Reduce Motion.

## Screens

Four tabs: Rain, Ground, Scan, Fix. A "Next building" button in the top bar.

1. **Rain.** The building's critical rainfall as the numeral, with the range in a blue chip and the server's figure in a green chip. Below, a cross-section of the door. A slider sets rain from 0 to 120 mm; the water rises against the doorstep using the building's depth curve (`dc` in the data), and the door turns pink at 10 cm. The only words are "mm of rain in an hour" and "floods this door".
2. **Ground.** A zoomed map with the deciding patch in solid pink with corner ticks, a dashed pink line to the door, and the distance in metres. Pills switch between up to three patches. A slider raises or lowers the patch from -20 to +20 cm; the numeral updates, and any other building that floods sooner gets a red ring on the map and a pink "N neighbours worse" chip.
3. **Scan.** The Gaussian splat of the street, drawn on the device, with a pink target on the ground to scan and the distance to it as a large number. Three pictograms replace instructions: doorstep, kerb, back to start. Heights come from LiDAR depth, not from the splat.
4. **Fix.** Full-height picture cards that swipe sideways: Barrier, Rain garden, Tree pit, Street note. Each has a generated picture, one figure, one chip, and a "Limits" button that reveals one or two sentences. Nothing else.

## Where each number comes from

| Shown | Source | Chip |
|---|---|---|
| Critical rainfall and what-if answers | C kernel on the phone (`fill/sweep.py` port). Until it is wired in, use the precomputed curves in `prototype_data.json` | Blue |
| Range | 10th to 90th percentile over the 100-terrain ensemble (`results/air/bet1_cpu.npz`, rows 0 to 99) | Blue |
| Server critical rainfall, peak depths at 15, 35, 70 mm | `results/pro/critical_centred_60min.npz`, `results/air/p1_chunks/base.npz`. Precomputed for the video; a live endpoint on the MacBook Pro is a stretch | Green |
| Barrier card figure | Peak depth at the door at 35 mm from the server, or settled depth from the phone if there is no server value | Green or blue |
| Rain garden and tree pit figures | Storage only: 0.25 m3 per m2, and 3.9 m3 per tree at most. The effect on the building is not computed yet, so the chip reads "Effect pending" | Outline |
| Street note figure | Number of buildings that share the deciding patch | Pink, "For the council" |

23 buildings flood only from moving water. The phone model gives no answer for them. Show the server figure with a green chip and no blue chip; never show them as dry.

## Recommendation pictures

- `gen_images.py` builds one prompt per card from the building's inputs (water depth at the door sets the depth drawn against the barrier; distance to the deciding ground goes into the street-note picture) and one fixed style: a cut-away street diorama on a near-black background in the app's four colours, no text, no people.
- It needs `OPENAI_API_KEY` in `.env`. Run from the repository root: `uv run --with openai --with pillow python docs/app_design/gen_images.py .env docs/app_design/prototype_data.json docs/app_design/images.json`. The model name is tried as `gpt-image-1.5` then `gpt-image-1`; I have not been able to run it, so check the name against OpenAI's documentation if both fail.
- In the app, generate on a server and cache per building and card. Label nothing in the picture; the figure and chip carry the facts.
- **A generated picture is an illustration of the idea, not a design for the site.** The "Limits" text must say so on every card.

## Limits text (use these; keep them short)

- **Barrier:** Peak depth at the door in the full simulation. Water can still get in through air bricks, drains and shared walls.
- **Rain garden:** Lined storage on the flow path. The clay here does not soak water away in a short storm, so removing paving alone does little. The effect on this door is not computed yet.
- **Tree pit:** The storage under the tree does the work. A canopy holds 1 to 2 mm and is not counted.
- **Street note:** This ground is public. The app writes an evidence note and never tells you to alter it. Changes are shown only if no other building gets worse.

Banned everywhere: "safe", "will not flood", a probability for a home, insurance, any number without a chip.

## Build order

1. C kernel and golden test (as in `docs/IPHONE_APP.md` task 1).
2. Bundle, now also carrying the range, receptor class, depth curve and solver figures (the fields in `prototype_data.json`).
3. SwiftUI shell with the four screens above, on the precomputed curves first, matching the prototype.
4. Swap in the kernel for the Ground screen; on-device timing.
5. Splat on the Scan screen, with the water plane and pink target drawn in it.
6. Generated pictures on the Fix screen.
7. LiDAR scan import; live server endpoint; in-app capture. Stretch.

The video needs 1 to 4 and 6. Record at step 4 and again whenever a later step lands.
