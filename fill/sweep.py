"""Exact critical rain depths after a terrain patch, from a repaired depression tree: no FillModel rebuild, no 261-storm run.

What it computes
    For the base terrain with a set of open cells raised or lowered (a patch), the critical net rain depth of every
    receptor: the smallest P on the grid PG at which the settled water level in the receptor's basin reaches
    z[receptor] + thr.  Same definitions as fill/decisive_par.py (FillModel + run(PG) + depth_at >= thr; outlet = open
    cells on the domain edge; threshold measured from the receptor cell's own, possibly patched, ground).
    It is a finite-change evaluation, not a derivative: structure changes inside the 5 cm step (a different pass
    becoming the lowest, pits created or removed, ponds merging earlier) are followed exactly.

How
    Built once: steepest-descent basins, the lowest pass per pair of adjacent basins in merge order, cells sorted by height.
    Per patch:
    1. Local repair.  Flow directions can change only in the patch and its 4-neighbours; only cells upstream of a
       changed direction can change basin; only passes between basin pairs that touch a changed cell are recomputed
       (by scanning the smaller basin of the pair).  Everything else is reused.
    2. One ascending sweep (Kruskal over the pass list, with cells and receptor thresholds merged in by height).  Each
       component carries (number of cells below the sweep height, sum of their heights), so a depression's capacity at
       its pass is cnt*h - sum at the moment it merges, and the volume a receptor needs is cnt*T - sum of its component
       when the sweep passes T = z_r + thr.  No per-node hypsometry tables.  Components that hold the outlet, or whose
       capacity exceeds all the rain that can fall (PG[-1] x open area), can never fill; their cells are skipped.
    3. Root-path walk.  In FillModel.run, overflow made at a node always lands in a leaf of the sibling subtree, so the
       water a node receives depends only on its ancestors.  Whether a receptor is flooded at rain P is decided by
       walking root -> n* (n* = the pond whose height range holds T): flooded iff an ancestor's on-path child fills,
       or n* receives at least the needed volume.  Receptors share path prefixes.
    4. Flooded-or-not is monotone in P, so the grid critical depth is found by bisection started at the baseline value
       (2 walks if the patch did not move the receptor, 1 if it never floods).

Assumptions / limits
    - Monotone in P (checked: results equal the brute-force first-wet-grid-point scan, see sweep_check.py).
    - The threshold test is done in volume in float64; FillModel inverts to a float32 level first.  They can differ
      only if a grid point lands within about 1e-6 m of the threshold.  Exact ties T == pass height count as dry.
    - Rain weight uniform over open cells (FillModel's default); open mask and receptors fixed; receptors on open cells.
    - Cost grows with the number of cells that change basin; above max_relabel the repair is still exact but slower.
    - Not thread-safe (baseline work arrays are edited in place and restored).

Use
    S = Sweep.from_files()                     # or Sweep(z, open, rc)
    S.c0                                       # baseline critical depths, mm (inf = never within PG)
    S.patch(r, c, dz, rad=2)                   # critical depths (mm) with the patch applied
    S.patches(jobs)                            # (n_jobs, n_receptors)
    S.crit(z)                                  # any terrain that differs from the base on some open cells
    S.patch(r, c, dz, cont=True), S.pstar()    # continuous critical depth (m), for derivative experiments
Run with: uv run --with numpy --with scipy --with numba python ...
"""
import numpy as np
from numba import njit

INF = np.inf


@njit(cache=True)
def _recv(i, zf, of, om, first, ny, nx):
    """Steepest-descent receiver of cell i (same tie rules as fillmodel._labels: up, down, left, right; strict)."""
    if not of[i]: return i
    if om[i]: return first
    r = i // nx; c = i - r * nx
    m = INF; k = i
    if r > 0 and of[i - nx] and zf[i - nx] < m: m = zf[i - nx]; k = i - nx
    if r < ny - 1 and of[i + nx] and zf[i + nx] < m: m = zf[i + nx]; k = i + nx
    if c > 0 and of[i - 1] and zf[i - 1] < m: m = zf[i - 1]; k = i - 1
    if c < nx - 1 and of[i + 1] and zf[i + 1] < m: m = zf[i + 1]; k = i + 1
    return k if m < zf[i] else i


