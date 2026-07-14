#!/bin/sh
# Symlinks every file under .config/ and .local/bin/ in this repo into the
# matching path under $HOME, then regenerates the Hyprland .lua files from
# their .json sources. Safe to re-run.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"

link() {
    src="$1"
    dst="$HOME/${src#"$REPO"/}"
    mkdir -p "$(dirname "$dst")"
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        mv "$dst" "$dst.bak"
        echo "backed up existing $dst -> $dst.bak"
    fi
    ln -sf "$src" "$dst"
    echo "linked: $dst -> $src"
}

# monitors.json is machine-specific (real output names/positions differ per
# box) - seed it only if the machine doesn't already have one, and never
# symlink it, so each machine keeps its own independent copy. Use the config
# editor's "Detect connected monitors" button (SUPER+SHIFT+E) to fill it in
# for real once Hyprland is running.
if [ ! -e "$HOME/.config/hypr/monitors.json" ]; then
    mkdir -p "$HOME/.config/hypr"
    cp "$REPO/.config/hypr/monitors.json" "$HOME/.config/hypr/monitors.json"
    echo "seeded: $HOME/.config/hypr/monitors.json (generic default)"
fi

find "$REPO/.config" "$REPO/.local" -type f | while read -r f; do
    case "$f" in
        */hypr/monitors.json) continue ;;
    esac
    link "$f"
done

chmod +x "$REPO/.local/bin/"*.sh "$REPO/.local/bin/"*.py 2>/dev/null || true

python3 "$REPO/.local/bin/hypr_config_lib.py"
echo "regenerated keybinds.lua / appearance.lua / monitors.lua / keybinds.txt"

if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] && command -v hyprctl >/dev/null 2>&1; then
    hyprctl reload
    echo "reloaded Hyprland"
fi

cat <<'EOF'

Done. See README.md for required packages if this is a fresh machine.
Then press SUPER+SHIFT+E once to open the config editor, go to the
Monitors tab, and click "Detect connected monitors" to fill in this
machine's real layout.
EOF
