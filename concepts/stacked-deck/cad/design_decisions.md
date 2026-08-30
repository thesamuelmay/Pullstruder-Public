# Design decisions — "Stacked Deck" concept CAD

**What this is:** the parametric CAD for one of my three repackaging concepts for the
Pullstruder (my PET-bottle filament recycler). This is the **highest-risk, most
compact** option. I modelled the new 3D-printed parts properly and dropped in
accurate stand-in blocks for the bought parts so I can check everything fits and
nothing clashes. The model lives in `model.py` (all the numbers are variables at
the top), and a separate script `qa_check.py` runs the geometry checks for me.

Everything here is millimetres and SI units.

---

## The idea in one paragraph

Instead of laying every part out flat on one big board (which is what the current
machine does, and why it wastes about three-quarters of its volume on air), Stacked
Deck folds the machine into **two levels**. The **top deck is open** and carries the
hot stuff you actually want to watch — the stripper, the Volcano hotend pointing
nozzle-down, and the cooling/quench fans — in a straight line. The **bottom tray is a
closed box** that hides the Arduino, the CNC shield and the sealed power supply,
because nobody needs to watch wiring. Between the two there's an **air gap and a heat
shield** so the hot top doesn't cook the electronics below. The spool **hangs off one
end** on a cantilever arm instead of needing its own stretch of chassis.

---

## The risks (leading with the honest ones)

I'm putting the risks first on purpose, because this concept's whole selling point —
being the smallest — is paid for with two genuinely hard problems that the flatter
concepts just don't have. If I oversell this and it fails the thermal test, I've
wasted build time. So here's the truth.

### Risk 1 (the big one) — heat isolation

I am deliberately parking heat-sensitive electronics **directly underneath a Volcano
hotend**, which runs at roughly 190–230 °C when it's extruding. The chassis is printed
in **PLA, which goes soft at about 55–60 °C** — much lower than people expect. If the
tray gets too hot, the chassis warps, the stepper driver starts behaving strangely as
it heats up, and in the worst case something fails mid-run. This is the make-or-break
of the entire concept.

What I've designed in to fight it, and how the CAD reflects it:

- **An air gap of 22 mm** (`AIR_GAP = 22`) between the top of the closed tray lid and
  the underside of the heat shield. Hot air rises, so a clear gap that can vent
  sideways gives the heat somewhere to go that isn't "down onto the lid". The QA check
  confirms this gap is ≥ 15 mm (it passes at 22 mm) and that nothing in the tray pokes
  up into it (the tallest thing in the tray, the stacked Arduino + CNC shield, tops out
  at 58 mm, and the shield underside sits at 83 mm — 25 mm of clearance).
- **A heat-shield plate** (`make_shield()`, 4 mm thick) that forms the floor of the hot
  zone. In real life this gets faced with aluminium foil tape so it **reflects radiant
  heat** (the heat that travels in straight lines from the hot nozzle, like the warmth
  you feel off a fire) back upward, and it physically blocks the hotend from "seeing"
  the boards.
- **Side venting.** The gap is open at the left and right ends, and the tray's long
  walls have vent slots (`VENT_COUNT = 6` per side), so the blower exhaust and any
  rising hot air sweep out the sides instead of pooling against the lid.

**Honest position:** these are *designed* mitigations, not *proven* ones. CAD can prove
the geometry (gap size, clearances, no clashes) — it **cannot** prove the tray stays
cool. **I am gating this whole concept on a thermal prototype test** before I commit to
building it: mount the real hotend nozzle-down at this exact height over a mock tray
lid, run it hot for a sustained period, and log the temperature where the Arduino would
sit. Decision rule: if the lid-side surface holds **comfortably below ~50 °C**, the
22 mm gap becomes the design value and I build it. If it doesn't, the gap grows (and so
does the height), I add a fan, or I drop this concept for a flatter one. Either way,
**that test comes before any other build work.**

### Risk 2 — getting at the buried electronics (serviceability)

