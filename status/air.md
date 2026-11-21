# Status: MacBook Air M4 agent

## Sat 13:50 — PLAN-CHANGING FINDING: the fill step decides almost no whole storms when all 207 receptors must be decided

Read this before continuing either brief. The numbers come from the fill model alone; the band is not yet measured against the solver, so they are a forecast, and an optimistic one.

| Band around the 0.10 m threshold | Storm-receptor pairs undecided | Whole storms decided, all 207 receptors | 50 receptors | 10 receptors | 1 receptor |
|---|---|---|---|---|---|
| +-1 cm | 1.7% | 4% | 41% | 85% | 98% |
| +-2 cm | 2.9% | 1% | 21% | 75% | 96% |
| +-5 cm | 8.2% | 0% | 1% | 42% | 94% |

(1,000 main storms; subsets are random draws of receptors; `fill/skip_curve.py`.)

**What it means.** The fill step decides more than 90% of individual storm-receptor cases, but the solver simulates the whole domain, so a storm is skipped only when every receptor is decided. On this flat terrain a few receptors sit in wide shallow ponds whose level creeps up slowly with rain, so some receptor is near the threshold in almost every storm. With 207 receptors the end-to-end speedup from skipping storms would be about 1x.

**What still works.** For a question about one asset, or a handful, the fill step decides most storms: 72 to 97% for the documented site alone, depending on the band.

**Untested assumption inside these numbers.** 127 receptors never see any water in the fill model, and are counted as decided dry. Water flowing past them on a slope is exactly what the fill model cannot see. Only the solver can say whether that holds.

**Decision needed from the human** (options are in the chat): keep the 207-receptor map and report the negative result, narrow the question to a few critical assets, or change how the two steps are combined.

## Sat 14:00 — Notes for the Pro agent, and a second forecast

- **Storm files now also carry `profile_dt_s`** (same value as `profile_step_s`, 60 s), as you asked. Nothing else changed.
- **Roof rain:** dropped in the fill model too. Rain falls on `open` cells only. We match.
- **Drainage loss:** I also subtract it from the rain rate, floored at zero, and never drain ponded water. We match.
- **The deep pits** are on open ground in the patches listed by the command in `fill/` history (rows about 190 to 230 east of Blackfriars Road, and others in the south-west). I have not filled them: I cannot tell sunken courtyards from leftovers of building removal, and changing terrain to make the solver faster needs a reason I can defend. Ask a mentor; if they are artefacts we both fill them and re-run.
- **The shared files exist, so the pilot can run now.** The pilot matters more than before: it is the only way to measure the band and to test the 127 receptors the fill model calls always dry.

**Second forecast: running the solver only around undecided receptors does not rescue the map.** In the fill model, the smallest closed unit around an undecided receptor is a median 9 to 12% of the open ground, but one large connected unit covers about 76%, and some undecided receptor falls in it in most storms. Cells to simulate per storm: 64% of the domain with a +-2 cm band (1.6x saving), 86% with +-5 cm (1.2x). `fill/local_forecast.py`.

## Sat 13:48 — Job 2 done: volume bound on the real tile

`fill/job2_bound.py`, results in `results/air/volume_bound.npz`.

- The bound here uses rain over the whole open domain, which is an upper limit on any upstream catchment, and gives no credit for outflow or drains.
- **It splits the receptors in two.** 114 of 207 have a bound above 120 mm, so the bound calls them dry in every storm. 33 have a bound under 2 mm, so it decides nothing for them. The median is 170 mm.
- **It decides 59% of storm-receptor pairs and 0% of whole storms.**
- No pair the fill model calls wet was called dry by the bound (0 conflicts), as expected since both rest on still water.
- For 172 receptors the below-threshold region reaches the domain edge, where water would leave. The bound ignores that, which keeps it conservative for still water but says nothing about water in motion.

Not yet checked against the solver. Until it is, this is a screen with an unmeasured miss rate.

## Sat 13:42 — Job 3 done: batched partial fill built; oracle gate passed on cells, narrowly missed on doors

`fill/fillmodel.py` (model), `fill/check_real.py`, `fill/check_oracle.py`.

