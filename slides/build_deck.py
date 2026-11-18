"""Build the final presentation as .pptx (uploaded to Drive and converted to Google Slides).

Run: .venv/Scripts/python.exe slides/build_deck.py  ->  slides/deck.pptx
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"

# ---- palette (academic muted; blue/orange match the figures)
BG = "FAFAFA"
DARK = "1B2430"
INK = "1F2328"
MUTED = "5F6368"
BLUE = "2A78D6"
ORANGE = "D2561F"
TINT_B = "E9F1FB"
TINT_O = "FCEDE5"
TINT_N = "F0F0EE"
RULE = "D9D9D6"
HEAD = "Georgia"
BODY = "Arial"

W, H = 13.333, 7.5
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


def rgb(h):
    return RGBColor.from_string(h)


def new_slide(dark=False):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(DARK if dark else BG)
    return s


def text(s, x, y, w, h, paras, size=18, color=INK, bold=False, font=BODY,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, bullets=False, space=6, name=None):
    """paras: str | list[str | list[(text, {opts})]]"""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        par.space_after = Pt(space)
        runs = p if isinstance(p, list) else [(p, {})]
        if bullets:
            pPr = par._p.get_or_add_pPr()
            pPr.set("marL", str(int(Inches(0.28))))
            pPr.set("indent", str(-int(Inches(0.28))))
            bu = pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar",
                                 {"char": "•"})
            pPr.append(bu)
        for t, o in runs:
            r = par.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def title(s, t, dark=False):
    text(s, 0.6, 0.38, 12.1, 1.25, t, size=30, bold=True, font=HEAD,
         color="FFFFFF" if dark else INK, anchor=MSO_ANCHOR.TOP, name="title")


def box(s, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(fill)
    if line:
        sh.line.color.rgb = rgb(line)
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = 0.06
    return sh


def card(s, x, y, w, h, head, body, fill=TINT_N, head_color=INK, body_size=16, head_size=20):
    box(s, x, y, w, h, fill)
    text(s, x + 0.2, y + 0.18, w - 0.4, 0.6, head, size=head_size, bold=True, color=head_color)
    text(s, x + 0.2, y + 0.18 + 0.12 + head_size / 72 * 1.25 * (1 + head.count("\n")),
         w - 0.4, h - 0.9, body, size=body_size, color=INK, bullets=isinstance(body, list), space=8)


def badge(s, x, y, n, fill=BLUE, d=0.5):
    c = box(s, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(n)
    r.font.size, r.font.bold, r.font.name = Pt(18), True, BODY
    r.font.color.rgb = rgb("FFFFFF")


def line(s, x1, y1, x2, y2, color=RULE, width=1.0):
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    ln.line.color.rgb = rgb(color)
    ln.line.width = Pt(width)
    return ln


def picture(s, path, x, y, w=None, h=None):
    """Place an image keeping its aspect ratio, fitting inside w x h."""
    iw, ih = Image.open(path).size
    ar = iw / ih
    if w and h:
        if w / h > ar:
            w = h * ar
        else:
            h = w / ar
    elif w:
        h = w / ar
    else:
        w = h * ar
    return s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h)), w, h


def stat(s, x, y, w, big, label, color=BLUE):
    text(s, x, y, w, 0.9, big, size=44, bold=True, color=color, font=HEAD)
    text(s, x, y + 0.95, w, 0.8, label, size=15, color=MUTED)


def notes(s, t):
    s.notes_slide.notes_text_frame.text = t


def footer(s, t):
    text(s, 0.6, 6.95, 12.1, 0.35, t, size=11, color=MUTED)


# =========================================================== 1. Title
s = new_slide(dark=True)
text(s, 0.8, 1.7, 11.7, 1.9, "Cardinality Sketches under Adaptive Inputs",
     size=44, bold=True, font=HEAD, color="FFFFFF")
text(s, 0.8, 3.55, 11.7, 1.0,
     "Reusing the hash lets about 4k random queries break HyperLogLog",
     size=22, color="C9D6E8")
text(s, 0.8, 5.3, 11.7, 0.5, "Ryan Zhu  ·  COMP 4801 final project  ·  Fall 2026",
     size=16, color="FFFFFF")
text(s, 0.8, 5.8, 11.7, 0.5,
     "Study and replication of Ahmadian & Cohen, “Unmasking Vulnerabilities” (ICML 2024)",
     size=14, color="9FB0C6")
notes(s, "My project is on a 2024 ICML paper by Sara Ahmadian and Edith Cohen. "
         "It shows that cardinality sketches like HyperLogLog, which are accurate on any fixed query, "
         "can be pushed far off by queries that depend on earlier answers. "
         "I'll explain why the usual guarantee breaks, how the attack works and why it needs only a "
         "linear number of queries, and then show my own implementation and experiments, "
         "including one sketch the paper proves things about but never tests.")

# =========================================================== 2. What a sketch is
s = new_slide()
title(s, "A sketch counts distinct keys in a few kilobytes and merges freely")
cw, gap, cy, ch = 3.8, 0.35, 2.0, 3.0
card(s, 0.6, cy, cw, ch, "Small",
     ["k registers, however many keys", "HLL with k = 1024: under 1 KB"], fill=TINT_B, head_color=BLUE,
     body_size=19, head_size=24)
card(s, 0.6 + cw + gap, cy, cw, ch, "Mergeable",
     ["Sketch of U ∪ V from the sketches of U and V",
      "Only works if every sketch uses the same hash"], fill=TINT_B, head_color=BLUE,
     body_size=19, head_size=24)
card(s, 0.6 + 2 * (cw + gap), cy, cw, ch, "Accurate",
     ["Relative error about 1/√k on any fixed set",
      "About 3% at k = 1024"], fill=TINT_B, head_color=BLUE, body_size=19, head_size=24)
text(s, 0.6, 5.4, 12.1, 0.9,
     [[("Used in practice: ", {"bold": True}),
       ("Google BigQuery, Apache DataSketches. The shared, fixed hash is the detail this talk is about.", {})]],
     size=17, color=INK)
notes(s, "A cardinality sketch summarizes a set in k registers and estimates how many distinct keys it has, "
         "with relative error around one over root k. The property that makes sketches popular is that they merge: "
         "the sketch of a union can be computed from the sketches of the parts. That only works if every sketch "
         "in the system uses the same hash functions. So the randomness is chosen once and reused for every query, "
         "and that reuse is exactly what the attack exploits.")

# =========================================================== 3. How sketches work
s = new_slide()
title(s, "Every sketch keeps the lowest-priority keys of the set")
lx0, lx1, ly = 0.9, 7.9, 3.55
line(s, lx0, ly, lx1, ly, color=MUTED, width=1.5)
text(s, lx0 - 0.2, ly + 0.15, 0.5, 0.4, "0", size=14, color=MUTED)
text(s, lx1 - 0.2, ly + 0.15, 0.5, 0.4, "1", size=14, color=MUTED)
pos = [0.03, 0.07, 0.115, 0.16, 0.21, 0.29, 0.34, 0.41, 0.46, 0.52, 0.58, 0.63,
       0.69, 0.74, 0.79, 0.84, 0.9, 0.95]
k = 5
for i, p in enumerate(pos):
    x = lx0 + p * (lx1 - lx0)
    d = 0.2
    box(s, x - d / 2, ly - d / 2, d, d, BLUE if i < k else "B8BEC6", shape=MSO_SHAPE.OVAL)
xk = lx0 + pos[k - 1] * (lx1 - lx0)
text(s, lx0 - 0.1, 2.25, 4.2, 0.9,
     [[("bottom-k sketch: the k = 5 smallest hashes", {"bold": True, "color": BLUE})]], size=16)
line(s, xk, ly - 0.45, xk, ly + 0.45, color=BLUE, width=1.5)
text(s, xk - 0.3, ly + 0.5, 4.5, 0.9,
     ["T = k-th smallest hash", "estimate = (k − 1) / T"], size=16, color=INK, space=2)
text(s, 0.9, 5.3, 7.2, 1.2,
     "More keys in the set push the smallest hashes toward 0, so T shrinks and the estimate grows.",
     size=16, color=MUTED)
card(s, 8.6, 1.95, 4.13, 4.6, "Three designs, one idea",
     [[("Bottom-k: ", {"bold": True}), ("one hash, keep the k smallest values", {})],
      [("k-mins: ", {"bold": True}), ("k hashes, keep each minimum", {})],
      [("HyperLogLog: ", {"bold": True}), ("k buckets, each keeps a rounded minimum (max leading-zero count)", {})]],
     fill=TINT_N)
notes(s, "All these sketches work the same way. Each key gets a random priority from a hash function, "
         "and the sketch keeps the lowest priorities that appear in the set. "
         "In bottom-k you keep the k smallest hash values; if T is the k-th smallest, then k minus one over T "
         "estimates the size. A bigger set has smaller minimums. k-mins uses k separate hashes, and HyperLogLog "
         "splits keys into k buckets and keeps a rounded version of each bucket's minimum. "
         "Important for later: the estimate only depends on a handful of the lowest-priority keys.")

# =========================================================== 4. Hidden assumption
s = new_slide()
title(s, "The guarantee assumes queries never depend on the hash")
cw = 5.9
card(s, 0.6, 1.95, cw, 3.4, "Fixed queries: exponentially many are safe",
     ["Each query fails with probability δ = e^(−Ω(ε²k))",
      "Union bound over r queries: all correct w.p. 1 − rδ",
      "So r can be exponential in k"], fill=TINT_B, head_color=BLUE, head_size=19)
card(s, 0.6 + cw + 0.3, 1.95, cw, 3.4, "Adaptive queries: the bound is gone",
     ["Query Uᵢ depends on earlier answers, so on the hash",
      "“The answer on Uᵢ is bad” is no longer an event about a fixed set",
      "A union bound over all 2^|N| possible sets says nothing"],
     fill=TINT_O, head_color=ORANGE, head_size=19)
text(s, 0.6, 5.65, 12.1, 1.0,
     [[("Same mistake as the Bloom filter p", {}), ("k", {"size": 12}),
       (" bound (Bose et al. 2008): ", {}),
       ("treating events that share one random object as independent.", {"bold": True})]],
     size=17, color=INK)
notes(s, "Why are sketches safe at all? For one fixed set, a sketch of size k fails with probability exponentially "
         "small in k. If the queries are fixed before the hash is drawn, a union bound over r queries says they are "
         "all fine unless r is exponential in k. "
         "But if the next query depends on earlier answers, it depends on the hash. The bad event is no longer about "
         "a fixed set, and the union bound would have to cover every set the adversary might pick, which is useless. "
         "This is the same kind of error we saw with Bloom filters in class, where the k probed bits all read one "
         "shared array, and it's the oblivious versus adaptive adversary distinction from the multiplicative weights unit.")

# =========================================================== 5. Algorithm 1
s = new_slide()
title(s, "Algorithm 1: query random halves, then sort keys by average score")
steps = [("Fix a ground set", "n keys, n ≫ k, chosen without looking at the hash"),
         ("Random halves", "r queries, each key in U with prob. 1/2"),
         ("Score every key", "T = 1/estimate, added to every key in U"),
         ("Sort by average", "A[x] = average T over queries containing x")]
bw, bg, by, bh = 2.75, 0.37, 1.95, 2.35
for i, (h_, b_) in enumerate(steps):
    x = 0.6 + i * (bw + bg)
    box(s, x, by, bw, bh, TINT_N)
    badge(s, x + 0.2, by + 0.2, i + 1)
    text(s, x + 0.2, by + 0.82, bw - 0.4, 0.5, h_, size=18, bold=True)
    text(s, x + 0.2, by + 1.3, bw - 0.4, 1.0, b_, size=15, color=INK)
    if i < 3:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.06), Inches(by + bh / 2 - 0.13),
                               Inches(0.25), Inches(0.26))
        a.fill.solid(); a.fill.fore_color.rgb = rgb(MUTED); a.line.fill.background()
ow = 5.9
card(s, 0.6, 4.65, ow, 1.6, "Lowest scores first → overestimated",
     "They are the low-hash keys: a small set with the sketch of all of N.", fill=TINT_B,
     head_color=BLUE, head_size=18)
card(s, 0.6 + ow + 0.3, 4.65, ow, 1.6, "Highest scores first → underestimated",
     "They avoid the low-hash keys: a large set that looks small.", fill=TINT_O,
     head_color=ORANGE, head_size=18)
footer(s, "All r queries are chosen in advance (one batch). Only the final sort uses the answers.")
notes(s, "Here is the whole attack. Pick a ground set of n keys, much bigger than k. Ask r queries, each a "
         "uniformly random half of the ground set. For each answer, compute T, one over the estimate, and add it to the "
         "score of every key in that query. At the end, sort keys by their average score. "
         "The keys with the lowest scores are the low-hash keys, so a prefix of the order is a small set whose sketch "
         "looks like the sketch of everything: it's overestimated. The keys with the highest scores avoid those keys, "
         "so a suffix is underestimated. Note the queries don't adapt at all; only the post-processing does.")

# =========================================================== 6. Why it works
s = new_slide()
title(s, "Low-hash keys shrink T whenever they are present, so their scores drop")
text(s, 0.6, 1.95, 5.6, 4.6,
     [[("A low-hash key sets the sketch whenever it is in U, so T is smaller on those queries.", {})],
      [("A high-hash key almost never affects the sketch; its average is just the overall mean.", {})],
      [("Averaging over about r/2 queries shrinks the noise by √r until the gap shows.", {})]],
     size=18, bullets=True, space=14)
sx = 6.8
box(s, sx, 1.95, 5.93, 4.6, TINT_N)
stat(s, sx + 0.35, 2.2, 2.6, "≈ 1/n", "gap in T per query (signal)")
stat(s, sx + 3.1, 2.2, 2.6, "≈ √k / n", "spread of T per query (noise)")
stat(s, sx + 0.35, 4.3, 5.3, "Θ(k) queries", "signal/noise = 1/√k, so averaging Θ(k) queries separates the keys",
     color=ORANGE)
notes(s, "Why does averaging work? If a key is one of the lowest-priority keys, then whenever it's in the query it "
         "determines part of the sketch, so the sketch looks bigger and T is smaller. A transparent key almost never "
         "matters, so its average is just the overall mean. "
         "The size of the effect: the gap in T is on the order of one over n, while the natural spread of T is about "
         "root k over n. The per-query signal-to-noise ratio is one over root k, so averaging order k queries is enough. "
         "That's why the attack is linear in the sketch size.")

# =========================================================== 7. Theorem
s = new_slide()
title(s, "Theorem 4.1: O(k/α²) queries give a 1/α overestimate")
box(s, 0.6, 1.95, 12.1, 1.55, TINT_B)
text(s, 0.85, 2.08, 11.6, 1.35,
     [[("For k-mins or bottom-k with T = 1/estimate: with n = Ω((k/α) log kr) and r = O(k/α²), "
        "with probability 0.99 the αn lowest-score keys U", {}), ("α", {"size": 13}),
       (" have E[estimate] = Θ(n), i.e. the sketch is biased up by Ω(1/α).", {})]],
     size=18, color=INK)
proof = [("Good draws", "Low-rank keys are distinct across hashes; every query hits each hash's L lowest keys"),
         ("Signal", "Conditioning on a minimum key lowers E[Z] by ≥ δ/3n (exponential order statistics)"),
         ("Noise", "Var[Z | u ∈ U] = O(k/n²): a sum of k terms of scale 1/n"),
         ("Chebyshev", "r' = O(k/α) queries per key separate minimum keys from transparent ones")]
pw = 2.83
for i, (h_, b_) in enumerate(proof):
    x = 0.6 + i * (pw + 0.26)
    badge(s, x, 3.85, i + 1)
    text(s, x + 0.62, 3.88, pw - 0.62, 0.5, h_, size=18, bold=True)
    text(s, x, 4.5, pw, 2.0, b_, size=15, color=INK)
footer(s, "Proof outline from Appendix A of Ahmadian & Cohen (2024). The O(k) count matches the trivial upper bound.")
notes(s, "Formally, Theorem 4.1 says that with r on the order of k over alpha squared queries, the alpha n lowest-score "
         "keys have an expected estimate of order n, so the estimate is too big by a factor of one over alpha. "
         "The proof has four steps. First, with a big enough ground set, the low-rank keys behave independently. "
         "Second, conditioning on a minimum key being present lowers the expected statistic by about one over n. "
         "Third, the variance is order k over n squared. Fourth, Chebyshev's inequality says order k over alpha "
         "samples per key separate the minimum keys from the rest.")

# =========================================================== 8. E1
s = new_slide()
title(s, "Without adaptivity both of our sketches stay near 1/√k error")
pic, pw_, ph_ = picture(s, FIG / "fig_e1_accuracy.png", 0.6, 1.9, w=6.9, h=4.8)
text(s, 7.9, 2.1, 4.8, 4.4,
     [[("Bottom-k: ", {"bold": True}), ("within 4% of 1/√k", {})],
      [("HLL: ", {"bold": True}), ("within 12%, close to its theoretical 1.04/√k", {})],
      [("Each point: 200 random sets of 10,000 keys", {})],
      [("Any large error later comes from the attack, not from noise", {"bold": True})]],
     size=18, bullets=True, space=14)
notes(s, "Now my experiments. I implemented bottom-k and HyperLogLog in Python with numpy, using one fixed seeded "
         "64-bit hash. First the sanity check: on random sets that don't depend on the hash, the error of both sketches "
         "follows one over root k from k equals 64 to 2048. So the implementations are correct, and anything we see "
         "next is caused by adaptivity.")

# =========================================================== 9. E2
s = new_slide()
title(s, "16,384 queries make 594 keys look like 5,298")
pic, pw_, ph_ = picture(s, FIG / "fig_e2_k128.png", 0.6, 1.75, w=12.1, h=5.0)
footer(s, "k = 128, ground set n = 5,000 keys. Dashed line: perfect estimate. Repeats Figures 1–2 of the paper.")
notes(s, "This repeats the paper's first experiment with k equals 128 and 5,000 keys. Each curve is a different number "
         "of attack queries, from 1 in light blue to 16,384 in dark blue. The x-axis is the true size of the set we "
         "build by adding keys in score order, and the y-axis is what the sketch says. "
         "With one query we sit on the diagonal. As r grows the left-hand curves shoot up: for HLL, with 16,384 "
         "queries, a set of 594 keys is estimated at almost 5,300, the size of the whole ground set. Bottom-k breaks "
         "even faster; at 4,096 queries 255 keys already look like 5,250. On the right, the high-score keys are "
         "underestimated by about a factor of three.")

# =========================================================== 10. E3
s = new_slide()
title(s, "With r = 4k queries the attack works equally well at every sketch size")
pic, pw_, ph_ = picture(s, FIG / "fig_e3_sizes.png", 0.6, 1.75, w=12.1, h=3.35)
sy = 5.3
sw = 3.0
stat(s, 0.7, sy, sw, "2.2×", "HLL overestimate (lowest-score 20–30% of N)")
stat(s, 0.7 + sw + 0.05, sy, sw, "0.53×", "HLL underestimate (highest-score keys)")
stat(s, 0.7 + 2 * (sw + 0.05), sy, sw, "≈ 5×", "bottom-k overestimate", color=ORANGE)
stat(s, 0.7 + 3 * (sw + 0.05), sy, sw, "64–2048", "values of k tested, same curves", color=MUTED)
notes(s, "This repeats the paper's headline experiment. For each k from 64 to 2048 I run 4k queries, three seeds each. "
         "Solid lines are the low-score prefixes, dashed lines the high-score ones. The striking thing is that the curves "
         "for different k lie on top of each other. If the budget grows linearly with k, the attack is equally "
         "effective at every size, which is the O(k) result in practice. HLL is off by about 2.2 times upward and "
         "about half downward; bottom-k is overestimated by about five times.")

# =========================================================== 11. Comparison
s = new_slide()
title(s, "We reproduce the paper's claim; our HLL attack is somewhat stronger")
rows = [["", "Sketch", "Peak over", "Peak at", "Worst under"],
        ["Paper", "HLL++", "1.6–1.8×", "20–40% of N", "≈ 40% error"],
        ["Ours", "HLL", "2.0–2.7×", "21–38% of N", "0.51–0.54×"],
        ["Ours", "bottom-k", "3.8–5.6×", "9–16% of N", "0.49–0.53×"]]
cols = [1.6, 2.0, 2.4, 2.6, 2.4]
tx, ty, rh = 0.6, 1.95, 0.55
tbl = s.shapes.add_table(len(rows), len(cols), Inches(tx), Inches(ty), Inches(sum(cols)), Inches(rh * len(rows))).table
tbl.first_row = False
tbl.horz_banding = False
for j, c in enumerate(cols):
    tbl.columns[j].width = Inches(c)
for i, row in enumerate(rows):
    tbl.rows[i].height = Inches(rh)
    for j, v in enumerate(row):
        cell = tbl.cell(i, j)
        cell.fill.solid(); cell.fill.fore_color.rgb = rgb(TINT_B if i == 2 else BG)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT if j < 2 else PP_ALIGN.RIGHT
        r = tf.paragraphs[0].add_run(); r.text = v
        r.font.size = Pt(17); r.font.name = BODY; r.font.color.rgb = rgb(INK)
        r.font.bold = (i == 0 or j == 0)
for i in range(1, len(rows)):
    line(s, tx, ty + i * rh, tx + sum(cols), ty + i * rh, color=RULE if i > 1 else MUTED)
text(s, 0.6, 4.45, 12.1, 2.2,
     [[("Same shape, same peak location, same independence from k. ", {"bold": True}),
       ("Our peaks are higher; we did not isolate why (HLL++ details, k = 128 vs 104, averaging over seeds).", {})],
      [("Bottom-k is about twice as vulnerable as HLL. ", {"bold": True}),
       ("Our explanation: HLL stores rounded ranks, so several keys tie for a register and one key’s presence often changes nothing.", {})]],
     size=17, bullets=True, space=12)
notes(s, "Comparing with the paper. They report that 4k queries give about 40 percent error on HLL++, and their curves "
         "peak at about 1.6 to 1.8 at 20 to 40 percent of the ground set. My HLL curves have the same shape and peak in "
         "the same place, but peak a bit higher, around 2 to 2.7. I haven't pinned down why; it could be details of their "
         "HLL++ implementation, the slightly different k values, or that I average over seeds. "
         "The new result is bottom-k, the sketch the theorem is actually proved for, which is about twice as vulnerable. "
         "My explanation is that HLL rounds its values, so several keys often tie for a register and removing one "
         "doesn't change anything, which weakens the signal.")

# =========================================================== 12. k^2
s = new_slide()
title(s, "Any estimator falls to Õ(k²) adaptive queries, never to one batch")
items = [("One batch is not enough", "Lemma 6.5",
          "A smart estimator can answer from k' = O(log 1/δ) components; one batch only learns those."),
         ("Symmetric estimators", "Algorithm 3, Thm 7.1",
          "Per-query gap is only Õ(1/k), so one batch needs Õ(k²) queries to separate keys."),
         ("Any correct estimator", "Algorithm 4, Thm 8.1",
          "Grow a mask M of low-hash keys; then S(M ∪ U) ≈ S(M) hides |U|. Õ(k²) adaptive queries.")]
cw = 3.85
for i, (h_, ref, b_) in enumerate(items):
    x = 0.6 + i * (cw + 0.275)
    box(s, x, 1.95, cw, 3.6, TINT_N)
    badge(s, x + 0.25, 2.2, i + 1, fill=ORANGE if i == 2 else BLUE)
    text(s, x + 0.25, 2.85, cw - 0.5, 0.5, h_, size=19, bold=True)
    text(s, x + 0.25, 3.35, cw - 0.5, 0.4, ref, size=14, color=MUTED)
    text(s, x + 0.25, 3.85, cw - 0.5, 1.6, b_, size=16)
text(s, 0.6, 5.85, 12.1, 0.8,
     [[("Tight: ", {"bold": True}),
       ("Hassidim et al. (2020) make any sketch robust to r² adaptive queries with Õ(r) copies.", {})]],
     size=17)
notes(s, "Algorithm 1 relies on the estimator reporting its best guess. What about a cleverer estimator? "
         "The paper gives the estimator every advantage and shows three things. One batch can never work, because the "
         "estimator can answer from a small piece of the sketch and the attacker only learns about that piece. "
         "Against symmetric estimators, one batch of about k squared queries works, because the signal per query is now "
         "only one over k. And against any correct estimator, an adaptive attack grows a mask of low-hash keys, "
         "after which the mask's sketch hides any set added to it. That takes about k squared queries, which matches the "
         "generic upper bound, so it's tight.")

# =========================================================== 13. Mitigation
s = new_slide()
title(s, "Fresh randomness stops the attack but breaks merging")
pic, pw_, ph_ = picture(s, FIG / "fig_e4_mitigation.png", 0.6, 1.9, w=7.0, h=4.8)
text(s, 7.9, 2.0, 4.8, 4.6,
     [[("The system re-draws its hash every B queries; the attacker keeps scoring", {})],
      [("B ≤ k/2: ", {"bold": True}), ("back to noise level (≤ 1.3× over)", {})],
      [("B = 2k: ", {"bold": True}), ("HLL drops from 2.3× to 1.5×", {})],
      [("Cost: ", {"bold": True, "color": ORANGE}),
       ("sketches under different hashes cannot be merged, so stored sketches must be rebuilt from raw data", {})]],
     size=17, bullets=True, space=14)
notes(s, "I also tried the obvious defense: the system draws a new hash every B queries, and I evaluate the attacker's "
         "sets under the hash in use at the end. If B is at most k over 2 the attack is back to noise level, and even "
         "at 2k it's weakened a lot. But the price is the very thing sketches are for: sketches built with different "
         "hashes can't be merged, so you'd have to rebuild every stored sketch from the raw data, or keep separate copies, "
         "which costs space linear in the number of queries.")

# =========================================================== 14. Takeaways
s = new_slide(dark=True)
title(s, "Takeaways", dark=True)
pts = [("Guarantees are per fixed query.", " Reusing one hash for mergeability lets answers leak it."),
       ("Breaking standard estimators takes O(k) queries.", " 4k random queries and an average push HLL off by about 2× at every k, and bottom-k by about 5×."),
       ("Breaking any estimator takes Õ(k²) queries.", " Multiple rounds are necessary, and the bound is tight."),
       ("Next:", " robust estimators that limit how often each key is queried (Cohen, Singhal & Stemmer, ICML 2025).")]
for i, (b_, t_) in enumerate(pts):
    y = 1.9 + i * 1.2
    badge(s, 0.7, y + 0.05, i + 1)
    text(s, 1.45, y, 11.2, 1.1, [[(b_, {"bold": True, "color": "FFFFFF"}), (t_, {"color": "C9D6E8"})]], size=19)
notes(s, "To wrap up. Sketch guarantees hold for queries fixed in advance, and because sketches must reuse one hash "
         "to be mergeable, adaptive queries can learn it. Against the standard estimators that takes only a linear "
         "number of queries, and in my experiments 4k random queries push HLL off by about a factor of two at every "
         "sketch size, and bottom-k by five. Against any estimator it takes about k squared adaptive queries. "
         "The open direction is robust estimators; Cohen, Singhal and Stemmer showed in 2025 that limiting how often "
         "each key appears in queries gets past the quadratic barrier. Thanks, happy to take questions.")

# =========================================================== 15. References
s = new_slide()
title(s, "References")
refs = ["S. Ahmadian, E. Cohen. Unmasking Vulnerabilities: Cardinality Sketches under Adaptive Inputs. ICML 2024.",
        "E. Cohen, M. Singhal, U. Stemmer. Breaking the Quadratic Barrier: Robust Cardinality Sketches for Adaptive Queries. ICML 2025.",
        "P. Flajolet, É. Fusy, O. Gandouet, F. Meunier. HyperLogLog. AofA 2007.",
        "P. Bose et al. On the False-Positive Rate of Bloom Filters. IPL 2008.",
        "A. Hassidim, H. Kaplan, Y. Mansour, Y. Matias, U. Stemmer. Adversarially Robust Streaming Algorithms via Differential Privacy. NeurIPS 2020.",
        "M. Hardt, D. P. Woodruff. How Robust Are Linear Sketches to Adaptive Inputs? STOC 2013.",
        "O. Ben-Eliezer, R. Jayaram, D. P. Woodruff, E. Yogev. A Framework for Adversarially Robust Streaming Algorithms. PODS 2020."]
text(s, 0.6, 1.8, 12.1, 5.0, refs, size=14, color=INK, bullets=True, space=8)
notes(s, "References for the talk; full list in the report.")

out = HERE / "deck.pptx"
prs.save(out)
print("wrote", out, len(prs.slides._sldIdLst), "slides")
