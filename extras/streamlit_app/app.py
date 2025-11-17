# Program for Streamlit UI for the QRNG navigation demo

import sys, os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT_DIR)

from extras.qrng.qrng_utils import generate_random_bits

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sim.orbit import OrbitSimulator
from estimator.kalman import SimpleKalman

# Page config
st.set_page_config(
    page_title="QRNG Nav Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Minimal CSS for space theme ---
st.markdown(
    """
    <style>
    :root{
      --bg-color: #071028;
      --card-bg: rgba(255,255,255,0.03);
      --accent: #59b3ff;
      --muted: #9fb6d6;
    }
    .stApp {
      background: linear-gradient(180deg, #041027 0%, #071028 35%, #081a2b 100%);
      color: #e6f2ff;
    }
    .block-container {
      padding: 1rem 2rem;
    }
    .sidebar .sidebar-content {
      background: linear-gradient(180deg, rgba(9,20,33,0.6), rgba(4,10,18,0.6));
    }
    .title {
      font-family: "Segoe UI", Roboto, Arial;
      font-weight: 700;
      color: white;
    }
    .small {
      color: var(--muted);
      font-size: 0.9rem;
    }
    .card {
      background: var(--card-bg);
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.03);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("<div class='title'>QRNG-Based Spacecraft Navigation Simulator</div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Simulate orbit → inject quantum/classical noise → estimate with Kalman filter</div>", unsafe_allow_html=True)

with col_h2:
    st.image("https://images.unsplash.com/photo-1454789548928-9efd52dc4031?q=80&w=800&auto=format&fit=crop&ixlib=rb-4.0.3&s=7bdf3b2b2356fae0d4161d3ac9b5f7bd", width=120)

st.markdown("---")

# --- Sidebar controls ---
with st.sidebar:
    st.header("Simulation controls")
    n_steps = st.slider("Steps", min_value=50, max_value=1000, value=300, step=50)
    dt = st.number_input("Time step (s)", value=10.0, step=1.0, format="%.1f")
    use_qrng = st.checkbox("Use QRNG (Qiskit if available)", value=False)
    noise_std = st.slider("Position noise std (km)", 0.0001, 0.01, 0.001, step=0.0001, format="%.6f")
    st.write(f"Selected noise_std = {noise_std:.6f} km")

    drift_scale = st.slider("Drift scale", 0.0, 0.0002, 0.00005, step=0.00001, format="%.8f")
    st.write(f"Selected drift_scale = {drift_scale:.8f}")


    run_btn = st.button("Run Simulation", key="run")

    st.markdown("---")
    st.subheader("Output options")
    save_png = st.checkbox("Save PNG to outputs/", value=True)
    save_csv = st.checkbox("Save CSV to outputs/", value=True)
    st.info("Tip: reduce steps for faster runs in demos.")

def bits_to_floats(bits, block_size=16):
    n_blocks = len(bits) // block_size
    bits = bits[:n_blocks*block_size]
    reshaped = bits.reshape((n_blocks, block_size))
    vals = []
    for row in reshaped:
        v = 0
        for i, b in enumerate(row):
            v |= (int(b) << i)
        vals.append(v)
    vals = np.array(vals, dtype=np.uint32)
    max_val = 2**block_size - 1
    return (vals / max_val) * 2 - 1

def uniform_to_gaussian(u):
    u = (u + 1) / 2
    u = np.clip(u, 1e-12, 1-1e-12)
    u1 = u[0::2]; u2 = u[1::2]
    r = np.sqrt(-2 * np.log(u1)); theta = 2 * np.pi * u2
    z0 = r * np.cos(theta); z1 = r * np.sin(theta)
    return np.hstack((z0, z1))

# --- Run / compute ---
if run_btn:
    sim = OrbitSimulator()
    t, true_pos, true_vel = sim.simulate_circular(n_steps=n_steps, dt=dt)

    bits_needed = 16 * (2 * n_steps)
    # request bits from ANU QRNG if toggled, else use OS entropy (no network)
    mode = "anu" if use_qrng else "os"
    bits = generate_random_bits(bits_needed, mode=mode)
    floats = bits_to_floats(bits, block_size=16)
    gauss = uniform_to_gaussian(floats)
    noise = gauss[:2*n_steps].reshape(n_steps, 2)

    drift = np.cumsum(noise * drift_scale, axis=0)
    meas = true_pos + noise * noise_std + drift

    kf = SimpleKalman(dt=dt)
    init_x = np.array([meas[0,0], meas[0,1], true_vel[0,0], true_vel[0,1]])
    kf.set_initial(init_x)
    est = np.zeros((n_steps, 4))
    for i in range(n_steps):
        est[i] = kf.step(meas[i])

    rmse = np.sqrt(np.mean((est[:,:2] - true_pos)**2, axis=1))

    # --- Interactive Plotly figure: trajectory + RMSE (subplot) ---
    fig = make_subplots(rows=1, cols=2, specs=[[{"type":"scatter"}, {"type":"xy"}]],
                        subplot_titles=("Trajectory (km)", "RMSE (km)"))

    # trajectory (left)
    fig.add_trace(go.Scatter(x=true_pos[:,0], y=true_pos[:,1], mode="lines",
                             name="True", line=dict(color="#59b3ff", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=meas[:,0], y=meas[:,1], mode="markers",
                             name="Measured", marker=dict(size=4, color="#ffd97a", opacity=0.7)), row=1, col=1)
    fig.add_trace(go.Scatter(x=est[:,0], y=est[:,1], mode="lines",
                             name="Estimated", line=dict(color="#7bf59b", dash="dash")), row=1, col=1)
    fig.update_xaxes(scaleanchor="y", scaleratio=1, row=1, col=1)

    # RMSE (right)
    fig.add_trace(go.Scatter(x=t, y=rmse, mode="lines", name="RMSE", line=dict(color="#ff6b6b")), row=1, col=2)
    fig.update_layout(
        template="plotly_dark",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary cards
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Final RMSE (km)", f"{rmse[-1]:.6f}")
    col_b.metric("Noise Std (km)", f"{noise_std:.6f}")
    col_c.metric("Drift Scale", f"{drift_scale:.6f}")

    # Download options and saving
    df = pd.DataFrame({
        "t": t,
        "true_x": true_pos[:,0], "true_y": true_pos[:,1],
        "meas_x": meas[:,0], "meas_y": meas[:,1],
        "est_x": est[:,0], "est_y": est[:,1],
        "rmse": rmse
    })

    if save_csv:
        df.to_csv("outputs/results.csv", index=False)

    if save_png:
        fig.write_image("outputs/trajectory_rmse.png", scale=2)

    st.download_button("Download results.csv", df.to_csv(index=False), file_name="results.csv")

    st.markdown("---")
    st.markdown("### Notes")
    st.markdown("- Use the QRNG toggle only if Qiskit is installed and configured; otherwise the app falls back to a high-quality PRNG.")
    st.markdown("- Reduce steps for quicker interactivity during live demos.")
else:
    st.markdown(
        "<div class='card'>Click **Run Simulation** to generate the orbit, inject noise and run the Kalman filter. "
        "Use the sidebar to experiment with QRNG, noise and drift.</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("<div class='small' style='margin-top:18px'>Built for hackathon demos • QRNG-based noise exploration • Visuals powered by Plotly</div>", unsafe_allow_html=True)
