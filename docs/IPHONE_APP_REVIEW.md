# Review of `docs/IPHONE_APP.md`, and the changes the human asked for

Written by the Air agent on Saturday at 18:45. A clickable prototype driven by real results is at https://claude.ai/artifact/Hp51P47Qe2F1JWCo3qNzoB (private to the human unless shared). Its data came from `results/air/decisive.npz`, `bet5_curves.npz`, `bet1_cpu.npz`, `fill_curve.npz`, `p1_chunks/base.npz` and `results/pro/critical_centred_60min.npz`.

## What the human asked for (18:40)

1. A Gaussian splat made and shown locally on the iPhone.
2. A local model on the phone.
3. A larger model on a server.
4. Recommendations, with caveats, on paving removal, tree planting and elevations for protecting a building.

The draft covers 2. It leaves out 1, 3 and 4, and its word list forbids part of 4.

## The draft is sound on these points; keep them

- The C kernel with a golden test against all 441,324 known answers before anything touches the phone.
- One task at a time, each with a check.
- Heights from a LiDAR mesh, not from splat centres. The Southwark station splat has no clean ground plane.
- The video is the deliverable.

## Changes

### 1. Gaussian splat on the phone: add it for seeing, keep LiDAR for measuring

- **Role.** The splat is the picture the person looks around and taps on. Heights still come from ARKit's LiDAR depth or mesh, captured in the same session so both share one coordinate frame.
- **Smallest version that is honest:** render a splat file on the device with Metal. The draft's "no Metal" rule is about this Mac's GPU being busy with solver runs; it does not apply to the phone. In the simulator, keep the splat view behind a flag so builds do not compete with the solver.
- **Training on the device** in our own app by Sunday is the risky part. Fallback, stated on screen: capture and train in Scaniverse (which trains on the device), export, and render in our app.
- **To check before choosing a renderer:** whether an open-source Swift/Metal splat renderer reads the SPZ file we have, or needs PLY. I have not verified any library; do not assume.
- **Overlay.** Draw the settled-water plane and the deciding patches in the splat view. This is the shot for the video.
- **New check:** the splat renders at an interactive frame rate on the device, and a tap on the splat maps to the right cell of the 1 m tile within 2 m.

### 2. Local model: three corrections to the bundle

- **Ranges are missing.** The rule is no single number without a range, but the bundle has none. Add the 10th and 90th percentile of critical rain per receptor from the 100-terrain ensemble (`results/air/bet1_cpu.npz`, arm A, rows 0 to 99).
- **55 buildings are at risk in the solver; the fill model sees 32.** The other 23 flood from moving water. The app must show these as "the phone cannot assess this building" with the server's answer, not as dry. Class per receptor: fill model finite, solver finite only, neither.
- **Use the response curves for the what-if screen's first build.** `results/air/bet5_curves.npz` has the exact shift for 175 (location, building) pairs at every centimetre from -20 to +20. Screen 3 can run on these before the C kernel is wired in, then switch to live calls. The prototype does exactly this.
- **Timing.** The Python kernel now measures 6 ms per evaluation on a laptop core, so expect the phone well under the 200 ms kill line.
- **"Your house" is a receptor.** Receptors are fixed when the base state is built. A new address needs either a receptor at every building-edge cell or a kernel init on the device. For the video, pick the three buildings in advance.

### 3. Server model: add it as a third tier

- **What it is.** The 2D solver, which includes moving water. It is the only source for the 23 moving-water buildings and for checking a suggestion before the app shows it.
- **Where it runs this weekend.** The solver is MLX on Apple hardware, so "the server" is the MacBook Pro behind a small HTTP endpoint, not a cloud host. One request is a storm plus a list of changed cells; one answer is peak depth at the 207 receptors, about 20 s later.
- **For the video,** precomputed solver results are enough (three storms on unchanged terrain are in `results/air/p1_chunks/base.npz`; critical depths in `results/pro/critical_*.npz`). Label every such number "full simulation, precomputed". Add a live endpoint only after tasks 1 to 5.
- **New screen element:** each number carries one of two tags, "on this phone" or "server".

### 4. Recommendations: allow them, with these limits

The draft's word list bans any claim that trees or grass help. The human wants recommendations on paving removal and tree planting. Both hold if the app says what the evidence says:

| Recommendation | What the app may say | Tag | Caveats it must show |
|---|---|---|---|
| Raise a doorstep or fit a barrier | Settled depth at the door for three storms from the phone; peak depth from the server | Phone, server check | Water also enters by air bricks, drains and shared walls. Depths come from a model with no sewer detail |
| Remove paving | Only as lined storage: about 0.25 m3 per m2 of rain garden, about 0.1 m3 per m2 of deep-base permeable paving | Server, not yet validated | The ground here does not soak water away in a short storm. Storage helps only on the flow path. The effect on a building's critical rainfall is not computed yet (the absorption map is still running), so show no number |
| Plant trees | Canopy holds 1 to 2 mm and is not counted. An engineered tree pit with a kerb inlet stores up to about 3.9 m3 and is treated as a small tank | Not yet validated | Same as above |
| Change ground on the street | Never an instruction. An evidence note for the council: which square metres, how many buildings they affect, and a change that passed the do-no-harm check | Phone, server check | One harm-free design has been confirmed in the solver; that is a demonstration, not a rate |

- **Do-no-harm stays in every what-if:** any other building whose critical rainfall falls is shown in red and the suggestion is withheld.
- **Keep banned:** "safe", "will not flood", a probability for a home, insurance, and any single number without a range.

## Order of work, revised

1. C kernel and golden test (unchanged).
2. Bundle, with ranges, receptor classes and the response curves added.
3. Swift shell: map, building card, what-if, and a Protect screen with the four cards above.
4. On-device timing.
5. Splat render on the device with the water plane and patches drawn in it.
6. LiDAR scan import from a file.
7. Stretch: in-app capture, guided targets, live server endpoint.

Tasks 1 to 4 are still the minimum. Task 5 moves ahead of scan import because the human asked for the splat and it carries the video.
