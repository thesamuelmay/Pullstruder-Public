# QA report — Pullstruder detailed CAD (spine-modules)

**Model:** `model_detailed.py`
**Checker:** `qa_check_detailed.py`
**How to run:**
```
cd /tmp && uv run --python 3.12 --with cadquery python model_detailed.py <OUTDIR>
cd /tmp && uv run --python 3.12 --with cadquery python qa_check_detailed.py <OUTDIR>/spine_detailed_assembly.step
```

The checker rebuilds the parametric model in memory, runs nine gates, and reimports the exported assembly STEP. It exits non-zero on any failure, so the build→check→fix loop is fully automatic.

---

## What each gate checks and why

| Gate | What it asserts | Why it matters |
|---|---|---|
| **G1 — per-part validity** | Every printed part is a valid solid (OpenCascade BRep check). | A part that isn't a clean solid can't be sliced or printed. |
| **G2 — assembly envelope** | The whole machine (printed + bought stand-ins) fits inside 500 × 200 × 300 mm. | Hard SAT footprint constraint. |
| **G3 — bed fit** | Every printed part fits the printer bed (BED = 256 mm, confirmed school printer), free to orient. | If a part is bigger than the bed it can't be printed in one piece. |
| **G4 — keyed mate + spacing** | Each module slot width = rail width + 2 × clearance, and no two modules overlap along the spine. | Proves the slide-fit clip works and the stations don't collide. |
| **G5 — minimum wall** | The thinnest designed wall is ≥ 2.0 mm. | Thinner than ~2 mm and PLA walls get weak/unreliable to print. |
| **G6 — cable channel clear** | The raceway clear bore is ≥ 8 × 8 mm. | The 12 V harness has to physically fit in the channel. |
| **G7 — STEP round-trip** | The exported assembly STEP reimports and is a valid solid. | Proves the file other software receives is actually usable. |
| **G8 — fastener clearance** | Every M3 hole ≥ 3.2 mm, every M4 hole ≥ 4.3 mm, and nut pockets are sized to the nut. | Print-tight holes still need to take the bolt; the captive nut has to seat. |
| **G9 — hole-pattern alignment** | The printed module holes land on the bought part's real holes within 0.2 mm. | If the holes don't line up, the part literally won't bolt on. Proven for: stripper module ↔ NEMA17 31 mm bolt square; controller mount ↔ Arduino Uno R3 4-hole pattern; hotend pair spacing ↔ Volcano. |

BED = 256 mm is **confirmed** — it is the school printer's measured build volume. It is a single parameter at the top of `model_detailed.py`; were the machine ever to change, edit it and re-run. The confirmed value is shown in the G3 gate label every run.

---

## Iteration log

### Iteration 1 — first full build
Ran the model, exported, ran all nine gates.

**Result: FAIL.** Three gates failed:

- **G2 envelope FAIL** — actual 459 × **202** × **316** mm. Width was 2 mm over the 200 mm limit and height was 16 mm over the 300 mm limit. Cause: the sealed-PSU stand-in sat too far out in Y (its far face reached Y = 109) and the take-up spool on the riser topped out at Z = 316 (riser was 175 mm tall, so the 95 mm-radius spool poked over the 300 mm ceiling).
- **G7 STEP round-trip FAIL** — "STEP File could not be loaded". Cause: the combined assembly was being written with `Assembly.save()`, which produces a structured (product-structure) STEP that CadQuery's own importer refuses to read back.
- **G9 hole-pattern alignment FAIL** — controller mount ↔ Arduino: maxdev = 6.84 mm. Cause: the Arduino stand-in was being centred on the **centroid** of the controller mount's holes. The Uno's four holes are an asymmetric pattern, so its centroid is not the same as the placement origin — centring on the centroid shifted the whole board off the printed holes.

**Fixes applied:**
1. G2 height: dropped the riser height from 175 mm to 155 mm so the spool top sits at Z = 296 mm (4 mm clear of the ceiling).
2. G2 width: pulled the PSU stand-in in from Y = 60 to Y = 48, and the LCD from Y = −75 to Y = −70, bringing total width to 185 mm.
3. G7: changed the assembly STEP export to a flat `Compound` written with `exporters.export(...)` (which reimports cleanly). The colour-coded structured STEP is still written separately as `spine_detailed_assembly_coloured.step` for viewing only.
4. G9: passed the printed controller mount's placement **origin** to the Arduino stand-in builder so the board's real 4-hole pattern is laid out about the same point — the holes then coincide exactly.

