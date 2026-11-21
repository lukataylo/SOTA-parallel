"""Batched partial fill-spill-merge on a depression tree.

Terrain work is done once (build). Every storm is then one column of a vectorised top-down sweep (run).

Model: rain lands on each cell and runs downhill to its pit. Pits fill. A full depression spills over its
lowest pass into the neighbouring depression; when both sides of a pass are full they merge into one pond
with a level set by the merged hypsometry. Water that reaches the outlet leaves. No time, no momentum.

Tree: leaves are steepest-descent basins (leaf 0 is the outlet, with infinite capacity). Internal nodes are
merges in ascending pass height (Kruskal). Every node n has
  h[n]   height at which its two children merged (leaves: -inf)
  hp[n]  its own spill height = h[parent]
  cap[n] volume it holds at hp[n]
A cell is "assigned" to the node n on its root path with h[n] <= z < hp[n]; those cells give the node's
hypsometry between h[n] and hp[n].
"""
import numpy as np


def _labels(z, open_, outlet):
    ny, nx = z.shape
    idx = np.arange(ny * nx).reshape(ny, nx)
    zz = np.where(open_, z, np.inf)
    P = np.pad(zz, 1, constant_values=np.inf)
    st = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
    k = st.argmin(0); m = st.min(0)
    rec = np.where(m < zz, idx + np.array([-nx, nx, -1, 1])[k], idx).ravel()
    out = outlet.ravel(); first = np.flatnonzero(out)[0]
    rec[out] = first
    while True:
        r2 = rec[rec]
        if np.array_equal(r2, rec): break
        rec = r2
    op = open_.ravel()
    roots = np.unique(rec[op]); roots = np.r_[first, roots[roots != first]]      # leaf 0 = outlet
    lut = np.full(ny * nx, -1, np.int64); lut[roots] = np.arange(len(roots))
    lab = np.where(op, lut[rec], -1).reshape(ny, nx)
    return lab, len(roots)


def _edges(z, lab):
    E = []
    for sa, sb in (((slice(None), slice(0, -1)), (slice(None), slice(1, None))),
                   ((slice(0, -1), slice(None)), (slice(1, None), slice(None)))):
        la, lb = lab[sa].ravel(), lab[sb].ravel(); w = np.maximum(z[sa], z[sb]).ravel()
        keep = (la != lb) & (la >= 0) & (lb >= 0)
        E.append((la[keep], lb[keep], w[keep]))
    u = np.concatenate([e[0] for e in E]); v = np.concatenate([e[1] for e in E]); w = np.concatenate([e[2] for e in E]).astype(np.float64)
    a, b = np.minimum(u, v), np.maximum(u, v)
    o = np.lexsort((w, b, a)); a, b, w = a[o], b[o], w[o]
    first = np.r_[True, (a[1:] != a[:-1]) | (b[1:] != b[:-1])]
    a, b, w = a[first], b[first], w[first]
    o = np.argsort(w, kind="stable")
    return a[o], b[o], w[o]


