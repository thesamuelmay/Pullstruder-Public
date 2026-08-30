"""
STACKED DECK — parametric CAD for the Pullstruder PET-bottle filament recycler.
Concept: two vertical levels. Open TOP thermal deck (visible process) over an
enclosed BOTTOM electronics tray, separated by an inter-deck air gap + heat shield.
Highest-compactness / highest-risk candidate.

Coordinate system (millimetres):
  X = length  (thermal-path direction; winder cantilevers off the -X end)
  Y = depth
  Z = height  (Z=0 is the underside of the bottom tray)
Origin = front-left-bottom corner of the tray footprint.

All bought-in components are ACCURATE BOUNDING-BOX PLACEHOLDERS (stand-ins),
not real geometry. See design_decisions.md.

Run:  cd /tmp && uv run --python 3.12 --with cadquery python model.py
Outputs stacked_assembly.step / .stl next to this file, plus per-part STEP files
used by the QA checker.
"""

import os
import cadquery as cq

# =============================================================================
# PARAMETERS  (edit here — everything downstream is derived)
# =============================================================================

# ---- Build / material constraints -------------------------------------------
WALL          = 3.0     # nominal printed wall thickness (mm). >= MIN_WALL.
MIN_WALL      = 2.0     # PLA minimum designed wall (QA constraint #6)
BED           = 256.0   # mm  CONFIRMED school printer bed (256 mm cube build volume).
                        #   This is the real school printer's bed — settled, not an
                        #   assumption. Parameterised so every printed part is checked
                        #   against it.

# ---- Bolt scheme ------------------------------------------------------------
M3_CLEAR      = 3.4     # M3 clearance hole diameter
M4_CLEAR      = 4.5     # M4 clearance hole diameter
M3_NUT_AF     = 5.5     # M3 hex nut across-flats (captive-nut pocket width)
M3_NUT_T      = 2.4     # M3 nut thickness (pocket depth)
NUT_POCKET_W  = M3_NUT_AF + 0.4   # slight clearance for the nut

# ---- Footprint --------------------------------------------------------------
TRAY_L        = 290.0   # tray length (X)
TRAY_W        = 200.0   # tray depth  (Y)

# ---- Bottom tray (enclosed electronics box) ---------------------------------
TRAY_FLOOR_T  = 3.0     # tray floor thickness
TRAY_WALL_T   = 3.0     # tray side-wall thickness
TRAY_H        = 55.0    # internal clear height of the tray cavity
LID_T         = 3.0     # removable service lid thickness
LID_LIP       = 4.0     # lid locating lip depth into the tray
VENT_SLOT_W   = 4.0     # width of each side-wall vent slot
VENT_SLOT_H   = 30.0    # height of each side-wall vent slot
VENT_COUNT    = 6       # vent slots per long side wall

# ---- Inter-deck gap + heat shield (THE CRUX) --------------------------------
AIR_GAP       = 22.0    # air gap between tray lid top and heat-shield underside (mm)
SHIELD_T      = 4.0     # heat-shield plate thickness (printed PLA, foil-faced)
MIN_INTERDECK = 15.0    # QA minimum air gap (constraint #4); AIR_GAP must exceed
SHIELD_MARGIN_X = 4.0   # shield overhang in X only (slack on the 500 limit)
SHIELD_MARGIN_Y = 0.0   # NO Y overhang — hard 200 mm depth limit (constraint #1)

# ---- Sectioning (bed-fit) ---------------------------------------------------
# Large flat parts (tray/lid/shield/deck) exceed the 256 mm bed in X, so
# they are split into two X-halves joined by a bolted butt flange. See QA #3.
SPLIT_JOINT_BOLTS = 3   # M4 bolts across each split joint (through butting flanges)

# ---- Corner posts / standoffs (set the inter-deck gap) ----------------------
POST_SIZE     = 18.0    # square post cross-section (outer)
POST_INSET    = 16.0    # post centre inset from tray corner (X and Y)
# post height spans: tray lid plane -> top deck underside = AIR_GAP + SHIELD_T

# ---- Top thermal deck plate -------------------------------------------------
DECK_T        = 5.0     # top deck plate thickness (carries station loads)
DECK_L        = 290.0   # deck length (X) — matches tray
DECK_W        = 200.0   # deck depth  (Y)
PAD_H         = 6.0     # raised mount-pad height above deck top
PAD_SIZE      = 30.0    # mount-pad square footprint

