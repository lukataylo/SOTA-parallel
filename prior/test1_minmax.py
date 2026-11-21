"""Test 1: depression fill as a (min,max) algebra problem.
Fill level F(c) = min over paths c->outlet of the max elevation on the path.
Reference: sequential priority-flood (heap). Parallel forms tested:
  A. grid Jacobi sweeps      F <- max(z, min_nbr F)
  B. basin graph: pointer-jumping labels, pass heights, then
     B1. Bellman-Ford rounds in (min,max) on the sparse basin graph
     B2. dense (min,max) matrix squaring (small graphs only)
Kill line: exact equality with the reference on every terrain."""
import heapq, time, json, sys, numpy as np
from scipy.ndimage import gaussian_filter
from skimage.morphology import reconstruction

def priority_flood(z, outlet):
    ny, nx = z.shape; F = np.full(z.shape, np.inf); done = np.zeros(z.shape, bool); pq = []
    for i, j in zip(*np.where(outlet)):
        F[i, j] = z[i, j]; done[i, j] = True; pq.append((z[i, j], i, j))
    heapq.heapify(pq)
    while pq:
        f, i, j = heapq.heappop(pq)
        for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if 0 <= a < ny and 0 <= b < nx and not done[a, b]:
                done[a, b] = True; F[a, b] = max(z[a, b], f); heapq.heappush(pq, (F[a, b], a, b))
    return F

def nbr_min(F):
    P = np.pad(F, 1, constant_values=np.inf)
    return np.minimum(np.minimum(P[:-2, 1:-1], P[2:, 1:-1]), np.minimum(P[1:-1, :-2], P[1:-1, 2:]))

def jacobi(z, outlet):
    F = np.where(outlet, z, np.inf); n = 0
    while True:
        G = np.where(outlet, z, np.maximum(z, nbr_min(F))); n += 1
        if np.array_equal(G, F): return F, n
        F = G

def basin_graph(z, outlet):
    ny, nx = z.shape; n = ny * nx; idx = np.arange(n).reshape(ny, nx)
    P = np.pad(z, 1, constant_values=np.inf)
    stack = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
    k = stack.argmin(0); m = stack.min(0)
    off = np.array([-nx, nx, -1, 1])[k]
    rec = np.where(m < z, idx + off, idx).ravel()
    out = outlet.ravel(); first_out = np.where(out)[0][0]
    rec[out] = first_out                               # all outlet cells collapse onto one node
    jumps = 0
    while True:                                        # pointer jumping: log rounds
        r2 = rec[rec]; jumps += 1
        if np.array_equal(r2, rec): break
        rec = r2
    roots, lab = np.unique(rec, return_inverse=True)
    out_lab = lab[first_out]
    zf = z.ravel(); L = lab.reshape(ny, nx)
    zo = z
    E = []
    for (sa, sb) in (((slice(None), slice(0, -1)), (slice(None), slice(1, None))),
                     ((slice(0, -1), slice(None)), (slice(1, None), slice(None)))):
        la, lb = L[sa].ravel(), L[sb].ravel(); w = np.maximum(zo[sa], zo[sb]).ravel()
        keep = la != lb; E.append(np.stack([la[keep], lb[keep], w[keep]]))
    E = np.concatenate(E, 1); u = np.minimum(E[0], E[1]).astype(np.int64); v = np.maximum(E[0], E[1]).astype(np.int64)
    nb = len(roots); key = u * nb + v; o = np.lexsort((E[2], key)); key, w = key[o], E[2][o]
    first = np.r_[True, key[1:] != key[:-1]]
    return lab, out_lab, nb, key[first] // nb, key[first] % nb, w[first], jumps

def bellman(nb, out_lab, u, v, w):
    d = np.full(nb, np.inf); d[out_lab] = -np.inf; n = 0
    while True:
        d2 = d.copy()
        np.minimum.at(d2, u, np.maximum(w, d[v])); np.minimum.at(d2, v, np.maximum(w, d[u])); n += 1
        if np.array_equal(d2, d): return d, n
        d = d2

def squaring(nb, out_lab, u, v, w):
    D = np.full((nb, nb), np.inf, np.float32); D[u, v] = w; D[v, u] = w; np.fill_diagonal(D, -np.inf); n = 0
    while True:
        D2 = np.empty_like(D)
        for s in range(0, nb, 64):
            D2[s:s + 64] = np.maximum(D[s:s + 64, :, None], D[None, :, :]).min(1)
        n += 1
        if np.array_equal(D2, D): return D[:, out_lab], n
        D = D2

def run(name, z, outlet, do_sq):
    z = z.astype(np.float64); r = dict(cells=int(z.size))
    t = time.time(); F0 = priority_flood(z, outlet); r["t_heap_python"] = time.time() - t
    seed = np.where(outlet, z, z.max() + 1); fp = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    t = time.time(); Fs = reconstruction(seed, z, method="erosion", footprint=fp); r["t_skimage_C"] = time.time() - t
    r["skimage_equal"] = bool(np.array_equal(Fs, F0))
    t = time.time(); FA, nA = jacobi(z, outlet); r["t_jacobi"] = time.time() - t
    r["jacobi_sweeps"] = nA; r["jacobi_equal"] = bool(np.array_equal(FA, F0))
    t = time.time(); lab, ol, nb, u, v, w, jumps = basin_graph(z, outlet); tg = time.time() - t
    t = time.time(); d, nBF = bellman(nb, ol, u, v, w); r["t_graph_total"] = tg + time.time() - t
    FB = np.where(outlet, z, np.maximum(z, d[lab].reshape(z.shape)))
    r.update(basins=nb, edges=len(u), pointer_jumps=jumps, bf_rounds=nBF, graph_equal=bool(np.array_equal(FB, F0)),
             max_abs_diff=float(np.abs(FB - F0).max()), filled_frac=float((F0 > z).mean()))
    if do_sq and nb <= 1500:
        t = time.time(); d2, nS = squaring(nb, ol, u, v, w); r["t_squaring"] = time.time() - t
        FS = np.where(outlet, z, np.maximum(z, d2.astype(np.float64)[lab].reshape(z.shape)))
        r.update(squarings=nS, log2_basins=float(np.log2(nb)),
                 squaring_equal=bool(np.allclose(FS, F0, atol=1e-6)), sq_max_diff=float(np.abs(FS - F0).max()))
    print(name, json.dumps(r), flush=True); return r

if __name__ == "__main__":
    from floodlab import make_street
    R = {}
    for seed in (1, 2, 3):
        st = make_street(seed, 0.25); z = st["z"]
        outlet = np.zeros(z.shape, bool); outlet[:, 0] = st["open"][:, 0]; outlet[:, -1] = st["open"][:, -1]
        R[f"street{seed}"] = run(f"street{seed}", z, outlet, True)
    for n in (128, 256, 512, 1024):
        rng = np.random.default_rng(n)
        z = sum(gaussian_filter(rng.normal(0, 1, (n, n)), s) * s for s in (1, 4, 16, 64))
        outlet = np.zeros((n, n), bool); outlet[0] = outlet[-1] = True; outlet[:, 0] = outlet[:, -1] = True
        R[f"rough{n}"] = run(f"rough{n}", z, outlet, n <= 128)
    json.dump(R, open("res_test1.json", "w"), indent=1)
