"""
Pullstruder — "Spine + Clip-On Modules" concept (RECOMMENDED).

Parametric CadQuery model of the NEW printed parts plus accurate bounding-box
PLACEHOLDER blocks for bought components.

Author: generated for Samuel's VCE SE SAT (concept stage).
Units: millimetres throughout (SI).

Coordinate system (AS1100 datum = spine origin):
  X = machine centreline (filament travel direction). X=0 at stripper datum.
  Y = lateral (width).  Y=0 = spine web centre plane.
  Z = vertical (height). Z=0 = underside of spine (bottom of cable channel).

All printed parts are authored as separate solids so each can be validity-checked
and bed-checked independently. Placeholder component blocks are authored separately
and tagged 'PLACEHOLDER_*' so they are never confused with printed geometry.
"""

import cadquery as cq

# ===========================================================================
# PARAMETERS  (edit here — everything downstream is derived)
# ===========================================================================

# ---- Global / manufacturing ----
WALL_MIN        = 2.0     # mm  minimum designed PLA wall (QA assert >= this)
BED             = 256.0   # mm  CONFIRMED school printer bed (256 mm cube build volume).
CLEARANCE       = 0.3     # mm  printed clip slide-fit clearance (slot larger than rail)

# ---- Spine cross-section (I-section beam) ----
# I-section: top flange (mounting deck) + vertical web + bottom flange that
# forms the lid of the cable channel. Cable channel is the hollow box slung
# under the web between the flanges.
SPINE_LEN       = 380.0   # mm  total centreline length (target footprint length)
FLANGE_W        = 60.0    # mm  flange width (Y) — gives modules a wide seat
FLANGE_T        = 6.0     # mm  flange thickness (Z) — > WALL_MIN, takes captive nuts
WEB_T           = 6.0     # mm  web thickness (Y)
SPINE_H         = 70.0    # mm  overall section height (Z), incl. flanges + channel

# ---- Integrated cable channel (raceway) ----
# The raceway is the hollow under the web. Clear internal section must fit the
# 12V harness. Concept states >= 8x8 mm clear minimum.
CHAN_CLEAR_W    = 16.0    # mm  clear channel width  (Y) — >= 8 required
CHAN_CLEAR_H    = 14.0    # mm  clear channel height (Z) — >= 8 required
CHAN_WALL       = 2.5     # mm  channel wall thickness (>= WALL_MIN)
COVER_LIP       = 1.5     # mm  snap-cover retaining lip
COVER_T         = 2.5     # mm  snap cover thickness

# ---- Spine splice (bolted, mid-length) ----
# Because SPINE_LEN (380) > BED (256), the spine prints as 2 segments joined by
# a bolted splice plate. Splice is offset from centre to avoid the hotend high-
# load zone (hotend at X~75). Both segments must each be < BED.
# Segment A runs from SPINE_X_MIN..SPLICE_X; we choose SPLICE_X so both halves
# clear the bed with margin (see derived check below).
SPLICE_X        = 130.0   # mm  splice plane X position (keeps both segments < bed)
SPLICE_PLATE_L  = 60.0    # mm  splice plate length spanning the joint
SPLICE_PLATE_T  = 5.0     # mm  splice plate thickness
SPLICE_BOLTS    = 4       # M4 bolts through the splice

# ---- Module-clip interface (keyed dovetail-ish tongue + slot) ----
# The spine top flange carries a raised KEY RAIL running along X. Each module
# has a matching KEY SLOT on its underside. Slot = rail + 2*CLEARANCE so it
# slides on and seats to a hard stop. This is the parametric mate the QA checks.
RAIL_W          = 12.0    # mm  key rail width (Y)
RAIL_H          = 4.0     # mm  key rail height (Z above flange)
SLOT_W          = RAIL_W + 2 * CLEARANCE   # derived — module slot width
SLOT_H          = RAIL_H + CLEARANCE       # derived — module slot depth

# ---- Module common geometry ----
MOD_WALL        = 3.0     # mm  module body wall (>= WALL_MIN)
MOD_BASE_T      = 6.0     # mm  module base plate thickness (holds captive nuts + slot)
MOD_W           = 56.0    # mm  module footprint width (Y) — sits within flange
BOLT_M4         = 4.0     # mm  clearance for M4 (use 4.3 hole)
BOLT_M3         = 3.0     # mm  clearance for M3 (use 3.2 hole)
HOLE_M4         = 4.3
HOLE_M3         = 3.2
NUT_M4_AF       = 7.0     # mm  M4 nut across-flats (captive pocket)
NUT_M4_T        = 3.2     # mm  M4 nut thickness (pocket depth)
NUT_M3_AF       = 5.5
NUT_M3_T        = 2.4

