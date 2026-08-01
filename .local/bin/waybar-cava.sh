#!/usr/bin/bash
# Waybar custom module: renders cava's output as inline Unicode bars.
# Runs continuously; waybar reads it in "tail" mode, one line per frame.

bars=(▁ ▂ ▃ ▄ ▅ ▆ ▇ █)

cava -p ~/.config/cava/config-waybar | while IFS=';' read -ra values; do
    out=""
    for v in "${values[@]}"; do
        [ -n "$v" ] && out+="${bars[v]}"
    done
    printf '%s\n' "$out"
done
