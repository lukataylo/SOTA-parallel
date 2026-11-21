import time, sys, numpy as np, jax, jax.numpy as jnp
from floodlab import *
dx = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
st = make_street(1, dx)
z = jnp.array(st["z"]); print("grid", z.shape)
sim, nsteps, dt = make_sim(st, 300.)
f = jax.jit(sim)
R = 60e-3 / 120; T = 120.
t0 = time.time(); d, h, acc = f(z, R, T); d.block_until_ready(); print("compile+run", time.time() - t0)
t0 = time.time(); d, h, acc = f(z, R, T); d.block_until_ready(); t1 = time.time() - t0
print("run s", t1, "Mcell-steps/s", z.size * nsteps / t1 / 1e6, "steps", nsteps, "dt", dt)
a2 = dx * dx
print("mass: in %.3f m3, drains %.3f, boundary %.3f, stored %.3f, imbalance %.2e" % (
    acc[0] * a2, acc[1] * a2, acc[2] * a2, h.sum() * a2, float((acc[0] - acc[1] - acc[2] - h.sum()) / acc[0])))
print("door max depths cm", np.round(np.array(d) * 100, 1))
print("thresholds t cm", [round(q["t"] * 100, 1) for q in st["doors"]])
# storms sweep: fraction flooded
for P in (20, 40, 60, 90, 130):
    d, _, _ = f(z, P * 1e-3 / 120, 120.); print(P, "mm ->", int((np.array(d) > 0.01).sum()), "doors flooded")
# gradient check
obj = lambda z: sim(z, R, T)[0].sum()
gf = jax.jit(jax.grad(obj))
t0 = time.time(); g = gf(z); g.block_until_ready(); print("grad compile+run", time.time() - t0)
t0 = time.time(); g = gf(z); g.block_until_ready(); print("grad run", time.time() - t0, "=", (time.time() - t0) / t1, "fwd")
r = np.random.default_rng(0); v = jnp.array(r.normal(0, 1, z.shape).astype(np.float32)) * jnp.array(st["rainmask"])
jf = jax.jit(obj)
for eps in (1e-3, 3e-4):
    fd = (jf(z + eps * v) - jf(z - eps * v)) / (2 * eps)
    print("eps", eps, "FD", float(fd), "AD", float((g * v).sum()))
