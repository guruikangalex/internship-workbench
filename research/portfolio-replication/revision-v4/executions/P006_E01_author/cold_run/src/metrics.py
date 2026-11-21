"""Portfolio evaluation metrics. Ported from helpers/usefull_functions.py
(and the alpha helpers used by the bar plots)."""
import numpy as np
import pandas as pd


def sharpe(df, axis=0):
    """Annualized (monthly) Sharpe ratio."""
    return np.sqrt(12) * np.mean(df, axis) / np.std(df, axis)


def rescale_for_sdf(opt_port):
    """Map an optimal-portfolio return series to its SDF: 1 - b*R."""
    return 1 - opt_port * (np.mean(opt_port, axis=0) / np.mean(opt_port ** 2, axis=0))


def turnover_fun(weights):
    """Time-series and cross-sectional turnover (%) per method.
    `weights` is a dict {method: DataFrame(index=date, columns=factors)}."""
    ts_turnover, cs_turnover = {}, {}
    for method, w in weights.items():
        gross = w.abs().sum(axis=1)
        diff_abs_sum = w.diff().abs().sum(axis=1)
        denom_prev = gross.shift()
        turnover_ts = 0.5 * diff_abs_sum / denom_prev
        turnover_ts.iloc[0] = 0.0
        ts_turnover[method] = 100 * turnover_ts

        num_cs = w.diff().abs().sum(axis=0)
        denom_cs = w.abs().shift().sum(axis=0)
        cs_turnover[method] = 100 * 0.5 * num_cs / denom_cs
    return ts_turnover, cs_turnover
