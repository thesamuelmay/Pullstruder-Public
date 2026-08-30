"""
Autonomous QA harness for the Pullstruder spine model.

Loads the exported STEP, runs the in-memory parametric model for per-part
checks, and asserts the 6 QA gates. Prints a machine-readable result block
that the loop driver parses; exits non-zero on any FAIL.
"""
import sys
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M   # the parametric model lives alongside this file

ENV_MAX = (500.0, 200.0, 300.0)   # L x W x H envelope limit (mm)
BED = M.BED                        # parameterised bed (confirmed 256 mm school printer)
WALL_MIN = M.WALL_MIN
CHAN_MIN = 8.0                     # min clear channel each side (mm)

results = []  # (gate, status, detail)

def add(gate, ok, detail):
    results.append((gate, "PASS" if ok else "FAIL", detail))
    return ok

# --- Rebuild printed parts in memory for per-part geometry checks ---
printed, placeholders, slot_dims, rail_dims = M.build_all()

# ---------------------------------------------------------------------------
# GATE 1: each printed part solid valid
# ---------------------------------------------------------------------------
g1_ok = True
g1_detail = []
for name, wp in printed.items():
    shape = wp.val()
    valid = BRepCheck_Analyzer(shape.wrapped).IsValid()
    g1_detail.append(f"{name}={'OK' if valid else 'INVALID'}")
    g1_ok = g1_ok and valid
add("G1 printed-part validity", g1_ok, "; ".join(g1_detail))

# ---------------------------------------------------------------------------
# GATE 2: assembly bbox <= envelope  (printed + placeholders, the packaged machine)
# ---------------------------------------------------------------------------
all_wps = list(printed.values()) + list(placeholders.values())
xs_min = ys_min = zs_min = 1e9
xs_max = ys_max = zs_max = -1e9
for wp in all_wps:
    bb = wp.val().BoundingBox()
    xs_min = min(xs_min, bb.xmin); xs_max = max(xs_max, bb.xmax)
    ys_min = min(ys_min, bb.ymin); ys_max = max(ys_max, bb.ymax)
    zs_min = min(zs_min, bb.zmin); zs_max = max(zs_max, bb.zmax)
L = xs_max - xs_min; W = ys_max - ys_min; H = zs_max - zs_min
g2_ok = (L <= ENV_MAX[0] and W <= ENV_MAX[1] and H <= ENV_MAX[2])
add("G2 envelope <=500x200x300", g2_ok,
    f"actual L={L:.1f} W={W:.1f} H={H:.1f} (limit {ENV_MAX})")

# ---------------------------------------------------------------------------
# GATE 3: each printed part fits the bed BED x BED x BED
# ---------------------------------------------------------------------------
g3_ok = True
g3_detail = []
for name, wp in printed.items():
    bb = wp.val().BoundingBox()
    # part can be oriented freely for printing: check sorted dims vs sorted bed
    dims = sorted([bb.xlen, bb.ylen, bb.zlen])
    bed = sorted([BED, BED, BED])
    fits = all(d <= b + 1e-6 for d, b in zip(dims, bed))
    g3_detail.append(f"{name}=({bb.xlen:.0f},{bb.ylen:.0f},{bb.zlen:.0f}){'OK' if fits else 'TOOBIG'}")
    g3_ok = g3_ok and fits
add(f"G3 fits bed {BED:.0f}^3 (confirmed 256 mm bed)", g3_ok, "; ".join(g3_detail))

# ---------------------------------------------------------------------------
# GATE 4: keyed mate + no module bbox overlap along spine
# ---------------------------------------------------------------------------
# 4a parametric mate: every module slot must equal rail + clearance and seat.
mate_ok = True
mate_detail = []
for mod, sd in slot_dims.items():
    w_ok = abs(sd["width"] - (rail_dims["width"] + 2 * M.CLEARANCE)) < 1e-6
    h_ok = sd["height"] >= rail_dims["height"]  # slot deep enough for rail
    fit_ok = sd["width"] > rail_dims["width"]   # slides on (slot > rail)
    ok = w_ok and h_ok and fit_ok
    mate_detail.append(f"{mod}: slotW={sd['width']:.2f} railW={rail_dims['width']:.2f} {'OK' if ok else 'BAD'}")
    mate_ok = mate_ok and ok
# 4b no overlap of module bodies along X
mod_keys = ["module_stripper", "module_hotend", "module_cooling", "module_hall_reserved"]
spans = []
for k in mod_keys:
    bb = printed[k].val().BoundingBox()
    spans.append((k, bb.xmin, bb.xmax))
spans.sort(key=lambda s: s[1])
overlap_ok = True
for i in range(len(spans) - 1):
    if spans[i][2] > spans[i+1][1] + 1e-6:
        overlap_ok = False
        mate_detail.append(f"OVERLAP {spans[i][0]}({spans[i][2]:.1f}) vs {spans[i+1][0]}({spans[i+1][1]:.1f})")
add("G4 keyed mate + no module overlap", mate_ok and overlap_ok,
    "; ".join(mate_detail) + f" | order={[s[0].split('_')[1] for s in spans]}")

# ---------------------------------------------------------------------------
# GATE 5: min designed wall >= WALL_MIN
# ---------------------------------------------------------------------------
# Parametric audit of the thinnest designed walls in the model.
walls = {
    "channel_wall": M.CHAN_WALL,
    "module_wall": M.MOD_WALL,
    "flange_t": M.FLANGE_T,
    "web_t": M.WEB_T,
    "cover_t": M.COVER_T,
    "mod_base_t": M.MOD_BASE_T,
}
min_wall = min(walls.values())
g5_ok = min_wall >= WALL_MIN - 1e-9
add(f"G5 min wall >= {WALL_MIN} mm", g5_ok,
    f"min designed wall={min_wall:.2f} ({min(walls, key=walls.get)})")

# ---------------------------------------------------------------------------
# GATE 6: cable channel clear section >= 8x8 mm
# ---------------------------------------------------------------------------
g6_ok = (M.CHAN_CLEAR_W >= CHAN_MIN and M.CHAN_CLEAR_H >= CHAN_MIN)
add(f"G6 channel clear >= {CHAN_MIN}x{CHAN_MIN} mm", g6_ok,
    f"clear={M.CHAN_CLEAR_W:.1f}x{M.CHAN_CLEAR_H:.1f} mm")

# ---------------------------------------------------------------------------
# Optionally re-load the exported STEP to confirm it reads back & is valid
# ---------------------------------------------------------------------------
step_ok = True
step_detail = ""
if len(sys.argv) > 1:
    try:
        imported = cq.importers.importStep(sys.argv[1])
        sv = imported.val()
        step_ok = BRepCheck_Analyzer(sv.wrapped).IsValid()
        bb = sv.BoundingBox()
        step_detail = f"reimport OK valid={step_ok} bbox=({bb.xlen:.0f},{bb.ylen:.0f},{bb.zlen:.0f})"
    except Exception as e:
        step_ok = False
        step_detail = f"reimport FAILED: {e}"
    add("G7 STEP reimport valid", step_ok, step_detail)

# ---------------------------------------------------------------------------
print("=== QA RESULTS ===")
all_ok = True
for gate, status, detail in results:
    print(f"[{status}] {gate} :: {detail}")
    all_ok = all_ok and (status == "PASS")
print(f"=== OVERALL: {'PASS' if all_ok else 'FAIL'} ===")
sys.exit(0 if all_ok else 1)