# ---- Thermal-path station X positions (on the deck top, single centreline) --
# concept centreline: stripper(0) -> hotend(100) -> quench(150) -> Hall(220)
X_STRIPPER    = 35.0    # stripper station (shifted +35 so X=0 of path sits on deck)
X_HOTEND      = 135.0   # Volcano hotend, nozzle-down
X_QUENCH      = 185.0   # cooling fans / quench
X_HALL        = 255.0   # reserved Hall-sensor station (Phase-2)
DECK_CL_Y     = TRAY_W / 2.0   # path centreline in Y

# ---- Cantilever winder arm (off the -X end) ---------------------------------
WINDER_ARM_L  = 95.0    # how far the arm reaches past the chassis end (-X)
WINDER_ARM_W  = 40.0    # arm width (Y)
WINDER_ARM_T  = 10.0    # arm thickness (Z)
WINDER_GUSSET = 35.0    # vertical gusset height bolting arm to deck end plate

# =============================================================================
# DERIVED HEIGHTS  (the vertical stack)
# =============================================================================
Z_TRAY_FLOOR_TOP = TRAY_FLOOR_T
Z_TRAY_LID_BOT   = TRAY_FLOOR_T + TRAY_H          # top of cavity / underside of lid
Z_TRAY_LID_TOP   = Z_TRAY_LID_BOT + LID_T         # top surface of the closed lid
POST_H           = AIR_GAP + SHIELD_T             # corner post height
Z_SHIELD_BOT     = Z_TRAY_LID_TOP + AIR_GAP       # heat-shield underside
Z_SHIELD_TOP     = Z_SHIELD_BOT + SHIELD_T
Z_DECK_BOT       = Z_SHIELD_TOP                   # top deck sits on shield/posts
Z_DECK_TOP       = Z_DECK_BOT + DECK_T
Z_TOTAL          = Z_DECK_TOP + PAD_H             # overall stack height (pads on top)

# Original machine envelope for % comparison
ORIG_L, ORIG_W, ORIG_H = 554.0, 220.0, 325.0


# =============================================================================
# HELPERS
# =============================================================================
def captive_nut_pocket(wp, depth):
    """A hex pocket + clearance shaft for an M3 captive nut, cut from the
    current workplane face downward by `depth`."""
    return wp


def _post_centres():
    """XY centres of the four corner posts."""
    return [
        (POST_INSET, POST_INSET),
        (TRAY_L - POST_INSET, POST_INSET),
        (POST_INSET, TRAY_W - POST_INSET),
        (TRAY_L - POST_INSET, TRAY_W - POST_INSET),
    ]


