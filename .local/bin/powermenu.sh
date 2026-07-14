#!/usr/bin/bash
# Wofi-driven power menu for Hyprland.

options="  Lock\n  Logout\n  Suspend\n  Reboot\n  Shutdown"

chosen=$(echo -e "$options" | wofi --dmenu --style ~/.config/wofi/powermenu.css --prompt "Power" --width 250 --height 250 --location center)

case "$chosen" in
    *Lock)     hyprlock ;;
    *Logout)   hyprctl dispatch 'hl.dsp.exit()' ;;
    *Suspend)  systemctl suspend ;;
    *Reboot)   systemctl reboot ;;
    *Shutdown) systemctl poweroff ;;
esac