# ---- Station X positions (centreline) ----
# Spaced so module footprints (below) do NOT overlap along X (QA gate 4).
X_STRIPPER      = 0.0
X_HOTEND        = 70.0
X_COOLING       = 120.0
X_HALL          = 180.0   # Phase-2 reserved (must stay free)
X_CONTROLLER    = -50.0   # controller / winder end (riser foot)

# ---- Module body sizes (length along X) ----
# Sized so neighbours do NOT bbox-overlap along the spine (QA check 4).
# Gaps: strip(-22..22) hot(45..95) cool(102..138) hall(160..200) -> no overlap.
STRIP_L         = 44.0
HOTEND_L        = 50.0
COOL_L          = 36.0
HALL_L          = 40.0
MOD_TOP_H       = 30.0    # nominal module body height above flange deck

# ---- Hotend thermal standoff ----
# PLA softens ~60C; Volcano runs hot. Module lifts the hotend on a tall standoff
# and the immediate cradle is a separate clipped piece (printed in higher-temp
# material in reality). Modelled here as standoff height.
HOTEND_STANDOFF = 25.0    # mm  vertical standoff lifting hotend off PLA deck

# ---- Winder riser (L-fold, vertical) ----
RISER_W         = 50.0    # mm  (Y)
RISER_T         = 12.0    # mm  (X thickness of the riser plate)
RISER_H         = 175.0   # mm  vertical height to carry spool above
RISER_FOOT_L    = 60.0    # mm  foot that clips/bolts to the spine end

# ===========================================================================
# DERIVED REFERENCE PLANES
# ===========================================================================
FLANGE_TOP_Z    = SPINE_H                  # top of top flange (mounting deck)
DECK_Z          = FLANGE_TOP_Z             # modules register their slot here
RAIL_TOP_Z      = DECK_Z + RAIL_H

# Channel sits in the lower portion of the section.
CHAN_OUTER_W    = CHAN_CLEAR_W + 2 * CHAN_WALL
CHAN_OUTER_H    = CHAN_CLEAR_H + 2 * CHAN_WALL