- **Real tile:** 9,811 basins. Terrain work takes 0.2 s once. All 1,000 main storms take 0.5 s on one CPU core. Water balance closes to 1 part in 10 million. Receptor depth never falls as rain increases.
- **Oracle:** settled JAX solver on 12 synthetic streets, 7 rain depths, no gullies, 30 minutes of settling.
  - Cell decisions (depth at least 5 cm): 99.1% agree over 181,440 cases. **Passes the 98% line.**
  - Door decisions (interior wet): 97.8% agree over 672 cases, 15 mismatches. **Just under the 98% line.**
  - Direction: 1,641 cells wet in the solver and dry in the fill model, against 18 the other way. Where either is wet, the solver sits a median 0.2 cm above the fill level (99th percentile 1.2 cm), because it is still draining.
- **My reading:** the water levels agree to millimetres, so the implementation is right. The door mismatches are in the heaviest storms, where water overtops a threshold during the peak and stays inside. That is moving water riding above the still level, the known mechanism, and it is a miss direction. I continued with the fill model. I did not adjust anything after seeing this.
- **Fill tier on the main set:** 11.5% of storm-receptor pairs are wet. 30 of 207 receptors ever reach the threshold. The documented site first reaches it at about 33 mm of net rain.
- The speed comparison against a plain single-threaded version is not done; at 0.5 s for 1,000 storms it will not change the entry.

## Sat 13:45 — Job 1 done: shared inputs are committed

The Pro agent can switch to these now. Built by `fill/make_shared.py`; picture in `shared/shared_preview.png`.

| File | Contents |
|---|---|
| `shared/terrain_512.npz` | `z` (ground height with building cells raised 20 m), `open` (cells that take rain and hold water), `dx` = 1 m. Extras: `dtm`, `road`, `blackfriars_road`. |
| `shared/receptors.npz` | `rc` (207 x 2, row then column), `threshold_m` = 0.10, `label` |
| `shared/storms_pilot.npz` | 64 storms, seed 101 |
| `shared/storms_main.npz` | 1,000 storms, seed 202 |

Storm arrays: `depth_mm`, `duration_s`, `profile` (storms x 60 rain rates in mm/h at `profile_step_s` = 60 s, zero after the storm ends), `loss_mm_h`, `kind` (0 front-loaded, 1 centred, 2 back-loaded), `net_depth_mm`.

**How the solver should apply rain:** on `open` cells only, at rate `max(profile - loss_mm_h, 0)`. Run for `duration_s` plus 20 minutes.

### Measured

- 65.3% of the domain is open ground. 99.3% of open ground is one connected region; 1,237 cells sit in 35 small enclosed courtyards.
- 207 receptors: 193 on building edges within 12 m of a street centreline and at least 22 m apart, 13 mapped entrances, 1 documented site.
- Documented site is cell (246, 290), ground 3.30 m. Blackfriars Road within 150 m of the station ranges from 3.12 to 3.91 m, so the road is nearly flat.
- Net rain after the drainage loss ranges from 2 to 108 mm across the main set. No storm has zero net rain.

### Assumptions (all unconfirmed; ask a mentor)

- **Buildings are walls.** Roof rain is assumed to go to the sewers and is not added to the ground. This lowers flooding compared with spilling roofs onto streets.
- **Drainage loss is a constant 12 mm/h** taken off the rain rate. Recalled from memory as a common UK urban allowance; not checked.
- **Storms are triangular in time**, with the peak at 15%, 50% or 85% of the duration. Depth 10 to 120 mm, one storm per depth stratum. Duration 15 to 60 minutes, but never shorter than depth/2 minutes, which caps mean intensity at 120 mm/h and the peak at 240 mm/h. The upper end is beyond anything I can vouch for as a real London storm.
- **Flooded means 0.10 m of water at the receptor cell** at any time.
- **Documented site** is the Blackfriars Road centreline cell with the lowest 9 m average carriageway height within 150 m of Southwark station. A first attempt picked a 2 m pit beside the road; that was discarded as a data artefact.

### Oddities in the terrain

- Several rectangular pits up to 2 m deep remain in open ground east of Blackfriars Road (rows 190 to 230). They may be real sunken courtyards or leftovers from building removal. They will store water in both the fill model and the solver. Not corrected.

## Next

Waiting on the human decision above. Meanwhile: an independent small solver run on this machine to measure the band early, and the two literature checks.
