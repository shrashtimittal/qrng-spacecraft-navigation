# Program for professional Kalman filter for state [x, y, vx, vy]

from __future__ import annotations
from typing import Optional
import numpy as np


class SimpleKalman:
    """
    Linear Kalman filter with constant-velocity model for a 4-state vector:
    x = [x, y, vx, vy]^T. Observations are positions [x, y].
    """

    def __init__(self, dt: float, process_var: float = 1e-6, meas_var: float = 1e-6):
        self.dt = float(dt)

        # State transition matrix (constant velocity)
        self.F = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=float)

        # Measurement matrix (we observe position only)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)

        # Process and measurement noise covariances
        self.Q = process_var * np.eye(4, dtype=float)
        self.R = meas_var * np.eye(2, dtype=float)

        # State estimate and covariance
        self.x = np.zeros((4,), dtype=float)
        self.P = np.eye(4, dtype=float)

    def set_process_noise(self, process_var: float):
        self.Q = float(process_var) * np.eye(4, dtype=float)

    def set_measurement_noise(self, meas_var: float):
        self.R = float(meas_var) * np.eye(2, dtype=float)

    def set_initial(self, x0: np.ndarray, P0: Optional[np.ndarray] = None):
        self.x = x0.astype(float).copy()
        if P0 is not None:
            self.P = P0.astype(float).copy()

    def predict(self):
        """Predict state and covariance forward one time step."""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z: np.ndarray):
        """Incorporate measurement z (shape: (2,)) to update the state."""
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        y = z - (self.H @ self.x)
        self.x = self.x + K @ y
        self.P = (np.eye(self.P.shape[0]) - K @ self.H) @ self.P

    def step(self, z: np.ndarray):
        """Full predict+update step. Returns the updated state vector."""
        self.predict()
        self.update(z)
        return self.x.copy()
