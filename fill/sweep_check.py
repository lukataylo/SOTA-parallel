"""Score fill/sweep.py against the 2,132 brute-force patch tests in results/air/decisive.npz.

Prints the four pass-line numbers (fixed in docs/BETS.md, Bet 2), every disagreement, and, as evidence on the
"differentiate the tree" claim, the score of a pure one-sided derivative (critical depth linearised at +-0.1 mm and
extrapolated to +-5 cm) on the same pass line.

Definitions (fixed before looking at results)
  active patch          moves some receptor's critical depth by >= 1 mm, or flips it between finite and inf
  active pair           a (patch, receptor) with such a move in the brute-force result
  line 1 recall         brute-force active patches that the method also flags active / brute-force active patches
  line 2 false alarms   patches the method flags active that are not brute-force active / patches the method flags
  line 3 size           over brute-force active pairs: both shifts finite -> |pred - bf| <= 0.2 |bf|;
                        brute-force is a finite<->inf flip -> counts only if the method predicts the same flip
                        (and, if the new value is finite, within 1 mm of it); method says inf where brute force is
                        finite -> miss
  line 4 speed          brute-force seconds per patch / method seconds per patch, one process, measured now, both as
                        wall-clock and as process CPU time (the machine is shared); also against the quoted 1.3 s

Run: uv run --with numpy --with scipy --with numba python fill/sweep_check.py [--no-lin] [--nbrute 3]
"""
import sys, time, numpy as np
sys.path.insert(0, "fill")
from sweep import Sweep
from fillmodel import FillModel

NBRUTE = int(sys.argv[sys.argv.index("--nbrute") + 1]) if "--nbrute" in sys.argv else 3
DO_LIN = "--no-lin" not in sys.argv
D = np.load("results/air/decisive.npz"); c0, jobs, C, PG = D["c0"], D["jobs"], D["crit_patch"], D["PG"]
nj, nr = C.shape


def shifts(c0, C):
    """shift in mm (nan where either is inf), flip mask, active mask"""
    with np.errstate(invalid="ignore"):
        d = C - c0[None]
    flip = np.isfinite(c0)[None] ^ np.isfinite(C)
    d = np.where(np.isfinite(d), d, np.nan)
    return d, flip, (np.abs(np.nan_to_num(d)) >= 1.0) | flip


def score(name, c0p, Cp):
    d, flip, eff = shifts(c0, C); dp, flipp, effp = shifts(c0p, Cp)
    A, Ap = eff.any(1), effp.any(1)
    rec = (A & Ap).sum() / A.sum(); fa = (Ap & ~A).sum() / max(Ap.sum(), 1)
    both = eff & ~flip & np.isfinite(Cp) & np.isfinite(c0p)[None]
    ok = np.zeros_like(eff)
    ok[both] = np.abs(dp[both] - d[both]) <= 0.2 * np.abs(d[both]) + 1e-9
    fl = eff & flip
    same = fl & (np.isfinite(Cp) == np.isfinite(C)) & (np.isfinite(c0p) == np.isfinite(c0))[None]
    fin = same & np.isfinite(C)
    ok[same & ~fin] = True; ok[fin] = np.abs(Cp[fin] - C[fin]) <= 1.0
    size = ok[eff].sum() / eff.sum()
    print("%s" % name)
    print("  1. recall of active patches: %d of %d = %.1f%%   (pass line >= 90%%)  %s" % ((A & Ap).sum(), A.sum(), 100 * rec, "PASS" if rec >= 0.9 else "FAIL"))
    print("  2. flagged but not active:   %d of %d flagged = %.1f%%   (pass line <= 5%%)  %s" % ((Ap & ~A).sum(), Ap.sum(), 100 * fa, "PASS" if fa <= 0.05 else "FAIL"))
    print("  3. size within 20%%:          %d of %d active pairs = %.1f%%   (pass line >= 80%%)  %s   [%d of the pairs are finite<->inf flips, %d of those matched]" % (
        ok[eff].sum(), eff.sum(), 100 * size, "PASS" if size >= 0.8 else "FAIL", fl.sum(), ok[fl].sum()))
    return dict(recall=rec, false_alarm=fa, size=size, ok=ok, eff=eff, effp=effp, d=d, dp=dp)