The flip side of hiding the boards is that when a wire comes loose or the A4988 driver
needs swapping, the top deck is sitting right on top of them. If I designed this badly,
a 30-second fix would mean dismantling the whole thermal deck. That's not acceptable, so
I made the fix a **design requirement, not a hope**:

- The tray has a **separate removable lid** (`make_lid()`), not a fused-on top. It drops
  into a rebate (a stepped ledge) in the tray rim and is held by six M3 bolts. The QA
  check specifically asserts the lid exports as its **own solid, distinct from the
  tray** — so I can prove it actually comes off.
- The lid has a **finger-pull recess** moulded into the top so I can lift it out by hand
  once the bolts are out.
- Because the tray is its own bolted sub-assembly under the deck, I can also unbolt the
  whole tray from the four corner posts and slide it out the side for bigger jobs.

So servicing the buried boards means: undo six M3 lid bolts, lift the lid by the finger
pull. No touching the hot deck.

### Risk 3 — this is the bold option, not the safe one

I want to be clear in the folio that I know what I'm choosing. Stacked Deck buys the
smallest machine but spends that saving on two hard sub-problems (heat and access) that
the other two concepts avoid. It should be presented as the ambitious candidate whose
go/no-go hangs on one test, not as the obvious pick.

### Risk 4 — the height number is the least certain

My placeholder stations sit low on the deck, so the CAD reports a low overall height
(143 mm chassis, 200 mm including the spool). The **real** hotend, its mount, and the
clearance I need to actually see and reach the nozzle will push that up. If the thermal
test forces a bigger air gap, the height grows with it. So I'm treating the Z height as
a **floor, not a final figure** — it's the number most likely to move.

---

## The new printed parts, and why they're shaped the way they are

All custom parts are printed in **PLA and bolted together — no glue** — so the machine
fully comes apart, which the brief requires.

| Part | What it does | Key decisions |
|---|---|---|
| **Bottom tray** (`tray_A`, `tray_B`) | Enclosed box for the Arduino, CNC shield and sealed PSU | 3 mm walls and floor; 55 mm internal height; vent slots down both long sides for cross-flow; a stepped rim (rebate) to locate the lid; M4 holes in the rim that bolt down onto the corner posts |
| **Service lid** (`lid_A`, `lid_B`) | Removable top for the tray | Separate part (proven by QA); locating lip drops into the rebate; finger-pull recess; six M3 fixings |
| **Four corner posts** (`post_1`–`post_4`) | Set the inter-deck gap and tie the two decks into one chassis | Each is an identical 18 × 18 mm square post, 26 mm tall (= air gap 22 + shield 4); M4 clearance hole straight through so one bolt ties tray → post → shield → deck |
| **Heat shield** (`shield_A`, `shield_B`) | Floor of the hot zone; reflects/blocks heat | 4 mm PLA, faced with foil tape in real life; no overhang in Y (hard 200 mm depth limit), 4 mm overhang in X where there's slack |
| **Top deck** (`deck_A`, `deck_B`) | Carries the visible thermal path | 5 mm thick (it holds the station loads); raised 30 mm mount pads at each of the four stations with four M3 holes each; a hole under the hotend pad so the nozzle pokes **down** through the deck |
| **Cantilever winder arm** (`winder_arm`) | Holds the spool off the −X end | A vertical gusset bolts to the deck end with four M3s, then a horizontal arm reaches 95 mm out to carry the spool axle |

### Why these specific numbers

- **Deck spacing = 26 mm of post (22 mm air + 4 mm shield).** This is the single most
  important dimension and it's a placeholder until the thermal test, exactly as the
  concept brief says. I chose 22 mm air because it clears the tallest tray component
  (the Arduino + shield stack at 58 mm tall, with the lid at 61 mm) with room, and it's
  comfortably above the 15 mm minimum the QA check enforces. If the test says I need
  more, I bump `AIR_GAP` and everything above it moves up automatically.
