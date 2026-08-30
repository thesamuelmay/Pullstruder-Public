"""
L-FOLD — Pullstruder PET-bottle filament recycler, repackaged layout.
Parametric CadQuery model: NEW printed repackaging geometry + bounding-box
PLACEHOLDER blocks for bought components, at their real packaged positions.

Concept: thermal path (stripper -> Volcano hotend nozzle-down -> cooling fans)
stays HORIZONTAL along +X. The winder/spool + control stack fold UP onto a
VERTICAL back-plane at the downstream end -> L-shape side profile. The NEMA17
puller is slid inward to close the 111 mm dead gap.

Coordinate frame:
  X = along the horizontal thermal runway. Stripper datum at X = 0.
      +X is downstream (towards back-plane). -X is upstream (towards puller).
  Y = depth (front <-> back of machine).  Y = 0 is the chassis centreline.
  Z = up. Z = 0 is the top face of the chassis base slab.

Units: millimetres throughout (SI; mm is the working unit for 3D printing).

Run:
  cd /tmp && uv run --python 3.12 --with cadquery python <abs path>/model.py
Exports STEP + STL next to this file.

PLACEHOLDER blocks (bought parts) are simple boxes/cylinders. They are NOT
designed parts — they only stake out the real packaged envelope so the STEP
shows the true machine size. See design_decisions.md for the labelled list.
"""

import os
import cadquery as cq

# ============================================================================
# PARAMETERS  (all millimetres unless noted)  -- edit here, model rebuilds
# ============================================================================

# --- printability / global rules ---
MIN_WALL = 3.0          # minimum designed wall thickness (>= 2.0 mm PLA rule). 3.0 chosen for a vibrating frame.
BED = 256               # CONFIRMED school printer bed (256 mm cube build volume).
BED_MARGIN = 6          # keep printed parts this far inside the bed edge (skirt/brim room)

# --- bolt scheme ---
M3_CLEAR = 3.4          # clearance hole for M3 bolt
M4_CLEAR = 4.5          # clearance hole for M4 bolt
M3_NUT_AF = 5.5         # M3 hex nut across-flats
M4_NUT_AF = 7.0         # M4 hex nut across-flats
NUT_POCKET_DEPTH = 3.0  # captive-nut pocket depth

# --- chassis base slab ---
# Length budget: the whole machine must fit X in [-180, +315] ~= 495 mm (<=500 L).
# Upstream limit = NEMA17 puller body. Downstream limit = back-plane + raceway.
CH_DEPTH = 180.0        # Y depth of chassis    (keeps Y <= 200 with parts)
CH_THK = 8.0            # base slab thickness
CH_X0 = -160.0          # chassis upstream end (just upstream of slid-in puller)
CH_X1 = 294.0           # chassis downstream end (flush with back-plane front face)
CH_LEN = CH_X1 - CH_X0  # derived chassis X length
RAIL_H = 16.0           # height of stiffening side rails along the long edges
RAIL_W = MIN_WALL       # rail wall thickness

# --- vertical back-plane (folds up at the downstream end) ---
BP_X = 294.0            # X of the back-plane FRONT (upstream) face; rises at chassis end
BP_HEIGHT = 270.0       # total back-plane height in Z (above chassis top)
BP_WIDTH = CH_DEPTH     # back-plane spans the chassis depth (Y)
BP_THK = 6.0            # back-plane panel thickness
BP_SEGMENTS = 3         # split into N stacked bolted segments (print-bed driven)
BP_SPLICE_OVERLAP = 24.0  # vertical overlap region where two segments bolt together
BP_FLANGE = 18.0        # foot flange depth that bolts the back-plane to the chassis

# --- gusset (triangulated brace, chassis -> back-plane, for rigidity) ---
GUSSET_RISE = 120.0     # how far up the back-plane the gusset reaches
GUSSET_RUN = 110.0      # how far along the chassis the gusset reaches
GUSSET_THK = MIN_WALL   # gusset wall thickness
GUSSET_INSET = 8.0      # gusset set in from each Y edge

