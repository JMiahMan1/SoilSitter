#!/usr/bin/env bash
# Rebuild every STL and the diagrams. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-.venv-cad/bin/python}
[ -x "$PY" ] || { echo "no $PY - run 'make venv' first" >&2; exit 1; }

for rim in 6 9 12; do
    echo "== body/rim $rim mm"
    "$PY" cad/soilsitter.py --rim-gap "$rim"
done

echo "== diagrams"
"$PY" cad/render.py
echo "done: $(ls stl/*.stl | wc -l | tr -d ' ') STLs, $(ls docs/diagrams/*.png | wc -l | tr -d ' ') images"
