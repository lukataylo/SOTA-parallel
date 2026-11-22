# Mythos: improving the shortcut model as a filter (Sunday 13:55)

Note added by the agent: section 5 assumes the full map takes 161 packed runs. It takes 1,800 (161 was the size of the unfinished 70 mm slice), so the run savings in that table do not apply.

**Bottom line:** you can get over 80% only with a rule chosen after seeing the answers, so the committed result stays "fail at 77%". The claimable finding is that the shortcut works as a ranker (3.8% of what-ifs hold 77% of movers), not as a filter.

## 1. Why it misses

- **Final versus peak.** The fill model computes where water rests; you score the highest water during the storm. Your own check shows this (85% against final, 66% against peak).
- **What it cannot see.** In the fill model a square matters only if it changes a lip or which dip the rain drains to. In the solver it also matters if it sits in moving water, where it can throttle, divert or back up flow without changing the resting state.
- **Not a threshold problem.** Misses match hits in size (1.6 against 1.7 cm) and distance (19 against 20 m), so lowering the 1 mm threshold is unlikely to help.
- **The 23 are mostly near-misses.** Five are the right square with the wrong sign, 10 are next door, 5 are two squares away and 3 are nowhere near a flag. Real overflow is a sheet several squares wide, while the model's spill path is one cell wide.
- **One place carries the failure.** Ten of the 23 are at the railway wall point. Away from it rule 2 finds 70 of 83 (84%). My guess is flat graded ground where a 5 cm change steers a shallow moving sheet.
- **Five-minute check:** compare baseline peak minus final depth at missed and found squares. If the misses sit in water that is deep at peak and gone at the end, the explanation holds.

## 2. Three changes, ranked

All three are already computed, so each takes minutes. The base rule earns about 20 recall points per flag point, for comparison.

| Rank | Change | Why it should help | Extra flags | Extra movers | Recall points per flag point |
|---|---|---|---|---|---|
| 1= | Ignore sign in rule 2 | Model finds the control but not the direction of a peak response | +256 (1.6%) | +5 | 3.1 |
| 1= | Rule 1 OR rule 2 | At peak the water state resembles a different rain volume | +413 (2.6%) | +8 | 3.1 |
| 3 | One-square neighbours | Sheet overflow is wider than one cell | +2,138 (13.5%) | +10 | 0.75 |

Two squares each way earns 0.37 and is not worth it. The combination "rule 1 OR sign-free rule 2" is not yet measured; compute it.

## 3. Evaluating it today

| Time | Step |
|---|---|
| 13:55 | Commit to git: the failed results as scored, the three candidates (sign-free rule 2; rule 1 OR rule 2; both), the split at column 256 by square centre, and the pass line. |
| 14:05 | On the west half only, pick the candidate with fewest flags that reaches 80%. If none does, stop and report the fail. |
| 14:15 | Score it once on the east half. |
| 14:20 | Re-run the fill model at 70 mm, apply the rule unchanged, and score once on the 59 finished packed runs. |
| 14:35 | Run the peak-minus-final check and write the slide. |

- **Pass line:** at least 80% of movers flagged, at most 10% of what-ifs flagged, and at most 1% wrongly dismissed. Fewer than 30 movers in the scored part counts as inconclusive. Also report recall without the railway point.
- **Why the flag cap:** the 1% mark is too lenient alone. The base rate is 98/15,788 = 0.62%, so dismissing everything would pass it.
- **The east half is not truly unseen.** You know the whole-tile totals, so it is a consistency check only.
- **The 70 mm partial map is the only clean test.** Use it only if your packed decode is already trusted.

## 4. What to say

- **If it passes:** "Our two pre-committed rules failed (43% and 77%); a rule chosen afterwards found X of Y movers on held-out data from the same tile while flagging Z%, which is a hypothesis for the next tile, not a validated filter."
- **If it does not:** "The shortcut failed our pass mark as a filter because it models resting water, not peak water; it does concentrate 77% of movers into 3.8% of what-ifs, so it ranks ground but cannot safely dismiss it."

Do not claim:
- 82% or 85% as results. The 82% is one mover over the line (80 against 79 needed), and sampling error on 98 clustered movers is about ±8 points.
- Predicted sizes, which failed three times.
- Anything beyond this tile and storm. Only 53 of 98 movers persist at 70 mm and 81 under doubled friction.

## 5. What it would buy

This assumes your 161-run packing covers all 15,788 what-ifs (about 98 per run) and that flagged squares pack as densely.

| Setup | What-ifs | Runs | Saved against 161 |
|---|---|---|---|
| Packing only | 15,788 | 161 | – |
| Plus rule 2 (3.8%) | 606 | 7 | 154 |
| Plus rule 1 OR rule 2 (6.5%) | 1,019 | 11 | 150 |
| Plus neighbours (19%) | 3,000 | 31 | 130 |

Flagged squares cluster, so real packing will be worse. Run your packer on the flagged set for the true count. Packing already takes 15,788 runs to 161. The filter saves at most about 150 runs per tile per storm, at the cost of 15–23% of movers.

## 6. First change afterwards

Give each dip a time axis. Use level-pool routing on the same tree, with weir outflow over each lip and the 40-minute rain as inflow, so the model gives a peak level that can stand above the lip. Test it first against the baseline peak fields at 15, 35 and 70 mm already on disk. It will not fix sheet flow on flat ground like the railway land.