- **3 mm walls everywhere structural, 4–5 mm where it matters.** PLA needs at least
  ~2 mm to be reliable; I used 3 mm as the default and went to 4 mm (shield) and 5 mm
  (deck) where the part either gets hot or carries load. The QA check enforces the 2 mm
  minimum.
- **M3 for light fixings, M4 for the structural ties.** The lid bolts, pad mounts and
  winder gusset are M3 (3.4 mm clearance holes). The corner-post column that holds the
  two decks together is M4 (4.5 mm clearance) because that's the load-bearing joint.

### The bolt scheme

One clean idea runs through it: **one M4 bolt per corner ties the whole stack together**
— it passes up through the tray rim, through the corner post, through the heat shield,
and into the top deck. Four bolts, four corners, and the two decks are one rigid chassis.
Everything else (lid, station pads, winder) is M3. No glue anywhere.

---

## How the machine stays watchable (visible-process constraint)

This is the constraint most at risk in a stacked layout, so I want to be explicit about
why I think it's satisfied. The rule is that the **material path** stays watchable. The
material path *is* the thermal path — stripper → molten strand → quench — and that lives
on the **fully open top deck** with no cover and no front panel. What I hid in the box is
the **wiring and power**, which were never part of the process you watch. So I'm not
trading away visible-process; I'm only hiding components that a viewer has no reason to
look at. The filament is pulled **horizontally** across the open deck into the cooling
fans — it is **never routed vertically through the hot zone**, and it never goes near the
electronics tray. (In the CAD the nozzle pokes down through a small hole in the deck;
the strand is pulled sideways above the deck, not down through that hole.)

---

## Compactness — the headline, told honestly

This is where I have to be careful not to overstate things, because there are two
different "footprint" numbers and they tell different stories.

| Measure | Stacked Deck | Original (554 × 220 × 325) | Change |
|---|---|---|---|
| **Chassis-only footprint** (the stacked box, no winder) | 298 × 200 = 59,600 mm² | 121,880 mm² | **−51.1 %** |
| **Full footprint** (including the cantilevered spool) | 437 × 200 = 87,400 mm² | 121,880 mm² | **−28.3 %** |
| **Full bounding volume** | 17,480,000 mm³ | 39,611,000 mm³ | **−55.9 %** |

**The honest bit:** the concept brief quotes "≈ −51 % footprint", and that's true **for
the chassis box** (298 × 200, which matches the ~300 × 200 target). But the spool
hanging off the cantilever reaches 143 mm past the end of the chassis, which **adds that
length back** and brings the *full* footprint down to only **−28 %**. Both numbers are
real and both are inside the 500 × 200 limit, so the machine still complies — but I'm not
going to claim the −51 % as the whole-machine figure when the spool clearly sticks out.

The number I'm most confident about is the **volume reduction: −56 %**. Folding the
layout into two decks is fundamentally a volume move, not a flat-area move, so the volume
shrink is the bigger and more honest story than the footprint shrink.

---

## Per-constraint compliance checklist

| Constraint | Status | Note |
|---|---|---|
| Footprint ≤ 500 × 200 × 300 mm | ✅ PASS | Full envelope 437 × 200 × 200 mm; verified by QA check 2 |
| Single chassis (non-negotiable) | ✅ PASS | Two decks are **one** bolted chassis (tray + posts + shield + deck tied by four M4 corner bolts), not two machines |
| Custom parts 3D-printed PLA, bolted, fully disassemblable | ✅ PASS | All custom parts PLA, all joints bolted, no adhesive. **Caveat:** PLA near the hotend depends on the heat shield keeping the tray below ~55 °C — unproven until the thermal test |
| Visible process | ✅ PASS | Open top deck exposes stripper → nozzle → quench; only non-process electronics are hidden |
| Mains inside sealed certified PSU; student wires only 12 V ELV | ✅ PASS | Sealed PSU lives in the tray (placeholder block); only the 12 V ELV loom is student-wired, and it's concealed under the deck |
| Room preserved for Phase-2 Hall-sensor upgrade | ✅ PASS | Reserved station + mount pad at the X = 255 deck position (placeholder `hall_station`); sensor wire drops straight into the tray below |
| 3D-printer bed size | ✅ CONFIRMED | **256 mm cube build volume — the real school printer, confirmed.** Modelled as `BED = 256 mm` and every part checked against it. Large plates are split into bolted halves so nothing depends on one big print |
| Min wall ≥ 2.0 mm (PLA) | ✅ PASS | 3 mm default, 4–5 mm where loaded/hot; QA check 6 |