class FillModel:
    def __init__(self, z, open_, outlet, rainw=None):
        z = np.asarray(z, np.float64); self.z = z; self.open = open_
        rainw = open_.astype(np.float64) if rainw is None else np.asarray(rainw, np.float64) * open_
        lab, nb = _labels(z, open_, outlet); self.lab = lab; self.nb = nb
        eu, ev, ew = _edges(z, lab)
        N = 2 * nb - 1
        h = np.full(N, -np.inf); parent = np.full(N, -1, np.int64)
        ca = np.full(N, -1, np.int64); cb = np.full(N, -1, np.int64)        # children
        la = np.full(N, -1, np.int64); lb = np.full(N, -1, np.int64)        # pass leaf inside child a / child b
        uf = np.arange(nb); node_of = np.arange(nb)
        def find(x):
            r = x
            while uf[r] != r: r = uf[r]
            while uf[x] != r: uf[x], x = r, uf[x]
            return r
        k = nb
        def join(u, v, w):
            nonlocal k
            ru, rv = find(u), find(v)
            if ru == rv: return
            a, b = node_of[ru], node_of[rv]
            ca[k], cb[k], la[k], lb[k], h[k] = a, b, u, v, w
            parent[a] = parent[b] = k
            uf[ru] = rv; node_of[rv] = k; k += 1
        for u, v, w in zip(eu.tolist(), ev.tolist(), ew.tolist()): join(u, v, w)
        for leaf in range(1, nb):                       # enclosed courtyards: tie to the outlet at a height nothing reaches
            join(leaf, 0, 1e9)
        assert k == N
        self.N, self.h, self.parent, self.ca, self.cb, self.la, self.lb = N, h, parent, ca, cb, la, lb
        root = N - 1; self.root = root
        hp = np.where(parent >= 0, h[np.maximum(parent, 0)], np.inf); self.hp = hp

        # areas (rain weight) and cell counts per node; leaf order positions
        op = open_.ravel(); labf = lab.ravel()[op]; zf = z.ravel()[op]
        area = np.zeros(N); np.add.at(area, labf, rainw.ravel()[op])
        nleaf = np.zeros(N, np.int64); nleaf[:nb] = 1
        has_out = np.zeros(N, bool); has_out[0] = True
        for n in range(nb, N):
            a, b = ca[n], cb[n]
            area[n] = area[a] + area[b]; nleaf[n] = nleaf[a] + nleaf[b]; has_out[n] = has_out[a] | has_out[b]
        lo = np.zeros(N, np.int64); hi = np.zeros(N, np.int64); hi[root] = nb
        for n in range(N - 1, nb - 1, -1):
            a, b = ca[n], cb[n]
            lo[a], hi[a] = lo[n], lo[n] + nleaf[a]; lo[b], hi[b] = hi[a], hi[n]
        self.area, self.lo, self.hi, self.has_out = area, lo, hi, has_out

        # assign each cell to the node whose [h, hp) range holds its height (binary lifting up the root path)
        anc = [np.where(parent >= 0, parent, np.arange(N))]
        while (1 << len(anc)) < N: anc.append(anc[-1][anc[-1]])
        cur = labf.copy()
        for up in reversed(anc):
            nxt = up[cur]; ok = h[nxt] <= zf; cur = np.where(ok, nxt, cur)
        o = np.lexsort((zf, cur)); cn, cz = cur[o], zf[o]
        start = np.searchsorted(cn, np.arange(N)); end = np.searchsorted(cn, np.arange(N), side="right")
        m = end - start
        hbase = h.copy()
        zmin = np.full(N, np.inf); np.minimum.at(zmin, labf, zf)
        hbase[:nb] = zmin[:nb]                          # leaves start at their pit
        N0 = np.zeros(N, np.int64); V0 = np.zeros(N); cap = np.zeros(N)
        self.Lb, self.G = [None] * N, [None] * N
        for n in range(N):
            if n >= nb:
                a, b = ca[n], cb[n]
                N0[n] = N0[a] + m[a] + N0[b] + m[b]; V0[n] = cap[a] + cap[b]
            zs = cz[start[n]:end[n]]
            Lb = np.r_[hbase[n], zs] if np.isfinite(hbase[n]) else zs[:1].repeat(1) if len(zs) else np.array([0.0])
            if not np.isfinite(hbase[n]): Lb = np.r_[zs[:1], zs] if len(zs) else np.array([0.0])
            G = np.r_[0.0, np.cumsum((N0[n] + np.arange(len(Lb) - 1)) * np.diff(Lb))]
            self.Lb[n], self.G[n] = Lb, G
            if np.isfinite(hp[n]) and hp[n] < 1e8 and not has_out[n]:
                cap[n] = V0[n] + G[-1] + (N0[n] + len(Lb) - 1) * (hp[n] - Lb[-1])
            else:
                cap[n] = np.inf
        self.N0, self.V0, self.cap, self.hbase = N0, V0, cap, hbase
        self.depth_tree = None

    def _level(self, n, dV):
        """Water level in node n holding dV above its base volume V0[n]."""
        Lb, G = self.Lb[n], self.G[n]
        j = np.clip(np.searchsorted(G, dV, side="right") - 1, 0, len(G) - 1)
        cnt = self.N0[n] + j
        return Lb[j] + np.where(cnt > 0, (dV - G[j]) / np.maximum(cnt, 1), 0.0)

    def run(self, P):
        """P: net rain depths in metres, shape (S,). Returns leaf water levels (nb, S) and outflow volume (S,)."""
        P = np.asarray(P, np.float64); S = len(P); nb, N = self.nb, self.N
        ca, cb, la, lb, cap, area, lo, hi, h = self.ca, self.cb, self.la, self.lb, self.cap, self.area, self.lo, self.hi, self.h
        fen = np.zeros((nb + 1, S))                     # Fenwick tree over leaf positions, one column per storm
        def add(pos, val):
            i = pos + 1
            while i <= nb: fen[i] += val; i += i & -i
        def pref(i):
            s = np.zeros(S)
            while i > 0: s += fen[i]; i -= i & -i
            return s
        any_inj = False
        def X(n):
            return pref(hi[n]) - pref(lo[n]) if any_inj else 0.0
        sub = np.zeros((N, S), bool); lev = np.full((N, S), -np.inf, np.float32)
        for n in range(N - 1, nb - 1, -1):
            a, b = ca[n], cb[n]
            act = ~sub[n]
            if not act.any():
                sub[a] = sub[b] = True; lev[a] = lev[b] = lev[n]; continue
            Ta = P * area[a] + X(a); Tb = P * area[b] + X(b)
            fa, fb = Ta > cap[a], Tb > cap[b]
            Ea = np.where(fa & ~fb, Ta - cap[a], 0.0) if np.isfinite(cap[a]) else np.zeros(S)
            Eb = np.where(fb & ~fa, Tb - cap[b], 0.0) if np.isfinite(cap[b]) else np.zeros(S)
            merged = act & ((fa & fb) | (fa & ~fb & (Tb + Ea > cap[b])) | (fb & ~fa & (Ta + Eb > cap[a])))
            onlya = act & fa & ~merged; onlyb = act & fb & ~merged
            if merged.any():
                L = self._level(n, Ta + Tb - self.V0[n])
                for c in (a, b):
                    sub[c] |= merged; lev[c] = np.where(merged, L, lev[c])
            if onlya.any():
                sub[a] |= onlya; lev[a] = np.where(onlya, h[n], lev[a])
                add(self.lo[lb[n]], np.where(onlya, Ea, 0.0)); any_inj = True
            if onlyb.any():
                sub[b] |= onlyb; lev[b] = np.where(onlyb, h[n], lev[b])
                add(self.lo[la[n]], np.where(onlyb, Eb, 0.0)); any_inj = True
            inh = ~act
            if inh.any():
                for c in (a, b):
                    sub[c] |= inh; lev[c] = np.where(inh, lev[n], lev[c])
        LL = np.empty((nb, S), np.float32)
        for l in range(nb):
            if l == 0: LL[l] = -np.inf; continue
            T = P * area[l] + X(l)
            LL[l] = np.where(sub[l], lev[l], self._level(l, np.minimum(T, cap[l])))
        outflow = P * area[0] + (X(0) if any_inj else 0.0)
        return LL, outflow

    def depth_at(self, LL, rc):
        r, c = rc[:, 0], rc[:, 1]
        return np.maximum(LL[self.lab[r, c]].T - self.z[r, c][None, :], 0.0)       # (S, n_receptors)

    def depth_field(self, LL, s):
        d = np.zeros(self.z.shape)
        op = self.open
        d[op] = np.maximum(LL[self.lab[op], s] - self.z[op], 0.0)
        return d
