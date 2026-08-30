# QA Report — Pullstruder "Spine + Clip-On Modules" parametric model

**Concept:** spine-modules (recommended)
**Model:** `model.py` (parametric, variables at top)
**Checker:** `qa_check.py` (loads the exported STEP, rebuilds parts in-memory, asserts 6 gates + a STEP-reimport gate)
**Toolchain:** CadQuery 2.7.0 via `uv run --python 3.12 --with cadquery`
**Units:** millimetres (SI)

The QA loop is: **export STEP/STL → run `qa_check.py` → on any FAIL, fix `model.py` → re-export → re-check**, repeated until every gate passes.

---

## What each gate checks

| Gate | Assertion |
|------|-----------|
| **G1** | Every PRINTED part is a valid solid (`BRepCheck_Analyzer.IsValid()`). |
| **G2** | Whole-machine bounding box ≤ **500 × 200 × 300 mm** (printed parts + component placeholders = the packaged machine). |
| **G3** | Every PRINTED part fits the printer bed **BED³ = 256 × 256 × 256 mm** (BED is a parameter; the school printer bed is **confirmed at 256 mm**). Parts may be re-oriented for printing, so sorted part dims are compared against sorted bed dims. |
| **G4** | (a) Every module's key-slot width equals rail width + 2 × clearance (parametric mate proof) **and** the slot is a slide-fit (slot > rail); (b) no two module bodies overlap along the spine X axis. |
| **G5** | Minimum *designed* wall ≥ **2.0 mm** (PLA), audited against every wall parameter. |
| **G6** | Cable-channel clear cross-section ≥ **8 × 8 mm** (to fit the 12 V harness). |
| **G7** | The exported assembly STEP re-imports and the resulting shape is valid (round-trip proof). |

---

## Iteration log

### Iteration 1 — FAIL (4 gates failed)

| Gate | Result | Why it failed |
|------|--------|---------------|
| G1 | PASS | All 10 printed solids valid. |
| **G2** | **FAIL** | Envelope was L=401 / **W=204** / **H=351 mm**. Width and height both over budget: the spool was oriented disc-in-Y-plane (200 mm of width) and was perched at the top of a 200 mm riser (height spike to 351 mm). |
| **G3** | **FAIL** | `spine_segment_A` was **290 mm** long > 256 mm bed (splice plane was at X=200, leaving one half too long). `cover_A` over too. |
| **G4** | **FAIL** | `module_hotend` (X=75, span 47.5–102.5) **overlapped** `module_cooling` (X=120, span 100–140). Stations too close for their footprints. The key-mate sub-check already passed. |
| G5 | PASS | Min wall 2.5 mm. |
| G6 | PASS | Channel clear 16 × 14 mm. |
| **G7** | **FAIL** | (consequence of the assembly not yet settling; resolved once geometry was fixed and re-exported). |

**Fixes applied to `model.py`:**
1. **Re-sectioned the spine** — moved the splice plane from X=200 to **X=130**. Segment A is now 220 mm, segment B 160 mm; both clear the 256 mm bed with margin. (Splice deliberately kept away from the hotend high-load zone at X≈70.)
2. **Re-spaced the stations and trimmed module lengths** so footprints no longer touch: stripper (−22…22), hotend (45…95), cooling (102…138), hall (160…200) — clean gaps between every pair.
3. **Re-oriented the spool** so its axle runs across the machine (along Y): the 56 mm spool *thickness* now sets width and the ~190 mm diameter goes into length (X, generous 500 mm budget) and height. Diameter trimmed to the real ~190 mm working envelope.
4. **Lowered the winder geometry** — riser cut from 200 → 175 mm, and the **NEMA17 puller dropped to a low mount at the controller end** (it pulls the strand along the centreline; only the slack-take-up spool needs height). Spool axle boss re-aligned to the spool centre.

### Iteration 2 — PASS (all gates)

Re-export → re-check: every gate green. Final envelope **465 × 192 × 251 mm**.

**QA loop iteration count: 2** (1 failing, 1 clean).

---

## Final PASS table

```
=== QA RESULTS ===
[PASS] G1 printed-part validity :: all 10 printed solids valid
[PASS] G2 envelope <=500x200x300 :: actual L=465.0 W=192.0 H=251.0
[PASS] G3 fits bed 256^3 (confirmed 256 mm bed) :: every printed part fits
       spine_A=(220x60x74) spine_B=(160x60x74) splice=(60x6x40)
       cover_A=(220x21x4) cover_B=(160x21x4)
       stripper=(44x56x36) hotend=(50x56x67) cooling=(36x56x36)
       hall=(40x56x36) riser=(64x65x181)
[PASS] G4 keyed mate + no module overlap :: all slotW=12.60 vs railW=12.00 (slide-fit);
       order stripper->hotend->cooling->hall, no overlaps
[PASS] G5 min wall >= 2.0 mm :: min designed wall=2.50 mm (channel wall)
[PASS] G6 channel clear >= 8.0x8.0 mm :: clear=16.0x14.0 mm
[PASS] G7 STEP reimport valid :: reimport OK, valid=True, bbox=(465x192x251)
=== OVERALL: PASS ===
```

| Gate | Final | Margin to limit |
|------|-------|-----------------|
| G1 printed-part validity | **PASS** | 10/10 valid |
| G2 envelope ≤ 500×200×300 | **PASS** | L 35 mm / W 8 mm / H 49 mm to spare |
| G3 fits bed 256³ (confirmed) | **PASS** | longest part 220 mm → 36 mm spare |
| G4 keyed mate + no overlap | **PASS** | slot 0.6 mm wider than rail (0.3 mm/side slide-fit); ≥7 mm gaps between modules |
| G5 min wall ≥ 2.0 mm | **PASS** | thinnest designed wall 2.5 mm (+0.5 mm) |
| G6 channel clear ≥ 8×8 mm | **PASS** | 16×14 mm (2× the minimum) |
| G7 STEP reimport valid | **PASS** | round-trips |

---

## Geometry summary (final)

- **Printed parts (10):** spine_segment_A, spine_segment_B, splice_plate, cover_A, cover_B, module_stripper, module_hotend, module_cooling, module_hall_reserved, winder_riser.
- **Placeholder component blocks (9, clearly tagged `PLACEHOLDER_*`):** NEMA17 (+shaft), Volcano hotend (+nozzle), Arduino Uno, CNC Shield, sealed PSU, 5015 fan ×2, 1602A LCD, spool.
- **Packaged envelope:** **465 (L) × 192 (W) × 251 (H) mm** — inside the ≤500×200×300 mm box on all three axes.
- **Solid PLA volume of printed parts:** ≈ 597 cm³ as solid bodies. Real print mass is much lower once hollowed/infilled — treat 597 cm³ as the solid upper bound, not the slicer figure.

> **Note on G3:** PASS is unconditional. The school printer bed is **confirmed at BED = 256 mm**, so every printed part is proven to fit the real bed with margin. `BED` is still a single parameter at the top of `model.py`; if the machine ever changed, lower `BED`, re-run `qa_check.py`, and (if a part fails) add another splice / shorten a module, then re-check — the harness re-sections-and-re-tests automatically against whatever BED is set.

---

## How to re-run

```bash
cd <this cad/ folder>
uv run --python 3.12 --with cadquery python model.py .        # re-export STEP + STL
uv run --python 3.12 --with cadquery python qa_check.py spine_assembly.step   # re-check
```
