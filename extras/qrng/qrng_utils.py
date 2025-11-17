"""
QRNG utilities:
- mode 'anu' -> real quantum bits from ANU public QRNG API (HTTP)
- mode 'os'  -> local OS cryptographic randomness (secrets)
- mode 'prng'-> numpy PRNG (fast, reproducible)
Returns numpy array of uint8 bits (0 or 1).
"""

import requests
import numpy as np
import secrets
from typing import Optional

ANU_URL = "https://qrng.anu.edu.au/API/jsonI.php"

def _bits_from_bytes(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, dtype=np.uint8)
    bits = ((arr[:, None] & (1 << np.arange(8))) > 0).astype(np.uint8)
    return bits.reshape(-1)

def _get_anu_bits(n_bits: int, retries: int = 2) -> np.ndarray:
    # Request bytes_needed bytes from ANU API (type=uint8)
    bytes_needed = (n_bits + 7) // 8
    params = {"length": bytes_needed, "type": "uint8"}
    for attempt in range(retries + 1):
        try:
            resp = requests.get(ANU_URL, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and "data" in data:
                arr = bytes(data["data"])
                bits = _bits_from_bytes(arr)[:n_bits]
                return bits.astype(np.uint8)
        except Exception:
            if attempt == retries:
                raise
            # otherwise loop and retry
    raise RuntimeError("ANU QRNG fetch failed.")

def _get_os_bits(n_bits: int) -> np.ndarray:
    byte_count = (n_bits + 7) // 8
    b = secrets.token_bytes(byte_count)
    bits = _bits_from_bytes(b)[:n_bits]
    return bits.astype(np.uint8)

def _get_prng_bits(n_bits: int, seed: Optional[int] = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=n_bits, dtype=np.uint8)

def generate_random_bits(n_bits: int, mode: str = "anu", fallback: bool = True, **kwargs) -> np.ndarray:
    """
    Generate n_bits bits as numpy uint8 array.
    mode: 'anu' | 'os' | 'prng'
    fallback: if True, fallback to next safe method on failure.
    """
    mode = mode.lower()
    if mode == "anu":
        try:
            return _get_anu_bits(n_bits, retries=kwargs.get("retries", 2))
        except Exception:
            if not fallback:
                raise
            return _get_os_bits(n_bits)
    if mode == "os":
        return _get_os_bits(n_bits)
    if mode == "prng":
        return _get_prng_bits(n_bits, seed=kwargs.get("seed"))
    raise ValueError("Unknown mode: choose 'anu', 'os', or 'prng'.")
