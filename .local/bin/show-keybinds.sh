#!/usr/bin/bash
# Shows the Hyprland keybind cheatsheet as a read-only wofi dialog,
# sized to fit within the focused monitor's vertical resolution
# (wofi's list scrolls internally if it still doesn't all fit).

screen_h=$(hyprctl monitors -j 2>/dev/null | python3 -c "
import json, sys
try:
    mons = json.load(sys.stdin)
    m = next((m for m in mons if m.get('focused')), mons[0])
    print(int(m['height'] / m['scale']))
except Exception:
    print(800)
" 2>/dev/null)
screen_h=${screen_h:-800}

# Cap well under the full screen height to leave room for the bar/margins.
height=$(( screen_h * 80 / 100 ))
if [ "$height" -gt 700 ]; then height=700; fi

cat ~/.config/hypr/keybinds.txt | wofi \
    --dmenu \
    --prompt "Keybinds (Esc to close)" \
    --width 640 \
    --height "$height" \
    --location center \
    >/dev/null
