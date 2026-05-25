"""Interactive animation: derive the area of a circle by peeling concentric rings.

Each thin ring is "unrolled" into a straight line and stacked. The stack forms a
triangle with base 2πr and height r, so  A = ½ × 2πr × r = πr².

Run with (pyenv + .venv):
    source .venv/bin/activate
    python circle_area_peel_demo.py

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
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.widgets import Button, CheckButtons, Slider

# ── constants ─────────────────────────────────────────────────────────────────
_N_MAX              = 150   # max ring count when layer δ/r → 0
_R_INIT             = 2.0
_R_MIN              = 1.2
_R_MAX              = 2.8
_PEEL_INIT          = 0.0
_LAYER_FRAC_INIT    = 1.0 / 72   # default layer thickness δ/r (≈72 rings)
_PEEL_STAGES        = 5
_RING_SEC_DEFAULT   = 0.25
_RING_SEC_MIN       = 0.01
_RING_SEC_MAX       = 3.0
_ANIM_TICK_MS       = 20

# high-contrast UI palette (dark readout panel + light control strip)
_C_R     = "#7DD3FC"   # sky blue
_C_C     = "#FCD34D"   # gold
_C_B     = "#FB923C"   # orange
_C_H     = "#F0ABFC"   # magenta
_C_A     = "#6EE7B7"   # mint
_C_N     = "#FDA4AF"   # coral
_C_D     = "#C4B5FD"   # violet
_C_WHITE = "#F9FAFB"   # primary text on dark bg
_C_LABEL = "#E5E7EB"   # descriptions on dark bg
_C_PROOF = "#4ADE80"   # formula highlight
_C_INK   = "#111827"   # text on light control strip
_C_EDGE  = "#1F2937"   # diagram edges

# layout (figure-normalised coords)
_CANVAS  = [0.04, 0.34, 0.52, 0.62]
_RD_BOX  = [0.58, 0.34, 0.38, 0.62]
_CTRL_BG = [0.03, 0.03, 0.54, 0.27]   # left strip only — under canvas
_SL_X, _SL_W, _SL_H = 0.06, 0.44, 0.022
_SL_YS = (0.21, 0.165, 0.12, 0.075)
_SL_LABELS = ("Sec / ring", "Layer δ/r", "Peel rings", "Radius r")
_SYM_X, _VAL_X, _DESC_X = 0.07, 0.24, 0.96
# ring fill colours — distinct hues, strong edges (readable when colour vision is limited)
_RING_COLORS = [
    "#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE",
    "#AA3377", "#BBBBBB", "#88CCEE", "#44AA99", "#DDCC77",
    "#882255", "#6699CC",
]


def _ring_color(i: int) -> str:
    return _RING_COLORS[i % len(_RING_COLORS)]


def _ring_layout(r: float, layer_frac: float) -> tuple[int, float]:
    """Return (ring count, radial thickness δ) for layer thickness δ/r = layer_frac."""
    frac = max(min(layer_frac, 1.0), 1.0 / _N_MAX)
    n = max(1, min(_N_MAX, round(1.0 / frac)))
    return n, r / n


def _annulus_poly(cx: float, cy: float, r_in: float, r_out: float,
                  n: int = 96) -> np.ndarray:
    """Closed polygon approximating a filled annulus."""
    if r_out <= 1e-9:
        return np.empty((0, 2))
    if r_in <= 1e-9:
        return _disk_poly(cx, cy, r_out, n)
    # endpoint=True so the outer loop covers a full 360° (no missing wedge)
    theta = np.linspace(0, 2 * math.pi, n, endpoint=True)
    xo = cx + r_out * np.cos(theta)
    yo = cy + r_out * np.sin(theta)
    xi = cx + r_in * np.cos(theta[::-1])
    yi = cy + r_in * np.sin(theta[::-1])
    return np.column_stack([np.r_[xo, xi], np.r_[yo, yi]])


def _disk_poly(cx: float, cy: float, r: float, n: int = 96) -> np.ndarray:
    """Closed polygon approximating a filled disk."""
    theta = np.linspace(0, 2 * math.pi, n, endpoint=True)
    return np.column_stack([cx + r * np.cos(theta), cy + r * np.sin(theta)])


def _bar_poly(cx: float, cy: float, width: float, height: float) -> np.ndarray:
    hw, hh = width / 2, height / 2
    return np.array([
        [cx - hw, cy - hh], [cx + hw, cy - hh],
        [cx + hw, cy + hh], [cx - hw, cy + hh],
    ])


def _ease(t: float) -> float:
    """Smooth ease-in-out for peel motion."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _peel_stage_params(t: float) -> tuple[float, float, float]:
    """Return (gap_half_rad, morph_to_line, drop_to_stack) for peel progress t ∈ [0, 1].

    Five visual stages per ring:
      1  tiny gap at top of ring on the circle
      2  gap widens — ring opening like a hinge at the top
      3  arc begins to flatten and lift away from the circle
      4  mostly straight, descending toward the stack
      5  nearly flat line settling onto the triangle
    """
    t = max(0.0, min(1.0, t))
    stage = min(int(t * _PEEL_STAGES), _PEEL_STAGES - 1)
    u = _ease(t * _PEEL_STAGES - stage)

    gap_table = [(0.06, 0.14), (0.14, 0.38), (0.38, 0.85), (0.85, 1.35), (1.35, math.pi - 0.06)]
    morph_table = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.30), (0.30, 0.82), (0.82, 1.0)]
    drop_table = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.18), (0.18, 0.88), (0.88, 1.0)]

    g0, g1 = gap_table[stage]
    m0, m1 = morph_table[stage]
    d0, d1 = drop_table[stage]
    return g0 + (g1 - g0) * u, m0 + (m1 - m0) * u, d0 + (d1 - d0) * u