# =============================================================================
# PRINTED PART 1 — BOTTOM ELECTRONICS TRAY (enclosed box, vented, open top)
# =============================================================================
def make_tray():
    outer_l = TRAY_L
    outer_w = TRAY_W
    outer_h = TRAY_FLOOR_T + TRAY_H
    # Solid outer block, then hollow the cavity from the top.
    tray = (
        cq.Workplane("XY")
        .box(outer_l, outer_w, outer_h, centered=(False, False, False))
    )
    # cavity
    cav = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_FLOOR_T)
        .moveTo(TRAY_WALL_T + (outer_l - 2 * TRAY_WALL_T) / 2.0,
                TRAY_WALL_T + (outer_w - 2 * TRAY_WALL_T) / 2.0)
        .box(outer_l - 2 * TRAY_WALL_T,
             outer_w - 2 * TRAY_WALL_T,
             TRAY_H + 1, centered=(True, True, False))
    )
    tray = tray.cut(cav)

    # Lid locating ledge: rebate the top inner edge so the lid lip drops in.
    rebate = (
        cq.Workplane("XY")
        .workplane(offset=Z_TRAY_LID_BOT - LID_LIP)
        .moveTo(outer_l / 2.0, outer_w / 2.0)
        .rect(outer_l - 2 * (TRAY_WALL_T - 1.0), outer_w - 2 * (TRAY_WALL_T - 1.0))
        .extrude(LID_LIP + 1)
    )
    # only cut the thin inner shoulder, not the whole wall: build a ring
    rebate_ring = rebate.cut(
        cq.Workplane("XY")
        .workplane(offset=Z_TRAY_LID_BOT - LID_LIP - 0.5)
        .moveTo(outer_l / 2.0, outer_w / 2.0)
        .rect(outer_l - 2 * TRAY_WALL_T - 2 * LID_LIP,
              outer_w - 2 * TRAY_WALL_T - 2 * LID_LIP)
        .extrude(LID_LIP + 2)
    )
    tray = tray.cut(rebate_ring)

    # Side-wall vent slots (both long Y-walls) for cross-flow ventilation.
    slot_pitch = outer_l / (VENT_COUNT + 1)
    slot_z = TRAY_FLOOR_T + (TRAY_H - VENT_SLOT_H) / 2.0
    for i in range(1, VENT_COUNT + 1):
        xc = i * slot_pitch
        for ywall in (0.0, outer_w):
            slot = (
                cq.Workplane("XY")
                .workplane(offset=slot_z)
                .moveTo(xc, ywall)
                .box(VENT_SLOT_W, TRAY_WALL_T * 3, VENT_SLOT_H,
                     centered=(True, True, False))
            )
            tray = tray.cut(slot)

    # Corner post bolt bosses on the tray top rim (M4 up into the posts).
    for (xc, yc) in _post_centres():
        hole = (
            cq.Workplane("XY")
            .workplane(offset=Z_TRAY_LID_BOT - 12)
            .moveTo(xc, yc)
            .circle(M4_CLEAR / 2.0)
            .extrude(20)
        )
        tray = tray.cut(hole)

    # Lid fixing holes in the top rim (M3, 6 around the perimeter).
    lid_holes = [
        (outer_l * 0.25, TRAY_WALL_T / 2.0),
        (outer_l * 0.75, TRAY_WALL_T / 2.0),
        (outer_l * 0.25, outer_w - TRAY_WALL_T / 2.0),
        (outer_l * 0.75, outer_w - TRAY_WALL_T / 2.0),
        (TRAY_WALL_T / 2.0, outer_w / 2.0),
        (outer_l - TRAY_WALL_T / 2.0, outer_w / 2.0),
    ]
    for (xc, yc) in lid_holes:
        h = (
            cq.Workplane("XY")
            .workplane(offset=Z_TRAY_LID_BOT - 14)
            .moveTo(xc, yc)
            .circle(M3_CLEAR / 2.0)
            .extrude(16)
        )
        tray = tray.cut(h)
    return tray, lid_holes


# =============================================================================
# PRINTED PART 2 — SERVICE LID (separate solid; removable for access)
# =============================================================================
def make_lid(lid_holes):
    outer_l = TRAY_L
    outer_w = TRAY_W
    # Main plate sits in the rebate; lip drops into the cavity mouth.
    plate = (
        cq.Workplane("XY")
        .workplane(offset=Z_TRAY_LID_BOT)
        .moveTo(outer_l / 2.0, outer_w / 2.0)
        .rect(outer_l - 2 * (TRAY_WALL_T - 1.0), outer_w - 2 * (TRAY_WALL_T - 1.0))
        .extrude(LID_T)
    )
    lip = (
        cq.Workplane("XY")
        .workplane(offset=Z_TRAY_LID_BOT - LID_LIP)
        .moveTo(outer_l / 2.0, outer_w / 2.0)
        .rect(outer_l - 2 * TRAY_WALL_T - 2 * LID_LIP,
              outer_w - 2 * TRAY_WALL_T - 2 * LID_LIP)
        .extrude(LID_LIP)
    )
    lid = plate.union(lip)
    # Finger pull recess (so the lid lifts out by hand for service).
    pull = (
        cq.Workplane("XY")
        .workplane(offset=Z_TRAY_LID_TOP - 1.2)
        .moveTo(outer_l / 2.0, outer_w / 2.0)
        .box(40, 12, 2.0, centered=(True, True, False))
    )
    lid = lid.cut(pull)
    # Lid fixing holes match the tray rim.
    for (xc, yc) in lid_holes:
        h = (
            cq.Workplane("XY")
            .workplane(offset=Z_TRAY_LID_BOT - 1)
            .moveTo(xc, yc)
            .circle(M3_CLEAR / 2.0)
            .extrude(LID_T + 2)
        )
        lid = lid.cut(h)
    return lid


# =============================================================================
# PRINTED PART 3 — FOUR CORNER POSTS (each is a separate identical printed part;
# built individually in build() so each is bed-checked on its own)
# =============================================================================
# (post geometry is generated inline in build(); see post_solids there)


