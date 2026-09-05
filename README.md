# Pullstruder

Design files for the **Pullstruder**: a school-affordable machine that turns waste plastic into
usable 3D-printing filament on site, so a school can close its own plastic loop instead of
shipping waste out and buying filament back in.

Designed and built by **Samuel Lundgren May** as a VCE Systems Engineering project, 2026.

## What is in this repo

Every part of the machine that was custom designed and 3D printed, as **3MF project files**.

The parts were modelled in **Autodesk Fusion 360** and prepared for printing in **Bambu Studio**.
Each `.3mf` here is the Bambu Studio project for that part: it carries the part geometry, the
plate layout it was printed on, and the print settings actually used. Opening one shows the part
exactly as it went to the printer.

Version numbers are the real design history, not tidy-ups after the fact. Where a part has
several versions, each one is a revision that was printed, assessed and changed.

### The machine

| File | Date | What it is |
| :-- | :-- | :-- |
| `Systems_V2_v01` to `v12` | 27 Jul to 11 Aug 2026 | The main machine assembly, twelve revisions |
| `Extruder_Full` | 24 May 2026 | Full extruder assembly |
| `Extruder_Module_Redesign_v01` | 13 Jun 2026 | Extruder module after redesign |
| `Cycloidal_Drive_v01` | 4 Sep 2026 | Cycloidal drive |

### Bottle cutter

| File | Date | What it is |
| :-- | :-- | :-- |
| `Bottle_Cutter_v02` to `v05` | 20 Mar to 4 May 2026 | Cutter body, four revisions |
| `Bottle_Cutter_Base_v01` | 5 May 2026 | Cutter base |
| `Bottle_Cutter_Fusion_More_Height` | 17 Aug 2026 | Taller revision |
| `Spinning_Bottle_Cap`, `_v02` | 28 Apr, 2 May 2026 | Spinning cap that feeds the bottle through the cutter |

### Housings, lids and covers

| File | Date | What it is |
| :-- | :-- | :-- |
| `Electrical_Lid_v01` | 17 Aug 2026 | Electrical enclosure lid |
| `Revised_Lids_v01` | 29 May 2026 | Revised lids |
| `Front_Cover_Screen_Revised` | 29 May 2026 | Front cover with screen cutout |
| `Switch_Backing_Fixed_v01` | 12 Jun 2026 | Switch backing plate |
| `Filament Catcher` | 14 Aug 2026 | Filament catcher |

### Test pieces

Printed to check a single property before committing to a full part.

| File | Date | What it was testing |
| :-- | :-- | :-- |
| `Thread_Test v01` | 13 Mar 2026 | Printed thread fit |
| `Housing_Curve_Test_V01` | 9 May 2026 | Curved housing wall |
| `TestPlate_v01`, `_v02` | 21 May 2026 | Plate geometry and fit |

## Opening the files

`.3mf` is an open format. Any of these will open the files:

- **Bambu Studio** (what they were made in), OrcaSlicer, or PrusaSlicer, to see the part on its
  print plate with the settings used
- **Autodesk Fusion 360**, or any CAD package that imports 3MF, to work with the geometry
- Windows **3D Viewer** or macOS **Preview**, to look at the shape without installing anything

## Licence

MIT. See [LICENSE](LICENSE). You are free to build, modify, and sell this; please keep the
copyright notice.
