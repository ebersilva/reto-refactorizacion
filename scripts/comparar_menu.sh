#!/bin/bash
# Compara el menú interactivo de `main` (código original) contra el working tree
# usando la misma entrada scriptada. Compara stdout y el JSON guardado (sin fechas).
# Uso: scripts/comparar_menu.sh [rama_base]   (por defecto: main)
set -euo pipefail
raiz=$(git rev-parse --show-toplevel)
base=${1:-main}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/orig" "$tmp/nuevo"
git -C "$raiz" archive "$base" src | tar -x -C "$tmp/orig"
cp -r "$raiz/src" "$tmp/nuevo/"
for d in orig nuevo; do
  git -C "$raiz" show "$base:datos_ejemplo.json" > "$tmp/$d/src/datos_ejemplo.json"
  (cd "$tmp/$d/src" && python3 main.py < "$raiz/scripts/sesion_menu.txt" > "$tmp/$d.out" 2>&1)
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); [v.pop("fecha") for v in d["ventas"]]; print(json.dumps(d, sort_keys=True))' \
    "$tmp/$d/src/datos_ejemplo.json" > "$tmp/$d.json"
done
diff "$tmp/orig.out" "$tmp/nuevo.out"
diff "$tmp/orig.json" "$tmp/nuevo.json"
echo "MENU IDENTICO ($(wc -l < "$tmp/nuevo.out") lineas de salida, JSON guardado igual)"
