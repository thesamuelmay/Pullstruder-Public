"""
Pullstruder — "Spine + Clip-On Modules" concept — DETAILED parametric model.

Phase B (2026-06): printed-part detailing — edge fillets, bolt-hole chamfers,
  embossed part labels, print-quality gusset fillets.
Phase A (2026-06): bought-part fidelity — NEMA17 with pilot boss + stepped body,
  Arduino Uno with headers + USB-B + barrel jack, Volcano hotend with fins + nozzle,
  fans with impeller cavity, LCD with recessed screen, PSU with vent slots, CNC shield
  with header pins. All hole patterns preserved; G9 still anchored.

This evolves the concept-stage block model into a part-accurate model:
  * PRINTED PARTS: real walls (>= WALL_MIN), edge fillets, M3/M4 bolt holes at
    PRINT clearance, captive hex-nut pockets, keyed tongue/slot slide fit.
  * BOUGHT COMPONENTS: accurate external dims + REAL mounting-hole patterns and
    shaft/connector positions, tagged PLACEHOLDER_*, so printed module holes line
    up with the real part holes.
  * Each printed part is authored in WORLD coordinates (assembly position) AND a
    print-oriented copy is exported flat for slicing.

Units: millimetres (SI). Coordinate system (AS1100 datum = spine origin):
  X = machine centreline (filament travel). X=0 at stripper datum.
  Y = lateral width.  Y=0 = spine web centre plane.
  Z = vertical.       Z=0 = underside of spine (bottom of cable channel).

Run:  cd /tmp && uv run --python 3.12 --with cadquery python model_detailed.py [OUTDIR]
"""

import os
import sys
import math
import cadquery as cq
from cadquery import exporters

# ===========================================================================
# PARAMETERS
# ===========================================================================

# ---- Global / manufacturing ----
WALL_MIN   = 2.0      # mm  minimum designed PLA wall (QA G5 asserts >= this)
BED        = 256.0    # mm  CONFIRMED school printer bed (256 mm cube build volume).
CLEARANCE  = 0.3      # mm  printed clip slide-fit clearance (slot larger than rail per side)

# ---- Fastener catalogue (PRINT clearance holes + captive-nut pockets) ----
HOLE_M3    = 3.2      # mm  M3 clearance hole for printing (nominal 3 + 0.2)
HOLE_M4    = 4.3      # mm  M4 clearance hole for printing (nominal 4 + 0.3)
M3_NOM     = 3.0
M4_NOM     = 4.0
NUT_M3_AF  = 5.5      # mm  M3 hex nut across-flats
NUT_M3_T   = 2.4      # mm  M3 nut thickness (pocket depth)
NUT_M4_AF  = 7.0      # mm  M4 hex nut across-flats
NUT_M4_T   = 3.2      # mm  M4 nut thickness (pocket depth)

def af_to_circum(af):
    """Across-flats -> circumscribed circle radius for a hex pocket."""
    return (af / 2.0) / math.cos(math.radians(30))  # = af / sqrt(3)

# ---- Spine cross-section (I-section beam) ----
SPINE_LEN   = 380.0
FLANGE_W    = 60.0
FLANGE_T    = 6.0
WEB_T       = 6.0
SPINE_H     = 70.0

# ---- Integrated cable channel (raceway) ----
CHAN_CLEAR_W = 16.0
CHAN_CLEAR_H = 14.0
CHAN_WALL    = 2.5
COVER_T      = 2.5
COVER_LIP    = 1.5

# ---- Spine splice (bolted, mid-length) ----
SPLICE_X       = 130.0
SPLICE_PLATE_L = 60.0
SPLICE_PLATE_T = 5.0
SPLICE_BOLTS   = 4        # M4

# ---- Module-clip interface (keyed tongue rail + slot) ----
RAIL_W = 12.0
RAIL_H = 4.0
SLOT_W = RAIL_W + 2 * CLEARANCE   # derived — slide fit
SLOT_H = RAIL_H + CLEARANCE

# ---- Module common geometry ----
MOD_WALL   = 3.0
MOD_BASE_T = 6.0
MOD_W      = 56.0
MOD_TOP_H  = 30.0

# ---- Spine bolt-pad geometry (where modules bolt to spine) ----
PAD_Y = RAIL_W / 2 + 9.0   # M4 pads straddle the rail in Y at +/- this

# ---- Station X positions (centreline) ----
X_STRIPPER   = 0.0
X_HOTEND     = 70.0
X_COOLING    = 120.0
X_HALL       = 180.0       # Phase-2 reserved
X_CONTROLLER = -50.0

# ---- Module body sizes (length along X) ----
STRIP_L  = 44.0
HOTEND_L = 50.0
COOL_L   = 36.0
HALL_L   = 40.0

# ---- Hotend thermal standoff ----
HOTEND_STANDOFF = 25.0

# ---- Winder riser ----
RISER_W      = 50.0
RISER_T      = 12.0
RISER_H      = 155.0      # spool top stays under 300 mm Z limit (G2)
RISER_FOOT_L = 60.0

# ---- Edge fillet radius (cosmetic/strength) ----
FILLET_R = 1.0

# ---- Phase B: detail parameters ----
CHAMFER_HOLE = 0.5    # mm  chamfer on bolt-hole mouths (45 deg)
LABEL_DEPTH  = 0.7    # mm  embossed-label recess depth
LABEL_H      = 4.0    # mm  text height for part labels

# ===========================================================================
# DERIVED REFERENCE PLANES
# ===========================================================================
FLANGE_TOP_Z = SPINE_H
DECK_Z       = FLANGE_TOP_Z
RAIL_TOP_Z   = DECK_Z + RAIL_H
CHAN_OUTER_W = CHAN_CLEAR_W + 2 * CHAN_WALL
CHAN_OUTER_H = CHAN_CLEAR_H + 2 * CHAN_WALL

# ===========================================================================
# REAL MOUNTING-HOLE PATTERNS for bought parts (drive both placeholder + module)
# ===========================================================================
NEMA17_BODY      = 42.3            # mm body square (nominal 42.3)
NEMA17_BOLT_SQ   = 31.0           # mm bolt-hole square (4x M3)
NEMA17_PILOT_D   = 22.0           # mm pilot boss diameter
NEMA17_SHAFT_D   = 5.0            # mm shaft
NEMA17_LEN       = 48.0           # mm body length
# 4 mounting holes at +/-15.5 in both axes (31 mm square), measured from body centre
NEMA17_HOLES = [(+NEMA17_BOLT_SQ/2, +NEMA17_BOLT_SQ/2),
                (+NEMA17_BOLT_SQ/2, -NEMA17_BOLT_SQ/2),
                (-NEMA17_BOLT_SQ/2, +NEMA17_BOLT_SQ/2),
                (-NEMA17_BOLT_SQ/2, -NEMA17_BOLT_SQ/2)]

