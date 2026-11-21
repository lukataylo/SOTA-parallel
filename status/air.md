# Status: MacBook Air M4 agent

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

Job 2: volume bound on the real tile, due 16:30.
