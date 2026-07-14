#!/usr/bin/env python3
"""GUI editor for Hyprland keybinds and appearance settings.

Edits ~/.config/hypr/keybinds.json and appearance.json, regenerates the
corresponding .lua files (required from hyprland.lua) on Save, and offers
a one-click `hyprctl reload`.
"""

import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import hypr_config_lib as lib

BG = "#0d1411"
FG = "#e8e8e8"
ACCENT = "#73ba25"
ACCENT2 = "#2fae87"
FIELD_BG = "#1a201c"
SELECT_BG = "#2fae87"


class BindDialog(simpledialog.Dialog):
    def __init__(self, parent, title, row=None):
        self.row = row or {"combo": "", "dispatcher": "", "opts": "", "desc": ""}
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        master.configure(bg=BG)
        labels = ["Combo (e.g. SUPER + Return)", "Dispatcher (Lua, e.g. hl.dsp.exec_cmd(\"kitty\"))",
                  "Extra opts (optional, e.g. { locked = true })", "Description"]
        keys = ["combo", "dispatcher", "opts", "desc"]
        self.entries = {}
        for i, (label, key) in enumerate(zip(labels, keys)):
            tk.Label(master, text=label, bg=BG, fg=FG, anchor="w").grid(row=i, column=0, sticky="w", pady=(6, 0))
            e = tk.Entry(master, width=55, bg=FIELD_BG, fg=FG, insertbackground=FG, relief="flat")
            e.insert(0, self.row.get(key, ""))
            e.grid(row=i, column=0, sticky="ew", pady=(24, 4))
            self.entries[key] = e
        return self.entries["combo"]

    def buttonbox(self):
        box = tk.Frame(self, bg=BG)
        ok = tk.Button(box, text="Save", width=10, command=self.ok, bg=ACCENT, fg="#0d1411",
                        relief="flat", activebackground=ACCENT2)
        ok.pack(side="left", padx=5, pady=8)
        cancel = tk.Button(box, text="Cancel", width=10, command=self.cancel, bg=FIELD_BG, fg=FG,
                            relief="flat")
        cancel.pack(side="left", padx=5, pady=8)
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        box.pack()

    def apply(self):
        self.result = {k: e.get().strip() for k, e in self.entries.items()}


class KeybindsTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.rows = lib.load_keybinds()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=FIELD_BG, foreground=FG, fieldbackground=FIELD_BG,
                         rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background=BG, foreground=ACCENT, relief="flat")
        style.map("Treeview", background=[("selected", SELECT_BG)], foreground=[("selected", "#0d1411")])

        cols = ("combo", "dispatcher", "opts", "desc")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = {"combo": "Combo", "dispatcher": "Dispatcher", "opts": "Extra opts", "desc": "Description"}
        widths = {"combo": 170, "dispatcher": 320, "opts": 160, "desc": 220}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        for text, cmd in [("Add", self.add_row), ("Edit", self.edit_selected),
                           ("Delete", self.delete_selected), ("Move Up", lambda: self.move(-1)),
                           ("Move Down", lambda: self.move(1))]:
            tk.Button(btns, text=text, command=cmd, bg=FIELD_BG, fg=FG, relief="flat",
                      activebackground=ACCENT, padx=10).pack(side="left", padx=4)

        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(i),
                              values=(row["combo"], row["dispatcher"], row.get("opts", ""), row.get("desc", "")))

    def selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_row(self):
        dlg = BindDialog(self, "Add keybind")
        if dlg.result and dlg.result["combo"] and dlg.result["dispatcher"]:
            self.rows.append(dlg.result)
            self.refresh()

    def edit_selected(self):
        idx = self.selected_index()
        if idx is None:
            return
        dlg = BindDialog(self, "Edit keybind", self.rows[idx])
        if dlg.result and dlg.result["combo"] and dlg.result["dispatcher"]:
            self.rows[idx] = dlg.result
            self.refresh()

    def delete_selected(self):
        idx = self.selected_index()
        if idx is None:
            return
        if messagebox.askyesno("Delete", f"Delete keybind '{self.rows[idx]['combo']}'?"):
            del self.rows[idx]
            self.refresh()

    def move(self, delta):
        idx = self.selected_index()
        if idx is None:
            return
        new = idx + delta
        if 0 <= new < len(self.rows):
            self.rows[idx], self.rows[new] = self.rows[new], self.rows[idx]
            self.refresh()
            self.tree.selection_set(str(new))

    def save(self):
        lib.save_keybinds(self.rows)


