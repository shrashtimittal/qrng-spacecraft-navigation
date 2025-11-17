"""
Test script for QRNG (ANU API → OS fallback)

Run:
    python test_qrng.py

This will verify:
1. ANU QRNG connectivity (real quantum randomness)
2. OS randomness as fallback
"""

from extras.qrng.qrng_utils import generate_random_bits


def test_anu():
    print("\n=== Testing ANU QRNG (no fallback) ===")
    try:
        bits = generate_random_bits(64, mode="anu", fallback=False)
        print("SUCCESS: Received", len(bits), "bits from ANU QRNG")
        print("Bits sample:", bits[:16], "...")
    except Exception as e:
        print("FAILED: ANU QRNG did not respond")
        print("Reason:", type(e).__name__, "-", e)


def test_os():
    print("\n=== Testing OS Cryptographic RNG ===")
    try:
        bits = generate_random_bits(64, mode="os")
        print("SUCCESS: Received", len(bits), "OS-generated bits")
        print("Bits sample:", bits[:16], "...")
    except Exception as e:
        print("FAILED: OS RNG error??")
        print("Reason:", type(e).__name__, "-", e)


def test_prng():
    print("\n=== Testing NumPy PRNG ===")
    try:
        bits = generate_random_bits(64, mode="prng", seed=42)
        print("SUCCESS: Received", len(bits), "PRNG bits")
        print("Bits sample:", bits[:16], "...")
    except Exception as e:
        print("FAILED: NumPy PRNG error??")
        print("Reason:", type(e).__name__, "-", e)


if __name__ == "__main__":
    print("\n----------------------------------------")
    print(" QRNG Test Script")
    print("----------------------------------------")

    test_anu()
    test_os()
    test_prng()

    print("\nDone.")
