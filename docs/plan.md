# COMP 4801 Final Project: Design & Execution Plan

**Topic:** Ahmadian & Cohen, *Unmasking Vulnerabilities: Cardinality Sketches under Adaptive Inputs* (ICML 2024).
**Deliverables (due tomorrow):** (1) ~4-page LaTeX report, CCCG two-column style, compiled to PDF; (2) 12–15 min Google Slides presentation.
**Constraint:** no git commits by Claude; everything stays local until Ryan commits.

---

## 1. Intent

Show, with theory and our own experiments, that cardinality sketches are only safe against queries that do not depend on the hash randomness, and that a simple single-batch attack (Algorithm 1) breaks the standard estimators with O(k) queries. The report should read as a short research article: explain the result, reproduce the paper's key empirical claim, and add one small thing of our own.

**Our addition (small but real):** the paper proves Theorem 4.1 for bottom-k / k-mins but only runs experiments on HLL++. We run the attack on **both** bottom-k and HLL, so the theorem's setting and the practical setting are both tested.

**Non-goals:** full proofs of the k² results (stated with intuition only); reproducing HLL++ sparse mode; any defense beyond the optional mitigation.

**Failure modes to avoid:** claiming a reproduction we didn't get (if numbers differ, say so and explain); a report over ~4.5 pages of body text; slides that are just the report pasted.

---

## 2. Corrections to the proposal (carry into report)

- Algorithm 1 averages **T = 1/estimate** (a sufficient statistic), not the estimate itself. Low average score ⇒ low-hash ("low priority") key. **Prefix** of the ascending order ⇒ overestimate; **suffix** ⇒ underestimate.
- Thm 4.1: n = Ω((k/α)·log(kr)), r = O(k/α²), w.p. ≥ 0.99 the αn lowest-score keys U_α have E[M(U_α)] = Θ(n), i.e. sketch biased up by Ω(1/α).
- Paper's "~40%" claim checks out: Fig. 3 peak estimate/true ratio ≈ 1.6–1.8 with r = 4k for k = 64…2048.

---

## 3. Implementation (Python, numpy + matplotlib, in `.venv`)

