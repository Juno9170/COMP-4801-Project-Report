"""Algorithm 1 of Ahmadian & Cohen (ICML 2024): attack on "standard" estimators.

Fix a ground set N of n keys. Issue r queries, each a uniformly random subset
U of N (every key independently with prob 1/2). The system returns the
cardinality estimate M(S(U)); the attacker uses T = 1/M as the sufficient
statistic and scores every key by the average T over the queries containing
it. Keys sorted by ascending score: low-score keys are the low-hash ("low
priority") keys, so a prefix is overestimated and a suffix underestimated.
"""
import numpy as np
from sketches import splitmix64


def run_attack(sk, keys, r, rng, hash_seed=0, rotate_every=None, batch=64):
    """Return (order, final_data).

    order      -- key positions of N sorted by ascending average score A[x]
    final_data -- the sketch data (prepared hashes) the system uses at the end,
                  i.e. under which the adversarial sets are evaluated.
    rotate_every -- if set, the system draws a fresh hash seed every this many
                  queries (mitigation experiment E4). None = fixed randomness.
    """
    n = len(keys)
    c = np.zeros(n)            # sum of T over queries containing x
    t = np.zeros(n)            # number of queries containing x
    epoch, data = None, None
    done = 0
    while done < r:
        b = min(batch, r - done)
        if rotate_every is not None:
            b = min(b, rotate_every - done % rotate_every)
        e = 0 if rotate_every is None else done // rotate_every
        if e != epoch:
            epoch = e
            data = sk.prepare(splitmix64(keys, seed=hash_seed + 1000 * e))
        masks = rng.random((b, n)) < 0.5
        T = np.array([1.0 / max(sk.estimate(data, m), 1e-9) for m in masks])
        c += T @ masks
        t += masks.sum(axis=0)
        done += b
    A = c / np.maximum(t, 1)
    order = np.argsort(A, kind="stable")
    return order, data


def prefix_curve(sk, data, order, sizes):
    """Estimates M(S(first s keys of `order`)) for each s in sizes."""
    out = []
    for s in sizes:
        mask = np.zeros(len(order), dtype=bool)
        mask[order[:s]] = True
        out.append(sk.estimate(data, mask))
    return np.array(out)
