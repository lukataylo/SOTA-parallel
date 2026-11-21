===== model=claude-mythos-5-2 stop=end_turn in=5782 out=24546 =====

## Corrections to your summary first

- **(6) breaks your own wording rule.** The percentages are not on the findings page. Use the mm figures, fill model only: 9.2 to 9.7 mm of critical rain for 5 cm of error at 1 to 3 m, 2.6 to 3.1 mm at 30 to 60 m. The one variogram you have (65 to 100 m) puts measurement error in the small-effect regime, which agrees with Abily. The claim is about unresolved kerbs and thresholds.
- **(7) is thinner than it reads.** It is one storm and one uniform change of n, and only 2 of the 30 patches were active. It shows nulls stay null under friction, little more.
- **(3) passes by half a millimetre.** The largest rise is 0.95 cm against a 1 cm line, on one design.
- **(5) is 200x only against 6 ms.** Under load it was 20 to 31 ms, which is 40 to 65x. The slide needs an idle, same-harness number.
- **(2):** "concentrated at the smallest storm" was seen after scoring, so it is a hypothesis.
- **A wording rule is stale.** "Direction and rank were confirmed" predates the control experiment, where sign missed its line (25 of 30) and rank was 0.51.

## 1. Five headlines, ranked

**1. "Which square metres flood your door?" (science)**
For each of 207 building edges we name the ground that sets its flood threshold, and a 2D solver moved for none of the ground we dismissed.
- Findings: 1, 2, 5.
- Number: 0 of 87 dismissed patches moved any receptor by 1 cm (95% upper bound about 3.4%); 22 of 33 flagged did.
- Hydrologist: one tile, buildings as walls, roof rain discarded; and it says which ground, not how much.
- Parallel judge: where is the parallelism?
- If Bet 1 is null: survives.

**2. "Every square metre, exactly, on every core" (parallel)**
One global recomputation per question becomes independent exact local repairs of a shared depression tree.
- Findings: 5.
- Carried now: only "an exact what-if, 200 times faster" (441,324 values identical; 6 ms against 1.3 s).
- Bolder version needs: the whole-tile sweep with a scaling curve, about 3 agent-hours and under an hour of compute (move 1).
- Hydrologist: exact with respect to a fill model that failed on size.
- Parallel judge: the speedup is algorithmic against your own rebuild, and independent tasks are embarrassingly parallel.
- If Bet 1 is null: survives.

**3. "The obvious fix floods the neighbours" (science)**
Five small changes chosen with harm in view helped all five targets and raised no receptor by 1 cm in the solver; the benefit-only set raised seven.
- Findings: 3.
- Number: 0 against 7, reproduced on two GPUs.
- Bolder version needs: "k of N designs", about 120 solver runs (move 2).
- Hydrologist: n = 1, a 0.95 cm margin, and two patches within 2 m of their receptor.
- Parallel judge: nothing parallel here.
- If Bet 1 is null: survives.

**4. "Ask what floods your door, in milliseconds" (phone)**
The exact what-if is fast enough to answer on a phone while you stand on the kerb.
- Findings: 5, 3.
- Number: 6 ms per what-if, on a laptop core. Nothing has run on a phone.
- Needs: the C port passing its golden test and timed on the device, 4 to 6 app-agent hours.
- Hydrologist: you put absolute mm in front of a householder from a model you say cannot give absolute mm.
- Parallel judge: an app is not a result.
- If Bet 1 is null: survives, if the "range" display is dropped.

**5. "Measure one per cent of the ground" (science)**
Knowing a chosen 1% of the ground cuts the spread in critical rainfall by 40% on unseen terrains; a random 1% cuts it by nothing.
- Findings: 4, 6.
- Number: 40% against 0%, fill model.
- Hydrologist: 40% sits exactly on the line and came from a second method. The 3 m correlation length is unsupported. The pilot interval (0.46 to 1.01) includes no effect.
- Parallel judge: no speedup claim.
- If Bet 1 is null: does not survive as a headline. It becomes a reported negative that fits the pattern (which ground, not how much).

Check that the Bet 1 scoring rule, including the contrast with the random arm, is written down before 21:30.

## 2. The headline I would use

**"Which square metres flood your door?"**

The three numbers on the first slide:
- **0 of 87**: dismissed patches that moved any receptor by 1 cm in the 2D solver.
- **6 ms, not 1.3 s**: the exact what-if, identical on 441,324 values. Replace this with the whole-tile time if move 1 lands.
- **0 against 7**: receptors raised 1 cm by our five changes and by the obvious five, with "one design" in small type until the replication is in.

The spoken opening:

"Flood maps say how much rain floods a building. They don't say which ground decides it. On half a kilometre of Southwark we can ask that of any patch of ground, exactly, in six milliseconds instead of 1.3 seconds. A full 2D solver agreed with every patch we dismissed: 87 tested, none moved the water a centimetre. And it matters: the obvious five fixes raised water at seven neighbours; ours raised it at none. What the fast model cannot do is say how much. We'll show you those failures."

## 3. Three moves, in order

**Move 1: the whole-tile exact sweep, with an honest scaling curve.** Air agent, now to about 23:00. This addresses two judging criteria you currently barely touch.

