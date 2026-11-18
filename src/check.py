"""Sanity checks for the sketches. Run: .venv/Scripts/python.exe src/check.py"""
import numpy as np
from sketches import splitmix64, BottomK, HLL, _bit_length

rng = np.random.default_rng(0)

# exact bit length
v = np.array([0, 1, 2, 3, 2**52, 2**53 - 1, 2**63, 2**64 - 1], dtype=np.uint64)
assert list(_bit_length(v)) == [0, 1, 2, 2, 53, 53, 64, 64], _bit_length(v)

# hash uniformity: top-byte histogram roughly flat
h = splitmix64(np.arange(1_000_000), seed=1)
counts = np.bincount((h >> np.uint64(56)).astype(np.int64), minlength=256)
chi2 = ((counts - counts.mean()) ** 2 / counts.mean()).sum()
assert chi2 < 350, chi2  # df=255
print(f"hash chi^2 (df=255): {chi2:.1f}")

# unbiasedness / NRMSE on random non-adaptive sets
for cls in (BottomK, HLL):
    for k in (64, 1024):
        sk = cls(k)
        n, trials = 20_000, 100
        errs = []
        for t in range(trials):
            keys = rng.integers(0, 2**63, size=n, dtype=np.uint64)
            d = sk.prepare(splitmix64(keys, seed=7))
            errs.append(sk.estimate(d) / n - 1)
        errs = np.array(errs)
        nrmse = np.sqrt(np.mean(errs**2))
        print(f"{cls.name:9s} k={k:5d}  mean rel err {errs.mean():+.4f}  NRMSE {nrmse:.4f}  1/sqrt(k) {1/np.sqrt(k):.4f}")
        assert abs(errs.mean()) < 4 * nrmse / np.sqrt(trials) + 0.01
        assert nrmse < 1.6 / np.sqrt(k)

# small sets: bottom-k exact, HLL linear counting accurate
d = BottomK(64).prepare(splitmix64(np.arange(50), 3))
assert BottomK(64).estimate(d) == 50
d = HLL(1024).prepare(splitmix64(np.arange(300), 3))
print("HLL k=1024 on 300 keys:", round(HLL(1024).estimate(d), 1))
print("all checks passed")
