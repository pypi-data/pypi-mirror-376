import copy
from typing import Tuple

import numpy as np
import pandas as pd

from annealing_ab.loss.losses import BaseLoss


class AnnealingAB:
    def __init__(
        self,
        general_population: pd.DataFrame,
        target_population: pd.DataFrame,
        test_stats_criteria: BaseLoss,
        fk_key: str,
        n_sub: int,
        num_groups: int,
        temperature: float = 100.0,
        cooling_rate: float = 0.95,
        min_temperature: float = 1e-3,
        max_iterations: int = 1000,
        random_state: int | None = None,
        early_stop_k: int = 50,
        early_stop_eps: float = 1e-4,
    ):
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.max_iterations = max_iterations
        self.random_state = np.random.RandomState(random_state)

        self.best_solution = None
        self.best_loss = None

        self.history_loss = []

        self.early_stop_k = early_stop_k
        self.early_stop_eps = early_stop_eps

        self.fk_key = fk_key

        self.general_population = general_population
        self.target_population = target_population
        self.fk_key_fisrt_col()

        self.test_stats_criteria = test_stats_criteria
        self.n_sub = n_sub
        self.num_groups = num_groups

    def acceptance_probability(self, old_loss: float, new_loss: float) -> float:
        if new_loss < old_loss:
            return 1.0
        return np.exp((old_loss - new_loss) / self.temperature)

    def cool_down(self):
        if self.temperature > self.min_temperature:
            self.temperature *= self.cooling_rate
            if self.temperature < self.min_temperature:
                self.temperature = self.min_temperature

    def early_stop(self) -> bool:
        if len(self.history_loss) > self.early_stop_k:
            window = self.history_loss[-self.early_stop_k :]
            return max(window) - min(window) < self.early_stop_eps
        return False

    def neighboring_state(
        self, X: np.ndarray, Y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        n_X, n_Y = len(X), len(Y)
        ind_X, ind_Y = np.random.randint(0, n_X), np.random.randint(0, n_Y)
        X_new, Y_new = np.copy(X), np.copy(Y)
        X_new[ind_X] = Y[ind_Y]
        Y_new[ind_Y] = X[ind_X]
        return X_new, Y_new, np.copy(X[ind_X]), np.copy(Y[ind_Y])

    def initial_state(self, general_population: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X = general_population.copy()
        n = X.shape[0]
        idx = np.random.choice(n, self.n_sub, replace=False)
        mask = np.ones(n, dtype=bool)
        mask[idx] = False
        subset = X[idx].copy()
        general_without_subset = X[mask].copy()
        return subset, general_without_subset

    def fk_key_fisrt_col(self):
        def move_fk_key_first(df: pd.DataFrame, key: str) -> pd.DataFrame:
            cols = [key] + [c for c in df.columns if c != key]
            return df[cols]

        self.general_population = move_fk_key_first(self.general_population, self.fk_key)
        self.target_population = move_fk_key_first(self.target_population, self.fk_key)

    def run(self):
        target_np = self.target_population.copy().to_numpy()
        general_np = self.general_population.copy().to_numpy()

        subset, general_without_subset = self.initial_state(general_np)
        self.test_stats_criteria.update(
            new_val=None, old_val=None, X=subset[:, 1:], Y=target_np[:, 1:]
        )
        current_loss = self.test_stats_criteria.calculate_loss()

        for _ in range(self.max_iterations):
            subset_new, general_without_subset_new, old_val, new_val = self.neighboring_state(
                subset, general_without_subset
            )
            temp_test_criteria = copy.deepcopy(self.test_stats_criteria)
            temp_test_criteria.update(
                new_val=new_val[1:], old_val=old_val[1:], X=subset_new[:, 1:].copy()
            )
            new_loss = temp_test_criteria.calculate_loss()
            if self.random_state.rand() < self.acceptance_probability(current_loss, new_loss):
                current_loss = new_loss
                subset = subset_new
                general_without_subset = general_without_subset_new

                self.test_stats_criteria.update(
                    new_val=new_val[1:], old_val=old_val[1:], X=subset_new[:, 1:]
                )
                self.history_loss.append(current_loss)
            self.cool_down()
            if self.early_stop():
                break
        return subset