# ---------------- the method ----------------
t = time.time(); S = Sweep.from_files(PG=PG); t_init = time.time() - t
print("Sweep init (numba compile or cache load + baseline): %.1f s; basins %d; baseline critical depths identical to c0: %s" % (t_init, S.nb, np.array_equal(S.c0, c0)))
Cp = np.empty((nj, nr)); nbp = np.empty(nj, np.int64); nwalk = np.empty(nj, np.int64)
t = time.time(); tc = time.process_time()
for i in range(nj):
    r, c, dz, rad = jobs[i]
    Cp[i] = S.patch(int(r), int(c), float(dz), int(rad)); nbp[i] = S.last_nb; nwalk[i] = S.last_nwalk
sw_wall = (time.time() - t) / nj; sw_cpu = (time.process_time() - tc) / nj
print("sweep: %d patches in %.1f s wall, %.1f s CPU, one process  (%.1f ms wall, %.1f ms CPU per patch; %.0f root-path walks per patch)" % (
    nj, sw_wall * nj, sw_cpu * nj, sw_wall * 1e3, sw_cpu * 1e3, nwalk.mean()))

# ---------------- brute force, re-measured now ----------------
z0 = S.z0; op = S.open; outlet = S.outlet; rc = S.rc
def brute(a):
    r, c, dz, rad = a; r, c, rad = int(r), int(c), int(rad); z = z0.copy(); sl = (slice(max(r - rad, 0), r + rad + 1), slice(max(c - rad, 0), c + rad + 1))
    z[sl] = np.where(op[sl], z[sl] + dz, z[sl])
    M = FillModel(z, op, outlet); LL, _ = M.run(PG); Dp = M.depth_at(LL, rc); wet = Dp >= 0.10
    return np.where(wet.any(0), PG[np.argmax(wet, 0)] * 1e3, np.inf)
pick = np.linspace(0, nj - 1, NBRUTE).astype(int)
t = time.time(); tc = time.process_time(); same = True
for i in pick: same &= np.array_equal(brute(jobs[i]), C[i])
bf_wall = (time.time() - t) / len(pick); bf_cpu = (time.process_time() - tc) / len(pick)
print("brute force now: %.2f s wall, %.2f s CPU per patch (%d patches, one process; reproduces decisive.npz: %s)" % (bf_wall, bf_cpu, len(pick), same))

print()
R = score("EXACT SWEEP (fill/sweep.py) vs brute force", S.c0, Cp)
sp_wall, sp_cpu, sp_q = bf_wall / sw_wall, bf_cpu / sw_cpu, 1.3 / sw_wall
ok4 = min(sp_wall, sp_cpu, sp_q) >= 50
print("  4. speed, one core:          %.0fx by wall-clock now, %.0fx by CPU time now, %.0fx against the quoted 1.3 s/patch; all 2,132 in %.1f s wall   (pass line >= 50x)  %s" % (
    sp_wall, sp_cpu, sp_q, sw_wall * nj, "PASS" if ok4 else "FAIL on at least one of the three ways of measuring"))
mis = np.argwhere(Cp != C)
print("  exact agreement: %d of %d (patch, receptor) critical depths identical to brute force; %d differ" % (nj * nr - len(mis), nj * nr, len(mis)))
for i, q in mis[:40]:
    print("    patch %d (r %d c %d dz %+.2f) receptor %d: brute %.1f mm, sweep %.1f mm, baseline %.1f mm" % (i, jobs[i, 0], jobs[i, 1], jobs[i, 2], q, C[i, q], Cp[i, q], c0[q]))