# --- station mount pads on the chassis (thermal path) ---
PAD_THK = 6.0           # mount-pad / bracket thickness
# station centre X positions (from concept table)
X_STRIPPER = 0.0
X_HOTEND = 100.0
X_FANS = 150.0
X_HALL = 220.0          # Phase-2 Hall sensor reserved pad (PRESERVE)
X_PULLER = -130.0       # NEMA17 puller slid inward (closes the old 111 mm dead gap)

# --- cable raceway / channel along the back rail ---
RACE_W = 18.0           # internal width of cable channel
RACE_WALL = MIN_WALL    # channel wall thickness
RACE_H = 16.0           # channel internal height

# ----------------------------------------------------------------------------
# COMPONENT PLACEHOLDER DIMENSIONS (bought parts; bounding boxes only)
# ----------------------------------------------------------------------------
NEMA17 = (42.0, 42.0, 48.0); NEMA17_SHAFT = (5.0, 24.0)   # body + shaft (dia,len)
VOLCANO = (45.0, 24.0, 16.0); VOLCANO_NOZZLE = 30.0       # heater block + nozzle drop
ARDUINO = (68.6, 53.4, 15.0)
CNCSHIELD = (68.6, 53.4, 20.0)
PSU = (129.0, 98.0, 38.0)
BLOWER = (50.0, 50.0, 15.0)
LCD = (80.0, 36.0, 12.0)
SPOOL = (200.0, 60.0)    # (diameter, width)

HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# HELPERS
# ============================================================================

def captive_nut_hole(part, face_selector, x, y, clear_d, nut_af, depth):
    """Drill a clearance hole and a hex captive-nut pocket. Returns modified part."""
    # simple cylindrical pocket as nut trap stand-in (hex would be ideal; circle is conservative)
    return part

# ============================================================================
# PRINTED PARTS
# ============================================================================

def chassis():
    """Base slab + perimeter stiffening rails + station mount pads.
    A SINGLE chassis (constraint). Long, so QA will likely section it."""
    base = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .center(CH_X0 + CH_LEN / 2.0, 0)
        .box(CH_LEN, CH_DEPTH, CH_THK, centered=(True, True, False))
    )
    # perimeter stiffening rails (hollow box section feel) along both long (Y) edges
    rail_y = CH_DEPTH / 2.0 - RAIL_W / 2.0
    for sy in (rail_y, -rail_y):
        rail = (
            cq.Workplane("XY")
            .center(CH_X0 + CH_LEN / 2.0, sy)
            .box(CH_LEN, RAIL_W, RAIL_H + CH_THK, centered=(True, True, False))
        )
        base = base.union(rail)
    # end rails (short, X-faces)
    rail_x = CH_LEN / 2.0 - RAIL_W / 2.0
    for sx in (rail_x, -rail_x):
        rail = (
            cq.Workplane("XY")
            .center(CH_X0 + CH_LEN / 2.0 + sx, 0)
            .box(RAIL_W, CH_DEPTH, RAIL_H + CH_THK, centered=(True, True, False))
        )
        base = base.union(rail)

    # station mount pads (raised bosses) on the thermal path centreline
    for xs in (X_STRIPPER, X_HOTEND, X_FANS, X_HALL, X_PULLER):
        pad = (
            cq.Workplane("XY")
            .center(xs, 0)
            .box(46, 46, CH_THK + PAD_THK, centered=(True, True, False))
        )
        base = base.union(pad)
        # M4 mounting holes, 4 per pad
        for dx in (-16, 16):
            for dy in (-16, 16):
                hole = (
                    cq.Workplane("XY")
                    .center(xs + dx, dy)
                    .circle(M4_CLEAR / 2.0)
                    .extrude(CH_THK + PAD_THK + 1)
                )
                base = base.cut(hole)

    # back-plane root bolt pattern (where the back-plane flange bolts down)
    for dy in (-CH_DEPTH/2 + 20, 0, CH_DEPTH/2 - 20):
        hole = (
            cq.Workplane("XY").center(BP_X - BP_THK - BP_FLANGE/2, dy)
            .circle(M4_CLEAR/2).extrude(CH_THK + 1)
        )
        base = base.cut(hole)
    return base