@njit(cache=True)
def _labels_edges(z, openm, outm, first):
    """Receivers, basin labels (leaf 0 = outlet, others by pit position), and the lowest pass per pair of adjacent basins."""
    ny, nx = z.shape; n = ny * nx
    zf = z.ravel(); of = openm.ravel(); om = outm.ravel()
    rec = np.empty(n, np.int64)
    for i in range(n): rec[i] = _recv(i, zf, of, om, first, ny, nx)
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
    pit = np.full(nb, -1, np.int64)
    for i in range(n):
        if of[i] and root[i] == i and i != first: pit[lid[i]] = i
    lab = np.full(n, -1, np.int64)
    for i in range(n):
        if of[i]: lab[i] = lid[root[i]]
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
            s = ((key * 40503) ^ (key >> 9)) & mask
            while True:
                e = slot[s]
                if e < 0:
                    if ne == emax:
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
    eo = o1[o2]                                            # order by (w, a, b), as fillmodel._edges
    return rec, lab, nb, pit, ekey[:ne][eo] // nb, ekey[:ne][eo] % nb, ew[:ne][eo]


@njit(cache=True)
def _flooded(P, D, vreq, areastar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, leaving):
    """Is the pond n* at or above the receptor threshold at rain P?  Arrays are indexed by depth d on the root path
    (path[0] = root, path[D] = n*): pAc/pCc = area/capacity of path[d], pAo/pCo = of its sibling, pT = leaf position that
    receives the sibling's overflow (inside path[d]), pLo/pHi = leaf interval of path[d].
    j0[d] caches the deepest depth whose node still contains that leaf (-2 = not yet computed);
    leaving[e] collects overflow whose target leaf is in path[e-1] but not in path[e]."""
    for d in range(1, D + 2): leaving[d] = 0.0
    X = 0.0                                               # overflow held in leaves of the current path node
    for d in range(1, D + 1):
        Xo = leaving[d]; Xc = X - Xo
        Tc = P * pAc[d] + Xc; To = P * pAo[d] + Xo
        if Tc > pCc[d]:
            return True                                   # on-path child full: merged, or held at its pass, above the threshold
        if To > pCo[d]:
            Eo = To - pCo[d]
            if Tc + Eo > pCc[d]:
                return True                               # sibling's overflow fills it too: merged above the threshold
            e = j0[d]
            if e == -2:
                p = pT[d]; a = d; st = 1                  # path[a] contains p; gallop down, then bisect
                b = d + 1
                while b <= D and p >= pLo[b] and p < pHi[b]:
                    a = b; st *= 2; b = a + st
                if b > D: b = D + 1
                while b - a > 1:                          # path[a] contains p, path[b] does not (or b = D+1)
                    mid = (a + b) // 2
                    if p >= pLo[mid] and p < pHi[mid]: a = mid
                    else: b = mid
                e = a; j0[d] = e
            leaving[e + 1] += Eo; Xc += Eo                # leaving[D+1] is never read: that overflow stays inside n*
        X = Xc
    return P * areastar + X >= vreq


