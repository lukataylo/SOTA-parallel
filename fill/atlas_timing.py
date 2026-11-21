"""Clean timing for the exact what-if, to be run on an IDLE machine (nothing else on CPU or GPU).
One harness and one language for both methods:
  A  exact local repair (fill/sweep.py), 20,000 random what-ifs, at 1, 2, 4, performance-core and all-core process counts, 3 repeats each
  B  rebuilding from scratch for each what-if in the same compiled code (Sweep constructed on the changed terrain), 40 what-ifs on one process, 3 repeats
  C  200 of the what-ifs checked for identical answers between A and B
  uv run --with numpy --with scipy --with numba python fill/atlas_timing.py
Writes results/pro/atlas_timing.json. Report per-core speed-up (B / A at one process) and parallel efficiency separately; do not multiply them."""
import sys, os, time, json, subprocess, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill")
T = np.load("shared/terrain_512.npz"); Z, OP = T["z"].astype(np.float64), T["open"]; RC = np.load("shared/receptors.npz")["rc"]
rng = np.random.default_rng(2026); cells = np.argwhere(OP); pick = cells[rng.choice(len(cells), 20000, replace=False)]
JOBS = [(int(r), int(c), float(dz)) for (r, c), dz in zip(pick, rng.choice([0.05, -0.05], len(pick)))]
_S = None
def init():
    global _S
    from sweep import Sweep
    _S = Sweep.from_files(); _S.patch(*JOBS[0], 2)                      # compile and warm up before timing
def run_chunk(jobs): return [_S.patch(r, c, dz, 2) for r, c, dz in jobs]
def rebuild(job):
    """Full rebuild in the SAME compiled code as the repair: construct Sweep from scratch on the changed terrain."""
    from sweep import Sweep
    r, c, dz = job; z = Z.copy(); sl = (slice(max(r - 2, 0), r + 3), slice(max(c - 2, 0), c + 3)); z[sl] = np.where(OP[sl], z[sl] + dz, z[sl])
    return Sweep(z, OP, RC).c0
if __name__ == "__main__":
    def sysctl(k):
        try: return int(subprocess.check_output(["sysctl", "-n", k]).strip())
        except Exception: return None
    pcores = sysctl("hw.perflevel0.physicalcpu") or 4; allc = os.cpu_count()
    out = dict(machine=subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip(), pcores=pcores, cores=allc, n_what_ifs=len(JOBS), sweep={}, load_before=os.getloadavg())
    for W in sorted({1, 2, 4, pcores, allc}):
        times = []
        with mp.Pool(W, initializer=init) as p:
            chunks = [JOBS[i::W * 8] for i in range(W * 8)]
            p.map(run_chunk, chunks[:W])                               # make sure every worker is warm
            for rep in range(3):
                t0 = time.perf_counter(); res = p.map(run_chunk, chunks); times.append(time.perf_counter() - t0)
        out["sweep"][W] = dict(wall_s=times, best_s=min(times), ms_per_what_if=1e3 * min(times) / len(JOBS)); print("sweep, %d processes: %s s; best %.2f ms per what-if" % (W, np.round(times, 1), 1e3 * min(times) / len(JOBS)), flush=True)
    t1 = out["sweep"][1]["best_s"]
    for W, v in out["sweep"].items(): v["speedup_vs_1"] = t1 / v["best_s"]; v["efficiency"] = t1 / v["best_s"] / W
    rb = []; ans = None
    for rep in range(3):
        t0 = time.perf_counter(); ans = [rebuild(j) for j in JOBS[:40]]; rb.append((time.perf_counter() - t0) / 40)
    out["rebuild_s_per_what_if"] = rb; out["per_core_speedup"] = min(rb) / (t1 / len(JOBS)); print("rebuild: %s s per what-if; per-core speed-up %.0fx" % (np.round(rb, 3), out["per_core_speedup"]), flush=True)
    init(); bad = 0; chk = JOBS[:40] + JOBS[1000:1160]
    for k, j in enumerate(chk):
        a = _S.patch(*j, 2); b = ans[k] if k < 40 else rebuild(j)
        bad += int(not np.array_equal(np.where(np.isfinite(a), a, -1), np.where(np.isfinite(b), b, -1)))
    out["checked"] = len(chk); out["mismatches"] = bad; out["load_after"] = os.getloadavg()
    print("identical answers: %d of %d what-ifs" % (len(chk) - bad, len(chk)))
    for W, v in sorted(out["sweep"].items()): print("  %2d processes: %.2f ms per what-if, speed-up %.1fx, efficiency %.0f%%" % (W, v["ms_per_what_if"], v["speedup_vs_1"], 100 * v["efficiency"]))
    os.makedirs("results/pro", exist_ok=True); json.dump(out, open("results/pro/atlas_timing.json", "w"), indent=1)
