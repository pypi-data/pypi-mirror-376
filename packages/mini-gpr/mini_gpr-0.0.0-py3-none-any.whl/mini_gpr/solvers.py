# ruff: noqa: F722, F821

from typing import Protocol

import numpy as np
from jaxtyping import Float

from mini_gpr.utils import ensure_2d


class LinearSolver(Protocol):
    """
    Solve a linear system of the form `A @ x = y`.
    """

    def __call__(
        self,
        A: Float[np.ndarray, "A B"],
        y: Float[np.ndarray, "N"],
    ) -> Float[np.ndarray, "N"]: ...


@ensure_2d("A")
def vanilla(A, y):
    """Use the standard `np.linalg.solve` method to solve the linear system."""
    return np.linalg.solve(A, y)


@ensure_2d("A")
def least_squares(A, y):
    """Use `np.linalg.lstsq` method to solve the linear system:
    slower than ``vanilla`` but more stable."""
    return np.linalg.lstsq(A, y, rcond=None)[0]
