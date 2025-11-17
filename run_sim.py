# Main simulation: orbit generation, noise injection, Kalman filtering

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sim.orbit import OrbitSimulator
from estimator.kalman import SimpleKalman


# -------------------------
# QRNG or PRNG bit source
# -------------------------
def generate_quantum_bits(n_bits: int):
    try:
        from qiskit import QuantumCircuit, Aer, execute
        backend = Aer.get_backend("aer_simulator")

        bits = []
        batch = min(20, n_bits)
        remaining = n_bits

        while remaining > 0:
            q = min(batch, remaining)
            qc = QuantumCircuit(q, q)
            qc.h(range(q))
            qc.measure(range(q), range(q))

            job = execute(qc, backend=backend, shots=1, memory=True)
            mem = job.result().get_memory()[0]
            bits.extend([int(b) for b in mem[::-1]])

            remaining -= q

        return np.array(bits, dtype=np.uint8)

    except Exception:
        # fallback: PRNG
        rng = np.random.default_rng()
        return rng.integers(0, 2, size=n_bits, dtype=np.uint8)


# -------------------------
# Bits -> uniform floats
# -------------------------
def bits_to_floats(bits, block_size=16):
    n_blocks = len(bits) // block_size
    bits = bits[:n_blocks * block_size]
    reshaped = bits.reshape((n_blocks, block_size))

    vals = []
    for row in reshaped:
        v = 0
        for i, b in enumerate(row):
            v |= (b << i)
        vals.append(v)

    vals = np.array(vals, dtype=np.uint32)
    max_val = 2**block_size - 1
    return (vals / max_val) * 2 - 1


# -------------------------
# Uniform -> Gaussian noise
# -------------------------
def uniform_to_gaussian(u):
    u = (u + 1) / 2
    u = np.clip(u, 1e-12, 1 - 1e-12)
    u1 = u[0::2]
    u2 = u[1::2]

    r = np.sqrt(-2 * np.log(u1))
    theta = 2 * np.pi * u2

    z0 = r * np.cos(theta)
    z1 = r * np.sin(theta)

    return np.hstack((z0, z1))


# -------------------------
# Main demo
# -------------------------
def run_demo(n_steps=300, dt=10.0, use_qrng=False):
    sim = OrbitSimulator()
    t, true_pos, true_vel = sim.simulate_circular(n_steps=n_steps, dt=dt)

    n_bits_needed = 16 * (2 * n_steps)
    bits = generate_quantum_bits(n_bits_needed) if use_qrng else np.random.randint(0, 2, n_bits_needed, dtype=np.uint8)

    floats = bits_to_floats(bits, block_size=16)
    gauss = uniform_to_gaussian(floats)
    noise = gauss[:2 * n_steps].reshape((n_steps, 2))

    noise_std = 0.001
    drift_scale = 0.00005
    drift = np.cumsum(noise * drift_scale, axis=0)

    meas = true_pos + noise * noise_std + drift

    kf = SimpleKalman(dt=dt)
    x0 = np.array([meas[0,0], meas[0,1], true_vel[0,0], true_vel[0,1]])
    kf.set_initial(x0)

    est = np.zeros((n_steps, 4))
    for i in range(n_steps):
        est[i] = kf.step(meas[i])

    rmse = np.sqrt(np.mean((est[:, :2] - true_pos)**2, axis=1))

    os.makedirs("outputs", exist_ok=True)

    # Trajectory plot
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(true_pos[:,0], true_pos[:,1], label="True")
    plt.scatter(meas[:,0], meas[:,1], s=6, alpha=0.6, label="Measured")
    plt.plot(est[:,0], est[:,1], "--", label="Estimated")
    plt.gca().set_aspect("equal")
    plt.legend()
    plt.title("Trajectory")

    plt.subplot(1, 2, 2)
    plt.plot(t, rmse)
    plt.xlabel("Time (s)")
    plt.ylabel("RMSE (km)")
    plt.title("Error")

    plt.tight_layout()
    plt.savefig("outputs/trajectory_rmse.png", dpi=200)
    plt.show()

    df = pd.DataFrame({
        "t": t,
        "true_x": true_pos[:,0],
        "true_y": true_pos[:,1],
        "meas_x": meas[:,0],
        "meas_y": meas[:,1],
        "est_x": est[:,0],
        "est_y": est[:,1],
        "rmse": rmse
    })
    df.to_csv("outputs/results.csv", index=False)

    print("Saved outputs/trajectory_rmse.png")
    print("Saved outputs/results.csv")


if __name__ == "__main__":
    run_demo(n_steps=300, dt=10.0, use_qrng=False)
