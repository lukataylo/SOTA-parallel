"""Fast exact critical rain depths for terrain patches: one linear sweep per patch instead of a FillModel rebuild + 261-storm run.

What it computes
    For a terrain z (the base terrain with a patch raised or lowered), the critical net rain depth of every receptor:
    the smallest P on the grid PG at which the settled water level in the receptor's basin reaches z[receptor] + thr.
    Same definitions as fill/decisive_par.py (FillModel + run(PG) + depth_at >= thr), reproduced exactly up to float rounding.

How (three ideas, all exact, none a derivative)
    1. One ascending sweep.  Passes (lowest pass per pair of adjacent basins), cells and receptor thresholds are merged in
       height order through a union-find.  Each component carries (number of cells below the sweep height, sum of their
       heights), so a depression's capacity at its pass is cnt*h - sum the moment it merges, and the volume a receptor
       needs is cnt*T - sum of its component when the sweep passes T = z_r + thr.  That replaces per-node hypsometry
       tables; the tree (parent, children, pass leaves, pass height, capacity, catchment area) comes out of the same sweep.
    2. Root-path evaluation.  In FillModel.run, overflow injected at a node only ever lands in a leaf of the sibling
       subtree, so the water a node receives depends only on its ancestors.  Whether receptor r is flooded at rain P is
       therefore decided by walking the root -> n* path (n* = the pond that holds level T), with no pass over the other
       ~20,000 nodes.  It floods iff some ancestor fills/merges, or n* receives >= the needed volume.
    3. Flooded-or-not is monotone in P, so the grid critical depth is found by bisection, started from the baseline
       critical depth (2 path walks if a patch did not move the receptor, 1 if it never floods).

Assumptions / limits
    - Monotone in P (true of the model; checked against the brute-force grid scan in sweep_check.py).
    - Threshold test is done in volume in float64 (flooded iff volume >= volume needed at T); FillModel inverts to a
      float32 level first.  They can differ only when a grid point lands within ~1e-6 m of the threshold.
    - Exact ties T == pass height are treated as "not yet flooded".
    - Rain weight is uniform over open cells (FillModel's default rainw).
    - Basins (steepest-descent labels) and pass list are recomputed from the patched grid each time (cheap, linear,
      compiled); the merge tree is rebuilt by the sweep.  So this is a ~10 ms rebuild, not an incremental repair, and
      not an analytic derivative: structure changes (new pits, a different pass becoming lowest, earlier merges) are
      handled because nothing is linearised.

Use
    S = Sweep.from_files()                     # or Sweep(z, open, rc)
    S.c0                                       # baseline critical depths, mm (inf = never within PG)
    S.patch(r, c, dz, rad=2)                   # critical depths (mm) with the patch applied
    S.patches(jobs)                            # (n_jobs, n_receptors)
    S.pstar(z)                                 # continuous critical depth (m), for derivative experiments
Run with: uv run --with numpy --with scipy --with numba python ...
"""
import numpy as np
from numba import njit

INF = np.inf


@njit(cache=True)
def _flooded(P, path, Lp, nstar, vreq, ca, cb, la, lb, cap, area, lo, hi, hasout, j0, leaving):
    """Is the pond n* (root path = path[0..Lp-1], path[0] = n*, path[Lp-1] = root) at or above the receptor threshold at rain P.
    j0[k] caches the path index of the last path node that still contains the leaf receiving node path[k]'s overflow
    (-2 = not yet computed); leaving[j] collects overflow whose target leaf drops off the path below path[j]."""
    if hasout[nstar]:
        return False
    for k in range(Lp): leaving[k] = 0.0
    X = 0.0                                               # overflow held in leaves of the current path node
    for k in range(Lp - 1, 0, -1):
        n = path[k]; c = path[k - 1]
        if ca[n] == c:
            o = cb[n]; tgt = la[n]
        else:
            o = ca[n]; tgt = lb[n]
        Xo = leaving[k]; Xc = X - Xo
        Tc = P * area[c] + Xc; To = P * area[o] + Xo
        if Tc > cap[c]:
            return True                                   # c full: merged, or held at the pass above the threshold
        if To > cap[o]:
            Eo = To - cap[o]
            if Tc + Eo > cap[c]:
                return True                               # sibling's overflow fills c too: merged above the threshold
            j = j0[k]
            if j == -2:
                p = lo[tgt]; a = 0; b = k - 1             # path[b] contains p; find the smallest index that does
                while a < b:
                    mid = (a + b) // 2
                    if p >= lo[path[mid]] and p < hi[path[mid]]: b = mid
                    else: a = mid + 1
                j = a; j0[k] = j
            leaving[j] += Eo; Xc += Eo                    # leaving[0] is never read: that overflow stays inside n*
        X = Xc
    return P * area[nstar] + X >= vreq


