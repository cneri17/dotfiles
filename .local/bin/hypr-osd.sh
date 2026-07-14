#!/bin/sh
# Volume/brightness control with swayosd feedback when available,
# falling back to plain wpctl/brightnessctl (no OSD) otherwise.

action="$1"

if command -v swayosd-client >/dev/null 2>&1; then
    case "$action" in
        vol-up)    exec swayosd-client --output-volume raise ;;
        vol-down)  exec swayosd-client --output-volume lower ;;
        vol-mute)  exec swayosd-client --output-volume mute-toggle ;;
        mic-mute)  exec swayosd-client --input-volume mute-toggle ;;
        bright-up)   exec swayosd-client --brightness raise ;;
        bright-down) exec swayosd-client --brightness lower ;;
    esac
fi

case "$action" in
    vol-up)    exec wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+ ;;
    vol-down)  exec wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- ;;
    vol-mute)  exec wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle ;;
    mic-mute)  exec wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle ;;
    bright-up)   exec brightnessctl set 5%+ ;;
    bright-down) exec brightnessctl set 5%- ;;
esac