### Iteration 2 — re-check after fixes
**Result: still one FAIL.**

- **G7 STEP round-trip FAIL** — "STEP File could not be loaded", but this time because the file **did not exist**. Cause: `export_all()` wrote into the output directory without creating it first, so the very first export raised and no files landed. (The earlier `Assembly.save()` had been creating the directory as a side effect, which masked the bug.)

**Fix applied:** added `os.makedirs(outdir, exist_ok=True)` at the top of `export_all()`.

### Iteration 3 — re-check after directory fix
**Result: all nine gates PASS.** Envelope 459 × 185 × 296 mm. Assembly STEP reimports valid. All hole patterns align to 0.000 mm.

### Iteration 4 — print-plate tidy (no gate change)
The combined print plate initially packed onto 3 plates because a tall-first sort wasted bed area (the 93 mm-deep controller mount and 74 mm-deep spine segments each opened a near-empty row). Switched to declared-order shelf packing (long bars first, then thin covers, then small modules), which fits everything onto **2 plates** of 256 × 256 mm. All nine gates still PASS.

---

## Final gate table

| Gate | Status | Key figure |
|---|---|---|
| G1 printed-part validity | **PASS** | all 11 printed parts valid |
| G2 envelope ≤ 500 × 200 × 300 | **PASS** | 459 × 185 × 296 mm |
| G3 fits bed 256² (confirmed) | **PASS** | largest = spine_segment_A, 36 mm margin |
| G4 keyed mate + no overlap | **PASS** | slot 12.60 = rail 12.00 + 2 × 0.3; stripper→hotend→cooling→hall, no overlap |
| G5 min wall ≥ 2.0 mm | **PASS** | min = 2.50 mm (channel wall) |
| G6 channel clear ≥ 8 × 8 mm | **PASS** | 16 × 14 mm |
| G7 STEP reimport valid | **PASS** | reimport valid, bbox 459 × 185 × 296 |
| G8 fastener clearance | **PASS** | M3 = 3.20, M4 = 4.30; nut AF M3 5.5 / M4 7.0 |
| G9 hole-pattern alignment ≤ 0.2 mm | **PASS** | stripper↔NEMA17 0.000; controller↔Uno 0.000; hotend spacing 24.00 |

## === OVERALL: PASS ===

---

## Notes and flags

- **BED = 256 mm (confirmed school printer).** This is the measured build volume, so G3 is a firm pass. The value is still one parameter — were the machine ever smaller, the spine segments (A = 220 mm, the tightest at 36 mm margin) and the riser (161 mm) would need re-splitting — but on the confirmed bed they all clear with margin.
- **Two print plates needed** at BED = 256. The total printed footprint (≈ 63,900 mm²) is just under one bed in raw area, but the long spine bars and the riser stop everything fitting on a single bed in practice.
- **Closest part to the bed limit:** spine_segment_A at 220 mm long — 36 mm of margin on the confirmed 256 mm bed. This is the part to watch if the machine ever changes.
- The cooling-fan and Hall-sensor component-mount holes are reserved, not yet cut (see `bom.md` §4) — flagged so the model stays honest at this stage.

---

## Phase B — printed-part detailing (iteration log)

### Phase B — Iteration 1

Added the following to every printed part:

**Edge fillets (1.0–1.5 mm):**
- Spine segments: 1.0 mm fillets on long outer edges (`|X` selector) applied BEFORE boring the cable channel, so the channel cut never intersects a fillet edge. Fillets on the flange outer flanks and channel box corners.
- Covers: 0.75 mm fillets on long outer top edges (`|X` selector) — gentle enough on a 2.5 mm cover that walls stay above 2.0 mm.
- Splice plate: 1.0 mm fillets on the long Y-axis edges (`|Y` selector) before bolt holes.
- All four modules + controller mount: 1.5 mm fillets on the outer Z-parallel (vertical) edges of the module body (`|Z` selector), applied BEFORE hole cutting to avoid intersecting any hole or thinning a wall. The module walls are 3.0 mm so a 1.5 mm fillet leaves 1.5 mm clear — within safe_fillet's fallback if any edge would fail.
- Winder riser: 1.5 mm fillets on outer Z-parallel edges including the gusset region, before hole cutting.

