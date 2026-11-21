"""Absorption in the fill model: sinks (a volume that must fill before a leaf basin holds any water) and point injections.
FillSink.run(P, sink=None, inject=None):
  sink    per-leaf volume in m3 (length nb). Water arriving at the leaf's pit fills the sink first; ground height is unchanged.
  inject  (leaf_index_per_column, volume_per_column): extra water added at one leaf in each storm column."""
import numpy as np
from fillmodel import FillModel

class FillSink(FillModel):
    def run(self, P, sink=None, inject=None):
        P = np.asarray(P, np.float64); S = len(P); nb, N = self.nb, self.N
        ca, cb, la, lb, area, lo, hi, h = self.ca, self.cb, self.la, self.lb, self.area, self.lo, self.hi, self.h
        ss = np.zeros(N)
        if sink is not None:
            ss[:nb] = sink
            for n in range(nb, N): ss[n] = ss[ca[n]] + ss[cb[n]]
        cap = self.cap + ss                                  # a node spills only after its sinks are full too
        fen = np.zeros((nb + 1, S)); any_inj = False
        def add(pos, val):
            i = pos + 1
            while i <= nb: fen[i] += val; i += i & -i
        def pref(i):
            s = np.zeros(S)
            while i > 0: s += fen[i]; i -= i & -i
            return s
        if inject is not None:
            leaf, vol = inject; cols = np.arange(S); i = self.lo[np.asarray(leaf)] + 1; v = np.broadcast_to(np.asarray(vol, np.float64), (S,))
            while True:
                m = i <= nb
                if not m.any(): break
                np.add.at(fen, (i[m], cols[m]), v[m]); i = np.where(m, i + (i & -i), i)
            any_inj = True
        X = lambda n: (pref(hi[n]) - pref(lo[n])) if any_inj else 0.0
        sub = np.zeros((N, S), bool); lev = np.full((N, S), -np.inf, np.float32)
        for n in range(N - 1, nb - 1, -1):
            a, b = ca[n], cb[n]; act = ~sub[n]
            if not act.any():
                sub[a] = sub[b] = True; lev[a] = lev[b] = lev[n]; continue
            Ta = P * area[a] + X(a); Tb = P * area[b] + X(b)
            fa, fb = Ta > cap[a], Tb > cap[b]
            Ea = np.where(fa & ~fb, Ta - cap[a], 0.0) if np.isfinite(cap[a]) else np.zeros(S)
            Eb = np.where(fb & ~fa, Tb - cap[b], 0.0) if np.isfinite(cap[b]) else np.zeros(S)
            merged = act & ((fa & fb) | (fa & ~fb & (Tb + Ea > cap[b])) | (fb & ~fa & (Ta + Eb > cap[a])))
            onlya = act & fa & ~merged; onlyb = act & fb & ~merged
            if merged.any():
                L = self._level(n, Ta + Tb - self.V0[n] - ss[n])
                for c in (a, b): sub[c] |= merged; lev[c] = np.where(merged, L, lev[c])
            if onlya.any():
                sub[a] |= onlya; lev[a] = np.where(onlya, h[n], lev[a]); add(lo[lb[n]], np.where(onlya, Ea, 0.0)); any_inj = True
            if onlyb.any():
                sub[b] |= onlyb; lev[b] = np.where(onlyb, h[n], lev[b]); add(lo[la[n]], np.where(onlyb, Eb, 0.0)); any_inj = True
            inh = ~act
            if inh.any():
                for c in (a, b): sub[c] |= inh; lev[c] = np.where(inh, lev[n], lev[c])
        LL = np.empty((nb, S), np.float32); self.last_inflow = np.zeros((nb, S), np.float32) if S <= 64 else None
        for l in range(nb):
            if l == 0: LL[l] = -np.inf; continue
            T = P * area[l] + X(l)
            if self.last_inflow is not None: self.last_inflow[l] = T
            LL[l] = np.where(sub[l], lev[l], self._level(l, np.maximum(np.minimum(T, cap[l]) - ss[l], 0.0)))
        return LL, P * area[0] + (X(0) if any_inj else 0.0)