def _gapped_annulus(cx: float, cy: float, r_in: float, r_out: float,
                    gap_half: float, n: int = 56) -> np.ndarray:
    """Annular sector with a radial gap centred at the top (θ = π/2)."""
    if r_out <= 1e-9:
        return np.empty((0, 2))
    if r_in <= 1e-9:
        return _gapped_disk(cx, cy, r_out, gap_half, n)

    t0 = math.pi / 2 + gap_half
    t1 = math.pi / 2 - gap_half + 2 * math.pi
    theta = np.linspace(t0, t1, n)
    xo = cx + r_out * np.cos(theta)
    yo = cy + r_out * np.sin(theta)
    xi = cx + r_in * np.cos(theta[::-1])
    yi = cy + r_in * np.sin(theta[::-1])
    return np.column_stack([np.r_[xo, xi], np.r_[yo, yi]])


def _gapped_disk(cx: float, cy: float, r: float, gap_half: float, n: int = 56) -> np.ndarray:
    """Disk sector with a radial gap at the top."""
    t0 = math.pi / 2 + gap_half
    t1 = math.pi / 2 - gap_half + 2 * math.pi
    theta = np.linspace(t0, t1, n)
    x = np.r_[cx, cx + r * np.cos(theta)]
    y = np.r_[cy, cy + r * np.sin(theta)]
    return np.column_stack([x, y])


def _peeling_ring_poly(
    cx: float, cy: float, r_in: float, r_out: float,
    y_stack: float, t_local: float,
) -> np.ndarray:
    """Polygon for one ring at peel progress t_local ∈ [0, 1]."""
    r_mid = 0.5 * (r_in + r_out)
    thick = max(r_out - r_in, 1e-9)
    line_len = 2 * math.pi * r_mid
    gap, morph, drop = _peel_stage_params(t_local)

    if morph < 0.04:
        return _gapped_annulus(cx, cy, max(r_in, 0.0), r_out, gap)

    # Arc endpoints for the opening at the top
    a0 = math.pi / 2 + min(gap, math.pi - 0.08)
    a1 = math.pi / 2 - min(gap, math.pi - 0.08) + 2 * math.pi
    n = max(20, int(48 * (1.0 - 0.35 * morph)))
    thetas = np.linspace(a0, a1, n)
    arc_len = max(r_mid * (a1 - a0), 1e-9)

    # Hover slightly above the stack while descending, then settle
    hover = thick * 1.6 * (1.0 - drop) * (0.35 + 0.65 * morph)
    y_line = y_stack + hover

    # Circular centreline → flat centreline
    xs_c = cx + r_mid * np.cos(thetas)
    ys_c = cy + r_mid * np.sin(thetas)
    s = r_mid * (thetas - a0)
    xs_f = cx - line_len / 2 + line_len * s / arc_len
    ys_f = np.full(n, y_line)

    xs = xs_c * (1.0 - morph) + xs_f * morph
    ys = ys_c * (1.0 - morph) + ys_f * morph

    # Ribbon thickness: radial on circle → vertical when flat
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    norm = np.hypot(dx, dy) + 1e-9
    nx = -dy / norm
    ny = dx / norm
    half = thick * 0.48

    upper = np.column_stack([xs + nx * half, ys + ny * half])
    lower = np.column_stack([xs - nx * half, ys - ny * half])[::-1]
    return np.vstack([upper, lower])


# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 7.8), facecolor="#F0EEEA")
fig.canvas.manager.set_window_title("Area of a Circle: Peel the Rings")

# control-strip background (groups sliders + buttons)
ctrl_bg = fig.add_axes(_CTRL_BG, zorder=-1)
ctrl_bg.set_facecolor("#E4E2DC")
ctrl_bg.set_xticks([])
ctrl_bg.set_yticks([])
for _sp in ctrl_bg.spines.values():
    _sp.set_color("#9CA3AF")
    _sp.set_linewidth(1.2)

ax = fig.add_axes(_CANVAS)
ax.set_facecolor("#FAFAF8")
ax.set_aspect("equal")
ax.axis("off")

# ── live readout panel ────────────────────────────────────────────────────────
rd = fig.add_axes(_RD_BOX)
rd.set_axis_off()
# solid dark fill (rd.patch alone is unreliable when axis is off)
rd.add_patch(Rectangle(
    (0.0, 0.0), 1.0, 1.0, transform=rd.transAxes,
    facecolor="#111827", edgecolor="none", zorder=0,
))

rd.add_patch(FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
    fill=False, edgecolor="#93C5FD", linewidth=2.5,
    transform=rd.transAxes, clip_on=False, zorder=10,
))
# title bar
rd.add_patch(Rectangle(
    (0.02, 0.925), 0.96, 0.065, transform=rd.transAxes,
    facecolor="#1D4ED8", edgecolor="none", zorder=9,
))
rd.text(0.5, 0.958, "AREA DERIVATION", ha="center", va="center",
        color="#FFFFFF", fontsize=13, fontweight="bold",
        transform=rd.transAxes, family="monospace")

for y, col, lw in [(0.885, "#6B7280", 1.5), (0.555, "#4B5563", 1.0),
                   (0.240, "#4B5563", 1.0)]:
    rd.add_artist(Line2D([0.04, 0.96], [y, y], color=col, lw=lw,
                         transform=rd.transAxes, zorder=5))

for y, sym, col, desc in [
    (0.820, "r", _C_R, "radius of circle"),
    (0.710, "C", _C_C, "circumference  2πr"),
    (0.600, "b", _C_B, "triangle base  =  C"),
    (0.490, "h", _C_H, "triangle height  =  r"),
    (0.380, "A", _C_A, "area  =  ½ × b × h"),
]:
    rd.text(_SYM_X, y, sym, ha="left", va="center", color=col,
            fontsize=22, fontweight="bold", transform=rd.transAxes,
            family="monospace", zorder=11)
    rd.text(_DESC_X, y, desc, ha="right", va="center", color=_C_LABEL,
            fontsize=10, transform=rd.transAxes, zorder=11)

