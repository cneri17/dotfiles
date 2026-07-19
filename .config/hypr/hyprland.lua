-- Hyprland config (Lua, 0.55+) - openSUSE green/teal theme, laptop-tuned
-- https://wiki.hypr.land/Configuring/Start/

------------------
---- MONITORS ----
------------------

-- GUI-editable: SUPER+SHIFT+E, "Monitors" tab
-- generated into monitors.lua from monitors.json - do not edit that file by hand
require("monitors")

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORM", "wayland")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-------------------
---- AUTOSTART ----
-------------------

hl.on("hyprland.start", function()
    -- hyprpaper 0.8.3 speaks an older IPC protocol than Hyprland 0.55.4 expects
    -- (upstream hasn't caught up yet), so wallpaper is handled by waypaper/swaybg instead.
    hl.exec_cmd("waypaper --restore")
    hl.exec_cmd("sh -c 'command -v swayosd-server >/dev/null && exec swayosd-server'")
    hl.exec_cmd("waybar")
    hl.exec_cmd("mako")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("blueman-applet")
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
end)

-----------------------
---- LOOK AND FEEL ----
-----------------------

-- general/decoration/animations are GUI-editable: SUPER+SHIFT+E, "Appearance" tab
-- generated into appearance.lua from appearance.json - do not edit that file by hand
require("appearance")

hl.config({
    dwindle = {
        preserve_split = true,
    },
})

hl.config({
    master = {
        new_status = "master",
    },
})

hl.config({
    misc = {
        disable_hyprland_logo   = true,
        force_default_wallpaper = 0,
        vrr                     = 1,
        mouse_move_enables_dpms = true,
        key_press_enables_dpms  = true,
    },
})

hl.config({
    debug = {
        vfr = true,
    },
})

---------------
---- INPUT ----
---------------

hl.config({
    input = {
        kb_layout    = "us",
        follow_mouse = 1,
        sensitivity  = 0,

        touchpad = {
            natural_scroll        = true,
            tap_to_click          = true,
            disable_while_typing  = true,
            scroll_factor         = 0.6,
        },
    },
})

hl.gesture({
    fingers   = 3,
    direction = "horizontal",
    action    = "workspace",
})

---------------------
---- KEYBINDINGS ----
---------------------

-- GUI-editable: SUPER+SHIFT+E, "Keybinds" tab
-- generated into keybinds.lua from keybinds.json - do not edit that file by hand
require("keybinds")

-- Shows each connected monitor's output name on that monitor for a couple
-- seconds, like the "Identify Displays" button on other desktops.
local function identify_monitors()
    for _, mon in ipairs(hl.get_monitors()) do
        hl.exec_cmd(
            "kitty -o font_size=56 --class identify-osd -e ~/.local/bin/identify-osd.sh " .. mon.name,
            { monitor = mon.name, float = true, center = true, pin = true, size = "25% 20%" }
        )
    end
end

hl.bind("SUPER + SHIFT + I", identify_monitors, { desc = "Identify monitors" })

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

hl.window_rule({ name = "float-pavucontrol", match = { class = "^(pavucontrol)$" },       float = true })
hl.window_rule({ name = "float-blueman",     match = { class = "^(blueman-manager)$" },   float = true })
hl.window_rule({ name = "float-nm-editor",   match = { class = "^(nm-connection-editor)$" }, float = true })
hl.window_rule({ name = "float-xarchiver",   match = { class = "^(xarchiver)$" },         float = true })
hl.window_rule({ name = "float-identify-osd", match = { class = "^(identify-osd)$" }, float = true, pin = true, size = "25% 20%" })

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },
    no_focus = true,
})

-- Lid switch is handled by systemd-logind (suspend); see /etc/systemd/logind.conf.d/laptop-lid.conf
