"""Benchmark shrinkage estimators: Ledoit-Wolf nonlinear (NLS), Ledoit-Wolf
linear, and PCA cross-validation. Ported verbatim from the original repo
(shrinkage/lw_nls.py, lw_linear.py, pca_cv.py)."""
import numpy as np
from numpy import matlib as ml
from sklearn.model_selection import KFold
from sklearn.covariance import LedoitWolf


# ------------------------------------------------------------ Ledoit-Wolf NLS
def do_lw(returns, eigenvalues, eigenvectors, remove_pc_pert=0):
    T, P = returns.shape
    normalized_mean = np.mean(returns, axis=0)
    effective_rank = min(T, P)
    num_pc_removed = int(effective_rank * remove_pc_pert)
    eigval = eigenvalues[num_pc_removed:]
    eigvec = eigenvectors[:, num_pc_removed:]

    if P <= T:
        P = len(eigval)
    else:
        T = len(eigval)

    lw_eigenvalues, effective_shrink = lw_nonlinear_shrinkage(lam=eigval, T=T, P=P)
    projected_mean_vec = eigvec.T @ normalized_mean

    lw_weights = np.squeeze((eigvec * (1 / lw_eigenvalues.reshape(1, -1))) @ projected_mean_vec)

    if P > len(eigenvalues):
        if effective_shrink is None:
            effective_shrink = min(eigenvalues)
        lw_weights = lw_weights + (normalized_mean - eigvec @ projected_mean_vec) / effective_shrink

    return lw_weights, lw_eigenvalues


def lw_nonlinear_shrinkage(lam, T, P):
    """Analytical nonlinear shrinkage of covariance eigenvalues (Ledoit-Wolf)."""
    L = ml.repmat(lam.T, np.minimum(P, T), 1).T
    h = np.power(T, -1 / 3.)
    H = h * L.T
    x = (L - L.T) / H
    f_tilde = (3 / 4. / np.sqrt(5)) * np.mean(np.maximum(1 - x ** 2. / 5., 0) / H, 1)
    hf_temp = (-3 / 10 / np.pi) * x + (3 / 4. / np.sqrt(5) / np.pi) * (1 - x ** 2. / 5.) * np.log(
        np.abs((np.sqrt(5) - x) / (np.sqrt(5) + x)))
    hf_temp[np.abs(x) == np.sqrt(5)] = (-3 / 10 / np.pi) * x[np.abs(x) == np.sqrt(5)]
    hf_tilde = np.mean(hf_temp / H, 1)

    if P <= T:
        d_tilde = lam / ((np.pi * (P / T) * lam * f_tilde) ** 2
                         + (1 - (P / T) - np.pi * (P / T) * lam * hf_tilde) ** 2)
        return d_tilde, None
    else:
        hf_tilde0 = (1 / np.pi) * (3 / 10. / h ** 2 + 3 / 4. / np.sqrt(5) / h * (1 - 1 / 5. / h ** 2)
                                   * np.log((1 + np.sqrt(5) * h) / (1 - np.sqrt(5) * h))) * np.mean(1 / lam)
        z = 1 / (np.pi * (P - T) / T * hf_tilde0)
        d_tilde = lam / (np.pi ** 2 * lam ** 2. * (f_tilde ** 2 + hf_tilde ** 2))
        return d_tilde, z


# --------------------------------------------------------- Ledoit-Wolf linear
def do_lw_linear(eigenvalues, eigenvectors, returns):
    T, P = returns.shape
    mu = np.sum(eigenvalues) / P
    lwl_shrinkage = LedoitWolf().fit(returns).shrinkage_
    lwl_effective_shrinkage = mu * lwl_shrinkage
    lwl_eigenvalues = lwl_effective_shrinkage + (1 - lwl_shrinkage) * eigenvalues

    normalized_mean = np.mean(returns, axis=0)
    projected_mean_vec = eigenvectors.T @ normalized_mean
    lwl_weights = np.squeeze((eigenvectors * (1 / lwl_eigenvalues.reshape(1, -1))) @ projected_mean_vec)

    if P > len(eigenvalues):
        lwl_weights = lwl_weights + (normalized_mean - eigenvectors @ projected_mean_vec) / lwl_effective_shrinkage

    return lwl_weights, lwl_eigenvalues


