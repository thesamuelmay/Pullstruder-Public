# Concept: "L-Fold" — Pullstruder layout redesign

## One-line summary
Fold the spool/winding stage up onto a vertical back-plane so the machine reads as an **L** in side profile instead of a 554 mm straight "runway", closing the dead gap at the motor end and stacking the spool above the thermal path to cut the footprint length to ~360 mm while keeping every station visible and the quench path horizontal.

---

## The problem it solves

The current "runway" layout has a bounding box of **554 (X) × 220 (Y) × 325 (Z) mm** and is only **~23 % occupied** — three-quarters of the bounding volume is air. Three specific faults drive that:

- **(A) Dead gap at the motor end.** The NEMA17 motor/puller end is flung out to **X = −527 mm**, leaving a **~111 mm gap** (only ~14 % full) between it and the central column. This single stretch is pure wasted length.
- **(B) Height spike from one column.** A single slender central hotend column spikes the height to **325 mm** while every other block sits under ~240 mm. One element sets the whole Z envelope.
- **(C) Footprint-wide chassis slab.** A flat full-footprint chassis slab spaces every functional block apart horizontally — it is the main structural cause of the low fill, because nothing is allowed to sit above anything else.

L-Fold attacks (A) by sliding the motor in, and attacks the *cause* of (C) by allowing one stage (the spool/winder) to leave the horizontal plane and stack vertically. It deliberately does **not** touch the thermal path geometry, because the linear stripper→hotend→cooling line is what guarantees the melt is quenched in the right order.

---

## How it works — the fold, station by station

The centreline of the thermal path stays horizontal along X. The winding stage rotates up ~90° onto a **vertical back-plane** that rises in Z at the downstream end. Coordinates below are approximate target positions in the redesigned frame; X is measured from the stripper datum at X = 0.

| Station | Current position | New target position | What changed |
|---|---|---|---|
| Stripper (bottle-to-strip entry) | X = 0 | **X = 0** | Unchanged — datum. |
| Volcano hotend (nozzle-down melt) | X = 100 | **X = 100, Z ≈ 0** | Unchanged. Stays nozzle-down, horizontal feed. |
| Cooling fans (5015 blowers, quench) | X = 150 | **X = 150** | Unchanged — quench stays immediately downstream of nozzle. |
| Hall sensor (Phase-2 reserved) | X = 220 | **X = 220** | Reserved pad + pivot-lever room preserved at X = 220. |
| NEMA17 motor / puller | X = −527 | **X ≈ −180 to −200** | **Slid inward ~330 mm**, closing the 111 mm dead gap and tucking the puller just upstream of the stripper. |
| Spool / winder | Z = 100 *beside* the line | **X ≈ 250–300, Z ≈ 150–230, on vertical back-plane** | **Folded up**: rotated onto the back-plane and stacked *above/downstream* of the thermal path instead of sitting beside it. |
| Control stack (Arduino Uno + CNC Shield v3 + A4988) | on chassis | mounted on the **rear face of the vertical back-plane** | Moves off the footprint and onto the standing plane — uses otherwise-dead vertical area. |
| 1602A LCD (I2C) + B10K pot | front edge | **front face of back-plane, eye-height** | Better readability; uses the vertical plane, not footprint. |
| 12 V 10 A PSU | on chassis | low and rearward, under the back-plane root | Heaviest item kept low for stability; off the working footprint. |

**Why the fold works:** the spool only needs the filament to *arrive* at it; it does not need to be co-linear with the melt. Lifting it onto the back-plane removes the longest "spacing" demand on the horizontal slab. The puller slide-in removes the other big empty stretch. Together they collapse length from 554 → ~360 mm without compressing any thermal clearance.

The back-plane also becomes a **mounting surface** for control electronics, LCD and wiring runs — turning the height that was previously dead air (problem B) into useful real estate, and giving wiring a single vertical spine to run along.

---

## Compactness gain

| Dimension | Current "runway" | L-Fold target | Change |
|---|---|---|---|
| Length (X) | 554 mm | **~360 mm** | **−194 mm (−35 %)** |
| Depth (Y) | 220 mm | ~200 mm | −20 mm (within envelope) |
| Height (Z) | 325 mm | ~280–290 mm | −35 to −45 mm (back-plane sets Z, not one spike) |
| Footprint (X × Y) | 554 × 220 = **121,880 mm²** | 360 × 200 = **72,000 mm²** | **−49,880 mm² ≈ −41 % footprint area** |
| Bounding volume | 554×220×325 ≈ **39.6 L** | 360×200×285 ≈ **20.5 L** | **−48 % bounding volume** |
| Occupancy (fill) | ~23 % | est. ~38–42 % (same parts, smaller box) | roughly +15–19 pp |

Headline: **length down ~35 %, footprint area down ~41 %, bounding volume down ~48 %.** All three target dimensions land inside the **≤ 500 × 200 × 300 mm** envelope with margin on every axis. Occupancy estimate is derived simply: the same physical parts (unchanged volume) inside a ~48 % smaller bounding box must raise fill fraction by roughly 1 / 0.52 ≈ 1.9×, i.e. ~23 % → ~38–42 %. This is an estimate, not a measured solid-model figure — flag for verification once the parts are placed in CAD (STEP assembly).