# ===========================================================================
# PRINTED PART: SPINE SEGMENT (generic builder, used for both segments)
# ===========================================================================
def build_spine_segment(x_start, x_end):
    """Build one I-section spine segment from x_start..x_end (centreline).

    Cross-section (looking down +X), Z increasing up:
      - top flange:    FLANGE_W wide, FLANGE_T thick, at top
      - key rail:      RAIL_W wide, RAIL_H tall, centred on top flange
      - web:           WEB_T wide, spanning between flanges
      - channel box:   CHAN_OUTER hollow box at the bottom = raceway
      - flange slot:   a slot through the top flange for leads to drop in
    """
    seg_len = x_end - x_start
    x_mid = (x_start + x_end) / 2.0

    # --- Build the cross-section as a 2D profile in the Y-Z plane, extrude in X.
    # We assemble by boolean union of prisms for clarity & robustness.

    # Top flange (deck)
    flange = (
        cq.Workplane("XY")
        .box(seg_len, FLANGE_W, FLANGE_T, centered=(True, True, False))
        .translate((x_mid, 0, FLANGE_TOP_Z - FLANGE_T))
    )

    # Key rail on top of the deck (runs full segment length)
    rail = (
        cq.Workplane("XY")
        .box(seg_len, RAIL_W, RAIL_H, centered=(True, True, False))
        .translate((x_mid, 0, DECK_Z))
    )

    # Channel outer box (the raceway shell) sits at the bottom
    chan_outer = (
        cq.Workplane("XY")
        .box(seg_len, CHAN_OUTER_W, CHAN_OUTER_H, centered=(True, True, False))
        .translate((x_mid, 0, 0))
    )

    # Web connects top flange down to the channel box
    web_bottom = CHAN_OUTER_H
    web_top = FLANGE_TOP_Z - FLANGE_T
    web_h = web_top - web_bottom
    web = (
        cq.Workplane("XY")
        .box(seg_len, WEB_T, web_h, centered=(True, True, False))
        .translate((x_mid, 0, web_bottom))
    )

    solid = flange.union(rail).union(chan_outer).union(web)

    # --- Hollow out the channel (clear bore) ---
    # Leave the bottom + sides as walls; open the TOP of the channel into the web
    # region so leads drop in, but keep a snap-cover lip. We model the clear bore
    # then a cover-lip rebate.
    bore = (
        cq.Workplane("XY")
        .box(seg_len + 1, CHAN_CLEAR_W, CHAN_CLEAR_H, centered=(True, True, False))
        .translate((x_mid, 0, CHAN_WALL))
    )
    solid = solid.cut(bore)

    # --- Lead-drop slots through the top flange + web at each station in range ---
    # A vertical slot lets each module's leads pass from deck into the channel.
    for sx in [X_STRIPPER, X_HOTEND, X_COOLING, X_HALL, X_CONTROLLER]:
        if x_start + 8 < sx < x_end - 8:
            slot = (
                cq.Workplane("XY")
                .box(10.0, 6.0, FLANGE_TOP_Z, centered=(True, True, False))
                .translate((sx, 0, CHAN_WALL))
            )
            solid = solid.cut(slot)

    # --- Captive-nut pockets + bolt holes in the top flange at station positions ---
    # Two M4 pads per station (straddling the rail in Y).
    for sx in [X_STRIPPER, X_HOTEND, X_COOLING, X_HALL]:
        if x_start <= sx <= x_end:
            for yoff in (+ (RAIL_W/2 + 9), - (RAIL_W/2 + 9)):
                # through hole for the bolt
                hole = (
                    cq.Workplane("XY")
                    .circle(HOLE_M4 / 2)
                    .extrude(FLANGE_T + 1)
                    .translate((sx, yoff, FLANGE_TOP_Z - FLANGE_T - 0.5))
                )
                solid = solid.cut(hole)
                # hex captive-nut pocket recessed from underside of flange
                nut = (
                    cq.Workplane("XY")
                    .polygon(6, NUT_M4_AF / 0.866)  # circumscribed for AF
                    .extrude(NUT_M4_T)
                    .translate((sx, yoff, FLANGE_TOP_Z - FLANGE_T))
                )
                solid = solid.cut(nut)

    # --- Splice bolt holes if the splice plane is within this segment's end ---
    # (handled on the splice plate; the segment ends get matching through-holes)
    if abs(x_end - SPLICE_X) < 1 or abs(x_start - SPLICE_X) < 1:
        for i in range(SPLICE_BOLTS):
            # holes along the web near the splice end
            xb = (x_end - 15) if abs(x_end - SPLICE_X) < 1 else (x_start + 15)
            zb = CHAN_OUTER_H + web_h * (0.25 + 0.5 * (i % 2))
            yb = 0
            hole = (
                cq.Workplane("YZ")
                .circle(HOLE_M4 / 2)
                .extrude(WEB_T + 4)
                .translate((xb - (WEB_T + 4) / 2 + (i * 6 - 9), yb, zb))
            )
            solid = solid.cut(hole)

    return solid


# ===========================================================================
# PRINTED PART: SNAP COVER (one per segment, runs the channel length)
# ===========================================================================
def build_cover(x_start, x_end):
    seg_len = x_end - x_start
    x_mid = (x_start + x_end) / 2.0
    cover = (
        cq.Workplane("XY")
        .box(seg_len, CHAN_OUTER_W, COVER_T, centered=(True, True, False))
        .translate((x_mid, 0, CHAN_OUTER_H + 1.0))  # sits just above channel, exploded up for view
    )
    # retaining lips
    for yoff in (CHAN_CLEAR_W / 2, -CHAN_CLEAR_W / 2):
        lip = (
            cq.Workplane("XY")
            .box(seg_len, COVER_LIP, COVER_LIP, centered=(True, True, False))
            .translate((x_mid, yoff, CHAN_OUTER_H + 1.0 - COVER_LIP))
        )
        cover = cover.union(lip)
    return cover


