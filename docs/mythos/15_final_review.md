# Mythos: final review before submission (Sunday 13:30)

**Top three fixes if you run out of time:** the burst-main sentence (step 4), the "eighth of the time" headline with its unrun baseline (steps 7, 9, 15), and the pass mark that failed but sits in an "ok" row (steps 10, 14).

## 1. Ten judge questions, hardest first

| # | Question | Answer to say |
|---|---|---|
| 1 | How do you know the model is right? | We don't. No rain flood is on record for this street, so this shows what the model reacts to, and it is not a forecast. |
| 2 | Did you run the 55-hour baseline? | No. It is 15,788 runs times the 13 seconds we measured; the 8x is a count of runs, 15,788 against 1,956, on the same solver and laptops. |
| 3 | 0 of 120 is a small sample. How many did you miss? | It only shows the miss rate is under about 2.5%, which still allows a few hundred among 15,690 dismissed tests. So 98 is what we found, not a proven total. |
| 4 | Why not an adjoint? | We didn't build one, so we can't be sure. Our 5 mm test scaled up found only 55% of the 5 cm effects, which suggests slopes miss water spilling over thresholds. |
| 5 | Batching gave nothing. Where is the parallelism? | In space: one simulation carries about nine independent experiments because their effects don't overlap. Tiles are also independent, so London's 6,000 can run on as many machines as exist. |
| 6 | Only 53 of 98 held at 70 mm. Is the map any use? | That failed our own pass mark. It means each storm needs its own map, which is why a map should cost 7 hours and not 55. |
| 7 | You count 1 cm moves but flooded means 10 cm. Does any change un-flood a building? | We measured change in peak depth, not crossings of the 10 cm line. (Give the count if you have it. If not, say so.) |
| 8 | Real London floods come from sewers. You have none. | Correct, and it is our biggest gap. With 303 rule-placed drains 79 of 98 findings held, but that is not sewers backing up. |
| 9 | Did you run anything after 11:00? | Yes: a tree test from another session, which we flagged. It is in no headline number; please ignore it. |
| 10 | Will 150 m work on another street? | Unknown. Here about 5% of effects travelled past 75 m along long ponds, so the re-run checks must be repeated on every site. |

If asked about noise: the five-square test matched the sum of the singles to 0.18 mm, far below the 1 cm threshold.

## 2. Copy fixes

| Step | Problem | Replacement |
|---|---|---|
| 4 | A burst pipe is not a rain flood, and the sentence reads as validation. | "This was a burst pipe, not rain, and we don't simulate pipes. We show it because the water gathered at the same low point where our 35 mm storm puts 17 cm. No rain flood is on record for this street, so the model has not been checked against a real one." |
| 4 | The council claim comes from a search summary, and the strategy places those floods in the south of the borough. This site is in the north. | Cut the council sentence. "We have no sewer data, so we cannot model sewers overflowing. Our tests take away a flat 12 mm…" (rest unchanged). |
| 7 | "As in a published study" reads as if the study measured 55 hours. | Label: "hours of graphics-chip time if every change gets its own run (our estimate: 15,788 × 13 s, not run)". |
| 9 | The baseline was not run, the saving is in runs, and "same map" was only checked by sample. | Headline: "The same 15,788 tests in an eighth of the runs". Add: "The 55 hours is an estimate. We did not run it." |
| 15, card 2 | Same misattribution. | "Done this way, our street would need about 55 hours (our estimate)." |
| 8 | 20 m is the median, so "mostly within 20 m" is wrong. | "Half the effects we found reach less than 20 metres." Add at the end: "About 5% of the time the nearest square was not the cause. We re-ran those." |
| 10, row 1 | It was not "every square", and the row hides a failed pass mark. | "We re-ran findings alone: 68 of 73 gave the same answer (93%). Repacked 300 m apart, 96 of 103 did. The rest were caused by a square further away, which we found." |
| 14 | The facts list five failures; the slide shows four. | Title: "Five things that didn't work". New row: "Crediting the nearest square was wrong 4.75% of the time. Our pass mark was 2%. Long ponds carry effects past 75 m, so we added a re-run step." |
| 14, row 3 | A 5 mm change is not a derivative. | "Scaling up a 5 mm change found only 55% (pass mark 90%). This suggests slope methods would miss many, but we did not build one." |
| 14, row 4 | The pass mark is missing. | Add "(pass mark 66)". |
| 10, row 4 | Marked ok, but half has no verdict, and the cause was a sleeping laptop. | "The lowered half finished: 34 of 34 known results showed up. The raised half stopped at 167 of 225 runs when a laptop went to sleep (38 of 38 so far), so it has no verdict." |
| 12 | "0 buildings with more water" is stronger than the facts. | Label: "0 rose by 1 cm or more". Title: "We tried a fix in the simulation". |
| 15, Blue Spot | It reads as if SCALGO's tool was tested, and 43% is not in your facts. | "Our own version found 77% here (pass mark 80%)." Keep 43 only if the README shows it. |
| 3 | You did test 70 mm, and 70 mm is far rarer than 20 mm. | "…twice the storm we mapped, and much rarer than 20 mm." Also "by the 2080s". |
| 2 | "Nobody knows" is an overclaim. | "…so they can't tell you which kerb to change." |
| 11, 12, 13, 16 | You measure 207 wall points, not buildings. | Unless you have checked that the points are on separate buildings, say "points on building walls". |

Two things I could not check: that arXiv 2311.00420 really runs one simulation per change, and that the 17 cm comes from a 1 m run and not the 4 m replay.

## 3. Five additions

| Criterion | Where | Sentence |
|---|---|---|
| 2 | Step 8, end | "This is the parallelism: about nine independent experiments share one simulation because their effects don't overlap." |
| 3 | Step 9, end | "Packing at 75 m would be roughly three times faster again. Half of that check passed and half didn't finish, so we don't claim it." |
| 1 | Step 10, row 2 | "That puts the miss rate under about 2.5%, not at zero." |
| 4 | Step 14, end | "The cheap shortcuts miss a quarter to a half of the ground that matters, and a map made for one storm is not safe for another." |
| Headline | Step 16, body | "At 7 hours a storm in place of 55, we could map several storm sizes for each neighbourhood and see which findings hold." |

## 4. Process risks

- **Tree run after cut-off:** Remove the tree rows and retitle step 13 "Drains are not fully tested yet". Keep the README note and tell an organiser before judging. The facts say 2 simulations but report three results (targeted, random, 70 mm), so check that count.
- **If the tree visual can't go:** change the body to "Not part of our entry. Run after the 11:00 stop by another session. Please ignore when scoring."
- **Edits after the 13:00 freeze:** I don't know your rule, so ask an organiser now. If it is binding, leave the slides, put a dated "Corrections" list at the top of the README and say the top three fixes aloud.
- **4 m replay:** Disclose once, on step 5: "The animation is a simplified 4 m replay for illustration. Every number comes from the 1 m runs."
- **Press photos:** Remove them, or credit each by outlet and photographer with a link. "Press" is not a credit.
- **Old dark deck:** Take it out of the submission or mark it "superseded". Stale numbers invite questions.
- **Cloud GPU check:** Leave it. It is already disclosed.

## 5. Closing line

"Flood maps tell you where the water ends up. With an eighth of the computing, we could ask which bit of ground sent it there. We did that for one street and one storm, in a model not yet checked against a real flood. With more scale, the question becomes whether those answers hold across storms and across London."