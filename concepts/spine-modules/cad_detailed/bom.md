# Pullstruder — Fastener / Bill of Materials (detailed CAD)

**Concept:** spine-modules (detailed, part-accurate model)
**Source of truth:** `model_detailed.py` — every count below is a real hole/pocket feature in the CAD, not an estimate.
**Units:** millimetres (SI).

This is the fastener list for assembling the printed parts to each other and to the bought-in parts. Every bolt goes into a **captive nut** — a hex nut that presses into a printed pocket once and stays put, so you only turn the bolt and never chase a loose nut with a spanner. The hole sizes are **print clearances**, meaning each hole is drilled a little bigger than the bolt so a 3D-printed hole (which always comes out slightly tight) still takes the bolt cleanly: M3 holes are 3.2 mm and M4 holes are 4.3 mm.

---

## 1. Fastener summary

| Fastener | Size | Length | Count | Goes where |
|---|---|---|---|---|
| Socket-head cap screw | M4 | 16 mm | 12 | Module / riser / controller-mount → spine deck (2 per part × 6 parts) |
| Hex nut (captive) | M4 | — | 12 | In the spine top-flange pockets, one per clip bolt above |
| Socket-head cap screw | M4 | 20 mm | 4 | Splice plate → both spine segments' webs |
| Hex nut (captive) | M4 | — | 4 | In the splice plate pockets, one per splice bolt |
| Socket-head cap screw | M3 | 10 mm | 4 | Stripper module → NEMA17 feed-motor face (31 mm bolt square) |
| Socket-head cap screw | M3 | 12 mm | 2 | Hotend module cradle → Volcano heater block |
| Socket-head cap screw | M3 | 10 mm | 4 | Controller mount → Arduino Uno R3 (canonical 4-hole pattern) |
| Hex nut (captive) | M3 | — | 10 | In the module / controller-mount pockets, one per M3 bolt above |

**Totals:** 26 bolts + 26 captive nuts = **52 fasteners.**

| Roll-up | M3 | M4 | Total |
|---|---|---|---|
| Bolts | 10 | 16 | 26 |
| Captive nuts | 10 | 16 | 26 |
| **All fasteners** | **20** | **32** | **52** |

---

## 2. Captive-nut pocket spec (printed into the parts)

| Bolt | Hole (clearance) | Nut across-flats (AF) | Pocket depth | Where the pocket lives |
|---|---|---|---|---|
| M3 | 3.2 mm | 5.5 mm | 2.4 mm | Underside of each module/controller cradle plate |
| M4 | 4.3 mm | 7.0 mm | 3.2 mm | Underside of spine top flange; inside splice plate |

Across-flats (AF) is the distance between two parallel faces of the hex nut — it sets how wide the printed hex pocket has to be so the nut drops in and can't spin.

---

## 3. Threaded inserts

**None used.** Every threaded joint is a bolt into a captive hex nut, which is cheaper and needs no heat-set tool. If a joint is opened and closed many times during prototyping and the PLA pocket wears, a heat-set brass insert is the drop-in upgrade — but the baseline design avoids inserts on purpose.

---

## 4. What is NOT yet in the fastener count (honest gaps)

The cooling module (two 5015 blower fans) and the Hall-sensor pivot module are modelled as bodies but **their component-mount holes are reserved, not yet cut**, because the exact fan-screw spacing and the Phase-2 sensor bracket aren't fixed at this stage. When those are pinned down they will add roughly:

- Cooling: 2 × M3 per fan × 2 fans = **4 × M3** (+ 4 captive nuts)
- Hall pivot (Phase 2): **2 × M3** (+ 2 captive nuts)

These are flagged so the BOM stays honest — the 52 figure is what the current CAD actually contains.
