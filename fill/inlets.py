"""Synthetic road gullies: in every 25 m square that contains road, the lowest road cell is an inlet. All inlets together can take
what a uniform loss of loss_mm_h over all open ground could. Returns inlet cells (n,2) and the rate per inlet cell in m/s."""
import numpy as np
def inlets(road, z, op, loss_mm_h, win=25):
    cells = []
    for r in range(0, z.shape[0], win):
        for c in range(0, z.shape[1], win):
            m = road[r:r + win, c:c + win] & op[r:r + win, c:c + win]
            if m.any(): zz = np.where(m, z[r:r + win, c:c + win], np.inf); k = np.unravel_index(zz.argmin(), zz.shape); cells.append((r + k[0], c + k[1]))
    cells = np.array(cells); return cells, loss_mm_h / 3.6e6 * op.sum() / len(cells)
if __name__ == "__main__":
    t = np.load("shared/terrain_512.npz"); c, f = inlets(t["road"], t["z"], t["open"], 12.0); print("inlets %d; each takes up to %.1f litres per second; total %.2f m3/s" % (len(c), f * 1000, f * len(c)))
