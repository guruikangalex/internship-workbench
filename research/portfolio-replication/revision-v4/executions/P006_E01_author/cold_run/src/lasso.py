"""PC-lasso shrinkage and KNS-style elastic-net selection.
Ported from shrinkage/lasso_for_pc_regression.py."""
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from src.upsa import UPSA
from src.shrinkage import do_lw


def _sharpe(ret):
    return np.sqrt(12) * np.mean(ret, axis=0) / np.std(ret, axis=0)


def pc_lasso(inv_pc_var, eigenvectors, r_ins, alpha_list, return_zero=False):
    """Soft-threshold PC loadings (lasso on the PC regression)."""
    pc_mean = eigenvectors.T @ np.mean(r_ins, axis=0).T
    pc_loading = pc_mean * inv_pc_var
    active = [(np.abs(pc_loading) > alpha * inv_pc_var) for alpha in alpha_list]
    pc_lasso_list = [np.sign(pc_loading) * (np.abs(pc_loading) - alpha * inv_pc_var) * a
                     for alpha, a in zip(alpha_list, active)]
    if return_zero:
        return pc_lasso_list, active
    return pc_lasso_list


def lasso_cv(returns, eigenvectors, shrunk_inv_eigenvalues, alpha_list, z_grid, k_fold):
    """Cross-validate the L1 penalty for UPSA/Ridge PC regressions."""
    T, P = returns.shape
    kf = KFold(n_splits=k_fold, shuffle=False)
    comp = shrunk_inv_eigenvalues.keys()
    oos_ret = {c_: np.zeros((T, len(alpha_list))) for c_ in comp}
    pc_lasso_selected = {}
    inv_eigs = {}

    for train_index, test_index in kf.split(returns):
        r_ins, r_oos = returns[train_index], returns[test_index]
        eigenvalues_fold, eigenvectors_fold = UPSA.smart_eigenvalue_decomposition_covariance(r_ins)
        pc_oos = r_oos @ eigenvectors_fold

        inv_eigs["LW"] = 1 / do_lw(returns=r_ins, eigenvalues=eigenvalues_fold,
                                   eigenvectors=eigenvectors_fold)[1]
        upsa = UPSA(z_list=z_grid).fit(returns=r_ins)
        inv_eigs["UPSA"] = upsa.get_inv_eigenvalues_upsa()
        inv_eigs["Ridge"] = upsa.get_inv_eigenvalues_ridge()

        for c_ in comp:
            pc_lasso_list = pc_lasso(inv_eigs[c_], eigenvectors_fold, r_ins, alpha_list)
            oos_ret[c_][test_index, :] = np.array([l_ @ pc_oos.T for l_ in pc_lasso_list]).T

    best_alpha = {}
    for c_ in comp:
        mean_lasso = np.mean(oos_ret[c_], axis=0)
        std_lasso = np.std(oos_ret[c_], axis=0)
        sharpe_pca = np.where(std_lasso == 0, 0, mean_lasso / std_lasso)
        best_idx = np.argmax(sharpe_pca)
        best_alpha[c_] = alpha_list[best_idx]
        pc_lasso_selected[c_] = pc_lasso(shrunk_inv_eigenvalues[c_], eigenvectors,
                                         returns, [alpha_list[best_idx]])[0]
    return pc_lasso_selected, best_alpha


def lasso_pca_cv_kns(returns, eigenvectors, eigenvalues, alpha_list, z_grid, k_fold, eig_folds):
    """KNS-style joint (alpha, z) cross-validation; returns scaled PC loadings."""
    kf = KFold(n_splits=k_fold, shuffle=False)
    columns = [(a, z) for a in range(len(alpha_list)) for z in range(len(z_grid))]
    fold_voc = pd.DataFrame(index=np.arange(len(returns)),
                            columns=pd.MultiIndex.from_tuples(columns), dtype=float)

    for i, (train_index, test_index) in enumerate(kf.split(returns)):
        r_ins, r_oos = returns[train_index], returns[test_index]
        eigenvalues_fold, eigenvectors_fold = eig_folds[i]
        pc_oos = r_oos @ eigenvectors_fold
        for z_idx in range(len(z_grid)):
            pc_lasso_list = pc_lasso(1 / (eigenvalues_fold + z_grid[z_idx]),
                                     eigenvectors_fold, r_ins, alpha_list)
            for a_index in range(len(alpha_list)):
                fold_voc.loc[test_index, (a_index, z_idx)] = pc_lasso_list[a_index] @ pc_oos.T

    best_a_z = _sharpe(fold_voc).idxmax()
    pc_lasso_selected, zeros = pc_lasso(1 / (eigenvalues + z_grid[best_a_z[1]]),
                                        eigenvectors, returns,
                                        [alpha_list[best_a_z[0]]], return_zero=True)
    scaling = np.sum((eigenvalues + z_grid[best_a_z[1]]) * zeros[0]) / np.sum(eigenvalues)
    return pc_lasso_selected[0] * scaling
