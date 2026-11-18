"""Experiments E1-E4. Run: .venv/Scripts/python.exe src/experiments.py [e1 e2 e3 e4]

Writes results/<exp>.json and report/figures/<fig>.{pdf,png}.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sketches import splitmix64, BottomK, HLL
from attack import run_attack, prefix_curve

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
SLIDES = os.environ.get("SLIDES") == "1"   # larger fonts, output to slides/figures
FIG = ROOT / ("slides" if SLIDES else "report") / "figures"
RES.mkdir(exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# ---- style (validated default palette; sequential blue ramp for magnitudes)
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
CAT = {"bottom-k": "#2a78d6", "HLL": "#eb6834"}
BLUE_RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
             "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]


def ramp(n):
    idx = np.linspace(0, len(BLUE_RAMP) - 1, n).round().astype(int)
    return [BLUE_RAMP[i] for i in idx]


_s = 1.35 if SLIDES else 1.0
plt.rcParams.update({
    "font.size": 7.5 * _s, "axes.titlesize": 8 * _s, "axes.labelsize": 7.5 * _s,
    "legend.fontsize": 6.5 * _s, "xtick.labelsize": 6.5 * _s, "ytick.labelsize": 6.5 * _s,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED,
    "ytick.color": MUTED, "text.color": INK, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
    "axes.spines.right": False, "lines.linewidth": 1.2, "legend.frameon": False,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42,
})


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=220)
    plt.close(fig)


def dump(name, obj):
    (RES / f"{name}.json").write_text(json.dumps(obj, indent=1))


SK = {"bottom-k": BottomK, "HLL": HLL}


# ------------------------------------------------------------------ E1
def e1():
    ks = [64, 128, 256, 512, 1024, 2048]
    n, trials = 10_000, 200
    rng = np.random.default_rng(1)
    out = {name: [] for name in SK}
    for k in ks:
        for name, cls in SK.items():
            sk = cls(k)
            errs = []
            for _ in range(trials):
                keys = rng.integers(0, 2**63, size=n, dtype=np.uint64)
                errs.append(sk.estimate(sk.prepare(splitmix64(keys, 11))) / n - 1)
            errs = np.array(errs)
            out[name].append({"k": k, "nrmse": float(np.sqrt(np.mean(errs**2))),
                              "bias": float(errs.mean())})
            print(f"E1 {name:9s} k={k:5d} NRMSE={out[name][-1]['nrmse']:.4f}")
    dump("e1", {"n": n, "trials": trials, "ks": ks, "results": out})

    fig, ax = plt.subplots(figsize=(3.3, 2.1))
    kk = np.array(ks, float)
    ax.plot(kk, 1 / np.sqrt(kk), ls="--", color=MUTED, lw=1, label=r"$1/\sqrt{k}$")
    ax.plot(kk, 1.04 / np.sqrt(kk), ls=":", color=MUTED, lw=1, label=r"$1.04/\sqrt{k}$")
    for name in SK:
        ax.plot(kk, [d["nrmse"] for d in out[name]], marker="o", ms=3.5,
                color=CAT[name], label=name)
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("sketch size $k$"); ax.set_ylabel("NRMSE")
    ax.set_xticks(ks, [str(k) for k in ks])
    ax.legend()
    save(fig, "fig_e1_accuracy")


# ------------------------------------------------------------------ E2
def e2():
    n = 5000
    rs = [4**i for i in range(8)]  # 1 .. 16384
    sizes = np.unique(np.linspace(1, n, 60).round().astype(int))
    keys = np.arange(n, dtype=np.uint64) + np.uint64(10**9)
    res = {}
    for k in (128, 512):
        for name, cls in SK.items():
            sk = cls(k)
            curves = {}
            for r in rs:
                t0 = time.time()
                order, data = run_attack(sk, keys, r, np.random.default_rng(r), hash_seed=5)
                up = prefix_curve(sk, data, order, sizes)
                down = prefix_curve(sk, data, order[::-1], sizes)
                curves[r] = {"up": up.tolist(), "down": down.tolist()}
                print(f"E2 k={k} {name:9s} r={r:6d} max over {np.max(up/sizes):.2f} "
                      f"min under {np.min(down/sizes):.2f}  ({time.time()-t0:.1f}s)")
            res[f"{name}|{k}"] = curves
    dump("e2", {"n": n, "rs": rs, "sizes": sizes.tolist(), "curves": res})
    plot_e2()


def plot_e2():
    d = json.loads((RES / "e2.json").read_text())
    sizes, rs = np.array(d["sizes"]), d["rs"]
    cols = ramp(len(rs))
    for k in (128, 512):
        fig, axes = plt.subplots(2, 2, figsize=(7.0, 2.9), sharex=True, sharey=True)
        for i, name in enumerate(SK):
            for j, direc in enumerate(("up", "down")):
                ax = axes[i, j]
                ax.plot([0, sizes[-1]], [0, sizes[-1]], ls="--", color=MUTED, lw=0.8)
                for r, c in zip(rs, cols):
                    ax.plot(sizes, d["curves"][f"{name}|{k}"][str(r)][direc], color=c,
                            lw=1.0, label=f"$r={r}$")
                if SLIDES:
                    ttl = "lowest scores first" if direc == "up" else "highest scores first"
                else:
                    ttl = "lowest-score prefix (overestimate)" if direc == "up" \
                        else "highest-score prefix (underestimate)"
                ax.set_title(f"{name}, $k={k}$: {ttl}", loc="left")
                if i == 1: ax.set_xlabel("true cardinality of adversarial set")
                if j == 0: ax.set_ylabel("estimate")
        h, l = axes[0, 0].get_legend_handles_labels()
        fig.legend(h, l, ncol=len(rs), loc="upper center", bbox_to_anchor=(0.5, 1.0),
                   handlelength=1.5, columnspacing=1.2)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        save(fig, f"fig_e2_k{k}")


# ------------------------------------------------------------------ E3
def e3(seeds=(0, 1, 2)):
    ks = [64, 128, 256, 512, 1024, 2048]
    fr = np.arange(1, 101) / 100
    res = {}
    for name, cls in SK.items():
        for k in ks:
            n = int(10 * 10 ** np.ceil(np.log10(k)))
            sizes = np.maximum(1, (fr * n).round().astype(int))
            sk = cls(k)
            ups, downs = [], []
            for s in seeds:
                t0 = time.time()
                keys = np.arange(n, dtype=np.uint64) + np.uint64(s * 10**8)
                order, data = run_attack(sk, keys, 4 * k, np.random.default_rng(100 + s),
                                         hash_seed=50 + s)
                ups.append(prefix_curve(sk, data, order, sizes) / sizes)
                downs.append(prefix_curve(sk, data, order[::-1], sizes) / sizes)
                print(f"E3 {name:9s} k={k:5d} n={n:6d} seed={s} peak over {ups[-1].max():.2f} "
                      f"min under {downs[-1].min():.2f} ({time.time()-t0:.1f}s)", flush=True)
            ups, downs = np.array(ups), np.array(downs)
            res[f"{name}|{k}"] = {
                "n": n, "up_mean": ups.mean(0).tolist(), "down_mean": downs.mean(0).tolist(),
                "peak_over": ups.max(1).tolist(), "argpeak_frac": fr[ups.argmax(1)].tolist(),
                "min_under": downs.min(1).tolist(),
                "under_at_peakfrac": [float(dn[a]) for dn, a in zip(downs, ups.argmax(1))],
            }
    dump("e3", {"ks": ks, "fracs": fr.tolist(), "seeds": list(seeds), "results": res})
    plot_e3()


def plot_e3():
    d = json.loads((RES / "e3.json").read_text())
    fr, ks = np.array(d["fracs"]) * 100, d["ks"]
    cols = ramp(len(ks))
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 1.85), sharey=True)
    for ax, name in zip(axes, SK):
        ax.axhline(1, ls="--", color=MUTED, lw=0.8)
        for k, c in zip(ks, cols):
            r = d["results"][f"{name}|{k}"]
            ax.plot(fr, r["up_mean"], color=c, label=f"$k={k}$")
            ax.plot(fr, r["down_mean"], color=c, lw=0.9, ls=(0, (3, 1.5)))
        ax.set_title(f"{name}, $r=4k$ queries", loc="left")
        ax.set_xlabel("adversarial set size (% of ground set $N$)")
    axes[0].set_ylabel("estimate / true size")
    axes[0].legend(ncol=2, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_e3_sizes")


# ------------------------------------------------------------------ E4
def e4(seeds=(0, 1, 2)):
    """Mitigation: system re-draws its hash seed every B queries."""
    k, n = 256, 10_000
    r = 4 * k
    Bs = [k // 4, k // 2, k, 2 * k, None]
    fr = np.arange(1, 101) / 100
    sizes = (fr * n).round().astype(int)
    res = {}
    for name, cls in SK.items():
        sk = cls(k)
        rows = []
        for B in Bs:
            peaks, unders = [], []
            for s in seeds:
                keys = np.arange(n, dtype=np.uint64) + np.uint64(s * 10**8)
                order, data = run_attack(sk, keys, r, np.random.default_rng(300 + s),
                                         hash_seed=70 + s, rotate_every=B)
                peaks.append(float((prefix_curve(sk, data, order, sizes) / sizes).max()))
                unders.append(float((prefix_curve(sk, data, order[::-1], sizes) / sizes).min()))
            rows.append({"B": B if B else r, "fixed": B is None,
                         "peak_over": float(np.mean(peaks)), "min_under": float(np.mean(unders))})
            print(f"E4 {name:9s} B={B} peak over {rows[-1]['peak_over']:.2f} "
                  f"min under {rows[-1]['min_under']:.2f}", flush=True)
        res[name] = rows
    dump("e4", {"k": k, "n": n, "r": r, "results": res})
    plot_e4()


def plot_e4():
    d = json.loads((RES / "e4.json").read_text())
    fig, ax = plt.subplots(figsize=(3.3, 1.9))
    ax.axhline(1, ls="--", color=MUTED, lw=0.8)
    for name in SK:
        rows = d["results"][name]
        B = [r["B"] for r in rows]
        ax.plot(B, [r["peak_over"] for r in rows], marker="o", ms=3.5, color=CAT[name],
                label=f"{name} max over")
        ax.plot(B, [r["min_under"] for r in rows], marker="s", ms=3.5, color=CAT[name],
                ls=(0, (3, 1.5)), label=f"{name} min under")
    ax.set_xscale("log", base=2)
    ax.set_xticks([r["B"] for r in d["results"]["HLL"]],
                  [f"{r['B']}" + ("\n(fixed)" if r["fixed"] else "")
                   for r in d["results"]["HLL"]])
    ax.set_xlabel(f"queries per hash seed $B$ ($k={d['k']}$, $r={d['r']}$)")
    ax.set_ylabel("estimate / true size")
    ax.legend(ncol=1, loc="upper left", fontsize=6)
    save(fig, "fig_e4_mitigation")


if __name__ == "__main__":
    which = sys.argv[1:] or ["e1", "e2", "e3"]
    for w in which:
        t0 = time.time()
        globals()[w]()
        print(f"== {w} done in {time.time()-t0:.0f}s", flush=True)
