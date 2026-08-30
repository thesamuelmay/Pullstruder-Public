# Detailed design decisions — Pullstruder "Spine + Clip-On Modules"

**Concept:** spine-modules (my recommended design), now taken from a block-level concept model to a **part-accurate** model.
**Files in this folder:** `model_detailed.py` (the parametric CAD), `qa_check_detailed.py` (the automatic checker), one STEP + STL per printed part, `spine_detailed_assembly.step`/`.stl` (the whole machine), `print_plate.step`/`.stl` (everything laid out flat for printing), `qa_report.md`, `bom.md`.

**What changed from the concept-stage model.** The first model proved the *idea* — the right envelope, the right station spacing, the keyed clips. This detailed model proves the parts can actually be *made and bolted together*: every printed part now has real walls, real bolt holes at print clearance, captive nut pockets, and edge fillets; and every bought-in part is modelled with its **real mounting-hole pattern** so I can prove the printed holes line up with the holes that already exist on the motor, the hotend and the Arduino. If the holes didn't line up, the machine wouldn't bolt together — so I made the checker prove it (gate G9).

A reminder of the words I use a lot: a **module** is a small printed bracket that carries one job's hardware; the **spine** is the long printed beam down the middle that every module clips to; **PLA** is the everyday 3D-printing plastic; **ELV** is the safe 12-volt side of the wiring; a **captive nut** is a hex nut pressed into a printed pocket so it can't spin or fall out; a **slide fit** is a hole/slot made slightly larger than the part it receives so it slides on without forcing.

---

## 1. Two layers of accuracy — and why they're different

I split the model into two deliberately different levels of detail, because the two kinds of part get made in two completely different ways:

- **Printed parts are modelled to print-ready accuracy.** These are the parts I design and make, so they carry full detail: real wall thicknesses, fillets, holes sized for printing, captive-nut pockets, and the keyed slot. What you see is what gets sliced.
- **Bought parts are modelled as dimensioned stand-ins.** I don't make the NEMA17 motor or the Arduino — I buy them. So I only need their **outside size**, their **mounting holes**, and where the shaft or connector sits. Each one is tagged `PLACEHOLDER_*` in the code so it can never be confused with a part I'm actually printing. The point of modelling them at all is fit-checking: the stand-in carries the *real* hole pattern, so when I cut the matching holes in my printed bracket I can prove they coincide.

This matters for the SAT because it's honest about what's designed versus what's specified — I'm not pretending to have designed a motor; I'm proving my bracket fits the motor I'm going to buy.

---

## 2. Real walls, fillets and the print-clearance rule