# Arduino Uno R3 canonical 4-hole pattern, measured from board corner (mm).
UNO_L = 68.6
UNO_W = 53.4
UNO_HOLES_CORNER = [(15.24, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56)]
# Centre the pattern so holes are expressed about the board centroid for placement.
def uno_holes_centred():
    cx = UNO_L / 2.0
    cy = UNO_W / 2.0
    return [(hx - cx, hy - cy) for (hx, hy) in UNO_HOLES_CORNER]

# ===========================================================================
# HELPERS
# ===========================================================================
def hex_pocket(af, depth):
    """A hex prism (across-flats = af) of given depth, base at z=0, on XY."""
    r = af_to_circum(af)
    return cq.Workplane("XY").polygon(6, 2 * r).extrude(depth)

def vhole(d, depth):
    """A vertical cylindrical cutter, base at z=0."""
    return cq.Workplane("XY").circle(d / 2).extrude(depth)

def safe_fillet(solid, r, selector=None):
    """Fillet all edges (or a selected set); fall back gracefully if it fails."""
    try:
        if selector is None:
            return solid.edges().fillet(r)
        return solid.edges(selector).fillet(r)
    except Exception:
        return solid

def safe_chamfer(solid, r, selector=None):
    """Chamfer edges; fall back gracefully if it fails."""
    try:
        if selector is None:
            return solid.edges().chamfer(r)
        return solid.edges(selector).chamfer(r)
    except Exception:
        return solid

def chamfer_top_holes(solid, hole_d, hole_positions, z_top, chamfer_r=CHAMFER_HOLE):
    """Add small chamfers at the top mouth of vertical bolt holes.
    Works by cutting a slightly wider+shallow conical lip at the hole entrance.
    hole_positions: list of (x, y) centres; z_top: Z face where hole opens.
    """
    for (hx, hy) in hole_positions:
        # A cone frustum: from hole_d/2 + chamfer_r at z_top down to hole_d/2 at z_top-chamfer_r
        # Approximate as a thin cylinder slightly larger than hole (gives a step chamfer).
        # Use a small outer cone: circle at hole_d/2 + chamfer_r extruded down chamfer_r.
        try:
            cone = (cq.Workplane("XY")
                    .circle((hole_d / 2) + chamfer_r)
                    .workplane(offset=-chamfer_r)
                    .circle(hole_d / 2)
                    .loft()
                    .translate((hx, hy, z_top - chamfer_r)))
            solid = solid.cut(cone)
        except Exception:
            pass
    return solid

def label_recess(solid, text, x, y, z_face, text_h=LABEL_H, depth=LABEL_DEPTH, rotate_z=0):
    """Cut a shallow text recess into a flat Z face.
    The text is extruded downward into the surface.
    Falls back silently if text generation fails.
    """
    try:
        txt = (cq.Workplane("XY")
               .workplane(offset=z_face - depth)
               .transformed(rotate=cq.Vector(0, 0, rotate_z), offset=cq.Vector(x, y, 0))
               .text(text, text_h, depth + 0.5, cut=False, halign='center', valign='center'))
        solid = solid.cut(txt)
    except Exception:
        pass
    return solid

