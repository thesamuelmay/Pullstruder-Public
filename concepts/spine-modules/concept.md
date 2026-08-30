# Pullstruder — Design Concept: "Spine + Clip-On Modules" (RECOMMENDED)

**Concept ID:** spine-modules
**Status:** Recommended concept
**Borrows from:** L-fold winder concept (vertical spool riser)

---

## One-line summary

Replace the flat full-footprint chassis slab with a single central structural **spine** (printed T-/I-section beam) that every functional station clips onto as a self-contained module, with all 12V wiring routed through an integrated cable channel to one terminal block — collapsing loose-part count, fixing the dead gap, and shrinking the footprint from ~554 mm to ~380 mm.

---

## The problem it solves

The current machine is a "runway": a bounding box of **554 (X) × 220 (Y) × 325 (Z) mm** that is only **~23% occupied** — roughly three-quarters air. Three specific faults drive that waste, and the spine attacks all three:

- **Problem A — the dead gap.** The NEMA17 motor/puller end is flung out to X = −527, leaving a ~111 mm gap (only ~14% full) between it and the central column. The spine concept folds the winder/puller up onto a short vertical riser, deleting that horizontal run entirely.
- **Problem B — the height spike.** One slender central hotend column spikes Z to 325 mm while everything else sits under ~240 mm. The spine carries the hotend as a low module clipped to the beam rather than perched on a tall isolated post, so the tall element becomes the *folded winder riser* (a deliberate, structural use of height) instead of an accidental spike.
- **Problem C — the spacing slab.** A flat full-footprint chassis slab holds every block apart horizontally and is the single biggest cause of low fill. Deleting the slab and replacing it with a centreline beam is the core move: stations register *to the beam*, not to a sheet, so they pack to their true functional spacing.

Underneath all three sits the project's documented headline burden: **assembly, and specifically wiring.** The current build has *no terminal block* and relies on hand-soldered branch joints — a known gap. A prior win already cut the 1602A LCD from **12 wires to 4** by moving to I2C; this concept cites that as precedent and extends the same "consolidate the wiring" logic to the whole 12V harness via one raceway and one terminal block.

---

## How it works

### The spine cross-section

A single printed PLA beam runs the machine centreline (the X axis). Cross-section is a **T- or I-profile** chosen for bending stiffness per gram of filament:

- The **vertical web** carries bending load along the length and gives the modules a tall, flat datum face to register against.
- The **top flange** is the mounting deck: a repeating pattern of bolt holes / captive-nut pockets at the documented station X positions.
- The **lower channel** (the hollow of the I, or a cap added under the T) is the **integrated cable raceway** — see below.

Because it is one printed part (or a small number of bolt-spliced sections, see Open Questions), the spine *is* the geometric datum for the whole machine. Every module's position and squareness is defined relative to it, which is exactly what an AS1100 assembly drawing needs as its reference frame.

### The module-clip interface

Each functional station becomes a **self-contained printed module** — its own little printed bracket carrying its hardware (hotend, fans, stripper, sensor pivot, etc.). The interface to the spine is deliberately idiot-proof:

- A **keyed slot / tongue** on the underside of each module mates with a matching key on the spine flange, so the module can only seat in the correct orientation and slides to a hard stop at its X position — **alignment by design**, no measuring during assembly.
- **Captive-nut bolt pads** on the module accept bolts from the spine flange. Bolted, not glued — fully disassemblable, per constraint.
- Modules are independent: any one can be printed, fitted, removed, or upgraded without disturbing its neighbours.

### The cable channel + terminal block

The lower channel of the spine runs the full length as a **wire raceway with a snap-on cover**:

- Each module drops its 12V leads straight down into the channel through a slot in the flange.
- All leads run along the channel to a single **terminal block** mounted at the controller end (near the Arduino Uno + CNC Shield v3).
- This directly closes the documented *"no terminal block / hand-soldered branches"* gap: branches become screw terminals, not solder blobs. Maintenance, fault-finding, and disassembly all improve.
- The snap cover keeps the **"visible process"** intent intact — the *material path* stays open and watchable while the *wiring* is the thing that gets tidied away. (Wiring was never the thing the assessor needs to watch; the filament path is.)
- **MAINS stays inside the sealed certified PSU.** Only the 12V ELV side enters the raceway. The raceway carries ELV only — this is stated explicitly so the safety boundary is unambiguous.