@njit(cache=True)
def _walks(nstar, vreq, NB, parent, ca, cb, la, lb, cap, area, nleaf, hasout, PG, guess, want_cont):
    """Critical grid index per receptor by root-path walks and bisection (see module docstring)."""
    N = len(parent); nr = len(nstar); nP = len(PG)
    lo = np.zeros(N, np.int64); hi = np.zeros(N, np.int64); hi[N - 1] = NB; dep = np.zeros(N, np.int64)
    for m in range(N - 1, NB - 1, -1):
        a = ca[m]; b = cb[m]
        lo[a] = lo[m]; hi[a] = lo[m] + nleaf[a]; lo[b] = hi[a]; hi[b] = hi[m]
        dep[a] = dep[m] + 1; dep[b] = dep[m] + 1
    out = np.full(nr, nP, np.int64); cont = np.full(nr, INF)
    M = N + 2
    pAc = np.empty(M); pCc = np.empty(M); pAo = np.empty(M); pCo = np.empty(M)
    pT = np.empty(M, np.int64); pLo = np.empty(M, np.int64); pHi = np.empty(M, np.int64); j0 = np.empty(M, np.int64); lv = np.empty(M)
    pnode = np.full(M, -1, np.int64)
    nwalk = 0; last = -1; D = 0; Dprev = -1
    key = np.empty(nr, np.int64)
    for q in range(nr): key[q] = lo[nstar[q]] * N + nstar[q]
    qo = np.argsort(key)                                   # neighbours in leaf order share most of their root path
    for qq in range(nr):
        q = qo[qq]; ns = nstar[q]; vq = vreq[q]
        if hasout[ns] or vq == INF: continue
        if ns != last:
            last = ns; D = dep[ns]; d = D; c = ns
            while d >= 1 and not (d <= Dprev and pnode[d] == c):
                m = parent[c]
                if ca[m] == c:
                    o = cb[m]; tgt = la[m]
                else:
                    o = ca[m]; tgt = lb[m]
                pAc[d] = area[c]; pCc[d] = cap[c]; pAo[d] = area[o]; pCo[d] = cap[o]
                pT[d] = lo[tgt]; pLo[d] = lo[c]; pHi[d] = hi[c]; j0[d] = -2; pnode[d] = c
                d -= 1; c = m
            for t in range(1, d + 1):                      # shared prefix: cached exits stay valid only if strictly above the fork
                if j0[t] >= d: j0[t] = -2
            Dprev = D
        ar = area[ns]
        a = -1; b = nP                                     # a: highest index known dry; b: lowest known flooded (nP = none)
        g = guess[q]
        if g >= 0 and g < nP:
            nwalk += 1
            if _flooded(PG[g], D, vq, ar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, lv):
                b = g
                if g > 0:
                    nwalk += 1
                    if _flooded(PG[g - 1], D, vq, ar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, lv): b = g - 1
                    else: a = g - 1
            else:
                a = g
        if b == nP:
            nwalk += 1
            if _flooded(PG[nP - 1], D, vq, ar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, lv): b = nP - 1
            else: continue
        while b - a > 1:
            mid = (a + b) // 2; nwalk += 1
            if _flooded(PG[mid], D, vq, ar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, lv): b = mid
            else: a = mid
        out[q] = b
        if want_cont:
            p0 = PG[b - 1] if b > 0 else 0.0; p1 = PG[b]
            for it in range(30):
                pm = 0.5 * (p0 + p1)
                if _flooded(pm, D, vq, ar, pAc, pCc, pAo, pCo, pT, pLo, pHi, j0, lv): p1 = pm
                else: p0 = pm
            cont[q] = p1
    return out, cont, nwalk