**Approach (my call):** vectorized simulation over precomputed hashes. Keys are integers 0..n−1; one fixed seeded 64-bit hash (splitmix64) is computed once per key. Every query/subset is a boolean mask, so a sketch of any subset is a reduction over masked precomputed values. This is equivalent to hashing strings (the paper's setup) because only hash values matter.

*Alternatives rejected:* an HLL++ library (adds a dependency, sparse mode irrelevant at n ≫ k, harder to vectorize); per-key Python loops (too slow for k = 2048, r = 8192, n = 100k).

```
src/
  sketches.py    splitmix64 hash; bottom-k (k-th smallest hash, estimate (k-1)/T);
                 HLL with m = 2^p registers (FFGM07 raw estimator + linear counting
                 for small range; 64-bit hash so no large-range correction)
  attack.py      Algorithm 1: r random half-subsets of N, per-key average of
                 T = 1/estimate, returns keys sorted by score
  experiments.py E1–E4 below; writes results/*.json and report/figures/*.pdf (+ .png for slides)
  check.py       sanity checks: hash uniformity, HLL & bottom-k within ~3 std of truth
                 on random sets, attack with r=1 gives ratio ≈ 1
```

Run: `.venv\Scripts\python.exe src\experiments.py`. Fixed seeds throughout so every figure is reproducible.

### Experiments

| ID | Question | Setup | Output |
|----|----------|-------|--------|
| **E1** | Non-adaptive accuracy ≈ 1/√k? | k ∈ {64,128,256,512,1024}; 200 random sets of size 10⁴ (fresh key sets, same hash); NRMSE for bottom-k and HLL | log-log plot of NRMSE vs k with 1/√k and 1.04/√k reference lines |
| **E2** | Attack strength vs #queries r (paper Figs 1–2) | k = 128 and 512 (powers of 2 for HLL; paper used 104/416), n = 5000, r ∈ {1,4,16,…,16384}; estimate on prefixes (ascending score) and suffixes (descending) | estimate vs true size, one curve per r; both sketches |
| **E3** | Attack strength vs k at r = 4k (paper Fig 3, headline claim) | k = 2⁶…2¹¹, n = 10·10^⌈log₁₀k⌉ (paper's rule), r = 4k; 3 seeds | ratio estimate/true vs prefix fraction; table of peak over/under-estimation per k, both sketches |
| **E4** *(optional, only if core finishes in time)* | Does re-randomizing help, and what does it cost? | system rotates hash seed every B queries; attacker keeps accumulating scores; B ∈ {k/4, k, 4k, ∞} | peak ratio vs B; discuss lost mergeability (sketches under different seeds can't be merged) |

Expected runtime: E3 at k = 2048 is ~8k queries × 100k keys of masked reductions — a minute or two in numpy.

---

## 4. Report (`report/main.tex`, CCCG class, latexmk + bibtex)

Header changed (in main.tex, not the .cls) from "CCCG 2020" to "COMP 4801 Project Report". Author block: Ryan Zhu, student no. 101301524 *(my call from the proposal filename — change if you prefer).* Bibliography as `refs.bib`.

| § | Content | Budget |
|---|---------|--------|
| Abstract | 4–5 sentences, incl. our headline number | — |
| 1 Introduction | sketches & mergeability → shared randomness; adaptive vs oblivious (link to Bose et al. Bloom analysis and the MW oblivious/adaptive adversary); problem statement; related work (Hardt–Woodruff, Ben-Eliezer et al., Reviriego–Ting); summary of what we did | 0.6 p |
| 2 Preliminaries | k-mins, bottom-k, k-partition, HLL; sufficient statistic; NRMSE 1/√k; union bound ⇒ exp(k) safe non-adaptive queries, and why it fails when U_i depends on ρ (Problem 1) | 0.7 p |
| 3 Attacks | Algorithm 1 (algorithm box), intuition, Thm 4.1 statement + proof sketch from Appendix A (score–priority correlation, variance bound, Chebyshev; dependence between queries) (Problem 2); §3.2 general estimators: soft-threshold problem, Lemma 6.5 (single batch impossible), Alg 3/Thm 7.1, Alg 4/Thm 8.1, Õ(k²) matching Hassidim et al. (Problem 3) | 1.3 p |
| 4 Experiments | setup; E1, E2, E3 (+E4); comparison with the paper's numbers; honest discussion of differences | 1.2 p, 3–4 figures |
| 5 Conclusion | summary, what I learned, future work: Cohen–Singhal–Stemmer 2025 (breaking the quadratic barrier), per-key query limits | 0.25 p |
| References | 6 from proposal + Hassidim et al. 2020, Heule et al. 2013, Reviriego & Ting 2020 | — |

---

## 5. Presentation (Google Slides, ~14 slides, speaker notes on each)

1. Title · 2. Sketches are everywhere (BigQuery, DataSketches) · 3. How bottom-k / HLL work (one picture) · 4. The hidden assumption: union bound needs queries independent of ρ (callback to Bose et al.) · 5. Adaptive query model · 6. Algorithm 1 in one diagram · 7. Why scores reveal low-hash keys · 8. Theorem 4.1 · 9. E1: non-adaptive works · 10. E2: more queries ⇒ worse · 11. E3: ~4k queries breaks every k (both sketches) · 12. Any estimator: k² attacks, why multiple rounds · 13. Defenses & cost (E4 / CSS 2025) · 14. Takeaways.

**How:** build with the Google Drive/Slides connector (load the google-workspace skill first), figures exported as PNG. **Fallback** if image insertion through the connector fails: generate a .pptx locally and upload it to Drive converted to Slides.

---

## 6. Execution order & checkpoints

1. `sketches.py` + `check.py` → sanity checks pass.
2. `attack.py`, E1–E3 → figures. **Checkpoint: show you the numbers/figures.**
3. Read paper Appendix A; write report; compile; fix to ~4 pages. **Checkpoint: you review the PDF.**
4. Decide on E4 (time permitting) → add to report.
5. Slides in Google Drive. **Checkpoint: you review the deck.**
6. Nothing committed — you commit when happy.
