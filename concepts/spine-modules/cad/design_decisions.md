# Design decisions — Pullstruder "Spine + Clip-On Modules"

**Concept:** spine-modules (my recommended design)
**Files in this folder:** `model.py` (the parametric CAD), `qa_check.py` (the automatic checker), `spine_assembly.step` and `spine_assembly.stl` (the exported 3D model), `qa_report.md` (the QA results).
**What this is:** the concept-stage CAD for the recommended Pullstruder design — a PET-bottle filament recycler that pulls a strip of plastic bottle, melts it through a hotend, and winds the result onto a spool as 3D-printer filament. This document explains *why* each printed part is shaped the way it is, and records the decisions so they become SAT evidence later.

A note on words I use a lot: a **module** is a small printed bracket that carries one job's hardware (the hotend, the fans, etc.). The **spine** is the single long printed beam that runs down the middle of the machine; every module clips onto it. **PLA** is the everyday 3D-printing plastic the custom parts are printed from. **ELV** means "extra-low voltage" — the safe 12-volt side of the wiring, as opposed to dangerous mains power.

---

## 1. The spine cross-section — what shape, what size, and why

**Decision: an I-section beam, 380 mm long, 60 mm wide flanges, 70 mm tall overall, with a hollow cable channel slung underneath.**

The spine is the backbone of the whole machine, so it has to do three jobs at once: be stiff so it doesn't sag, give every module a flat face to line up against, and hide the wiring. I picked an **I-section** (the cross-section looks like a capital I — a flat top, a flat bottom, and a thin wall joining them) because that shape gives the most bending stiffness for the least plastic. Putting material at the top and bottom and only a thin **web** (the vertical wall in the middle) between them is exactly how steel I-beams in buildings work, and it works for the same reason: bending load is carried mostly at the top and bottom surfaces, so that's where you want the material.

The dimensions I chose:

| Feature | Size | Why |
|---|---|---|
| Overall length | 380 mm | The footprint target from the concept; it's the longest single thing in the machine. |
| Flange width (the top deck) | 60 mm | Wide enough to give each module a generous flat seat and room for bolt pads on both sides of the centre rail. |
| Flange thickness | 6 mm | Thick enough to swallow a captive nut (see §6) and not flex when a module bolts down. |
| Web thickness | 6 mm | The middle wall. 6 mm is well over the 2 mm minimum and resists twisting. |
| Section height | 70 mm | Tall enough to fit the cable channel underneath the web. |

The top flange is the **mounting deck** — it has a repeating pattern of bolt holes and captive-nut pockets at each station position. The hollow underneath is the cable channel. So one printed part is the datum, the mount, and the wiring duct all in one.

**Honest unknown:** I can't *prove* the I-section is stiff enough until I print a length and hang a representative load off it (a deflection test). The cross-section is sized for stiffness on paper; the test confirms it. This is flagged in the open questions.

---

## 2. The bolted splice joint — why the spine is in two pieces

**Decision: print the spine as two segments and bolt them together with a splice plate at X = 130 mm.**

The spine is 380 mm long. School 3D printers usually have a bed somewhere around 220–256 mm, so a 380 mm part almost certainly won't fit in one print. Rather than guess, I designed the spine to print in **two segments** joined by a **splice** — a short plate that bridges the joint and bolts through both segments' webs with four M4 bolts.

Two decisions inside that decision:
- **Where to split.** I put the splice at **X = 130 mm**, not in the middle. That keeps both halves comfortably under the bed (segment A = 220 mm, segment B = 160 mm — see the QA report) *and* keeps the joint away from the hotend at X ≈ 70 mm, which is the hottest, most loaded spot on the beam. You don't want a join right where the stress and heat are highest.
- **Bolted, not glued.** The constraint says everything must come apart without adhesive, and a bolted splice obeys that. It also means if I crack one segment I reprint only that segment, not the whole beam.

Even split in two, the spine is still **one logical chassis** — the two segments bolt into a single rigid beam that the whole machine registers to. So it still satisfies the "single chassis" constraint.

---

## 3. The keyed clip interface — how alignment happens by itself

