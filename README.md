# QRNG-Based Spacecraft Navigation

A compact demo that uses quantum (or high-quality) randomness to inject realistic noise into a simple 2D spacecraft navigation simulation and evaluates state estimation using a Kalman filter.

This repository contains a small simulator, an estimator, a polished Streamlit demo (interactive UI) and utilities to fetch randomness from multiple sources (ANU QRNG, OS entropy, PRNG). The project is designed to run locally for a 1-day hackathon/demo.

---

## Highlights
- Simulates a circular spacecraft orbit (ground truth).
- Injects noise generated from QRNG (ANU) or local entropy with automatic fallback.
- Runs a 4-state Kalman filter to estimate position & velocity.
- Interactive Streamlit UI with space-themed visuals and download options.
- Clean project structure ready for presentation and GitHub portfolio.

---

## Quick start (5 minutes)

### 1. Clone repository
```bash
git clone https://github.com/<your-username>/qrng-spacecraft-navigation.git
cd qrng-spacecraft-navigation

