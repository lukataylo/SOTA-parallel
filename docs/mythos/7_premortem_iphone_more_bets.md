===== model=claude-mythos-5-2 stop=end_turn in=5738 out=30099 =====

Guesses are marked "(guess)" once, where they first appear. I don't have my earlier placing estimates in this thread, so the numbers in section 1 are fresh, not a delta.

## 1. Pre-mortem (Sunday 19:00, we did not place)

**Reason 1: the solver does not carry the headline.** The striking results (sparse control, the harm-free set, 1% of ground, Sweep) live in the fill model. That model has 66% recall against solver peak, over-predicts remote effects (slope 0.58), and failed the flip test twice. If P1 is ambiguous or unscored when slides are made, a judge says "you studied your own surrogate".
- Tonight: score P1 against the committed lines the moment it lands, before any other work.
- Put Bet 3's do-no-harm solver check first in the Pro queue.
- Word the headline at the level that passed: direction and rank, not flips.

**Reason 2: it reads as hydrology on a GPU, with novelty unverified.** Sweep is single-core, the speed figure carries a caveat, and Lowe 2021 is unread.
- Tonight: the builder reads Lowe's abstract, contents and the uncertainty chapter on the train (30 minutes).
- An agent produces a clean idle-machine timing and a core-scaling curve (Bet 4 below).

**Reason 3: too many threads, nothing finished.** Bet 1 sits exactly on its line (40% at 40%), absorption is inconclusive, and the app becomes a fourth front that eats the builder's hours.
- Tonight: freeze the one-sentence claim and slide skeleton at 18:30, after P1.
- Cap the builder's app time at three hours tonight.