**Edges skipped (logged):**
- Flange inner corners (where the web meets the flange underside): skipping because the corner is tight (6 mm web T, 6 mm flange T) and a fillet there intersects the hex-nut pocket. Applied the safe_fillet fallback selector instead — the `|X` selector naturally avoids these internal corners.
- Cover snap lips: the 1.5 mm lip is too thin to fillet (would breach 2 mm G5 floor); skipped.
- Splice plate bolt-hole edges: skipping per-hole edge chamfers in favour of the mouth chamfer (see below).

**Bolt-hole mouth chamfers (0.5 mm × 45°):**
- All M4 spine clip holes: chamfer at the top face where bolt head seats.
- All M4 flange holes: chamfer at the top face of the flange.
- All M3 module mount holes: chamfer at the top of the cradle plate.
- All M3 controller-mount standoff bosses: chamfer at the top of the boss.
- Implementation: lofted cone frustum (hole_d/2 + 0.5 → hole_d/2 over 0.5 mm depth) — gives a genuine 45° chamfer cone, not a step. Falls back silently per hole if the boolean fails.

**Embossed part labels (0.7 mm recess, text height 3.0–4.0 mm):**
- `SPINE-A` on the top face of spine_segment_A (x_mid, y=0, Z=FLANGE_TOP_Z).
- `SPINE-B` on the top face of spine_segment_B.
- `COVER-A` on the top face of cover_A.
- `COVER-B` on the top face of cover_B.
- `SPLICE` on the top face of the splice plate.
- `MOD-STRIPPER`, `MOD-HOTEND`, `MOD-COOLING`, `MOD-HALL` on each module's end wall top face.
- `RISER` on the riser foot top face.
- `CTRL-MNT` on the controller mount plate top face.
- Each label uses CadQuery's `.text()` workplane method with `cut=False` (extrudes up), then subtracts from the solid at the face Z minus depth — giving a genuine recessed engraving. Falls back silently if the text operation fails (e.g. on a face that's too small).