# =============================================================================
# PRINTED PART 4 — HEAT-SHIELD PLATE (floor of the top deck zone)
# =============================================================================
def make_shield():
    sl = TRAY_L + 2 * SHIELD_MARGIN_X
    sw = TRAY_W + 2 * SHIELD_MARGIN_Y
    shield = (
        cq.Workplane("XY")
        .workplane(offset=Z_SHIELD_BOT)
        .moveTo(TRAY_L / 2.0, TRAY_W / 2.0)
        .rect(sl, sw)
        .extrude(SHIELD_T)
    )
    # Bolt holes over the posts.
    for (xc, yc) in _post_centres():
        h = (
            cq.Workplane("XY")
            .workplane(offset=Z_SHIELD_BOT - 1)
            .moveTo(xc, yc)
            .circle(M4_CLEAR / 2.0)
            .extrude(SHIELD_T + 2)
        )
        shield = shield.cut(h)
    return shield


# =============================================================================
# PRINTED PART 5 — TOP THERMAL DECK PLATE (with station mount pads + holes)
# =============================================================================
def make_deck():
    deck = (
        cq.Workplane("XY")
        .workplane(offset=Z_DECK_BOT)
        .moveTo(DECK_L / 2.0, DECK_W / 2.0)
        .rect(DECK_L, DECK_W)
        .extrude(DECK_T)
    )
    # Corner-post fixing holes.
    for (xc, yc) in _post_centres():
        h = (
            cq.Workplane("XY")
            .workplane(offset=Z_DECK_BOT - 1)
            .moveTo(xc, yc)
            .circle(M4_CLEAR / 2.0)
            .extrude(DECK_T + 2)
        )
        deck = deck.cut(h)

    # Raised mount pads at each station + M3 mounting holes through them.
    stations = [X_STRIPPER, X_HOTEND, X_QUENCH, X_HALL]
    for xs in stations:
        pad = (
            cq.Workplane("XY")
            .workplane(offset=Z_DECK_TOP)
            .moveTo(xs, DECK_CL_Y)
            .box(PAD_SIZE, PAD_SIZE, PAD_H, centered=(True, True, False))
        )
        deck = deck.union(pad)
        # 4 M3 holes per pad
        for dx in (-9, 9):
            for dy in (-9, 9):
                h = (
                    cq.Workplane("XY")
                    .workplane(offset=Z_DECK_BOT - 1)
                    .moveTo(xs + dx, DECK_CL_Y + dy)
                    .circle(M3_CLEAR / 2.0)
                    .extrude(DECK_T + PAD_H + 2)
                )
                deck = deck.cut(h)

    # Hotend nozzle pass-through slot (nozzle pokes DOWN through the deck; the
    # quench path is HORIZONTAL above the deck — filament never goes through).
    nozzle_slot = (
        cq.Workplane("XY")
        .workplane(offset=Z_DECK_BOT - 1)
        .moveTo(X_HOTEND, DECK_CL_Y)
        .circle(8.0)
        .extrude(DECK_T + PAD_H + 2)
    )
    deck = deck.cut(nozzle_slot)
    return deck


# =============================================================================
# PRINTED PART 6 — CANTILEVER WINDER ARM (off the -X end, bolted to deck end)
# =============================================================================
def make_winder_arm():
    # Vertical gusset bolting to the deck end plate (at X=0 face), then a
    # horizontal arm reaching out to -X to carry the spool axle.
    gusset = (
        cq.Workplane("XY")
        .workplane(offset=Z_DECK_BOT)
        .moveTo(0, DECK_CL_Y)
        .box(WALL * 3, WINDER_ARM_W, WINDER_GUSSET, centered=(True, True, False))
    )
    arm = (
        cq.Workplane("XY")
        .workplane(offset=Z_DECK_BOT)
        .moveTo(-WINDER_ARM_L / 2.0, DECK_CL_Y)
        .box(WINDER_ARM_L, WINDER_ARM_W, WINDER_ARM_T, centered=(True, True, False))
    )
    winder = gusset.union(arm)
    # Spool axle hole at the far end.
    axle = (
        cq.Workplane("YZ")
        .workplane(offset=-WINDER_ARM_L + 12)
        .moveTo(DECK_CL_Y, Z_DECK_BOT + WINDER_ARM_T / 2.0)
        .circle(4.0)
        .extrude(-30)
    )
    winder = winder.cut(axle)
    # Bolt holes through gusset into deck end.
    for dz in (8, WINDER_GUSSET - 8):
        for dy in (-12, 12):
            h = (
                cq.Workplane("XY")
                .workplane(offset=Z_DECK_BOT + dz)
                .moveTo(0, DECK_CL_Y + dy)
                .box(WALL * 6, M3_CLEAR, M3_CLEAR, centered=(True, True, True))
            )
            winder = winder.cut(h)
    return winder