class MonitorDialog(simpledialog.Dialog):
    """Add/edit a monitor rule. Position can be typed exactly, left as 'auto',
    or computed from another monitor's resolved mode/position (e.g. 'right of
    eDP-1') - the offset is computed once, at save time, and stored as plain
    'XxY' coordinates. It does not stay a live relationship: if the reference
    monitor's own mode or position changes later, re-open this dialog and
    recompute it.
    """

    POSITION_MODES = ["Exact coordinates", "Auto", "Right of", "Left of", "Above", "Below"]

    def __init__(self, parent, title, row=None, other_rows=None):
        self.row = row or {"output": "", "mode": "preferred", "position": "auto", "scale": "auto"}
        self.other_rows = [r for r in (other_rows or []) if r.get("output")]
        self.result = None
        self._computed_position = None
        super().__init__(parent, title)

    def body(self, master):
        master.configure(bg=BG)

        tk.Label(master, text="Output (e.g. eDP-1, or blank for all)", bg=BG, fg=FG, anchor="w"
                  ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.output_entry = tk.Entry(master, width=45, bg=FIELD_BG, fg=FG, insertbackground=FG, relief="flat")
        self.output_entry.insert(0, str(self.row.get("output", "")))
        self.output_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        tk.Label(master, text="Mode (pick a detected resolution, or type e.g. 1920x1200@60 / 'preferred')",
                 bg=BG, fg=FG, anchor="w").grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._available_modes = lib.get_available_modes()
        self.mode_var = tk.StringVar(value=str(self.row.get("mode", "")))
        self.mode_combo = ttk.Combobox(master, textvariable=self.mode_var, width=42,
                                        values=self._modes_for_output(self.output_entry.get().strip()))
        self.mode_combo.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.output_entry.bind("<KeyRelease>", lambda e: self._refresh_mode_options())

        tk.Label(master, text="Position", bg=BG, fg=FG, anchor="w"
                  ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.pos_mode_var = tk.StringVar(value=self._infer_position_mode())
        pos_combo = ttk.Combobox(master, textvariable=self.pos_mode_var, values=self.POSITION_MODES,
                                  state="readonly", width=16)
        pos_combo.grid(row=5, column=0, sticky="w", pady=(0, 8))
        pos_combo.bind("<<ComboboxSelected>>", lambda e: self._on_position_mode_change())

        other_names = [r["output"] for r in self.other_rows]
        self.relative_var = tk.StringVar(value=other_names[0] if other_names else "")
        self.relative_combo = ttk.Combobox(master, textvariable=self.relative_var, values=other_names,
                                            state="readonly", width=20)

        self.exact_entry = tk.Entry(master, width=20, bg=FIELD_BG, fg=FG, insertbackground=FG, relief="flat")
        if self._infer_position_mode() == "Exact coordinates":
            self.exact_entry.insert(0, str(self.row.get("position", "0x0")))

        self.relative_combo.grid(row=5, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
        self.exact_entry.grid(row=5, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
        self._on_position_mode_change()

        tk.Label(master, text="Scale (e.g. 1.25, or 'auto')", bg=BG, fg=FG, anchor="w"
                  ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.scale_entry = tk.Entry(master, width=45, bg=FIELD_BG, fg=FG, insertbackground=FG, relief="flat")
        self.scale_entry.insert(0, str(self.row.get("scale", "auto")))
        self.scale_entry.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        return self.output_entry

    def _infer_position_mode(self):
        return "Auto" if self.row.get("position", "auto") == "auto" else "Exact coordinates"

    def _modes_for_output(self, output_name):
        detected = self._available_modes.get(output_name, [])
        return ["preferred"] + detected

    def _refresh_mode_options(self):
        self.mode_combo["values"] = self._modes_for_output(self.output_entry.get().strip())

    def _on_position_mode_change(self):
        mode = self.pos_mode_var.get()
        if mode in ("Right of", "Left of", "Above", "Below"):
            self.relative_combo.grid()
            self.exact_entry.grid_remove()
        elif mode == "Exact coordinates":
            self.exact_entry.grid()
            self.relative_combo.grid_remove()
        else:  # Auto
            self.exact_entry.grid_remove()
            self.relative_combo.grid_remove()

    def buttonbox(self):
        box = tk.Frame(self, bg=BG)
        ok = tk.Button(box, text="Save", width=10, command=self.ok, bg=ACCENT, fg="#0d1411",
                        relief="flat", activebackground=ACCENT2)
        ok.pack(side="left", padx=5, pady=8)
        cancel = tk.Button(box, text="Cancel", width=10, command=self.cancel, bg=FIELD_BG, fg=FG,
                            relief="flat")
        cancel.pack(side="left", padx=5, pady=8)
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        box.pack()

    @staticmethod
    def _parse_mode_dims(mode_str):
        m = re.match(r"(\d+)x(\d+)", mode_str.strip())
        if not m:
            raise ValueError(
                f"Can't compute a relative position from mode {mode_str!r} - "
                "both monitors need an exact 'WIDTHxHEIGHT[@rate]' mode (not 'preferred') for this"
            )
        return int(m.group(1)), int(m.group(2))

    @staticmethod
    def _parse_exact_position(pos_str):
        m = re.fullmatch(r"(-?\d+)x(-?\d+)", pos_str.strip())
        if not m:
            raise ValueError(
                f"Reference monitor's position is {pos_str!r}, not exact coordinates - "
                "set its position to exact coordinates first (or use Detect), then position relative to it"
            )
        return int(m.group(1)), int(m.group(2))

    def _compute_position(self):
        mode = self.pos_mode_var.get()
        if mode == "Auto":
            return "auto"
        if mode == "Exact coordinates":
            val = self.exact_entry.get().strip()
            self._parse_exact_position(val)  # validates format
            return val

        ref_name = self.relative_var.get()
        if not ref_name:
            raise ValueError("Pick a monitor to position relative to")
        ref = next((r for r in self.other_rows if r["output"] == ref_name), None)
        if ref is None:
            raise ValueError(f"Unknown reference monitor {ref_name!r}")

        ref_w, ref_h = self._parse_mode_dims(ref.get("mode", ""))
        ref_x, ref_y = self._parse_exact_position(ref.get("position", ""))
        this_w, this_h = self._parse_mode_dims(self.mode_var.get().strip())

        if mode == "Right of":
            return f"{ref_x + ref_w}x{ref_y}"
        if mode == "Left of":
            return f"{ref_x - this_w}x{ref_y}"
        if mode == "Above":
            return f"{ref_x}x{ref_y - this_h}"
        if mode == "Below":
            return f"{ref_x}x{ref_y + ref_h}"
        raise ValueError(f"Unknown position mode {mode!r}")

    def validate(self):
        try:
            self._computed_position = self._compute_position()
        except ValueError as e:
            messagebox.showerror("Invalid position", str(e), parent=self)
            return False
        return True

    def apply(self):
        self.result = {
            "output": self.output_entry.get().strip(),
            "mode": self.mode_var.get().strip(),
            "position": self._computed_position,
            "scale": self.scale_entry.get().strip(),
        }


class MonitorsTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.rows = lib.load_monitors()

        cols = ("output", "mode", "position", "scale")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        headings = {"output": "Output", "mode": "Mode", "position": "Position", "scale": "Scale"}
        widths = {"output": 140, "mode": 220, "position": 140, "scale": 100}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        for text, cmd in [("Add", self.add_row), ("Edit", self.edit_selected),
                           ("Delete", self.delete_selected), ("Move Up", lambda: self.move(-1)),
                           ("Move Down", lambda: self.move(1)),
                           ("Detect connected monitors", self.detect)]:
            tk.Button(btns, text=text, command=cmd, bg=FIELD_BG, fg=FG, relief="flat",
                      activebackground=ACCENT, padx=10).pack(side="left", padx=4)

        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.rows):
            out = row["output"] or "(all)"
            self.tree.insert("", "end", iid=str(i),
                              values=(out, row["mode"], row["position"], row["scale"]))

    def selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_row(self):
        dlg = MonitorDialog(self, "Add monitor", other_rows=self.rows)
        if dlg.result:
            self.rows.append(dlg.result)
            self.refresh()

    def edit_selected(self):
        idx = self.selected_index()
        if idx is None:
            return
        others = [r for i, r in enumerate(self.rows) if i != idx]
        dlg = MonitorDialog(self, "Edit monitor", self.rows[idx], other_rows=others)
        if dlg.result:
            self.rows[idx] = dlg.result
            self.refresh()

    def delete_selected(self):
        idx = self.selected_index()
        if idx is None:
            return
        label = self.rows[idx]["output"] or "(all)"
        if messagebox.askyesno("Delete", f"Delete monitor rule '{label}'?"):
            del self.rows[idx]
            self.refresh()

    def move(self, delta):
        idx = self.selected_index()
        if idx is None:
            return
        new = idx + delta
        if 0 <= new < len(self.rows):
            self.rows[idx], self.rows[new] = self.rows[new], self.rows[idx]
            self.refresh()
            self.tree.selection_set(str(new))

    def detect(self):
        try:
            detected = lib.detect_monitors()
        except Exception as e:
            messagebox.showerror("Detect failed", str(e))
            return
        by_output = {r["output"]: i for i, r in enumerate(self.rows) if r["output"]}
        for d in detected:
            if d["output"] in by_output:
                self.rows[by_output[d["output"]]] = d
            else:
                self.rows.append(d)
        self.refresh()

    def save(self):
        lib.save_monitors(self.rows)


class AppearanceTab(tk.Frame):
    FIELDS = [
        ("gaps_in", "Gaps (inner, px)", int),
        ("gaps_out", "Gaps (outer, px)", int),
        ("border_size", "Border size (px)", int),
        ("rounding", "Corner rounding (px)", int),
        ("active_color_1", "Active border color 1 (hex, e.g. 73ba25ee)", str),
        ("active_color_2", "Active border color 2 (hex)", str),
        ("gradient_angle", "Border gradient angle (deg)", int),
        ("inactive_color", "Inactive border color (hex)", str),
        ("blur_size", "Blur size", int),
        ("blur_passes", "Blur passes", int),
        ("active_opacity", "Active window opacity (0-1)", float),
        ("inactive_opacity", "Inactive window opacity (0-1)", float),
    ]

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.data = lib.load_appearance()
        self.vars = {}

        form = tk.Frame(self, bg=BG)
        form.pack(fill="both", expand=True, padx=20, pady=20)

        for i, (key, label, _type) in enumerate(self.FIELDS):
            tk.Label(form, text=label, bg=BG, fg=FG, anchor="w").grid(row=i, column=0, sticky="w", pady=6)
            var = tk.StringVar(value=str(self.data.get(key, "")))
            e = tk.Entry(form, textvariable=var, width=25, bg=FIELD_BG, fg=FG, insertbackground=FG, relief="flat")
            e.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            self.vars[key] = var

        self.blur_var = tk.BooleanVar(value=self.data.get("blur_enabled", True))
        tk.Checkbutton(form, text="Blur enabled", variable=self.blur_var, bg=BG, fg=FG,
                        selectcolor=FIELD_BG, activebackground=BG, activeforeground=FG
                        ).grid(row=len(self.FIELDS), column=0, sticky="w", pady=6)

        self.shadow_var = tk.BooleanVar(value=self.data.get("shadow_enabled", True))
        tk.Checkbutton(form, text="Shadow enabled", variable=self.shadow_var, bg=BG, fg=FG,
                        selectcolor=FIELD_BG, activebackground=BG, activeforeground=FG
                        ).grid(row=len(self.FIELDS), column=1, sticky="w", pady=6)

    def save(self):
        for key, _label, _type in self.FIELDS:
            raw = self.vars[key].get().strip()
            try:
                self.data[key] = _type(raw)
            except ValueError:
                raise ValueError(f"'{raw}' is not a valid value for {key}")
        self.data["blur_enabled"] = self.blur_var.get()
        self.data["shadow_enabled"] = self.shadow_var.get()
        lib.save_appearance(self.data)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hyprland Config Editor")
        self.geometry("920x600")
        self.configure(bg=BG)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=FIELD_BG, foreground=FG, padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#0d1411")])

        nb = ttk.Notebook(self)
        self.keybinds_tab = KeybindsTab(nb)
        self.appearance_tab = AppearanceTab(nb)
        self.monitors_tab = MonitorsTab(nb)
        nb.add(self.keybinds_tab, text="Keybinds")
        nb.add(self.appearance_tab, text="Appearance")
        nb.add(self.monitors_tab, text="Monitors")
        nb.pack(fill="both", expand=True)

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=10, pady=10)
        self.status = tk.Label(footer, text="", bg=BG, fg=ACCENT2, anchor="w")
        self.status.pack(side="left")
        tk.Button(footer, text="Save && Reload Hyprland", command=self.save_and_reload,
                  bg=ACCENT, fg="#0d1411", relief="flat", padx=14, pady=6,
                  activebackground=ACCENT2).pack(side="right")

    def save_and_reload(self):
        try:
            self.keybinds_tab.save()
            self.appearance_tab.save()
            self.monitors_tab.save()
            lib.generate_all()
        except Exception as e:
            messagebox.showerror("Error saving config", str(e))
            return

        result = lib.reload_hyprland()
        if result.returncode == 0:
            self.status.config(text="Saved and reloaded successfully.", fg=ACCENT)
        else:
            self.status.config(text="Saved, but hyprctl reload reported an error - see dialog.", fg="#e05050")
            messagebox.showerror("hyprctl reload error", result.stderr or result.stdout)


if __name__ == "__main__":
    App().mainloop()