@njit(cache=True)
def _crit(z, openm, outm, first, cord, pcells, rcf, thr, PG, guess, zoff, want_cont):
    """z: patched terrain (ny, nx) float64.  cord: open cells (flat) in ascending base height.  pcells: flat indices of
    cells whose height differs from the base terrain.  guess: starting grid index per receptor (-1 = none).
    Returns grid index of the critical depth per receptor (len(PG) = never), continuous P* (if want_cont), and nb."""
    ny, nx = z.shape; n = ny * nx
    zf = z.ravel(); of = openm.ravel(); om = outm.ravel()
    # ---- steepest-descent receivers and basin labels (same tie rules as fillmodel._labels) ----
    rec = np.empty(n, np.int64)
    for i in range(n):
        if not of[i]:
            rec[i] = i; continue
        if om[i]:
            rec[i] = first; continue
        r = i // nx; c = i - r * nx
        m = INF; k = i
        if r > 0 and of[i - nx] and zf[i - nx] < m: m = zf[i - nx]; k = i - nx
        if r < ny - 1 and of[i + nx] and zf[i + nx] < m: m = zf[i + nx]; k = i + nx
        if c > 0 and of[i - 1] and zf[i - 1] < m: m = zf[i - 1]; k = i - 1
        if c < nx - 1 and of[i + 1] and zf[i + 1] < m: m = zf[i + 1]; k = i + 1
        rec[i] = k if m < zf[i] else i
    root = np.full(n, -1, np.int64); root[first] = first
    for i in range(n):
        if (not of[i]) or root[i] >= 0: continue
        j = i
        while root[j] < 0 and rec[j] != j: j = rec[j]
        rt = root[j] if root[j] >= 0 else j
        j = i
        while root[j] < 0 and rec[j] != j:
            nxt = rec[j]; root[j] = rt; j = nxt
        root[j] = rt
    lid = np.full(n, -1, np.int64); lid[first] = 0; nb = 1
    for i in range(n):
        if of[i] and root[i] == i and i != first:
            lid[i] = nb; nb += 1
    lab = np.full(n, -1, np.int64)
    N = 2 * nb - 1
    area = np.zeros(N)
    for i in range(n):
        if of[i]:
            lab[i] = lid[root[i]]; area[lab[i]] += 1.0
    # ---- lowest pass per pair of adjacent basins (hash dedup), then order by (w, a, b) ----
    bits = 12
    while (1 << bits) < 8 * nb: bits += 1
    H = 1 << bits; mask = H - 1
    slot = np.full(H, -1, np.int64)
    emax = 4 * nb + 64
    ekey = np.empty(emax, np.int64); ew = np.empty(emax, np.float64); ne = 0
    for i in range(n):
        li = lab[i]
        if li < 0: continue
        c = i % nx
        for d in range(2):
            if d == 0:
                if c == nx - 1: continue
                j = i + 1
            else:
                j = i + nx
                if j >= n: continue
            lj = lab[j]
            if lj < 0 or lj == li: continue
            w = zf[i] if zf[i] > zf[j] else zf[j]
            key = li * nb + lj if li < lj else lj * nb + li
            s = ((li * 40503 + lj * 9973) ^ (key >> 7)) & mask
            while True:
                e = slot[s]
                if e < 0:
                    if ne == emax:                         # grow (rare)
                        emax *= 2
                        k2 = np.empty(emax, np.int64); k2[:ne] = ekey[:ne]; ekey = k2
                        w2 = np.empty(emax, np.float64); w2[:ne] = ew[:ne]; ew = w2
                    slot[s] = ne; ekey[ne] = key; ew[ne] = w; ne += 1; break
                if ekey[e] == key:
                    if w < ew[e]: ew[e] = w
                    break
                s = (s + 1) & mask
    o1 = np.argsort(ekey[:ne])
    o2 = np.argsort(ew[:ne][o1], kind="mergesort")
    eo = o1[o2]
    # ---- patched cells as a second sorted stream; receptor thresholds as a third ----
    skip = np.zeros(n, np.bool_)
    npc = len(pcells)
    pz = np.empty(npc)
    for i in range(npc):
        skip[pcells[i]] = True; pz[i] = zf[pcells[i]]
    po = np.argsort(pz)
    nr = len(rcf)
    T = np.empty(nr)
    for q in range(nr): T[q] = zf[rcf[q]] + thr
    qo = np.argsort(T)
    nstar = np.zeros(nr, np.int64); vreq = np.zeros(nr)
    # ---- the sweep: Kruskal over passes + running (count, sum z) of cells below the sweep height per component ----
    h = np.full(N, -INF); parent = np.full(N, -1, np.int64)
    ca = np.full(N, -1, np.int64); cb = np.full(N, -1, np.int64); la = np.full(N, -1, np.int64); lb = np.full(N, -1, np.int64)
    cap = np.full(N, INF); hasout = np.zeros(N, np.bool_); hasout[0] = True
    nleaf = np.ones(N, np.int64)
    uf = np.arange(nb); node_of = np.arange(nb)
    cnt = np.zeros(nb); sm = np.zeros(nb)
    k = nb; ie = 0; ic = 0; ip = 0; iq = 0; nc = len(cord)
    while True:
        he = ew[eo[ie]] if ie < ne else INF
        while ic < nc and skip[cord[ic]]: ic += 1
        hc1 = zf[cord[ic]] if ic < nc else INF
        hc2 = pz[po[ip]] if ip < npc else INF
        hq = T[qo[iq]] if iq < nr else INF
        hc = hc1 if hc1 <= hc2 else hc2
        if he <= hc and he <= hq:
            if he == INF: break
            e = eo[ie]; ie += 1
            key = ekey[e]; u = key // nb; v = key - u * nb; w = ew[e]
            ru = u
            while uf[ru] != ru: ru = uf[ru]
            while uf[u] != ru:
                t = uf[u]; uf[u] = ru; u = t
            rv = v
            while uf[rv] != rv: rv = uf[rv]
            while uf[v] != rv:
                t = uf[v]; uf[v] = rv; v = t
            if ru == rv: continue
            a = node_of[ru]; b = node_of[rv]
            ca[k] = a; cb[k] = b; la[k] = key // nb; lb[k] = key - (key // nb) * nb; h[k] = w
            parent[a] = k; parent[b] = k
            if not hasout[a]: cap[a] = cnt[ru] * (w - zoff) - sm[ru]
            if not hasout[b]: cap[b] = cnt[rv] * (w - zoff) - sm[rv]
            area[k] = area[a] + area[b]; nleaf[k] = nleaf[a] + nleaf[b]; hasout[k] = hasout[a] or hasout[b]
            uf[ru] = rv; node_of[rv] = k; cnt[rv] += cnt[ru]; sm[rv] += sm[ru]; k += 1
        elif hc <= hq:
            if hc1 <= hc2:
                i = cord[ic]; ic += 1
            else:
                i = pcells[po[ip]]; ip += 1
            u = lab[i]; ru = u
            while uf[ru] != ru: ru = uf[ru]
            while uf[u] != ru:
                t = uf[u]; uf[u] = ru; u = t
            cnt[ru] += 1.0; sm[ru] += zf[i] - zoff
        else:
            q = qo[iq]; iq += 1
            u = lab[rcf[q]]; ru = u
            while uf[ru] != ru: ru = uf[ru]
            nstar[q] = node_of[ru]; vreq[q] = cnt[ru] * (T[q] - zoff) - sm[ru]
    for leaf in range(1, nb):                              # enclosed courtyards: tied to the outlet at 1e9, never spill
        ru = leaf
        while uf[ru] != ru: ru = uf[ru]
        rv = 0
        while uf[rv] != rv: rv = uf[rv]
        if ru == rv: continue
        a = node_of[ru]; b = node_of[rv]
        ca[k] = a; cb[k] = b; la[k] = leaf; lb[k] = 0; h[k] = 1e9
        parent[a] = k; parent[b] = k
        area[k] = area[a] + area[b]; nleaf[k] = nleaf[a] + nleaf[b]; hasout[k] = True
        uf[ru] = rv; node_of[rv] = k; k += 1
    lo = np.zeros(N, np.int64); hi = np.zeros(N, np.int64); hi[N - 1] = nb
    for m in range(N - 1, nb - 1, -1):
        a = ca[m]; b = cb[m]
        lo[a] = lo[m]; hi[a] = lo[m] + nleaf[a]; lo[b] = hi[a]; hi[b] = hi[m]
    # ---- critical depth per receptor: root-path walks, bisection on the grid ----
    nP = len(PG)
    out = np.full(nr, nP, np.int64); cont = np.full(nr, INF)
    path = np.empty(N, np.int64); lpos = np.empty(N, np.int64); lE = np.empty(N)   # lpos: cached exit index, lE: leaving volume
    nwalk = 0
    for q in range(nr):
        ns = nstar[q]
        if hasout[ns]: continue
        Lp = 0; m = ns
        while m >= 0:
            path[Lp] = m; lpos[Lp] = -2; Lp += 1; m = parent[m]
        a = -1; b = nP                                     # a: highest index known dry; b: lowest known flooded (nP = none)
        g = guess[q]
        if g >= 0 and g < nP:
            nwalk += 1
            if _flooded(PG[g], path, Lp, ns, vreq[q], ca, cb, la, lb, cap, area, lo, hi, hasout, lpos, lE):
                b = g
                if g > 0:
                    nwalk += 1
                    if _flooded(PG[g - 1], path, Lp, ns, vreq[q], ca, cb, la, lb, cap, area, lo, hi, hasout, lpos, lE): b = g - 1
                    else: a = g - 1
            else:
                a = g
        if b == nP:
            nwalk += 1
            if _flooded(PG[nP - 1], path, Lp, ns, vreq[q], ca, cb, la, lb, cap, area, lo, hi, hasout, lpos, lE): b = nP - 1
            else: continue
        while b - a > 1:
            mid = (a + b) // 2; nwalk += 1
            if _flooded(PG[mid], path, Lp, ns, vreq[q], ca, cb, la, lb, cap, area, lo, hi, hasout, lpos, lE): b = mid
            else: a = mid
        out[q] = b
        if want_cont:
            p0 = PG[b - 1] if b > 0 else 0.0; p1 = PG[b]
            for it in range(30):
                pm = 0.5 * (p0 + p1)
                if _flooded(pm, path, Lp, ns, vreq[q], ca, cb, la, lb, cap, area, lo, hi, hasout, lpos, lE): p1 = pm
                else: p0 = pm
            cont[q] = p1
    return out, cont, nb, nwalk