**Decision: a raised key rail on the spine deck + a matching key slot on each module, with a 0.3 mm-per-side slide-fit clearance.**

This is the cleverest part of the concept and the thing that makes assembly fast. Down the centre of the spine deck runs a **key rail** — a raised strip 12 mm wide and 4 mm tall. The underside of every module has a **key slot** cut into it that is exactly the rail width plus a small gap, so the module can only drop onto the rail one way and then slides along it to a hard stop at the right X position.

That means **alignment is built into the parts**. There's no measuring, no jig, no "is it square?" during assembly — the module physically cannot sit crooked or in the wrong orientation, because the slot only fits the rail one way. This is what the SAT calls "design for assembly", and it's a real, photographable design choice.

The **clearance** matters and I made it a parameter:
- Rail width = 12.0 mm.
- Slot width = rail + 2 × 0.3 = **12.6 mm**.

So the slot is 0.6 mm wider than the rail — 0.3 mm of gap on each side. That's the sweet spot for printed PLA: tight enough that the module doesn't wobble, loose enough that it actually slides on without forcing. The QA checker proves this mate every run: it asserts that every module's slot width equals rail + 2 × clearance and that the slot is genuinely larger than the rail (a slide-fit, not an interference jam).

**Honest unknown:** the *right* clearance for the school's specific printer needs a quick fit-test print before I commit — 0.3 mm is my starting estimate. Easy to change: it's one variable (`CLEARANCE`) at the top of `model.py`.

---

## 4. The cable channel and the single terminal block

**Decision: a hollow raceway under the web, 16 × 14 mm clear inside, with a snap-on cover, feeding one terminal block at the controller end.**

The biggest documented weakness of the current build is the wiring: there's **no terminal block**, and the branches are hand-soldered — messy to build, hard to fix, and impossible to take apart cleanly. The spine fixes this by running a **cable channel** (a wiring tunnel) the full length underneath the web. Each module drops its 12 V leads straight down through a slot in the deck into the channel, the leads run along to **one terminal block** near the Arduino, and a **snap-on cover** tidies them away.

**Sizing the channel.** I made the clear inside **16 mm wide × 14 mm tall**. The concept set a floor of 8 × 8 mm to fit the harness; I went to 16 × 14 — double the minimum — for two reasons: a 12 V harness with several leads needs room to bundle without crushing, and the heavier leads (the PSU feed and the heater wire) run warm, so giving them air space stops heat building up in a tight duct. The QA checker asserts the clear section is at least 8 × 8 mm every run; 16 × 14 passes with margin.

**Why one terminal block is the right move — with precedent.** This is the *same idea* that already paid off once on this project: the 1602A LCD screen used to need **12 wires**, and switching it to **I2C** (a wiring standard that talks over just two signal lines) cut that to **4 wires** — a two-thirds reduction. That win proved that consolidating wiring is worth doing. The terminal block extends the same logic to the *whole* 12 V harness: instead of scattered solder blobs, every branch lands on one labelled screw terminal. That makes the machine easier to build, far easier to fault-find, and properly disassemblable.

**Safety boundary, stated plainly:** the dangerous mains power never leaves the **sealed, certified PSU**. Only the safe 12 V ELV side enters the raceway. The channel carries ELV only. That keeps the safety line unambiguous — I'm only ever wiring the low-voltage side.

**On "visible process":** the assessor needs to *watch the plastic travel* through the machine — that's the process. The wiring was never the thing to watch. So covering the wires in a raceway while leaving the filament path along the top of the spine open and watchable keeps the "visible process" requirement satisfied; it tidies the boring bit and shows off the interesting bit.

---

## 5. The winder riser — folding the machine up instead of out

**Decision: a short vertical riser at the controller end carries the spool up high; the NEMA17 puller sits low.**

The old layout flung the motor and spool way out along the X axis, leaving a big dead gap. The **L-fold** deletes that: instead of running the winder out horizontally, it **folds it up** onto a vertical **riser** (175 mm tall) at the controller end. The spool sits up on an axle near the top, and the **NEMA17 stepper motor** — the part that actually pulls the filament strand along the centreline — mounts **low**, near the spine, where the strand is. Only the slack-take-up spool needs height; the puller doesn't, so I dropped it down. That keeps the tall element deliberate (the riser, by design) rather than an accidental height spike, and it kept the whole machine under the 300 mm height limit (final height 251 mm).