@njit(cache=True)
def _crit(z, openm, outm, first, pcells, rcf, thr, PG, guess, zoff, want_cont, vmax,
          rec, lab, nb0, pit0, area0, es_a, es_b, es_w, ek0, ekpos, cz0, clab0, cord, pos0, lptr, lcells,
          mark, idw, skipc, skipe, max_relabel):
    """One patch.  z: patched terrain; pcells: flat indices of the open cells that differ from the base terrain.
    rec, lab, mark, idw, skipc, skipe are work arrays holding baseline state; they are restored before returning.
    Returns (grid index of critical depth per receptor, continuous P*, number of basins, path walks, status);
    status -1 = too many cells changed basin, caller should use the full rebuild."""
    ny, nx = z.shape; n = ny * nx
    zf = z.ravel(); of = openm.ravel(); om = outm.ravel()
    npc = len(pcells)
    # ---- A. receivers can only change in the patch and its 4-neighbours ----
    cand = np.empty(5 * npc + 1, np.int64); ncand = 0
    for t in range(npc):
        x = pcells[t]; r = x // nx; c = x - r * nx
        for d in range(5):
            y = x
            if d == 1:
                if r == 0: continue
                y = x - nx
            elif d == 2:
                if r == ny - 1: continue
                y = x + nx
            elif d == 3:
                if c == 0: continue
                y = x - 1
            elif d == 4:
                if c == nx - 1: continue
                y = x + 1
            if of[y] and mark[y] == 0:
                mark[y] = 1; cand[ncand] = y; ncand += 1
    qmax = max_relabel + ncand + 8
    queue = np.empty(qmax, np.int64); nq = 0
    rcx = np.empty(ncand + 1, np.int64); rco = np.empty(ncand + 1, np.int64); nrc = 0
    for t in range(ncand):
        x = cand[t]; mark[x] = 0
        nrv = _recv(x, zf, of, om, first, ny, nx)
        if nrv != rec[x]:
            rcx[nrc] = x; rco[nrc] = rec[x]; nrc += 1; rec[x] = nrv
    # ---- B. cells upstream of a changed receiver may change basin ----
    status = 0
    for t in range(nrc):
        x = rcx[t]
        if mark[x] != 2:
            mark[x] = 2; queue[nq] = x; nq += 1
    qh = 0
    while qh < nq and status == 0:
        x = queue[qh]; qh += 1
        r = x // nx; c = x - r * nx
        for d in range(4):
            if d == 0:
                if r == 0: continue
                y = x - nx
            elif d == 1:
                if r == ny - 1: continue
                y = x + nx
            elif d == 2:
                if c == 0: continue
                y = x - 1
            else:
                if c == nx - 1: continue
                y = x + 1
            if of[y] and mark[y] != 2 and rec[y] == x and y != x:
                if nq == qmax:
                    status = -1; break
                mark[y] = 2; queue[nq] = y; nq += 1
    if status < 0:
        for t in range(nq): mark[queue[t]] = 0
        for t in range(nrc): rec[rcx[t]] = rco[t]
        return np.zeros(1, np.int64), np.zeros(1), 0, 0, -1
    NB = nb0; nvan = 0
    pit = np.empty(nb0 + nq + 1, np.int64); pit[:nb0] = pit0
    for t in range(nrc):
        if rco[t] == rcx[t]: nvan += 1                     # a baseline pit that now drains somewhere
    for t in range(nq):                                    # new basin id of every affected cell (memoised chase)
        x = queue[t]
        if idw[x] >= 0: continue
        j = x
        while mark[j] == 2 and idw[j] < 0 and rec[j] != j: j = rec[j]
        if mark[j] != 2: lid = lab[j]
        elif idw[j] >= 0: lid = idw[j]
        else:
            lid = NB; pit[NB] = j; NB += 1                 # a new pit
        j = x
        while mark[j] == 2 and idw[j] < 0 and rec[j] != j:
            nxt = rec[j]; idw[j] = lid; j = nxt
        if mark[j] == 2: idw[j] = lid
    area = np.zeros(2 * NB - 1); area[:nb0] = area0
    lcx = np.empty(nq + 1, np.int64); lco = np.empty(nq + 1, np.int64); nlc = 0
    for t in range(nq):
        x = queue[t]; nl = idw[x]; idw[x] = -1; mark[x] = 0
        if nl != lab[x]:
            lcx[nlc] = x; lco[nlc] = lab[x]; nlc += 1
            area[lab[x]] -= 1.0; area[nl] += 1.0; lab[x] = nl
    # ---- C. dirty cells (height or basin changed) leave the main cell stream and form a second one ----
    dc = np.empty(npc + nlc, np.int64); ndc = 0
    for t in range(nlc):
        x = lcx[t]; idw[x] = lco[t]; mark[x] = 3; dc[ndc] = x; ndc += 1      # idw now holds the OLD label of relabelled cells
    for t in range(npc):
        x = pcells[t]
        if mark[x] != 3:
            mark[x] = 3; dc[ndc] = x; ndc += 1
    dz_ = np.empty(ndc)
    for t in range(ndc):
        skipc[pos0[dc[t]]] = True; dz_[t] = zf[dc[t]]
    do = np.argsort(dz_)
    # ---- D. passes between pairs of basins that touch a dirty cell are recomputed; the rest are reused ----
    bits = 6
    while (1 << bits) < 32 * ndc + 64: bits += 1
    H = 1 << bits; hmask = H - 1
    slot = np.full(H, -1, np.int64)
    pk = np.empty(8 * ndc + 8, np.int64); npk = 0
    for t in range(ndc):
        x = dc[t]; r = x // nx; c = x - r * nx
        ox = idw[x] if idw[x] >= 0 else lab[x]; nxl = lab[x]
        for d in range(4):
            if d == 0:
                if r == 0: continue
                y = x - nx
            elif d == 1:
                if r == ny - 1: continue
                y = x + nx
            elif d == 2:
                if c == 0: continue
                y = x - 1
            else:
                if c == nx - 1: continue
                y = x + 1
            if not of[y]: continue
            oy = idw[y] if idw[y] >= 0 else lab[y]; nyl = lab[y]
            for v in range(2):
                if v == 0:
                    A = ox; B = oy
                else:
                    A = nxl; B = nyl
                if A == B: continue
                if A > B:
                    A, B = B, A
                key = A * NB + B
                s = ((A * 40503 + B * 9973) ^ (key >> 7)) & hmask
                while True:
                    e = slot[s]
                    if e < 0:
                        slot[s] = npk; pk[npk] = key; npk += 1; break
                    if pk[e] == key: break
                    s = (s + 1) & hmask
    nea = np.empty(npk + 1, np.int64); neb = np.empty(npk + 1, np.int64); nw = np.empty(npk + 1); nne = 0
    ske = np.empty(npk + 1, np.int64); nske = 0
    ne0 = len(es_w)
    for t in range(npk):
        A = pk[t] // NB; B = pk[t] - A * NB
        if A < nb0 and B < nb0:                            # drop the baseline pass of this pair, if it had one
            key0 = A * nb0 + B
            a = 0; b = ne0
            while a < b:
                mid = (a + b) // 2
                if ek0[mid] < key0: a = mid + 1
                else: b = mid
            if a < ne0 and ek0[a] == key0:
                skipe[ekpos[a]] = True; ske[nske] = ekpos[a]; nske += 1
        S = A; O = B
        if area[B] < area[A]:
            S = B; O = A
        mw = INF
        for src in range(2):
            if src == 0:
                if S >= nb0: continue
                i0 = lptr[S]; i1 = lptr[S + 1]
            else:
                i0 = 0; i1 = nlc
            for ii in range(i0, i1):
                x = lcells[ii] if src == 0 else lcx[ii]
                if lab[x] != S: continue
                r = x // nx; c = x - r * nx
                if r > 0 and lab[x - nx] == O:
                    w = zf[x] if zf[x] > zf[x - nx] else zf[x - nx]
                    if w < mw: mw = w
                if r < ny - 1 and lab[x + nx] == O:
                    w = zf[x] if zf[x] > zf[x + nx] else zf[x + nx]
                    if w < mw: mw = w
                if c > 0 and lab[x - 1] == O:
                    w = zf[x] if zf[x] > zf[x - 1] else zf[x - 1]
                    if w < mw: mw = w
                if c < nx - 1 and lab[x + 1] == O:
                    w = zf[x] if zf[x] > zf[x + 1] else zf[x + 1]
                    if w < mw: mw = w
        if mw < INF:
            if pit[A] > pit[B]:
                A, B = B, A
            j = nne                                        # insertion sort by (w, pit a, pit b)
            while j > 0 and (nw[j - 1] > mw or (nw[j - 1] == mw and (pit[nea[j - 1]] > pit[A] or (pit[nea[j - 1]] == pit[A] and pit[neb[j - 1]] > pit[B])))):
                nea[j] = nea[j - 1]; neb[j] = neb[j - 1]; nw[j] = nw[j - 1]; j -= 1
            nea[j] = A; neb[j] = B; nw[j] = mw; nne += 1
    # ---- receptor thresholds ----
    nr = len(rcf)
    T = np.empty(nr)
    for q in range(nr): T[q] = zf[rcf[q]] + thr
    qo = np.argsort(T)
    nstar = np.zeros(nr, np.int64); vreq = np.full(nr, INF)
    # ---- E. the sweep: Kruskal over passes + running (count, sum z) of cells below the sweep height per component ----
    N = 2 * NB - 1
    parent = np.full(N, -1, np.int64)
    ca = np.full(N, -1, np.int64); cb = np.full(N, -1, np.int64); la = np.full(N, -1, np.int64); lb = np.full(N, -1, np.int64)
    cap = np.full(N, INF); hasout = np.zeros(N, np.bool_); hasout[0] = True
    nleaf = np.ones(N, np.int64)
    uf = np.arange(NB); node_of = np.arange(NB)
    cnt = np.zeros(NB); sm = np.zeros(NB)
    deadc = np.zeros(NB, np.bool_); deadc[0] = True        # component can never fill within PG (has the outlet, or capacity > all the rain)
    deadl = np.zeros(NB, np.bool_); deadl[0] = True        # leaf known to sit in such a component: its cells are skipped
    k = NB; ie = 0; ie2 = 0; ic = 0; ip = 0; iq = 0; nc = len(cz0)
    while True:
        while ie < ne0 and skipe[ie]: ie += 1
        he1 = es_w[ie] if ie < ne0 else INF
        he2 = nw[ie2] if ie2 < nne else INF
        while ic < nc and (skipc[ic] or deadl[clab0[ic]]): ic += 1
        hc1 = cz0[ic] if ic < nc else INF
        hc2 = dz_[do[ip]] if ip < ndc else INF
        hq = T[qo[iq]] if iq < nr else INF
        he = he1 if he1 <= he2 else he2
        hc = hc1 if hc1 <= hc2 else hc2
        if he <= hc and he <= hq:
            if he == INF: break
            usemain = he1 < he2
            if he1 == he2:
                a1 = pit[es_a[ie]]; a2 = pit[nea[ie2]]
                usemain = a1 < a2 or (a1 == a2 and pit[es_b[ie]] < pit[neb[ie2]])
            if usemain:
                u0 = es_a[ie]; v0 = es_b[ie]; w = he1; ie += 1
            else:
                u0 = nea[ie2]; v0 = neb[ie2]; w = he2; ie2 += 1
            u = u0; ru = u
            while uf[ru] != ru: ru = uf[ru]
            while uf[u] != ru:
                t = uf[u]; uf[u] = ru; u = t
            v = v0; rv = v
            while uf[rv] != rv: rv = uf[rv]
            while uf[v] != rv:
                t = uf[v]; uf[v] = rv; v = t
            if ru == rv: continue
            a = node_of[ru]; b = node_of[rv]
            ca[k] = a; cb[k] = b; la[k] = u0; lb[k] = v0
            parent[a] = k; parent[b] = k
            da = deadc[ru]; db = deadc[rv]; tot = 0.0
            if not da:
                cv = cnt[ru] * (w - zoff) - sm[ru]
                if cv <= vmax:
                    cap[a] = cv; tot += cv
                else: da = True
            if not db:
                cv = cnt[rv] * (w - zoff) - sm[rv]
                if cv <= vmax:
                    cap[b] = cv; tot += cv
                else: db = True
            area[k] = area[a] + area[b]; nleaf[k] = nleaf[a] + nleaf[b]; hasout[k] = hasout[a] or hasout[b]
            uf[ru] = rv; node_of[rv] = k; cnt[rv] += cnt[ru]; sm[rv] += sm[ru]
            deadc[rv] = da or db or tot > vmax
            k += 1
        elif hc <= hq:
            if hc1 <= hc2:
                lim = he if he < hc2 else hc2             # run of main-stream cells strictly below every other stream head
                if hq < lim: lim = hq
                while True:
                    u = clab0[ic]
                    if not (skipc[ic] or deadl[u]):
                        ru = u
                        while uf[ru] != ru: ru = uf[ru]
                        if uf[u] != ru: uf[u] = ru
                        if deadc[ru]: deadl[u] = True
                        else:
                            cnt[ru] += 1.0; sm[ru] += cz0[ic] - zoff
                    ic += 1
                    if ic >= nc or cz0[ic] >= lim: break
                continue
            else:
                i = dc[do[ip]]; ip += 1; u = lab[i]; zc = hc2
                if deadl[u]: continue
            u0 = u; ru = u
            while uf[ru] != ru: ru = uf[ru]
            while uf[u] != ru:
                t = uf[u]; uf[u] = ru; u = t
            if deadc[ru]: deadl[u0] = True
            else:
                cnt[ru] += 1.0; sm[ru] += zc - zoff
        else:
            q = qo[iq]; iq += 1
            u = lab[rcf[q]]; ru = u
            while uf[ru] != ru: ru = uf[ru]
            nstar[q] = node_of[ru]
            if not deadc[ru]: vreq[q] = cnt[ru] * (T[q] - zoff) - sm[ru]
    for leaf in range(1, NB):                              # enclosed courtyards (and emptied basins): tied to the outlet at 1e9, never spill
        ru = leaf
        while uf[ru] != ru: ru = uf[ru]
        rv = 0
        while uf[rv] != rv: rv = uf[rv]
        if ru == rv: continue
        a = node_of[ru]; b = node_of[rv]
        ca[k] = a; cb[k] = b; la[k] = leaf; lb[k] = 0
        parent[a] = k; parent[b] = k
        area[k] = area[a] + area[b]; nleaf[k] = nleaf[a] + nleaf[b]; hasout[k] = True
        uf[ru] = rv; node_of[rv] = k; k += 1
    # ---- restore the baseline work arrays ----
    for t in range(ndc):
        x = dc[t]; mark[x] = 0; idw[x] = -1; skipc[pos0[x]] = False
    for t in range(nlc): lab[lcx[t]] = lco[t]
    for t in range(nrc): rec[rcx[t]] = rco[t]
    for t in range(nske): skipe[ske[t]] = False
    out, cont, nwalk = _walks(nstar, vreq, NB, parent, ca, cb, la, lb, cap, area, nleaf, hasout, PG, guess, want_cont)
    return out, cont, NB - nvan, nwalk, nlc


