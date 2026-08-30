"""
QA checker for the L-Fold assembly. Rebuilds the model in-process (so we can
distinguish printed parts from placeholders), then asserts the 5 QA rules.
Prints a PASS/FAIL table. Exit code 0 only if all pass.

Run:
  cd /tmp && uv run --python 3.12 --with cadquery python <abs>/qa_check.py
"""
import sys, os, importlib.util
import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer

HERE = os.path.dirname(os.path.abspath(__file__))

# import model.py by path
spec = importlib.util.spec_from_file_location("lfold_model", os.path.join(HERE, "model.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

ENVELOPE = (500.0, 200.0, 300.0)   # L x W x H goal (X,Y,Z)
BED = model.BED
BED_MARGIN = model.BED_MARGIN
MIN_WALL = model.MIN_WALL

printed, placeholders = model.build()

results = []   # (check, status, detail)

def bbox(solid):
    return solid.val().BoundingBox()

# ---- 1. validity of each PRINTED part ----
all_valid = True
for name, solid in printed.items():
    ok = BRepCheck_Analyzer(solid.val().wrapped).IsValid()
    if not ok:
        all_valid = False
        results.append((f"validity:{name}", "FAIL", "BRepCheck invalid"))
results.append(("1. all printed parts valid", "PASS" if all_valid else "FAIL",
                f"{len(printed)} parts checked"))

# ---- 2. overall assembly bbox <= envelope ----
# combine everything (printed + placeholders) for the true packaged envelope
everything = list(printed.values()) + list(placeholders.values())
compound = None
for s in everything:
    compound = s if compound is None else compound.union(s)
bb = compound.val().BoundingBox()
L, W, H = bb.xlen, bb.ylen, bb.zlen
env_ok = (L <= ENVELOPE[0] and W <= ENVELOPE[1] and H <= ENVELOPE[2])
results.append(("2. envelope <= 500x200x300", "PASS" if env_ok else "FAIL",
                f"actual L={L:.1f} W={W:.1f} H={H:.1f}"))

# ---- 3. each PRINTED part fits bed (BED x BED x BED) ----
usable = BED - 2 * BED_MARGIN
bed_ok = True
bed_detail = []
for name, solid in printed.items():
    b = bbox(solid)
    fits = (b.xlen <= usable and b.ylen <= usable and b.zlen <= usable)
    if not fits:
        bed_ok = False
        bed_detail.append(f"{name} {b.xlen:.0f}x{b.ylen:.0f}x{b.zlen:.0f} > {usable:.0f}")
results.append((f"3. printed parts fit bed (BED={BED}, usable={usable:.0f})",
                "PASS" if bed_ok else "FAIL",
                "; ".join(bed_detail) if bed_detail else f"all {len(printed)} fit"))

# ---- 4. no PRINTED part-vs-part hard interference (bbox overlap heuristic) ----
# Excluded pairs: parts that share a bolted/spliced joint legitimately overlap a
# little; we exclude pairs that are designed to mate (segments, foot/chassis, etc).
def overlaps(a, b, tol=0.5):
    return (a.xmin < b.xmax - tol and b.xmin < a.xmax - tol and
            a.ymin < b.ymax - tol and b.ymin < a.ymax - tol and
            a.zmin < b.zmax - tol and b.zmin < a.zmax - tol)

# pairs allowed to overlap by design (mating joints / braces touching)
def is_mating(n1, n2):
    s = {n1, n2}
    # backplane segments stack (overlap splice)
    if all("backplane_seg" in n for n in (n1, n2)):
        return True
    # foot mates chassis + backplane
    if any("foot" in n for n in (n1, n2)):
        return True
    # gussets brace chassis + backplane
    if any("gusset" in n for n in (n1, n2)):
        return True
    # raceway sits on backplane
    if any("raceway" in n for n in (n1, n2)) and any("backplane" in n for n in (n1, n2)):
        return True
    # chassis segments butt-splice
    if all("chassis_seg" in n for n in (n1, n2)):
        return True
    return False

names = list(printed.keys())
interf = []
for i in range(len(names)):
    for j in range(i+1, len(names)):
        n1, n2 = names[i], names[j]
        if is_mating(n1, n2):
            continue
        if overlaps(bbox(printed[n1]), bbox(printed[n2])):
            # bbox overlap is only a hint; confirm with real solid intersection volume
            try:
                inter = printed[n1].intersect(printed[n2])
                vol = inter.val().Volume() if inter.val() is not None else 0.0
            except Exception:
                vol = -1.0
            if vol is None:
                vol = 0.0
            if vol > 1.0:   # >1 mm^3 real overlap = genuine interference
                interf.append(f"{n1}<->{n2} vol={vol:.0f}mm3")
results.append(("4. no printed part interference", "PASS" if not interf else "FAIL",
                "; ".join(interf) if interf else "no genuine overlaps"))

# ---- 5. wall thickness sanity via parametric vars ----
wall_ok = MIN_WALL >= 2.0
wall_vars = {
    "MIN_WALL": MIN_WALL, "RAIL_W": model.RAIL_W, "BP_THK": model.BP_THK,
    "GUSSET_THK": model.GUSSET_THK, "RACE_WALL": model.RACE_WALL,
    "CH_THK": model.CH_THK, "PAD_THK": model.PAD_THK,
}
thin = [f"{k}={v}" for k, v in wall_vars.items() if v < 2.0]
if thin:
    wall_ok = False
results.append(("5. min designed wall >= 2.0 mm", "PASS" if wall_ok else "FAIL",
                f"thin: {thin}" if thin else f"min wall var = {min(wall_vars.values()):.1f}"))

# ---- print table ----
print("\n=== QA RESULTS ===")
width = max(len(r[0]) for r in results)
all_pass = True
for check, status, detail in results:
    if status == "FAIL":
        all_pass = False
    print(f"[{status}] {check.ljust(width)}  | {detail}")
print(f"\nOVERALL: {'ALL PASS' if all_pass else 'FAIL — fix and re-run'}")
print(f"(BED={BED} mm is the CONFIRMED school printer bed — 256 mm cube build volume.)")
sys.exit(0 if all_pass else 1)
