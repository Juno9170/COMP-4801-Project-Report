"""Cardinality sketches over precomputed hashes.

Keys are integers. A fixed, seeded 64-bit hash (splitmix64) is computed once per
key; a sketch of any subset U of a ground set N is then a reduction over the
precomputed values restricted to a boolean mask. Only hash values matter, so this
is equivalent to hashing arbitrary strings.
"""
import numpy as np

_M64 = np.uint64(0xFFFFFFFFFFFFFFFF)
TWO64 = float(2**64)


def splitmix64(keys, seed):
    """Vectorized splitmix64 finalizer of (key + seed * golden). Returns uint64."""
    with np.errstate(over="ignore"):
        z = np.asarray(keys, dtype=np.uint64) + np.uint64(seed) * np.uint64(0x9E3779B97F4A7C15)
        z = z + np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return z


def _bit_length(v):
    """Exact bit length of each uint64 entry (0 -> 0)."""
    v = v.copy()
    bl = np.zeros(v.shape, dtype=np.int64)
    for s in (32, 16, 8, 4, 2, 1):
        big = v >= (np.uint64(1) << np.uint64(s))
        bl[big] += s
        v[big] >>= np.uint64(s)
    bl += (v > 0)
    return bl


# ---------------------------------------------------------------- bottom-k
class BottomK:
    """Bottom-k sketch: keep the k smallest hash values (as uniforms in [0,1)).

    Sufficient statistic T = k-th smallest value; estimate (k-1)/T.
    For |U| < k the sketch holds every key and the count is exact.
    """

    name = "bottom-k"

    def __init__(self, k):
        self.k = k

    def prepare(self, h):
        """Per-key data from uint64 hashes."""
        return h  # keep uint64; order is all that matters for the k-th smallest

    def estimate(self, data, mask=None):
        vals = data if mask is None else data[mask]
        k = self.k
        if vals.size < k:
            return float(vals.size)
        kth = np.partition(vals, k - 1)[k - 1]
        return (k - 1) / ((float(kth) + 0.5) / TWO64)


# ---------------------------------------------------------------- HyperLogLog
def _alpha(m):
    return {16: 0.673, 32: 0.697, 64: 0.709}.get(m, 0.7213 / (1 + 1.079 / m))


class HLL:
    """HyperLogLog with m = 2^p registers (Flajolet et al. 2007).

    Register index = top p bits; rank = 1 + leading zeros of the remaining 64-p
    bits. Raw estimate alpha_m m^2 / sum 2^-M, with linear counting
    m ln(m/V) when the raw estimate is <= 2.5m and V > 0 registers are empty.
    A 64-bit hash makes the large-range correction unnecessary. In the regime
    n >> m used here this agrees with HLL++'s dense-mode estimator.
    """

    name = "HLL"

    def __init__(self, k):
        p = int(round(np.log2(k)))
        assert 2**p == k, "HLL needs k = 2^p"
        self.k, self.p = k, p

    def prepare(self, h):
        p = self.p
        idx = (h >> np.uint64(64 - p)).astype(np.int64)
        rest = h & np.uint64((1 << (64 - p)) - 1)
        rank = (64 - p) - _bit_length(rest) + 1
        return idx, rank.astype(np.int8)

    def registers(self, data, mask=None):
        idx, rank = data
        if mask is not None:
            idx, rank = idx[mask], rank[mask]
        regs = np.zeros(self.k, dtype=np.int8)
        np.maximum.at(regs, idx, rank)
        return regs

    def estimate_regs(self, regs):
        m = self.k
        raw = _alpha(m) * m * m / np.sum(np.exp2(-regs.astype(np.float64)))
        zeros = int(np.count_nonzero(regs == 0))
        if raw <= 2.5 * m and zeros > 0:
            return m * np.log(m / zeros)
        return raw

    def estimate(self, data, mask=None):
        return self.estimate_regs(self.registers(data, mask))


SKETCHES = {"bottom-k": BottomK, "HLL": HLL}
