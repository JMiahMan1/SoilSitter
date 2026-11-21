# Print these, not those

Two folders, two different things. Same parts, different orientations, and only
one of them prints without support.

| Folder | What it is | Body, as measured |
|---|---|---|
| **`stl/print/`** | **Pre-rotated for printing. Use these.** | 2820 mm² of *bridged* area, widest span **27 mm**, nothing floating |
| `stl/` | The parts in **assembly position**, for CAD, dimensions and the diagrams | 6218 mm² of overhang, widest span **44 mm** — this one needs supports everywhere |

If your slicer wants supports all over the body, it is almost certainly the wrong
folder: check that you opened `stl/print/body_rim<N>.stl`.

The numbers above come from `cad/printability.py`, which measures each unsupported
span and how high it sits:

```bash
.venv-cad/bin/python cad/printability.py --rim 9
```

## What OrcaSlicer actually did with it

Measured, not assumed: OrcaSlicer 2.4.2, 0.4 mm nozzle, 0.20 mm layers, PLA,
`BLOCKS Pro S100` profile, on the exported files.

| Slice | Support moves | What that means |
|---|---|---|
| `print/body_rim9.stl`, supports **off** | **0** | Prints. The 82 x 27 ceiling is emitted as `Internal Bridge` (1513 moves) plus `Bridge` — spanned between walls, which is exactly what you want |
| `print/body_rim9.stl`, supports **on**, default profile | 22,615 | Fills the bay from z 4.5 to 57.5 **and** the probe cavity from z 34.5 to 140.5 |
| same, `bridge_no_support=1`, `max_bridge_length=40`, 60 deg | 14,303 | Cavity support disappears; the bay is still filled |
| `body_rim9.stl` (assembly position), supports on | 52,922 | The wrong file — see the table at the top |

So the part prints without support, but **a default slice will not agree with
you**. The reason is `max_bridge_length`, which defaults to **10 mm**: spans shorter
than that are treated as bridges, longer ones as overhangs. The bay's ceiling is
27 mm, so the slicer would rather grow a tower inside the bay — and that tower
cannot be pulled back out through the 27 mm opening, nor out of the 25 x 9 mm probe
cavity.

**Settings that matter**

- Supports: **off**. This is the whole trick; everything else is comfort.
- Brim 5-8 mm on the body, and slow the top third to ~40 mm/s — the sleeve is an
  87 mm cantilever and stiffness, not overhang, is the real risk.
- If you must slice with supports on for some other reason, set
  `bridge_no_support` ("don't support bridges") and raise `max_bridge_length` past
  30 mm, or you will spend an hour digging support out of two enclosed voids.

## What the body actually asks of the printer

In the print orientation (bay down, sleeve up) there are exactly two ceilings:

| Where | Area | Widest span | Height | What happens |
|---|---|---|---|---|
| Bay's inner ceiling | 2214 mm² | 27 mm | 57 mm | Bridges from all four walls. It is a closed span, not a floating plate — expect 0.2–0.5 mm of sag, which lands **inside** the bay and is invisible |
| Probe cavity's roof | 284 mm² | 11 mm | 140 mm | Bridges cleanly |
| Everything else | < 70 mm² each | ≤ 13 mm | — | Fillets and steps, all anchored |

Nothing in the body is a free-floating roof, so **supports are not required** — but
two settings matter:

- **Turn supports off** (or "support only from the build plate" plus "don't support
  bridges"). Support generated inside the bay cannot be removed through the 27 mm
  opening, and it would also fill the probe cavity.
- **Brim + slow first 40 mm.** The body is 144.5 mm tall and the sleeve is an
  87 mm cantilever above the bay, so this is a rigidity problem, not a support
  problem. Bed-slingers especially: 40 mm/s on the sleeve's top third.

The gaskets are 1 mm thick and 106 mm long; they need a clean, cool bed far more
than they need anything else.

## Where the manifest lives

`stl/print/manifest_rim<N>.json` records the chosen orientation, the bed contact,
and the overhang split for each part. `cad/orient.py` regenerates it by scoring all
24 axis-aligned orientations; `cad/check_fit.py` fails the build if a geometry
change brings back a free overhang.