### The L-folded winder

Borrowed from the L-fold concept: the **spool/winder + NEMA17 puller** fold up onto a short **vertical riser** at the controller end of the spine instead of running out along the X axis to X = −527. The puller still pulls the filament along the centreline, then the spool sits above on the riser. This deletes the ~111 mm dead gap and is the single biggest length saving.

### Station-by-station (approximate new positions on the spine)

The functional order is preserved; the spacing is compressed to true functional clearances and the winder is folded vertical.

| Station | Old position | New position (spine) | Notes |
|---|---|---|---|
| Stripper module | X = 0 | X ≈ 0 (datum origin) | Sets the centreline; first clip-on, defines origin. |
| Volcano hotend module (nozzle-down) | X = 100 | X ≈ 70–80 | Pulled in; low module on the beam, not a tall post. |
| Cooling fans module (5015 blowers) | X = 150 | X ≈ 120 | Always-on; clips just downstream of the nozzle. |
| Hall-sensor pivot module (Phase-2 reserve) | X = 220 | X ≈ 180 | Pivot-lever mount kept as a reserved clip slot — populated later. |
| Spool / winder + NEMA17 | X = −527 (flung out) | folded onto vertical riser at the controller end (X ≈ −40 to −60, Z up) | The L-fold. Kills the dead gap. |
| Controller + terminal block | scattered | controller end of spine | Arduino + CNC Shield + A4988 + terminal block in one zone. |

All values are approximate design intents for the concept stage, to be fixed against real part envelopes and the school printer bed at prototyping.

---

## Compactness gain

| Dimension | Before (runway) | After (spine, target) | Change |
|---|---|---|---|
| Length (X) | 554 mm | ≈ 380 mm | **−174 mm (≈ −31%)** |
| Depth (Y) | 220 mm | ≈ 150 mm | **−70 mm (≈ −32%)** |
| Height (Z) | 325 mm | ≈ 250–280 mm | **−45 to −75 mm (≈ −14 to −23%)** (winder riser is now the tallest element by design, not an accidental hotend spike) |
| Bounding-box volume | ≈ 0.0396 m³ | ≈ 0.0152–0.0160 m³ | **≈ −60% volume** |
| Fill (occupied fraction) | ~23% | target ~40–50% | roughly **doubled** |

Footprint target **≈ 380 × 150 × ~270 mm** sits comfortably inside the **≤ 500 × 200 × 300 mm** envelope on every axis. The ~31% length reduction comes almost entirely from (a) deleting the slab so stations pack to true spacing and (b) folding the winder vertical to kill the 111 mm dead gap.

---

## Assembly-ease gain

**Part-count argument.** The flat slab plus per-block standoffs and brackets become **one spine + N self-contained modules**. Loose fasteners and one-off spacers (the parts most likely to be dropped, mismatched, or left out) are absorbed into printed captive-nut pads. Fewer distinct loose parts, fewer ways to assemble it wrong.

**Wire-count argument.** Today: no terminal block, hand-soldered branch joints scattered along the runway. With the spine: every 12V lead drops into one raceway and lands on **one terminal block**. This is the same consolidation logic that already took the **LCD from 12 wires to 4 via I2C** — cited as precedent. The harness goes from scattered soldered branches to a single documented, screw-terminated bus.

**Assembly order (defined, repeatable):**
1. Print/assemble the spine (or bolt-splice its sections).
2. Mount the terminal block + controller at the controller end.
3. Clip the stripper module at the origin (X ≈ 0).
4. Clip hotend → cooling → (reserved Hall slot) in order along the beam.
5. Fold-mount the winder riser + NEMA17 at the controller end.
6. Drop all 12V leads into the raceway, land them on the terminal block, snap the cover.
7. Power-on check (ELV only).

**Alignment by design.** Keyed slots + hard stops mean each module can only seat correctly and at the right X — no jigs, no measuring, no cumulative tolerance stack along a slab.

---

## How it respects each hard constraint (checklist)