# ===========================================================================
# PRINTED PART: SPLICE PLATE (bolts the two segments together)
# ===========================================================================
def build_splice_plate():
    plate = (
        cq.Workplane("XY")
        .box(SPLICE_PLATE_L, WEB_T, 40.0, centered=(True, True, False))
        .translate((SPLICE_X, WEB_T / 2 + 0.5, CHAN_OUTER_H + 5))
    )
    # bolt holes matching segment ends
    for i in range(SPLICE_BOLTS):
        xb = SPLICE_X + (i * 6 - 9)
        zb = CHAN_OUTER_H + 5 + 40.0 * (0.25 + 0.5 * (i % 2))
        hole = (
            cq.Workplane("YZ")
            .circle(HOLE_M4 / 2)
            .extrude(WEB_T + 6)
            .translate((xb - (WEB_T + 6) / 2, WEB_T / 2 + 0.5, zb))
        )
        plate = plate.cut(hole)
    return plate


# ===========================================================================
# PRINTED PART: GENERIC CLIP-ON MODULE BODY
# ===========================================================================
def build_module(x_center, length, top_h, with_standoff=0.0, label=""):
    """A clip-on module: base plate with keyed slot underside + captive-nut pads,
    walls forming an open cradle, optional standoff to lift hardware off PLA.
    Returns (solid, slot_dims_dict) so QA can verify the mate.
    """
    x0 = x_center
    # Base plate sits ON the deck, straddling the rail
    base = (
        cq.Workplane("XY")
        .box(length, MOD_W, MOD_BASE_T, centered=(True, True, False))
        .translate((x0, 0, DECK_Z))
    )

    # Key SLOT cut in the underside of the base — mates with spine rail.
    slot = (
        cq.Workplane("XY")
        .box(length + 1, SLOT_W, SLOT_H, centered=(True, True, False))
        .translate((x0, 0, DECK_Z - 0.001))
    )
    body = base.cut(slot)

    # Side walls (cradle) rising from the base
    for yoff in (MOD_W / 2 - MOD_WALL / 2, -(MOD_W / 2 - MOD_WALL / 2)):
        wall = (
            cq.Workplane("XY")
            .box(length, MOD_WALL, top_h, centered=(True, True, False))
            .translate((x0, yoff, DECK_Z + MOD_BASE_T))
        )
        body = body.union(wall)
    # End wall (one end, leaves the filament path open through the other)
    endwall = (
        cq.Workplane("XY")
        .box(MOD_WALL, MOD_W, top_h, centered=(True, True, False))
        .translate((x0 - length / 2 + MOD_WALL / 2, 0, DECK_Z + MOD_BASE_T))
    )
    body = body.union(endwall)

    # Optional thermal standoff posts (for hotend) lifting a top cradle plate
    if with_standoff > 0:
        for xoff in (length / 2 - 8, -(length / 2 - 8)):
            for yoff in (MOD_W / 2 - 6, -(MOD_W / 2 - 6)):
                post = (
                    cq.Workplane("XY")
                    .box(6, 6, with_standoff, centered=(True, True, False))
                    .translate((x0 + xoff, yoff, DECK_Z + MOD_BASE_T + top_h))
                )
                body = body.union(post)
        cradle = (
            cq.Workplane("XY")
            .box(length, MOD_W, MOD_BASE_T, centered=(True, True, False))
            .translate((x0, 0, DECK_Z + MOD_BASE_T + top_h + with_standoff))
        )
        body = body.union(cradle)

    # Bolt clearance holes through base to meet the spine captive nuts
    for yoff in (+ (RAIL_W/2 + 9), - (RAIL_W/2 + 9)):
        hole = (
            cq.Workplane("XY")
            .circle(HOLE_M4 / 2)
            .extrude(MOD_BASE_T + 2)
            .translate((x0, yoff, DECK_Z - 0.5))
        )
        body = body.cut(hole)

    slot_dims = {"width": SLOT_W, "height": SLOT_H}
    return body, slot_dims