# =============================================================================
# PLACEHOLDER COMPONENT BLOCKS  (bought-in; accurate bounding boxes; STAND-INS)
# =============================================================================
def _block(x, y, z, lx, ly, lz, centeredXY=True):
    """Axis-aligned placeholder block with its base at z."""
    return (
        cq.Workplane("XY")
        .workplane(offset=z)
        .moveTo(x, y)
        .box(lx, ly, lz, centered=(centeredXY, centeredXY, False))
    )


def make_placeholders():
    ph = {}

    # ---- TOP DECK components ----
    # Stripper assembly (approx block over the stripper pad)
    ph["stripper"] = _block(X_STRIPPER, DECK_CL_Y, Z_DECK_TOP + PAD_H,
                            40, 40, 45)
    # Volcano hotend body (~45x24x16) sitting on pad, nozzle ~30 DOWN through deck
    ph["hotend_body"] = _block(X_HOTEND, DECK_CL_Y, Z_DECK_TOP + PAD_H,
                               45, 24, 16)
    ph["hotend_nozzle"] = (
        cq.Workplane("XY")
        .workplane(offset=Z_DECK_BOT - 30)
        .moveTo(X_HOTEND, DECK_CL_Y)
        .circle(3.0).extrude(30 + DECK_T)
    )
    # 5015 blower fans (50x50x15) x2 at the quench station
    ph["fan_1"] = _block(X_QUENCH, DECK_CL_Y - 35, Z_DECK_TOP + PAD_H, 50, 50, 15)
    ph["fan_2"] = _block(X_QUENCH, DECK_CL_Y + 35, Z_DECK_TOP + PAD_H, 50, 50, 15)
    # Reserved Hall-sensor station placeholder (small block — Phase 2)
    ph["hall_station"] = _block(X_HALL, DECK_CL_Y, Z_DECK_TOP + PAD_H, 30, 30, 25)

    # ---- BOTTOM TRAY components (inside the enclosed cavity) ----
    floor = Z_TRAY_FLOOR_TOP
    # Arduino Uno 68.6x53.4x15 + CNC shield stacked +20 -> total ~35 tall
    ph["arduino"] = _block(70, 60, floor, 68.6, 53.4, 15)
    ph["cnc_shield"] = _block(70, 60, floor + 15, 68.6, 53.4, 20)
    # Sealed PSU ~129x98x38
    ph["psu"] = _block(200, 110, floor, 129, 98, 38)
    # 1602A LCD 80x36x12 (mounted to underside of lid, hanging down)
    ph["lcd"] = _block(70, 150, Z_TRAY_LID_BOT - 12, 80, 36, 12)

    # ---- WINDER spool placeholder (~200 dia x 60) on the cantilever axle ----
    ph["spool"] = (
        cq.Workplane("YZ")
        .workplane(offset=-WINDER_ARM_L + 12)
        .moveTo(DECK_CL_Y, Z_DECK_BOT + WINDER_ARM_T / 2.0)
        .circle(100).extrude(-60)
    )
    return ph