- Kill E0 now to free the Air's CPU.
- Run the control's 25 m² patch, at +5 and -5 cm, centred on every open cell. That is up to 524,000 what-ifs.
- Projected from 6 ms: about 52 core-minutes, so roughly ten minutes on eight cores. Rebuilding would take about eight days on one core.
- Start the full sweep now. Answers are identical under load, so its timing does not matter.
- Take the timing on the Pro in an idle window when Bet 1 finishes (about 21:30 to 22:15). The Air is fanless and will throttle.
- Timing protocol: 20,000 what-ifs at 1, 2, 4, performance-core and all-core counts, three repeats. Run the rebuild baseline in the same harness and language.
- Check 1,000 random what-ifs against brute force.
- Fallback if it is not running by 22:00: clean idle timing on the existing 2,132 patches.

The honest speedup statement has three parts:
- "N times per core from the algorithm, measured idle, with identical answers."
- "E% parallel efficiency on p cores; the whole tile takes T minutes on one laptop."
- "Rebuilding parallelises equally, so cores multiply both columns." Never multiply the two factors into one number.

The honest reshaping statement: questions no longer share state, so they fan out, and the GPU solver is spent only on the roughly 9% flagged. Say before the judge does that this is task parallelism unlocked by an exact algorithm. It is not a parallel hierarchy build.

The resulting map of how many buildings each square metre moves is your first-slide figure.

**Move 2: replicate do-no-harm overnight.** Pro agent; designs on the Pro's CPU before 22:15, GPU from then. This is my answer to (d): it is the first-slide number resting on n = 1.

- About 20 target sets, each with a harm-aware and a benefit-only design, at three storms. That is roughly 120 runs.
- Include a remote-only variant, with no patch within 5 m of the receptor it helps.
- Commit the lines tonight: a paired comparison of receptors raised 1 cm, and beneficiaries falling 1 cm.
- Report how many distinct patches the designs share. On this tile they will overlap.
- If it fails, the slide says "one design" and the failure is reported.
- The Air's GPU, after 21:30, runs the control harness on a fresh sample from the whole-tile map, about 300 dismissed and 100 flagged patches. That tightens 0 of 87 and validates move 1's product. If Bet 1's rate holds, both jobs fit overnight; that rate is my inference from its ETA.

**Move 3: Lowe, then the story.** Human, tonight for Lowe (1 to 2 hours); Sunday 09:30 to 13:00 for slides.

- Read Lowe 2021 for three things: an incremental update under terrain change, attribution to cells, and where to re-survey. If any is there, cite it and reposition as "applied and solver-tested".
- Keep the field test to one hour with the web mock. Its only job is photographs of the named square metres and the five design patches.

**(b) The app.** No criterion scores it. Use it for the last 30 seconds, on one screen: the ground what-if showing neighbours harmed, which is solver-backed. It hurts if it leads. Two of its screens show things you have decided not to claim: the critical-rainfall range and the rain slider at the door. Label them "fill model" or hide them.

**(c) The failures.** Give them one slide, as committed line against result:
- Flips: 9 of 20 (line 14) and 7 of 12 (line 9).
- Sign: 25 of 30 (line 26). Rank correlation: 0.51 (line 0.7). Slope: -0.12.
- Screen replacing the solver: 66% recall.
- First measurement method: 24% (line 40%).

The message: every test of how much failed, and the solver control of which ground passed under the same rules. That is why the claim is a screen. Mark the 15 mm explanation as post hoc.

**Stop:**
- Absorption, entirely. It gets one line under future work.
- The native shell, splat view, server tier and generated images. Synthetic pictures of fixes read as fabricated evidence to scientific judges.
- Other London tiles, the learned correction, and response-curve polishing.

The app agent does only the C port, the golden test and a device timing. The only other job allowed is the fill-model check of buildings as floodable footprints, on the Air's CPU after the sweep, for the assumptions slide.

## 4. Slides

| # | Message | Figure | Pending |
|---|---|---|---|
| 1 | Which square metres flood your door? | Whole-tile map and the three numbers | Sweep; fallback is the 2,132-patch map |
| 2 | Rain-to-flood is prior art; which ground decides it, we did not find | Blue Spot, SCALGO, Rav 2017, Lowe 2021 against ours | Lowe reading |
| 3 | A derivative fails here; an exact local repair does not | Kinked one-sided response curve; 65% recall, 29% false alarms | No |
| 4 | Exact, N times per core, whole tile in T minutes | Scaling curve; rebuild beside it | Move 1 |
| 5 | The solver ignores ground we dismiss | 22 / 11 / 0 / 87 table; solver checks in a footnote | Enlarged sample |
| 6 | What failed: it says which ground, not how much | Committed lines against results | No |
| 7 | The obvious fix floods the neighbours | Two maps, receptors up and down | Replication |
| 8 | Short-range structure decides; a chosen 1% helps | 40% against 0%; mm by length scale; solver arm | Bet 1 |
| 9 | Assumptions and limits | Table of departures from the Environment Agency method; friction result; one site | Buildings check |
| 10 | Who this is for | Phone what-if, 30 seconds | Device timing |

## 5. Odds

I cannot see the field, so these are rough. As it stands: top three about 35%, first about 10%. With move 1 landed and the replication holding: top three about 50%, first about 20%.

What moves it most is move 1, because a parallelism hackathon will not give first place to a single-core result. Next is the failures slide delivered plainly. Bet 1 moves it least.

What would cut it:
- a judge finding that the 1.3 s baseline is a weak rebuild;
- Lowe containing the attribution;
- the app taking the first minute.