# Design decisions — L-Fold Pullstruder repackaging (CAD)

This document explains the parametric CAD model in `model.py` for the **L-Fold** layout of my Pullstruder (the machine that turns PET drink bottles into 3D-printer filament). It covers what I designed, what numbers I chose and *why*, how it stays inside every hard constraint, and what's still an open question. The model is the new **printed repackaging geometry** plus simple **placeholder blocks** that stand in for the parts I'm buying, so the STEP file shows the true size of the finished machine.

I built it in CadQuery (Python that drives a CAD kernel), so every dimension is a named variable at the top of `model.py` — change one number and the whole model rebuilds. That's deliberate: the bed is set by a single value (the confirmed 256 mm school printer), so if any constraint ever shifts I just update one value and re-run.

---

## 1. The big idea, in one paragraph

The old "runway" layout was a 554 mm straight line that was mostly air. L-Fold keeps the **thermal path** (the bit where plastic gets melted and then cooled, which must happen in a fixed left-to-right order) flat and horizontal, but **folds the spool and electronics up onto a vertical wall** at the downstream end. From the side the machine now reads as an **L**. That fold lets the spool sit *above* the machine instead of beside it, and it turns the previously-dead vertical air into mounting space for the control box, screen and power supply. I also slid the motor inward to delete the big empty gap it used to leave.

**Result from the model: the packaged machine is 495 × 180 × 270 mm** (length × depth × height), which fits inside the 500 × 200 × 300 mm size limit with room to spare on every axis.

---

## 2. Coordinate system (so the numbers make sense)

- **X** = along the horizontal thermal runway. The stripper (where the bottle strip enters) is the datum at **X = 0**. Positive X is downstream toward the back-plane; negative X is upstream toward the motor.
- **Y** = depth (front-to-back). Y = 0 is the centreline.
- **Z** = up. Z = 0 is the top face of the chassis base.
- Everything is in **millimetres** (mm), the natural unit for 3D printing.

---

## 3. The printed parts and why each value

### 3.1 Chassis (base) — the single frame everything bolts to
The chassis is one flat base slab with stiffening rails around the edge and raised pads where each station bolts down.

- **Thickness `CH_THK = 8 mm`** — thick enough not to flex under the motor's pull and the spool's spinning mass, but not wasteful of plastic. A thin base would bow.
- **Length** runs from `CH_X0 = −160 mm` (just upstream of the motor) to `CH_X1 = 294 mm` (flush with the front face of the vertical wall). That's **454 mm** of chassis — the single biggest driver of the final length.
- **Depth `CH_DEPTH = 180 mm`** — chosen so that once the widest parts (the power supply at 98 mm and the spool at 60 mm wide) are added, the total depth still stays under the 200 mm limit. It came out at 180 mm.
- **Side rails `RAIL_H = 16 mm`, wall `RAIL_W = 3 mm`** — a raised lip around the perimeter acts like the flange of an I-beam: it makes a thin slab much stiffer for very little extra plastic. 3 mm is my minimum wall (see §6).
- **Station pads** at X = 0 (stripper), 100 (hotend), 150 (fans), 220 (Hall sensor — reserved), and −130 (motor). Each pad is a raised boss with four **M4 clearance holes (4.5 mm)** so each station bolts down independently and can be unbolted on its own.

**The chassis is too long to print in one piece**, so `model.py` automatically cuts it into **bolted segments** that each fit the print bed. With the confirmed 256 mm bed it split into **2 chassis segments** (~227 mm each), joined by a bolted butt-splice. The sectioning is driven by the `BED` variable, not hard-coded, so it stays parametric.

### 3.2 Vertical back-plane — the "fold" surface (designed as bolted segments)
This is the standing wall that the spool, control box, screen and wiring mount to. It rises from the downstream end of the chassis.

