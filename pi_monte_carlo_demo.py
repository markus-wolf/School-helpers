"""Interactive animation: estimate π with the Monte Carlo method.

Throw random dots into a square that contains an inscribed circle. The fraction
of dots landing inside the circle estimates the ratio of areas, so
π ≈ 4 × (hits / total).

Run with (pyenv + .venv):
    source .venv/bin/activate
    python pi_monte_carlo_demo.py

Setup once:
    pyenv install -s
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from matplotlib.widgets import Button, CheckButtons, Slider, TextBox

# ── constants ─────────────────────────────────────────────────────────────────
_R = 1.0
_SQUARE_HALF = 1.0
_N_DOTS_MIN = 100
_N_DOTS_MAX = 200_000
_N_DOTS_INIT = 10_000
_LOG_N_MIN = math.log(_N_DOTS_MIN)
_LOG_N_SPAN = math.log(_N_DOTS_MAX) - _LOG_N_MIN
_BATCH_MIN = 1
_BATCH_MAX = 500
_BATCH_INIT = 40
_TICK_MS = 25
_DOTS_PER_SEC_INIT = 800.0
_DOTS_PER_SEC_MIN = 50.0
_DOTS_PER_SEC_MAX = 20_000.0
_LOG_RATE_MIN = math.log(_DOTS_PER_SEC_MIN)
_LOG_RATE_SPAN = math.log(_DOTS_PER_SEC_MAX) - _LOG_RATE_MIN

# high-contrast UI palette (matches circle_area_peel_demo)
_C_N = "#FDA4AF"   # coral — total dots
_C_H = "#6EE7B7"   # mint — hits inside
_C_P = "#7DD3FC"   # sky — ratio p
_C_PI = "#FCD34D"  # gold — π estimate
_C_ERR = "#F0ABFC" # magenta — error
_C_TRUE = "#4ADE80"
_C_WHITE = "#F9FAFB"
_C_LABEL = "#E5E7EB"
_C_PROOF = "#4ADE80"
_C_INK = "#111827"
_C_EDGE = "#1F2937"
_C_OUT = "#F87171"   # outside dots
_C_IN = "#34D399"    # inside dots

# layout — 2/3 left (canvas + sliders) | 1/3 right (readout + checkboxes)
_MX, _MY = 0.02, 0.03
_GUTTER = 0.012
_COL_W = 1.0 - 2 * _MX - _GUTTER
_LEFT_W = _COL_W * 2 / 3
_RIGHT_W = _COL_W / 3
_LEFT_X = _MX
_RIGHT_X = _MX + _LEFT_W + _GUTTER
_CTRL_H = 0.27
_TOP_GAP = 0.012
_TOP_H = 1.0 - 2 * _MY - _CTRL_H - _TOP_GAP

_CANVAS = [_LEFT_X, _MY + _CTRL_H + _TOP_GAP, _LEFT_W, _TOP_H]
_CTRL_BG = [_LEFT_X, _MY, _LEFT_W, _CTRL_H]
_RD_BOX = [_RIGHT_X, _MY + _CTRL_H + _TOP_GAP, _RIGHT_W, _TOP_H]
_CTRL_CHK = [_RIGHT_X, _MY, _RIGHT_W, _CTRL_H]

_ROW_L = _LEFT_X + 0.030
_ROW_R = _LEFT_X + _LEFT_W - 0.025
_SL_GAP = 0.010
_LBL_COL = 0.088
_TB_W, _SL_H, _TB_H = 0.070, 0.030, 0.030
_LBL_FS = 9
_LBL_X = _ROW_R
_TB_X = _ROW_R - _LBL_COL - _SL_GAP - _TB_W
_SL_X = _ROW_L
_SL_W = _TB_X - _SL_GAP - _SL_X
_SL_YS = (0.22, 0.175, 0.130, 0.085)
_SL_LABELS = ("Dots / sec", "Batch size", "Max dots", "Seed")

_RD_FS_SYM = 17
_RD_FS_VAL = 17
_RD_FS_SM = 15
_RD_FS_DESC = 8
_RD_FS_TITLE = 11
_RD_FS_PROOF = 8.5
_RD_FS_FORM = 11
_RD_FS_CMP = 7.5
_SYM_X, _VAL_X, _DESC_X = 0.08, 0.22, 0.97


def _target_from_slider(s: float) -> int:
    n = round(math.exp(_LOG_N_MIN + max(0.0, min(1.0, s)) * _LOG_N_SPAN))
    return max(_N_DOTS_MIN, min(_N_DOTS_MAX, n))


def _slider_from_target(n: int) -> float:
    n = max(_N_DOTS_MIN, min(_N_DOTS_MAX, int(n)))
    return (math.log(n) - _LOG_N_MIN) / _LOG_N_SPAN


def _rate_from_slider(s: float) -> float:
    r = math.exp(_LOG_RATE_MIN + max(0.0, min(1.0, s)) * _LOG_RATE_SPAN)
    return max(_DOTS_PER_SEC_MIN, min(_DOTS_PER_SEC_MAX, r))


def _slider_from_rate(r: float) -> float:
    r = max(_DOTS_PER_SEC_MIN, min(_DOTS_PER_SEC_MAX, float(r)))
    return (math.log(r) - _LOG_RATE_MIN) / _LOG_RATE_SPAN


def _inside_circle(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    return xs * xs + ys * ys <= _R * _R + 1e-12


def _estimate_pi(hits: int, total: int) -> float:
    if total <= 0:
        return float("nan")
    return 4.0 * hits / total


def _sigma_pct(total: int) -> float:
    """Expected 1σ of percent deviation |π̂−π|/π at *total* dots (true p = π/4)."""
    if total <= 0:
        return float("nan")
    p = math.pi / 4.0
    sigma_pi = 4.0 * math.sqrt(p * (1.0 - p) / total)
    return 100.0 * sigma_pi / math.pi


# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 7.8), facecolor="#F0EEEA")
fig.canvas.manager.set_window_title("Estimate π: Monte Carlo Darts")

ctrl_bg = fig.add_axes(_CTRL_BG, zorder=-1)
ctrl_bg.set_facecolor("#E4E2DC")
ctrl_bg.set_xticks([])
ctrl_bg.set_yticks([])
ctrl_bg.set_navigate(False)
for _sp in ctrl_bg.spines.values():
    _sp.set_color("#9CA3AF")
    _sp.set_linewidth(1.2)

ax = fig.add_axes(_CANVAS)
ax.set_facecolor("#FAFAF8")
ax.set_aspect("equal")
ax.axis("off")

# static square + circle (drawn once)
_square = Rectangle(
    (-_SQUARE_HALF, -_SQUARE_HALF), 2 * _SQUARE_HALF, 2 * _SQUARE_HALF,
    fill=False, edgecolor=_C_EDGE, linewidth=2.0, zorder=2,
)
_circle = Circle(
    (0.0, 0.0), _R, fill=False, edgecolor="#2563EB",
    linewidth=2.2, linestyle="--", zorder=3,
)
ax.add_patch(_square)
ax.add_patch(_circle)
ax.set_xlim(-1.45, 1.45)
ax.set_ylim(-1.45, 1.45)

_scatter_out = ax.scatter([], [], s=5, c=_C_OUT, alpha=0.55,
                          edgecolors="none", zorder=4)
_scatter_in = ax.scatter([], [], s=5, c=_C_IN, alpha=0.75,
                         edgecolors="none", zorder=5)

# ── live readout panel ────────────────────────────────────────────────────────
rd = fig.add_axes(_RD_BOX)
rd.set_axis_off()
rd.add_patch(Rectangle(
    (0.0, 0.0), 1.0, 1.0, transform=rd.transAxes,
    facecolor="#111827", edgecolor="none", zorder=0,
))
rd.add_patch(FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
    fill=False, edgecolor="#93C5FD", linewidth=2.5,
    transform=rd.transAxes, clip_on=False, zorder=10,
))
rd.add_patch(Rectangle(
    (0.02, 0.925), 0.96, 0.065, transform=rd.transAxes,
    facecolor="#1D4ED8", edgecolor="none", zorder=9,
))
rd.text(0.5, 0.958, "MONTE CARLO π", ha="center", va="center",
        color="#FFFFFF", fontsize=_RD_FS_TITLE, fontweight="bold",
        transform=rd.transAxes, family="monospace")

for y, col, lw in [(0.885, "#6B7280", 1.5), (0.555, "#4B5563", 1.0),
                   (0.240, "#4B5563", 1.0)]:
    rd.add_artist(Line2D([0.04, 0.96], [y, y], color=col, lw=lw,
                         transform=rd.transAxes, zorder=5))

for y, sym, col, desc in [
    (0.820, "N", _C_N, "dots thrown"),
    (0.710, "H", _C_H, "inside circle"),
    (0.600, "p", _C_P, "p = H / N"),
    (0.490, "π̂", _C_PI, "4 × p"),
    (0.380, "ε", _C_ERR, "|π̂ − π|"),
]:
    rd.text(_SYM_X, y, sym, ha="left", va="center", color=col,
            fontsize=_RD_FS_SYM, fontweight="bold", transform=rd.transAxes,
            family="monospace", zorder=11)
    rd.text(_DESC_X, y, desc, ha="right", va="center", color=_C_LABEL,
            fontsize=_RD_FS_DESC, transform=rd.transAxes, zorder=11)

_rd_n = rd.text(_VAL_X, 0.820, "0", ha="left", va="center",
                color=_C_N, fontsize=_RD_FS_VAL, fontweight="bold",
                transform=rd.transAxes, family="monospace", zorder=11)
_rd_h = rd.text(_VAL_X, 0.710, "0", ha="left", va="center",
                color=_C_H, fontsize=_RD_FS_VAL, fontweight="bold",
                transform=rd.transAxes, family="monospace", zorder=11)
_rd_p = rd.text(_VAL_X, 0.600, "—", ha="left", va="center",
                color=_C_P, fontsize=_RD_FS_VAL, fontweight="bold",
                transform=rd.transAxes, family="monospace", zorder=11)
_rd_pi = rd.text(_VAL_X, 0.490, "—", ha="left", va="center",
                 color=_C_PI, fontsize=_RD_FS_VAL, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_err = rd.text(_VAL_X, 0.380, "—", ha="left", va="center",
                  color=_C_ERR, fontsize=_RD_FS_VAL, fontweight="bold",
                  transform=rd.transAxes, family="monospace", zorder=11)
_rd_true = rd.text(_VAL_X, 0.318, f"{math.pi:.6f}", ha="left", va="center",
                   color=_C_TRUE, fontsize=_RD_FS_SM, fontweight="bold",
                   transform=rd.transAxes, family="monospace", zorder=11)
_rd_dev = rd.text(_VAL_X, 0.268, "—", ha="left", va="center",
                   color="#C4B5FD", fontsize=_RD_FS_SM, fontweight="bold",
                   transform=rd.transAxes, family="monospace", zorder=11)
_rd_sigma = rd.text(_VAL_X, 0.218, "—", ha="left", va="center",
                    color="#A5B4FC", fontsize=_RD_FS_SM, fontweight="bold",
                    transform=rd.transAxes, family="monospace", zorder=11)

rd.text(_SYM_X, 0.318, "π", ha="left", va="center", color=_C_TRUE,
        fontsize=_RD_FS_SM, fontweight="bold", transform=rd.transAxes,
        family="monospace", zorder=11)
rd.text(_DESC_X, 0.318, "true value", ha="right", va="center", color=_C_LABEL,
        fontsize=_RD_FS_DESC, transform=rd.transAxes, zorder=11)
rd.text(_SYM_X, 0.268, "%", ha="left", va="center", color="#C4B5FD",
        fontsize=_RD_FS_SM, fontweight="bold", transform=rd.transAxes,
        family="monospace", zorder=11)
rd.text(_DESC_X, 0.268, "|π̂ − π| / π", ha="right", va="center",
        color=_C_LABEL, fontsize=_RD_FS_DESC, transform=rd.transAxes, zorder=11)
rd.text(_SYM_X, 0.218, "σ", ha="left", va="center", color="#A5B4FC",
        fontsize=_RD_FS_SM, fontweight="bold", transform=rd.transAxes,
        family="monospace", zorder=11)
rd.text(_DESC_X, 0.218, "expected ±1σ wobble", ha="right", va="center",
        color=_C_LABEL, fontsize=_RD_FS_DESC, transform=rd.transAxes, zorder=11)

rd.text(0.5, 0.178, "the idea", ha="center", va="center",
        color=_C_WHITE, fontsize=_RD_FS_PROOF, fontweight="bold",
        transform=rd.transAxes, zorder=11)
_rd_step1 = rd.text(0.5, 0.138, "random dots fill the square",
                    ha="center", va="center", color=_C_WHITE,
                    fontsize=_RD_FS_PROOF, transform=rd.transAxes, zorder=11)
_rd_step2 = rd.text(0.5, 0.098, "count how many land in the circle",
                    ha="center", va="center", color=_C_WHITE,
                    fontsize=_RD_FS_PROOF, transform=rd.transAxes, zorder=11)
_rd_formula = rd.text(
    0.5, 0.055,
    "π ≈ 4 × (circle area / square area) = 4 × H/N",
    ha="center", va="center", color=_C_PROOF,
    fontsize=_RD_FS_FORM, fontweight="bold", transform=rd.transAxes,
    family="monospace", zorder=11,
)
_rd_area_cmp = rd.text(0.5, 0.018, "", ha="center", va="center",
                       color=_C_LABEL, fontsize=_RD_FS_CMP, transform=rd.transAxes,
                       family="monospace", zorder=11)

# ── sliders + text boxes ──────────────────────────────────────────────────────
for _lbl, _y in zip(_SL_LABELS, _SL_YS):
    fig.text(_LBL_X, _y + _SL_H / 2, _lbl,
             transform=fig.transFigure, ha="right", va="center",
             fontsize=_LBL_FS, fontweight="bold", color=_C_INK)

ax_rate = fig.add_axes([_SL_X, _SL_YS[0], _SL_W, _SL_H])
ax_tb_rate = fig.add_axes([_TB_X, _SL_YS[0], _TB_W, _TB_H])
ax_batch = fig.add_axes([_SL_X, _SL_YS[1], _SL_W, _SL_H])
ax_tb_batch = fig.add_axes([_TB_X, _SL_YS[1], _TB_W, _TB_H])
ax_target = fig.add_axes([_SL_X, _SL_YS[2], _SL_W, _SL_H])
ax_tb_target = fig.add_axes([_TB_X, _SL_YS[2], _TB_W, _TB_H])
ax_seed = fig.add_axes([_SL_X, _SL_YS[3], _SL_W, _SL_H])
ax_tb_seed = fig.add_axes([_TB_X, _SL_YS[3], _TB_W, _TB_H])

sl_rate = Slider(ax_rate, "", 0.0, 1.0,
                 valinit=_slider_from_rate(_DOTS_PER_SEC_INIT),
                 color="#7C3AED", track_color="#6B7280")
sl_batch = Slider(ax_batch, "", _BATCH_MIN, _BATCH_MAX,
                  valinit=_BATCH_INIT, color="#DB2777", track_color="#6B7280")
sl_target = Slider(ax_target, "", 0.0, 1.0,
                   valinit=_slider_from_target(_N_DOTS_INIT),
                   color="#2563EB", track_color="#6B7280")
sl_seed = Slider(ax_seed, "", 0, 9999, valinit=42,
                 valstep=1, color="#0284C7", track_color="#6B7280")

_TB_BG, _TB_HOVER = "#1E293B", "#334155"
tb_rate = TextBox(ax_tb_rate, "", initial=f"{_DOTS_PER_SEC_INIT:.0f}",
                  color=_TB_BG, hovercolor=_TB_HOVER)
tb_batch = TextBox(ax_tb_batch, "", initial=str(_BATCH_INIT),
                   color=_TB_BG, hovercolor=_TB_HOVER)
tb_target = TextBox(ax_tb_target, "", initial=str(_N_DOTS_INIT),
                    color=_TB_BG, hovercolor=_TB_HOVER)
tb_seed = TextBox(ax_tb_seed, "", initial="42",
                  color=_TB_BG, hovercolor=_TB_HOVER)
_TEXTBOXES = (tb_rate, tb_batch, tb_target, tb_seed)

for _sax, _sl in zip((ax_rate, ax_batch, ax_target, ax_seed),
                     (sl_rate, sl_batch, sl_target, sl_seed)):
    _sax.set_zorder(2)
    _sax.set_facecolor("#E4E2DC")
    _sax.set_xticks([])
    _sl.valtext.set_visible(False)

for _ax in (ax_tb_rate, ax_tb_batch, ax_tb_target, ax_tb_seed):
    _ax.set_zorder(3)

for _tb in _TEXTBOXES:
    try:
        _tb.text_disp.set_color("#F9FAFB")
        _tb.text_disp.set_fontsize(10)
        _tb.text_disp.set_fontfamily("monospace")
    except AttributeError:
        pass


def _batch_for_tick() -> int:
    rate = _rate_from_slider(sl_rate.val)
    from_rate = max(1, int(round(rate * _TICK_MS / 1000.0)))
    cap = int(round(sl_batch.val))
    return max(_BATCH_MIN, min(_BATCH_MAX, cap, from_rate))


ax_btn_play = fig.add_axes([_SL_X, 0.035, 0.12, 0.042])
ax_btn_reset = fig.add_axes([_SL_X + 0.135, 0.035, 0.12, 0.042])
btn_play = Button(ax_btn_play, "▶  Throw", color="#BFDBFE", hovercolor="#93C5FD")
btn_reset = Button(ax_btn_reset, "Reset", color="#FFFFFF", hovercolor="#E5E7EB")
for _bax in (ax_btn_play, ax_btn_reset):
    _bax.set_zorder(2)
    _bax.set_facecolor("#FFFFFF")
    for _sp in _bax.spines.values():
        _sp.set_color("#64748B")
        _sp.set_linewidth(1.5)

_CHK_PAD = 0.02
chk_bg = fig.add_axes(_CTRL_CHK, zorder=-1)
chk_bg.set_facecolor("#E4E2DC")
chk_bg.set_xticks([])
chk_bg.set_yticks([])
chk_bg.set_navigate(False)
for _sp in chk_bg.spines.values():
    _sp.set_color("#9CA3AF")
    _sp.set_linewidth(1.2)

ax_checks = fig.add_axes([
    _RIGHT_X + _CHK_PAD, _MY + 0.015,
    _RIGHT_W - 2 * _CHK_PAD, _CTRL_H - 0.03,
])
ax_checks.set_zorder(2)
ax_checks.set_facecolor("#E4E2DC")
checks = CheckButtons(
    ax_checks,
    ["Show labels", "Show grid", "Fade old dots"],
    actives=[True, False, True],
)
for _lbl in checks.labels:
    _lbl.set_color(_C_INK)
    _lbl.set_fontsize(9)
    _lbl.set_fontweight("bold")

# ── simulation state ──────────────────────────────────────────────────────────
_rng = np.random.default_rng(int(sl_seed.val))
_xs: list[float] = []
_ys: list[float] = []
_inside: list[bool] = []
_hits = 0
_total = 0
_anim_active = False
_suppress_tb = False
_label_artists: list = []


def _textbox_typing() -> bool:
    return any(tb.capturekeystrokes for tb in _TEXTBOXES)


def _sync_textboxes() -> None:
    pairs = (
        (tb_rate, f"{_rate_from_slider(sl_rate.val):.0f}"),
        (tb_batch, str(int(round(sl_batch.val)))),
        (tb_target, str(_target_from_slider(sl_target.val))),
        (tb_seed, str(int(sl_seed.val))),
    )
    for tb, s in pairs:
        if tb.capturekeystrokes or tb.text == s:
            continue
        tb.text_disp.set_text(s)
        tb.cursor_index = len(s)


def _clear_labels() -> None:
    for obj in _label_artists:
        obj.remove()
    _label_artists.clear()


def _draw_labels(show_labels: bool) -> None:
    _clear_labels()
    if not show_labels:
        return
    _label_artists.append(ax.text(
        0.0, 1.28, "Square area = 4", ha="center", va="bottom",
        fontsize=13, fontweight="bold", color=_C_INK, zorder=8,
    ))
    _label_artists.append(ax.text(
        0.0, -1.22, "Circle area = π", ha="center", va="top",
        fontsize=13, fontweight="bold", color="#2563EB", zorder=8,
    ))
    _label_artists.append(ax.annotate(
        "", xy=(_SQUARE_HALF, -_SQUARE_HALF), xytext=(-_SQUARE_HALF, -_SQUARE_HALF),
        arrowprops=dict(arrowstyle="<->", color=_C_INK, lw=2.0),
        zorder=8,
    ))
    _label_artists.append(ax.text(
        0.0, -1.38, "side = 2", ha="center", va="top",
        fontsize=11, fontweight="bold", color=_C_INK, zorder=8,
    ))


def _display_arrays(show_fade: bool) -> tuple[np.ndarray, np.ndarray,
                                             np.ndarray, np.ndarray]:
    if not _xs:
        return (np.empty(0), np.empty(0), np.empty(0), np.empty(0))
    xs = np.asarray(_xs)
    ys = np.asarray(_ys)
    inside = np.asarray(_inside, dtype=bool)
    if show_fade and len(xs) > 4000:
        # keep full count for π, but fade display to the most recent dots
        xs = xs[-4000:]
        ys = ys[-4000:]
        inside = inside[-4000:]
    out_x, out_y = xs[~inside], ys[~inside]
    in_x, in_y = xs[inside], ys[inside]
    return out_x, out_y, in_x, in_y


def _update_scatter(show_fade: bool) -> None:
    out_x, out_y, in_x, in_y = _display_arrays(show_fade)
    _scatter_out.set_offsets(np.column_stack([out_x, out_y]) if len(out_x) else np.empty((0, 2)))
    _scatter_in.set_offsets(np.column_stack([in_x, in_y]) if len(in_x) else np.empty((0, 2)))


def _update_readout() -> None:
    if _total <= 0:
        _rd_n.set_text("0")
        _rd_h.set_text("0")
        _rd_p.set_text("—")
        _rd_pi.set_text("—")
        _rd_err.set_text("—")
        _rd_dev.set_text("—")
        _rd_dev.set_color("#C4B5FD")
        _rd_sigma.set_text("—")
        _rd_step1.set_color(_C_LABEL)
        _rd_step2.set_color(_C_LABEL)
        _rd_area_cmp.set_text("Press ▶ Throw to start")
        return

    p = _hits / _total
    pi_hat = _estimate_pi(_hits, _total)
    err = abs(pi_hat - math.pi)
    pct_dev = 100.0 * err / math.pi
    sigma = _sigma_pct(_total)

    _rd_n.set_text(f"{_total:,}")
    _rd_h.set_text(f"{_hits:,}")
    _rd_p.set_text(f"{p:.4f}")
    _rd_pi.set_text(f"{pi_hat:.5f}")
    _rd_err.set_text(f"{err:.5f}")
    _rd_dev.set_text(f"{pct_dev:.2f}%")
    _rd_sigma.set_text(f"±{sigma:.2f}%")

    if pct_dev <= sigma:
        _rd_dev.set_color(_C_TRUE)
        wobble = "within normal wobble"
    elif pct_dev <= 2.0 * sigma:
        _rd_dev.set_color("#FCD34D")
        wobble = "typical random fluctuation"
    else:
        _rd_dev.set_color(_C_OUT)
        wobble = "lucky/unlucky streak (~5% of steps)"

    _rd_step1.set_color(_C_PROOF if _total >= 20 else _C_WHITE)
    _rd_step2.set_color(_C_PROOF if _hits >= 5 else _C_LABEL)
    _rd_area_cmp.set_text(
        f"{wobble}  ·  shrinks ~1/√N  ·  estimate can move either way"
    )


def _refresh(_=None) -> None:
    show_labels, show_grid, show_fade = checks.get_status()
    if not _textbox_typing():
        _sync_textboxes()
    ax.grid(show_grid, color="#E5E7EB", linewidth=0.8, zorder=1) if show_grid else ax.grid(False)
    _draw_labels(show_labels)
    _update_scatter(show_fade)
    _update_readout()
    fig.canvas.draw_idle()


def _throw_batch(n: int) -> None:
    global _hits, _total
    if n <= 0:
        return
    target = _target_from_slider(sl_target.val)
    n = min(n, target - _total)
    if n <= 0:
        return

    xs = _rng.uniform(-_SQUARE_HALF, _SQUARE_HALF, n)
    ys = _rng.uniform(-_SQUARE_HALF, _SQUARE_HALF, n)
    inside = _inside_circle(xs, ys)

    _xs.extend(xs.tolist())
    _ys.extend(ys.tolist())
    _inside.extend(inside.tolist())
    _hits += int(inside.sum())
    _total += n


def _on_tb_rate(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_rate.set_val(_slider_from_rate(float(text)))
    except ValueError:
        _sync_textboxes()


def _on_tb_batch(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_batch.set_val(max(_BATCH_MIN, min(_BATCH_MAX, int(round(float(text))))))
    except ValueError:
        _sync_textboxes()


def _on_tb_target(text: str) -> None:
    if _suppress_tb:
        return
    try:
        n = int(round(float(text.replace(",", ""))))
        n = max(_N_DOTS_MIN, min(_N_DOTS_MAX, n))
        sl_target.set_val(_slider_from_target(n))
    except ValueError:
        _sync_textboxes()


def _on_tb_seed(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_seed.set_val(max(0, min(9999, int(round(float(text))))))
    except ValueError:
        _sync_textboxes()


def _reseed() -> None:
    global _rng
    _rng = np.random.default_rng(int(sl_seed.val))


def _reset(_=None) -> None:
    global _anim_active, _hits, _total
    _anim_active = False
    btn_play.label.set_text("▶  Throw")
    btn_play.ax.set_facecolor("#BFDBFE")
    _xs.clear()
    _ys.clear()
    _inside.clear()
    _hits = 0
    _total = 0
    _reseed()
    _refresh()


def _toggle_anim(_=None) -> None:
    global _anim_active
    if _anim_active:
        _anim_active = False
        btn_play.label.set_text("▶  Throw")
        btn_play.ax.set_facecolor("#BFDBFE")
        return
    if _total >= _target_from_slider(sl_target.val):
        _reset()
    _anim_active = True
    btn_play.label.set_text("■  Stop")
    btn_play.ax.set_facecolor("#FECACA")
    _run_anim()


def _run_anim() -> None:
    if not _anim_active:
        return
    target = _target_from_slider(sl_target.val)
    if _total >= target:
        globals()["_anim_active"] = False
        btn_play.label.set_text("▶  Throw")
        btn_play.ax.set_facecolor("#BFDBFE")
        _refresh()
        return
    _throw_batch(_batch_for_tick())
    _refresh()
    fig.canvas.flush_events()
    if _anim_active:
        timer.start()


timer = fig.canvas.new_timer(interval=_TICK_MS)
timer.single_shot = True
timer.add_callback(_run_anim)


def _on_seed_change(_=None) -> None:
    if _total == 0:
        _reseed()
    _refresh()


# ── wire up ───────────────────────────────────────────────────────────────────
sl_rate.on_changed(_refresh)
sl_batch.on_changed(_refresh)
sl_target.on_changed(_refresh)
sl_seed.on_changed(_on_seed_change)
tb_rate.on_submit(_on_tb_rate)
tb_batch.on_submit(_on_tb_batch)
tb_target.on_submit(_on_tb_target)
tb_seed.on_submit(_on_tb_seed)
checks.on_clicked(_refresh)
btn_play.on_clicked(_toggle_anim)
btn_reset.on_clicked(_reset)

_refresh()
if __name__ == "__main__":
    plt.show()
