import numpy as np
from numba import njit, prange

@njit
def track_reconstruction(hits: np.ndarray):
    n_layers = hits.shape[0]
    A = np.zeros((n_layers, 2), dtype=np.float32)
    B = np.zeros((n_layers, 2), dtype=np.float32)

    for i in range(n_layers):
        A[i, 0] = hits[i, 2]
        A[i, 1] = 1
        B[i, 0] = hits[i, 0]
        B[i, 1] = hits[i, 1]

    AtA_inv = np.linalg.inv(A.T @ A)
    AtB = A.T @ B
    params = AtA_inv @ AtB

    slope_x = params[0, 0]
    intercept_x = params[1, 0]
    slope_y = params[0, 1]
    intercept_y = params[1, 1]

    theta_x = np.degrees(np.arctan(slope_x))
    theta_y = np.degrees(np.arctan(slope_y))

    return np.array([intercept_x, intercept_y, theta_x, theta_y], dtype=np.float32)