The riser is braced with a **gusset** (a triangular web between the upright and the foot) so it doesn't flex under the spool's weight and the pull of the motor.

---

## 6. Bolts and captive nuts — how the modules hold down

**Decision: M4 bolts through every module into captive hex-nut pockets in the spine flange; M3/M4 holes parameterised.**

Every module bolts to the spine with **M4 bolts** (4 mm machine screws). The clever bit is the **captive nut**: instead of trying to hold a loose nut with a spanner while you tighten a bolt (awkward, and you drop the nut), I designed **hex-shaped pockets** into the underside of the spine flange. The nut presses into the pocket once and stays there — "captive" — so you just turn the bolt from above. No loose fasteners to drop or lose, which is exactly the kind of fiddly loose part the concept set out to eliminate.

The hole and pocket sizes are all parameters (M4 clearance hole 4.3 mm, nut pocket 7.0 mm across the flats, 3.2 mm deep), so if I change bolt size I change one number.

---

## 7. Per-constraint compliance checklist

| Constraint | Status | Evidence |
|---|---|---|
| **Footprint ≤ 500 × 200 × 300 mm** | **PASS** | QA G2: actual **465 × 192 × 251 mm** — inside on all three axes (35/8/49 mm to spare). |
| **Single chassis (non-negotiable)** | **PASS** | The spine *is* the chassis; everything registers to it. Split into two bolted segments for printing, it remains one rigid logical chassis (§2). |
| **3D-printed PLA, BOLTED, fully disassemblable, no adhesive** | **PASS** | All custom parts are PLA; every joint is an M3/M4 bolt into a captive nut; no glue anywhere; any module unbolts and lifts off the key rail (§3, §6). |
| **Visible process (material path watchable)** | **PASS** | The filament path along the top of the spine stays open; only the wiring is covered, by the raceway (§4). |
| **Mains stays in sealed PSU; student wires 12 V ELV only** | **PASS** | Raceway and terminal block carry ELV only; mains never leaves the certified PSU (§4). |
| **Preserve Phase-2 Hall-sensor slot at X ≈ 180–220** | **PASS** | `module_hall_reserved` is modelled now as a reserved clip slot at **X = 180**, kept clear of its neighbours (QA G4 shows no overlap). Populated later without touching other modules. |
| **Attack the wiring/assembly burden** | **PASS** | One raceway + one terminal block; captive nuts kill loose fasteners; keyed clips give alignment-by-design; cites the I2C 12→4 precedent (§3, §4, §6). |

---

## 8. Placeholder components — clearly marked stand-ins

The grey-blue parts in the model are the **real printed parts** I'm designing. The following blocks are **PLACEHOLDERS** — accurate bounding boxes for bought-in components, sitting at their real positions so I can check fit and clearance. **They are not designed parts and carry no detail beyond their outside size.** In `model.py` every one is tagged `PLACEHOLDER_*`.

| Placeholder | Modelled size (mm) | Stands in for |
|---|---|---|
| `PLACEHOLDER_NEMA17` | 42 × 42 × 48 + 5 mm shaft | The stepper motor (filament puller), low at the controller end. |
| `PLACEHOLDER_VOLCANO_HOTEND` | 45 × 24 × 16 + ~30 nozzle down | The Volcano hotend that melts the plastic. |
| `PLACEHOLDER_ARDUINO_UNO` | 68.6 × 53.4 × 15 | The Arduino Uno controller board. |
| `PLACEHOLDER_CNC_SHIELD` | 68.6 × 53.4 × 20 (stacked) | The CNC Shield v3 that sits on the Arduino. |
| `PLACEHOLDER_PSU_SEALED` | 129 × 98 × 38 | The sealed mains power supply. |
| `PLACEHOLDER_FAN_5015_A/B` | 50 × 50 × 15 each | The two 5015 blower fans on the cooling module. |
| `PLACEHOLDER_LCD_1602A` | 80 × 36 × 12 | The 1602A character display. |
| `PLACEHOLDER_SPOOL` | ~190 dia × 56 | The take-up spool of finished filament. |

