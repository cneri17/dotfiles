#!/bin/sh
# Symlinks every file under .config/ and .local/bin/ in this repo into the
# matching path under $HOME, then regenerates the Hyprland .lua files from
# their .json sources. Safe to re-run.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"

# openSUSE-specific: install every package these dotfiles assume is present.
# Package names verified against a working machine via `rpm -qf` on each
# binary, not guessed. On any other distro this just skips with a note -
# see README.md for the general prerequisite list to translate by hand.
if command -v zypper >/dev/null 2>&1; then
    echo "Installing required packages via zypper (will prompt for your sudo password)..."
    sudo zypper --non-interactive install \
        pavucontrol NetworkManager-connection-editor blueman grim slurp swappy \
        wl-clipboard cliphist brightnessctl playerctl wireplumber hypridle hyprlock \
        hyprpaper waypaper kitty wofi mako hyprland waybar yazi python313-tk \
        thunar papirus-icon-theme papirus-folders sassc
else
    echo "zypper not found - skipping package install (not openSUSE?)."
    echo "See README.md for the list of packages these dotfiles expect."
fi

# Deep-black/green GTK theme for Thunar etc. Graphite isn't packaged for
# openSUSE, so it's built from source into a cache dir outside the repo
# (idempotent - re-running just re-clones/re-installs the same variant).
# gtk-3.0/gtk-4.0 settings.ini (tracked below, under .config/) point at the
# resulting "Graphite-green-Dark" theme name and Papirus-Dark icons.
if command -v git >/dev/null 2>&1 && command -v sassc >/dev/null 2>&1; then
    GRAPHITE_SRC="$HOME/.cache/dotfiles-vendor/Graphite-gtk-theme"
    mkdir -p "$(dirname "$GRAPHITE_SRC")"
    if [ -d "$GRAPHITE_SRC" ]; then
        git -C "$GRAPHITE_SRC" pull --ff-only
    else
        git clone --depth=1 https://github.com/vinceliuice/Graphite-gtk-theme.git "$GRAPHITE_SRC"
    fi
    "$GRAPHITE_SRC/install.sh" -t green -c dark --tweaks black -l
else
    echo "git/sassc not found - skipping Graphite GTK theme install."
fi

if command -v papirus-folders >/dev/null 2>&1; then
    papirus-folders -C green -t Papirus-Dark
fi
sh "$REPO/.local/bin/papirus-recolor-folders.sh"

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
