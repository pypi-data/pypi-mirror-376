from abc import ABC, abstractmethod

import numpy as np


class BaseLoss(ABC):
    def __init__(self, X: np.ndarray | None = None, Y: np.ndarray | None = None):
        self.X = X.copy() if X is not None else np.array([])
        self.Y = Y.copy() if Y is not None else np.array([])

    @abstractmethod
    def calculate_test_statistic(self) -> np.ndarray:
        pass

    @abstractmethod
    def loss_function(self, test_stats: np.ndarray) -> float:
        pass

    def calculate_loss(self) -> float:
        return self.loss_function(self.calculate_test_statistic())

    def update(self, new_val=None, old_val=None, X=None, Y=None):
        if X is not None:
            self.X = X.copy()
        if Y is not None:
            self.Y = Y.copy()


class TTestLoss(BaseLoss):
    def __init__(self, X, Y, new_val=None, old_val=None, equal_var=False):
        super().__init__(X, Y)
        self.new_val = new_val
        self.old_val = old_val
        self.equal_var = equal_var
        self.mean_X, self.var_X, self.n_X = self._compute_stats(self.X)
        self.mean_Y, self.var_Y, self.n_Y = self._compute_stats(self.Y)

    def loss_function(self, test_stats: np.ndarray) -> float:
        return np.mean(-((1 - test_stats) ** 5) * 5 * np.log(test_stats))

    def _compute_stats(self, arr):
        mean = arr.mean(axis=0)
        var = np.var(arr, ddof=1, axis=0)
        return mean, var, len(arr)

    def _update_mean_var_x(self):
        if self.new_val is not None and self.old_val is not None:
            new_mean = self.mean_X + (self.new_val - self.old_val) / self.n_X
            new_var = self.var_X + (
                (self.new_val - self.old_val)
                * (self.new_val - self.mean_X + self.old_val - new_mean)
            ) / (self.n_X - 1)
            self.mean_X = new_mean
            self.var_X = new_var

    def update(self, new_val=None, old_val=None, X=None, Y=None):
        if new_val is not None and old_val is not None:
            self.new_val = new_val
            self.old_val = old_val
            self._update_mean_var_x()
        else:
            super().update(X=X, Y=Y)
            self.mean_X, self.var_X, self.n_X = self._compute_stats(self.X)
            self.mean_Y, self.var_Y, self.n_Y = self._compute_stats(self.Y)

    def calculate_test_statistic(self):
        if self.equal_var:
            pooled_var = ((self.n_X - 1) * self.var_X + (self.n_Y - 1) * self.var_Y) / (
                self.n_X + self.n_Y - 2
            )
            pooled_var = np.where(pooled_var == 0, 1e-16, pooled_var)
            t_stat = (self.mean_X - self.mean_Y) / np.sqrt(
                pooled_var * (1 / self.n_X + 1 / self.n_Y)
            )
        else:
            pooled_var = self.var_X / self.n_X + self.var_Y / self.n_Y
            pooled_var = np.where(pooled_var == 0, 1e-16, pooled_var)
            t_stat = (self.mean_X - self.mean_Y) / np.sqrt(pooled_var)
        return 1 / (1 + np.abs(t_stat))


class KSLoss(BaseLoss):
    def calculate_test_statistic(self):
        D_list = []
        for i in range(self.X.shape[1]):
            all_vals = np.sort(np.concatenate([self.X[:, i], self.Y[:, i]]))
            cdf_X = np.searchsorted(np.sort(self.X[:, i]), all_vals, side="right") / len(self.X)
            cdf_Y = np.searchsorted(np.sort(self.Y[:, i]), all_vals, side="right") / len(self.Y)
            D_list.append(np.max(np.abs(cdf_X - cdf_Y)))
        return np.array(D_list)

    def loss_function(self, test_stats: np.ndarray) -> float:
        return np.mean(-((1 - test_stats) ** 5) * 5 * np.log(test_stats))


class LeveneLoss(BaseLoss):
    def calculate_test_statistic(self):
        Z_X = np.abs(self.X - self.X.mean(axis=0))  # (n_X, d)
        Z_Y = np.abs(self.Y - self.Y.mean(axis=0))  # (n_Y, d)

        mean_Z_X = Z_X.mean(axis=0)  # (d,)
        mean_Z_Y = Z_Y.mean(axis=0)  # (d,)

        numerator = (
            len(self.X) * (mean_Z_X - (mean_Z_X + mean_Z_Y) / 2) ** 2
            + len(self.Y) * (mean_Z_Y - (mean_Z_X + mean_Z_Y) / 2) ** 2
        )  # (d,)

        denominator = ((Z_X - mean_Z_X) ** 2).sum(axis=0) + ((Z_Y - mean_Z_Y) ** 2).sum(
            axis=0
        )  # (d,)

        W = (len(self.X) + len(self.Y) - 2) * (numerator / denominator)  # (d,)

        # усредняем по колонкам, чтобы получить одно число
        return 1 / (1 + np.mean(np.abs(W)))

    def loss_function(self, test_stats: np.ndarray) -> float:
        return np.mean(-((1 - test_stats) ** 5) * 5 * np.log(test_stats))