---

## Assembly-ease gain

- **Wiring spine.** Folding the control stack and LCD onto the vertical back-plane gives every wire a single flat surface to run along, with the PSU at its root. This directly extends the **prior LCD win** (12 wires → 4 via I2C) by giving the remaining harness one tidy plane instead of a sprawl across a 554 mm slab. Wiring is the stated main assembly burden, so this is the largest ease gain.
- **Shorter runs.** Sliding the motor in ~330 mm shortens the stepper/driver cable run and the puller-to-control loop.
- **Stays bolted and disassemblable.** The back-plane is a bolted bracket off the single chassis, not a glued sub-assembly. Each stage still unbolts independently.
- **Better service access.** Electronics on the back-plane face are reachable without disturbing the thermal path; LCD at eye height improves operation.

---

## How it respects each hard constraint (checklist)

- [x] **Footprint ≤ 500 × 200 × 300 mm** — target 360 × 200 × ~285 mm; inside on all three axes.
- [x] **Single chassis (non-negotiable)** — the back-plane is a bolted bracket rising from the *one* chassis, not a second base. No second footprint.
- [x] **Custom parts 3D-printed PLA, bolted, no adhesive, fully disassemblable** — back-plane and all brackets are printed PLA, bolted; every stage unbolts.
- [x] **Visible process (watchable material path)** — thermal path stays horizontal, open and unobstructed at the front; the fold lifts only the spool, which does not occlude the melt/quench line. Filament remains visible from strip entry through quench, then up to the spool.
- [x] **Mains sealed inside certified PSU; student wires only 12 V ELV** — PSU unchanged and sealed; relocating it low/rear does not open the mains side. Student wiring is still all 12 V.
- [x] **Phase-2 Hall-sensor closed-loop room preserved** — Hall pad and pivot-lever clearance retained at **X = 220**, untouched by the fold (the fold happens downstream at X ≈ 250+ and upward in Z).
- [x] **Quench requirement** — cooling fans stay immediately downstream of the nozzle on the horizontal line; melt order is preserved.

---

## Risks / tradeoffs

- **Spool feed angle.** Lifting the spool onto the back-plane introduces an upward feed path from puller to spool. The filament must turn from horizontal to climbing without kinking on still-warm material. **Mitigation:** keep the spool downstream and well past the quench so filament is fully solidified before it climbs; verify the minimum bend radius for ~1.75 mm PET.
- **Back-plane rigidity / vibration.** A tall printed PLA plane carrying the spool (a rotating mass) and electronics can resonate or flex. **Mitigation:** triangulated bolted gussets to the chassis; keep PSU low to drop the centre of mass.
- **Heat rising onto electronics.** Folding electronics above/behind a hotend means convected heat rises toward the control stack. **Mitigation:** mount electronics on the *rear* face and offset upstream of the nozzle; the always-on blowers already move air. Confirm with a thermocouple check.
- **Print size of the back-plane.** A single tall plane may exceed the school printer bed (see open questions). **Mitigation:** design it as 2–3 bolted printed segments from the start — consistent with the bolted/disassemblable rule anyway.
- **Occupancy is estimated, not modelled.** The ~38–42 % fill is arithmetic, not a CAD measurement. Could come in lower once real clearances are placed.
- **Lower compaction ambition than a full "tower" rethink.** L-Fold is deliberately low-risk: it does not attempt to fold the thermal path itself, so it leaves some length on the table versus a more aggressive vertical stack. This is the intended tradeoff — defensible, buildable, preserves the quench.

---

## What to prototype first

1. **The fold joint / back-plane root bracket.** Print a single bolted bracket that rises from the chassis and carries a mock spool. Validate rigidity and that it bolts/unbolts cleanly. This is the load-bearing novelty — prove it before anything else.
2. **Filament climb path.** Rig a string/filament from puller height up to the proposed spool position and check the bend radius and feed angle with a real ~1.75 mm sample. Cheap, fast, de-risks the biggest functional unknown.
3. **Back-plane as wiring spine.** Lay out the LCD + control stack on a flat card the size of the back-plane face and route the actual harness to confirm the wire-consolidation gain before committing the print.

Defer the full melt/quench rebuild — it is unchanged from the current machine, so it carries no new risk.

---

## Open questions

- **School 3D-printer bed size (confirmed 256 mm cube).** This is now a known constraint, not an unknown. The back-plane is taller than the bed, so it must be segmented (already the recommended approach) — the geometry is sized against the confirmed 256 mm bed.
- **Exact spool Z and feed angle** — pending the climb-path prototype.
- **Measured occupancy** — pending CAD/STEP placement of real part solids.
- **Electronics temperature on the back-plane** — pending a thermocouple check under running conditions.
- **Puller final X** — −180 vs −200 mm depends on stripper/puller mechanical clearance; resolve in CAD.