# ===========================================================================
# PRINTED PART: WINDER RISER (L-fold vertical)
# ===========================================================================
def build_riser():
    # Foot that bolts to the controller end of the spine
    foot = (
        cq.Workplane("XY")
        .box(RISER_FOOT_L, RISER_W, MOD_BASE_T, centered=(True, True, False))
        .translate((X_CONTROLLER, 0, DECK_Z))
    )
    # Keyed slot in foot underside (same mate as modules)
    slot = (
        cq.Workplane("XY")
        .box(RISER_FOOT_L + 1, SLOT_W, SLOT_H, centered=(True, True, False))
        .translate((X_CONTROLLER, 0, DECK_Z - 0.001))
    )
    foot = foot.cut(slot)
    # Vertical riser plate rising from the foot's controller-end
    riser_x = X_CONTROLLER - RISER_FOOT_L / 2 + RISER_T / 2
    riser = (
        cq.Workplane("XY")
        .box(RISER_T, RISER_W, RISER_H, centered=(True, True, False))
        .translate((riser_x, 0, DECK_Z + MOD_BASE_T))
    )
    # Gusset for stiffness (triangle-ish via tapered box approximation -> use a wedge)
    gusset = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(40, 0)
        .lineTo(0, 60)
        .close()
        .extrude(12)
        .translate((riser_x + RISER_T/2, -6, DECK_Z + MOD_BASE_T))
    )
    body = foot.union(riser).union(gusset)
    # Spool axle boss near top of riser, aligned with the spool placeholder centre
    boss_z = DECK_Z + MOD_BASE_T + RISER_H - 100
    boss = (
        cq.Workplane("XZ")
        .circle(10)
        .extrude(40)
        .translate((riser_x, 0, boss_z))
    )
    body = body.union(boss)
    # bolt holes in foot
    for yoff in (+ (RAIL_W/2 + 9), - (RAIL_W/2 + 9)):
        hole = (
            cq.Workplane("XY")
            .circle(HOLE_M4 / 2)
            .extrude(MOD_BASE_T + 2)
            .translate((X_CONTROLLER, yoff, DECK_Z - 0.5))
        )
        body = body.cut(hole)
    return body


# ===========================================================================
# PLACEHOLDER COMPONENT BLOCKS (bought parts — bounding boxes, clearly stand-ins)
# ===========================================================================
def ph_box(l, w, h, x, y, z):
    return (
        cq.Workplane("XY")
        .box(l, w, h, centered=(True, True, False))
        .translate((x, y, z))
    )

def build_placeholders():
    ph = {}
    deck = DECK_Z + RAIL_H  # parts sit roughly on the deck/module tops

    # NEMA17 42x42x48 + 5mm shaft — LOW at the controller end, mounted to the
    # riser foot. It is the filament PULLER (drives the strand along the
    # centreline); the spool sits up high to take up slack. Shaft points +X
    # along the centreline toward the puller wheel.
    nema_z = DECK_Z + MOD_BASE_T + 4
    nema = ph_box(42, 42, 48, X_CONTROLLER - 5, 0, nema_z)
    shaft = (cq.Workplane("YZ").circle(2.5).extrude(20)
             .translate((X_CONTROLLER - 5 + 21, 0, nema_z + 24)))
    ph["PLACEHOLDER_NEMA17"] = nema.union(shaft)

    # Volcano hotend ~45x24x16 + ~30 nozzle DOWN — on hotend module cradle
    hot_z = DECK_Z + MOD_BASE_T + MOD_TOP_H + HOTEND_STANDOFF + MOD_BASE_T
    hot_body = ph_box(45, 24, 16, X_HOTEND, 0, hot_z)
    nozzle = (cq.Workplane("XY").circle(4).extrude(-30)
              .translate((X_HOTEND, 0, hot_z)))
    ph["PLACEHOLDER_VOLCANO_HOTEND"] = hot_body.union(nozzle)

    # Arduino Uno 68.6x53.4x15 — controller end, on deck
    ph["PLACEHOLDER_ARDUINO_UNO"] = ph_box(68.6, 53.4, 15, X_CONTROLLER + 40, -45, DECK_Z)

    # CNC Shield stacked +20 above Arduino
    ph["PLACEHOLDER_CNC_SHIELD"] = ph_box(68.6, 53.4, 20, X_CONTROLLER + 40, -45, DECK_Z + 15)

    # Sealed PSU ~129x98x38 — controller end, opposite side
    ph["PLACEHOLDER_PSU_SEALED"] = ph_box(129, 98, 38, X_CONTROLLER + 55, 55, DECK_Z)

    # 5015 blower fans 50x50x15 x2 — cooling module
    ph["PLACEHOLDER_FAN_5015_A"] = ph_box(50, 50, 15, X_COOLING, 18, DECK_Z + MOD_BASE_T + MOD_TOP_H)
    ph["PLACEHOLDER_FAN_5015_B"] = ph_box(50, 50, 15, X_COOLING, -18, DECK_Z + MOD_BASE_T + MOD_TOP_H)

    # 1602A LCD 80x36x12 — front, near controller, raised on deck
    ph["PLACEHOLDER_LCD_1602A"] = ph_box(80, 36, 12, X_CONTROLLER + 30, -70, DECK_Z + 20)

    # Spool ~200 dia x 60 — up on the riser axle.
    # Axle runs along Y (across machine width) so the 60 mm spool THICKNESS sets
    # width (W budget is tight at 200) and the 200 dia goes into X (length, budget
    # 500) and Z (height). Disc centre sits so its top stays under the Z limit.
    spool_cz = DECK_Z + MOD_BASE_T + RISER_H - 100   # centre Z so top ~ +100
    spool = (cq.Workplane("XZ").circle(95).extrude(56)
             .translate((X_CONTROLLER - 30, 28, spool_cz)))
    ph["PLACEHOLDER_SPOOL"] = spool

    return ph


