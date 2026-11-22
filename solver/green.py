"""Green drainage interventions as inputs to flood_sink.simulate_sink: grass and street trees.

Each intervention is a set of cells plus four per-cell numbers: instant storage s1 (m), slow storage s2 (m),
the rate the slow storage fills at f (m/s), and Manning's n. Ground height is never changed.

Values (docs/ABSORPTION.md and research_notes/.../absorption_parameters_and_geology.md):
  grass      3 mm depression storage, 15 mm topsoil at 10 mm/h, n = 0.03. The subgrade is London Clay, so no
             sustained infiltration is credited. The 3 / 15 / 10 figures are NOT sourced; n is the EA 2013 value.
  tree       a 2 x 2 m pit holding 3.9 m3 (15 m3 of structural soil at 26% voids: an UPPER BOUND, assumes empty
             voids and an inlet that delivers), plus 1 mm of canopy storage over the 5 x 5 m around it.
The uniform 12 mm/h loss stays on everywhere, which double-counts slightly on grass: grass results are upper bounds.
"""
import numpy as np

GRASS = dict(s1=0.003, s2=0.015, f=10 / 3.6e6, n=0.03)
TREE = dict(pit_m3=3.9, canopy=0.001)
N0 = 0.015


def empty(shape):
    """Layers for 'no intervention'."""
    z = lambda: np.zeros(shape, np.float32)
    return dict(s1=z(), s2=z(), f=z(), n=np.full(shape, N0, np.float32))


def add_grass(L, mask):
    """Turn the cells of `mask` into grass."""
    L["s1"][mask] += GRASS["s1"]; L["s2"][mask] += GRASS["s2"]; L["f"][mask] = GRASS["f"]; L["n"][mask] = GRASS["n"]
    return L


def add_trees(L, sites, open_):
    """Plant a tree at each (row, col): the pit is the 2 x 2 cells from there, the canopy the 5 x 5 around it."""
    for r, c in sites:
        L["s1"][r:r + 2, c:c + 2] += TREE["pit_m3"] / 4
        L["s1"][max(r - 1, 0):r + 4, max(c - 1, 0):c + 4] += TREE["canopy"]
    L["s1"] *= open_
    return L


def grass_blocks(open_, road, min_cells=20):
    """5 x 5 m blocks that could be grassed: at least min_cells open cells that are not road. Returns (n,2) block indices."""
    ok = (open_ & ~road)[:510, :510].reshape(102, 5, 102, 5).sum((1, 3)) >= min_cells
    ok[[0, -1]] = False; ok[:, [0, -1]] = False
    return np.argwhere(ok)


def blocks_mask(blocks, open_, road):
    m = np.zeros(open_.shape, bool)
    for i, j in blocks: m[5 * i:5 * i + 5, 5 * j:5 * j + 5] = True
    return m & open_ & ~road


def tree_sites(open_, road):
    """Kerb sites: 2 x 2 open blocks on the 2 m lattice that hold both road and pavement. Returns (n,2) top-left cells."""
    v = lambda a: a[2:510, 2:510].reshape(254, 2, 254, 2)
    ok = v(open_).all((1, 3)) & v(road).any((1, 3)) & (~road & open_)[2:510, 2:510].reshape(254, 2, 254, 2).any((1, 3))
    return np.argwhere(ok) * 2 + 2


def spaced(sites, order, k, gap=10.0):
    """First k sites in `order` that are at least `gap` m from every site already taken."""
    out = []
    for q in order:
        s = sites[q]
        if all(np.hypot(*(s - o)) >= gap for o in out):
            out.append(s)
            if len(out) == k: break
    return np.array(out)
