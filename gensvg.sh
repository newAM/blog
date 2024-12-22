#!/usr/bin/env bash
set -euo pipefail

for file in svgbob/*; do
    filename="${file##*/}"

    # svgbob --background white --fill-color '#222' --stroke-color '#222' "$file" > "content/images/${filename%.*}_light.svg"
    svgbob --background '#111' --fill-color '#ddd' --stroke-color '#ddd' "$file" > "content/images/${filename%.*}_dark.svg"
done
