#!/bin/sh
# Overrides Papirus-Dark's folder icons with the same bright green used for
# Hyprland's active window border (see appearance.json active_color_1),
# since papirus-folders' built-in "green" preset is a duller olive tone.
# Writes to ~/.icons (highest icon lookup priority) so the system package is
# never touched and survives updates/reinstalls. Safe to re-run.
set -eu

THEME_DIR="/usr/share/icons/Papirus-Dark"
OVERRIDE_DIR="$HOME/.icons/Papirus-Dark"

if [ ! -d "$THEME_DIR" ]; then
    echo "Papirus-Dark not installed - skipping folder recolor."
    exit 0
fi

for size_dir in "$THEME_DIR"/*/places; do
    size="$(basename "$(dirname "$size_dir")")"
    mkdir -p "$OVERRIDE_DIR/$size/places"
    for src in "$size_dir"/folder-green.svg "$size_dir"/folder-green-*.svg \
               "$size_dir"/user-green.svg "$size_dir"/user-green-*.svg; do
        [ -f "$src" ] || continue
        name="$(basename "$src" | sed 's/-green//')"
        sed -e 's/#2f3e1f/#304d0f/gI' \
            -e 's/#60924b/#73ba25/gI' \
            -e 's/#87b158/#88d633/gI' \
            "$src" > "$OVERRIDE_DIR/$size/places/$name"
    done
done

echo "Recolored Papirus-Dark folders to bright green in $OVERRIDE_DIR"
