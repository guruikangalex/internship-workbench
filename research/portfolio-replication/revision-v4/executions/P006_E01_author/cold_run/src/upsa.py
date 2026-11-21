"""Universal Portfolio Shrinkage (UPSA).

One canonical class used identically by every figure (empirical and
simulation). The ensemble loadings are the CONSTRAINED (non-negative) Markowitz
solution on the leave-one-out return matrix (`self.upsa`); `get_upsa_weights`
applies the trace `scale`. Bit-identical to the original empirical class
(`shrinkage/upsa_no_scalling.py`) in-process. Only numpy + cvxopt are required.
"""
import numpy as np
from cvxopt import matrix, solvers

solvers.options["show_progress"] = False


class UPSA:
    def __init__(self, z_list=None, eigenvalues=None, eigenvectors=None):
        self.z_list = z_list
        self.eigenvalues = eigenvalues
        self.eigenvectors = eigenvectors
        self.estimated_loo_rets = None
        self.eff_port = None
        self.best_z = None
        self.upsa = None  # constrained (non-negative) ensemble loadings

    # ------------------------------------------------------------------ fit
    def fit(self, returns, eig_range=10):
        if self.eigenvalues is None or self.eigenvectors is None:
            self.eigenvalues, self.eigenvectors = \
                self.smart_eigenvalue_decomposition_covariance(returns)

        if self.z_list is None or isinstance(self.z_list, int):
            n = 10 if self.z_list is None else self.z_list
            self.z_list = np.logspace(
                np.log10(np.min(self.eigenvalues) / eig_range),
                np.log10(eig_range * np.max(self.eigenvalues)),
                n,
            )

        self.estimated_loo_rets, self.eff_port = \
            self._leave_one_out_and_eff_port_estimators(
                returns, self.eigenvalues, self.eigenvectors)

        self.best_z, self.upsa = self.compute_upsa(self.estimated_loo_rets)
        return self

    # ------------------------------------------------------- weight getters
    def get_upsa_weights(self, output_scale=False):
        """UPSA weights: constrained ensemble loadings, trace-scaled."""
        inv_eigs = self.upsa @ (1 / (self.eigenvalues.reshape(1, -1)
                                     + self.z_list.reshape(-1, 1)))
        scale = np.sum(1 / inv_eigs) / np.sum(self.eigenvalues)
        w = self.eff_port @ self.upsa * scale
        return (w, scale) if output_scale else w

    def get_ridge_weights(self, output_scale=False):
        inv_eigs = 1 / (self.eigenvalues + self.z_list[self.best_z])
        scale = np.sum(1 / inv_eigs) / np.sum(self.eigenvalues)
        w = self.eff_port[:, self.best_z] * scale
        return (w, scale) if output_scale else w

    # --------------------------------------------- shrinkage-function curves
    def get_inv_eigenvalues_upsa(self):
        inv_eigs = self.upsa @ (1 / (self.eigenvalues.reshape(1, -1)
                                     + self.z_list.reshape(-1, 1)))
        scale = np.sum(1 / inv_eigs) / np.sum(self.eigenvalues)
        return inv_eigs * scale

    def get_inv_eigenvalues_ridge(self):
        inv_eigs = 1 / (self.eigenvalues + self.z_list[self.best_z])
        scale = np.sum(1 / inv_eigs) / np.sum(self.eigenvalues)
        return inv_eigs * scale

    # ------------------------------------------------------------- internals
    @staticmethod
    def compute_upsa(estimated_loo_rets):
        mean = np.mean(estimated_loo_rets, 0)
        t_ = estimated_loo_rets.shape[0]
        cov = estimated_loo_rets.T @ estimated_loo_rets / t_
        upsa = UPSA.markowitz_constrained(mean, cov)
        best_z = UPSA.find_best_z(mean, cov)
        return best_z, upsa

    @staticmethod
    def find_best_z(mean, cov):
        all_sharpes = mean / np.sqrt(np.diag(cov))
        return np.argmax(all_sharpes)

    def _leave_one_out_and_eff_port_estimators(self, returns, eigenvalues, eigenvectors):
        ridge_smoothers, eff_portfolios = self.w_and_lambda(
            returns, eigenvalues, eigenvectors)
        loo_returns, _ = self.calculate_loo_returns(ridge_smoothers)
        return loo_returns, eff_portfolios

    def w_and_lambda(self, returns, eigenvalues, eigenvectors):
        """Ridge smoothers and ridge efficient portfolios across the z-grid,
        using (z+R'R)^{-1} = U(z+lambda)^{-1}U' + z^{-1}(I-UU')."""
        T, P = returns.shape
        projected_returns = eigenvectors.T @ returns.T          # U'R'
        normalized_mean = np.mean(returns, axis=0)              # mu
        projected_mean_vec = eigenvectors.T @ normalized_mean   # U'mu

        if P <= T:
            l_adj = 0
            w_adj = 0
        else:
            w_adj = (returns @ returns.T - projected_returns.T @ projected_returns) / T
            l_adj = normalized_mean - eigenvectors @ projected_mean_vec

        ridge_smoothers = [
            projected_returns.T @ ((1 / (eigenvalues.reshape(-1, 1) + z)) * projected_returns) / T
            + w_adj / z
            for z in self.z_list
        ]
        ridge_eff_portfolios = [
            (eigenvectors * (1 / (eigenvalues.reshape(1, -1) + z))) @ projected_mean_vec
            + l_adj / z
            for z in self.z_list
        ]
        ridge_eff_portfolios = np.array(ridge_eff_portfolios).T
        return ridge_smoothers, ridge_eff_portfolios

    def calculate_loo_returns(self, list_of_ridge_smoother, w_diag=None):
        """Leave-one-out realized returns: (Wbar - W_tt)/(1 - W_tt) per z."""
        if w_diag is None:
            w_diag = [np.diag(w) for w in list_of_ridge_smoother]
        w_bar = [np.sum(w, axis=1) for w in list_of_ridge_smoother]
        loo = [(w_bar[i] - w_diag[i]) / (1 - w_diag[i])
               for i in range(len(list_of_ridge_smoother))]
        return np.array(loo).T, w_diag

    @staticmethod
    def smart_eigenvalue_decomposition_covariance(features):
        """Eigendecomposition of the second-moment matrix; if P>T work in the
        T-dim space and project eigenvectors back to dimension P."""
        T, P = features.shape
        if P > T:
            covariance = features @ features.T / T
        else:
            covariance = features.T @ features / T
        eigval, eigvec = np.linalg.eigh(covariance)
        if P > T:
            eigvec = features.T @ eigvec * (eigval ** (-1 / 2)).reshape(1, -1) / np.sqrt(T)
        return eigval, eigvec

    @staticmethod
    def markowitz_constrained(mean, cov):
        """Non-negative Markowitz: min 1/2 x'cov x - mean'x  s.t.  x >= 0."""
        G_mat = matrix(-np.eye(len(mean)))
        h_mat = matrix(np.zeros((len(mean), 1)))
        nu_mat = matrix(-mean.astype(np.double))
        m_mat = matrix(cov.astype(np.double))
        sol = solvers.qp(m_mat, nu_mat, G_mat, h_mat)
        return np.array(sol["x"]).flatten()