# ------------------------------------------------------------------- PCA-CV
def pca_cv(returns, k_folds=5, sort_by="variance", eig_folds=None, eig_full=None):
    """K-fold CV over the number of principal components for a PCA-Markowitz
    strategy; returns (weights, best_pc)."""
    T, P = returns.shape
    max_pc = int(np.floor(T * (k_folds - 1) / k_folds))
    max_pc = max(min(max_pc, P), 1)

    cross_val_pca = np.zeros((T, max_pc))
    kf = KFold(n_splits=k_folds, shuffle=False)
    for fold_i, (train_idx, test_idx) in enumerate(kf.split(returns)):
        r_ins, r_oos = returns[train_idx], returns[test_idx]
        if eig_folds is not None:
            e_val_fold, e_vec_fold = eig_folds[fold_i]
        else:
            e_val_fold, e_vec_fold = _smart_eig(r_ins)
        sorted_indices = _get_sorted_indices(e_val_fold, e_vec_fold, r_ins, sort_by)
        for p_ in range(1, max_pc + 1):
            top_p = sorted_indices[-p_:]
            w_pca = _pca_markowitz(e_val_fold[top_p], e_vec_fold[:, top_p], r_ins)
            cross_val_pca[test_idx, p_ - 1] = r_oos @ w_pca

    mean_pca = np.mean(cross_val_pca, axis=0)
    std_pca = np.std(cross_val_pca, axis=0)
    sharpe_pca = np.where(std_pca == 0, 0, mean_pca / std_pca)
    best_pc = int(np.argmax(sharpe_pca)) + 1

    if eig_full is not None:
        e_val_full, e_vec_full = eig_full
    else:
        e_val_full, e_vec_full = _smart_eig(returns)
    sorted_full = _get_sorted_indices(e_val_full, e_vec_full, returns, sort_by)
    top_p_full = sorted_full[-best_pc:]
    best_eigvals = e_val_full[top_p_full]
    best_weights = _pca_markowitz(best_eigvals, e_vec_full[:, top_p_full], returns)
    best_weights = best_weights * (np.sum(best_eigvals) / np.sum(e_val_full))
    return best_weights, best_pc


def _get_sorted_indices(eigvals, eigvecs, returns, sort_by):
    if sort_by == "variance":
        return np.arange(len(eigvals))
    elif sort_by == "sharpe":
        pc_returns = returns @ eigvecs
        mu = np.mean(pc_returns, axis=0)
        std = np.std(pc_returns, axis=0)
        sr = np.where(std == 0, 0, mu / std)
        return np.argsort(np.abs(sr) * np.sqrt(np.maximum(eigvals, 0)))
    raise ValueError(f"sort_by must be 'variance' or 'sharpe', got '{sort_by}'")


def _pca_markowitz(eigvals_subset, eigvecs_subset, returns):
    mu = np.mean(returns, axis=0)
    proj_mu = eigvecs_subset.T @ mu
    return (eigvecs_subset / eigvals_subset.reshape(1, -1)) @ proj_mu


def _smart_eig(returns):
    T, P = returns.shape
    if P > T:
        cov = returns @ returns.T / T
        eigvals, eigvecs = np.linalg.eigh(cov)
        eigvecs = returns.T @ eigvecs * (eigvals ** -0.5).reshape(1, -1) / np.sqrt(T)
    else:
        cov = returns.T @ returns / T
        eigvals, eigvecs = np.linalg.eigh(cov)
    return eigvals, eigvecs