# ---------------- kink evidence from the brute-force table itself ----------------
d, flip, eff = R["d"], shifts(c0, C)[1], R["eff"]
up = jobs[:, 2] > 0; key = jobs[:, 0] * 10000 + jobs[:, 1]
iu = np.flatnonzero(up); idn = np.flatnonzero(~up); assert np.array_equal(key[iu], key[idn])
eu, ed = eff[iu], eff[idn]; anyp = eu | ed
du, dd = np.nan_to_num(d[iu]), np.nan_to_num(d[idn])
anti = anyp & eu & ed & ~flip[iu] & ~flip[idn] & (np.abs(du + dd) <= 0.2 * np.maximum(np.abs(du), np.abs(dd)) + 0.5)
print("\nKINKS in the brute-force table (a linear response would give raise = -lower):")
print("  (centre, receptor) pairs active in either direction: %d; active in one direction only: %d; active both ways and antisymmetric within 20%% + 0.5 mm: %d" % (
    anyp.sum(), (eu ^ ed).sum(), anti.sum()))
print("  patches that change the number of basins (pit created or removed): %d of %d; among brute-force active patches: %d of %d" % (
    (nbp != S.nb).sum(), nj, (nbp[eff.any(1)] != S.nb).sum(), eff.any(1).sum()))

# ---------------- pure one-sided derivative, scored on the same line ----------------
out = dict(c0=c0, c0_sweep=S.c0, jobs=jobs, crit_sweep=Cp, shift_sweep=Cp - np.where(np.isfinite(S.c0), S.c0, np.nan)[None], nb_patch=nbp, nb0=S.nb,
           sweep_wall_s_per_patch=sw_wall, sweep_cpu_s_per_patch=sw_cpu, brute_wall_s_per_patch=bf_wall, brute_cpu_s_per_patch=bf_cpu,
           speedup_wall=sp_wall, speedup_cpu=sp_cpu, speedup_vs_quoted_1p3s=sp_q, recall=R["recall"], false_alarm=R["false_alarm"], size_within_20pct=R["size"],
           n_mismatch=len(mis))
if DO_LIN:
    EPS = 1e-4; step = PG[1] - PG[0]
    p0 = S.pstar(S.z0)                                      # continuous baseline critical depth, m
    Cl = np.empty((nj, nr)); slope = np.empty((nj, nr))
    t = time.time()
    for i in range(nj):
        r, c, dz, rad = jobs[i]
        pe = S.patch(int(r), int(c), np.sign(dz) * EPS, int(rad), cont=True)
        with np.errstate(invalid="ignore"):
            sl = (pe - p0) / (np.sign(dz) * EPS)            # one-sided dP*/dz for this patch, m per m
            pl = p0 + sl * dz
        slope[i] = sl
        idx = np.ceil(pl / step - 1e-6)
        Cl[i] = np.where(np.isfinite(pl) & (idx <= len(PG) - 1), np.maximum(idx, 0) * step * 1e3, np.inf)
    t_lin = time.time() - t
    print()
    L = score("PURE ONE-SIDED DERIVATIVE (dP*/dz measured at %+.1f mm in the patch's own direction, extrapolated to 5 cm, put on the 0.5 mm grid)" % (EPS * 1e3), S.c0, Cl)
    print("  (this is what an exact adjoint would return; computed here by the exact evaluator at a tiny step, %.0f s)" % t_lin)
    eff, effl = L["eff"], L["effp"]
    miss = eff & ~L["ok"]
    zero = miss & (np.abs(np.nan_to_num(L["dp"])) < 1.0) & ~effl
    print("  why it misses, over %d brute-force active pairs not matched in size: derivative says < 1 mm (structure change needed to act): %d; derivative nonzero but wrong size: %d; of all misses, %d are in patches that create or remove a pit" % (
        miss.sum(), zero.sum(), (miss & ~zero).sum(), (miss & (nbp != S.nb)[:, None]).sum()))
    fa = effl & ~eff
    print("  false alarms: %d pairs where the derivative predicts >= 1 mm and brute force moves < 1 mm (the response saturates within 5 cm)" % fa.sum())
    out.update(crit_lin=Cl, slope_onesided=slope, lin_recall=L["recall"], lin_false_alarm=L["false_alarm"], lin_size_within_20pct=L["size"], lin_eps=EPS)
np.savez("results/air/sweep_check.npz", **out)
print("\nsaved results/air/sweep_check.npz")