- **Height `BP_HEIGHT = 270 mm`** — tall enough to carry the spool high up and give the screen an eye-height position, while keeping the whole machine under the 300 mm height limit.
- **Panel thickness `BP_THK = 6 mm`** plus side stiffener ribs — a tall thin PLA wall can wobble (resonate) when the spool spins, so 6 mm of panel with reinforcing ribs down each vertical edge keeps it rigid.
- **Split into `BP_SEGMENTS = 3` stacked pieces.** A single 270 mm-tall wall almost certainly won't fit the printer in one go, and the constraint says custom parts must be **bolted and fully disassemblable** anyway — so I designed it as three printed segments from the start, stacked and bolted at overlapping **splice bands** (`BP_SPLICE_OVERLAP = 24 mm`) with M4 bolts. This is the single most important "design for the printer" decision in the model.
- **Foot flange `BP_FLANGE = 18 mm`** — the bottom segment has a flange that lies on the chassis top and bolts down with three M4 bolts. **This flange is the bolted joint** — the wall does not pass through the chassis (I caught and fixed exactly that clash in QA iteration 3). The wall stands at the chassis edge; the flange is what holds it.
- **Mounting holes** — M3 holes (3.4 mm) on a grid on the rear face for the electronics, and M4 splice holes at each segment join.

### 3.3 Gussets — the anti-wobble braces
Two triangular braces (`GUSSET_RISE = 120 mm` up the wall, `GUSSET_RUN = 110 mm` along the chassis, 3 mm thick) tie the bottom of the back-plane to the chassis. A triangle is the rigid shape — these stop the tall wall from rocking back and forth when the spool spins. They sit just inside each side edge so they don't block the view of the process.

### 3.4 Cable raceway — the wiring spine
A U-shaped channel (open trough, 18 mm internal width, 3 mm walls) runs vertically up the rear face of the back-plane. All the 12 V wiring runs in here, tucked to one side so it doesn't sit on top of the electronics. This is the practical payoff of the fold: instead of wires sprawling across a 554 mm slab, every wire has one tidy vertical spine to follow.

---

## 4. Placeholder blocks — bought parts, NOT designed parts

These are **simple boxes and cylinders** that stake out where each bought component sits, so the STEP shows the real packaged size. **They are stand-ins, not parts I'm designing or printing.** In the model they're added with an **orange colour** and every placeholder name is prefixed **`PLACEHOLDER_`** in the STEP assembly tree, while the printed parts are **grey** — so it's obvious which is which.

| Placeholder | Size used (mm) | Where it sits |
|---|---|---|
| NEMA17 stepper (the motor/puller) | 42 × 42 × 48 body + 5 mm shaft | upstream, slid in to X = −130 |
| Volcano hotend (the melter) | 45 × 24 × 16 block + 30 nozzle, **nozzle pointing down** | X = 100, on the runway |
| 5015 blower fans ×2 (the quench) | 50 × 50 × 15 each | X = 150, flanking the nozzle |
| Arduino Uno (the brain) | 68.6 × 53.4 × 15 | rear face of back-plane |
| CNC Shield (driver board) | 68.6 × 53.4 × 20, **stacked on the Uno** | rear face of back-plane |
| 1602A LCD (the screen) | 80 × 36 × 12 | **front** face, eye height |
| 12 V 10 A PSU (power supply) | 129 × 98 × 38 | low and rearward, on the chassis |
| Spool of PET filament | 200 dia × 60 wide cylinder | folded up, high on the wall |

