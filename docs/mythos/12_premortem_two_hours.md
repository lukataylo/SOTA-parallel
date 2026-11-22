# Mythos: premortem, chances and the two-hour list (Sunday 05:00)

**Best move:** launch three jobs by 05:30, then stop experimenting. The agent fixes the deck while they run, and the humans rehearse from 07:00. The talk and slide errors are a bigger risk than any missing result.

## 1. Premortem

| # | Why we lost | The judge's sentence | Cheapest defuse |
|---|---|---|---|
| 1 | Talk too long, no single claim. The spoken text is roughly 1,100 words, about 8 minutes plus the demo. | "What exactly is your result?" | Cut to 7 slides with one claim on the first and last. Rehearse against a clock. |
| 2 | A slide number is shown to be wrong. On a correctness criterion this discounts everything else. | "Slide 6 says three days at 17 s; slide 8 says 55 hours. Which?" | The fixes in section 4, about 30 minutes of agent time. |
| 3 | Speedup read as small and not parallel. | "8x from batching your own runs on two laptops. Where is the parallelism?" | Item 2. Cite the one-simulation-per-cell study by name. Say the gain multiplies with GPU and machine count. |
| 4 | Hydrologist doubts the map is a property of the street. | "One storm, friction 0.015, no sewers. Same 84 squares at another storm?" | Item 1. |
| 5 | Negatives and novelty. | "You confirmed the hits. What about the 15,690 you dismissed? Have you read Lowe 2021?" | Items 2 and 3. A human reads Lowe's abstract and chapter list before 07:00. |

## 2. Chances

I do not know the field; assuming 15 to 20 teams, top three is about 25% and winning about 7%.

- **Top three moves most on:** whether the talk lands one claim in time with consistent numbers, and whether judges weigh pre-set lines and reported failures as heavily as speedup.
- **Winning moves most on:** whether item 2 passes, and whether another team has 100x on a recognised problem (out of our hands).
- **What winners usually have that we lack:** a speedup of an order of magnitude or more against an external baseline rather than their own code, a scaling plot on real parallel hardware, validation against something outside their own model, and a ten-second story.

## 3. The two-hour list

Write each line into `G_CRITERIA.md` before launch. Item 2 is a new experiment with its own line; no map number changes.

**1. Do the 98 movers persist? (Air, criterion 4)**
- **Run:** the 98 mover what-ifs, each alone, at 70 mm, then at 35 mm with friction 0.03, then at 15 mm. That is 297 runs with unchanged runs, about 75 minutes. Skip friction if it is not already a runner argument.
- **Line:** at least 66 of 98 move the same receptor 1 cm the same way, at 70 mm and at friction 0.03. The 15 mm count is reported without a line.
- **Pass:** "X of 98 still matter at double the rain and on rougher ground."
- **Fail:** "Which ground matters depends on the storm; the map is needed per storm."
- **Wording:** say "persist". This does not test for new movers.

**2. Dense re-map at 75 m (Pro, criteria 3 and 1)**
- **Run:** the lower sign, packed by block mod 15. That is 225 runs at 35 what-ifs per run, about 41 minutes; it should be a parameter change to `map_run.py`.
- **Line:** at least 95% of known lower-sign movers show their receptor move in the run that holds them. Zero new movers after tracing any move not explained by a known mover within 125 m.
- **Pass:** "Re-run at 35 per run: all known movers seen, none new. We report 8.1, the one fully confirmed." Also count the re-test runs it would need and give the all-in figure.
- **Fail:** "At 75 m packing loses X%. The reach of water sets the factor; 150 m is near the limit here."
- **Bonus:** it re-tests every lower what-if with different partners, which is the stronger check on negatives.

**3. Random dismissed squares, alone (Pro, after item 2, criterion 1)**
- **Run:** 240 what-ifs drawn with a fixed seed from the 15,690 dismissed, each run alone, about 44 minutes.
- **Line:** 0 of 240 move a receptor 1 cm.
- **Pass:** "0 of 240 dismissed squares moved a building when run alone."
- **Fail:** "The map misses about X%; the true count is nearer N."
- **Limit:** the 95% bound is 1.25%, about 196 what-ifs, so alone it cannot exclude misses as numerous as the finds. Lean on item 2 and the 0.02 mm agreement.

