"""Chunked, resumable brute-force run over a storm set. One file per chunk; rerun to resume.

uv run --with mlx --with numpy python solver/run.py shared/storms_pilot.npz pilot [batch=8]

Other code can call run_storms(storms_path, indices) to simulate any subset (the cascade needs this).
"""
import os, sys, time, glob
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from flood import simulate, make_step

SETTINGS = dict(scheme="local-inertial (Bates 2010), semi-implicit Manning, flux limiter", alpha=0.7,
                h_floor=0.05, n_manning=0.015, theta=1.0, dtype="float32", tail_s=1200.0, rain_mult=1.0,
                dt_rule="per storm, alpha*dx/sqrt(g*hmax), refreshed every 10 steps, max 1.0 s")


def run_storms(storms_path, indices=None, batch=8, chunk_dir=None, fields_dir=None, log=print):
    """Simulate storms[indices]. Returns dict with peak_depth, final_depth (storms x receptors), etc.
    With chunk_dir, each batch is saved as it finishes and existing chunk files are reused."""
    t = np.load("shared/terrain_512.npz"); r = np.load("shared/receptors.npz"); s = np.load(storms_path)
    z, op, dx, rc = t["z"], t["open"], float(t["dx"]), r["rc"]
    idx = np.arange(len(s["depth_mm"])) if indices is None else np.asarray(indices)
    idx = idx[np.argsort(s["duration_s"][idx], kind="stable")]     # similar lengths share a batch
    step = make_step(z, op, dx)
    keys = ("peak_depth", "final_depth", "imbalance", "rain_net_m3", "stored_m3", "boundary_m3", "nsteps", "hmax")
    parts = []
    for c in range(0, len(idx), batch):
        ii = idx[c:c + batch]
        f = chunk_dir and os.path.join(chunk_dir, f"chunk_{c // batch:04d}.npz")
        if f and os.path.exists(f) and (np.load(f)["storm_index"] == ii).all():
            parts.append(dict(np.load(f))); continue
        t0 = time.time()
        o = simulate(z, op, dx, rc, s["profile"][ii], float(s["profile_step_s"]), s["loss_mm_h"][ii],
                     s["duration_s"][ii] + SETTINGS["tail_s"], step=step, return_fields=bool(fields_dir),
                     **{k: SETTINGS[k] for k in ("alpha", "h_floor", "n_manning", "theta", "rain_mult")})
        p = {k: o[k] for k in keys}
        p["storm_index"] = ii
        p["wall_s"] = np.full(len(ii), (time.time() - t0) / len(ii))   # chunk wall-clock shared equally
        if fields_dir:   # full peak-depth maps in mm, kept locally so receptors can change without a rerun
            os.makedirs(fields_dir, exist_ok=True)
            np.savez_compressed(os.path.join(fields_dir, f"peak_mm_{c // batch:04d}.npz"), storm_index=ii,
                                peak_mm=np.minimum(np.round(o["peak_field"] * 1000), 65535).astype(np.uint16))
        if f:
            os.makedirs(chunk_dir, exist_ok=True)
            np.savez(f + ".tmp.npz", **p); os.replace(f + ".tmp.npz", f)
        parts.append(p)
        log(f"chunk {c // batch + 1}/{-(-len(idx) // batch)}: {time.time() - t0:.0f}s, "
            f"max |imbalance| {np.abs(o['imbalance']).max():.1e}, hmax {o['hmax'].max():.2f} m, "
            f"{o['cell_steps_per_s'] / 1e6:.0f} Mcs/s")
    out = {k: np.concatenate([p[k] for p in parts]) for k in keys + ("storm_index", "wall_s")}
    order = np.argsort(out["storm_index"])
    return {k: v[order] for k, v in out.items()}


if __name__ == "__main__":
    path, tag = sys.argv[1], sys.argv[2]
    batch = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    t0 = time.time()
    out = run_storms(path, None, batch, f"results/pro/chunks_{tag}", f"results/pro/fields_{tag}")
    np.savez_compressed(f"results/pro/bruteforce_{tag}.npz", **out, batch=batch,
                        settings=np.array(repr(SETTINGS)), storms_file=path)
    print(f"{tag}: {len(out['storm_index'])} storms, this invocation {time.time() - t0:.0f}s, "
          f"summed chunk wall {out['wall_s'].sum():.0f}s, max |imbalance| {np.abs(out['imbalance']).max():.1e}")