# =============================================================================
# SECTIONING — split an oversize part into two X-halves with a bolted joint
# =============================================================================
def split_in_x(obj, name):
    """If `obj` is longer than BED in X, cut it at mid-X into two halves and
    add M4 butt-joint bolt holes straddling the cut so the halves bolt back
    together. Returns a dict of {part_name: solid}. Otherwise returns the part
    unchanged. The cut is a plain butt joint (parts print flat, bolt edge-to-
    edge through aligned holes drilled near the seam)."""
    bb = obj.val().BoundingBox()
    if bb.xlen <= BED:
        return {name: obj}

    xmid = (bb.xmin + bb.xmax) / 2.0
    big = max(bb.xlen, bb.ylen, bb.zlen) + 10

    # Bolt holes straddling the seam (in Y, through the part thickness in Z is
    # awkward for thin plates, so we run M4 holes horizontally along X through
    # the seam — i.e. the two halves are edge-bolted). Model them as X-axis
    # cylinders near the seam, spread across Y.
    ys = [bb.ymin + (i + 1) * bb.ylen / (SPLIT_JOINT_BOLTS + 1)
          for i in range(SPLIT_JOINT_BOLTS)]
    zc = (bb.zmin + bb.zmax) / 2.0

    def add_seam_holes(half):
        for yy in ys:
            hole = (
                cq.Workplane("YZ")
                .workplane(offset=xmid - 14)
                .moveTo(yy, zc)
                .circle(M4_CLEAR / 2.0)
                .extrude(28)
            )
            half = half.cut(hole)
        return half

    half_a = obj.intersect(
        cq.Workplane("XY").moveTo(xmid - big / 2.0, 0)
        .box(big, big * 2, big * 2, centered=(True, True, True)))
    half_b = obj.intersect(
        cq.Workplane("XY").moveTo(xmid + big / 2.0, 0)
        .box(big, big * 2, big * 2, centered=(True, True, True)))

    half_a = add_seam_holes(half_a)
    half_b = add_seam_holes(half_b)
    return {f"{name}_A": half_a, f"{name}_B": half_b}


# =============================================================================
# BUILD + EXPORT
# =============================================================================
def build():
    tray, lid_holes = make_tray()
    lid = make_lid(lid_holes)
    shield = make_shield()
    deck = make_deck()
    winder = make_winder_arm()
    placeholders = make_placeholders()

    # Posts: FOUR separate identical printed parts (each tiny, always bed-safe).
    post_solids = []
    for (xc, yc) in _post_centres():
        p = (
            cq.Workplane("XY")
            .workplane(offset=Z_TRAY_LID_TOP)
            .moveTo(xc, yc)
            .box(POST_SIZE, POST_SIZE, POST_H, centered=(True, True, False))
        )
        hole = (
            cq.Workplane("XY")
            .workplane(offset=Z_TRAY_LID_TOP - 1)
            .moveTo(xc, yc)
            .circle(M4_CLEAR / 2.0)
            .extrude(POST_H + 2)
        )
        post_solids.append(p.cut(hole))

    printed = {}
    # Section the large flat parts for bed-fit.
    printed.update(split_in_x(tray, "tray"))
    printed.update(split_in_x(lid, "lid"))
    printed.update(split_in_x(shield, "shield"))
    printed.update(split_in_x(deck, "deck"))
    printed["winder_arm"] = winder
    for i, ps in enumerate(post_solids, start=1):
        printed[f"post_{i}"] = ps

    return printed, placeholders


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    printed, placeholders = build()

    # Per-part STEP exports (QA loads these individually).
    for name, obj in printed.items():
        cq.exporters.export(obj, os.path.join(here, f"part_{name}.step"))

    # Combined assembly (printed parts + placeholders) as one compound.
    asm = cq.Assembly()
    for name, obj in printed.items():
        asm.add(obj, name=name, color=cq.Color(0.2, 0.5, 0.9))
    for name, obj in placeholders.items():
        asm.add(obj, name=f"PLACEHOLDER_{name}", color=cq.Color(0.8, 0.3, 0.3))

    asm.save(os.path.join(here, "stacked_assembly.step"))

    # STL of the whole thing (fuse everything into one compound for meshing).
    all_solids = list(printed.values()) + list(placeholders.values())
    compound = all_solids[0]
    for s in all_solids[1:]:
        compound = compound.union(s) if False else compound  # keep separate
    # Build a true compound for STL without booleans (faster, robust):
    from cadquery import Compound
    shapes = [o.val() for o in all_solids]
    comp = Compound.makeCompound(shapes)
    cq.exporters.export(cq.Workplane("XY").newObject([comp]),
                        os.path.join(here, "stacked_assembly.stl"))

    # Report derived stack geometry.
    print("Z stack (mm):")
    print(f"  tray floor top   = {Z_TRAY_FLOOR_TOP}")
    print(f"  tray lid top     = {Z_TRAY_LID_TOP}")
    print(f"  air gap          = {AIR_GAP}  (min {MIN_INTERDECK})")
    print(f"  shield bot/top   = {Z_SHIELD_BOT} / {Z_SHIELD_TOP}")
    print(f"  deck bot/top     = {Z_DECK_BOT} / {Z_DECK_TOP}")
    print(f"  total height     = {Z_TOTAL}")
    print("Exports written to", here)


if __name__ == "__main__":
    main()