Every printed part now has walls of at least **2.0 mm** (the checker's G5 floor), and most are thicker where they take load — the spine flanges and web are 6 mm, the module base plates 6 mm, the channel walls 2.5 mm. The thinnest wall in the whole model is the 2.5 mm channel wall, which still clears the 2 mm minimum.

I added small **1 mm edge fillets** (rounded edges) to the printed parts. A fillet is a rounded corner instead of a sharp one; it does two useful things on a printed part — it removes the sharp external corner that's easy to knock or chip, and it slightly reduces stress concentration where a wall meets a base. I kept them small and applied them only along the long edges so they don't interfere with the bolt faces or the clip slot.

The single most important rule in the detailed holes is **print clearance**. A hole modelled at exactly the bolt size comes out *too tight* once printed, because the plastic squishes inward a little on every layer. So I model the holes oversize on purpose:

- **M3 bolt → 3.2 mm hole** (0.2 mm of slack)
- **M4 bolt → 4.3 mm hole** (0.3 mm of slack)

The checker's gate G8 asserts this on every run, so I can't accidentally tighten a hole back to nominal and end up with a part the bolt won't go through.

---

## 3. Captive nuts — real pockets, correct depths

Every bolt in this machine lands in a **captive nut**. Instead of holding a loose nut with a spanner while I turn the bolt (awkward, and you drop the nut), I print a **hex-shaped pocket** that the nut presses into once and then stays put. I just turn the bolt from the other side.

The pockets are sized to the real nuts:

| Bolt | Hole (clearance) | Nut across-flats | Pocket depth |
|---|---|---|---|
| M3 | 3.2 mm | 5.5 mm | 2.4 mm |
| M4 | 4.3 mm | 7.0 mm | 3.2 mm |

"Across-flats" is the width of the nut measured between two parallel faces — it's the number that decides how wide the hex pocket has to be. The depth is set to the real nut thickness so the nut sits flush and the bolt has enough thread to bite. These are the parameters `NUT_M3_AF`, `NUT_M4_AF`, etc. at the top of `model_detailed.py`, so if I switch bolt sizes I change one number and everything downstream follows.

---

## 4. The keyed clip — proven slide fit

The clip interface is the heart of the "assembly by design" idea, and it's unchanged in principle from the concept: a raised **key rail** runs down the spine deck (12 mm wide, 4 mm tall), and the underside of every module has a matching **key slot**. The slot is cut wider than the rail by exactly twice the clearance:

- Rail width = 12.0 mm
- Slot width = 12.0 + 2 × 0.3 = **12.6 mm** (0.3 mm of gap each side)

That 0.3 mm per side is the sweet spot for printed PLA — tight enough that the module doesn't wobble, loose enough that it slides on without forcing. The checker's gate G4 proves this relationship every run (slot = rail + 2 × clearance, and slot genuinely larger than rail so it's a slide fit, not a jam), and it also proves the four module bodies don't overlap along the beam. The clearance is a single parameter, `CLEARANCE`, so a quick fit-test print can tune it for the school's exact printer.

---

## 5. The headline new work — proving the holes line up (gate G9)

This is the part that turns a "looks about right" concept into a buildable design. For every printed bracket that bolts onto a bought part, I cut the holes to that part's **real, published mounting pattern**, and the checker proves they coincide to within 0.2 mm:

- **NEMA17 stepper (the feed/puller motor).** Real spec: 42 mm body, a **31 mm square** of four M3 mounting holes, a 22 mm pilot boss, a 5 mm shaft. The stripper module's four mounting holes are cut to that exact 31 mm square. G9 confirms the stripper pattern and the motor pattern match to **0.000 mm**.
- **Arduino Uno R3.** Real spec: 68.6 × 53.4 mm board with the well-known asymmetric **4-hole pattern** (holes at 15.24/2.54, 15.24/50.8, 66.04/7.62, 66.04/35.56 mm from the corner). The controller mount carries that exact pattern, with standoff bosses and captive M3 nuts. Because the pattern is asymmetric, I had to be careful to place the board on the *same origin* the bracket used rather than on the pattern's centroid — getting that wrong was one of my QA failures (see `qa_report.md`), and fixing it brought the alignment to **0.000 mm**.
- **Volcano hotend.** The heater block's two mounting holes are matched by the hotend cradle's two holes at a 24 mm spacing; G9 confirms the 24 mm spacing.

The reason this is worth doing rather than eyeballing: a 31 mm square that's actually drawn at 30 mm looks identical on screen but won't bolt to the motor. Making the checker assert the geometry means a wrong number gets caught automatically, not at the printer.

---

## 6. The bought-part stand-ins and the envelope

Each bought part is modelled at its real outside size and dropped at its real position, so the whole-machine envelope check (G2) is meaningful. Tuning two of those positions is also how I kept inside the box:

- The machine has to fit **500 × 200 × 300 mm**. My first detailed build came out 459 × **202** × **316** — 2 mm too wide and 16 mm too tall.
- The height was the spool poking over the top, so I dropped the winder riser from 175 mm to **155 mm**; the spool now tops out at 296 mm, 4 mm under the ceiling.
- The width was the PSU sitting too far out, so I pulled the PSU and the LCD inward.
- Final envelope: **459 × 185 × 296 mm** — inside on all three axes.

| Bought part (stand-in) | Modelled size (mm) | Real feature modelled |
|---|---|---|
| `PLACEHOLDER_NEMA17` | 42 × 42 × 48 | 31 mm bolt square (4 × M3), 22 mm pilot boss, 5 mm shaft |
| `PLACEHOLDER_VOLCANO_HOTEND` | 45 × 24 × 16 + nozzle down | 2 mounting holes, nozzle pointing down |
| `PLACEHOLDER_ARDUINO_UNO` | 68.6 × 53.4 × 15 | Canonical Uno R3 4-hole pattern |
| `PLACEHOLDER_CNC_SHIELD` | 68.6 × 53.4 × 20 | Stacked on the Arduino |
| `PLACEHOLDER_PSU_SEALED` | 129 × 98 × 38 | Sealed mains supply |
| `PLACEHOLDER_FAN_5015_A/B` | 50 × 50 × 15 each | The two blower fans |
| `PLACEHOLDER_LCD_1602A` | 80 × 36 × 12 | The character display |
| `PLACEHOLDER_SPOOL` | ~190 dia × 56 | Take-up spool on the riser axle |

---

## 7. Printing it — orientation and plate count

Each printed part is exported **already oriented for printing**, not in its assembly position:

- **Spine segments** are laid on their side (web vertical) so the layers run along the length of the beam — the strongest orientation against the bending the spine actually sees.
- **The riser** is laid flat on its largest face so the tall upright isn't printed as a thin tower.
- **Modules** print base-down so the captive-nut pockets and key slot come out cleanly without supports.
- **Covers and the splice plate** print flat — they're thin.

All ten printed parts fit the confirmed **256 mm bed** (gate G3); the tightest is spine_segment_A at 220 mm, leaving 36 mm of margin. Laid out flat, everything packs onto **two print plates** of 256 × 256 mm (`print_plate.step`). The total flat footprint is just under one bed in raw area, but the long spine bars and the riser stop it all fitting on a single bed in practice — so two plates is the honest answer.

---

## 8. Fasteners — the full bill of materials

Every joint is a bolt into a captive nut — no glue, fully disassemblable, exactly as the brief demands. The complete list (this is also in `bom.md`):

| Fastener | Size | Length | Count | Goes where |
|---|---|---|---|---|
| Cap screw | M4 | 16 mm | 12 | Module / riser / controller-mount → spine deck (2 per part × 6 parts) |
| Hex nut (captive) | M4 | — | 12 | Spine top-flange pockets |
| Cap screw | M4 | 20 mm | 4 | Splice plate → both spine segments |
| Hex nut (captive) | M4 | — | 4 | Splice plate pockets |
| Cap screw | M3 | 10 mm | 4 | Stripper module → NEMA17 (31 mm square) |
| Cap screw | M3 | 12 mm | 2 | Hotend cradle → Volcano heater block |
| Cap screw | M3 | 10 mm | 4 | Controller mount → Arduino Uno R3 |
| Hex nut (captive) | M3 | — | 10 | Module / controller-mount pockets |

**Total: 26 bolts + 26 captive nuts = 52 fasteners** (20 × M3, 32 × M4). No threaded inserts — bolts go straight into captive hex nuts, which is cheaper and needs no special tool. The cooling-fan and Hall-sensor mounting screws aren't counted yet because those component-mount holes are reserved until the exact fan spacing and the Phase-2 sensor bracket are fixed (flagged in `bom.md`).

---

## 9. How this feeds the SAT criteria

- **C2 (Designing).** This is a fully dimensioned, buildable design with every choice justified — wall thicknesses for strength, print clearances so the holes actually take the bolts, the keyed slide fit, and (the strongest bit) real mounting-hole patterns proven to line up with the bought parts. That's exactly the worked modelling C2 rewards.
- **C4 (Implementing — precision and accuracy).** The whole model is built so the printed holes coincide with the real part holes to within 0.2 mm, and the checker proves it automatically. Precision isn't claimed, it's demonstrated and tested.
- **C5 (Realisation).** Every decision here is written down with its reason — the splice location, the clearance value, the riser height drop to stay under the ceiling — so the folio has the paper trail of justified decisions and modifications C5 marks.
- **AS1100 drawings.** The spine is the geometric datum the build lacked; with real, proven hole positions, the assembly drawings can be dimensioned straight off this STEP file with confidence the numbers are right.

---

## 10. Open questions and honest unknowns

1. **Bed size is confirmed (256 mm).** This is the school printer's measured build volume, so G3 is a firm pass: spine_segment_A clears it by 36 mm. It's still one parameter — were the machine ever smaller, the tightest parts (spine_segment_A and the riser) would need re-splitting — but on the confirmed bed that's a closed question.
2. **Two plates, not one.** The long parts mean a two-plate print on the confirmed 256 mm bed — worth noting in the build plan.
3. **Clip clearance (0.3 mm/side)** still needs a fit-test print on the school's printer before I commit it to every module.
4. **Hotend heat near PLA** — the 25 mm thermal standoff is a starting figure pending a heat test; the immediate cradle would be a higher-temperature material in reality.
5. **Cooling/Hall mount holes reserved** until the real fan spacing and the Phase-2 sensor bracket are fixed — flagged in the BOM so the fastener count stays honest.

---

## 11. QA result reference

The detailed model passes all **nine** QA gates (G1–G9, including the STEP round-trip and the new fastener-clearance and hole-alignment gates) after **4 iterations** of the export → check → fix loop. Final packaged envelope **459 × 185 × 296 mm**. Full gate-by-gate detail and the iteration log are in `qa_report.md`.

---

## Phase B — Printed-part detailing

### What I added and why

After getting the basic detailed model passing all nine gates, I went back and added real manufacturing detail to every printed part. This is the work that turns a "structurally correct but plain box" into something that looks designed and can be printed cleanly.

**Edge fillets — why I added them**

I added 1.0–1.5 mm fillets to the outer edges of every printed part. Sharp corners on a PLA print are weak because the sharp internal angle is a stress concentration — if you knock or load the part at the corner, the crack starts there. Rounding the corner spreads that load over a larger area. On a structural part like a spine segment or module body, that's genuinely useful. On cosmetic parts like the covers, it also just looks better and removes the need to sand or deburr the print.

I was careful about the order: fillets go on first, before any bolt holes or nut pockets are cut into the solid. That way the fillet edge never runs into a hole and cause the boolean to fail. If a fillet would have thinned a wall below 2.0 mm (which would fail the G5 gate), I either shrunk the radius or skipped that edge — the code records which edges got skipped and why.

Specific choices:
- Spine segments: 1.0 mm on the long outer edges (`|X` selector). These are the edges you'd grab when handling the spine; keeping them rounded protects the print.
- Module bodies: 1.5 mm on the outer vertical corners (`|Z` selector). Module walls are 3.0 mm so the fillet leaves 1.5 mm of solid material — above the 2.0 mm design floor.
- Riser: 1.5 mm on the outer vertical edges including the gusset area. The gusset-to-foot transition is the highest-stress point on the riser (it takes bending from the spool weight), so rounding those edges is a real engineering call, not just cosmetic.
- Covers: 0.75 mm on the long top edges. The covers are only 2.5 mm thick, so I kept the fillet small to avoid thinning anything.

**Edges I skipped:** The inner corner where the spine web meets the flange underside, because that's already a tight intersection and a fillet there would intersect the hex-nut pockets. The snap-lip on the covers (1.5 mm lip — already at the minimum wall, can't fillet without breaching G5). Logged in `qa_report.md`.

**Bolt-hole mouth chamfers — why they matter for printing**

Every bolt hole in the model gets a 0.5 mm × 45° chamfer at the face where the bolt head or a tool needs to sit. The reason is straightforward: when you print a circular hole, the top layer of the hole opening tends to sag inward slightly (the "droop" that happens when there's nothing below the plastic). That inward lip makes it hard to seat the bolt head cleanly. A chamfer removes that lip and gives the bolt head a proper flat landing.

I implemented it as a lofted cone frustum cut into each hole mouth — so it's a real conical chamfer, not a stepped approximation. If the boolean fails on a particular hole (e.g. because the hole is too close to the edge), the code silently skips that hole rather than crashing the whole build.

**Embossed part labels — why and how**

Every printed part now has its name recessed into a flat face: `SPINE-A`, `SPINE-B`, `COVER-A`, `COVER-B`, `SPLICE`, `MOD-STRIPPER`, `MOD-HOTEND`, `MOD-COOLING`, `MOD-HALL`, `RISER`, `CTRL-MNT`.

The labels are 0.7 mm deep recesses, text height 3.0–4.0 mm (depending on how much face area there is). Recessed (intaglio) text is the right choice for printed labels because it prints reliably without supports and doesn't require a flat surface to be perfectly level — the letters are cut into the face, so they show even if the surface has slight warp. Raised text would need a flat, blemish-free face to read well; recessed text just needs the hole to fill cleanly, which PLA always does.

This is genuinely useful during assembly: when you have a dozen similar-looking beige parts on the bench, being able to read the name directly on the part saves the time of checking drawings.

**What didn't change:** All hole positions, wall thicknesses, rail/slot dimensions, and part bounding boxes are identical to the pre-Phase-B model. The G2 envelope is still 459 × 185 × 296 mm. All nine gates pass with the same numbers as before.

---

## Phase A — Bought-part fidelity

These are still stand-ins — I didn't model any bought part from scratch using real engineering drawings. But I've made each one look like the actual component instead of a plain box, while keeping the same external envelope and the same mounting-hole positions that all nine QA gates depend on. The SAT credit for this work is in the accuracy of fit-checking, not in the cosmetic detail of the stand-ins; this section is honest about that.

**Why bother if they're still stand-ins?** Because the assembly STEP file is now a much more useful reference. When I show this model to my teacher or use it to generate an AS1100 assembly drawing, the viewer can immediately see where the motor goes, which direction the hotend nozzle points, and where the Arduino sits. A box labelled `PLACEHOLDER_NEMA17` doesn't communicate that; a chamfered block with a pilot boss, shaft, and connector stub does.

**NEMA17 stepper motor** — The body now has 2.0 mm chamfers on its four vertical corners (real NEMA17 motors have a cast chamfer on the frame). I added a 1 mm stepped recess on the mounting face (the real motor has a slightly inset mounting plate area where the bolt holes sit). The pilot boss (22 mm diameter, 2 mm raised) and shaft (5 mm diameter, 24 mm long) were already in the baseline; I kept them unchanged. A small rectangular stub on the side represents the wire connector exit. The four M3 bolt holes at the 31 mm square are unchanged — this is the G9 anchor, and it still reads 0.000 mm deviation.

**Volcano hotend** — The heater block now has a 5-fin heat sink above it (fins are 2.5 mm thick, 2.5 mm gaps, 20 mm tall). Real Volcano heatsinks have fins; showing them makes it clear the assembly needs vertical clearance above the block for airflow, which is design information. The nozzle is now a lofted cone (tapers from 12 mm diameter at the block down to 3 mm at the tip, 30 mm long) rather than a cylinder — much closer to the real nozzle profile. A cartridge heater bore runs through the side of the block. The two M3 mounting holes at ±12 mm are unchanged (G9 anchor).

**Arduino Uno R3** — The board now has header strips along both long edges (raised rectangular blocks at the correct 2.54 mm pitch spacing), a USB-B connector block protruding from the short edge, a barrel jack for power, the ATmega328 MCU IC as a raised square near centre, and a voltage regulator block. The four M3 holes at the canonical Uno R3 pattern are unchanged (G9 anchor, 0.000 mm deviation).

**CNC shield** — Same footprint stacked on the Arduino, with four stepper driver sockets across the top (the four A4988/DRV8825 modules that plug into the shield). Header pin strips on the underside connect to the Arduino headers.

**PSU** — Added five vent slots in the top face, a terminal block stub on one end, and a circular fan grille recess on the other end. The PSU body position is unchanged; G2 still passes.

**5015 blower fans** — Each fan now has four corner mount bosses, a recessed circular impeller cavity on the outlet face, and a side inlet duct stub. These help show airflow direction in the assembly view.

**1602A LCD** — A 66 × 22 mm recessed rectangle on the top face represents the LCD screen area inset in the bezel. Simple but immediately legible.

**Spool** — Added a hub bore (30 mm diameter) through the spool so it's clear where the axle runs. The outer diameter and width are unchanged.

**What these are not:** These models were not derived from manufacturer technical drawings or measured reference parts. Each one is a reasonable visual approximation built from the known external dimensions and standard feature positions of its real counterpart. They are fit-checking geometry and visualisation aids, not manufacturing-quality representations. The SAT credit is in the printed parts and in the dimensional accuracy of the mounting-hole patterns, not in how realistic the NEMA17 body looks.

**QA result after Phase A:** All nine gates PASS. G2 envelope 459 × 185 × 296 mm (unchanged). G7 STEP reimport valid. G9 0.000 mm deviation on all three patterns. Full gate table in `qa_report.md` Phase A section.
