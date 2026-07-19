#!/usr/bin/bash
# Waybar custom module: reports pending zypper updates on openSUSE Tumbleweed.
# Reads zypper's local repo cache only (no network refresh), so it's safe to
# poll on an interval. Click actions (see waybar config) trigger the refresh.

set -o pipefail

if ! command -v zypper >/dev/null 2>&1; then
    jq -nc '{text: "!", tooltip: "zypper not found", class: "error"}'
    exit 0
fi

updates=$(LC_ALL=C zypper --non-interactive lu 2>/dev/null | awk -F'|' '
    /^v/ {
        for (i = 1; i <= NF; i++) { gsub(/^[ \t]+|[ \t]+$/, "", $i) }
        print $3 "  " $4 " -> " $5
    }
')

count=$(printf '%s\n' "$updates" | grep -c . || true)

if [ "$count" -gt 0 ]; then
    preview=$(printf '%s\n' "$updates" | sort | head -n 20)
    if [ "$count" -gt 20 ]; then
        preview="${preview}
... and $((count - 20)) more"
    fi
    tooltip="$count update$([ "$count" -eq 1 ] || echo s) available

$preview"
    jq -nc --arg text "$count" --arg tooltip "$tooltip" \
        '{text: $text, tooltip: $tooltip, class: "has-updates"}'
else
    jq -nc '{text: "0", tooltip: "System up to date", class: "no-updates"}'
fi