The 1602A screen is on the **front** of the wall (facing me when I operate it); the control boards are on the **rear** (out of the way, and offset upstream from the hotend so rising heat doesn't cook them).

---

## 5. How it respects every hard constraint

- **Footprint ≤ 500 × 200 × 300 mm** — model measures **495 × 180 × 270 mm**. Inside on all three axes, confirmed by reloading the exported STEP. ✔
- **Single chassis (non-negotiable)** — there is exactly one base. The back-plane is a bolted bracket rising from that one chassis, not a second base with its own footprint. ✔
- **Custom parts 3D-printed PLA, bolted, no adhesive, fully disassemblable** — every printed part joins with M3/M4 bolts: chassis segments butt-splice, back-plane segments stack-splice, the foot bolts to the chassis, stations bolt to pads. No glue anywhere; it all comes apart. ✔
- **Visible process (you can watch the plastic the whole way)** — the melt-and-cool path stays flat, horizontal and open at the front. The fold only lifts the *spool*, which sits high and to one side, so it never blocks the view of the strip entering, melting, and being cooled. ✔
- **Mains stays sealed in the certified PSU; I only wire 12 V** — the power supply is a sealed bought unit (a placeholder block here). Moving it low and rearward doesn't open it up. Everything I wire downstream of it is 12 V extra-low-voltage (ELV — safe, low-voltage DC). ✔
- **Room kept for the Phase-2 Hall sensor** — the Hall sensor (a magnetic speed sensor for a future closed-loop speed control) has its reserved pad untouched at **X = 220**, exactly where the concept fixed it. The fold happens downstream and upward, well clear of it. ✔
- **Quench order preserved** — the cooling fans stay immediately downstream of the nozzle (X = 150, just past the hotend at X = 100), so the melt is always cooled in the right order. ✔

---

## 6. Wall thickness and print orientation

- **Minimum wall `MIN_WALL = 3.0 mm`.** The PLA printability rule is 2.0 mm; I set every structural wall to **3.0 mm** because this frame vibrates (the spool spins), and a bit of extra wall buys stiffness and strength cheaply. The QA check confirms no designed wall is under 2.0 mm.
- **Print orientation notes:** the chassis segments print flat on the bed (largest face down — strongest and easiest). The back-plane segments print flat too, lying down, so the bolt-hole walls and splice bands come out clean. The gussets print on their flat triangular face. None of the printed parts need support material in these orientations, which keeps prints faster and the surfaces clean.

---

## 7. QA results (summary — full log in `qa_report.md`)

The model went through an automatic check-and-fix loop. It took **4 iterations** to get clean. The final result:

| Check | Result | Value |
|---|---|---|
| All printed parts geometrically valid | **PASS** | 9/9 |
| Envelope ≤ 500 × 200 × 300 | **PASS** | **495 × 180 × 270 mm** |
| Each printed part fits the bed (confirmed 256 mm) | **PASS** | all fit the 244 mm usable area |
| No printed part crashes into another | **PASS** | 0 real overlaps |
| Minimum wall ≥ 2.0 mm | **PASS** | 3.0 mm |

The three fixes along the way were: (1) a wrong-axis orientation bug that made the wall point sideways, (2) the spool sticking out too far downstream — fixed by stacking it *above* the runway, and (3) the wall passing through the chassis — fixed by bolting it on at the edge with the foot flange. The full diagnosis of each is in `qa_report.md`.

---

## 8. Open questions (be honest about what's unknown)

- **The school printer's bed size is confirmed at 256 mm** (`BED = 256`, a 256 mm cube build volume). Every "fits the bed" result is firm against that known constraint. The model stays parametric — if the bed value ever changed, it auto-splits the chassis and I'd bump `BP_SEGMENTS` for the wall, no redesign, just a re-run.
- **Exact spool height and feed angle** are still rough. The model puts the spool high on the wall, but the real climb path for the filament (so it doesn't kink while still warm) needs the physical string-test prototype the concept calls for.
- **Electronics temperature on the wall** — the boards are on the rear and offset from the hotend, but I should still do a thermocouple check under running conditions to be sure the rising heat is fine.
- **Placeholder accuracy** — the bought-part blocks are approximate sizes. When I have the real parts I'll measure them and update the placeholder dimensions, which will tighten the envelope number.
- **Clearance vs interference** — QA confirms nothing overlaps, but it doesn't yet check that there's enough *gap* for fingers/tools to assemble each bolt. That's a manual review before the build.

---

## 9. Files

- `model.py` — the parametric CadQuery model (all parameters at the top).
- `qa_check.py` — the automatic QA checker (the 5 rules).
- `lfold_assembly.step` — the STEP export (CAD interchange; opens in any CAD program).
- `lfold_assembly.stl` — the STL export (mesh, for slicing/printing or quick viewing).
- `qa_report.md` — the full iteration-by-iteration QA log.
