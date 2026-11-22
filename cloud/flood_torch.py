"""PyTorch port of solver/flood.py (same local-inertial scheme, float32, theta = 1). Only what the packed map needs:
a (B,H,W) batch of terrains, per-member rain series and adaptive time step, peak depth at receptors, mass balance."""
import time, numpy as np, torch, torch.nn.functional as Fn
G = 9.81
@torch.inference_mode()
def simulate(z, open_, dx, rc, profile, profile_dt_s, loss_mm_h, t_end_s, alpha=0.7, h_floor=0.05, check=10, n_manning=0.015, device="cuda"):
    profile = np.atleast_2d(np.asarray(profile, np.float64)); B, K = profile.shape; H, W = z.shape[-2:]; n2 = n_manning ** 2
    loss = np.broadcast_to(np.asarray(loss_mm_h, np.float64), (B,)); tend = np.broadcast_to(np.asarray(t_end_s, np.float64), (B,))
    eff = np.concatenate([np.maximum(profile - loss[:, None], 0.) / 3.6e6, np.zeros((B, 1))], 1); op = np.asarray(open_, bool); n_rain = float(op.sum())
    T = lambda a, dt=torch.float32: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=device)
    zz = T(np.asarray(z, np.float32)); zfx = torch.maximum(zz[..., :, :-1], zz[..., :, 1:]); zfy = torch.maximum(zz[..., :-1, :], zz[..., 1:, :])
    fx = T(op[:, :-1] & op[:, 1:], torch.bool); fy = T(op[:-1] & op[1:], torch.bool); rm = T(op.astype(np.float32))
    e = np.zeros((H, W), bool); e[0] = e[-1] = e[:, 0] = e[:, -1] = True; edge = T((e & op).astype(np.float32))
    P = lambda a, t, b, l, r: Fn.pad(a, (l, r, t, b)); zero = torch.zeros((), device=device); one = torch.ones((), device=device)
    def step(h, qx, qy, peak, bacc, rate, dt):
        eta = zz + h
        hfx = torch.clamp_min(torch.maximum(eta[:, :, :-1], eta[:, :, 1:]) - zfx, 0.); hfy = torch.clamp_min(torch.maximum(eta[:, :-1], eta[:, 1:]) - zfy, 0.)
        wx = (hfx > 1e-4) & fx; wy = (hfy > 1e-4) & fy; sx = torch.where(wx, hfx, one); sy = torch.where(wy, hfy, one)
        qx = torch.where(wx, (qx - G * sx * dt * (eta[:, :, 1:] - eta[:, :, :-1]) / dx) / (1 + G * dt * n2 * qx.abs() / sx ** (7 / 3)), zero)
        qy = torch.where(wy, (qy - G * sy * dt * (eta[:, 1:] - eta[:, :-1]) / dx) / (1 + G * dt * n2 * qy.abs() / sy ** (7 / 3)), zero)
        qxp = qx.clamp_min(0); qxm = (-qx).clamp_min(0); qyp = qy.clamp_min(0); qym = (-qy).clamp_min(0)
        out = (P(qxp, 0, 0, 0, 1) + P(qxm, 0, 0, 1, 0) + P(qyp, 0, 1, 0, 0) + P(qym, 1, 0, 0, 0)) * dt / dx
        f = torch.clamp_max(h / (out + 1e-12), 1.)
        qx = qxp * f[:, :, :-1] - qxm * f[:, :, 1:]; qy = qyp * f[:, :-1] - qym * f[:, 1:]
        div = P(qx, 0, 0, 0, 1) - P(qx, 0, 0, 1, 0) + P(qy, 0, 1, 0, 0) - P(qy, 1, 0, 0, 0)
        h = (h - div * dt / dx).clamp_min(0.) + rate * dt * rm
        hs = h.clamp_min(1e-9); bo = torch.minimum(h, edge * dt / dx * hs * torch.sqrt(G * hs)); h = h - bo
        return h, qx, qy, torch.maximum(peak, h), bacc + bo.sum(dim=(1, 2))
    h = torch.zeros((B, H, W), device=device); qx = torch.zeros((B, H, W - 1), device=device); qy = torch.zeros((B, H - 1, W), device=device); peak = h; bacc = torch.zeros(B, device=device)
    t = np.zeros(B); rain_in = np.zeros(B); bnd = np.zeros(B); dt = np.full(B, alpha * dx / np.sqrt(G * h_floor)); ar = np.arange(B); rc = np.asarray(rc); t0 = time.time(); i = 0
    while (t < tend - 1e-9).any():
        d = np.minimum(dt, tend - t).clip(0); r = eff[ar, np.minimum((t / profile_dt_s).astype(int), K)]
        h, qx, qy, peak, bacc = step(h, qx, qy, peak, bacc, T(r.astype(np.float32)).reshape(B, 1, 1), T(d.astype(np.float32)).reshape(B, 1, 1))
        rain_in += r.astype(np.float32).astype(np.float64) * d.astype(np.float32) * n_rain; t += d; i += 1
        if i % check == 0:
            hmax = h.amax(dim=(1, 2)).cpu().numpy(); bnd += bacc.double().cpu().numpy(); bacc = torch.zeros(B, device=device)
            if not np.isfinite(hmax).all(): raise FloatingPointError(f"non-finite depth at step {i}")
            dt = alpha * dx / np.sqrt(G * np.maximum(hmax, h_floor))
    bnd += bacc.double().cpu().numpy(); stored = h.double().sum(dim=(1, 2)).cpu().numpy(); pk = peak[:, T(rc[:, 0], torch.long), T(rc[:, 1], torch.long)].cpu().numpy()
    if device == "cuda": torch.cuda.synchronize()
    return dict(peak_depth=pk, imbalance=(rain_in - stored - bnd) / np.maximum(rain_in, 1e-12), wall_s=time.time() - t0, steps=i)