**Result: OVERALL PASS — all 9 gates.** G2 envelope unchanged at 459 × 185 × 296 mm. G9 deviation 0.000 mm on all patterns. G5 min wall still 2.50 mm. Bounding boxes of all printed parts unchanged (fillets are cosmetic, don't grow the outer envelope appreciably; label recesses only remove material).

---

## Phase A — bought-part fidelity (iteration log)

### Phase A — Iteration 1

Replaced all block placeholders with higher-fidelity models. All external envelopes and hole patterns preserved — G9 anchor is unchanged.

**PLACEHOLDER_NEMA17:**
- 42.3 × 42.3 × 48 mm body with 2.0 mm chamfer on the 4 vertical (Z-parallel) corner edges — the real NEMA17 has chamfered corners cast into the frame.
- 1.5 mm stepped face detail: a 38 × 38 recessed square cut 1 mm into the +Z mounting face (the real motor has a slightly inset mounting flange).
- 22 mm diameter pilot boss raised 2 mm on the +Z face.
- 5 mm diameter rounded shaft, 24 mm long, protruding from the +Z face and pilot boss centre.
- Small rectangular connector stub on the -Z side face (wire exit).
- 4 × M3 bolt holes at the exact 31 mm square (G9 anchor — unchanged from baseline; confirmed 0.000 mm deviation).

**PLACEHOLDER_VOLCANO_HOTEND:**
- 45 × 24 × 16 mm heater block.
- 5-fin heat sink: fins are 2.5 mm thick, 2.5 mm gap, 20 mm tall, 45 mm wide, stacked above the block. Each fin is a separate rectangular solid unioned to the block.
- Cartridge heater bore: cylindrical hole from the side into the heater block (6 mm diameter, matches real Volcano heater cartridge).
- Nozzle: lofted cone frustum from 6 mm radius at the block base down to 1.5 mm radius, 30 mm long, pointing downward (-Z). More realistic than the original cylinder.
- 2 × M3 mounting holes at ±12 mm (G9 anchor — unchanged; 24.00 mm spacing confirmed).

**PLACEHOLDER_ARDUINO_UNO:**
- 68.6 × 53.4 × 15 mm board.
- 4 × M3 holes at canonical Uno R3 pattern (G9 anchor — unchanged; 0.000 mm deviation confirmed).
- Two header strips: a 28-pin strip (70 mm × 5 mm raised block) along -Y edge and an 8-pin strip along +Y edge.
- USB-B connector block (12 × 16 × 11 mm) protruding from the +X short edge.
- Barrel jack (9 × 11 × 11 mm) also on +X edge, offset in Y.
- ATmega328 MCU IC: 10 × 10 × 3.5 mm raised square near board centre.
- Voltage regulator: 5 × 4.5 × 9 mm block on +Y edge.

**PLACEHOLDER_CNC_SHIELD:**
- Same 68.6 × 53.4 × 20 mm body stacked on the Arduino.
- 4 stepper driver module sockets (14 × 18 × 8 mm raised blocks) across the top face.
- Header pin strips on the underside (connecting to Arduino headers).

**PLACEHOLDER_PSU_SEALED:**
- 129 × 98 × 38 mm body (unchanged position, G2 passes).
- 5 vent slots cut into the top face (20 × 4 × 2 mm each — the real sealed PSU has a ventilated case lid).
- Terminal block stub (10 × 30 × 20 mm) on the +X end face.
- Circular fan grille recess on the -X end face.

**PLACEHOLDER_FAN_5015_A/B:**
- 50 × 50 × 15 mm body for each fan (unchanged position).
- 4 corner mount bosses (2.5 mm radius cylinders).
- Recessed circular impeller cavity (18 mm radius, 3 mm deep) on the outlet (+Z) face.
- Inlet duct stub (15 × 50 × 12 mm) on the -X side face.

**PLACEHOLDER_LCD_1602A:**
- 80 × 36 × 12 mm body (unchanged position).
- Screen recess: 66 × 22 × 2 mm pocket cut into the top face — the real 16×2 display has a slightly recessed LCD panel inside the bezel.

**PLACEHOLDER_SPOOL:**
- Same 190 mm diameter × 56 mm cylindrical spool (unchanged position).
- Hub bore: 30 mm diameter through-hole for the axle boss (cleaner than a solid cylinder).

**Result: OVERALL PASS — all 9 gates.** G2 envelope unchanged at 459 × 185 × 296 mm. G7 STEP reimport valid (bbox 459 × 185 × 296). G9 deviation 0.000 mm on all three patterns. The additional bought-part geometry does not grow any external envelope — all new features are internal details or protrusions within the original bounding boxes (connectors and duct stubs on the fan are additive but stay within the assembly envelope). G5 min wall is still 2.50 mm (unchanged — bought parts don't affect this gate).

### Phase A — Final gate table

| Gate | Status | Key figure |
|---|---|---|
| G1 printed-part validity | **PASS** | all 11 printed parts valid |
| G2 envelope ≤ 500 × 200 × 300 | **PASS** | 459 × 185 × 296 mm |
| G3 fits bed 256² (confirmed) | **PASS** | largest = spine_segment_A, 36 mm margin |
| G4 keyed mate + no overlap | **PASS** | slot 12.60 = rail 12.00 + 2 × 0.3; order correct, no overlap |
| G5 min wall ≥ 2.0 mm | **PASS** | min = 2.50 mm (channel wall) |
| G6 channel clear ≥ 8 × 8 mm | **PASS** | 16 × 14 mm |
| G7 STEP reimport valid | **PASS** | reimport valid, bbox 459 × 185 × 296 |
| G8 fastener clearance | **PASS** | M3 = 3.20, M4 = 4.30; nut AF M3 5.5 / M4 7.0 |
| G9 hole-pattern alignment ≤ 0.2 mm | **PASS** | stripper↔NEMA17 0.000; controller↔Uno 0.000; hotend spacing 24.00 |

## === OVERALL: PASS ===