---

## Placeholder list (these are STAND-INS, not designed parts)

Every bought-in component below is modelled as a plain bounding-box block at its real
size and real position, just so I can check fit and clashes. **None of these is real
geometry** — they're red blocks standing in for the actual parts.

| Placeholder | Real component | Box size (mm) | Where |
|---|---|---|---|
| `stripper` | Bottle stripper assembly | 40 × 40 × 45 | top deck, X = 35 |
| `hotend_body` + `hotend_nozzle` | Volcano hotend, nozzle-down | 45 × 24 × 16 body + ~30 nozzle down | top deck, X = 135 |
| `fan_1`, `fan_2` | 5015 blower fans (quench) | 50 × 50 × 15 each | top deck, X = 185 |
| `hall_station` | Reserved Phase-2 Hall sensor | 30 × 30 × 25 | top deck, X = 255 |
| `arduino` | Arduino Uno | 68.6 × 53.4 × 15 | in tray |
| `cnc_shield` | CNC Shield v3 (stacked on Uno) | 68.6 × 53.4 × 20 | in tray, on Arduino |
| `psu` | Sealed 12 V 10 A PSU | 129 × 98 × 38 | in tray |
| `lcd` | 1602A LCD | 80 × 36 × 12 | under lid |
| `spool` | Filament spool | ~200 dia × 60 | on cantilever arm |

When I have the real parts in hand I'll replace these blocks with proper mounts and
re-run the QA check.

---

## Print orientation

- **Tray halves, deck halves, shield halves, lid halves** — print flat (largest face
  on the bed). They're shallow, so this is the obvious orientation and avoids supports.
- **Corner posts** — print standing up (26 mm tall); small footprint, prints quickly,
  four of them.
- **Winder arm** — print lying on its side so the arm and gusset are both supported by
  the bed and the M3 holes run cleanly.
- All large plates are **split into A/B halves bolted at the seam**, so every section
  sits comfortably inside the confirmed 256 mm bed with margin to spare.

---

## Open questions (carried forward, not pretending they're solved)

1. **Real 3D-printer bed size — CONFIRMED at 256 mm.** This is settled: the school
   printer has a 256 mm cube build volume, and it's parameterised (`BED = 256`). Every
   section sits inside it with margin, so this is no longer an open item.
2. **The inter-deck gap value — placeholder.** 22 mm is my starting guess. The thermal
   prototype sets the real number, and that number sets the final height.
3. **The thermal test itself — not yet done.** This is the gate. Until the tray-side
   temperature is measured under a running hotend, the heat-isolation mitigations are
   designed but unproven, and the whole concept is provisional.

---

## QA results (summary)

The autonomous check loop took **2 iterations** (one fixing pass) to go fully clean.
First pass caught a Y-depth overshoot (212 > 200 mm, from the heat-shield overhang) and
the large plates exceeding the 256 mm bed; both were fixed by removing the Y overhang
and splitting oversize plates into bolted halves. Final result: **all 31 checks pass**.
Full log and the PASS table are in `qa_report.md`.

**Single biggest honest risk, in one line:** PLA softens at ~55 °C and I'm putting the
electronics directly under a 200 °C+ hotend — if the thermal prototype shows the tray
runs hot, this concept doesn't go ahead.
