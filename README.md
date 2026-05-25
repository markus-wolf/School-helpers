# School Helpers

Interactive Python visualisations for exploring geometry and area — aimed at middle-school students and anyone learning the ideas behind the formulas.

Each program opens a **matplotlib** window with a drawing area, live numeric readouts, and sliders/buttons you can drag and click to experiment. Nothing runs in the browser; everything is local on your machine.

## Requirements

- **Python 3.13** (via [pyenv](https://github.com/pyenv/pyenv); see `.python-version`)
- **matplotlib** and **numpy** (listed in `requirements.txt`)

## Setup

```bash
cd School-helpers
pyenv install -s          # installs 3.13.0 if needed
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running a helper

Activate the virtual environment, then run any script:

```bash
source .venv/bin/activate
python circle_area_peel_demo.py
```

| Program | Command |
|---------|---------|
| Circles & ellipses | `python circle_ellipse_demo.py` |
| Square area puzzle | `python geometry_areas_demo.py` |
| Circle area (peel) | `python circle_area_peel_demo.py` |

---

## Programs

### `circle_ellipse_demo.py` — Circles and ellipses

Shows how a **circle** and an **ellipse** relate through their two foci.

- Drag **Foci apart** from 0 to watch the two foci merge into one point — a **circle** — then separate again into an **ellipse**.
- Adjust **a** (semi-major axis), move a point around the curve, and see distances **d₁** and **d₂** to each focus.
- The live panel tracks **a**, **b**, **c**, and checks that **d₁ + d₂ = 2a** (the string property of an ellipse).
- Presets: **Circle**, **Wide Ellipse**; optional **Animate Foci** to oscillate between circle and ellipse.
- Toggles: string lines, axes, and dimension labels.

**Concepts:** focus, semi-major/semi-minor axes, Pythagorean rule **b² = a² − c²**, ellipse as “two foci + fixed string length”.

---

### `geometry_areas_demo.py` — Square area balance puzzle

An interactive puzzle built from two squares inside a larger square **ABCD**.

- A small green square **DEPF** (side **x**) sits in the corner; the rest of the green region is a triangle.
- The remaining **white** region must equal the total **green** area — find **x**.
- Drag **x** (or type a value) and watch areas update in the live panel with a balance bar.
- **Show x = 4** jumps to the solution; **Animate** sweeps **x** back and forth.
- Optional area labels and formula hints on the diagram.

**Concepts:** area of squares and triangles, setting up an equation, solving **x(x − 4) = 0** → **x = 4 cm**.

---

### `circle_area_peel_demo.py` — Area of a circle (peel the rings)

An animated proof that **A = πr²** by cutting the circle into concentric rings, unrolling each into a straight line, and stacking them into a triangle.

#### The idea

1. Start with a full circle of radius **r**, built from coloured concentric rings.
2. Peel each ring from the outside in. Every ring goes through **five animation stages**:
   - small gap at the top of the ring on the circle
   - gap widens (ring opening)
   - arc flattens and lifts away
   - mostly straight line, descending toward the stack
   - nearly flat line landing on the triangle
3. Stacked lines form a triangle with base **2πr** and height **r**.
4. Therefore **A = ½ × 2πr × r = πr²**.

#### Controls

| Control | What it does |
|---------|--------------|
| **Peel rings** | Scrub peel progress (0 = full circle, 1 = fully stacked) |
| **▶ Peel** / **■ Stop** | Play or stop the automatic peel animation |
| **Reset** | Return to the full circle |
| **Sec / ring** | Animation speed per ring (default **0.25 s**; range **0.01–3 s**) |
| **Layer δ/r** | Ring thickness as a fraction of **r** (0 → many thin rings; 1 → one thick ring) |
| **Radius r** | Resize the circle |
| **Show labels** | Toggle dimension arrows (**r**, **2πr**) on the diagram |
| **Show peel hint** | Toggle yellow gap markers and drop guides during peeling |

#### Live readout panel

Tracks **r**, circumference **C**, triangle base **b**, height **h**, area **A**, ring count **N**, and layer thickness **δ**. The proof steps and formula update as you peel.

**Concepts:** circumference, triangle area, visual derivation of **πr²**, how finer rings (smaller **δ/r**) better approximate the true area.

---

## Project layout

```
School-helpers/
├── README.md
├── requirements.txt
├── .python-version
├── circle_ellipse_demo.py
├── geometry_areas_demo.py
└── circle_area_peel_demo.py
```