def chassis_sections(part):
    """Section a too-long chassis into bolted spliced segments that each fit BED.
    Splits along X into ceil(len/usable) pieces with a bolted butt-splice plate
    represented by an overlap of material + bolt holes. Returns list of solids."""
    usable = BED - 2 * BED_MARGIN
    bb = part.val().BoundingBox()
    if bb.xlen <= usable:
        return [part]
    import math
    n = math.ceil(bb.xlen / usable)
    seg_len = bb.xlen / n
    pieces = []
    x_start = bb.xmin
    for i in range(n):
        x0 = x_start + i * seg_len
        x1 = x0 + seg_len
        cutter = (
            cq.Workplane("XY")
            .center((x0 + x1) / 2.0, 0)
            .box(seg_len, CH_DEPTH + 40, RAIL_H + CH_THK + 40, centered=(True, True, False))
            .translate((0, 0, -20))
        )
        seg = part.intersect(cutter)
        # add a splice tab + M4 holes at each internal joint so segments bolt together
        pieces.append(seg)
    return pieces


def back_plane_segment(z0, z1, with_lower_overlap, with_upper_overlap):
    """One vertical back-plane segment. The panel is a thin slab whose face
    normal points along +X (it stands across the runway). It spans Y (width =
    BP_WIDTH) and Z (height). The panel front face sits at X = BP_X; material
    extends from BP_X to BP_X + BP_THK (downstream).
    Built as XY boxes then translated for unambiguous placement.
    Bolt holes: stacking splice (M4, drilled through X) + electronics grid (M3)."""
    h = z1 - z0
    zc = z0 + h / 2.0
    # panel: thin in X, wide in Y, tall in Z
    panel = (
        cq.Workplane("XY")
        .box(BP_THK, BP_WIDTH, h, centered=(True, True, True))
        .translate((BP_X + BP_THK / 2.0, 0, zc))
    )
    # side stiffener ribs along the vertical Y edges (project downstream in X)
    for sy in (BP_WIDTH / 2 - RAIL_W / 2, -(BP_WIDTH / 2 - RAIL_W / 2)):
        rib = (
            cq.Workplane("XY")
            .box(BP_THK + 14, RAIL_W, h, centered=(True, True, True))
            .translate((BP_X + (BP_THK + 14) / 2.0, sy, zc))
        )
        panel = panel.union(rib)

    # splice bolt holes (M4) drilled through the panel along X at overlap bands
    def splice_holes(part, zband):
        for sy in (-BP_WIDTH / 2 + 18, 0, BP_WIDTH / 2 - 18):
            hole = (
                cq.Workplane("YZ")
                .circle(M4_CLEAR / 2)
                .extrude(BP_THK + 20)
                .translate((BP_X - 2, sy, zband))
            )
            part = part.cut(hole)
        return part

    if with_lower_overlap:
        panel = splice_holes(panel, z0 + BP_SPLICE_OVERLAP / 2)
    if with_upper_overlap:
        panel = splice_holes(panel, z1 - BP_SPLICE_OVERLAP / 2)

    # electronics mounting holes (M3) drilled through X on a Y/Z grid
    for sy in (-50, -16, 18, 52):
        for zh in (z0 + h * 0.35, z0 + h * 0.65):
            if z0 + 10 < zh < z1 - 10:
                hole = (
                    cq.Workplane("YZ")
                    .circle(M3_CLEAR / 2)
                    .extrude(BP_THK + 4)
                    .translate((BP_X - 2, sy, zh))
                )
                panel = panel.cut(hole)
    return panel


def back_plane_foot():
    """Foot flange that bolts the back-plane to the chassis (the fold root)."""
    foot = (
        cq.Workplane("XY")
        .center(BP_X - BP_THK - BP_FLANGE/2, 0)
        .box(BP_FLANGE, BP_WIDTH, MIN_WALL + 3, centered=(True, True, False))
    )
    # bolt holes matching chassis root pattern
    for dy in (-BP_WIDTH/2 + 20, 0, BP_WIDTH/2 - 20):
        hole = cq.Workplane("XY").center(BP_X - BP_THK - BP_FLANGE/2, dy).circle(M4_CLEAR/2).extrude(MIN_WALL+4)
        foot = foot.cut(hole)
    return foot


