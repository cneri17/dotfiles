-- Pin workspaces to monitors by EDID description, not port name (DP-3/DP-4
-- numbering is reassigned by the driver on every resume/reboot, but the
-- monitor's description never changes).
--
-- Workspaces 1-9 (keys 1-9) -> main ultrawide (Samsung Odyssey G95NC)
-- Workspace 10  (key 0)     -> small side monitor (Cyrix XENEON EDGE)

local MAIN = "desc:Samsung Electric Company Odyssey G95NC"
local SMALL = "desc:Cyrix Corporation XENEON EDGE"

for i = 1, 9 do
    hl.workspace_rule({ workspace = tostring(i), monitor = MAIN, default = (i == 1) })
end

hl.workspace_rule({ workspace = "10", monitor = SMALL, default = true })