**4. A design drawn from the map (Air, after item 1, criterion 4)**
- **Run:** pick up to five mover what-ifs that lower a building, with no saved receptor rise above 0.3 cm. Run the combined terrain once.
- **Line:** every target falls 1 cm, no receptor rises 1 cm, and the change is within 5 mm of the sum of the single effects.
- **Pass:** "A second design, taken only from the map, did what the map said."
- **Fail:** "Single effects do not add up; every design needs its own run."
- **Stop rule:** drop it if not launched by 06:30.

**Rejected candidates:**
- **Scaling across two machines:** trivial; give wall-clock from the logs in one sentence.
- **Colouring bound:** theory, no evidence.
- **Grid convergence (e):** needs a resampled terrain; too risky.
- **App work (f):** do not touch it.

**Free, from saved peaks, 10 minutes:** count how many of the 98 take a receptor across 0.10 m. Slides 5 and 9 need it.

## 4. The deck

**Seven slides:**
1. Cover with the claim (fold slide 2 into one spoken sentence).
2. How a street floods.
3. Move the ground, 15,788 what-ifs (old 4, 5, 6).
4. Packing and speed (old 7, 8).
5. The map, then the demo here, 20 seconds.
6. The fix (survey result becomes one spoken line and a backup slide).
7. What failed and what London needs (old 12, 13).

**Claim, first and last slide:** "We tested every 5 m square of half a kilometre of London in a full flood solver: 15,788 what-ifs in 1,956 runs. One square in a hundred changes a building's peak water, typically 20 m from the door."

**Wrong or overclaimed:**
- **Slide 6 against 8:** 17 s and "three days" contradict 55 hours. 6.3 GPU-hours over 1,800 runs is 12.6 s per run. Say "55 GPU-hours became 7, checks included".
- **Slide 7, "9 tests":** your own rule says 8.8.
- **Slide 7, "0.2 mm" and "20 of 20":** these come from the 120 m pilot. Use the map's figures: 274 of 276, median difference 0.02 mm.
- **Slide 7, "almost never beyond 75 m":** 18 of 379 moves did, up to 124 m, and that line failed. Say "about 1 in 20".
- **Slide 7, picture:** "an illustration, not our data" is weak; use a real packed run.
- **Slide 8, "identical answers":** true only of the 13x quick estimate. In the packed map, 93% of movers kept their verdict.
- **Slide 8, withdrawn 200x:** take it off the slide; keep it for questions.
- **Slide 9, "re-ran every one on its own":** false. 73 ran alone; the rest were repacked 300 m apart.
- **Slides 5 and 9, "door stays dry" and "change a building's flood":** flips were never confirmed. Say "peak water by 1 cm" unless the flip count supports more.
- **Slide 10, "seven other buildings":** the finding is 7 receptors. "Harm no one" rests on 0.95 cm against a 1 cm line; say so.
- **Slide 11, "forecast uncertainty":** it is spread under synthetic error whose 3 m correlation your own page calls unsupported. "A phone can" was never tested.
- **Slide 13 against 12:** slide 12 says the quick estimate failed as a filter; slide 13 uses it as one. Give the honest cost instead: about 8.5 GPU-hours per tile per storm.
- **Slide 13, "do not talk beyond a margin":** the plan still says 75 m; measured reach is 124 m. That is the reach of a 5 cm change, not of the flood itself.

## 5. Hardest questions

**"Is 8x a parallel speedup, and against what?"**
Same solver, GPU and grid, one what-if per run: 55 GPU-hours against 7 with every check counted. The gain comes from running independent experiments in one domain, because a change reaches a median 20 m; it is the 1974 colouring idea, and it multiplies with GPU and machine count.

**"No sewers, one storm, no observed flood. Why believe the 84 squares?"**
We claim which ground a 2D solver is sensitive to, not depths in mm; [item 1 result] of 98 persist at 70 mm and at rougher friction. Absolute thresholds need sewer data and July 2021 door records, which we do not have.

**"What is new against Blue Spot, SCALGO and merge trees?"**
Those give the rain that floods a point from a fill model; ours found only 43 to 77% of the ground the solver says matters and could not size it. What we add is the solver-tested map of causes and the packing that makes it affordable; we did not find either in a limited search.