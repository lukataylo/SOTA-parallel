"""Bet 4 / Mythos move 1: the exact what-if for EVERY open square metre of the tile.
A 5 x 5 m patch centred on each open cell, raised and lowered 5 cm, evaluated exactly with Sweep for all 207 receptors.
Answers do not depend on machine load; timings here do, and the clean timing is taken separately on an idle machine.
  uv run --with numpy --with scipy --with numba python fill/atlas.py [workers]"""
import sys, time, os, numpy as np, multiprocessing as mp
sys.path.insert(0, "fill")
T = np.load("shared/terrain_512.npz"); OP = T["open"]
_S = None
def init():
    global _S
    from sweep import Sweep
    _S = Sweep.from_files()
def work(rows):
    c0 = _S.c0; cap = lambda x: np.minimum(np.where(np.isfinite(x), x, 130.5), 130.5); out = []
    for r in rows:
        cols = np.flatnonzero(OP[r]); res = np.zeros((len(cols), 2, 3), np.float32)        # per cell, per sign: n moved, max rise, max fall
        for k, c in enumerate(cols):
            for s, dz in enumerate((0.05, -0.05)):
                d = cap(_S.patch(int(r), int(c), dz, 2)) - cap(c0); m = np.abs(d) >= 1.0
                res[k, s] = (m.sum(), d.max(), d.min())
        out.append((r, cols, res))
    return out
if __name__ == "__main__":
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 8; rows = np.arange(512); chunks = [rows[i::64] for i in range(64)]
    t0 = time.time(); n = np.zeros((2, 512, 512), np.int16); rise = np.zeros((2, 512, 512), np.float32); fall = np.zeros((2, 512, 512), np.float32); done = 0
    with mp.Pool(W, initializer=init) as p:
        for part in p.imap_unordered(work, chunks):
            for r, cols, res in part:
                n[:, r, cols] = res[:, :, 0].T; rise[:, r, cols] = res[:, :, 1].T; fall[:, r, cols] = res[:, :, 2].T
            done += 1
            if done % 8 == 0: print("%d/64 chunks, %.0f s" % (done, time.time() - t0), flush=True)
    wall = time.time() - t0; nq = int(OP.sum()) * 2
    np.savez_compressed("results/air/atlas.npz", n_moved=n, max_rise_mm=rise, max_fall_mm=fall, wall_s=wall, workers=W, what_ifs=nq)
    act = (n > 0).any(0) & OP
    print("WHOLE TILE: %d exact what-ifs (every open cell, +5 and -5 cm) in %.0f s on %d processes = %.1f ms each wall, %.1f ms per core" % (nq, wall, W, 1e3 * wall / nq, 1e3 * wall * W / nq))
    print("cells where a 25 m2, 5 cm change moves some building's critical rain by >= 1 mm: %d of %d open cells (%.1f%%)" % (act.sum(), OP.sum(), 100 * act.sum() / OP.sum()))
    print("   moves 2+ buildings: %d cells; 5+: %d; most buildings moved from one cell: %d" % ((n.max(0) >= 2).sum(), (n.max(0) >= 5).sum(), n.max()))
    print("   raise-only active %d, lower-only active %d, both %d" % (((n[0] > 0) & (n[1] == 0)).sum(), ((n[1] > 0) & (n[0] == 0)).sum(), ((n[0] > 0) & (n[1] > 0)).sum()))
    print("   by rebuilding at 1.3 s each this would take %.1f days on one core" % (nq * 1.3 / 86400))
