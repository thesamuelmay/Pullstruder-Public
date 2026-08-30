# QA Report — Stacked Deck concept CAD

Autonomous export → check → fix loop. Toolchain: CadQuery (OCCT kernel) via `uv`.
Checker: `qa_check.py` (loads the exported STEP files and asserts 6 constraints).

## Iteration log

### Iteration 1 — 3 of 6 checks failing
- **Check 1 (part validity):** PASS — all printed solids valid.
- **Check 2 (envelope ≤ 500×200×300):** **FAIL** — assembly was 439 × **212** × 200 mm. The Y depth blew past the hard 200 mm limit because the heat shield was given a 6 mm overhang on every side (200 + 6 + 6 = 212).
- **Check 3 (bed-fit, BED = 256):** **FAIL** — tray, lid, shield and deck were all 290 mm long in X, over the 256 mm bed. Posts were modelled as one fused body, so their combined bounding box (276 mm) also failed even though each individual post is tiny.
- **Checks 4, 5, 6:** PASS.

**Fixes applied:**
1. Heat-shield overhang split into two parameters: `SHIELD_MARGIN_X = 4` (X has slack under the 500 limit) and `SHIELD_MARGIN_Y = 0` (Y is hard-limited to 200). Removes the depth violation.
2. Added a generic `split_in_x()` sectioning function: any printed part longer than `BED` in X is cut at mid-length into two halves (`_A`, `_B`) with three M4 butt-joint holes across the seam, so the halves bolt back together. Applied to tray, lid, shield and deck.
3. Re-modelled the four corner posts as four separate printed parts (`post_1…post_4`), each bed-checked on its own, instead of one fused body.
4. QA checker updated to discover parts dynamically from the exported `part_*.step` files and to aggregate Z-extents across the `_A`/`_B` sections.

### Iteration 2 — all checks passing
All 31 assertions PASS (13 part-validity + envelope + 13 bed-fit + 2 gap + lid + wall).

## Final PASS table

| # | Constraint | Result | Evidence |
|---|---|---|---|
| 1 | Each printed part solid is valid | **PASS** | 13/13 parts `BRepCheck_Analyzer.IsValid() == True` (tray_A/B, lid_A/B, shield_A/B, deck_A/B, post_1–4, winder_arm) |
| 2 | Assembly bbox ≤ 500 × 200 × 300 mm | **PASS** | actual **437 × 200 × 200 mm** |
| 3 | Each printed part ≤ BED (256×256×256, **confirmed school printer**) | **PASS** | largest section 149 × 200 × 58 mm; all under 256 |
| 4a | Inter-deck air gap ≥ 15 mm | **PASS** | air gap = **22.0 mm** |
| 4b | Tray electronics clear of shield + deck (no bbox collision) | **PASS** | tallest tray item top = 58.0 mm < shield underside = 83.0 mm |
| 5 | Service lid is a separate removable solid (not fused to tray) | **PASS** | lid exports as own part file(s) `lid_A`, `lid_B`, distinct from `tray_A/B` |
| 6 | Min designed wall ≥ 2.0 mm (PLA) | **PASS** | WALL = 3.0, tray wall = 3.0, deck = 5.0, shield = 4.0 |

**Iterations to clean: 2** (1 fixing pass).

## Envelope and compactness (vs original 554 × 220 × 325 mm)

| Measure | Value | vs original |
|---|---|---|
| Full envelope (incl. cantilevered spool) | 437 × 200 × 200 mm | — |
| Full footprint (X × Y) | 87,400 mm² | **−28.3 %** |
| Full bounding volume | 17,480,000 mm³ | **−55.9 %** |
| Chassis-only footprint (the stacked box, no winder/spool) | 298 × 200 = 59,600 mm² | **−51.1 %** |

The two footprint numbers are both reported on purpose — see the honesty note in `design_decisions.md`. The cantilevered spool reaches 143 mm past the chassis end, which roughly doubles the X footprint from the 298 mm chassis box to the 437 mm full envelope. Both are inside the 500 mm limit.

## Caveats carried in the model
- **BED = 256 mm is the confirmed school printer bed** (256 mm cube build volume). Every section sits inside it with margin; the A/B splits keep all plates well under the limit.
- **Placeholder blocks are stand-ins**, not real parts, and are excluded from the printed-part validity and bed-fit checks. They drive only the envelope and the collision check.
- **Z height (200 mm full / 143 mm chassis) is well under the 260 mm concept target** because the placeholder stations sit low on the deck — there is no tall Volcano "column" placeholder reaching full height. Real hotend + mount + reading-clearance will raise this. Treat the Z figures as a floor, not the final height.
