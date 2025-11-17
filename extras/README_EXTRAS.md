# Extras — Optional Components

This `extras/` folder holds optional add-ons that expand the core demo without cluttering the main repository.

## Contents overview

- `streamlit_app/`  
  Lightweight Streamlit UI to toggle QRNG/PRNG, change noise parameters, and view results interactively.

- `notebook/`  
  Jupyter notebook with a compact, runnable demo for inline plots and step-by-step explanation.

- `qrng_ibmq/`  
  Instructions to configure IBM Quantum (IBMQ) as a real QRNG backend, plus example snippet.

- `presentation/`  
  Slide outline and a short 90-second demo script for your hackathon pitch.

## How to use these extras

- Streamlit app:
  ```bash
  source venv/Scripts/activate
  pip install -r requirements.txt
  streamlit run extras/streamlit_app/app.py