**Estimates (guess; I don't know the field size or judging rubric):**

| | Top three | First |
|---|---|---|
| P1 passes | 35% | 12% |
| P1 fails | 15% | 4% |

Take a third off either row if Lowe covers attribution or where to re-survey.

## 2. The iPhone framing

### a. Real versus marketing

**Real and new:**
- Your own results say short-range relative error matters most (9 mm spread at 1 to 3 m correlation) and gentle tilts matter little. A phone is good at short-range relative height and has no absolute height. That match between instrument and sensitivity is the scientific content.
- Telling a person which few square metres to measure, and re-evaluating exactly on the device.

**Marketing:**
- "The rainfall that floods your home" as an absolute number. It is not validated against any flood, there are no drains beyond a uniform loss, and the model departs from the Environment Agency's.
- "Chance" of flooding. That needs rainfall frequency and a validated threshold.
- "Fix". The decisive ground is mostly public.

**The claim ARIA could fund, which could be wrong:** for most at-risk urban buildings, uncertainty in critical rainfall is dominated by relative heights of under about 30 m² of kerb and threshold that a 1 m airborne map cannot resolve; a handheld depth sensor, pointed where the model says, cuts that uncertainty by at least 40%, while the same area scanned at random does not.

It fails if any of these hold:
- Drains dominate.
- Scans cannot give 1 to 2 cm relative heights.
- The decisive cells are inaccessible.

### b. Demo by Sunday 13:00

**Is sub-second on the phone achievable?** Yes. Numba is already compiled code, so expect 20 to 50 ms per what-if on a recent iPhone performance core (guess until measured). Memory is a few megabytes.

**What to port:** the Sweep kernel in plain C through a bridging header.
- Not Swift: bounds checks and reference counting make a naive port slow.
- Not Metal: the union-find sweep is serial.
- C also lets you verify the port on the laptop against all 441,324 critical depths before it touches the phone.
- Kill line: over 200 ms on device means the port is wrong.

**Build order:**
1. C kernel plus golden test on the laptop.
2. Python bundle writer.
3. Swift shell calling the kernel in the simulator.
4. On-device timing.
5. Scan import from a file.
6. In-app ARKit capture.
7. Guided targets.
8. AR water-level overlay.

**Where things run:**

| On device | Bundled | Never on the phone |
|---|---|---|
| Sweep what-ifs | 1 m tile, building mask, receptors, base tree state | The 2D solver |
| Plane fitting and step heights | Leverage list per building with response per cm | |
| Scan placement | Precomputed solver maps for three storms, labelled as such | |
| | 32 ensemble base states (stretch) | |

**Minimum app, screen by screen:**
1. **Map.** The tile with buildings coloured by fill-model critical rainfall, labelled "settled-water model".
2. **Building card.** Critical rainfall as a range, the three patches that decide it with distances, and what the solver said where precomputed.
3. **What-if.** Tap a patch, slide ±10 cm, and the number updates live with milliseconds shown. Any neighbour whose critical rainfall falls turns red.
4. **Import a scan.** Measured heights replace map cells and the range updates.

**Stretch:** in-app scanner with guided targets, on-device ensemble for the range, and an AR plane at the settled water level.

**What a scan changes in the answer:**
- The building's own flood depth: measured threshold above pavement replaces the assumed 0.10 m.
- The heights of 10 to 30 listed cells: each takes the height of the surface covering most of it, so a kerb becomes a clean step.

**Agent split:**
- Agent A does science only and never touches the app.
- Agent B does the app.
- The shared interface is the C kernel, the bundle format and the golden test.
- The scan pipeline takes a point-cloud file, so it can be tested on the laptop.

**What to fake honestly if time runs out:**
- Scanner slips: import from an existing scanning app and say so on screen.
- Registration slips: the user drags the scan onto the map.
- Ensemble slips: show a precomputed range, labelled as such.
- App slips: compile the same C kernel to WebAssembly for a web page, plus a video of the scan.

### c. The measurement loop

**Registration, using relative heights only:**
- **No heights across scans.** Each scan is under about 10 m in one session and is tied to the map on its own.
- **Vertical.** Fit one offset per scan, as the median of map minus scan over flat open cells on both sides of the target. This is justified by your own finding: the offset absorbs tilts, which do not matter.
- **Step heights.** Fit a plane on each side of the step and difference them within about 0.5 m of the edge, so gravity-tilt error stays at millimetres. Do not use mesh points, because the mesh rounds edges.
- **Horizontal.** A wall plane gives heading and across-street position. A building corner or door jamb gives along-street position. GPS and compass only seed the guess, and the user confirms by dragging. One to two metres is enough for 5 m patches.
- **Your own threshold.** This needs no registration at all.
- **Worth a 15-minute check:** whether ARKit geo-tracking is available at the site (guess: London is covered).

**Each scan must contain:**
- The target feature.
- Two square metres of flat surface on each side of it.
- A wall base or corner.
- A return to the starting point. Rescan if the start point has moved more than 1 cm.

**Turn-by-turn instructions:**
1. Rank patches for the chosen building by expected narrowing of its range, from the ensemble.
2. Drop anything in the carriageway or under buildings.
3. Merge cells into nameable features.
4. Phrase each by distance and bearing from the door, for example: "Scan your threshold and 2 m of pavement. Then walk 14 m left to the dropped kerb and scan it from the pavement, including 1 m of road."
5. Show the expected gain for each.

**Stopping rule.** Stop when either holds:
- The same patch controls in 90% of ensemble members and the 80% range is under 5 mm. That is the fill-versus-solver agreement floor; claiming tighter is false precision.
- The next best scan is expected to narrow the range by under 10%.

### d. The fix

**What it can responsibly say:**
- **Barrier height.** Settled water level above the measured threshold at a stated rainfall, plus freeboard for moving water, with a cap. UK guidance discourages holding back more than about 0.6 m (guess on the exact figure). Always add that water also enters through air bricks, drains and party walls.
- **Storage volume.** Give it honestly: 1 mm of critical rainfall costs contributing area divided by 1,000 in cubic metres. For most houses that shows a water butt is negligible, which is useful to know. Storage is lined, on the flow path, and never described as infiltration.
- **Gullies.** Only "this is the low point that fills before your door; if there is a gully here, it is the one to report". Gullies are not modelled, so give no quantified effect.
- **Public ground.** Produce an evidence note for the council: which square metres, how many buildings they control, and the harm-free change in the model. Never give a DIY instruction for public ground.
- **Do-no-harm.** Every suggestion is checked against all 207 receptors and hidden if anyone's critical rainfall falls.

**What it must never say:**
- "Safe" or "will not flood".
- A probability or return period for a home.
- Anything for insurance or purchase decisions.
- "Raise this kerb".
- Anything about sewer, river, groundwater or burst-main flooding.
- A single number without a range.
- That trees or grass will help.

### e. Field experiment, Sunday 08:30 to 10:00

**Commit tonight (git hash):**
- Three buildings with accessible frontage.
- For each, the 80% range of critical rainfall, three chosen patches and three distance-matched control patches, with the response per cm at each.
- The leverage rank of the Boundary Row dropped kerb, reported whatever it is.

**Predictions:**
- **A, instrument.** Phone step heights are within 1 cm of a steel rule on 8 of 10 features, and repeat scans agree within 1 cm.
- **B, error model.** Map-minus-scan relative differences have a standard deviation of 3 to 8 cm at kerb and threshold cells, and are smaller on open pavement.
- **C, consequence.** With scans substituted, each building's critical rainfall lands inside its committed range, and chosen scans narrow the range by at least 40% on two of three buildings.

**Success:** A and B pass and C holds on two of three.

**Failure worth reporting:** the answer jumps outside the range. That means the unknown is missing features, not noise, which supports the "kerb-and-threshold structure" framing.

**Honest limits:**
- Three buildings, about 18 patches and 10 thresholds, one morning, one operator.
- Controls narrow little by construction, so C is partly internal to the model.
- No flood is observed. This tests the measurement loop, not flood prediction.

**Dry run tonight:** the builder scans any kerb and doorstep with a tape measure to hand. If the phone is off by more than 2 cm, the morning becomes rule-and-level with the phone as recorder.

### f. How it could embarrass us, and the one-sentence pre-emption

| Objection | Pre-emption |
|---|---|
| No drains | "Surface-only with a uniform 12 mm/h loss; the claim is which ground decides, not millimetres." |
| Absolute numbers | Show ranges and ranks, and the Environment Agency departures table. |
| The phone runs the fill model, which misses moving water | Label it "settled water"; cite solver agreement for direction and rank only. |
| A phone has no datum | "We use only step heights within one scan, tied to the map on flat ground, checked against a steel rule." |
| Abily 2016 | "We agree: kerbs and thresholds are omitted features, and the phone adds features, not noise reduction." |
| The site's flood record is a burst main | Say it before they do. |
| One 512 m tile with closed edges | State it, and show Bet 6 if it runs. |
| Blue Spot and SCALGO | Cite them on slide two; ours adds attribution, targeted measurement and exact what-ifs. |

## 3. Three more bets

### Bet 4 (parallel computing): every square metre, exactly

**Idea.** Batch Sweep across cores from one shared base state, and evaluate every cell of the tile, both directions, for all 207 receptors. That is about 524,000 what-ifs, roughly three core-hours, or under an hour on one laptop.

**Why new.** Parallel fill-spill-merge and parallel merge trees exist for one terrain. We did not find batched exact counterfactuals sharing one hierarchy.

**Go/no-go (90 minutes).** Run the 2,132 patches at 1, 2, 4 and 6 threads on an idle machine, with all 441,324 depths identical. Go at 4x or better on 6 threads; kill below 2.5x.

**Cost.** One agent-hour, then Air CPU overnight.

**Slide.** A scaling plot, and "9% of sampled patches" replaced by an exhaustive leverage atlas.

### Bet 5 (uses the kinks): response curves, not derivatives

**Idea.** For each active (patch, receptor) pair, compute the exact response from -20 to +20 cm and summarise it as dead band, one-sided slope and saturation. From these, build a tolerance map: the largest error each square metre can carry without moving any building by 1 mm.

**Why new.** Sensitivity here is normally done by derivatives or sampling. Persistence stability theorems bound spill levels but not volumes or rainfall. We did not find exact finite-change response functions for fill-spill-merge. It also explains why this morning's gradient scan map was unstable.

**Go/no-go.** 175 pairs at 41 heights is minutes of compute. Go if 80% fit within 0.5 mm with those three numbers; kill below 60%. As a free check, see whether the curves beat the linear slope on the 21 existing solver patches.

**Cost.** One agent-hour.

**Slide.** Three curves, and "x% of the ground can be wrong by 10 cm with no effect; y m² cannot be wrong by 2 cm". This is the scientific basis for the phone's scan list and stopping rule.

### Bet 6: does it hold on another street?

**Idea.** Run the unchanged fill pipeline on eight more London tiles, with the tile list committed before looking. Report the spread of the active-ground fraction, control distance and the 1% cut.

**Why new.** It replaces "one street" with a distribution. We did not find a city-scale statement of how little ground controls building thresholds.

**Go/no-go.** One new tile end to end with no hand edits in 90 minutes; kill if receptors need manual work. If the active fraction varies by more than a factor of five, report it as site-dependent.

**Cost.** Air CPU overnight, fill model only.

**Slide.** "Nine tiles", honestly labelled as fill model only.

## 4. The plan, 18:00 Saturday to 13:00 Sunday

**Decision: the iPhone is the closing slide and the recorded demo, not the headline.**
- Its evidence by Sunday will be three buildings and one morning.
- A consumer headline invites every objection in 2f.
- The event is about parallelism.
- If the demo breaks, the headline survives.

**Headline title:** "The few square metres that decide a flood".

**Claim, if P1 passes:** for each of 207 buildings we identify the few square metres that set its flooding rainfall, re-evaluate any change to them exactly in 20 ms, and a full 2D solver moves the predicted way when those cells change and not when others do.

**Closing line:** "Those square metres are what a phone can measure and a 1 m map cannot."

**If P1 fails:** drop "and not when others do" and lead with Sweep, the atlas and the response curves.

**Timeline:**

| When | Agent A (science) | Agent B (app) | Human |
|---|---|---|---|
| 18:00 to 18:30 | Score P1 | Start C port | Lowe verdict; freeze claim |
| 18:30 to 20:00 | Bet 4 go/no-go; clean timing | C kernel passes golden test; bundle writer | Pick three buildings and targets |
| 20:00 to 22:00 | Bet 5; start atlas | Swift shell, screens 1 to 3, on device | Dry-run scan with tape; commit predictions |
| 22:00 to 23:00 | Queue the Pro: do-no-harm, Bet 1 pilot, buildings, friction last | Scan import from file | Test on device, then sleep |
| Overnight | Pro GPU queue; Air on atlas and Bet 6; draft slides | In-app scanner, only if screens 1 to 3 ran on device by 22:00 | |
| 07:30 to 10:00 | Score overnight runs | Fix import against real scans | Field experiment |
| 10:00 to 13:00 | Final figures | Record demo video at 11:00 | Slides frozen 13:00; submit by 17:00 |

**Cut:**
- Absorption beyond one slide, unless E0 shows a clear go by 19:00.
- The learned correction.
- Metal.
- The AR overlay.
- Any baseline change.
- A live demo. Use the video.