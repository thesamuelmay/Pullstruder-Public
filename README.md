# Pullstruder

Open-source CAD for the **Pullstruder**: a school-affordable, single-chassis machine that
turns waste plastic into usable 3D-printing filament on site, so a school can close its own
plastic loop instead of shipping waste out and buying filament back in.

Designed and built by **Samuel Lundgren May** as a VCE Systems Engineering project, 2026.

Everything here is parametric CadQuery source plus exported geometry. Change a dimension at the
top of the model file, re-run one command, and the whole machine rebuilds.

## What is in this repo

Three design concepts were developed and evaluated. All three are published, because the two
that were rejected are part of how the final design was chosen.

| Folder | Concept | Status |
| :-- | :-- | :-- |
| `concepts/spine-modules/` | Rigid spine with clip-on modules | ✅ **Built.** The selected design |
| `concepts/l-fold/` | L-shaped folding chassis | Considered, rejected |
| `concepts/stacked-deck/` | Stacked-deck layout | Considered, rejected |

Inside `concepts/spine-modules/`:

- `cad/` — the concept-stage block model
- `cad_detailed/` — the detailed model: real wall thicknesses, edge fillets, M3/M4 bolt holes,
  captive hex-nut pockets, and accurate mounting-hole patterns for the bought components
- `concept.md`, `design_decisions*.md`, `bom.md`, `qa_report.md` — the reasoning behind the
  geometry, written up as the design developed

## The 11 printed parts

Every custom structural part is 3D-printable. Each is exported as both `.step` (editable CAD)
and `.stl` (ready to slice):

`spine_segment_A` · `spine_segment_B` · `splice_plate` · `cover_A` · `cover_B` ·
`module_stripper` · `module_hotend` · `module_cooling` · `module_hall` · `winder_riser` ·
`module_controller`

All fit a 256 mm bed with at least 2.0 mm walls. The spine is about 380 mm long, longer than the bed,
so it prints as two segments joined by a bolted splice plate.

## Regenerating the geometry

You need [uv](https://docs.astral.sh/uv/). It fetches Python and CadQuery for you, so there is
nothing else to install.

From `concepts/spine-modules/cad_detailed/`:

```bash
# Rebuild every part and export STEP + STL
uv run --python 3.12 --with cadquery python model_detailed.py out

# Check the result against the nine QA gates
uv run --python 3.12 --with cadquery python qa_check_detailed.py out/spine_detailed_assembly.step
```

The first command writes 27 files and prints `Printed parts: 11`. The second rebuilds the model
in memory and runs gates G1 to G9, covering part validity, the overall envelope, bed fit,
minimum wall thickness, the filament channel, STEP re-import, fastener clearances, and
hole-pattern alignment against the real bought parts. It exits non-zero if any gate fails.

The other two concepts have the same shape: `model.py` and `qa_check.py` in each `cad/` folder.

## Units and conventions

Millimetres throughout. The coordinate datum follows AS 1100, with the origin at the spine:
X along the machine centreline (the direction filament travels), Y lateral, Z vertical.

Bought components (stepper motor, hotend, Arduino, fans, PSU) are modelled as `PLACEHOLDER_*`
stand-ins with accurate external envelopes and real mounting-hole positions, so the printed
parts line up with the actual hardware.

## Licence

MIT. See [LICENSE](LICENSE). You are free to build, modify, and sell this; please keep the
copyright notice.