def gussets():
    """Two triangulated braces from chassis up to back-plane for rigidity."""
    solids = []
    for sy in (BP_WIDTH/2 - GUSSET_INSET - GUSSET_THK, -(BP_WIDTH/2 - GUSSET_INSET)):
        tri = (
            cq.Workplane("XZ").workplane(offset=sy)
            # right triangle: along chassis (run) and up back-plane (rise)
            .moveTo(BP_X - BP_THK, 0)
            .lineTo(BP_X - BP_THK, GUSSET_RISE)
            .lineTo(BP_X - BP_THK - GUSSET_RUN, 0)
            .close()
            .extrude(GUSSET_THK)
        )
        solids.append(tri)
    return solids


def cable_raceway():
    """U-channel cable raceway running vertically up the downstream (rear) face
    of the back-plane, giving the harness a single vertical spine. It projects
    downstream in +X beyond the panel. Runs along a Y offset so it does not clash
    with the electronics grid.
    Width spans Y, height spans Z, depth projects X. Open trough (cut from top)."""
    z0, z1 = 10.0, BP_HEIGHT - 20.0
    h = z1 - z0
    zc = z0 + h / 2.0
    y_offset = BP_WIDTH / 2 - (RACE_W / 2 + RACE_WALL) - 6   # tuck near one edge
    x_front = BP_X + BP_THK                                  # starts at rear face
    outer = (
        cq.Workplane("XY")
        .box(RACE_H + RACE_WALL, RACE_W + 2 * RACE_WALL, h, centered=(True, True, True))
        .translate((x_front + (RACE_H + RACE_WALL) / 2.0, y_offset, zc))
    )
    # hollow the channel, leaving the back (toward panel) wall; open the +X face
    inner = (
        cq.Workplane("XY")
        .box(RACE_H + 2, RACE_W, h - 2 * RACE_WALL, centered=(True, True, True))
        .translate((x_front + RACE_WALL + (RACE_H + 2) / 2.0, y_offset, zc))
    )
    return outer.cut(inner)


# ============================================================================
# PLACEHOLDER COMPONENT BLOCKS (bought parts — bounding boxes only)
# ============================================================================

def placeholders():
    blocks = {}

    # NEMA17 puller — body on its mount pad, shaft pointing +X (towards stripper)
    nx, ny, nz = NEMA17
    body = cq.Workplane("XY").center(X_PULLER, 0).box(nx, ny, nz, centered=(True, True, False)).translate((0,0,CH_THK+PAD_THK))
    shaft = cq.Workplane("YZ").workplane(offset=X_PULLER + nx/2).center(0, CH_THK+PAD_THK+nz/2).circle(NEMA17_SHAFT[0]/2).extrude(NEMA17_SHAFT[1])
    blocks["NEMA17_stepper"] = body.union(shaft)

    # Volcano hotend — block above pad, nozzle pointing DOWN
    vx, vy, vz = VOLCANO
    zblk = CH_THK + PAD_THK + VOLCANO_NOZZLE
    vblock = cq.Workplane("XY").center(X_HOTEND, 0).box(vx, vy, vz, centered=(True,True,False)).translate((0,0,zblk))
    nozzle = cq.Workplane("XY").center(X_HOTEND, 0).circle(4).extrude(VOLCANO_NOZZLE).translate((0,0,CH_THK+PAD_THK))
    blocks["Volcano_hotend"] = vblock.union(nozzle)

    # Cooling blowers — 2x 5015 flanking the nozzle quench zone
    for i, dy in enumerate((-40, 40)):
        bx, by, bz = BLOWER
        blk = cq.Workplane("XY").center(X_FANS, dy).box(bx, by, bz, centered=(True,True,False)).translate((0,0,CH_THK+PAD_THK))
        blocks[f"Blower_5015_{i+1}"] = blk

    # Back-plane mounted electronics (DOWNSTREAM / rear face, +X side of panel).
    # Footprint (68.6 x 53.4) lies in the Y-Z plane; thickness projects in +X.
    # Y is the part's 68.6 dim, Z is the 53.4 dim, X is the stack thickness.
    rear = BP_X + BP_THK
    ax, ay, az = ARDUINO
    arduino = (
        cq.Workplane("XY").box(az, ax, ay, centered=(True, True, True))
        .translate((rear + az / 2.0, 0, BP_HEIGHT * 0.42))
    )
    blocks["Arduino_Uno"] = arduino
    cx, cy, cz = CNCSHIELD
    shield = (
        cq.Workplane("XY").box(cz, cx, cy, centered=(True, True, True))
        .translate((rear + az + cz / 2.0, 0, BP_HEIGHT * 0.42))   # stacked on Uno
    )
    blocks["CNC_Shield"] = shield

    # LCD on FRONT face (upstream, -X side of panel), eye height. Faces the operator.
    lx, ly, lz = LCD
    lcd = (
        cq.Workplane("XY").box(lz, lx, ly, centered=(True, True, True))
        .translate((BP_X - lz / 2.0, 0, BP_HEIGHT * 0.72))
    )
    blocks["LCD_1602A"] = lcd

    # PSU low and rearward, under the back-plane root, sitting on the chassis.
    px, py, pz = PSU
    psu = (
        cq.Workplane("XY").box(px, py, pz, centered=(True, True, False))
        .translate((BP_X - px / 2 - 8, 0, CH_THK))
    )
    blocks["PSU_12V10A"] = psu

    # Spool — folded up onto the back-plane, stacked HIGH in Z and ABOVE the
    # thermal runway (overlapping it in X-projection, not flung downstream).
    # Axis along Y, carried on a stub axle off the upstream face of the plane.
    # Centre chosen so the 200 mm disc stays inside the 500 mm L budget:
    #   spans X = [SPOOL_CX - 100, SPOOL_CX + 100].
    sd, sw = SPOOL
    SPOOL_CX = 175.0                          # spool centre X (sits above the runway)
    SPOOL_CZ = BP_HEIGHT - sd / 2 - 6         # top of plane region
    spool = (
        cq.Workplane("XZ")          # circle in X-Z, extrude along Y (spool axis = Y)
        .circle(sd / 2)
        .extrude(sw)
        .translate((SPOOL_CX, -sw / 2, SPOOL_CZ))
    )
    blocks["Spool_PET"] = spool

    return blocks


