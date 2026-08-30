# Concept: "Stacked Deck"

## One-line summary
A two-level repackaging of the Pullstruder that puts the thermal path (stripper → hotend → cooling) on an open top deck and hides the electronics + sealed PSU in a tray directly underneath — collapsing the footprint to roughly **300 × 200 × 260 mm** and making it the smallest of the candidate concepts, at the cost of the hardest heat-isolation and serviceability problems.

---

## The problem it solves

The current machine is a **"runway" layout**: a bounding box of **554 × 220 × 325 mm** that is only about **23 % occupied** — three-quarters of the volume is air. Three specific faults drive that waste:

- **(A) The flung-out puller end.** The NEMA17 motor/puller is pushed all the way out to X = −527, leaving a ~111 mm dead gap (only ~14 % full) between it and the central column. Pure empty length.
- **(B) The height spike.** A single slender central column carries the Volcano hotend and spikes the height to **325 mm**, while every other block sits under ~240 mm. One thin tower sets the whole Z envelope.
- **(C) The full-footprint chassis slab.** A flat slab spanning the entire footprint spaces every functional block apart horizontally. This is the *main* cause of the low fill — the layout is 2D when it could be 3D.

Stacked Deck attacks fault (C) head-on: instead of spreading blocks across one flat plane, it folds the machine into two planes stacked vertically. The electronics and PSU — which previously demanded their own slice of slab area — move *underneath* the thermal path, reclaiming nearly all of their footprint. It also resolves (A) by bringing the winder in as a cantilever rather than a long runway extension, and it tames (B) by accepting that *some* height is unavoidable for the hotend, but spending that height budget on a second useful deck rather than on empty air around a lone tower.

---

## How it works

### Top deck — the thermal path (open and watchable)
The top deck carries the **visible process** in a straight, horizontal line on a single centreline:

`stripper (X=0) → Volcano hotend, nozzle-down (X=100) → cooling fans / quench (X=150) → Hall-sensor station reserved (X=220)`

This deck is built as an **open frame**: side rails and end plates only, no top cover, no front panel. The filament is fully exposed from the moment it leaves the nozzle through the quench zone. The hotend still mounts nozzle-down and the molten strand is pulled **horizontally** across the deck into the cooling fans — the quench path stays linear and horizontal. **Filament is never routed vertically through the hot zone**, and it never passes near the electronics tray below.

### Bottom deck — electronics + PSU tray (hidden, and that's fine)
Directly beneath the top deck sits a shallow enclosed **tray** holding the things that gain nothing from being visible:

- Arduino Uno + CNC Shield v3 + A4988 driver
- D4184 MOSFET + heater wiring
- the **sealed, certified 12 V 10 A PSU** (mains stays entirely inside it)
- all 12 V ELV loom routing

Because these are control and power components — not part of the "process" a viewer wants to watch — hiding them costs the demonstration nothing. The tray doubles as a cable raceway: the 12 V loom runs concealed beneath the deck instead of draping across an open slab.

### Cantilevered winder
The spool/winder is **cantilevered off one end** of the stack rather than extended along a runway. The NEMA17 driving it mounts to the end plate of the top deck, and the spool hangs out past the footprint on a bolted bracket arm. This removes the ~111 mm dead runway gap entirely — the winder no longer needs its own stretch of chassis between itself and the hotend column.

### The heat-isolation gap / shield (the crux)
The single most important feature of this concept is the **inter-deck barrier**. Between the hot top deck and the electronics tray below there is:

1. **An air gap** of ~20–30 mm (final value to be set by the thermal test — see Open Questions). Hot air rises, so the gap alone provides convective separation if it can vent sideways.
2. **A reflective/insulating shield** forming the floor of the top deck — a thin sheet (e.g. aluminium foil-faced board, or a printed PLA panel faced with foil tape) that reflects radiant heat from the Volcano back upward and blocks line-of-sight from the hotend to the boards.
3. **Side-venting**: the gap is open on the left and right so the 5015 blower exhaust and any rising hot air sweep *out the sides* rather than pooling against the tray lid.

The PLA chassis itself is a constraint here: PLA softens around 55–60 °C, so the shield must keep the tray-side surface comfortably below that. This is exactly what the first prototype must verify.

### How visible-process is preserved
The requirement is that **the material path stays watchable**. Stacked Deck satisfies this by being honest about *what* needs to be visible: the **process** is the thermal path, not the wiring. So the top deck is left fully open and the entire stripper → nozzle → quench journey is exposed and demonstrable. The electronics, which a viewer has no reason to watch, are the *only* thing hidden. The concept therefore does not trade away visible-process — it trades away visibility of components that were never part of the process in the first place.

---

## Compactness gain (the headline)

| Dimension | Runway (current) | Stacked Deck (target) | Reduction |
|---|---|---|---|
| X (length) | 554 mm | ~300 mm | −254 mm (−46 %) |
| Y (depth) | 220 mm | ~200 mm | −20 mm (−9 %) |
| Z (height) | 325 mm | ~260 mm | −65 mm (−20 %) |
| **Footprint (X × Y)** | 121,880 mm² | ~60,000 mm² | **≈ −51 %** |
| **Bounding volume (X × Y × Z)** | 39,611,000 mm³ | ~15,600,000 mm³ | **≈ −61 %** |

**Headline:** roughly a **half** the footprint and about a **61 % cut in bounding volume** — the most compact of the candidate concepts. The volume shrink is the bigger story than the footprint shrink, because folding the layout into two decks is fundamentally a volumetric move, not a planar one. (All targets are nominal; the Y and Z figures depend on the final inter-deck gap and tray depth, which the thermal prototype will fix.)

