# QA Report — L-Fold Pullstruder CAD

**Model:** `model.py` (parametric CadQuery)
**Checker:** `qa_check.py` (rebuilds the model in-process, asserts 5 rules)
**Exports:** `lfold_assembly.step`, `lfold_assembly.stl`
**Toolchain:** CadQuery 2.7.0 via `uv run --python 3.12 --with cadquery`

The QA loop runs: **export → qa_check → fix → re-export → re-check**, repeating until every rule passes. Below is the log of each iteration.

---

## The 5 QA rules

1. **Validity** — every printed part passes `BRepCheck_Analyzer.IsValid()`.
2. **Envelope** — whole packaged assembly bounding box ≤ **500 × 200 × 300 mm** (L×W×H = X×Y×Z).
3. **Bed fit** — every printed part fits the print bed. The bed is **CONFIRMED** as the school printer's 256 mm cube build volume, set as `BED = 256` mm with `BED_MARGIN = 6` mm skirt room → usable **244 mm** cube.
4. **No interference** — no genuine solid-on-solid overlap between printed structural parts. Bbox overlap is the first screen; any hit is confirmed by a real boolean-intersection volume (> 1 mm³ = genuine). Designed mating pairs (stacked back-plane segments at their splice, foot↔chassis, gussets↔chassis/back-plane, raceway↔back-plane, chassis butt-splice) are excluded — they are *supposed* to touch.
5. **Min wall** — no designed wall < **2.0 mm** (PLA printability). Asserted through the parametric wall variables, since several walls can't be measured directly off the solid.

---

## Iteration log

### Iteration 1 — first export
| Rule | Result | Detail |
|---|---|---|
| 1 Validity | PASS | 9 printed parts valid |
| 2 Envelope | **FAIL** | actual L=609 W=441 H=322 |
| 3 Bed fit | PASS | all fit |
| 4 Interference | PASS | none |
| 5 Min wall | PASS | min wall 3.0 mm |

**Diagnosis:** the back-plane, cable raceway, LCD, Arduino, CNC shield and spool were built on `XZ`/`YZ` workplanes with an `offset`, which put their face-normals along the **wrong axis** — the back-plane landed at Y ≈ −300 instead of standing across the runway at X ≈ 300. That blew Y out to 441 mm and scattered parts.

**Fix:** rebuilt every back-plane-related part as `XY` boxes positioned by explicit `.translate()`, so the panel is thin in X, wide in Y, tall in Z (unambiguous). Re-oriented the spool (axis along Y), raceway (projects in +X), and the back-plane-mounted electronics/LCD.

### Iteration 2 — after orientation fix
| Rule | Result | Detail |
|---|---|---|
| 2 Envelope | **FAIL** | actual L=735 W=180 H=270 |

**Diagnosis:** Y (180) and H (270) now correct, but L = 735 mm. The 200 mm-diameter spool was flung downstream past the back-plane (X out to 512), and the chassis didn't reach the back-plane root (floating gap).

**Fix:** three parametric moves — (a) slid the NEMA17 puller further inward (`X_PULLER` −200 → −130) to close the dead gap, (b) pulled the chassis upstream end in (`CH_X0` −210 → −160), (c) stacked the spool **above** the runway (centre `SPOOL_CX = 175`, high in Z) so its 200 mm disc overlaps the thermal path in X-projection instead of projecting past the machine — exactly the "fold up and stack" intent.

### Iteration 3 — after layout compaction
| Rule | Result | Detail |
|---|---|---|
| 2 Envelope | PASS | L=495 W=180 H=270 |
| 4 Interference | **FAIL** | chassis_seg2 ↔ backplane_seg1, real overlap 17,568 mm³ |

**Diagnosis:** the back-plane panel rose from Z=0 and the chassis extended under it, so the panel passed *through* the chassis slab — a genuine clash, not a designed mate.

**Fix:** ended the chassis flush with the back-plane front face (`CH_X1 = 294`, = `BP_X`) so the panel stands at the chassis edge rather than inside it. The bolted joint is the **foot flange** sitting on the chassis top (an allowed mate), not the panel ploughing through the slab.

### Iteration 4 (final) — all pass
```
[PASS] 1. all printed parts valid                      | 9 parts checked
[PASS] 2. envelope <= 500x200x300                      | actual L=495.0 W=180.0 H=270.0
[PASS] 3. printed parts fit bed (BED=256, usable=244)  | all 9 fit
[PASS] 4. no printed part interference                 | no genuine overlaps
[PASS] 5. min designed wall >= 2.0 mm                  | min wall var = 3.0

OVERALL: ALL PASS
```
The exported STEP was independently re-imported (`cq.importers.importStep`) and confirmed: 18 solids, bbox 495 × 180 × 270 mm — matches the in-process build.

---

## Final PASS table

| # | Check | Result | Measured / asserted value |
|---|---|---|---|
| 1 | Validity (each printed part) | **PASS** | 9/9 solids `IsValid()` = True |
| 2 | Envelope ≤ 500×200×300 | **PASS** | **495 (L) × 180 (W) × 270 (H) mm** |
| 3 | Per-part bed fit (BED=256, usable 244) | **PASS** | largest printed part within 244 mm cube |
| 4 | No printed-part interference | **PASS** | 0 genuine overlaps (mates excluded) |
| 5 | Min designed wall ≥ 2.0 mm | **PASS** | min wall variable = **3.0 mm** |

**QA iterations to clean: 4** (3 fixes).

**Final packaged envelope: 495 × 180 × 270 mm** — inside the ≤ 500 × 200 × 300 mm goal with 5 mm (L), 20 mm (W) and 30 mm (H) of margin.

---

## Open flags

- **BED = 256 mm is the confirmed school printer** (a 256 mm cube build volume). All "fits the bed" results are firm against this known constraint, not conditional. The model stays parametric — if the bed value ever changed, the chassis and back-plane segment counts (`BP_SEGMENTS`, the auto-sectioner in `chassis_sections`) adjust automatically.
- **Interference check is bbox-screened then volume-confirmed.** It catches solid overlaps reliably but does not check *clearance* (e.g. a 1 mm air gap for assembly). Clearance review is a manual follow-up.
- **Placeholders are envelopes, not parts.** Component placeholder blocks are excluded from the printed-part validity and bed checks by design — they only stake out the packaged envelope.
