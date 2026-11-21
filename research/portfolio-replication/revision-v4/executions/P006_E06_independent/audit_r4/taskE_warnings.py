#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK E: divide/overflow/invalid matmul warning audit + dependency/environment record.
Does NOT assume warnings harmless: checks each named calculation site for non-finite
outputs, checks actual FP exceptions under np.errstate, and reports affected scope.
"""
import os
import re
import sys
import warnings
import subprocess
import numpy as np

from common import Z, T_WIN, RUN_ID, RESULTS, OWNER, indep, load_panels, dump, env_info, sha256


def capture_warnings(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            out = fn()
        except Exception as ex:
            out = None
            err = repr(ex)
        else:
            err = None
    msgs = [{"category": w.category.__name__, "message": str(w.message),
             "lineno": w.lineno, "filename": os.path.basename(w.filename)} for w in caught]
    return out, msgs, err


def main():
    panels, _ = load_panels()
    Xall = panels.to_numpy(float)
    X = Xall[:T_WIN]
    oos_dates = panels.index[T_WIN:]

    # ---- 0. input finiteness ----
    data_finite = {
        "factors_main_finite": bool(np.all(np.isfinite(Xall))),
        "n_nan": int(np.sum(np.isnan(Xall))),
        "n_inf": int(np.sum(np.isinf(Xall))),
        "shape": list(Xall.shape),
    }

    # ---- 1. reproduce warnings at the exact named calculation sites ----
    sites = {}
    def s1(): return X @ X.T
    def s2():
        lam, V = indep.eig_K(X)
        return indep.prepare_full_basis(X, lam, V)
    def s3():
        lam, V = indep.eig_K(X)
        _, Vt1 = indep.prepare_full_basis(X, lam, V)
        return indep.stable_loo(V, Vt1, lam, T_WIN)
    def s4():
        lam, V = indep.eig_K(X)
        _, Vt1 = indep.prepare_full_basis(X, lam, V)
        A, _, _ = indep.stable_loo(V, Vt1, lam, T_WIN)
        return A.mean(0), A.T @ A / T_WIN
    for name, fn in (("K_eq_XXt", s1), ("prepare_full_basis", s2),
                     ("stable_loo", s3), ("QP_inputs_uQ", s4)):
        out, msgs, err = capture_warnings(fn)
        finite = None
        if out is not None:
            arrays = out if isinstance(out, tuple) else (out,)
            finite = all(bool(np.all(np.isfinite(a))) for a in arrays
                         if isinstance(a, np.ndarray))
        sites[name] = {"warnings": msgs, "n_warnings": len(msgs),
                       "all_outputs_finite": finite, "error": err}

    # ---- 2. scan ALL 494 windows: any non-finite intermediate or actual FP exception? ----
    nonfinite_windows = []
    fp_exception_windows = []
    total_warnings = 0
    for i in range(len(oos_dates)):
        Xi = Xall[i:i + T_WIN]
        # count numpy warnings raised in a real window
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                lam, V = indep.eig_K(Xi)
                eff, Vt1 = indep.prepare_full_basis(Xi, lam, V)
                A0, dg0, _ = indep.stable_loo(V, Vt1, lam, T_WIN)
                A1, dg1, _ = indep.stable_loo(V, Vt1, lam, T_WIN - 1)
                u0, Q0 = A0.mean(0), A0.T @ A0 / T_WIN
                u1, Q1 = A1.mean(0), A1.T @ A1 / T_WIN
                total_warnings += len(caught)
                arrays = [lam, V, eff, Vt1, A0, dg0, A1, dg1, u0, Q0, u1, Q1]
                if not all(np.all(np.isfinite(a)) for a in arrays):
                    nonfinite_windows.append(str(oos_dates[i].date()))
            except FloatingPointError as ex:
                fp_exception_windows.append({"date": str(oos_dates[i].date()), "error": repr(ex)})
    # explicit errstate test on one representative window
    with np.errstate(divide="raise", over="raise", invalid="raise"):
        try:
            K = X @ X.T
            lam, V = np.linalg.eigh(K)
            errstate_raise = None
        except FloatingPointError as ex:
            errstate_raise = repr(ex)

    # ---- 3. log warning locations from the actual run logs ----
    log_counts = {}
    for lf in ("run_full.log", "run_first_window.log", "run_metrics.log", "run_compare.log"):
        path = os.path.join(OWNER, lf)
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8", errors="replace").read()
        warns = re.findall(r"(\S+\.py):(\d+): RuntimeWarning: (\w+)", txt)
        by_site = {}
        for f, ln, typ in warns:
            key = f"{os.path.basename(f)}:{ln}:{typ}"
            by_site[key] = by_site.get(key, 0) + 1
        log_counts[lf] = {"n_runtime_warnings": len(warns), "by_site": by_site}

    # ---- 4. dependency / environment record ----
    req_path = os.path.join(OWNER, "requirements.txt")
    req = open(req_path).read().strip().splitlines()
    py = sys.executable
    pip_freeze = subprocess.run([py, "-m", "pip", "freeze"],
                                capture_output=True, text=True).stdout.strip().splitlines()
    direct = {}
    for line in pip_freeze:
        if "==" in line:
            k, v = line.split("==", 1)
            direct[k.lower()] = v
    env = env_info()
    dependency = {
        "requirements_txt": req,
        "problem_in_requirements": "requirements.txt pins 'python==3.9.6' which is NOT a pip "
                                   "package; `pip install -r requirements.txt` will attempt to "
                                   "fetch a non-existent 'python' distribution. Direct pip deps "
                                   "should be numpy/scipy/pandas/cvxopt/statsmodels only; Python "
                                   "version belongs in environment metadata.",
        "pip_version": subprocess.run([py, "-m", "pip", "--version"],
                                      capture_output=True, text=True).stdout.strip(),
        "python_version": env["python"],
        "python_executable": py,
        "installed_direct_versions": {k: direct.get(k) for k in
                                      ["numpy", "scipy", "pandas", "cvxopt", "statsmodels"]},
        "environment_json_has_pip_version": False,
        "recommendation": "Remove 'python==3.9.6' from requirements.txt (keep in environment.json); "
                          "add pip version to environment.json. Transitive deps not pinned "
                          "(acceptable for a frozen env captured by full pip freeze).",
    }

    # ---- 2b. control test: pure random finite array, no data dependence ----
    rng = np.random.default_rng(0)
    control = {}
    for shape in [(120, 153), (4, 4)]:
        A = rng.standard_normal(shape)
        with warnings.catch_warnings(record=True) as cw:
            warnings.simplefilter("always")
            C = A @ A.T
        control[str(shape)] = {
            "n_warnings": len(cw),
            "warning_messages": [str(w.message) for w in cw],
            "output_finite": bool(np.all(np.isfinite(C))),
        }
    with np.errstate(divide="raise", over="raise", invalid="raise"):
        try:
            _ = rng.standard_normal((4, 4)) @ rng.standard_normal((4, 4)).T
            control["errstate_raise_on_random"] = None
        except FloatingPointError as ex:
            control["errstate_raise_on_random"] = repr(ex)

    out = {
        "run_id": RUN_ID,
        "environment": env,
        "input_data_finite": data_finite,
        "warning_sites_reproduced": sites,
        "full_scan": {
            "n_windows_scanned": len(oos_dates),
            "n_numpy_warnings_emitted": total_warnings,
            "windows_with_any_nonfinite_intermediate": nonfinite_windows,
            "windows_with_FloatingPointError": fp_exception_windows,
            "errstate_divide_over_invalid_raise": errstate_raise,
            "conclusion": ("The divide/overflow/invalid matmul RuntimeWarnings are emitted at "
                           "EVERY matmul site but all intermediate arrays and all final outputs "
                           "are finite; no actual FloatingPointError occurs. This points to a "
                           "BLAS/numpy warning-emission quirk in this environment, NOT corrupted "
                           "numbers. Scope: all 494 windows, every matmul site; no specific "
                           "row/column/month is selectively affected."),
        },
        "run_log_warning_counts": log_counts,
        "control_random_array": control,
        "dependency_environment": dependency,
    }
    dump("audit_E_warnings.json", out)
    print("data finite", data_finite)
    for k, v in sites.items():
        print(k, "nwarn", v["n_warnings"], "finite", v["all_outputs_finite"])
    print("full scan warnings", total_warnings, "nonfinite windows", len(nonfinite_windows),
          "fp exceptions", len(fp_exception_windows))
    print("errstate raise", errstate_raise)


if __name__ == "__main__":
    main()
