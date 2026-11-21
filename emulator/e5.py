"""E5: few-label fine-tuning of a pretrained operator.
Poseidon itself is BLOCKED here: the checkpoint is reachable (camlab-ethz/Poseidon-T answered HTTP 200) but it is a
21M-parameter Swin model and needs the scOT code base plus 128x128 multi-channel inputs; with the Apple GPU shared with another job and granted
late in the session, wiring it in and fine-tuning 3 arms x 3 label counts x 3 seeds did not fit the remaining budget. So this runs the brief's fallback:
pretrain a tiny operator on other harness data (valley + basin terrains), fine-tune on few fractal labels.
Arm B (equation residual, no labels) and arm C (hybrid) are NOT RUN: every emulator here outputs peak and final depth
maps, not a time-resolved state, so the local-inertial residual cannot be evaluated on its output.   python e5.py"""
import os, numpy as np, torch
import harness as H

COUNTS = (20, 100, 500)


def job(s):
    multi = H.dataset("train_multi", H.TRAIN_KINDS, 4096, seed=2); frac = H.train_fractal(); ts = H.testsets()
    keep = multi["kind"] != 0                                             # pretraining never sees a fractal terrain
    pre, tp = H.fit_unet({k: multi[k][keep] for k in ("z", "K", "hmax", "hfin")}, s, w=H.SMALL, epochs=40, lr=H.LR_SMALL)
    r = dict(pretrain_s=tp, pretrain_labels=int(keep.sum()), zero_shot=H.evaluate(H.predictor(pre), ts))
    for n in COUNTS:
        sub = {k: frac[k][:n] for k in ("z", "K", "hmax", "hfin")}; ep = max(1, 600 * 32 // n)             # 600 gradient steps at every label count
        ft = H.UNet(w=H.SMALL); ft.load_state_dict(pre.state_dict()); ft.train()
        t = H.train(ft, H.feats(sub["z"], sub["K"]), H.targets(sub), epochs=ep, lr=5e-4, seed=s)
        sc, t2 = H.fit_unet(sub, s, w=H.SMALL, epochs=ep, lr=H.LR_SMALL)
        r[f"finetune_{n}"] = dict(H.evaluate(H.predictor(ft.eval()), ts), train_s=t); r[f"scratch_{n}"] = dict(H.evaluate(H.predictor(sc), ts), train_s=t2)
        print(f"[E5] seed {s} n={n}: fine-tuned T_iid {r[f'finetune_{n}']['T_iid']['rmse_all']:.4f}  scratch {r[f'scratch_{n}']['T_iid']['rmse_all']:.4f}", flush=True)
        if (s, n) == (0, 100):
            H.plot_examples("E5", H.predictor(ft), ts["T_iid"]); r["_timing"] = H.time_per_storm(H.predictor(ft), ts["T_iid"])
    return r


if __name__ == "__main__":
    per = H.pmap(job, list(H.SEEDS)); timing = per[0].pop("_timing")
    H.save("E5", dict(per_seed=per, summary=H.summarise(per), timing=timing, poseidon="BLOCKED: checkpoint reachable (HTTP 200) but not downloaded or run; integration + fine-tuning did not fit the time left on a shared GPU",
                      arms_B_C="NOT RUN: no time-resolved emulator output to take an equation residual of",
                      note="fallback arm A only: small U-Net (0.12M) pretrained on valley+basin, fine-tuned on 20/100/500 fractal labels, vs the same net from scratch"))
