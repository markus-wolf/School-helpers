"""Geometry area puzzle: ABCD and DEPF are squares.

Find x such that the white area equals the green area.

Run with (pyenv + .venv):
    source .venv/bin/activate
    python geometry_areas_demo.py

Setup once:
    pyenv install -s
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle
from matplotlib.widgets import Button, CheckButtons, Slider, TextBox

SIDE = 8.0   # side length of the large square ABCD


# ── geometry helpers ──────────────────────────────────────────────────────────

def _vertices(x: float) -> dict[str, tuple[float, float]]:
    s = SIDE
    return dict(
        A=(0,   0  ),
        B=(s,   0  ),
        C=(s,   s  ),
        D=(0,   s  ),
        E=(0,   s-x),
        F=(x,   s  ),
        P=(x,   s-x),
    )


def _areas(x: float) -> tuple[float, float, float]:
    """Return (green_square, green_triangle, white)."""
    sq  = x * x
    tri = 0.5 * SIDE * (SIDE - x)
    return sq, tri, SIDE * SIDE - sq - tri


# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 7.8), facecolor="#fdfaf4")
fig.canvas.manager.set_window_title("Area Puzzle: ABCD and DEPF squares")

# Main drawing canvas
ax = fig.add_axes([0.03, 0.25, 0.52, 0.71])
ax.set_facecolor("#f8fafc")
ax.set_xlim(-1.6, 10.8)
ax.set_ylim(-1.6, 10.8)
ax.set_aspect("equal")
ax.axis("off")

# ── live readout panel (dark) ─────────────────────────────────────────────────
rd = fig.add_axes([0.58, 0.25, 0.39, 0.71])
rd.set_axis_off()
rd.patch.set_facecolor("#0f172a")
rd.patch.set_visible(True)

rd.add_patch(FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
    fill=False, edgecolor="#3b82f6", linewidth=2.5,
    transform=rd.transAxes, clip_on=False, zorder=10,
))
rd.text(0.5, 0.965, "◈  AREA BALANCE", ha="center", va="top",
        color="#ffffff", fontsize=12, fontweight="bold",
        transform=rd.transAxes, family="monospace")

# Separators
for y, col, lw in [(0.895, "#3b82f6", 1.5), (0.535, "#334155", 1.0),
                   (0.290, "#334155", 1.0)]:
    rd.add_artist(Line2D([0.04, 0.96], [y, y], color=col, lw=lw,
                         transform=rd.transAxes, zorder=5))

# ── main rows: letter | value | description  (matches circle-demo style) ──────
#   Each row: big bold letter on left (fontsize 22, monospace)
#             live value next to it  (same size/colour)
#             short description right-aligned (fontsize 8, muted)
_MAIN_ROWS = [
    (0.840, "x", "#38bdf8", "current  x  (cm)"),
    (0.730, "s", "#4ade80", "x²  →  green square"),
    (0.625, "t", "#86efac", "½·8·(8−x)  →  triangle"),
    (0.490, "G", "#4ade80", "total green area"),
    (0.385, "W", "#f1f5f9", "total white area"),
]
for y, sym, col, desc in _MAIN_ROWS:
    rd.text(0.06, y, sym, ha="left", va="center", color=col,
            fontsize=22, fontweight="bold", transform=rd.transAxes,
            family="monospace")
    rd.text(0.95, y, desc, ha="right", va="center", color="#94a3b8",
            fontsize=8, transform=rd.transAxes)

# dynamic value text objects — updated in-place every frame
_rd_x   = rd.text(0.31, 0.840, "—", ha="left", va="center",
                  color="#38bdf8", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_sq  = rd.text(0.31, 0.730, "—", ha="left", va="center",
                  color="#4ade80", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_tri = rd.text(0.31, 0.625, "—", ha="left", va="center",
                  color="#86efac", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_grn = rd.text(0.31, 0.490, "—", ha="left", va="center",
                  color="#4ade80", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_wht = rd.text(0.31, 0.385, "—", ha="left", va="center",
                  color="#f1f5f9", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")

# ── balance section ───────────────────────────────────────────────────────────
rd.text(0.5, 0.255, "green  ←  balance  →  white",
        ha="center", va="center", color="#64748b",
        fontsize=8.5, transform=rd.transAxes)

_bar_bg = rd.add_patch(Rectangle(
    (0.05, 0.175), 0.90, 0.065,
    facecolor="#1e293b", edgecolor="#334155", linewidth=1,
    transform=rd.transAxes, zorder=4,
))
_bar_fill = rd.add_patch(Rectangle(
    (0.05, 0.175), 0.45, 0.065,
    facecolor="#4ade80", edgecolor="none",
    transform=rd.transAxes, zorder=5,
))
rd.add_artist(Line2D([0.505, 0.505], [0.165, 0.250],
                     color="#3b82f6", lw=2, transform=rd.transAxes, zorder=6))

_rd_status = rd.text(0.5, 0.132, "", ha="center", va="center",
                     color="#fbbf24", fontsize=12, fontweight="bold",
                     transform=rd.transAxes, family="monospace")

# ── algebra hint ──────────────────────────────────────────────────────────────
rd.text(0.5, 0.088,
        "32 + 4x − x²  =  x² + 32 − 4x",
        ha="center", va="center", color="#475569",
        fontsize=8.5, transform=rd.transAxes, style="italic")
rd.text(0.5, 0.052,
        "2x² − 8x = 0   →   x(x − 4) = 0",
        ha="center", va="center", color="#475569",
        fontsize=8.5, transform=rd.transAxes, style="italic")
rd.text(0.5, 0.020,
        "∴  x = 4 cm",
        ha="center", va="center", color="#34d399",
        fontsize=10, fontweight="bold", transform=rd.transAxes,
        family="monospace")

# ── slider + textbox ──────────────────────────────────────────────────────────
ax_sl    = fig.add_axes([0.06, 0.155, 0.43, 0.032])
ax_sl_tb = fig.add_axes([0.505, 0.155, 0.068, 0.030])

sl_x = Slider(ax_sl, "x  (side of small square)", 0.0, SIDE, valinit=2.0,
              color="#4ade80", track_color="#dcfce7")
tb_x = TextBox(ax_sl_tb, "", initial="2.00", color="#1e293b", hovercolor="#334155")
try:
    tb_x.text_disp.set_color("#e2e8f0")
    tb_x.text_disp.set_fontsize(9)
    tb_x.text_disp.set_fontfamily("monospace")
except AttributeError:
    pass

# ── checkboxes ────────────────────────────────────────────────────────────────
ax_checks = fig.add_axes([0.06, 0.030, 0.25, 0.095])
checks = CheckButtons(
    ax_checks,
    ["Show area labels", "Show formulas"],
    actives=[True, False],
)

# ── buttons ───────────────────────────────────────────────────────────────────
ax_btn_solve = fig.add_axes([0.34, 0.065, 0.115, 0.042])
ax_btn_anim  = fig.add_axes([0.34, 0.018, 0.115, 0.042])
btn_solve = Button(ax_btn_solve, "Show x = 4",     color="#dcfce7", hovercolor="#bbf7d0")
btn_anim  = Button(ax_btn_anim,  "▶  Animate",     color="#dbeafe", hovercolor="#bfdbfe")

# ── mutable drawing artists ────────────────────────────────────────────────────
_artists: list = []
_anim_active    = False
_anim_direction = 1
_suppress_tb    = False


def _clear() -> None:
    for obj in _artists:
        obj.remove()
    _artists.clear()


def _draw(x: float, show_labels: bool, show_formulas: bool) -> None:
    v  = _vertices(x)
    sq, tri, white = _areas(x)
    # ── filled regions ──
    # white background of big square
    bg = Rectangle((0, 0), SIDE, SIDE, facecolor="#ffffff",
                   edgecolor="none", zorder=1)
    ax.add_patch(bg)
    _artists.append(bg)

    # green triangle ABP
    t = Polygon([v["A"], v["B"], v["P"]], closed=True,
                facecolor="#4ade80", edgecolor="#16a34a",
                linewidth=1.8, alpha=0.80, zorder=2)
    ax.add_patch(t)
    _artists.append(t)

    # green small square DEPF
    s = Polygon([v["D"], v["E"], v["P"], v["F"]], closed=True,
                facecolor="#4ade80", edgecolor="#16a34a",
                linewidth=1.8, alpha=0.80, zorder=3)
    ax.add_patch(s)
    _artists.append(s)

    # outline of big square on top
    outline = Rectangle((0, 0), SIDE, SIDE, facecolor="none",
                        edgecolor="#1e293b", linewidth=2.8, zorder=4)
    ax.add_patch(outline)
    _artists.append(outline)

    # ── dimension arrows ──
    S = SIDE
    # bottom: 8 cm
    a1 = ax.annotate("", xy=(S, -0.55), xytext=(0, -0.55),
                     arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.5),
                     zorder=5)
    _artists.append(a1)
    _artists.append(ax.text(S/2, -0.90, "8 cm", ha="center", va="top",
                            fontsize=11, fontweight="bold", color="#1e293b"))

    # right: 8 cm
    a2 = ax.annotate("", xy=(S + 0.55, S), xytext=(S + 0.55, 0),
                     arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.5),
                     zorder=5)
    _artists.append(a2)
    _artists.append(ax.text(S + 0.92, S/2, "8 cm", ha="left", va="center",
                            fontsize=11, fontweight="bold", color="#1e293b",
                            rotation=90))

    if x > 0.3:
        # top: x
        a3 = ax.annotate("", xy=(x, S + 0.45), xytext=(0, S + 0.45),
                         arrowprops=dict(arrowstyle="<->", color="#16a34a", lw=1.8),
                         zorder=5)
        _artists.append(a3)
        _artists.append(ax.text(x/2, S + 0.75, f"x = {x:.2f}", ha="center",
                                va="bottom", fontsize=11, fontweight="bold",
                                color="#16a34a"))
        # left: x
        a4 = ax.annotate("", xy=(-0.45, S), xytext=(-0.45, S - x),
                         arrowprops=dict(arrowstyle="<->", color="#16a34a", lw=1.8),
                         zorder=5)
        _artists.append(a4)
        _artists.append(ax.text(-0.75, S - x/2, "x", ha="right", va="center",
                                fontsize=12, fontweight="bold", color="#16a34a"))

    # ── vertex dots and labels ──
    offsets = dict(
        A=(-0.18, -0.18), B=(0.18, -0.18), C=(0.18, 0.18), D=(-0.18, 0.18),
        E=(-0.18, 0.0),   F=(0.0,  0.18),  P=(0.22, -0.18),
    )
    ha_map = dict(A="right", B="left", C="left", D="right",
                  E="right", F="center", P="left")
    va_map = dict(A="top", B="top", C="bottom", D="bottom",
                  E="center", F="bottom", P="top")

    for name, (vx, vy) in v.items():
        dx, dy = offsets[name]
        dot, = ax.plot(vx, vy, "o", ms=5.5, color="#1e293b", zorder=7)
        _artists.append(dot)
        lbl = ax.text(vx + dx, vy + dy, name,
                      ha=ha_map[name], va=va_map[name],
                      fontsize=12, fontweight="bold", color="#1e293b", zorder=7)
        _artists.append(lbl)

    # ── area labels on canvas ──
    if show_labels and x > 0.5:
        # label inside small square
        cx_sq = x / 2
        cy_sq = SIDE - x / 2
        if x > 1.0:
            _artists.append(ax.text(cx_sq, cy_sq, f"x² = {sq:.1f}",
                                    ha="center", va="center", fontsize=9,
                                    fontweight="bold", color="#14532d", zorder=8))
        # label inside triangle
        cx_tr = (v["A"][0] + v["B"][0] + v["P"][0]) / 3
        cy_tr = (v["A"][1] + v["B"][1] + v["P"][1]) / 3
        _artists.append(ax.text(cx_tr, cy_tr, f"½·8·(8−x)\n= {tri:.1f}",
                                ha="center", va="center", fontsize=9,
                                fontweight="bold", color="#14532d", zorder=8))

    if show_formulas:
        # formula strings floating next to the shapes
        if x > 0.5:
            _artists.append(ax.text(x/2, SIDE - x/2, f"x² = {sq:.2f}",
                                    ha="center", va="center", fontsize=8.5,
                                    color="#166534", zorder=8,
                                    bbox=dict(fc="#f0fdf4", ec="#86efac",
                                              boxstyle="round,pad=0.3")))
        _artists.append(ax.text((SIDE + x)/2 + 0.2, (SIDE - x)/3,
                                f"4(8−x)\n= {tri:.2f}",
                                ha="left", va="center", fontsize=8.5,
                                color="#166534", zorder=8,
                                bbox=dict(fc="#f0fdf4", ec="#86efac",
                                          boxstyle="round,pad=0.3")))

    fig.canvas.draw_idle()


def _update_readout(x: float) -> None:
    sq, tri, white = _areas(x)
    green = sq + tri
    total = SIDE * SIDE
    diff  = green - white      # positive → too much green

    _rd_x.set_text(f"{x:.2f} cm")
    _rd_sq.set_text(f"{sq:.2f}")
    _rd_tri.set_text(f"{tri:.2f}")
    _rd_grn.set_text(f"{green:.2f}")
    _rd_wht.set_text(f"{white:.2f}")

    # Balance bar: width = fraction of total that is green
    frac = green / total
    bar_w = 0.90 * max(0.0, min(1.0, frac))
    _bar_fill.set_width(bar_w)

    if abs(diff) < 0.3:
        _bar_fill.set_facecolor("#4ade80")
        _rd_status.set_text("✓  BALANCED!")
        _rd_status.set_color("#4ade80")
    elif diff > 0:
        _bar_fill.set_facecolor("#f87171")
        _rd_status.set_text(f"green > white  +{diff:.2f}")
        _rd_status.set_color("#f87171")
    else:
        _bar_fill.set_facecolor("#60a5fa")
        _rd_status.set_text(f"white > green  +{-diff:.2f}")
        _rd_status.set_color("#60a5fa")


def _refresh(_=None) -> None:
    global _suppress_tb
    x = sl_x.val
    status = checks.get_status()
    show_labels, show_formulas = status[0], status[1]

    _suppress_tb = True
    tb_x.set_val(f"{x:.2f}")
    _suppress_tb = False

    _clear()
    _draw(x, show_labels, show_formulas)
    _update_readout(x)


# ── textbox handler ───────────────────────────────────────────────────────────
def _on_tb(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_x.set_val(max(0.0, min(SIDE, float(text))))
    except ValueError:
        pass


# ── animation ─────────────────────────────────────────────────────────────────
def _animate(_=None) -> None:
    global _anim_active, _anim_direction
    _anim_active = not _anim_active
    btn_anim.label.set_text("■  Stop" if _anim_active else "▶  Animate")
    btn_anim.ax.set_facecolor("#fecaca" if _anim_active else "#dbeafe")
    if _anim_active:
        _run_anim()


def _run_anim() -> None:
    if not _anim_active:
        return
    nxt = sl_x.val + _anim_direction * 0.06
    if nxt >= SIDE:
        nxt = SIDE;  globals()["_anim_direction"] = -1
    elif nxt <= 0.0:
        nxt = 0.0;   globals()["_anim_direction"] = 1
    sl_x.set_val(nxt)
    fig.canvas.flush_events()
    timer.start()


timer = fig.canvas.new_timer(interval=40)
timer.single_shot = True
timer.add_callback(_run_anim)

# ── wire up ───────────────────────────────────────────────────────────────────
sl_x.on_changed(_refresh)
tb_x.on_submit(_on_tb)
checks.on_clicked(_refresh)
btn_solve.on_clicked(lambda _: sl_x.set_val(4.0))
btn_anim.on_clicked(_animate)

# ── initial draw ──────────────────────────────────────────────────────────────
_refresh()
plt.show()
