"""Interactive circle and ellipse demonstration for middle school students.

Run with (pyenv + .venv):
    source .venv/bin/activate
    python circle_ellipse_demo.py

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
from matplotlib.patches import Ellipse, FancyBboxPatch
from matplotlib.widgets import Button, CheckButtons, Slider, TextBox

# ── initial / range constants ─────────────────────────────────────────────────
_A_INIT     = 4.0
_A_MIN      = 1.5
_A_MAX      = 5.5
_ANGLE_INIT = 45.0


def _semi_minor(a: float, c: float) -> float:
    """Semi-minor axis b from a and focal distance c."""
    return math.sqrt(max(a**2 - c**2, 0.0))


def _point_on_ellipse(angle_deg: float, a: float, c: float) -> tuple[float, float]:
    b   = _semi_minor(a, c)
    rad = math.radians(angle_deg)
    return a * math.cos(rad), b * math.sin(rad)


# ── figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 7.8), facecolor="#fdfaf4")
fig.canvas.manager.set_window_title("Circles and Ellipses: One Centre, Two Foci")

# Main drawing canvas – raised to y=0.37 to make room for three slider rows
ax = fig.add_axes([0.04, 0.37, 0.54, 0.59])
ax.set_facecolor("#fffdf5")
ax.set_xlim(-6.0, 6.0)
ax.set_ylim(-5.2, 5.2)
ax.set_aspect("equal")
ax.grid(color="#ede8db", linewidth=0.8)
ax.tick_params(labelsize=9, color="#aaa")
for spine in ax.spines.values():
    spine.set_color("#d5cfc0")

# ── live readout panel ────────────────────────────────────────────────────────
rd = fig.add_axes([0.60, 0.62, 0.38, 0.34])
rd.set_axis_off()
# set_axis_off() hides the patch too – restore manually
rd.patch.set_facecolor("#0f172a")
rd.patch.set_visible(True)

rd.add_patch(FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
    fill=False, edgecolor="#3b82f6", linewidth=2.5,
    transform=rd.transAxes, clip_on=False, zorder=10,
))
rd.text(0.5, 0.945, "◈  LIVE VALUES", ha="center", va="top",
        color="#ffffff", fontsize=12, fontweight="bold",
        transform=rd.transAxes, family="monospace")

for y, col, lw in [(0.855, "#3b82f6", 1.5), (0.515, "#334155", 1.0),
                   (0.330, "#334155", 1.0)]:
    rd.add_artist(Line2D([0.04, 0.96], [y, y], color=col, lw=lw,
                         transform=rd.transAxes, zorder=5))

for y, sym, col, desc in [
    (0.75, "a", "#38bdf8", "half-width  (semi-major)"),
    (0.62, "b", "#c084fc", "half-height (semi-minor)"),
    (0.43, "c", "#fb923c", "focus distance"),
]:
    rd.text(0.06, y, sym, ha="left", va="center", color=col,
            fontsize=22, fontweight="bold", transform=rd.transAxes,
            family="monospace")
    rd.text(0.95, y, desc, ha="right", va="center", color="#94a3b8",
            fontsize=8, transform=rd.transAxes)

rd.text(0.5, 0.275, "distances  P → foci", ha="center", va="center",
        color="#64748b", fontsize=8.5, transform=rd.transAxes)

# dynamic text objects – updated in-place every frame
_rd_a   = rd.text(0.31, 0.75, f"{_A_INIT:.2f}", ha="left", va="center",
                  color="#38bdf8", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_b   = rd.text(0.31, 0.62, "—", ha="left", va="center",
                  color="#c084fc", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_c   = rd.text(0.31, 0.43, "0.00", ha="left", va="center",
                  color="#fb923c", fontsize=22, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_d1  = rd.text(0.06, 0.195, "d₁ = —", ha="left", va="center",
                  color="#fbbf24", fontsize=12, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_d2  = rd.text(0.54, 0.195, "d₂ = —", ha="left", va="center",
                  color="#fbbf24", fontsize=12, fontweight="bold",
                  transform=rd.transAxes, family="monospace")
_rd_sum = rd.text(0.5, 0.085, "d₁ + d₂ = —", ha="center", va="center",
                  color="#34d399", fontsize=13, fontweight="bold",
                  transform=rd.transAxes, family="monospace")

# ── explanatory text panel ────────────────────────────────────────────────────
info_ax = fig.add_axes([0.60, 0.08, 0.38, 0.52])
info_ax.set_axis_off()
info_text = info_ax.text(
    0.0, 1.0, "", transform=info_ax.transAxes,
    va="top", ha="left", fontsize=10, wrap=True,
    bbox=dict(boxstyle="round,pad=0.7", fc="#f7f2e4", ec="#c8bfa0", lw=1.5),
)

# ── sliders + textbox entry fields ────────────────────────────────────────────
# Layout: slider occupies x 0.07–0.44, textbox x 0.455–0.525
_SL_X, _SL_W, _SL_H = 0.07, 0.37, 0.032
_TB_X, _TB_W, _TB_H = 0.455, 0.068, 0.030

# y positions for the three rows
_Y_A, _Y_F, _Y_ANG = 0.295, 0.237, 0.179

ax_a        = fig.add_axes([_SL_X, _Y_A,   _SL_W, _SL_H])
ax_a_tb     = fig.add_axes([_TB_X, _Y_A,   _TB_W, _TB_H])
ax_focus    = fig.add_axes([_SL_X, _Y_F,   _SL_W, _SL_H])
ax_focus_tb = fig.add_axes([_TB_X, _Y_F,   _TB_W, _TB_H])
ax_angle    = fig.add_axes([_SL_X, _Y_ANG, _SL_W, _SL_H])
ax_angle_tb = fig.add_axes([_TB_X, _Y_ANG, _TB_W, _TB_H])

sl_a     = Slider(ax_a,     "a  (half-width)", _A_MIN, _A_MAX,  valinit=_A_INIT,
                  color="#38bdf8", track_color="#e0f2fe")
sl_focus = Slider(ax_focus, "Foci apart",      0.0,    _A_MAX,  valinit=0.0,
                  color="#9b59b6", track_color="#e8dff5")
sl_angle = Slider(ax_angle, "Point angle",     0.0,    360.0,   valinit=_ANGLE_INIT,
                  color="#e67e22", track_color="#fde8c8")

_TB_BG, _TB_HOVER = "#1e293b", "#334155"
tb_a     = TextBox(ax_a_tb,     "", initial=f"{_A_INIT:.2f}",    color=_TB_BG, hovercolor=_TB_HOVER)
tb_focus = TextBox(ax_focus_tb, "", initial="0.00",               color=_TB_BG, hovercolor=_TB_HOVER)
tb_angle = TextBox(ax_angle_tb, "", initial=f"{_ANGLE_INIT:.1f}", color=_TB_BG, hovercolor=_TB_HOVER)

# Make textbox text readable on dark background
for tb in (tb_a, tb_focus, tb_angle):
    try:
        tb.text_disp.set_color("#e2e8f0")
        tb.text_disp.set_fontsize(9)
        tb.text_disp.set_fontfamily("monospace")
    except AttributeError:
        pass

# ── checkboxes ────────────────────────────────────────────────────────────────
ax_checks = fig.add_axes([0.07, 0.025, 0.26, 0.115])
checks = CheckButtons(
    ax_checks,
    ["Show string lines", "Show axes", "Show a & b"],
    actives=[True, True, False],
)

# ── preset / action buttons ───────────────────────────────────────────────────
ax_btn_circle  = fig.add_axes([0.36, 0.062, 0.10, 0.042])
ax_btn_ellipse = fig.add_axes([0.47, 0.062, 0.10, 0.042])
ax_btn_anim    = fig.add_axes([0.36, 0.015, 0.21, 0.042])
btn_circle  = Button(ax_btn_circle,  "Circle",          color="#dceeff", hovercolor="#b8daff")
btn_ellipse = Button(ax_btn_ellipse, "Wide Ellipse",    color="#eadfff", hovercolor="#d4c4f7")
btn_anim    = Button(ax_btn_anim,    "▶  Animate Foci", color="#d5f5e3", hovercolor="#a9dfbf")

# ── mutable canvas artists ────────────────────────────────────────────────────
_shape_patch: Ellipse | None = None
_focus_dots:  list = []
_center_dot   = None
_center_label = None
_string_lines: list[Line2D] = []
_point_dot    = None
_point_label  = None
_axis_lines:  list[Line2D] = []
_foci_labels: list = []
_title_text   = None
_ab_artists:  list = []

_anim_active    = False
_anim_direction = 1
_suppress_tb    = False   # guard: prevents slider→textbox→slider feedback loops


def _clear_artists() -> None:
    global _shape_patch, _center_dot, _center_label, _point_dot, _point_label, _title_text

    for obj in (_shape_patch, _center_dot, _center_label,
                _point_dot, _point_label, _title_text):
        if obj is not None:
            obj.remove()
    _shape_patch = _center_dot = _center_label = None
    _point_dot = _point_label = _title_text = None

    for obj in (_string_lines + _axis_lines + _focus_dots
                + _foci_labels + _ab_artists):
        obj.remove()
    _string_lines.clear()
    _axis_lines.clear()
    _focus_dots.clear()
    _foci_labels.clear()
    _ab_artists.clear()


def _draw(a: float, c: float, angle_deg: float,
          show_strings: bool, show_axes: bool, show_ab: bool) -> None:
    global _shape_patch, _center_dot, _center_label, _point_dot, _point_label, _title_text

    b  = _semi_minor(a, c)
    px, py = _point_on_ellipse(angle_deg, a, c)
    is_circle   = c < 0.05
    shape_color = "#2e86de" if is_circle else "#7b3fe4"
    fill_color  = "#dceeff" if is_circle else "#eadfff"

    # Dynamic canvas limits so the shape always fits with some padding
    pad = a * 0.38 + 0.8
    ax.set_xlim(-(a + pad), a + pad)
    ax.set_ylim(-(a + pad * 0.75), a + pad * 0.75)

    # Shape
    _shape_patch = Ellipse(
        (0, 0), width=2 * a, height=2 * b,
        edgecolor=shape_color, facecolor=fill_color, linewidth=3.5, zorder=2,
    )
    ax.add_patch(_shape_patch)

    # Guide axes (dashed)
    if show_axes:
        h, = ax.plot([-a, a], [0, 0], color="#a09080", lw=1.6, ls="--", zorder=1)
        v, = ax.plot([0, 0], [-b, b], color="#a09080", lw=1.6, ls="--", zorder=1)
        _axis_lines.extend([h, v])

    # a & b dimension arrows
    if show_ab:
        v_off = b * 0.20 + 0.28        # vertical offset for the horizontal arrow
        h_off = a * 0.20 + 0.28        # horizontal offset for the vertical arrow
        font_sz = max(9, min(12, int(a * 2.2)))

        arr_a = ax.annotate("", xy=(a, v_off), xytext=(0, v_off),
                            arrowprops=dict(arrowstyle="<->", color="#38bdf8",
                                            lw=2.5, mutation_scale=16), zorder=4)
        lbl_a = ax.text(a / 2, v_off + a * 0.07, f"a = {a:.2f}",
                        ha="center", va="bottom", color="#38bdf8",
                        fontsize=font_sz, fontweight="bold", zorder=4)

        arr_b = ax.annotate("", xy=(-h_off, b), xytext=(-h_off, 0),
                            arrowprops=dict(arrowstyle="<->", color="#c084fc",
                                            lw=2.5, mutation_scale=16), zorder=4)
        lbl_b = ax.text(-h_off - a * 0.06, b / 2, f"b = {b:.2f}",
                        ha="right", va="center", color="#c084fc",
                        fontsize=font_sz, fontweight="bold", zorder=4, rotation=90)

        _ab_artists.extend([arr_a, lbl_a, arr_b, lbl_b])

    # Foci
    unit = a * 0.11   # scale label offsets with a
    if is_circle:
        dot, = ax.plot(0, 0, "o", ms=16, color="none",
                       markeredgecolor="#e67e22", markeredgewidth=3.5, zorder=5)
        _focus_dots.append(dot)
        lbl = ax.text(0, unit * 1.3, "both foci here", ha="center",
                      color="#b35400", fontsize=11, fontweight="bold", zorder=6)
        _foci_labels.append(lbl)
    else:
        for xi, label in [(-c, "focus 1"), (c, "focus 2")]:
            d, = ax.plot(xi, 0, "o", ms=11, color="#e67e22",
                         markeredgecolor="white", markeredgewidth=1.8, zorder=5)
            _focus_dots.append(d)
            lbl = ax.text(xi, -unit * 1.2, label, ha="center",
                          color="#b35400", fontsize=10, fontweight="bold", zorder=6)
            _foci_labels.append(lbl)

    # Centre
    _center_dot, = ax.plot(0, 0, "o", ms=9, color="#222",
                           markeredgecolor="white", markeredgewidth=1.8, zorder=6)
    _center_label = ax.text(unit * 0.35, -unit * 1.2, "centre",
                            color="#222", fontsize=10, fontweight="bold", zorder=6)

    # String lines
    if show_strings:
        for fx in [-c, c]:
            line, = ax.plot([fx, px], [0, py], color="#f39c12", lw=2.5, zorder=3)
            _string_lines.append(line)

    # Point P
    _point_dot, = ax.plot(px, py, "o", ms=10, color="#c0392b",
                          markeredgecolor="white", markeredgewidth=1.8, zorder=7)
    _point_label = ax.text(px + unit * 0.35, py + unit * 0.55, "point P",
                           color="#8e2a1e", fontsize=10, fontweight="bold", zorder=7)

    # Title (axes-fraction coordinates so it stays at the top regardless of scale)
    _title_text = ax.text(0.5, 0.97, "Circle" if is_circle else "Ellipse",
                          ha="center", va="top", color=shape_color,
                          fontsize=26, fontweight="bold", zorder=8,
                          transform=ax.transAxes)

    fig.canvas.draw_idle()


def _update_readout(a: float, c: float, angle_deg: float) -> None:
    b  = _semi_minor(a, c)
    px, py = _point_on_ellipse(angle_deg, a, c)
    d1 = math.hypot(px - (-c), py)
    d2 = math.hypot(px - c,    py)

    _rd_a.set_text(f"{a:.2f}")
    _rd_b.set_text(f"{b:.2f}")
    _rd_c.set_text(f"{c:.2f}")
    _rd_d1.set_text(f"d₁ = {d1:.2f}")
    _rd_d2.set_text(f"d₂ = {d2:.2f}")
    check = "  ✓" if abs(d1 + d2 - 2 * a) < 0.05 else ""
    _rd_sum.set_text(f"d₁ + d₂ = {d1 + d2:.2f}{check}")


def _update_info(a: float, c: float) -> None:
    b = _semi_minor(a, c)
    if c < 0.05:
        shape_note = (
            "The two foci have converged to one\n"
            "point — the centre. Every point on\n"
            "the shape is the same distance away.\n"
            "That is the definition of a circle!"
        )
    else:
        shape_note = (
            "The two foci are separated.\n"
            f"  Pythagorean rule: b² = a² − c²\n"
            f"  {b:.2f}² ≈ {a:.2f}² − {c:.2f}²  ✓"
        )

    info_text.set_text(
        "── What you are seeing ──\n"
        f"{shape_note}\n\n"
        "── Ellipse string rule ──\n"
        "Tie a string between the two foci and\n"
        "loop it around a pencil. Wherever you\n"
        "draw, the total string length stays fixed.\n\n"
        "── Try it ──\n"
        "① Drag 'Foci apart' to 0   → circle\n"
        "② Drag it right            → ellipse\n"
        "③ Change 'a (half-width)'  → resize shape\n"
        "④ Move 'Point angle'       → watch d₁+d₂\n"
        "⑤ Press Animate Foci       → see foci merge\n"
        "⑥ Tick 'Show a & b'       → see dimensions\n"
        "  Type a number + Enter in any box →\n"
        "  jump straight to that value"
    )


def _c_max(a: float) -> float:
    """Maximum allowed focal distance for a given a (keeps b ≥ 0.1)."""
    return math.sqrt(max(a**2 - 0.01, 0.0))


def _refresh(_=None) -> None:
    global _suppress_tb

    a         = sl_a.val
    c         = min(sl_focus.val, _c_max(a))   # clamp without touching slider
    angle_deg = sl_angle.val

    status = checks.get_status()
    show_strings, show_axes, show_ab = status[0], status[1], status[2]

    # Sync textboxes without triggering their on_submit callbacks
    _suppress_tb = True
    tb_a.set_val(f"{a:.2f}")
    tb_focus.set_val(f"{c:.2f}")
    tb_angle.set_val(f"{angle_deg:.1f}")
    _suppress_tb = False

    _clear_artists()
    _draw(a, c, angle_deg, show_strings, show_axes, show_ab)
    _update_readout(a, c, angle_deg)
    _update_info(a, c)


# ── textbox submit handlers ────────────────────────────────────────────────────
def _on_tb_a(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_a.set_val(max(_A_MIN, min(_A_MAX, float(text))))
    except ValueError:
        pass


def _on_tb_focus(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_focus.set_val(max(0.0, min(_c_max(sl_a.val), float(text))))
    except ValueError:
        pass


def _on_tb_angle(text: str) -> None:
    if _suppress_tb:
        return
    try:
        sl_angle.set_val(max(0.0, min(360.0, float(text))))
    except ValueError:
        pass


# ── animation ─────────────────────────────────────────────────────────────────
def _animate(_=None) -> None:
    global _anim_active, _anim_direction
    _anim_active = not _anim_active
    btn_anim.label.set_text("■  Stop" if _anim_active else "▶  Animate Foci")
    btn_anim.ax.set_facecolor("#f5b7b1" if _anim_active else "#d5f5e3")
    if _anim_active:
        _run_anim()


def _run_anim() -> None:
    if not _anim_active:
        return
    top = _c_max(sl_a.val)
    nxt = sl_focus.val + _anim_direction * 0.06
    if nxt >= top:
        nxt = top
        globals()["_anim_direction"] = -1
    elif nxt <= 0.0:
        nxt = 0.0
        globals()["_anim_direction"] = 1
    sl_focus.set_val(nxt)
    fig.canvas.flush_events()
    timer.start()


timer = fig.canvas.new_timer(interval=35)
timer.single_shot = True
timer.add_callback(_run_anim)

# ── wire everything up ────────────────────────────────────────────────────────
sl_a.on_changed(_refresh)
sl_focus.on_changed(_refresh)
sl_angle.on_changed(_refresh)
checks.on_clicked(_refresh)
tb_a.on_submit(_on_tb_a)
tb_focus.on_submit(_on_tb_focus)
tb_angle.on_submit(_on_tb_angle)
btn_circle.on_clicked(lambda _: (sl_focus.set_val(0.0),))
btn_ellipse.on_clicked(lambda _: (sl_focus.set_val(sl_a.val * 0.82),))
btn_anim.on_clicked(_animate)

# ── initial draw ──────────────────────────────────────────────────────────────
_refresh()
plt.show()