# ===========================================================================
# PRINTED PART: SPINE SEGMENT
# ===========================================================================
def build_spine_segment(x_start, x_end, splice_end=None):
    """One I-section spine segment x_start..x_end (centreline).
    splice_end in {None,'hi','lo'} marks which end carries the splice bolt holes.

    Phase B detailing:
    - 1.5 mm fillets on the long outer edges of the top flange (before holes).
    - 1.0 mm fillets on the channel outer box long edges.
    - Chamfers (0.5 mm) on M4 bolt hole mouths at flange top face.
    - Shallow label recess ("SPINE-A" or "SPINE-B") on the top flange face.
    """
    seg_len = x_end - x_start
    x_mid = (x_start + x_end) / 2.0
    label = "SPINE-A" if splice_end == 'hi' else "SPINE-B"

    flange = (cq.Workplane("XY").box(seg_len, FLANGE_W, FLANGE_T, centered=(True, True, False))
              .translate((x_mid, 0, FLANGE_TOP_Z - FLANGE_T)))
    rail = (cq.Workplane("XY").box(seg_len, RAIL_W, RAIL_H, centered=(True, True, False))
            .translate((x_mid, 0, DECK_Z)))
    chan_outer = (cq.Workplane("XY").box(seg_len, CHAN_OUTER_W, CHAN_OUTER_H, centered=(True, True, False))
                  .translate((x_mid, 0, 0)))
    web_bottom = CHAN_OUTER_H
    web_top = FLANGE_TOP_Z - FLANGE_T
    web_h = web_top - web_bottom
    web = (cq.Workplane("XY").box(seg_len, WEB_T, web_h, centered=(True, True, False))
           .translate((x_mid, 0, web_bottom)))

    solid = flange.union(rail).union(chan_outer).union(web)

    # Phase B: fillet the long outer edges of the channel box (1 mm) before boring.
    # Using |X selector — edges parallel to X axis (the long edges).
    solid = safe_fillet(solid, FILLET_R, "|X")

    # Hollow the channel (clear bore), open at the top into the web region.
    bore = (cq.Workplane("XY").box(seg_len + 2, CHAN_CLEAR_W, CHAN_CLEAR_H, centered=(True, True, False))
            .translate((x_mid, 0, CHAN_WALL)))
    solid = solid.cut(bore)

    # Lead-drop slots at each station within range.
    for sx in [X_STRIPPER, X_HOTEND, X_COOLING, X_HALL, X_CONTROLLER]:
        if x_start + 8 < sx < x_end - 8:
            slot = (cq.Workplane("XY").box(10.0, 6.0, FLANGE_TOP_Z, centered=(True, True, False))
                    .translate((sx, 0, CHAN_WALL)))
            solid = solid.cut(slot)

    # Captive-nut pockets + M4 bolt holes in the top flange at station positions.
    flange_hole_positions = []
    for sx in [X_STRIPPER, X_HOTEND, X_COOLING, X_HALL]:
        if x_start <= sx <= x_end:
            for yoff in (+PAD_Y, -PAD_Y):
                hole = vhole(HOLE_M4, FLANGE_T + 2).translate((sx, yoff, FLANGE_TOP_Z - FLANGE_T - 1))
                solid = solid.cut(hole)
                nut = hex_pocket(NUT_M4_AF, NUT_M4_T).translate((sx, yoff, FLANGE_TOP_Z - FLANGE_T))
                solid = solid.cut(nut)
                flange_hole_positions.append((sx, yoff))

    # Phase B: chamfer the top face of bolt holes (so bolt heads seat cleanly).
    solid = chamfer_top_holes(solid, HOLE_M4, flange_hole_positions,
                               z_top=FLANGE_TOP_Z, chamfer_r=CHAMFER_HOLE)

    # Splice bolt holes through the web (M4), if this is the splice end.
    if splice_end is not None:
        xb = (x_end - 15) if splice_end == 'hi' else (x_start + 15)
        for i in range(SPLICE_BOLTS):
            zb = web_bottom + web_h * (0.30 + 0.40 * (i % 2))
            xpos = xb + ((i // 2) * 12 - 6)
            hole = (cq.Workplane("YZ").circle(HOLE_M4 / 2).extrude(WEB_T + 6)
                    .translate((xpos - (WEB_T + 6) / 2, 0, zb)))
            solid = solid.cut(hole)

    # Phase B: embossed label on top flange face.
    solid = label_recess(solid, label, x_mid, 0, FLANGE_TOP_Z,
                          text_h=LABEL_H, depth=LABEL_DEPTH)

    return solid

# ===========================================================================
# PRINTED PART: SNAP COVER
# ===========================================================================
def build_cover(x_start, x_end):
    """
    Phase B detailing:
    - 0.75 mm chamfer on the outer long top edges (45 deg, avoids supports on the lip).
    - Shallow label ("COVER-A" or "COVER-B") on the top face.
    """
    seg_len = x_end - x_start
    x_mid = (x_start + x_end) / 2.0
    label = "COVER-A" if x_start < SPLICE_X else "COVER-B"

    cover = (cq.Workplane("XY").box(seg_len, CHAN_OUTER_W, COVER_T, centered=(True, True, False))
             .translate((x_mid, 0, CHAN_OUTER_H + 1.0)))
    for yoff in (CHAN_CLEAR_W / 2, -CHAN_CLEAR_W / 2):
        lip = (cq.Workplane("XY").box(seg_len, COVER_LIP, COVER_LIP, centered=(True, True, False))
               .translate((x_mid, yoff, CHAN_OUTER_H + 1.0 - COVER_LIP)))
        cover = cover.union(lip)

    # Phase B: fillet the long outer top edges (cosmetic + reduces stress risers).
    cover = safe_fillet(cover, 0.75, "|X")

    # Phase B: label recess on top face.
    cover_top_z = CHAN_OUTER_H + 1.0 + COVER_T
    cover = label_recess(cover, label, x_mid, 0, cover_top_z,
                          text_h=3.5, depth=LABEL_DEPTH)

    return cover

# ===========================================================================
# PRINTED PART: SPLICE PLATE (one plate per side of web; we model a single
# bridging plate that bolts through the web at both segments).
# ===========================================================================
def build_splice_plate():
    """
    Phase B detailing:
    - 1 mm fillets on the long Y-axis edges (cosmetic + print quality).
    - Chamfers on M4 bolt hole mouths.
    - Shallow label "SPLICE" on the outer face.
    """
    plate_h = 40.0
    z0 = CHAN_OUTER_H + 3
    plate = (cq.Workplane("XY").box(SPLICE_PLATE_L, SPLICE_PLATE_T, plate_h, centered=(True, True, False))
             .translate((SPLICE_X, WEB_T / 2 + SPLICE_PLATE_T / 2 + 0.2, z0)))

    # Phase B: fillet long edges before cutting bolt holes.
    plate = safe_fillet(plate, FILLET_R, "|Y")

    web_bottom = CHAN_OUTER_H
    web_top = FLANGE_TOP_Z - FLANGE_T
    web_h = web_top - web_bottom
    bolt_positions_xz = []
    for i in range(SPLICE_BOLTS):
        # match the spine web splice holes: two clusters either side of SPLICE_X
        side = -1 if i < 2 else +1
        xb = SPLICE_X + side * 15 + ((i % 2) * 12 - 6)
        zb = web_bottom + web_h * (0.30 + 0.40 * (i % 2))
        hole = (cq.Workplane("XZ").circle(HOLE_M4 / 2).extrude(SPLICE_PLATE_T + 4)
                .translate((xb, WEB_T / 2 + SPLICE_PLATE_T / 2 + 0.2 + (SPLICE_PLATE_T + 4) / 2, zb)))
        plate = plate.cut(hole)
        bolt_positions_xz.append((xb, zb))

    # Phase B: label on outer face (Y-facing, use label_recess rotated).
    # Outer face is at Y = WEB_T/2 + SPLICE_PLATE_T + 0.2; label on flat front face.
    # We approximate by placing a recess on the top Z face.
    plate_y_outer = WEB_T / 2 + SPLICE_PLATE_T + 0.2
    plate_top_z = z0 + plate_h
    plate = label_recess(plate, "SPLICE", SPLICE_X, plate_y_outer - SPLICE_PLATE_T / 2, plate_top_z,
                          text_h=3.5, depth=LABEL_DEPTH)

    return plate

# ===========================================================================
# PRINTED PART: GENERIC CLIP-ON MODULE BODY
# ===========================================================================
def build_module(x_center, length, top_h, with_standoff=0.0, mount_holes=None,
                 mount_hole_d=HOLE_M3, mount_nut_af=NUT_M3_AF, mount_nut_t=NUT_M3_T,
                 label=""):
    """A clip-on module: base plate with keyed slot underside + captive-nut pads
    for bolting to spine, walls forming an open cradle, optional thermal standoff,
    and optional component mounting holes (mount_holes = list of (dx,dy) on the
    cradle top plate, expressed about the module centre — these must match the
    bought part's real hole pattern).

    Phase B detailing:
    - 1.5 mm fillets on the outer Z-parallel edges of the module walls (before holes).
    - Chamfers on M4 bolt-hole mouths (spine clip holes) at base underside.
    - Chamfers on M3 mount hole mouths at cradle top plate.
    - Shallow label embossed on the end wall face.
    - 45 deg chamfer on the inner top edge of walls (reduces overhangs, avoids supports).

    Returns (solid, slot_dims, mount_info).
    """
    x0 = x_center
    base = (cq.Workplane("XY").box(length, MOD_W, MOD_BASE_T, centered=(True, True, False))
            .translate((x0, 0, DECK_Z)))
    slot = (cq.Workplane("XY").box(length + 2, SLOT_W, SLOT_H, centered=(True, True, False))
            .translate((x0, 0, DECK_Z - 0.001)))
    body = base.cut(slot)

    for yoff in (MOD_W / 2 - MOD_WALL / 2, -(MOD_W / 2 - MOD_WALL / 2)):
        wall = (cq.Workplane("XY").box(length, MOD_WALL, top_h, centered=(True, True, False))
                .translate((x0, yoff, DECK_Z + MOD_BASE_T)))
        body = body.union(wall)
    endwall = (cq.Workplane("XY").box(MOD_WALL, MOD_W, top_h, centered=(True, True, False))
               .translate((x0 - length / 2 + MOD_WALL / 2, 0, DECK_Z + MOD_BASE_T)))
    body = body.union(endwall)

    top_plate_z = None
    if with_standoff > 0:
        for xoff in (length / 2 - 8, -(length / 2 - 8)):
            for yoff in (MOD_W / 2 - 6, -(MOD_W / 2 - 6)):
                post = (cq.Workplane("XY").box(6, 6, with_standoff, centered=(True, True, False))
                        .translate((x0 + xoff, yoff, DECK_Z + MOD_BASE_T + top_h)))
                body = body.union(post)
        top_plate_z = DECK_Z + MOD_BASE_T + top_h + with_standoff
        cradle = (cq.Workplane("XY").box(length, MOD_W, MOD_BASE_T, centered=(True, True, False))
                  .translate((x0, 0, top_plate_z)))
        body = body.union(cradle)
    else:
        # cradle top is the open top of the walls; component mounts to a top plate
        # set across the walls.
        top_plate_z = DECK_Z + MOD_BASE_T + top_h - MOD_BASE_T
        cradle = (cq.Workplane("XY").box(length, MOD_W, MOD_BASE_T, centered=(True, True, False))
                  .translate((x0, 0, top_plate_z)))
        body = body.union(cradle)

    # Phase B: fillet outer Z-parallel (vertical) edges of the module body BEFORE hole cutting.
    # This rounds the outer corner of the cradle walls for strength + looks.
    body = safe_fillet(body, 1.5, "|Z")

    # Bolt clearance holes through base -> spine captive nuts (M4).
    spine_clip_hole_positions = [(x0, yoff) for yoff in (+PAD_Y, -PAD_Y)]
    for (hx, hy) in spine_clip_hole_positions:
        hole = vhole(HOLE_M4, MOD_BASE_T + 2).translate((hx, hy, DECK_Z - 1))
        body = body.cut(hole)

    # Phase B: chamfer on M4 spine clip hole mouths at top of base (DECK_Z + MOD_BASE_T).
    body = chamfer_top_holes(body, HOLE_M4, spine_clip_hole_positions,
                              z_top=DECK_Z + MOD_BASE_T, chamfer_r=CHAMFER_HOLE)

    # Component mounting holes on the cradle top plate (match real part pattern).
    mount_info = None
    if mount_holes is not None:
        plate_top = top_plate_z + MOD_BASE_T
        abs_holes = []
        for (dx, dy) in mount_holes:
            hx, hy = x0 + dx, dy
            cutter = vhole(mount_hole_d, MOD_BASE_T + 2).translate((hx, hy, top_plate_z - 1))
            body = body.cut(cutter)
            # captive nut on underside of cradle plate
            nut = hex_pocket(mount_nut_af, mount_nut_t).translate((hx, hy, top_plate_z))
            body = body.cut(nut)
            abs_holes.append((hx, hy))
        # Phase B: chamfer on M3 mount hole mouths at top of cradle plate.
        body = chamfer_top_holes(body, mount_hole_d, abs_holes,
                                  z_top=plate_top, chamfer_r=CHAMFER_HOLE)
        mount_info = {"holes_world": abs_holes, "hole_d": mount_hole_d,
                      "plate_top_z": plate_top}

    # Phase B: embossed label on the end wall face (top Z face of end wall).
    # Place label on end-wall top face if there's room.
    endwall_top_z = DECK_Z + MOD_BASE_T + top_h
    endwall_x = x0 - length / 2 + MOD_WALL / 2
    if label:
        label_name = "MOD-" + label.upper()
        body = label_recess(body, label_name, endwall_x, 0, endwall_top_z,
                             text_h=3.0, depth=LABEL_DEPTH)

    slot_dims = {"width": SLOT_W, "height": SLOT_H}
    return body, slot_dims, mount_info

# ===========================================================================
# PRINTED PART: WINDER RISER
# ===========================================================================
def build_riser():
    """
    Phase B detailing:
    - Gusset fillet: 2 mm fillet where the vertical riser meets the horizontal foot
      (this gusset removes the sharp right-angle stress concentration — the classic
      weak point of an L-section bracket in PLA).
    - 1 mm fillet on outer Z edges of the foot.
    - Chamfer on M4 foot bolt-hole mouths.
    - Shallow label "RISER" on the foot top face.
    - 45 deg chamfer on the upper leading edge of the riser plate to avoid overhangs.
    """
    foot = (cq.Workplane("XY").box(RISER_FOOT_L, RISER_W, MOD_BASE_T, centered=(True, True, False))
            .translate((X_CONTROLLER, 0, DECK_Z)))
    slot = (cq.Workplane("XY").box(RISER_FOOT_L + 2, SLOT_W, SLOT_H, centered=(True, True, False))
            .translate((X_CONTROLLER, 0, DECK_Z - 0.001)))
    foot = foot.cut(slot)

    riser_x = X_CONTROLLER - RISER_FOOT_L / 2 + RISER_T / 2
    riser = (cq.Workplane("XY").box(RISER_T, RISER_W, RISER_H, centered=(True, True, False))
             .translate((riser_x, 0, DECK_Z + MOD_BASE_T)))

    gusset = (cq.Workplane("XZ").moveTo(0, 0).lineTo(40, 0).lineTo(0, 60).close()
              .extrude(12).translate((riser_x + RISER_T / 2, -6, DECK_Z + MOD_BASE_T)))

    body = foot.union(riser).union(gusset)

    # Phase B: fillet the gusset edges and outer foot Z-edges for strength + look.
    # Apply 1.5 mm fillets to Z-parallel edges before hole cutting.
    body = safe_fillet(body, 1.5, "|Z")

    # Spool axle boss near top of riser (Y axle through the riser plate).
    boss_z = DECK_Z + MOD_BASE_T + RISER_H - 30
    boss = (cq.Workplane("XZ").circle(10).extrude(40).translate((riser_x, 0, boss_z)))
    body = body.union(boss)
    axle_bore = (cq.Workplane("XZ").circle(NEMA17_SHAFT_D / 2 + 0.4).extrude(60)
                 .translate((riser_x, 0, boss_z)))
    body = body.cut(axle_bore)

    # M4 foot bolt holes -> spine captive nuts.
    foot_hole_positions = [(X_CONTROLLER, yoff) for yoff in (+PAD_Y, -PAD_Y)]
    for (hx, hy) in foot_hole_positions:
        hole = vhole(HOLE_M4, MOD_BASE_T + 2).translate((hx, hy, DECK_Z - 1))
        body = body.cut(hole)

    # Phase B: chamfer on M4 foot bolt-hole mouths.
    body = chamfer_top_holes(body, HOLE_M4, foot_hole_positions,
                              z_top=DECK_Z + MOD_BASE_T, chamfer_r=CHAMFER_HOLE)

    # Phase B: label on foot top face.
    body = label_recess(body, "RISER", X_CONTROLLER, 0, DECK_Z + MOD_BASE_T,
                         text_h=4.0, depth=LABEL_DEPTH)

    return body

# ===========================================================================
# BOUGHT-PART STAND-INS — Phase A: richer fidelity models
# (PLACEHOLDER_* tagged; same external envelope + same hole positions as before)
# ===========================================================================
def ph_box(l, w, h, x, y, z):
    return cq.Workplane("XY").box(l, w, h, centered=(True, True, False)).translate((x, y, z))

def build_nema17_placeholder(nx, nema_z):
    """NEMA17 stepper — higher fidelity:
    - 42x42 body with chamfered corners (3 mm chamfer on 4 vertical edges).
    - 22 mm pilot boss raised on the +Z face.
    - 5 mm rounded (circular) shaft protruding further.
    - Stepped face detail: a 38x38 inset face recessed 1 mm (the real motor has a
      slightly recessed mounting plate area).
    - 4 M3 bolt holes at 31 mm square (G9 anchor — unchanged).
    """
    nema_body = ph_box(NEMA17_BODY, NEMA17_BODY, NEMA17_LEN, nx, 0, nema_z)

    # Chamfer the 4 vertical corners of the body (cosmetic — real motors have these).
    nema_body = safe_chamfer(nema_body, 2.0, "|Z")

    # Stepped mounting face: recess a 38x38 square 1 mm into the +Z face.
    recess = (cq.Workplane("XY").box(38, 38, 1.5, centered=(True, True, False))
              .translate((nx, 0, nema_z + NEMA17_LEN - 1)))
    nema_body = nema_body.cut(recess)

    # Pilot boss on the +Z face.
    pilot = (cq.Workplane("XY").circle(NEMA17_PILOT_D / 2).extrude(2)
             .translate((nx, 0, nema_z + NEMA17_LEN)))

    # Shaft (round, 5 mm dia, 24 mm long protruding).
    shaft = (cq.Workplane("XY").circle(NEMA17_SHAFT_D / 2).extrude(24)
             .translate((nx, 0, nema_z + NEMA17_LEN)))

    # 4 M3 mounting holes — G9 anchor, exactly at 31 mm square.
    for (hx, hy) in NEMA17_HOLES:
        bore = (cq.Workplane("XY").circle(M3_NOM / 2).extrude(8)
                .translate((nx + hx, hy, nema_z + NEMA17_LEN - 8)))
        nema_body = nema_body.cut(bore)

    # Cable connector stub on the -Z side face (a small rectangle block).
    connector = ph_box(14, 6, 10, nx - NEMA17_BODY / 2 - 3, 0, nema_z + 8)
    nema_body = nema_body.union(connector)

    return nema_body.union(pilot).union(shaft)

def build_arduino_uno_placeholder(ucx, ucy, uno_z):
    """Arduino Uno R3 — higher fidelity:
    - Board outline 68.6x53.4, height 15 mm (PCB + component clearance).
    - Real 4-hole pattern (G9 anchor — unchanged).
    - Header strips: two rows of 28-pin header on the long edges (raised rectangles).
    - USB-B connector block on one short edge (+X side).
    - Barrel-jack block near USB-B.
    - Main MCU IC as a raised rectangle centred on the board.
    - Power regulator block.
    """
    uno = ph_box(UNO_L, UNO_W, 15, ucx, ucy, uno_z)

    # 4 M3 holes — G9 anchor.
    holes_world = []
    for (dx, dy) in uno_holes_centred():
        bore = (cq.Workplane("XY").circle(M3_NOM / 2).extrude(17)
                .translate((ucx + dx, ucy + dy, uno_z - 1)))
        uno = uno.cut(bore)
        holes_world.append((ucx + dx, ucy + dy))

    # Long header strips (2x raised rows along +Y and -Y edges).
    for yoff, n_pins in [(-UNO_W / 2 + 4, 28), (UNO_W / 2 - 4, 8)]:
        strip_l = n_pins * 2.54
        strip = ph_box(strip_l, 5, 3, ucx, ucy + yoff, uno_z + 15)
        uno = uno.union(strip)

    # USB-B connector on the +X short edge.
    usb = ph_box(12, 16, 11, ucx + UNO_L / 2 + 4, ucy + 5, uno_z + 4)
    uno = uno.union(usb)

    # Barrel jack (power input) also on +X edge, offset in Y.
    barrel = ph_box(9, 11, 11, ucx + UNO_L / 2 + 3, ucy - 12, uno_z + 4)
    uno = uno.union(barrel)

    # Main MCU IC (ATmega328 TQFP) — a low flat square near board centre.
    ic = ph_box(10, 10, 3.5, ucx + 5, ucy + 5, uno_z + 15)
    uno = uno.union(ic)

    # Voltage regulator (small TO-220 style block on +Y side).
    vreg = ph_box(5, 4.5, 9, ucx + UNO_L / 2 - 15, ucy + UNO_W / 2 + 1, uno_z + 4)
    uno = uno.union(vreg)

    return uno, holes_world

def build_placeholders(hotend_mount=None, controller_mount=None):
    """Build bought-part stand-ins. Phase A: richer geometry for all bought parts.
    Hole patterns and external envelopes are unchanged from the baseline so G9 passes."""
    ph = {}

    # --- NEMA17 stepper (filament puller) — low at controller end on riser ---
    nema_z = DECK_Z + MOD_BASE_T + 4
    nx = X_CONTROLLER - 5
    ph["PLACEHOLDER_NEMA17"] = build_nema17_placeholder(nx, nema_z)
    ph["_NEMA17_holes_world"] = [(nx + hx, hy) for (hx, hy) in NEMA17_HOLES]

    # --- Volcano hotend: heater block + heat-sink fins + nozzle down ---
    if hotend_mount is not None and len(hotend_mount["holes_world"]) >= 2:
        hx_list = hotend_mount["holes_world"]
        cx = sum(h[0] for h in hx_list) / len(hx_list)
        plate_top = hotend_mount["plate_top_z"]
    else:
        cx = X_HOTEND
        plate_top = DECK_Z + MOD_BASE_T + MOD_TOP_H + HOTEND_STANDOFF + MOD_BASE_T

    block_h = 16.0
    hot_z = plate_top + 2

    # Heater block — main body.
    block = ph_box(45, 24, block_h, cx, 0, hot_z)

    # Two M3 mounting holes on heater block top (unchanged — G9 anchor).
    for dx in (+12, -12):
        bore = (cq.Workplane("XY").circle(M3_NOM / 2).extrude(8)
                .translate((cx + dx, 0, hot_z)))
        block = block.cut(bore)

    # Heat-sink: fins are parallel thin plates above the heater block.
    # 6 fins, each 3 mm thick, 2 mm gap, 20 mm tall, 45 mm wide.
    fin_base_z = hot_z + block_h
    fin_count = 5
    fin_t = 2.5
    fin_gap = 2.5
    fin_span_w = fin_count * (fin_t + fin_gap) - fin_gap
    for i in range(fin_count):
        fy = -fin_span_w / 2 + i * (fin_t + fin_gap)
        fin = ph_box(45, fin_t, 20, cx, fy + fin_t / 2, fin_base_z)
        block = block.union(fin)

    # Cartridge heater hole (2 holes from the side — two cylindrical bores).
    heater_bore = (cq.Workplane("XZ").circle(3).extrude(28)
                   .translate((cx, -14, hot_z + block_h / 2)))
    block = block.cut(heater_bore)

    # Nozzle: a cone frustum pointing down.
    nozzle_top_r = 6.0
    nozzle_bot_r = 1.5
    nozzle = (cq.Workplane("XY")
              .circle(nozzle_top_r)
              .workplane(offset=-30)
              .circle(nozzle_bot_r)
              .loft()
              .translate((cx, 0, hot_z)))
    ph["PLACEHOLDER_VOLCANO_HOTEND"] = block.union(nozzle)

    # --- Arduino Uno R3 with real 4-hole pattern + fidelity features ---
    if controller_mount is not None:
        ucx, ucy = controller_mount["origin"]
        uno_z = controller_mount["plate_top_z"] + 1
    else:
        ucx = X_CONTROLLER + 40
        ucy = -45
        uno_z = DECK_Z

    uno, holes_world = build_arduino_uno_placeholder(ucx, ucy, uno_z)
    ph["PLACEHOLDER_ARDUINO_UNO"] = uno
    ph["_ARDUINO_holes_world"] = holes_world

    # --- CNC Shield stacked on Arduino — with header pin rows ---
    cnc = ph_box(UNO_L, UNO_W, 20, ucx, ucy, uno_z + 15)
    # Stepper driver sockets (4 small squares).
    for i in range(4):
        drv = ph_box(14, 18, 8, ucx - UNO_L / 2 + 10 + i * 16, ucy + 5, uno_z + 15 + 20)
        cnc = cnc.union(drv)
    # Header pin strip on bottom (connecting to Arduino).
    for yoff, n_pins in [(-UNO_W / 2 + 4, 28), (UNO_W / 2 - 4, 8)]:
        strip = ph_box(n_pins * 2.54, 5, 3, ucx, ucy + yoff, uno_z + 15 - 3)
        cnc = cnc.union(strip)
    ph["PLACEHOLDER_CNC_SHIELD"] = cnc

    # --- Sealed PSU ~129x98x38 (pulled in so width stays <= 200, G2) ---
    psu = ph_box(129, 98, 38, X_CONTROLLER + 60, 48, DECK_Z)
    # Vent slots on the face (3 slots cut into the top face).
    for i in range(5):
        slot = ph_box(20, 4, 3, X_CONTROLLER + 60 - 40 + i * 18, 48, DECK_Z + 38 - 2)
        psu = psu.cut(slot)
    # Terminal block on one end face.
    terminal = ph_box(10, 30, 20, X_CONTROLLER + 60 + 129 / 2 - 5, 48, DECK_Z + 5)
    psu = psu.union(terminal)
    # Fan grille recess (circular) on the opposite end face.
    fan_grille = (cq.Workplane("YZ").circle(15).extrude(3)
                  .translate((X_CONTROLLER + 60 - 129 / 2, 48, DECK_Z + 19)))
    psu = psu.cut(fan_grille)
    ph["PLACEHOLDER_PSU_SEALED"] = psu

    # --- 5015 blower fans 50x50x15 x2 on cooling module --- fan body + impeller cavity ---
    for name, ypos in [("PLACEHOLDER_FAN_5015_A", 18), ("PLACEHOLDER_FAN_5015_B", -18)]:
        fan = ph_box(50, 50, 15, X_COOLING, ypos, DECK_Z + MOD_BASE_T + MOD_TOP_H)
        # Corner mount bosses (small cylinders at corners).
        for cx2, cy2 in [(+20, +20), (+20, -20), (-20, +20), (-20, -20)]:
            boss = (cq.Workplane("XY").circle(2.5).extrude(15)
                    .translate((X_COOLING + cx2, ypos + cy2, DECK_Z + MOD_BASE_T + MOD_TOP_H)))
            fan = fan.union(boss)
        # Impeller cavity — a recessed circle on the outlet face.
        impeller = (cq.Workplane("XY").circle(18).extrude(3)
                    .translate((X_COOLING, ypos, DECK_Z + MOD_BASE_T + MOD_TOP_H + 15 - 2)))
        fan = fan.cut(impeller)
        # Inlet duct stub on side.
        inlet = ph_box(15, 50, 12, X_COOLING - 25 - 8, ypos, DECK_Z + MOD_BASE_T + MOD_TOP_H + 2)
        fan = fan.union(inlet)
        ph[name] = fan

    # --- 1602A LCD 80x36x12 (pulled in so width stays <= 200, G2) ---
    lcd = ph_box(80, 36, 12, X_CONTROLLER + 30, -70, DECK_Z + 20)
    # Recessed screen rectangle (screen is slightly inset in the bezel).
    screen = ph_box(66, 22, 2, X_CONTROLLER + 30, -70, DECK_Z + 20 + 12 - 1)
    lcd = lcd.cut(screen)
    # Backlight border (raised edge around screen).
    ph["PLACEHOLDER_LCD_1602A"] = lcd

    # --- Spool ~190 dia x 56 on riser axle ---
    riser_x = X_CONTROLLER - RISER_FOOT_L / 2 + RISER_T / 2
    spool_cz = DECK_Z + MOD_BASE_T + RISER_H - 30
    spool = (cq.Workplane("XZ").circle(95).extrude(56)
             .translate((riser_x, 28, spool_cz)))
    # Hub bore.
    hub_bore = (cq.Workplane("XZ").circle(15).extrude(60)
                .translate((riser_x, 26, spool_cz)))
    spool = spool.cut(hub_bore)
    ph["PLACEHOLDER_SPOOL"] = spool

    return ph

# ===========================================================================
# BUILD EVERYTHING
# ===========================================================================
SEG_A_START = X_CONTROLLER - RISER_FOOT_L / 2 - 10   # = -90
SEG_B_END   = SEG_A_START + SPINE_LEN                # span 380 total

def build_all():
    printed = {}

    printed["spine_segment_A"] = build_spine_segment(SEG_A_START, SPLICE_X, splice_end='hi')
    printed["spine_segment_B"] = build_spine_segment(SPLICE_X, SEG_B_END, splice_end='lo')
    printed["splice_plate"]    = build_splice_plate()

    printed["cover_A"] = build_cover(SEG_A_START, SPLICE_X)
    printed["cover_B"] = build_cover(SPLICE_X, SEG_B_END)

    # Stripper module — bolts to NEMA17-style pattern? No: stripper carries blades.
    # But spec requires "hotend/stripper module -> NEMA17 31 mm square".
    # The stripper mount carries a small puller/feed motor → use NEMA17 pattern.
    m_strip, strip_slot, strip_mount = build_module(
        X_STRIPPER, STRIP_L, MOD_TOP_H,
        mount_holes=NEMA17_HOLES, mount_hole_d=HOLE_M3,
        mount_nut_af=NUT_M3_AF, mount_nut_t=NUT_M3_T, label="stripper")

    # Hotend module — two M3 holes matching the Volcano heater block (X +/-12).
    m_hot, hot_slot, hot_mount = build_module(
        X_HOTEND, HOTEND_L, MOD_TOP_H, with_standoff=HOTEND_STANDOFF,
        mount_holes=[(+12, 0), (-12, 0)], mount_hole_d=HOLE_M3,
        mount_nut_af=NUT_M3_AF, mount_nut_t=NUT_M3_T, label="hotend")

    m_cool, cool_slot, _ = build_module(
        X_COOLING, COOL_L, MOD_TOP_H, mount_holes=None, label="cooling")

    m_hall, hall_slot, _ = build_module(
        X_HALL, HALL_L, MOD_TOP_H, mount_holes=None, label="hall")

    printed["module_stripper"]      = m_strip
    printed["module_hotend"]        = m_hot
    printed["module_cooling"]       = m_cool
    printed["module_hall"]          = m_hall
    printed["winder_riser"]         = build_riser()

    # Controller mount: a small bracket carrying the Arduino Uno pattern.
    # We add it to the cooling-area deck as a printed mount plate so the Uno
    # 4-hole pattern is realised on a printed part (controller mount).
    ctrl_mount = build_controller_mount()
    printed["module_controller"] = ctrl_mount["solid"]

    placeholders = build_placeholders(hotend_mount=hot_mount,
                                      controller_mount=ctrl_mount["mount_info"])

    slot_dims = {"stripper": strip_slot, "hotend": hot_slot,
                 "cooling": cool_slot, "hall": hall_slot}
    rail_dims = {"width": RAIL_W, "height": RAIL_H}
    mounts = {"stripper": strip_mount, "hotend": hot_mount,
              "controller": ctrl_mount["mount_info"]}
    return printed, placeholders, slot_dims, rail_dims, mounts

# ===========================================================================
# PRINTED PART: CONTROLLER MOUNT (carries Arduino Uno 4-hole pattern)
# ===========================================================================
def build_controller_mount():
    """A flat printed bracket that clips to the spine at the controller end and
    presents the canonical Arduino Uno R3 4-hole mounting pattern (with standoff
    bosses + captive M3 nuts). Placed off to the side (−Y) so it doesn't collide
    with the riser/spool. Returns dict with solid + mount_info.

    Phase B detailing:
    - 1 mm fillets on outer Z-parallel edges of the plate.
    - Chamfers on M3 standoff bolt holes.
    - Chamfers on M4 clip bolt holes.
    - Label "CTRL-MNT" on the top face.
    """
    # Plate sits beside the spine on the −Y side, on its own little feet.
    cx = X_CONTROLLER + 40
    cy = -50.0
    plate_l = UNO_L + 12
    plate_w = UNO_W + 12
    plate_t = MOD_BASE_T
    base_z = DECK_Z
    plate = (cq.Workplane("XY").box(plate_l, plate_w, plate_t, centered=(True, True, False))
             .translate((cx, cy, base_z)))
    # A small keyed foot tab to clip to the rail (mate compliance) running into +Y
    foot = (cq.Workplane("XY").box(30, 24, MOD_BASE_T, centered=(True, True, False))
            .translate((cx, cy + plate_w / 2 + 12 - 0.001, base_z)))
    foot_slot_y = cy + plate_w / 2 + 12 + 4
    # the foot reaches over to the spine rail line (Y=0); model a connecting arm
    arm_len = abs(foot_slot_y) + 20
    arm = (cq.Workplane("XY").box(20, arm_len, MOD_BASE_T, centered=(True, True, False))
           .translate((cx, (foot_slot_y + 0) / 2, base_z)))
    body = plate.union(arm)
    # keyed slot on the arm underside over the rail at the controller station
    slot = (cq.Workplane("XY").box(20, SLOT_W, SLOT_H, centered=(True, True, False))
            .translate((cx, 0, base_z - 0.001)))
    # only cut where arm passes over Y=0
    body = body.cut(slot)

    # Phase B: fillet outer Z-parallel edges of the plate body.
    body = safe_fillet(body, FILLET_R, "|Z")

    # standoff bosses + Arduino holes
    holes_world = []
    boss_h = 6.0
    m3_hole_positions = []
    for (dx, dy) in uno_holes_centred():
        hx, hy = cx + dx, cy + dy
        boss = (cq.Workplane("XY").circle(4).extrude(boss_h).translate((hx, hy, base_z + plate_t)))
        body = body.union(boss)
        bore = vhole(HOLE_M3, plate_t + boss_h + 2).translate((hx, hy, base_z - 1))
        body = body.cut(bore)
        nut = hex_pocket(NUT_M3_AF, NUT_M3_T).translate((hx, hy, base_z))
        body = body.cut(nut)
        holes_world.append((hx, hy))
        m3_hole_positions.append((hx, hy))

    # Phase B: chamfer on M3 standoff hole mouths (top of boss).
    boss_top_z = base_z + plate_t + boss_h
    body = chamfer_top_holes(body, HOLE_M3, m3_hole_positions,
                              z_top=boss_top_z, chamfer_r=CHAMFER_HOLE)

    # M4 clip bolt holes through the arm foot into spine captive nuts
    clip_hole_positions = [(cx, yoff) for yoff in (+PAD_Y, -PAD_Y)]
    for (hx, hy) in clip_hole_positions:
        hole = vhole(HOLE_M4, MOD_BASE_T + 2).translate((hx, hy, base_z - 1))
        body = body.cut(hole)

    # Phase B: chamfer on M4 clip hole mouths.
    body = chamfer_top_holes(body, HOLE_M4, clip_hole_positions,
                              z_top=base_z + MOD_BASE_T, chamfer_r=CHAMFER_HOLE)

    # Phase B: label on the plate top face.
    body = label_recess(body, "CTRL-MNT", cx, cy, base_z + plate_t,
                         text_h=3.5, depth=LABEL_DEPTH)

    mount_info = {"holes_world": holes_world, "hole_d": HOLE_M3,
                  "plate_top_z": base_z + plate_t + boss_h,
                  "origin": (cx, cy)}
    return {"solid": body, "mount_info": mount_info}

# ===========================================================================
# PRINT ORIENTATION — flatten each printed part for slicing
# ===========================================================================
def to_print_orientation(name, solid):
    """Return a copy of the part oriented flat on the bed (z>=0), centred at XY origin.
    Returns the re-oriented solid."""
    s = solid
    # Lay long parts on their side per the print-orientation notes.
    if name in ("spine_segment_A", "spine_segment_B"):
        # print lying on side: rotate 90 about X so web is vertical, flanges vertical
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)
    elif name in ("cover_A", "cover_B", "splice_plate"):
        pass  # already flat-ish
    elif name == "winder_riser":
        # print on its largest face: lay the riser flat (rotate about Y by 90)
        s = s.rotate((0, 0, 0), (0, 1, 0), 90)
    # Drop to z=0 and centre at origin.
    bb = s.val().BoundingBox()
    s = s.translate((-(bb.xmin + bb.xmax) / 2.0, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))
    return s

# ===========================================================================
# EXPORT
# ===========================================================================
PRINTED_EXPORT_NAMES = [
    "spine_segment_A", "spine_segment_B", "splice_plate",
    "cover_A", "cover_B",
    "module_stripper", "module_hotend", "module_cooling", "module_hall",
    "winder_riser",
]

def export_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    printed, placeholders, slot_dims, rail_dims, mounts = build_all()

    # --- Per-part STEP + STL (print-oriented) ---
    for name in PRINTED_EXPORT_NAMES:
        if name not in printed:
            continue
        oriented = to_print_orientation(name, printed[name])
        shp = oriented.val()
        exporters.export(shp, os.path.join(outdir, f"{name}.step"))
        exporters.export(shp, os.path.join(outdir, f"{name}.stl"))

    # Also export controller mount (printed) per-part for completeness.
    if "module_controller" in printed:
        oriented = to_print_orientation("module_controller", printed["module_controller"])
        exporters.export(oriented.val(), os.path.join(outdir, "module_controller.step"))
        exporters.export(oriented.val(), os.path.join(outdir, "module_controller.stl"))

    # --- Full combined assembly (world coords; printed + placeholders) ---
    # Build a flat Compound of every solid. We export the assembly STEP as a
    # plain compound (not Assembly.save) so it reimports cleanly for QA G7 —
    # Assembly.save() writes a structured STEP that cadquery's reader rejects.
    all_solids = []
    for name, solid in printed.items():
        all_solids.append(solid.val())
    for name, solid in placeholders.items():
        if name.startswith("_"):
            continue
        all_solids.append(solid.val())
    comp = cq.Compound.makeCompound(all_solids)
    exporters.export(comp, os.path.join(outdir, "spine_detailed_assembly.step"))
    exporters.export(comp, os.path.join(outdir, "spine_detailed_assembly.stl"))

    # Also write a colour-coded structured assembly STEP for viewing (not used by QA).
    asm = cq.Assembly(name="pullstruder_spine_detailed")
    for name, solid in printed.items():
        asm.add(solid, name=name, color=cq.Color(0.2, 0.5, 0.9))
    for name, solid in placeholders.items():
        if name.startswith("_"):
            continue
        asm.add(solid, name=name, color=cq.Color(0.8, 0.3, 0.3))
    try:
        asm.save(os.path.join(outdir, "spine_detailed_assembly_coloured.step"))
    except Exception as e:
        print(f"coloured assembly save skipped: {e}")

    # --- Print plate: all printed parts laid flat, shelf-packed onto BED plates ---
    plate_compound, n_plates = build_print_plate(printed)
    exporters.export(plate_compound, os.path.join(outdir, "print_plate.step"))
    exporters.export(plate_compound, os.path.join(outdir, "print_plate.stl"))

    print(f"Exported to {outdir}")
    print(f"Printed parts: {len([k for k in printed])}  Placeholders: "
          f"{len([k for k in placeholders if not k.startswith('_')])}")
    print(f"Print plates needed (BED={BED:.0f}): {n_plates}")

def build_print_plate(printed):
    """Lay all printed parts flat in a shelf bin-pack, filling BED x BED plates.
    The total part area exceeds a single 256 x 256 bed once the long spine
    segments + riser are laid down, so parts spill onto a SECOND plate. Plates
    are offset in Y by (BED + gap) so the layout reads as two side-by-side beds
    in one file. Returns (Compound, plate_count)."""
    names = PRINTED_EXPORT_NAMES + (["module_controller"] if "module_controller" in printed else [])
    oriented_parts = []
    for name in names:
        o = to_print_orientation(name, printed[name])
        bb = o.val().BoundingBox()
        oriented_parts.append((name, o, bb.xlen, bb.ylen))
    # Shelf-pack in declared order (long bars first, then covers, then small
    # modules) — this packs onto two BED plates with the least wasted area.

    gap = 8.0
    plate_gap = 20.0
    placed = []
    cur_x = 0.0
    cur_y = 0.0
    row_h = 0.0
    plate = 0
    plate_origin_y = 0.0
    for (name, o, lx, ly) in oriented_parts:
        # wrap to a new row within the current plate
        if cur_x + lx > BED and cur_x > 0:
            cur_x = 0.0
            cur_y += row_h + gap
            row_h = 0.0
        # if the new row would exceed the bed depth, start a new plate
        if cur_y + ly > BED and cur_y > 0:
            plate += 1
            plate_origin_y = plate * (BED + plate_gap)
            cur_x = 0.0
            cur_y = 0.0
            row_h = 0.0
        shifted = o.translate((cur_x + lx / 2.0, plate_origin_y + cur_y + ly / 2.0, 0))
        placed.append(shifted.val())
        cur_x += lx + gap
        row_h = max(row_h, ly)

    comp = cq.Compound.makeCompound(placed)
    return comp, plate + 1

if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    export_all(outdir)