class Sweep:
    def __init__(self, z, open_, rc, PG=None, thr=0.10, max_relabel=20000):
        self.z0 = np.ascontiguousarray(z, np.float64); self.open = np.ascontiguousarray(open_, np.bool_)
        ny, nx = self.z0.shape; n = ny * nx
        edge = np.zeros_like(self.open); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
        self.outlet = np.ascontiguousarray(edge & self.open)
        self.first = int(np.flatnonzero(self.outlet.ravel())[0])
        self.rc = np.asarray(rc); self.rcf = (self.rc[:, 0] * nx + self.rc[:, 1]).astype(np.int64)
        assert self.open.ravel()[self.rcf].all(), "receptor on a closed cell"
        self.PG = np.linspace(0.0, 0.130, 261) if PG is None else np.asarray(PG, np.float64)
        self.thr = float(thr); self.max_relabel = int(max_relabel)
        # baseline structures, built once and reused by every patch
        rec, lab, nb, pit, ea, eb, ew = _labels_edges(self.z0, self.open, self.outlet, self.first)
        self.nb = int(nb)
        opf = np.flatnonzero(self.open.ravel()); zo = self.z0.ravel()[opf]
        o = np.argsort(zo, kind="stable")
        cord = opf[o].astype(np.int64); cz0 = np.ascontiguousarray(zo[o]); clab0 = np.ascontiguousarray(lab[cord])
        pos0 = np.full(n, -1, np.int64); pos0[cord] = np.arange(len(cord))
        ol = np.argsort(lab[opf], kind="stable"); lcells = opf[ol].astype(np.int64)
        area0 = np.bincount(lab[opf], minlength=nb).astype(np.float64)
        lptr = np.r_[0, np.cumsum(area0.astype(np.int64))].astype(np.int64)
        ek = ea * nb + eb; ko = np.argsort(ek)
        self.zoff = float(zo.min()); self.vmax = float(self.PG[-1] * len(opf) * (1 + 1e-6))
        self._base = (rec, lab, self.nb, pit, area0, np.ascontiguousarray(ea), np.ascontiguousarray(eb), np.ascontiguousarray(ew),
                      np.ascontiguousarray(ek[ko]), ko.astype(np.int64), cz0, clab0, cord, pos0, lptr, lcells,
                      np.zeros(n, np.int8), np.full(n, -1, np.int64), np.zeros(len(cord), np.bool_), np.zeros(len(ew), np.bool_))
        self._zw = self.z0.copy(); self._none = np.empty(0, np.int64)
        self.guess = np.full(len(self.rcf), -1, np.int64)
        self.last_nb = self.nb; self.last_nwalk = 0; self.last_relabelled = 0
        idx = self._run(self.z0, self._none, False)[0]
        self.idx0 = idx; self.guess = np.where(idx < len(self.PG), idx, -1).astype(np.int64)
        self.c0 = self._mm(idx)

    @classmethod
    def from_files(cls, terrain="shared/terrain_512.npz", receptors="shared/receptors.npz", **kw):
        T = np.load(terrain)
        return cls(T["z"].astype(np.float64), T["open"], np.load(receptors)["rc"], **kw)

    def _mm(self, idx):
        nP = len(self.PG)
        return np.where(idx < nP, self.PG[np.minimum(idx, nP - 1)] * 1e3, np.inf)

    def _run(self, z, changed, cont, max_relabel=None):
        mr = self.max_relabel if max_relabel is None else max_relabel
        idx, ct, nbp, nwalk, st = _crit(z, self.open, self.outlet, self.first, changed, self.rcf, self.thr, self.PG, self.guess,
                                        self.zoff, cont, self.vmax, *self._base, mr)
        if st < 0:                                         # very large re-routing: lift the cap (still exact, just slower)
            return self._run(z, changed, cont, z.size)
        self.last_nb, self.last_nwalk, self.last_relabelled = int(nbp), int(nwalk), int(st)
        return idx, ct

    def crit(self, z, changed=None, cont=False):
        """Critical depths (mm; or continuous, m, if cont) for a terrain z that differs from the base terrain on a set
        of open cells (flat indices `changed`, found by comparison if omitted).  Cost grows with the number of changed cells."""
        z = np.ascontiguousarray(z, np.float64)
        if changed is None: changed = np.flatnonzero((z != self.z0).ravel() & self.open.ravel())
        idx, ct = self._run(z, np.asarray(changed, np.int64), cont)
        return ct if cont else self._mm(idx)

    def pstar(self, z=None, changed=None):
        """Continuous critical depth (m) per receptor (inf if above PG[-1])."""
        return self.crit(self.z0 if z is None else z, changed, cont=True)

    def patch(self, r, c, dz, rad=2, cont=False):
        """Critical depths (mm) with open cells of rows r-rad..r+rad, cols c-rad..c+rad moved by dz (m)."""
        z = self._zw; ny, nx = z.shape; r, c, rad = int(r), int(c), int(rad)
        r0, r1, c0, c1 = max(r - rad, 0), min(r + rad + 1, ny), max(c - rad, 0), min(c + rad + 1, nx)
        rr, cc = np.nonzero(self.open[r0:r1, c0:c1])
        ch = ((rr + r0) * nx + (cc + c0)).astype(np.int64)
        z.ravel()[ch] = self.z0.ravel()[ch] + dz
        try:
            idx, ct = self._run(z, ch, cont)
        finally:
            z.ravel()[ch] = self.z0.ravel()[ch]
        return ct if cont else self._mm(idx)

    def patches(self, jobs):
        """jobs: (n, 4) rows (r, c, dz, rad).  Returns (n, n_receptors) critical depths in mm."""
        out = np.empty((len(jobs), len(self.rcf)))
        for i, (r, c, dz, rad) in enumerate(jobs):
            out[i] = self.patch(int(r), int(c), float(dz), int(rad))
        return out