# ===========================================================================
# BUILD EVERYTHING
# ===========================================================================
def build_all():
    printed = {}

    # Two spine segments split at the splice plane
    printed["spine_segment_A"] = build_spine_segment(X_CONTROLLER - RISER_FOOT_L/2 - 10, SPLICE_X)
    printed["spine_segment_B"] = build_spine_segment(SPLICE_X, SPLICE_X + (SPINE_LEN - (SPLICE_X - (X_CONTROLLER - RISER_FOOT_L/2 - 10))))
    printed["splice_plate"]    = build_splice_plate()

    # Covers (one per segment)
    printed["cover_A"] = build_cover(X_CONTROLLER - RISER_FOOT_L/2 - 10, SPLICE_X)
    printed["cover_B"] = build_cover(SPLICE_X, SPLICE_X + (SPINE_LEN - (SPLICE_X - (X_CONTROLLER - RISER_FOOT_L/2 - 10))))

    # Modules
    m_strip, strip_slot = build_module(X_STRIPPER, STRIP_L, MOD_TOP_H, label="stripper")
    m_hot, hot_slot     = build_module(X_HOTEND, HOTEND_L, MOD_TOP_H, with_standoff=HOTEND_STANDOFF, label="hotend")
    m_cool, cool_slot   = build_module(X_COOLING, COOL_L, MOD_TOP_H, label="cooling")
    m_hall, hall_slot   = build_module(X_HALL, HALL_L, MOD_TOP_H, label="hall")
    printed["module_stripper"] = m_strip
    printed["module_hotend"]   = m_hot
    printed["module_cooling"]  = m_cool
    printed["module_hall_reserved"] = m_hall

    printed["winder_riser"] = build_riser()

    placeholders = build_placeholders()

    slot_dims = {
        "stripper": strip_slot, "hotend": hot_slot,
        "cooling": cool_slot, "hall": hall_slot,
    }
    rail_dims = {"width": RAIL_W, "height": RAIL_H}
    return printed, placeholders, slot_dims, rail_dims


if __name__ == "__main__":
    import sys
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."

    printed, placeholders, slot_dims, rail_dims = build_all()

    # Compose a single assembly for STEP/STL export
    asm = cq.Assembly(name="pullstruder_spine")
    for name, solid in printed.items():
        asm.add(solid, name=name, color=cq.Color(0.2, 0.5, 0.9))
    for name, solid in placeholders.items():
        asm.add(solid, name=name, color=cq.Color(0.8, 0.3, 0.3))

    step_path = f"{outdir}/spine_assembly.step"
    stl_path = f"{outdir}/spine_assembly.stl"
    asm.save(step_path)

    # STL: combine all solids into one compound
    compound = printed["spine_segment_A"]
    for name, solid in list(printed.items())[1:]:
        compound = compound.union(solid) if False else compound  # keep separate; export compound below
    # Build a true compound for STL
    from cadquery import exporters
    all_solids = list(printed.values()) + list(placeholders.values())
    comp = all_solids[0]
    for s in all_solids[1:]:
        comp = comp.add(s) if hasattr(comp, "add") else comp
    # Simplest robust STL: union printed parts only (placeholders optional)
    union_printed = printed["spine_segment_A"]
    for name in list(printed.keys())[1:]:
        try:
            union_printed = union_printed.union(printed[name])
        except Exception:
            pass
    # export full assembly to STL via toCompound
    try:
        comp_shape = asm.toCompound()
        exporters.export(comp_shape, stl_path)
    except Exception as e:
        exporters.export(union_printed, stl_path)
        print(f"STL fallback used: {e}")

    print(f"Wrote {step_path}")
    print(f"Wrote {stl_path}")
    print(f"Printed parts: {len(printed)}  Placeholders: {len(placeholders)}")
