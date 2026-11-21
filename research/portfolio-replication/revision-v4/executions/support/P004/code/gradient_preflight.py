#!/usr/bin/env python3
"""P004 minimal synthetic-data gradient preflight.

Uses the AUTHOR'S UNMODIFIED code (e2e.Net, DataLoad.synthetic_exp,
PortfolioClasses.SlidingWindow) from the frozen commit
b5e299ad7748468bc39e3e711eceee809143c648. Does NOT read any author
trained-model / result cache (cache/exp5/*.pkl). Does NOT change the
algorithm: for each of the six Exp5 configs we do exactly one forward
pass, one backward pass and one Adam step on the FIRST training window.

The purpose is purely a structural preflight: shapes, finite gradients,
nonzero update, weight simplex, y_perf window length (perf_period=13 ->
14 forward realizations). NO Table 11 / Figure 7 target is computed.

Run (from this directory):
  PYTHONPATH=<repo> python gradient_preflight.py > ../logs/gradient_preflight.stdout.log 2> ../logs/gradient_preflight.stderr.log
"""
import json
import os
import sys
import traceback

REPO = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/execution/P004_repo"
SUPPORT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import numpy as np
import torch
import e2edro.DataLoad as dl
import e2edro.e2edro as e2e
import e2edro.PortfolioClasses as pc

torch.set_num_threads(1)

PERF_LOSS = "sharpe_loss"
PRED_LOSS_FACTOR = 0.5
PRISK = "p_var"
DR_LAYER = "hellinger"
N_X, N_Y = 5, 10
N_OBS, N_TOT = 100, 1200
SPLIT = [0.7, 0.3]
PERF_PERIOD = 13
LR = 0.005
CACHE = os.path.join(SUPPORT, "results", "grad_cache")
os.makedirs(CACHE, exist_ok=True)

CONFIGS = [
    ("nom_linear", "nominal", "linear", 2000),
    ("dr_linear",  "hellinger", "linear", 2000),
    ("nom_2layer", "nominal", "2layer", 3000),
    ("dr_2layer",  "hellinger", "2layer", 3000),
    ("nom_3layer", "nominal", "3layer", 4000),
    ("dr_3layer",  "hellinger", "3layer", 4000),
]


def main():
    out = {
        "batch": "CO-REP-20261120-02",
        "paper": "P004",
        "preflight": "minimal_synthetic_gradient",
        "author_commit": "b5e299ad7748468bc39e3e711eceee809143c648",
        "environment": {"python": sys.version.split()[0], "torch": torch.__version__,
                        "numpy": np.__version__},
        "config": {"n_x": N_X, "n_y": N_Y, "n_obs": N_OBS, "n_tot": N_TOT,
                   "split": SPLIT, "perf_period": PERF_PERIOD,
                   "pred_loss_factor": PRED_LOSS_FACTOR, "lr": LR,
                   "opt_layer_dr": DR_LAYER, "prisk": PRISK},
        "rule": "author code unmodified; first training window only; one fwd/bwd/Adam step; no author result cache read",
        "models": {},
        "status": "UNKNOWN",
    }

    # Synthetic DGP via author's function (seed 123 internally).
    X, Y = dl.synthetic_exp(n_x=N_X, n_y=N_Y, n_obs=N_OBS, n_tot=N_TOT, split=SPLIT)
    sw = pc.SlidingWindow(X.train(), Y.train(), N_OBS, PERF_PERIOD)
    x, y, y_perf = sw[0]
    x, y, y_perf = x.squeeze(), y.squeeze(), y_perf.squeeze()
    out["dgp"] = {
        "function": "e2edro.DataLoad.synthetic_exp",
        "seed": 123,
        "X_train_shape": list(X.train().values.shape),
        "Y_train_shape": list(Y.train().values.shape),
        "first_window_x_shape": list(x.shape),
        "first_window_y_shape": list(y.shape),
        "first_window_y_perf_shape": list(y_perf.shape),
        "note": "perf_period=13 but SlidingWindow uses index+n_obs : index+n_obs+perf_period+1 => 14 forward realizations (author snapshot; not silently changed)",
        "n_windows_total": len(sw),
    }
    print("DGP:", out["dgp"])

    loss_fn = e2e.lf.sharpe_loss if hasattr(e2e, "lf") else None
    import e2edro.LossFunctions as lf
    perf_loss = getattr(lf, PERF_LOSS)
    mse = torch.nn.MSELoss()

    for name, opt_layer, pred_model, seed in CONFIGS:
        rec = {"opt_layer": opt_layer, "pred_model": pred_model, "set_seed": seed}
        try:
            net = e2e.e2e_net(N_X, N_Y, N_OBS, prisk=PRISK, train_pred=True,
                              train_gamma=True, train_delta=True,
                              pred_model=pred_model, set_seed=seed,
                              opt_layer=opt_layer, perf_loss=PERF_LOSS,
                              perf_period=PERF_PERIOD,
                              pred_loss_factor=PRED_LOSS_FACTOR,
                              cache_path=CACHE).double()
            net.train()
            before = {n: p.detach().clone() for n, p in net.named_parameters()}
            rec["init"] = {n: round(p.item(), 6) for n, p in net.named_parameters() if p.numel() == 1}

            optimizer = torch.optim.Adam(net.parameters(), lr=LR)
            optimizer.zero_grad()
            z_star, y_hat = net(x, y)
            loss = (perf_loss(z_star, y_perf) +
                    (PRED_LOSS_FACTOR / N_Y) * mse(y_hat, y_perf[0]))
            loss.backward()

            grad_norms = {}
            all_finite = True
            for n, p in net.named_parameters():
                if p.grad is None:
                    grad_norms[n] = None
                else:
                    grad_norms[n] = float(p.grad.norm().item())
                    all_finite = all_finite and bool(torch.isfinite(p.grad).all().item())
            rec["grad_norms"] = grad_norms
            rec["all_grads_finite"] = all_finite
            rec["loss"] = float(loss.item())

            optimizer.step()
            for n, p in net.named_parameters():
                if n in ("gamma", "delta"):
                    p.data.clamp_(0.0001)
            update_l2 = {}
            for n, p in net.named_parameters():
                update_l2[n] = float((p.detach() - before[n]).norm().item())
            rec["update_l2"] = update_l2
            rec["any_update_nonzero"] = any(v > 0 for v in update_l2.values())
            rec["z_sum"] = float(z_star.sum().item())
            rec["z_min"] = float(z_star.min().item())
            rec["z_max_abs_err_vs_1"] = float(abs(rec["z_sum"] - 1.0))
            rec["status"] = "PASS" if (all_finite and rec["any_update_nonzero"]
                                        and rec["z_max_abs_err_vs_1"] < 1e-6
                                        and rec["z_min"] > -1e-6) else "CHECK"
            print(name, "status", rec["status"], "grads_finite", all_finite,
                  "z_sum", rec["z_sum"], "loss", rec["loss"])
        except Exception as e:
            rec["status"] = "ERROR"
            rec["error"] = repr(e)
            rec["traceback"] = traceback.format_exc()
            print(name, "ERROR", repr(e))
        out["models"][name] = rec

    statuses = [m["status"] for m in out["models"].values()]
    out["status"] = ("PASS" if all(s == "PASS" for s in statuses)
                     else ("PARTIAL" if any(s == "PASS" for s in statuses) else "ERROR"))
    out["target_results"] = {"Table11_Fig7": "NOT_RUN", "economic_conclusion": "NOT_ASSESSED"}
    path = os.path.join(SUPPORT, "results", "gradient_preflight.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("OVERALL", out["status"])
    return 0 if out["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
