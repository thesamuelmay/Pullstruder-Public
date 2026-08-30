"""
Autonomous QA checker for the STACKED DECK assembly.
Loads exported STEP files and asserts the 6 QA constraints. Prints a PASS/FAIL
table and exits non-zero on any failure so the loop can detect it.

Run:  cd /tmp && uv run --python 3.12 --with cadquery python qa_check.py
"""
import os
import sys
import glob
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- constraints (mirror model.py) ----
ENV_MAX = (500.0, 200.0, 300.0)        # constraint #2 envelope
ORIG    = (554.0, 220.0, 325.0)        # original machine envelope
BED     = 256.0                        # constraint #3 (confirmed 256 mm school printer)
MIN_INTERDECK = 15.0                   # constraint #4 air gap minimum
MIN_WALL = 2.0                         # constraint #6

# Discover printed parts dynamically from exported part_*.step files.
PRINTED_PARTS = sorted(
    os.path.basename(p)[5:-5]                      # strip "part_" and ".step"
    for p in glob.glob(os.path.join(HERE, "part_*.step"))
)

results = []   # (name, pass_bool, detail)


def add(name, ok, detail=""):
    results.append((name, ok, detail))


def load_part(name):
    path = os.path.join(HERE, f"part_{name}.step")
    return cq.importers.importStep(path)


def bbox_of(wp):
    bb = wp.val().BoundingBox()
    return bb


# -------------------------------------------------------------------------
# Load all printed parts and the placeholders (from the assembly step).
# -------------------------------------------------------------------------
parts = {}
for p in PRINTED_PARTS:
    parts[p] = load_part(p)

asm = cq.importers.importStep(os.path.join(HERE, "stacked_assembly.step"))


# =========================================================================
# CHECK 1 — each PRINTED part solid is valid
# =========================================================================
for p in PRINTED_PARTS:
    shp = parts[p].val()
    valid = BRepCheck_Analyzer(shp.wrapped).IsValid()
    add(f"1. valid:{p}", bool(valid), f"IsValid={valid}")


# =========================================================================
# CHECK 2 — assembly bbox <= 500 x 200 x 300 mm
# =========================================================================
abb = asm.val().BoundingBox()
ax, ay, az = abb.xlen, abb.ylen, abb.zlen
env_ok = (ax <= ENV_MAX[0] + 1e-6 and ay <= ENV_MAX[1] + 1e-6 and az <= ENV_MAX[2] + 1e-6)
fp_red = (1 - (ax * ay) / (ORIG[0] * ORIG[1])) * 100
vol_red = (1 - (ax * ay * az) / (ORIG[0] * ORIG[1] * ORIG[2])) * 100
add("2. envelope<=500x200x300", env_ok,
    f"actual {ax:.1f}x{ay:.1f}x{az:.1f} | footprint -{fp_red:.1f}% vol -{vol_red:.1f}% vs original")


# =========================================================================
# CHECK 3 — each PRINTED part fits the bed (BED x BED x BED)
# =========================================================================
for p in PRINTED_PARTS:
    bb = bbox_of(parts[p])
    fits = bb.xlen <= BED and bb.ylen <= BED and bb.zlen <= BED
    add(f"3. bed-fit:{p}", fits,
        f"{bb.xlen:.1f}x{bb.ylen:.1f}x{bb.zlen:.1f} vs BED={BED} (confirmed 256 mm)")


# =========================================================================
# CHECK 4 — inter-deck gap >= MIN_INTERDECK AND electronics don't collide
# with the heat shield / top deck.
# =========================================================================
# Air gap = shield underside Z - tray lid top Z. Aggregate across any sections.
def logical_zextent(prefix):
    zmins, zmaxs = [], []
    for nm, wp in parts.items():
        base = nm.split("_A")[0].split("_B")[0]
        if base == prefix or nm == prefix:
            bb = wp.val().BoundingBox()
            zmins.append(bb.zmin)
            zmaxs.append(bb.zmax)
    return min(zmins), max(zmaxs)

lid_zmin, lid_zmax = logical_zextent("lid")
shield_zmin, shield_zmax = logical_zextent("shield")
deck_zmin, deck_zmax = logical_zextent("deck")

tray_lid_top = lid_zmax             # top of closed lid
shield_bot = shield_zmin
air_gap = shield_bot - tray_lid_top
add("4a. air-gap>=min", air_gap >= MIN_INTERDECK - 1e-6,
    f"air_gap={air_gap:.1f} mm (min {MIN_INTERDECK})")

# Electronics placeholders live below the lid (inside tray). Their top must be
# below the shield underside and below the deck. Pull placeholder z-extents
# from the assembly by scanning solids that sit in the tray Y/Z band.
# Simpler + robust: re-import the placeholder blocks by re-running geometry math.
# The tallest tray-internal item is the PSU top and the cnc_shield top.
import importlib.util
spec = importlib.util.spec_from_file_location("model", os.path.join(HERE, "model.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
ph = model.make_placeholders()

# Bottom-tray electronics names
tray_elec = ["arduino", "cnc_shield", "psu", "lcd"]
max_elec_top = max(ph[n].val().BoundingBox().zmax for n in tray_elec)
no_collide = max_elec_top <= shield_bot + 1e-6 and max_elec_top <= deck_zmin + 1e-6
add("4b. electronics clear of shield/deck", no_collide,
    f"tallest tray item top={max_elec_top:.1f} <= shield_bot={shield_bot:.1f}")


# =========================================================================
# CHECK 5 — service lid exports as its own solid(s) (removable, not fused
# to the tray). The lid must exist as its own part file(s), distinct from tray.
# =========================================================================
lid_names = [n for n in parts if n.split("_A")[0].split("_B")[0] == "lid" or n == "lid"]
tray_names = [n for n in parts if n.split("_A")[0].split("_B")[0] == "tray" or n == "tray"]
lid_valid = all(BRepCheck_Analyzer(parts[n].val().wrapped).IsValid() for n in lid_names)
lid_is_own = len(lid_names) >= 1 and lid_valid and not set(lid_names) & set(tray_names)
add("5. lid is separate removable solid", bool(lid_is_own),
    f"lid parts={lid_names}, distinct from tray={tray_names}")


# =========================================================================
# CHECK 6 — min designed wall >= 2.0 mm (parametric var)
# =========================================================================
wall = model.WALL
min_wall_ok = wall >= MIN_WALL and model.TRAY_WALL_T >= MIN_WALL and \
              model.DECK_T >= MIN_WALL and model.SHIELD_T >= MIN_WALL
add("6. min wall>=2.0mm", bool(min_wall_ok),
    f"WALL={wall} tray_wall={model.TRAY_WALL_T} deck={model.DECK_T} shield={model.SHIELD_T}")


# =========================================================================
# REPORT
# =========================================================================
print("\n=== QA RESULTS ===")
allpass = True
for name, ok, detail in results:
    tag = "PASS" if ok else "FAIL"
    if not ok:
        allpass = False
    print(f"[{tag}] {name:42s} {detail}")

print("\nENVELOPE:", f"{ax:.1f} x {ay:.1f} x {az:.1f} mm",
      f"| footprint -{fp_red:.1f}% | volume -{vol_red:.1f}% vs {ORIG}")
print("OVERALL:", "ALL PASS" if allpass else "FAILURES PRESENT")
sys.exit(0 if allpass else 1)