---

## Assembly-ease gain

- **Wiring hidden and consolidated.** The under-tray is a dedicated raceway: the 12 V loom is routed beneath the deck, out of sight and out of the way. This continues the project's main assembly win — the earlier move that cut the **LCD from 12 wires to 4 via I2C** — by giving the remaining loom a single confined channel rather than letting it sprawl across an open slab. It invites further consolidation (e.g. a small terminal block or a single 12 V distribution point inside the tray).
- **Modular decks.** Top deck and bottom tray are separate bolted sub-assemblies. Each can be built, wired, and bench-tested on its own, then bolted together. This suits the fully-disassemblable, no-adhesive requirement and makes the build less of a single tangled operation.
- **One PSU, one mains boundary.** The sealed PSU lives in the tray; the student only ever wires the 12 V ELV side, all of which is inside the concealed loom.

---

## How it respects each hard constraint (checklist)

- **Footprint ≤ 500 × 200 × 300 mm** — ✅ Target ~300 × 200 × 260 mm is inside the envelope on all three axes with margin to spare on X and Z.
- **Single chassis (non-negotiable)** — ✅ The two decks are one bolted chassis assembly (top frame + bottom tray joined by corner posts), not two separate machines. Worth stating explicitly in the folio so the stack is not mistaken for two chassis.
- **Custom parts 3D-printed PLA, bolted, fully disassemblable** — ✅ Corner posts, deck frame, tray, winder bracket all printed PLA and bolted; no adhesive. *Caveat:* PLA near the hotend needs the heat shield to stay below softening (~55 °C) — see Risks.
- **Visible process** — ✅ Top thermal deck is fully open; stripper → nozzle → quench is exposed and watchable. Only the non-process electronics are hidden. (This is the constraint most at risk in a stacked layout, so the open top deck is a deliberate, defensible answer — not an afterthought.)
- **Mains inside sealed certified PSU; student wires only 12 V ELV** — ✅ Sealed PSU in the tray; only the ELV loom is student-wired, and it is concealed under the deck.
- **Room preserved for Phase-2 Hall-sensor closed-loop upgrade (pivot lever at X=220)** — ✅ The X=220 station is reserved *on the open top deck*, where a pivot lever has clear swing room and the sensor wire can drop straight into the tray below — arguably a cleaner upgrade path than the runway gave.
- **3D-printer bed size confirmed (256 mm cube)** — ✅ The school printer's bed is confirmed at 256 mm. The corner posts and deck frame are the largest printed parts; every printed part is still designed to be splittable/boltable so nothing depends on a single large print, and all sections sit inside the 256 mm bed with margin.

---

## Risks / tradeoffs

**1. Heat isolation (lead risk).** Putting heat-generating electronics directly under a Volcano hotend is the central gamble. PLA softens at ~55–60 °C and the Arduino/driver have their own thermal limits. If the inter-deck gap and shield are under-designed, the tray cooks: warped chassis, drifting driver behaviour, or worse. This is the make-or-break of the concept and must be proven before anything else is committed. Mitigations are designed in (air gap + reflective shield + side-venting), but they are unproven until tested.

**2. Serviceability of the buried electronics.** The flip side of hiding the boards is that you have to *get at* them. If a wire comes loose or the A4988 needs swapping, the top deck is in the way. Mitigation: design the tray to **slide or hinge out** from one side (e.g. a drawer on the long axis) so the electronics are reachable without dismantling the thermal deck. This must be a design requirement, not a hope — otherwise a 30-second fix becomes a full teardown.

**3. Concept maturity / risk profile.** This is explicitly the **highest-risk** candidate. It buys the smallest envelope but spends that saving on two genuinely hard sub-problems (heat, access) that the flatter concepts simply don't have. The folio should present it as the bold option, not the safe one.

**4. Build height of the hotend column.** Z is still partly set by the hotend; the 260 mm target assumes the deck spacing can accommodate the Volcano nozzle-down plus the tray plus the gap. If the gap has to grow for thermal reasons, Z grows with it — the height saving is the least certain number in the table.

---

## What to prototype first

**The inter-deck thermal mock-up — before any other build work.** Build a throwaway rig: the Volcano hotend mounted nozzle-down at its real height above a representative tray lid, with the candidate air gap and heat shield in place. Run the hotend at full operating temperature for a sustained period and log the temperature on the tray-side surface (a cheap thermistor or thermocouple where the Arduino would sit). 

Decision rule: if the tray-side surface holds comfortably below ~50 °C, the concept is viable and the measured gap becomes the design value. If it doesn't, either the gap grows (and Z grows), forced ventilation is added, or the concept is abandoned in favour of a flatter one. **Do this first because every other dimension and the whole go/no-go decision depends on its result.**

---

## Open questions

- **School 3D-printer bed size — confirmed at 256 mm (settled).** The bed is a 256 mm cube build volume. The corner posts and the deck frame are the largest printed parts; every part is still designed to be split and bolted, and all sections sit inside the 256 mm bed with margin. This is no longer an open item.
- **Inter-deck gap — exact value.** The 20–30 mm gap and the ~260 mm height target are placeholders pending the thermal prototype above. The test sets the real number, and that number sets the final Y/Z envelope.
- **Tray access mechanism.** Drawer vs hinge vs lift-off lid for servicing the buried electronics — to be resolved alongside the thermal layout, since how the tray opens affects the venting geometry.

---

*Concept "Stacked Deck" — high-compactness, high-risk candidate. Smallest envelope of the set; viability gated on a single thermal test.*