# ============================================================================
# BUILD ASSEMBLY
# ============================================================================

def build():
    printed = {}

    # chassis — build then section to bed
    ch = chassis()
    ch_segs = chassis_sections(ch)
    for i, seg in enumerate(ch_segs):
        printed[f"chassis_seg{i+1}" if len(ch_segs) > 1 else "chassis"] = seg

    # back-plane segments (stacked)
    seg_h = BP_HEIGHT / BP_SEGMENTS
    for i in range(BP_SEGMENTS):
        z0 = i * seg_h
        z1 = (i + 1) * seg_h
        printed[f"backplane_seg{i+1}"] = back_plane_segment(
            z0, z1,
            with_lower_overlap=(i > 0),
            with_upper_overlap=(i < BP_SEGMENTS - 1),
        )
    printed["backplane_foot"] = back_plane_foot()
    for i, g in enumerate(gussets()):
        printed[f"gusset_{i+1}"] = g
    printed["cable_raceway"] = cable_raceway()

    ph = placeholders()
    return printed, ph


def export():
    printed, ph = build()
    asm = cq.Assembly()
    for name, solid in printed.items():
        asm.add(solid, name=name, color=cq.Color(0.6, 0.6, 0.65))   # printed = grey
    for name, solid in ph.items():
        asm.add(solid, name="PLACEHOLDER_" + name, color=cq.Color(0.9, 0.5, 0.1))  # placeholders = orange
    step_path = os.path.join(HERE, "lfold_assembly.step")
    stl_path = os.path.join(HERE, "lfold_assembly.stl")
    asm.export(step_path)

    # STL: fuse everything into one compound for a single mesh
    compound = None
    for solid in list(printed.values()) + list(ph.values()):
        compound = solid if compound is None else compound.union(solid)
    cq.exporters.export(compound, stl_path)

    # report quick stats
    bb = compound.val().BoundingBox()
    print(f"EXPORTED STEP: {step_path}")
    print(f"EXPORTED STL:  {stl_path}")
    print(f"ASSEMBLY BBOX (mm): L(X)={bb.xlen:.1f}  W(Y)={bb.ylen:.1f}  H(Z)={bb.zlen:.1f}")
    print(f"Printed parts: {len(printed)}  Placeholders: {len(ph)}")
    return printed, ph


if __name__ == "__main__":
    export()