- [x] **Footprint ≤ 500 × 200 × 300 mm** — target ≈ 380 × 150 × ~270 mm; passes on all three axes.
- [x] **Single chassis (non-negotiable)** — the spine *is* the single chassis; everything registers to it. (If bed-sectioned, it remains one logical chassis via a bolted splice — see Open Questions.)
- [x] **Custom parts 3D-printed PLA, BOLTED, fully disassemblable** — spine + modules are printed PLA; all joints are bolted captive-nut pads; no adhesive; any module removable.
- [x] **Visible process (material path watchable/open)** — the filament path along the top of the spine stays open and watchable; only the *wiring* is covered (raceway), which was never the thing to watch.
- [x] **MAINS stays in sealed certified PSU; student wires 12V ELV only** — raceway and terminal block carry ELV only; mains never leaves the PSU enclosure. Stated explicitly.
- [x] **Preserve room for Phase-2 Hall-sensor closed-loop upgrade (pivot lever at X≈220→180)** — a reserved clip slot for the Hall-sensor pivot module is designed in from the start; populated later without disturbing other modules.
- [x] **Attacks the wiring/assembly burden** — single raceway + single terminal block; cites the I2C 12→4 precedent; defined assembly order.

---

## How it sets up SAT criteria evidence

- **C5 (integration / assembly).** The spine gives a clean, photographable, defined assembly sequence: spine → modules → raceway → terminal block. Each step is discrete evidence. The terminal block + raceway are concrete, demonstrable integration improvements over the hand-soldered baseline.
- **C8 (improvement / evaluation).** A direct before→after story with numbers: footprint −31% length / ~−60% volume, fill roughly doubled, wiring consolidated to one terminal block, loose-part count down. The I2C 12→4 precedent shows a *pattern* of justified improvement, strengthening the evaluation narrative.
- **AS1100 assembly drawings.** The spine is the geometric datum the current build lacks. With a defined datum, the missing AS1100 assembly drawings become straightforward: dimension every module's X position and clip interface from the spine origin. This closes the documentation gap *and* produces drawing evidence.

---

## Risks / tradeoffs

- **Spine stiffness.** A printed PLA beam must not sag or twist under the hotend, fan, and puller loads. Mitigate with an I/T section sized for stiffness, and validate by deflection test on the first printed section. (Honest unknown until printed.)
- **Print length vs bed size.** The spine at ~380 mm exceeds the confirmed 256 mm school printer bed. Requires **sectioning + a bolted splice** — adds a joint that must itself be stiff and aligned. See Open Questions.
- **Heat near the hotend.** The Volcano at the hotend module sits close to PLA. The hotend module needs a thermal standoff / heat break so the PLA spine doesn't soften locally. Validate with a thermal test.
- **Raceway capacity & heat.** All 12V leads in one channel — verify the channel cross-section fits the full harness and that no high-current lead (PSU feed, heater MOSFET) over-heats the channel. Keep the heater leads appropriately gauged.
- **Tolerance of keyed clips.** Printed keyed slots must be tight enough to align but loose enough to assemble — needs a tolerance/fit test print before committing the interface.
- **Single point of failure.** One spine means a cracked spine disables the machine. Bolted modularity mitigates (reprint one section), but it is a real concentration of risk vs. independent blocks.

---

## What to prototype first

1. **One spine section + one module clip interface.** Print a short length of the chosen I/T section plus one module with the keyed slot + captive-nut pads. Test: does it self-align, seat to a hard stop, and bolt up disassemblably?
2. **Deflection test** on that section under a representative load to validate the cross-section choice.
3. **Bolted splice coupon** — print two short spine ends and the splice; check stiffness and alignment across the joint (de-risks the bed-size problem early).
4. **Raceway + terminal block mock** — route a representative harness through the channel to one terminal block; confirm fit and the snap cover.

---

## Open questions

- **School 3D-printer bed is confirmed at 256 mm — and it matters most here.** The spine is the longest single part in the whole machine (~380 mm), so it exceeds the bed and **must be printed in sections joined by a bolted splice**. This needs: (a) deciding section count and splice location (avoid splicing under the hotend/high-load zones), (b) a splice that keeps the spine stiff and straight and *remains the single logical chassis*. Both are settled in the CAD: two segments (≤ 220 mm each), splice clear of the hot zone at X≈70.
- Final cross-section (T vs I) and wall thickness — pending the deflection test.
- Exact raceway cross-section — pending the real harness bundle diameter.
- Hotend thermal standoff geometry — pending the thermal test near the PLA.
- Confirm the folded-winder riser height keeps total Z under 300 mm with the spool fitted.

---

*Concept stage. Dimensions are design intents in SI units (mm), to be fixed against real part envelopes at prototyping; the printer bed is confirmed at 256 mm.*
