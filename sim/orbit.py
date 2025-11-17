# Program for Circular + Keplerian (planar) orbit simulator

from __future__ import annotations
import math
import numpy as np
from typing import Tuple


class OrbitSimulator:
    def __init__(self, radius_km: float = 6771.0, mu: float = 398600.4418):
        self.radius_km = radius_km
        self.mu = mu

    # -------------------------
    # Circular orbit generator
    # -------------------------
    def simulate_circular(
        self,
        n_steps: int = 300,
        dt: float = 10.0,
        phase0: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

        r = float(self.radius_km)
        v = math.sqrt(self.mu / r)
        omega = v / r

        t = np.arange(n_steps, dtype=float) * float(dt)
        theta = omega * t + float(phase0)

        x = r * np.cos(theta)
        y = r * np.sin(theta)
        vx = -r * omega * np.sin(theta)
        vy = r * omega * np.cos(theta)

        pos = np.column_stack((x, y))
        vel = np.column_stack((vx, vy))

        return t, pos, vel

    # ------------------------------------
    # Kepler's equation solver (planar)
    # ------------------------------------
    @staticmethod
    def _solve_kepler(M: float, e: float, tol: float = 1e-10, max_iter: int = 60) -> float:
        E = M if e < 0.8 else math.pi
        for _ in range(max_iter):
            f = E - e * math.sin(E) - M
            fp = 1 - e * math.cos(E)
            dE = -f / fp
            E += dE
            if abs(dE) < tol:
                break
        return E

    # ------------------------------------
    # Elliptical orbit (planar propagation)
    # ------------------------------------
    def simulate_keplerian(
        self,
        a: float,
        e: float,
        n_steps: int = 300,
        dt: float = 10.0,
        M0: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

        n = math.sqrt(self.mu / (a**3))
        t = np.arange(n_steps, dtype=float) * float(dt)
        M = M0 + n * t

        pos = np.zeros((n_steps, 2))
        vel = np.zeros((n_steps, 2))
        sqrt_mu_a = math.sqrt(self.mu * a)

        for i, Mi in enumerate(M):
            E = self._solve_kepler(Mi, e)
            r = a * (1 - e * math.cos(E))

            x = a * (math.cos(E) - e)
            y = a * math.sqrt(1 - e*e) * math.sin(E)

            vx = -(sqrt_mu_a / r) * math.sin(E)
            vy = (sqrt_mu_a * math.sqrt(1 - e*e) / r) * math.cos(E)

            pos[i] = [x, y]
            vel[i] = [vx, vy]

        return t, pos, vel