When I move to detailed design I'll swap each placeholder for the real part model or measured envelope and re-run the QA.

---

## 9. Print orientation

- **Spine segments:** print lying on their side (web vertical, flange faces vertical) so the layers run along the length of the beam — that's the strongest orientation against bending, which is the load the spine actually sees. Each segment is ≤ 220 mm, inside the 256 mm bed.
- **Modules:** print base-down (the seat that meets the spine on the print bed) so the captive-nut pockets and the key slot print cleanly without supports.
- **Riser:** print flat on its largest face so the tall upright isn't a thin tower mid-print; the gusset prints in the same pass.
- **Covers:** print flat — they're thin lids.

All printed parts are confirmed to fit the 256 mm bed (QA G3); the longest is a spine segment at 220 mm.

---

## 10. How this feeds the SAT criteria

- **C2 (Designing).** This is a worked, dimensioned design option with every decision justified above — exactly the "speculative thinking and modelling" C2 wants, and the justifications (I-section for stiffness-per-gram, splice location to dodge the hot zone, clearance for a slide-fit) are the kind of reasoning that pushes toward Very High.
- **C5 (Integration / Realisation).** The keyed-clip + captive-nut + raceway design gives a clean, repeatable, photographable assembly sequence (spine → modules → raceway → terminal block). Each step is discrete evidence, and the terminal block is a concrete integration improvement over the hand-soldered baseline — and every decision here is already written down with its reason, which is what C5 marks.
- **C8 (Evaluation / Improvement).** There's a direct before→after story with numbers (footprint shrinks, wiring consolidates to one block, loose parts drop), and the I2C 12→4 precedent shows a *pattern* of justified improvement — strengthening the evaluation narrative.
- **AS1100 drawings.** The spine is the geometric **datum** the current build never had. With a datum, the missing AS1100 assembly drawings become straightforward: dimension every module's X position and clip interface from the spine origin. The STEP file in this folder is the source those drawings come off.

---

## 11. Open questions and honest unknowns

1. **The printer bed is confirmed at 256 mm — and the spine is what it matters most for.** QA gate G3 runs against **BED = 256 mm**, the school printer's measured build volume, so G3 is a firm pass, not a conditional one. The split into bolted segments stands because the full 380 mm spine exceeds the bed: each segment (≤ 220 mm) clears it with margin. `BED` remains a single parameter, so if the machine ever changed the model re-sections and re-checks in one run — but on the confirmed 256 mm bed nothing needs re-splitting.
2. **PLA stiffness near the hotend.** PLA starts to soften around 60 °C and the Volcano runs far hotter. The hotend module lifts the hotend on a 25 mm **thermal standoff** (a gap that keeps the hot part away from the PLA), and in reality the immediate cradle would be printed in a higher-temperature material. The standoff height is a starting guess — it needs a thermal test near the PLA to confirm the spine doesn't soften locally.
3. **Spine deflection.** The I-section is sized for stiffness on paper; it needs a real deflection test on a printed section to confirm it doesn't sag or twist under the hotend, fans, and puller loads.
4. **Clip clearance fit.** The 0.3 mm-per-side slide-fit is my estimate; a quick fit-test print on the school's printer should confirm it before I commit the interface to every module.
5. **Single point of failure.** One spine means a cracked spine stops the machine. The bolted modularity softens this (reprint one segment), but it's a real concentration of risk versus fully independent blocks — worth stating in the evaluation.

---

## 12. QA result reference

The model passes all six QA gates (plus a STEP round-trip check) after **2 iterations** of the export → check → fix loop. Final packaged envelope **465 × 192 × 251 mm**. Full gate-by-gate detail and the iteration log are in **`qa_report.md`** in this folder.

**One-line assembly argument:** the flat slab + scattered standoffs + hand-soldered branches become **one spine (2 bolted segments) + 4 keyed clip-on modules + 1 winder riser**, with every 12 V lead dropping into **one raceway onto one terminal block** — fewer distinct loose parts, fewer ways to build it wrong, and a wiring count cut the same way the **LCD went from 12 wires to 4** via I2C.