class Sweep:
    def __init__(self, z, open_, rc, PG=None, thr=0.10):
        self.z0 = np.ascontiguousarray(z, np.float64); self.open = np.ascontiguousarray(open_, np.bool_)
        edge = np.zeros_like(self.open); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
        self.outlet = np.ascontiguousarray(edge & self.open)
        self.first = int(np.flatnonzero(self.outlet.ravel())[0])
        self.rc = np.asarray(rc); self.rcf = (self.rc[:, 0] * self.z0.shape[1] + self.rc[:, 1]).astype(np.int64)
        assert self.open.ravel()[self.rcf].all(), "receptor on a closed cell"
        self.PG = np.linspace(0.0, 0.130, 261) if PG is None else np.asarray(PG, np.float64)
        self.thr = float(thr)
        opf = np.flatnonzero(self.open.ravel())
        self.cord = opf[np.argsort(self.z0.ravel()[opf], kind="stable")].astype(np.int64)
        self.zoff = float(self.z0.ravel()[opf].min())
        self._none = np.empty(0, np.int64)
        self.guess = np.full(len(self.rcf), -1, np.int64)
        idx, _, self.nb, _ = _crit(self.z0, self.open, self.outlet, self.first, self.cord, self._none, self.rcf, self.thr, self.PG, self.guess, self.zoff, False)
        self.idx0 = idx; self.guess = np.where(idx < len(self.PG), idx, -1).astype(np.int64)
        self.c0 = self._mm(idx)
        self.last_nwalk = 0

    @classmethod
    def from_files(cls, terrain="shared/terrain_512.npz", receptors="shared/receptors.npz", **kw):
        T = np.load(terrain)
        return cls(T["z"].astype(np.float64), T["open"], np.load(receptors)["rc"], **kw)

    def _mm(self, idx):
        nP = len(self.PG)
        return np.where(idx < nP, self.PG[np.minimum(idx, nP - 1)] * 1e3, np.inf)

    def crit(self, z, changed=None):
        """Critical depths (mm) for an arbitrary terrain z.  changed: flat indices of cells that differ from the base
        terrain (found by comparison if omitted)."""
        z = np.ascontiguousarray(z, np.float64)
        if changed is None: changed = np.flatnonzero((z != self.z0).ravel() & self.open.ravel())
        idx, _, _, self.last_nwalk = _crit(z, self.open, self.outlet, self.first, self.cord, np.asarray(changed, np.int64), self.rcf, self.thr, self.PG, self.guess, self.zoff, False)
        return self._mm(idx)

    def pstar(self, z, changed=None):
        """Continuous critical depth (m) per receptor (inf if above PG[-1])."""
        z = np.ascontiguousarray(z, np.float64)
        if changed is None: changed = np.flatnonzero((z != self.z0).ravel() & self.open.ravel())
        return _crit(z, self.open, self.outlet, self.first, self.cord, np.asarray(changed, np.int64), self.rcf, self.thr, self.PG, self.guess, self.zoff, True)[1]

    def _apply(self, z, r, c, dz, rad):
        ny, nx = z.shape
        r0, r1, c0, c1 = max(r - rad, 0), min(r + rad + 1, ny), max(c - rad, 0), min(c + rad + 1, nx)
        sub = self.open[r0:r1, c0:c1]
        rr, cc = np.nonzero(sub)
        ch = ((rr + r0) * nx + (cc + c0)).astype(np.int64)
        z.ravel()[ch] = self.z0.ravel()[ch] + dz
        return ch

    def patch(self, r, c, dz, rad=2, cont=False):
        """Critical depths (mm) with open cells of rows r-rad..r+rad, cols c-rad..c+rad moved by dz (m)."""
        if not hasattr(self, "_zw"): self._zw = self.z0.copy()
        z = self._zw
        ch = self._apply(z, int(r), int(c), float(dz), int(rad))
        try:
            idx, ct, self.last_nb, self.last_nwalk = _crit(z, self.open, self.outlet, self.first, self.cord, ch, self.rcf, self.thr, self.PG, self.guess, self.zoff, cont)
        finally:
            z.ravel()[ch] = self.z0.ravel()[ch]
        return ct if cont else self._mm(idx)

    def patches(self, jobs):
        """jobs: (n, 4) rows (r, c, dz, rad).  Returns (n, n_receptors) critical depths in mm."""
        out = np.empty((len(jobs), len(self.rcf)))
        for i, (r, c, dz, rad) in enumerate(jobs):
            out[i] = self.patch(int(r), int(c), float(dz), int(rad))
        return out