_rd_r  = rd.text(_VAL_X, 0.820, "—", ha="left", va="center",
                 color=_C_R, fontsize=22, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_c  = rd.text(_VAL_X, 0.710, "—", ha="left", va="center",
                 color=_C_C, fontsize=22, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_b  = rd.text(_VAL_X, 0.600, "—", ha="left", va="center",
                 color=_C_B, fontsize=22, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_h  = rd.text(_VAL_X, 0.490, "—", ha="left", va="center",
                 color=_C_H, fontsize=22, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_a  = rd.text(_VAL_X, 0.380, "—", ha="left", va="center",
                 color=_C_A, fontsize=22, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_n  = rd.text(_VAL_X, 0.318, "—", ha="left", va="center",
                 color=_C_N, fontsize=20, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)
_rd_d  = rd.text(_VAL_X, 0.268, "—", ha="left", va="center",
                 color=_C_D, fontsize=20, fontweight="bold",
                 transform=rd.transAxes, family="monospace", zorder=11)

rd.text(_SYM_X, 0.318, "N", ha="left", va="center", color=_C_N,
        fontsize=20, fontweight="bold", transform=rd.transAxes,
        family="monospace", zorder=11)
rd.text(_DESC_X, 0.318, "ring count", ha="right", va="center", color=_C_LABEL,
        fontsize=10, transform=rd.transAxes, zorder=11)
rd.text(_SYM_X, 0.268, "δ", ha="left", va="center", color=_C_D,
        fontsize=20, fontweight="bold", transform=rd.transAxes,
        family="monospace", zorder=11)
rd.text(_DESC_X, 0.268, "layer thick  (× r)", ha="right", va="center",
        color=_C_LABEL, fontsize=10, transform=rd.transAxes, zorder=11)

rd.text(0.5, 0.218, "the proof", ha="center", va="center",
        color=_C_WHITE, fontsize=10, fontweight="bold",
        transform=rd.transAxes, zorder=11)

_rd_step1 = rd.text(0.5, 0.178, "peel each ring → straight line",
                    ha="center", va="center", color=_C_WHITE,
                    fontsize=10, transform=rd.transAxes, zorder=11)
_rd_step2 = rd.text(0.5, 0.138, "stack lines → triangle",
                    ha="center", va="center", color=_C_WHITE,
                    fontsize=10, transform=rd.transAxes, zorder=11)
_rd_formula = rd.text(
    0.5, 0.095,
    "A = ½ × 2πr × r  =  πr²",
    ha="center", va="center", color=_C_PROOF,
    fontsize=15, fontweight="bold", transform=rd.transAxes,
    family="monospace", zorder=11,
)
_rd_area_cmp = rd.text(0.5, 0.048, "", ha="center", va="center",
                       color=_C_LABEL, fontsize=10, transform=rd.transAxes,
                       family="monospace", zorder=11)

# ── sliders (labels in figure coords — avoids matplotlib clipping them) ───────
for _lbl, _y in zip(_SL_LABELS, _SL_YS):
    fig.text(_SL_X, _y + _SL_H + 0.006, _lbl,
             transform=fig.transFigure, ha="left", va="bottom",
             fontsize=10, fontweight="bold", color=_C_INK)

ax_speed = fig.add_axes([_SL_X, _SL_YS[0], _SL_W, _SL_H])
ax_thick = fig.add_axes([_SL_X, _SL_YS[1], _SL_W, _SL_H])
ax_peel  = fig.add_axes([_SL_X, _SL_YS[2], _SL_W, _SL_H])
ax_rad   = fig.add_axes([_SL_X, _SL_YS[3], _SL_W, _SL_H])

sl_speed = Slider(ax_speed, "", _RING_SEC_MIN, _RING_SEC_MAX,
                  valinit=_RING_SEC_DEFAULT, color="#7C3AED", track_color="#6B7280")
sl_thick = Slider(ax_thick, "", 0.0, 1.0, valinit=_LAYER_FRAC_INIT,
                  color="#DB2777", track_color="#6B7280")
sl_peel = Slider(ax_peel, "", 0.0, 1.0, valinit=_PEEL_INIT,
                 color="#2563EB", track_color="#6B7280")
sl_r    = Slider(ax_rad,  "", _R_MIN, _R_MAX, valinit=_R_INIT,
                 color="#0284C7", track_color="#6B7280")

for _sax, _sl in zip((ax_speed, ax_thick, ax_peel, ax_rad),
                     (sl_speed, sl_thick, sl_peel, sl_r)):
    _sax.set_facecolor("#E4E2DC")
    _sax.set_xticks([])
    _sl.valtext.set_color(_C_INK)
    _sl.valtext.set_fontsize(9)
    _sl.valtext.set_fontweight("bold")


def _anim_step() -> float:
    """Peel-slider advance per animation tick for the current sec/ring setting."""
    n_rings, _ = _ring_layout(sl_r.val, sl_thick.val)
    ticks_per_ring = sl_speed.val * 1000.0 / _ANIM_TICK_MS
    return 1.0 / (n_rings * ticks_per_ring)

ax_btn_play  = fig.add_axes([_SL_X, 0.035, 0.12, 0.042])
ax_btn_reset = fig.add_axes([_SL_X + 0.135, 0.035, 0.12, 0.042])
btn_play  = Button(ax_btn_play,  "▶  Peel",   color="#BFDBFE", hovercolor="#93C5FD")
btn_reset = Button(ax_btn_reset, "Reset",      color="#FFFFFF", hovercolor="#E5E7EB")
for _bax in (ax_btn_play, ax_btn_reset):
    _bax.set_facecolor("#FFFFFF")
    for _sp in _bax.spines.values():
        _sp.set_color("#64748B")
        _sp.set_linewidth(1.5)

# checkboxes — under readout panel, separate box
_CTRL_CHK = [0.58, 0.03, 0.38, 0.27]
chk_bg = fig.add_axes(_CTRL_CHK, zorder=-1)
chk_bg.set_facecolor("#E4E2DC")
chk_bg.set_xticks([])
chk_bg.set_yticks([])
for _sp in chk_bg.spines.values():
    _sp.set_color("#9CA3AF")
    _sp.set_linewidth(1.2)

ax_checks = fig.add_axes([0.60, 0.08, 0.34, 0.09])
ax_checks.set_facecolor("#E4E2DC")
checks = CheckButtons(
    ax_checks,
    ["Show labels", "Show peel hint"],
    actives=[True, True],
)
for _lbl in checks.labels:
    _lbl.set_color(_C_INK)
    _lbl.set_fontsize(10)
    _lbl.set_fontweight("bold")

# ── mutable artists ───────────────────────────────────────────────────────────
_artists: list = []
_anim_active = False
_suppress    = False


def _clear() -> None:
    for obj in _artists:
        obj.remove()
    _artists.clear()


def _draw(r: float, peel: float, layer_frac: float,
          show_labels: bool, show_hint: bool) -> None:
    n_rings, dr = _ring_layout(r, layer_frac)
    circ = 2 * math.pi * r
    area = math.pi * r * r
    bar_h = dr * 0.96
    edge_lw = max(0.15, min(1.2, dr / r * 8.0))

    # layout: circle above, triangle below
    tri_top    = 0.0
    tri_bottom = -r
    cx         = 0.0
    cy         = r + 1.35          # circle centre sits above the stack

    pad_x = circ / 2 + 1.8
    circle_top = cy + r
    ax.set_xlim(-pad_x, pad_x)
    ax.set_ylim(tri_bottom - 1.4, circle_top + 0.85)

    n_done = peel * n_rings

    # ── peeled / peeling rings ────────────────────────────────────────────────
    for i in range(n_rings):
        r_in  = max(r - (i + 1) * dr, 0.0)
        r_out = r - i * dr
        r_mid = (r_in + r_out) / 2
        line_len = 2 * math.pi * r_mid
        y_bar = tri_bottom + (i + 0.5) * dr

        if i < n_done - 1:
            # fully peeled — flat bar in the stack
            poly = _bar_poly(cx, y_bar, line_len, bar_h)
            patch = Polygon(
                poly, closed=True, facecolor=_ring_color(i),
                edgecolor=_C_EDGE, linewidth=edge_lw, zorder=2,
            )
            ax.add_patch(patch)
            _artists.append(patch)

        elif i < n_done:
            # mid-peel — 5-stage morph (gapped arc → opening → flatten → drop → line)
            t_local = n_done - i
            poly = _peeling_ring_poly(cx, cy, r_in, r_out, y_bar, t_local)
            if len(poly) >= 3:
                patch = Polygon(
                    poly, closed=True, facecolor=_ring_color(i),
                    edgecolor=_C_EDGE, linewidth=edge_lw, zorder=5,
                )
                ax.add_patch(patch)
                _artists.append(patch)

            if show_hint:
                gap, morph, drop = _peel_stage_params(t_local)
                # yellow tick marks at the gap when still on/near the circle
                if morph < 0.55:
                    for sign in (-1, 1):
                        ang = math.pi / 2 + sign * gap
                        x0 = cx + r_in * math.cos(ang)
                        y0 = cy + r_in * math.sin(ang)
                        x1 = cx + r_out * math.cos(ang)
                        y1 = cy + r_out * math.sin(ang)
                        cut, = ax.plot([x0, x1], [y0, y1], color="#F59E0B",
                                       lw=2.5, solid_capstyle="round", zorder=7)
                        _artists.append(cut)
                # faint guide from peel toward stack
                elif drop < 0.95:
                    gx = cx
                    gy0 = cy + r_out * 0.15
                    gy1 = y_bar + dr * (1.6 - drop)
                    guide, = ax.plot([gx, gx], [gy0, gy1], color="#F59E0B",
                                     lw=2.0, ls="--", alpha=0.75, zorder=6)
                    _artists.append(guide)

    # ── remaining rings on the circle ─────────────────────────────────────────
    first_remaining = min(n_rings, max(0, int(math.ceil(n_done - 1e-9))))
    for i in range(first_remaining, n_rings):
        r_in  = max(r - (i + 1) * dr, 0.0)
        r_out = r - i * dr
        if r_out <= 1e-9:
            continue
        poly = _annulus_poly(cx, cy, r_in, r_out)
        show_ring_edge = dr / r > 0.04
        patch = Polygon(
            poly, closed=True, facecolor=_ring_color(i),
            edgecolor=_C_EDGE if show_ring_edge else "none",
            linewidth=edge_lw if show_ring_edge else 0.0, zorder=4,
        )
        ax.add_patch(patch)
        _artists.append(patch)

    # outer outline — hide while a ring is actively opening (avoids flat-top artefact)
    peeling_now = any(i < n_done < i + 1 for i in range(n_rings))
    if n_done < n_rings - 0.5 and not peeling_now:
        outline = Circle(
            (cx, cy), r, fill=False, edgecolor=_C_EDGE,
            linewidth=2.0, zorder=6,
        )
        ax.add_patch(outline)
        _artists.append(outline)

    # global peel marker on the circle top (only when no ring is mid-peel)
    if 0.0 < n_done < n_rings and show_hint and not peeling_now:
        cut, = ax.plot([cx - r * 0.12, cx + r * 0.12],
                       [cy + r, cy + r],
                       color="#F59E0B", lw=2.5, zorder=7)
        _artists.append(cut)

    # ── dimension labels ──────────────────────────────────────────────────────
    if show_labels:
        # radius on circle
        _artists.append(ax.annotate(
            "", xy=(cx, cy + r), xytext=(cx, cy),
            arrowprops=dict(arrowstyle="<->", color=_C_R, lw=2.5),
            zorder=8,
        ))
        _artists.append(ax.text(cx - r * 0.22, cy + r / 2, "r",
                                ha="right", va="center", color=_C_R,
                                fontsize=14, fontweight="bold", zorder=8))

        # triangle height
        if peel > 0.15:
            _artists.append(ax.annotate(
                "", xy=(cx - circ / 2 - 0.35, tri_top),
                xytext=(cx - circ / 2 - 0.35, tri_bottom),
                arrowprops=dict(arrowstyle="<->", color=_C_H, lw=2.5),
                zorder=8,
            ))
            _artists.append(ax.text(cx - circ / 2 - 0.65, (tri_top + tri_bottom) / 2,
                                    "r", ha="right", va="center", color=_C_H,
                                    fontsize=14, fontweight="bold", zorder=8))

        # base 2πr when mostly peeled
        if peel > 0.75:
            _artists.append(ax.annotate(
                "", xy=(cx - circ / 2, tri_bottom - 0.35),
                xytext=(cx + circ / 2, tri_bottom - 0.35),
                arrowprops=dict(arrowstyle="<->", color=_C_B, lw=2.5),
                zorder=8,
            ))
            _artists.append(ax.text(cx, tri_bottom - 0.72, "2πr",
                                    ha="center", va="top", color=_C_B,
                                    fontsize=14, fontweight="bold", zorder=8))

        # title
        if peel < 0.08:
            _artists.append(ax.text(
                0.5, 0.97, "Circle of radius  r",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=18, fontweight="bold", color=_C_INK, zorder=8,
            ))
        elif peel > 0.92:
            _artists.append(ax.text(
                0.5, 0.97, "Same area → triangle!",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=18, fontweight="bold", color="#15803D", zorder=8,
            ))
        else:
            _artists.append(ax.text(
                0.5, 0.97, "Peeling rings…",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=18, fontweight="bold", color="#1D4ED8", zorder=8,
            ))

    fig.canvas.draw_idle()


def _update_readout(r: float, peel: float, layer_frac: float) -> None:
    circ = 2 * math.pi * r
    area = math.pi * r * r
    n_rings, dr = _ring_layout(r, layer_frac)
    frac = dr / r

    _rd_r.set_text(f"{r:.2f}")
    _rd_c.set_text(f"{circ:.2f}")
    _rd_b.set_text(f"{circ:.2f}")
    _rd_h.set_text(f"{r:.2f}")
    _rd_a.set_text(f"{area:.2f}")
    _rd_n.set_text(f"{n_rings}")
    _rd_d.set_text(f"{frac:.3f}")

    if peel < 0.05:
        _rd_step1.set_color(_C_LABEL)
        _rd_step2.set_color(_C_LABEL)
    elif peel < 0.95:
        _rd_step1.set_color(_C_C)
        _rd_step2.set_color(_C_LABEL)
    else:
        _rd_step1.set_color(_C_PROOF)
        _rd_step2.set_color(_C_PROOF)

    _rd_area_cmp.set_text(
        f"circle area  πr² = {area:.2f}   |   "
        f"triangle  ½·2πr·r = {0.5 * circ * r:.2f}"
    )


def _refresh(_=None) -> None:
    r          = sl_r.val
    peel       = sl_peel.val
    layer_frac = sl_thick.val
    show_labels, show_hint = checks.get_status()

    _clear()
    _draw(r, peel, layer_frac, show_labels, show_hint)
    _update_readout(r, peel, layer_frac)


# ── animation ─────────────────────────────────────────────────────────────────
def _toggle_anim(_=None) -> None:
    global _anim_active
    _anim_active = not _anim_active
    btn_play.label.set_text("■  Stop" if _anim_active else "▶  Peel")
    btn_play.ax.set_facecolor("#FECACA" if _anim_active else "#BFDBFE")
    if _anim_active:
        _run_anim()


def _run_anim() -> None:
    if not _anim_active:
        return
    nxt = sl_peel.val + _anim_step()
    if nxt >= 1.0:
        nxt = 1.0
        globals()["_anim_active"] = False
        btn_play.label.set_text("▶  Peel")
        btn_play.ax.set_facecolor("#BFDBFE")
    sl_peel.set_val(nxt)
    fig.canvas.flush_events()
    if _anim_active:
        timer.start()


timer = fig.canvas.new_timer(interval=_ANIM_TICK_MS)
timer.single_shot = True
timer.add_callback(_run_anim)


def _reset(_=None) -> None:
    global _anim_active
    _anim_active = False
    btn_play.label.set_text("▶  Peel")
    btn_play.ax.set_facecolor("#BFDBFE")
    sl_peel.set_val(0.0)


# ── wire up ───────────────────────────────────────────────────────────────────
sl_peel.on_changed(_refresh)
sl_r.on_changed(_refresh)
sl_thick.on_changed(_refresh)
checks.on_clicked(_refresh)
btn_play.on_clicked(_toggle_anim)
btn_reset.on_clicked(_reset)

_refresh()
plt.show()
