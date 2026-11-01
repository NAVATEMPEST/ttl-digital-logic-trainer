"""
DIGITAL LOGIC TRAINER SIMULATOR
Single-file Python/Tkinter application with real-time TTL logic evaluation,
smooth 60 FPS animations, live signal propagation pulses, and interactive hover HUD.

ICs supported:
    7404  - Hex inverter
    7408  - Quad 2-input AND
    7432  - Quad 2-input OR
    7486  - Quad 2-input XOR
    74151 - 8-to-1 multiplexer

Controls:
    Click an IC in the palette, then click the central board to place it.
    Click a switch (S1-S16) to toggle its value between 0 and 1.
    Click one jack/pin, then another jack/pin, to create a patch wire (Esc or click same jack to cancel).
    Click the PULSE button to fire a momentary logic pulse on the PULSE jack.
    Drag an IC body to move it across the breadboard.
    Right-click (or Ctrl+Click) a wire to remove it.
    Right-click (or Ctrl+Click) an IC body to remove the IC and its wires.
    AUTO-POWER toggle switches between convenient Auto-Power and Strict (+5V/GND required) mode.
    CLEAR WIRES removes all wires.
    RESET BOARD removes ICs and wires and resets switches.
    CHECK / STATUS reports wiring, power, and output states.

Power connections:
    7404, 7408, 7432, 7486:
        Pin 14 = +5 V
        Pin 7  = GND

    74151:
        Pin 16 = +5 V
        Pin 8  = GND
"""

import tkinter as tk
from tkinter import messagebox
import math
import time


# ============================================================
# APPEARANCE & THEME PALETTE
# ============================================================

W, H = 1450, 900

BG = "#111c18"
BOARD = "#16382e"
BOARD_INNER = "#194236"
BOARD_EDGE = "#c29963"
PANEL = "#1b2625"
PANEL_BORDER = "#2f443e"

TEXT = "#eef5f0"
MUTED = "#9eb5ab"
GOLD = "#e2bc74"

RED = "#ef5b5b"
GREEN = "#42e695"
BLUE = "#5eb8ff"
AMBER = "#ffca4b"
CYAN = "#4deeea"

WIRE_COLORS = [
    "#ef5350",  # Red
    "#26c6da",  # Cyan
    "#ffca28",  # Yellow
    "#42a5f5",  # Blue
    "#ffa726",  # Orange
    "#ec407a",  # Pink
    "#ab47bc",  # Purple
    "#66bb6a",  # Green
]


# ============================================================
# COLOR UTILITIES FOR SMOOTH ANIMATIONS
# ============================================================

def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = [max(0, min(255, int(round(c)))) for c in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((
        r1 + (r2 - r1) * t,
        g1 + (g2 - g1) * t,
        b1 + (b2 - b1) * t,
    ))


# ============================================================
# IC SPECIFICATIONS & PIN DESCRIPTIONS
# ============================================================

IC_SPECS = {
    "7404": {
        "pins": 14,
        "label": "HEX INVERTER",
        "vcc": 14,
        "gnd": 7,
        "pin_names": {
            1: "1A (In 1)", 2: "1Y (Out ¬1A)",
            3: "2A (In 2)", 4: "2Y (Out ¬2A)",
            5: "3A (In 3)", 6: "3Y (Out ¬3A)",
            7: "GND (0V)",
            8: "4Y (Out ¬4A)", 9: "4A (In 4)",
            10: "5Y (Out ¬5A)", 11: "5A (In 5)",
            12: "6Y (Out ¬6A)", 13: "6A (In 6)",
            14: "VCC (+5V)",
        },
    },
    "7408": {
        "pins": 14,
        "label": "QUAD AND",
        "vcc": 14,
        "gnd": 7,
        "pin_names": {
            1: "1A (Gate 1 In A)", 2: "1B (Gate 1 In B)", 3: "1Y (Out 1A·1B)",
            4: "2A (Gate 2 In A)", 5: "2B (Gate 2 In B)", 6: "2Y (Out 2A·2B)",
            7: "GND (0V)",
            8: "3Y (Out 3A·3B)", 9: "3A (Gate 3 In A)", 10: "3B (Gate 3 In B)",
            11: "4Y (Out 4A·4B)", 12: "4A (Gate 4 In A)", 13: "4B (Gate 4 In B)",
            14: "VCC (+5V)",
        },
    },
    "7432": {
        "pins": 14,
        "label": "QUAD OR",
        "vcc": 14,
        "gnd": 7,
        "pin_names": {
            1: "1A (Gate 1 In A)", 2: "1B (Gate 1 In B)", 3: "1Y (Out 1A+1B)",
            4: "2A (Gate 2 In A)", 5: "2B (Gate 2 In B)", 6: "2Y (Out 2A+2B)",
            7: "GND (0V)",
            8: "3Y (Out 3A+3B)", 9: "3A (Gate 3 In A)", 10: "3B (Gate 3 In B)",
            11: "4Y (Out 4A+4B)", 12: "4A (Gate 4 In A)", 13: "4B (Gate 4 In B)",
            14: "VCC (+5V)",
        },
    },
    "7486": {
        "pins": 14,
        "label": "QUAD XOR",
        "vcc": 14,
        "gnd": 7,
        "pin_names": {
            1: "1A (Gate 1 In A)", 2: "1B (Gate 1 In B)", 3: "1Y (Out 1A⊕1B)",
            4: "2A (Gate 2 In A)", 5: "2B (Gate 2 In B)", 6: "2Y (Out 2A⊕2B)",
            7: "GND (0V)",
            8: "3Y (Out 3A⊕3B)", 9: "3A (Gate 3 In A)", 10: "3B (Gate 3 In B)",
            11: "4Y (Out 4A⊕4B)", 12: "4A (Gate 4 In A)", 13: "4B (Gate 4 In B)",
            14: "VCC (+5V)",
        },
    },
    "74151": {
        "pins": 16,
        "label": "8:1 MULTIPLEXER",
        "vcc": 16,
        "gnd": 8,
        "pin_names": {
            1: "D3 (Data In 3)", 2: "D2 (Data In 2)",
            3: "D1 (Data In 1)", 4: "D0 (Data In 0)",
            5: "Y (MUX Out)", 6: "W (Inverted ¬Y)",
            7: "/G (Strobe/Enable, Active LOW)",
            8: "GND (0V)",
            9: "A (Select S0 - LSB)", 10: "B (Select S1)", 11: "C (Select S2 - MSB)",
            12: "D7 (Data In 7)", 13: "D6 (Data In 6)",
            14: "D5 (Data In 5)", 15: "D4 (Data In 4)",
            16: "VCC (+5V)",
        },
    },
}

# 7-Segment Hexadecimal font table (segments a, b, c, d, e, f, g)
HEX_7SEG = {
    0x0: (1, 1, 1, 1, 1, 1, 0),
    0x1: (0, 1, 1, 0, 0, 0, 0),
    0x2: (1, 1, 0, 1, 1, 0, 1),
    0x3: (1, 1, 1, 1, 0, 0, 1),
    0x4: (0, 1, 1, 0, 0, 1, 1),
    0x5: (1, 0, 1, 1, 0, 1, 1),
    0x6: (1, 0, 1, 1, 1, 1, 1),
    0x7: (1, 1, 1, 0, 0, 0, 0),
    0x8: (1, 1, 1, 1, 1, 1, 1),
    0x9: (1, 1, 1, 1, 0, 1, 1),
    0xA: (1, 1, 1, 0, 1, 1, 1),
    0xB: (0, 0, 1, 1, 1, 1, 1),
    0xC: (1, 0, 0, 1, 1, 1, 0),
    0xD: (0, 1, 1, 1, 1, 0, 1),
    0xE: (1, 0, 0, 1, 1, 1, 1),
    0xF: (1, 0, 0, 0, 1, 1, 1),
}


# ============================================================
# ANIMATED TOOLBAR BUTTON
# ============================================================

class HoverButton(tk.Button):
    """Tkinter Button with smooth color interpolation on mouse hover."""

    def __init__(self, master, base_bg, hover_bg, active_bg=None, **kwargs):
        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg or hover_bg
        self.is_selected = False
        self._hover_t = 0.0
        self._hover_target = 0.0
        self._anim_job = None

        super().__init__(
            master,
            bg=base_bg,
            activebackground=self.active_bg,
            cursor="hand2",
            **kwargs
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set_selected(self, selected):
        self.is_selected = selected
        self._update_color()

    def _on_enter(self, _event=None):
        self._hover_target = 1.0
        self._schedule_step()

    def _on_leave(self, _event=None):
        self._hover_target = 0.0
        self._schedule_step()

    def _schedule_step(self):
        if self._anim_job is None:
            self._anim_job = self.after(16, self._step)

    def _step(self):
        self._anim_job = None
        diff = self._hover_target - self._hover_t
        if abs(diff) < 0.04:
            self._hover_t = self._hover_target
        else:
            self._hover_t += diff * 0.35
            self._schedule_step()
        self._update_color()

    def _update_color(self):
        if self.is_selected:
            color = lerp_color(self.active_bg, "#589982", self._hover_t * 0.4)
        else:
            color = lerp_color(self.base_bg, self.hover_bg, self._hover_t)
        try:
            self.configure(bg=color)
        except tk.TclError:
            pass


# ============================================================
# DIGITAL TRAINER APPLICATION
# ============================================================

class DigitalTrainer:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "Digital Logic Trainer — Interactive IC & Patch-Wire Simulator"
        )
        self.root.configure(bg=BG)
        self.root.geometry("1450x900")
        self.root.minsize(1120, 720)

        self.selected_ic_type = None
        self.ics = []
        self.wires = []

        self.input_values = {i: 0 for i in range(1, 17)}
        self.next_ic_id = 1
        self.wire_start = None

        self.drag_ic = None
        self.drag_offset = (0, 0)
        self.wire_color_index = 0

        # Auto-power allows gates to evaluate immediately even before VCC/GND
        # wires are added, while still honoring explicit VCC/GND connections
        # and reporting power wiring status. Can be toggled to STRICT mode.
        self.auto_power = True

        # Interactive hover & cursor state
        self.mouse_x = 0
        self.mouse_y = 0
        self.hover_node = None
        self.hover_switch = None
        self.hover_wire = None
        self.hover_ic = None
        self.hover_pulser = False

        # Smooth animation state dictionaries
        self.switch_anim = {i: 0.0 for i in range(1, 17)}
        self.switch_hover_anim = {i: 0.0 for i in range(1, 17)}
        self.led_anim = {i: 0.0 for i in range(1, 17)}
        self.node_hover_anim = {}
        self.ic_scale_anim = {}
        self.ic_hover_anim = {}
        self.wire_hover_anim = {}

        # Clock & Pulser state
        self.start_time = time.perf_counter()
        self.clock_states = {n: 0 for n in range(6)}
        self.pulse_state = 0
        self.pulse_until = 0.0
        self.pulse_Phase = 0.0
        self.signal_phase = 0.0

        # Cached circuit evaluation results
        self.eval_cache = ({}, {}, {}, {}, [])

        self.status_text = tk.StringVar(
            value=(
                "Choose an IC from the palette, place it on the board, "
                "and wire the pins to switches and LEDs."
            )
        )
        self.detail_text = tk.StringVar(
            value=(
                "Hover over any IC pin or jack to inspect its function and live logic state. "
                "14-pin ICs: Pin 14=+5V, Pin 7=GND • 74151: Pin 16=+5V, Pin 8=GND."
            )
        )

        self.palette_buttons = {}
        self._build_ui()

        # Compute initial layout & draw
        self.draw()

        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<Escape>", self._on_escape)

        # Start 60 FPS animation loop
        self._tick_animations()

    # ========================================================
    # WINDOW RESIZING & ESCAPE
    # ========================================================

    def _on_resize(self, event=None):
        if event is not None:
            if event.widget not in (self.root, self.canvas):
                return
        if hasattr(self, "canvas"):
            try:
                if self.canvas.winfo_exists():
                    self.draw()
            except tk.TclError:
                pass

    def _on_escape(self, _event=None):
        if self.wire_start is not None:
            self.wire_start = None
            self.status_text.set("Wire connection cancelled.")
            self.draw()
        elif self.selected_ic_type is not None:
            self.selected_ic_type = None
            for btn in self.palette_buttons.values():
                btn.set_selected(False)
            self.status_text.set("IC placement cancelled.")
            self.draw()

    # ========================================================
    # USER INTERFACE
    # ========================================================

    def _build_ui(self):
        top = tk.Frame(self.root, bg=PANEL, height=86)
        top.pack(side="top", fill="x")

        title_frame = tk.Frame(top, bg=PANEL)
        title_frame.pack(side="left", padx=(16, 16), pady=8)

        tk.Label(
            title_frame,
            text="DIGITAL LOGIC TRAINER",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="Interactive TTL IC & Patch-Cord Simulator",
            bg=PANEL,
            fg=GOLD,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        tk.Label(
            top,
            text="IC PALETTE:",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 6))

        for typ, spec in IC_SPECS.items():
            button = HoverButton(
                top,
                text=f"{typ}\n{spec['label']}",
                command=lambda t=typ: self.choose_ic(t),
                base_bg="#2b3f39",
                hover_bg="#3e5e54",
                active_bg="#2b7a5e",
                fg=TEXT,
                activeforeground="white",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground="#48685e",
                font=("Segoe UI", 9, "bold"),
                width=13,
                height=2
            )
            button.pack(side="left", padx=3, pady=8)
            self.palette_buttons[typ] = button

        HoverButton(
            top,
            text="CHECK / STATUS",
            command=self.show_status,
            base_bg="#246950",
            hover_bg="#318a6a",
            fg="white",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=11,
            pady=6
        ).pack(side="right", padx=(4, 12), pady=10)

        HoverButton(
            top,
            text="CLEAR WIRES",
            command=self.clear_wires,
            base_bg="#784737",
            hover_bg="#965a46",
            fg="white",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=11,
            pady=6
        ).pack(side="right", padx=4, pady=10)

        HoverButton(
            top,
            text="RESET BOARD",
            command=self.reset_board,
            base_bg="#633b46",
            hover_bg="#824d5c",
            fg="white",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=11,
            pady=6
        ).pack(side="right", padx=4, pady=10)

        self.power_mode_btn = HoverButton(
            top,
            text="PWR: AUTO (+5V)",
            command=self.toggle_power_mode,
            base_bg="#2f5266",
            hover_bg="#3e6c87",
            fg="white",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6
        )
        self.power_mode_btn.pack(side="right", padx=4, pady=10)

        self.canvas = tk.Canvas(
            self.root,
            bg=BG,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Control-Button-1>", self.on_ctrl_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave_canvas)

        bottom = tk.Frame(self.root, bg=PANEL)
        bottom.pack(side="bottom", fill="x")

        tk.Label(
            bottom,
            textvariable=self.status_text,
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(7, 2))

        tk.Label(
            bottom,
            textvariable=self.detail_text,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=1400,
            justify="left"
        ).pack(fill="x", padx=14, pady=(0, 7))

    # ========================================================
    # MODE & IC SELECTION
    # ========================================================

    def toggle_power_mode(self):
        self.auto_power = not self.auto_power
        if self.auto_power:
            self.power_mode_btn.configure(text="PWR: AUTO (+5V)")
            self.power_mode_btn.base_bg = "#2f5266"
            self.power_mode_btn.hover_bg = "#3e6c87"
            self.status_text.set(
                "Power Mode: AUTO — ICs operate automatically unless VCC/GND are miswired."
            )
        else:
            self.power_mode_btn.configure(text="PWR: STRICT (WIRE)")
            self.power_mode_btn.base_bg = "#6b4c25"
            self.power_mode_btn.hover_bg = "#8c6532"
            self.status_text.set(
                "Power Mode: STRICT — Every IC requires physical +5V (VCC) and GND wires to operate."
            )
        self.power_mode_btn._update_color()
        self.draw()

    def choose_ic(self, typ):
        if self.selected_ic_type == typ:
            self.selected_ic_type = None
            for btn in self.palette_buttons.values():
                btn.set_selected(False)
            self.status_text.set("IC selection cleared.")
            self.draw()
            return

        self.selected_ic_type = typ
        for k, btn in self.palette_buttons.items():
            btn.set_selected(k == typ)

        spec = IC_SPECS[typ]
        self.status_text.set(
            f"{typ} ({spec['label']}) selected — click inside the central breadboard area to place it."
        )
        self.detail_text.set(
            f"{spec['pins']}-pin DIP package • Power: Pin {spec['vcc']} = +5V, Pin {spec['gnd']} = GND • "
            "Move cursor over the board to preview placement."
        )
        self.draw()

    # ========================================================
    # LAYOUT & NODE COORDINATE COMPUTATION (RUNS BEFORE EVAL)
    # ========================================================

    def _layout(self):
        cw = max(self.canvas.winfo_width(), 1120)
        ch = max(self.canvas.winfo_height(), 620)
        return cw, ch

    def _compute_geometry(self):
        """
        Computes all board coordinates and registers every jack and IC pin
        BEFORE circuit evaluation runs. This guarantees that _all_nodes()
        and _evaluate() always see every input, output, power, clock, display,
        and IC pin node on the very first pass.
        """
        cw, ch = self._layout()
        margin = 18

        bx1 = margin
        by1 = 14
        bx2 = cw - margin
        by2 = ch - 12

        left_x1 = bx1 + 18
        left_x2 = bx1 + 334

        right_x1 = bx2 - 334
        right_x2 = bx2 - 18

        section_y1 = by1 + 45
        section_y2 = by1 + ch * 0.41

        self.board_bounds = (bx1, by1, bx2, by2)
        self.panel_bounds = (left_x1, left_x2, right_x1, right_x2, section_y1, section_y2)

        # 1. Input Switches & Jacks (I1 - I16)
        self.input_jacks = {}
        self.switch_boxes = {}
        ix0 = left_x1 + 74
        iy0 = section_y1 + 46

        for i in range(1, 17):
            col = 0 if i <= 8 else 1
            row = (i - 1) % 8
            x = ix0 + col * 145
            y = iy0 + row * 26
            jx = x + 44
            jy = y
            self.input_jacks[f"I{i}"] = (jx, jy)
            self.switch_boxes[i] = (x - 48, y - 11, x + 26, y + 11, x, y)

        # 2. Output LEDs & Jacks (O1 - O16)
        self.output_jacks = {}
        self.led_positions = {}
        ox0 = right_x1 + 70
        oy0 = section_y1 + 46

        for i in range(1, 17):
            col = 0 if i <= 8 else 1
            row = (i - 1) % 8
            x = ox0 + col * 145
            y = oy0 + row * 26
            jx = x + 45
            jy = y
            self.output_jacks[f"O{i}"] = (jx, jy)
            self.led_positions[i] = (x, y)

        # 3. Clock Jacks (C0 - C5)
        cy = section_y2 + 48
        self.clock_jacks = {}
        self.clock_freqs = [
            ("0.1Hz", 0.1),
            ("1Hz", 1.0),
            ("10Hz", 2.5),
            ("100Hz", 5.0),
            ("200Hz", 8.0),
            ("500Hz", 12.0),
        ]
        for n, (hz, _f) in enumerate(self.clock_freqs):
            x = left_x1 + 70 + (n % 2) * 140
            y = cy + 28 + (n // 2) * 44
            self.clock_jacks[f"C{n}"] = (x + 25, y)

        # 4. Logic Pulser Jack & Button
        py = by2 - 66
        self.pulser_pos = (left_x1 + 185, py)
        self.pulser_btn_box = (left_x1 + 108, py - 12, left_x1 + 162, py + 12)
        self.pulser_jacks = {"PULSE": self.pulser_pos}

        # 5. 7-Segment Displays & BCD Input Jacks (DA0-DA3, DB0-DB3)
        dx = right_x1 + 65
        dy = section_y2 + 66
        self.seg_displays = {
            "A": (dx, dy, "DISPLAY A"),
            "B": (dx + 150, dy, "DISPLAY B"),
        }
        self.seg_jacks = {}
        bit_labels = ["D3(8)", "D2(4)", "D1(2)", "D0(1)"]
        for disp_key, (sx, sy, _title) in self.seg_displays.items():
            for bit_idx in range(4):
                bit_num = 3 - bit_idx  # D3, D2, D1, D0
                jx = sx - 9 + bit_idx * 26
                jy = sy + 122
                self.seg_jacks[f"D{disp_key}{bit_num}"] = (jx, jy, bit_labels[bit_idx])

        # 6. Power Jacks (VCC, GND)
        power_y = by2 - 58
        self.power_jacks = {
            "VCC": (right_x1 + 100, power_y),
            "GND": (right_x1 + 210, power_y),
        }

        # 7. IC Area & IC Pin Positions
        self.ic_area = (
            left_x2 + 24,
            section_y1 + 34,
            right_x1 - 24,
            by2 - 42
        )

        for ic in self.ics:
            self._compute_ic_geometry(ic)

    def _compute_ic_geometry(self, ic):
        x = ic["x"]
        y = ic["y"]
        pins = ic["pins"]
        half = pins // 2
        spacing = 18

        body_h = (half - 1) * spacing + 28
        body_w = 92 if pins <= 16 else 108

        x1 = x - body_w / 2
        y1 = y - body_h / 2
        x2 = x + body_w / 2
        y2 = y + body_h / 2

        ic["pin_positions"] = {}
        for p in range(1, pins + 1):
            if p <= half:
                px = x1 - 11
                py = y1 + 14 + (p - 1) * spacing
            else:
                rp = pins - p + 1
                px = x2 + 11
                py = y1 + 14 + (rp - 1) * spacing
            ic["pin_positions"][p] = (px, py)

        ic["body_rect"] = (x1, y1, x2, y2)
        ic["bbox"] = (x1 - 18, y1 - 12, x2 + 18, y2 + 22)

    # ========================================================
    # SMOOTH 60 FPS ANIMATION ENGINE
    # ========================================================

    def _tick_animations(self):
        now = time.perf_counter()
        elapsed = now - self.start_time
        need_redraw = False

        # 1. Update real-time clock generators & pulser
        for n, (_label, freq) in enumerate(getattr(self, "clock_freqs", [])):
            new_clk = 1 if math.sin(2.0 * math.pi * freq * elapsed) >= 0 else 0
            if self.clock_states.get(n) != new_clk:
                self.clock_states[n] = new_clk
                # Redraw if any wire is hooked up to this clock or if visible
                need_redraw = True

        if self.pulse_state == 1 and now >= self.pulse_until:
            self.pulse_state = 0
            need_redraw = True

        # Advance wire signal flow animation when any wire exists
        if self.wires or self.wire_start is not None:
            self.signal_phase = (self.signal_phase + 0.045) % 1.0
            need_redraw = True

        # 2. Smooth switch toggle & switch hover animations
        for i in range(1, 17):
            target_s = float(self.input_values[i])
            cur_s = self.switch_anim[i]
            if abs(target_s - cur_s) > 0.005:
                self.switch_anim[i] = cur_s + (target_s - cur_s) * 0.28
                need_redraw = True
            else:
                self.switch_anim[i] = target_s

            target_h = 1.0 if self.hover_switch == i else 0.0
            cur_h = self.switch_hover_anim[i]
            if abs(target_h - cur_h) > 0.01:
                self.switch_hover_anim[i] = cur_h + (target_h - cur_h) * 0.3
                need_redraw = True
            else:
                self.switch_hover_anim[i] = target_h

        # 3. Evaluate circuit to get target LED states
        self._compute_geometry()
        self.eval_cache = self._evaluate()
        _groups, roots, _drivers, net_states, _errors = self.eval_cache

        for i in range(1, 17):
            root = roots.get(f"O{i}")
            state = net_states.get(root) if root is not None else None
            target_led = 1.0 if state == 1 else (0.5 if state == "X" else 0.0)
            cur_led = self.led_anim[i]
            if abs(target_led - cur_led) > 0.01:
                self.led_anim[i] = cur_led + (target_led - cur_led) * 0.25
                need_redraw = True
            else:
                self.led_anim[i] = target_led

        # 4. Smooth node hover animations
        all_nodes = self._all_nodes()
        for node in list(all_nodes.keys()):
            target_nh = 1.0 if (node == self.hover_node or node == self.wire_start) else 0.0
            cur_nh = self.node_hover_anim.get(node, 0.0)
            if abs(target_nh - cur_nh) > 0.01:
                self.node_hover_anim[node] = cur_nh + (target_nh - cur_nh) * 0.32
                need_redraw = True
            else:
                self.node_hover_anim[node] = target_nh

        # 5. Smooth IC pop-in scale & hover animations
        for ic in self.ics:
            ic_id = ic["id"]
            cur_sc = self.ic_scale_anim.get(ic_id, 1.0)
            if abs(1.0 - cur_sc) > 0.008:
                self.ic_scale_anim[ic_id] = cur_sc + (1.0 - cur_sc) * 0.28
                need_redraw = True
            else:
                self.ic_scale_anim[ic_id] = 1.0

            target_ih = 1.0 if (self.hover_ic and self.hover_ic["id"] == ic_id) else 0.0
            cur_ih = self.ic_hover_anim.get(ic_id, 0.0)
            if abs(target_ih - cur_ih) > 0.01:
                self.ic_hover_anim[ic_id] = cur_ih + (target_ih - cur_ih) * 0.3
                need_redraw = True
            else:
                self.ic_hover_anim[ic_id] = target_ih

        # 6. Smooth wire settle & hover animations
        for idx, wire in enumerate(self.wires):
            settle = wire.get("settle", 1.0)
            if abs(1.0 - settle) > 0.01:
                wire["settle"] = settle + (1.0 - settle) * 0.22
                need_redraw = True
            else:
                wire["settle"] = 1.0

            target_wh = 1.0 if self.hover_wire == idx else 0.0
            cur_wh = self.wire_hover_anim.get(idx, 0.0)
            if abs(target_wh - cur_wh) > 0.01:
                self.wire_hover_anim[idx] = cur_wh + (target_wh - cur_wh) * 0.32
                need_redraw = True
            else:
                self.wire_hover_anim[idx] = target_wh

        if need_redraw:
            self.draw(recompute=False)

        self.root.after(16, self._tick_animations)

    # ========================================================
    # DRAW THE BOARD
    # ========================================================

    def draw(self, recompute=True):
        c = self.canvas
        c.delete("all")

        if recompute:
            self._compute_geometry()
            self.eval_cache = self._evaluate()

        groups, roots, drivers, net_states, errors = self.eval_cache
        bx1, by1, bx2, by2 = self.board_bounds
        left_x1, left_x2, right_x1, right_x2, section_y1, section_y2 = self.panel_bounds

        # Outer Board Shadow & Chassis
        c.create_rectangle(
            bx1 + 6, by1 + 8, bx2 + 6, by2 + 8,
            fill="#070c0a", outline=""
        )
        c.create_rectangle(
            bx1, by1, bx2, by2,
            fill=BOARD, outline=BOARD_EDGE, width=4
        )
        c.create_rectangle(
            bx1 + 4, by1 + 4, bx2 - 4, by2 - 4,
            fill="", outline="#355e50", width=1
        )

        # Header Banner on Board
        c.create_text(
            bx1 + 18,
            by1 + 15,
            text="TTL DIGITAL LOGIC TRAINER  •  +5V REGULATED SUPPLY  •  LIVE SIGNAL PROBE",
            anchor="nw",
            fill="#dfd2b2",
            font=("Segoe UI", 10, "bold")
        )

        mode_badge_color = GREEN if self.auto_power else AMBER
        mode_badge_text = (
            "● AUTO-POWER ACTIVE (Gates ready)"
            if self.auto_power
            else "● STRICT POWER MODE (Wire VCC & GND)"
        )
        c.create_text(
            bx2 - 18,
            by1 + 15,
            text=mode_badge_text,
            anchor="ne",
            fill=mode_badge_color,
            font=("Segoe UI", 9, "bold")
        )

        # Sections
        self._section(
            left_x1, section_y1, left_x2, section_y2,
            "INPUT SWITCHES  S1–S16"
        )
        self._section(
            right_x1, section_y1, right_x2, section_y2,
            "OUTPUT LED INDICATORS  L1–L16"
        )
        self._section(
            left_x1, section_y2 + 12, left_x2, by2 - 18,
            "CLOCK GENERATOR / LOGIC PULSER & PROBE"
        )
        self._section(
            right_x1, section_y2 + 12, right_x2, by2 - 18,
            "HEX 7-SEGMENT DISPLAYS / +5V POWER"
        )
        self._section(
            left_x2 + 14, section_y1, right_x1 - 14, by2 - 18,
            "BREADBOARD IC SOCKETS  •  DRAG ICs  •  CLICK PINS TO WIRE"
        )

        # ----------------------------------------------------
        # 1. INPUT SWITCHES (Animated Sliders & Hover Glow)
        # ----------------------------------------------------
        for i in range(1, 17):
            _bx1, _by1, _bx2, _by2, x, y = self.switch_boxes[i]
            val = self.input_values[i]
            anim_t = self.switch_anim[i]
            hov_t = self.switch_hover_anim[i]

            label_col = lerp_color(TEXT, GOLD, hov_t)
            c.create_text(
                x - 43, y,
                text=f"S{i}",
                fill=label_col,
                font=("Segoe UI", 9, "bold")
            )

            # Switch track with hover border highlight
            track_bg = lerp_color("#0e1714", "#162922", anim_t)
            track_border = lerp_color("#7a9689", GOLD, hov_t)
            if hov_t > 0.05:
                c.create_rectangle(
                    x - 27, y - 11, x + 7, y + 11,
                    fill="", outline=lerp_color("#1b4438", "#50806c", hov_t), width=2
                )

            c.create_rectangle(
                x - 25, y - 9, x + 5, y + 9,
                fill=track_bg, outline=track_border, width=1
            )

            # Smoothly interpolated slider knob position & color
            knob_x1 = (x - 22) + anim_t * 14.0
            knob_x2 = knob_x1 + 11.0
            knob_color = lerp_color("#687870", GREEN, anim_t)
            c.create_rectangle(
                knob_x1, y - 6, knob_x2, y + 6,
                fill=knob_color, outline="#e8f5ee" if hov_t > 0.3 else ""
            )

            # Bit readout
            c.create_text(
                x + 16, y,
                text=str(val),
                fill=lerp_color(MUTED, GREEN, anim_t),
                font=("Consolas", 9, "bold")
            )

            jx, jy = self.input_jacks[f"I{i}"]
            self._jack(
                jx, jy, f"I/P{i}",
                color=lerp_color("#cfdcd4", GREEN, anim_t),
                node_id=f"I{i}"
            )

        # ----------------------------------------------------
        # 2. OUTPUT LEDS (Smooth Glow Halo & Accurate Logic State)
        # ----------------------------------------------------
        for i in range(1, 17):
            x, y = self.led_positions[i]
            root = roots.get(f"O{i}")
            state = net_states.get(root) if root is not None else None
            led_b = self.led_anim[i]

            c.create_text(
                x - 44, y,
                text=f"L{i}",
                fill=TEXT,
                font=("Segoe UI", 9, "bold")
            )

            # Outer LED bloom rings when active
            cx_led, cy_led = x - 16, y
            if state == "X":
                c.create_oval(
                    cx_led - 13, cy_led - 13, cx_led + 13, cy_led + 13,
                    fill="#4d1f24", outline=RED, width=1
                )
            elif led_b > 0.05:
                halo_r = 9 + led_b * 5.0
                halo_col = lerp_color("#1b4438", "#6e5c24", led_b)
                c.create_oval(
                    cx_led - halo_r, cy_led - halo_r,
                    cx_led + halo_r, cy_led + halo_r,
                    fill=halo_col, outline=""
                )

            if state == "X":
                led_fill = RED
                led_outline = "#ffb3b3"
            else:
                led_fill = lerp_color("#34453c", "#ffdb4d", led_b)
                led_outline = lerp_color("#70857a", "#fff3b0", led_b)

            c.create_oval(
                cx_led - 8, cy_led - 8, cx_led + 8, cy_led + 8,
                fill=led_fill, outline=led_outline, width=1.5
            )
            # Specular highlight dot on LED lens
            if led_b > 0.2:
                c.create_oval(
                    cx_led - 4, cy_led - 5, cx_led - 1, cy_led - 2,
                    fill="#ffffff", outline=""
                )

            display_state = (
                "1" if state == 1
                else "0" if state == 0
                else "X" if state == "X"
                else "Z"
            )
            state_color = (
                GREEN if state == 1
                else "#8fd4b0" if state == 0
                else RED if state == "X"
                else MUTED
            )

            c.create_text(
                x + 3, y,
                text=display_state,
                fill=state_color,
                font=("Consolas", 9, "bold")
            )

            jx, jy = self.output_jacks[f"O{i}"]
            self._jack(
                jx, jy, f"O/P{i}",
                color=lerp_color("#d9cba0", "#ffe066", led_b),
                node_id=f"O{i}"
            )

        # ----------------------------------------------------
        # 3. CLOCK GENERATORS & LOGIC PULSER / PROBE
        # ----------------------------------------------------
        cy = section_y2 + 48
        c.create_text(
            left_x1 + 16, cy,
            text="CLOCK OUT (LIVE OSCILLATORS)",
            fill=GOLD, anchor="w",
            font=("Segoe UI", 9, "bold")
        )

        for n, (hz, _freq) in enumerate(self.clock_freqs):
            jx, jy = self.clock_jacks[f"C{n}"]
            clk_val = self.clock_states.get(n, 0)
            c.create_text(
                jx - 56, jy,
                text=hz,
                fill=TEXT,
                font=("Segoe UI", 8, "bold")
            )
            # Mini oscillating LED next to clock label
            c.create_oval(
                jx - 25, jy - 4, jx - 17, jy + 4,
                fill=BLUE if clk_val else "#263834",
                outline="#8acbff" if clk_val else "#526b63"
            )
            self._jack(
                jx, jy, "",
                color=BLUE if clk_val else "#9bc4e2",
                node_id=f"C{n}"
            )

        # Logic Pulser button & jack
        px, py = self.pulser_pos
        c.create_text(
            left_x1 + 16, py,
            text="PULSER",
            fill=GOLD, anchor="w",
            font=("Segoe UI", 9, "bold")
        )

        pbx1, pby1, pbx2, pby2 = self.pulser_btn_box
        btn_fill = (
            RED if self.pulse_state == 1
            else "#9e3b3b" if self.hover_pulser
            else "#6e2b2b"
        )
        c.create_rectangle(
            pbx1, pby1, pbx2, pby2,
            fill=btn_fill, outline="#f29b9b", width=1
        )
        c.create_text(
            (pbx1 + pbx2) / 2, (pby1 + pby2) / 2,
            text="PULSE",
            fill="white",
            font=("Segoe UI", 8, "bold")
        )

        self._jack(
            px, py, "OUT",
            color=RED if self.pulse_state else "#e09090",
            node_id="PULSE"
        )

        # Live Logic Probe Box at bottom-left
        probe_y = by2 - 34
        probe_info = self._get_probe_summary(roots, net_states)
        c.create_rectangle(
            left_x1 + 14, probe_y - 11, left_x2 - 14, probe_y + 11,
            fill="#102921", outline="#467362", width=1
        )
        c.create_text(
            left_x1 + 22, probe_y,
            text=probe_info,
            fill=CYAN if self.hover_node else MUTED,
            anchor="w",
            font=("Consolas", 8, "bold")
        )

        # ----------------------------------------------------
        # 4. 7-SEGMENT DISPLAYS & POWER TERMINALS
        # ----------------------------------------------------
        for disp_key, (sx, sy, title) in self.seg_displays.items():
            bits = []
            for bit_num in (3, 2, 1, 0):
                node_name = f"D{disp_key}{bit_num}"
                r = roots.get(node_name)
                st = net_states.get(r) if r is not None else None
                bits.append(st)

            self._draw_7seg(sx, sy, title, bits)

            for bit_num in (3, 2, 1, 0):
                node_name = f"D{disp_key}{bit_num}"
                jx, jy, blabel = self.seg_jacks[node_name]
                r = roots.get(node_name)
                st = net_states.get(r) if r is not None else None
                jcol = GREEN if st == 1 else ("#8fd4b0" if st == 0 else "#d8e4dc")
                self._jack(jx, jy, "", color=jcol, radius=4, node_id=node_name)
                c.create_text(
                    jx, jy + 12,
                    text=blabel[:2],
                    fill=MUTED,
                    font=("Segoe UI", 7, "bold")
                )

        power_y = by2 - 58
        c.create_text(
            right_x1 + 18, power_y,
            text="POWER:",
            fill=GOLD, anchor="w",
            font=("Segoe UI", 9, "bold")
        )
        vcc_x, vcc_y = self.power_jacks["VCC"]
        gnd_x, gnd_y = self.power_jacks["GND"]
        self._jack(vcc_x, vcc_y, "+5V (VCC)", color=RED, node_id="VCC")
        self._jack(gnd_x, gnd_y, "GND (0V)", color="#222826", label_color=TEXT, node_id="GND")

        # ----------------------------------------------------
        # 5. BREADBOARD IC SOCKET GRID & PLACED ICs
        # ----------------------------------------------------
        ax1, ay1, ax2, ay2 = self.ic_area
        c.create_rectangle(
            ax1, ay1, ax2, ay2,
            fill=BOARD_INNER, outline="#396656", width=1
        )

        for x in range(int(ax1 + 24), int(ax2 - 12), 32):
            for y in range(int(ay1 + 16), int(ay2 - 12), 32):
                c.create_oval(
                    x - 1.5, y - 1.5, x + 1.5, y + 1.5,
                    fill="#3e6b5b", outline=""
                )

        # Ghost IC preview when placing a new IC from palette
        if (
            self.selected_ic_type
            and ax1 <= self.mouse_x <= ax2
            and ay1 <= self.mouse_y <= ay2
        ):
            self._draw_ghost_ic(self.mouse_x, self.mouse_y, self.selected_ic_type)

        # Placed ICs
        for ic in self.ics:
            self._draw_ic(ic, groups, roots, drivers, net_states)

        # ----------------------------------------------------
        # 6. DRAW PATCH WIRES (With Hover Glow & Signal Flow)
        # ----------------------------------------------------
        for wi, wire in enumerate(self.wires):
            a = self._point_for_node(wire["a"])
            b = self._point_for_node(wire["b"])
            if not a or not b:
                continue

            x1, y1 = a
            x2, y2 = b
            settle = wire.get("settle", 1.0)
            hov_w = self.wire_hover_anim.get(wi, 0.0)

            base_sag = max(
                18,
                min(85, abs(x2 - x1) * 0.12 + abs(y2 - y1) * 0.10)
            )
            # Spring settle effect when wire is newly created
            sag = base_sag * settle + math.sin(settle * math.pi * 2.5) * (1.0 - settle) * 18.0

            color = wire["color"]
            mid_x = (x1 + x2) / 2
            mid_y = max(y1, y2) + sag
            coords = (x1, y1, mid_x, mid_y, x2, y2)

            # Determine logic state on this wire for live signal pulse animation
            w_root = roots.get(wire["a"])
            w_state = net_states.get(w_root) if w_root is not None else None

            # Hover aura
            if hov_w > 0.02:
                c.create_line(
                    *coords,
                    smooth=True, splinesteps=28,
                    fill=lerp_color("#1b4438", "#ffffff", hov_w * 0.75),
                    width=7 + hov_w * 4,
                    capstyle="round"
                )

            # Wire shadow
            c.create_line(
                x1, y1 + 3, mid_x, mid_y + 3, x2, y2 + 3,
                smooth=True, splinesteps=24,
                fill="#070d0b",
                width=6.5,
                capstyle="round"
            )

            # Main wire insulation
            c.create_line(
                *coords,
                smooth=True, splinesteps=28,
                fill=lerp_color(color, "#ffffff", hov_w * 0.28),
                width=4.0 + hov_w * 1.5,
                capstyle="round"
            )

            # Animated signal propagation pulse dots when wire is HIGH (1) or CONFLICT (X)
            if w_state in (1, "X"):
                pulse_col = "#ffffff" if w_state == 1 else RED
                for offset in (0.0, 0.33, 0.66):
                    t = (self.signal_phase + offset) % 1.0
                    px_w = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * mid_x + t ** 2 * x2
                    py_w = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * mid_y + t ** 2 * y2
                    c.create_oval(
                        px_w - 2.5, py_w - 2.5, px_w + 2.5, py_w + 2.5,
                        fill=pulse_col, outline=""
                    )

            # Plug boots at ends
            for ex, ey in ((x1, y1), (x2, y2)):
                c.create_oval(
                    ex - 4.5, ey - 4.5, ex + 4.5, ey + 4.5,
                    fill=color, outline="#f5f5f5", width=1
                )

        # ----------------------------------------------------
        # 7. LIVE RUBBER-BAND WIRE PREVIEW WHILE WIRING
        # ----------------------------------------------------
        if self.wire_start is not None:
            start_pt = self._point_for_node(self.wire_start)
            if start_pt:
                sx, sy = start_pt
                tx, ty = self.mouse_x, self.mouse_y
                if self.hover_node and self.hover_node != self.wire_start:
                    snap_pt = self._point_for_node(self.hover_node)
                    if snap_pt:
                        tx, ty = snap_pt

                preview_color = WIRE_COLORS[self.wire_color_index % len(WIRE_COLORS)]
                sag = max(16, min(70, abs(tx - sx) * 0.12 + abs(ty - sy) * 0.10))
                p_coords = (sx, sy, (sx + tx) / 2, max(sy, ty) + sag, tx, ty)

                c.create_line(
                    *p_coords,
                    smooth=True, splinesteps=24,
                    fill="#09120f", width=6, capstyle="round"
                )
                c.create_line(
                    *p_coords,
                    smooth=True, splinesteps=24,
                    fill=preview_color, width=3.5, dash=(8, 4), capstyle="round"
                )
                c.create_oval(
                    tx - 5, ty - 5, tx + 5, ty + 5,
                    outline=preview_color, width=2
                )

        # ----------------------------------------------------
        # 8. DRAW ACTIVE & HOVER RINGS ON JACKS
        # ----------------------------------------------------
        for node, (nx, ny) in self._all_nodes().items():
            is_start = (node == self.wire_start)
            hov_n = self.node_hover_anim.get(node, 0.0)

            if is_start or hov_n > 0.03:
                ring_r = 7.0 + hov_n * 4.5
                ring_col = (
                    "#ffe066" if is_start
                    else lerp_color("#467362", CYAN, hov_n)
                )
                c.create_oval(
                    nx - ring_r, ny - ring_r, nx + ring_r, ny + ring_r,
                    outline=ring_col,
                    width=2.0 + hov_n * 1.0
                )

        # ----------------------------------------------------
        # 9. FLOATING HOVER TOOLTIP HUD
        # ----------------------------------------------------
        self._draw_hover_tooltip(roots, net_states)

        c.create_text(
            bx2 - 14,
            by2 - 7,
            text=(
                "LEFT CLICK: toggle / wire / place  •  "
                "DRAG IC: move  •  RIGHT CLICK (or Ctrl+Click): remove wire/IC  •  ESC: cancel"
            ),
            fill="#9ec2b4",
            anchor="se",
            font=("Segoe UI", 8)
        )

    # ========================================================
    # DRAW BOARD SECTIONS & JACKS
    # ========================================================

    def _section(self, x1, y1, x2, y2, title):
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#193f33", outline="#588271", width=1
        )
        self.canvas.create_rectangle(
            x1, y1, x2, y1 + 24,
            fill="#143329", outline="#588271", width=1
        )
        self.canvas.create_text(
            x1 + 10, y1 + 5,
            text=title,
            fill=GOLD, anchor="nw",
            font=("Segoe UI", 8, "bold")
        )

    def _jack(
        self,
        x,
        y,
        label,
        color="#d8e4dc",
        radius=5,
        label_color=TEXT,
        node_id=None
    ):
        hov = self.node_hover_anim.get(node_id, 0.0) if node_id else 0.0
        r = radius + hov * 1.6

        self.canvas.create_oval(
            x - r - 1.5, y - r - 1.5, x + r + 1.5, y + r + 1.5,
            fill="#0b1511",
            outline=lerp_color("#c9ba93", CYAN, hov),
            width=1.2
        )
        self.canvas.create_oval(
            x - r + 1, y - r + 1, x + r - 1, y + r - 1,
            fill=lerp_color(color, "#ffffff", hov * 0.35),
            outline="#21332b",
            width=1
        )
        # Inner socket hole
        self.canvas.create_oval(
            x - 1.8, y - 1.8, x + 1.8, y + 1.8,
            fill="#0d1713", outline=""
        )

        if label:
            self.canvas.create_text(
                x + 8, y - 8,
                text=label,
                fill=lerp_color(label_color, GOLD, hov),
                anchor="sw",
                font=("Segoe UI", 7, "bold")
            )

    # ========================================================
    # DRAW 7-SEGMENT DISPLAY
    # ========================================================

    def _draw_7seg(self, x, y, title, bits):
        c = self.canvas
        c.create_text(
            x + 34, y - 14,
            text=title,
            fill=TEXT,
            font=("Segoe UI", 8, "bold")
        )
        c.create_rectangle(
            x, y, x + 68, y + 100,
            fill="#0d1412", outline="#8fa399", width=2
        )

        # Decode 4-bit BCD/Hex input if any pin is connected
        any_connected = any(b in (0, 1) for b in bits)
        has_conflict = any(b == "X" for b in bits)

        if has_conflict:
            seg_mask = (1, 0, 0, 1, 0, 0, 1)  # Error bars
        elif any_connected:
            val = 0
            for b in bits:
                val = (val << 1) | (1 if b == 1 else 0)
            seg_mask = HEX_7SEG.get(val, (0,) * 7)
        else:
            seg_mask = (0, 0, 0, 0, 0, 0, 0)

        segments = [
            (x + 16, y + 12, x + 52, y + 18),  # a (top)
            (x + 52, y + 18, x + 58, y + 46),  # b (top-right)
            (x + 52, y + 52, x + 58, y + 80),  # c (bottom-right)
            (x + 16, y + 80, x + 52, y + 86),  # d (bottom)
            (x + 10, y + 52, x + 16, y + 80),  # e (bottom-left)
            (x + 10, y + 18, x + 16, y + 46),  # f (top-left)
            (x + 16, y + 46, x + 52, y + 52),  # g (middle)
        ]

        for idx, seg_coords in enumerate(segments):
            lit = seg_mask[idx] == 1
            c.create_rectangle(
                *seg_coords,
                fill="#ff4d4d" if lit else "#2b1919",
                outline="#ff9999" if lit else "#3d2424"
            )

    # ========================================================
    # DRAW GHOST IC & PLACED IC
    # ========================================================

    def _draw_ghost_ic(self, x, y, typ):
        c = self.canvas
        pins = IC_SPECS[typ]["pins"]
        half = pins // 2
        spacing = 18
        body_h = (half - 1) * spacing + 28
        body_w = 92 if pins <= 16 else 108

        x1, y1 = x - body_w / 2, y - body_h / 2
        x2, y2 = x + body_w / 2, y + body_h / 2

        c.create_rectangle(
            x1, y1, x2, y2,
            fill="#1f4d3f", outline=GOLD, width=2, dash=(5, 3)
        )
        c.create_text(
            x, y - 4,
            text=typ,
            fill=GOLD,
            font=("Consolas", 12, "bold")
        )
        c.create_text(
            x, y + 12,
            text="CLICK TO PLACE",
            fill=TEXT,
            font=("Segoe UI", 6, "bold")
        )

    def _draw_ic(self, ic, groups, roots, drivers, net_states):
        c = self.canvas
        x = ic["x"]
        y = ic["y"]
        ic_id = ic["id"]
        typ = ic["type"]
        spec = IC_SPECS[typ]
        pins = ic["pins"]
        half = pins // 2

        scale = self.ic_scale_anim.get(ic_id, 1.0)
        hov = self.ic_hover_anim.get(ic_id, 0.0)
        is_dragging = (self.drag_ic is not None and self.drag_ic["id"] == ic_id)

        x1, y1, x2, y2 = ic["body_rect"]
        if abs(scale - 1.0) > 0.005:
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            x1 = cx + (x1 - cx) * scale
            x2 = cx + (x2 - cx) * scale
            y1 = cy + (y1 - cy) * scale
            y2 = cy + (y2 - cy) * scale

        # Check IC power state for visual badge
        pwr_status = self._ic_power_status(ic, groups, roots, drivers)

        # Drop shadow (elevates when dragging or hovering)
        sh_off = 7 if is_dragging else (4 + hov * 2)
        c.create_rectangle(
            x1 + sh_off, y1 + sh_off, x2 + sh_off, y2 + sh_off,
            fill="#08110e", outline=""
        )

        # IC Body
        body_border = lerp_color("#98a89f", GOLD, hov)
        if is_dragging:
            body_border = CYAN
        c.create_rectangle(
            x1, y1, x2, y2,
            fill=lerp_color("#121a17", "#1a2622", hov),
            outline=body_border,
            width=2
        )

        # Metallic pins legs connecting body to pin jacks
        for p, (px, py) in ic["pin_positions"].items():
            if p <= half:
                c.create_line(px + 4, py, x1, py, fill="#9aa8a0", width=3)
            else:
                c.create_line(x2, py, px - 4, py, fill="#9aa8a0", width=3)

        # Top orientation notch & Pin 1 dot
        c.create_arc(
            x - 11, y1 - 1, x + 11, y1 + 17,
            start=0, extent=-180,
            outline="#d0dbd4", width=2, style="arc"
        )
        c.create_oval(
            x1 + 8, y1 + 10, x1 + 14, y1 + 16,
            fill="#768a80", outline=""
        )

        # Power Indicator LED on IC package
        pwr_col = (
            GREEN if pwr_status == "POWERED"
            else CYAN if pwr_status == "AUTO"
            else RED
        )
        c.create_oval(
            x2 - 15, y1 + 9, x2 - 7, y1 + 17,
            fill=pwr_col, outline="#ffffff" if pwr_status in ("POWERED", "AUTO") else "#773333"
        )

        # IC Labels
        c.create_text(
            x, y - 6,
            text=f"IC{ic_id} • {typ}",
            fill="#f0f4ec",
            font=("Consolas", 11, "bold")
        )
        c.create_text(
            x, y + 10,
            text=spec["label"],
            fill=GOLD if hov > 0.3 else "#9bb5a8",
            font=("Segoe UI", 7, "bold")
        )

        pwr_label = (
            "PWR: +5V OK" if pwr_status == "POWERED"
            else "PWR: AUTO" if pwr_status == "AUTO"
            else "PWR: FAULT!" if pwr_status == "FAULT"
            else "UNPOWERED"
        )
        c.create_text(
            x, y + 25,
            text=pwr_label,
            fill=pwr_col,
            font=("Segoe UI", 6, "bold")
        )

        # Draw IC Pin Jacks with live state color coding
        for p, (px, py) in ic["pin_positions"].items():
            node_id = self._pin_node(ic, p)
            r = roots.get(node_id)
            p_state = net_states.get(r) if r is not None else None

            if p_state == 1:
                pin_col = GREEN
            elif p_state == 0:
                pin_col = "#7bc7a2"
            elif p_state == "X":
                pin_col = RED
            else:
                pin_col = "#c7d4cd"

            self._jack(
                px, py, "",
                color=pin_col,
                radius=4.2,
                node_id=node_id
            )

            # Pin number label positioned cleanly inside/beside pin
            lbl_x = px - 13 if p <= half else px + 13
            c.create_text(
                lbl_x, py,
                text=str(p),
                fill=TEXT if self.hover_node == node_id else MUTED,
                font=("Consolas", 7, "bold")
            )

        c.create_text(
            x, y2 + 10,
            text=f"VCC=Pin {spec['vcc']}   GND=Pin {spec['gnd']}",
            fill="#f3d18a",
            font=("Segoe UI", 7, "bold")
        )

    # ========================================================
    # HOVER TOOLTIP & PROBE SUMMARY
    # ========================================================

    def _describe_node(self, node):
        if not node:
            return ""
        if node.startswith("I") and node[1:].isdigit():
            idx = int(node[1:])
            return f"Input Switch S{idx} (Jack I/P{idx})"
        if node.startswith("O") and node[1:].isdigit():
            idx = int(node[1:])
            return f"Output Indicator LED L{idx} (Jack O/P{idx})"
        if node == "VCC":
            return "+5V Regulated Supply Rail (Logic 1)"
        if node == "GND":
            return "Ground Reference Rail (Logic 0)"
        if node == "PULSE":
            return "Logic Pulser Output Jack"
        if node.startswith("C") and node[1:].isdigit():
            idx = int(node[1:])
            hz = self.clock_freqs[idx][0] if idx < len(self.clock_freqs) else ""
            return f"Clock Oscillator Output ({hz})"
        if node.startswith("DA") or node.startswith("DB"):
            disp = node[1]
            bit = node[2]
            return f"7-Segment Display {disp} • BCD Input Bit D{bit} (Weight {1 << int(bit)})"
        if node.startswith("IC") and ".P" in node:
            ic_part, p_part = node.split(".P")
            ic_id = int(ic_part[2:])
            pin_num = int(p_part)
            for ic in self.ics:
                if ic["id"] == ic_id:
                    spec = IC_SPECS[ic["type"]]
                    pname = spec.get("pin_names", {}).get(pin_num, f"Pin {pin_num}")
                    return f"IC{ic_id} ({ic['type']}) • Pin {pin_num}: {pname}"
        return node

    def _format_state(self, state):
        if state == 1:
            return "HIGH (1 / +5V)"
        if state == 0:
            return "LOW (0 / 0V)"
        if state == "X":
            return "CONFLICT (X)"
        return "FLOATING (Hi-Z)"

    def _get_probe_summary(self, roots, net_states):
        if self.hover_node:
            r = roots.get(self.hover_node)
            st = net_states.get(r) if r is not None else None
            return f"PROBE [{self.hover_node}] -> {self._format_state(st)}"
        if self.hover_wire is not None and 0 <= self.hover_wire < len(self.wires):
            w = self.wires[self.hover_wire]
            r = roots.get(w["a"])
            st = net_states.get(r) if r is not None else None
            return f"PROBE WIRE [{w['a']} ↔ {w['b']}] -> {self._format_state(st)}"
        return "PROBE READY: Hover over any pin, jack, or wire to inspect logic level"

    def _draw_hover_tooltip(self, roots, net_states):
        c = self.canvas
        text_lines = []

        if self.hover_node:
            r = roots.get(self.hover_node)
            st = net_states.get(r) if r is not None else None
            text_lines.append(self._describe_node(self.hover_node))
            text_lines.append(f"Logic State: {self._format_state(st)}")
            if self.wire_start is None:
                text_lines.append("Left-click to start a patch wire")
            elif self.wire_start == self.hover_node:
                text_lines.append("Left-click to cancel wire")
            else:
                text_lines.append(f"Left-click to connect wire from {self.wire_start}")

        elif self.hover_wire is not None and 0 <= self.hover_wire < len(self.wires):
            w = self.wires[self.hover_wire]
            r = roots.get(w["a"])
            st = net_states.get(r) if r is not None else None
            text_lines.append(f"Patch Wire: {w['a']} ↔ {w['b']}")
            text_lines.append(f"Signal: {self._format_state(st)} • Right-click to remove")

        elif self.hover_ic is not None and not self.drag_ic:
            ic = self.hover_ic
            spec = IC_SPECS[ic["type"]]
            text_lines.append(f"IC{ic['id']}: {ic['type']} ({spec['label']})")
            text_lines.append(
                f"VCC=Pin {spec['vcc']}, GND=Pin {spec['gnd']} • Drag to move • Right-click to remove"
            )

        if not text_lines:
            return

        full_text = "\n".join(text_lines)
        tx = self.mouse_x + 16
        ty = self.mouse_y - 14

        cw, ch = self._layout()
        if tx > cw - 320:
            tx = self.mouse_x - 16
            anchor = "se"
        else:
            anchor = "sw"
        if ty < 70:
            ty = self.mouse_y + 24
            anchor = "nw" if anchor == "sw" else "ne"

        tid = c.create_text(
            tx, ty,
            text=full_text,
            fill=TEXT,
            anchor=anchor,
            font=("Segoe UI", 8, "bold")
        )
        bbox = c.bbox(tid)
        if bbox:
            pad_x, pad_y = 8, 5
            bg_id = c.create_rectangle(
                bbox[0] - pad_x, bbox[1] - pad_y,
                bbox[2] + pad_x, bbox[3] + pad_y,
                fill="#0d1815", outline=GOLD, width=1.2
            )
            c.tag_raise(tid, bg_id)

    # ========================================================
    # NODE MANAGEMENT & HIT TESTING
    # ========================================================

    def _all_nodes(self):
        nodes = {}
        for k, p in getattr(self, "input_jacks", {}).items():
            nodes[k] = p
        for k, p in getattr(self, "output_jacks", {}).items():
            nodes[k] = p
        for k, p in getattr(self, "clock_jacks", {}).items():
            nodes[k] = p
        for k, p in getattr(self, "pulser_jacks", {}).items():
            nodes[k] = p
        for k, p in getattr(self, "power_jacks", {}).items():
            nodes[k] = p
        for k, (jx, jy, _lbl) in getattr(self, "seg_jacks", {}).items():
            nodes[k] = (jx, jy)
        for ic in self.ics:
            for p, pos in ic.get("pin_positions", {}).items():
                nodes[self._pin_node(ic, p)] = pos
        return nodes

    def _pin_node(self, ic, pin):
        return f"IC{ic['id']}.P{pin}"

    def _point_for_node(self, node):
        return self._all_nodes().get(node)

    def _find_node(self, x, y):
        nodes = self._all_nodes()
        best = None
        best_d = 14
        for node, (nx, ny) in nodes.items():
            d = math.hypot(x - nx, y - ny)
            if d < best_d:
                best = node
                best_d = d
        return best

    def _find_switch(self, x, y):
        for i, (bx1, by1, bx2, by2, _sx, _sy) in getattr(self, "switch_boxes", {}).items():
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return i
        return None

    def _find_wire(self, x, y):
        best_i = None
        best_d = 10
        for i, wire in enumerate(self.wires):
            a = self._point_for_node(wire["a"])
            b = self._point_for_node(wire["b"])
            if not a or not b:
                continue
            x1, y1 = a
            x2, y2 = b
            sag = max(18, min(85, abs(x2 - x1) * 0.12 + abs(y2 - y1) * 0.10))
            for j in range(31):
                t = j / 30
                qx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * ((x1 + x2) / 2) + t ** 2 * x2
                qy = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * (max(y1, y2) + sag) + t ** 2 * y2
                d = math.hypot(x - qx, y - qy)
                if d < best_d:
                    best_i = i
                    best_d = d
        return best_i

    def _find_ic(self, x, y):
        for ic in reversed(self.ics):
            box = ic.get("bbox")
            if box and (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
                return ic
        return None

    def _in_pulser_btn(self, x, y):
        box = getattr(self, "pulser_btn_box", None)
        return bool(box and box[0] <= x <= box[2] and box[1] <= y <= box[3])

    # ========================================================
    # MOUSE MOTION & HOVER DETECTION
    # ========================================================

    def on_motion(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

        prev_state = (
            self.hover_node,
            self.hover_switch,
            self.hover_wire,
            self.hover_ic["id"] if self.hover_ic else None,
            self.hover_pulser,
        )

        self.hover_node = self._find_node(event.x, event.y)
        self.hover_switch = None if self.hover_node else self._find_switch(event.x, event.y)
        self.hover_pulser = (
            False if (self.hover_node or self.hover_switch)
            else self._in_pulser_btn(event.x, event.y)
        )
        self.hover_ic = (
            None if (self.hover_node or self.hover_switch or self.hover_pulser)
            else self._find_ic(event.x, event.y)
        )
        self.hover_wire = (
            None if (self.hover_node or self.hover_switch or self.hover_pulser or self.hover_ic)
            else self._find_wire(event.x, event.y)
        )

        # Update cursor smoothly based on hovered interactive element
        if self.hover_node or self.hover_switch or self.hover_pulser or self.hover_wire is not None:
            self.canvas.configure(cursor="hand2")
        elif self.hover_ic:
            self.canvas.configure(cursor="fleur")
        elif self.selected_ic_type:
            self.canvas.configure(cursor="crosshair")
        else:
            self.canvas.configure(cursor="")

        new_state = (
            self.hover_node,
            self.hover_switch,
            self.hover_wire,
            self.hover_ic["id"] if self.hover_ic else None,
            self.hover_pulser,
        )

        if self.hover_node != prev_state[0] and self.hover_node is not None:
            self.detail_text.set(self._describe_node(self.hover_node))

        if (
            new_state != prev_state
            or self.wire_start is not None
            or self.selected_ic_type is not None
        ):
            self.draw(recompute=False)

    def on_leave_canvas(self, _event=None):
        self.hover_node = None
        self.hover_switch = None
        self.hover_wire = None
        self.hover_ic = None
        self.hover_pulser = False

    # ========================================================
    # CLICK, DRAG & RIGHT-CLICK HANDLING
    # ========================================================

    def on_click(self, event):
        x = event.x
        y = event.y

        # 1. Logic Pulser momentary button
        if self._in_pulser_btn(x, y):
            self.pulse_state = 1
            self.pulse_until = time.perf_counter() + 0.45
            self.status_text.set("Logic Pulser triggered: PULSE = 1 (450 ms single shot).")
            self.draw()
            return

        # 2. Toggle an input switch (S1 - S16)
        sw = self._find_switch(x, y)
        if sw is not None:
            self.input_values[sw] = 1 - self.input_values[sw]
            self.draw()
            self.status_text.set(f"Switch S{sw} toggled to {self.input_values[sw]}.")
            return

        # 3. Connect or start a patch wire on a node/jack
        node = self._find_node(x, y)
        if node:
            if self.wire_start is None:
                self.wire_start = node
                self.status_text.set(
                    f"Wire started at {node} ({self._describe_node(node)}). "
                    "Click another jack or pin to complete connection."
                )
                self.draw()
            elif node == self.wire_start:
                self.wire_start = None
                self.status_text.set("Wire cancelled.")
                self.draw()
            else:
                self.wires.append({
                    "a": self.wire_start,
                    "b": node,
                    "color": WIRE_COLORS[self.wire_color_index % len(WIRE_COLORS)],
                    "settle": 0.0,
                })
                self.wire_color_index += 1
                start = self.wire_start
                self.wire_start = None
                self.draw()
                self.status_text.set(f"Connected {start} ↔ {node}.")
            return

        # 4. Drag an existing IC
        ic = self._find_ic(x, y)
        if ic:
            self.drag_ic = ic
            self.drag_offset = (x - ic["x"], y - ic["y"])
            self.ics.remove(ic)
            self.ics.append(ic)
            self.draw()
            return

        # 5. Place a selected IC in the breadboard socket area
        if self.selected_ic_type:
            if not (
                self.ic_area[0] <= x <= self.ic_area[2]
                and self.ic_area[1] <= y <= self.ic_area[3]
            ):
                self.status_text.set("Place IC inside the central breadboard IC socket area.")
                return

            typ = self.selected_ic_type
            spec = IC_SPECS[typ]
            ic = {
                "id": self.next_ic_id,
                "type": typ,
                "pins": spec["pins"],
                "x": x,
                "y": y,
            }
            self.ic_scale_anim[ic["id"]] = 0.65
            self.next_ic_id += 1
            self.ics.append(ic)
            self.selected_ic_type = None
            for btn in self.palette_buttons.values():
                btn.set_selected(False)

            self.draw()
            self.status_text.set(
                f"Placed {typ} (IC{ic['id']}). "
                f"Power pins: Pin {spec['vcc']}=+5V, Pin {spec['gnd']}=GND."
            )

    def on_drag(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.drag_ic:
            ic = self.drag_ic
            ax1, ay1, ax2, ay2 = self.ic_area
            ic["x"] = max(ax1 + 55, min(ax2 - 55, event.x - self.drag_offset[0]))
            ic["y"] = max(ay1 + 75, min(ay2 - 75, event.y - self.drag_offset[1]))
            self.draw()

    def on_release(self, _event):
        if self.drag_ic:
            self.drag_ic = None
            self.draw()

    def on_right_click(self, event):
        if self.wire_start is not None:
            self.wire_start = None
            self.status_text.set("Wire cancelled.")
            self.draw()
            return

        wire_idx = self._find_wire(event.x, event.y)
        if wire_idx is not None:
            wire = self.wires.pop(wire_idx)
            self.hover_wire = None
            self.draw()
            self.status_text.set(f"Removed wire {wire['a']} ↔ {wire['b']}.")
            return

        ic = self._find_ic(event.x, event.y)
        if ic:
            removed = ic["id"]
            prefix = f"IC{removed}."
            self.wires = [
                w for w in self.wires
                if not (w["a"].startswith(prefix) or w["b"].startswith(prefix))
            ]
            self.ics.remove(ic)
            self.hover_ic = None
            self.draw()
            self.status_text.set(f"Removed IC{removed} and its attached wires.")

    def on_ctrl_click(self, event):
        self.on_right_click(event)

    # ========================================================
    # CLEAR / RESET
    # ========================================================

    def clear_wires(self):
        self.wires.clear()
        self.wire_start = None
        self.hover_wire = None
        self.draw()
        self.status_text.set("All patch wires cleared.")

    def reset_board(self):
        answer = messagebox.askyesno(
            "Reset board",
            "Remove every IC and patch wire and reset switches?"
        )
        if not answer:
            return

        self.ics.clear()
        self.wires.clear()
        self.wire_start = None
        self.input_values = {i: 0 for i in range(1, 17)}
        self.next_ic_id = 1
        self.selected_ic_type = None
        for btn in self.palette_buttons.values():
            btn.set_selected(False)
        self.draw()
        self.status_text.set("Board reset.")

    # ========================================================
    # NET CONNECTIONS & DIGITAL LOGIC ENGINE
    # ========================================================

    def _net_map(self):
        nodes = list(self._all_nodes().keys())
        parent = {n: n for n in nodes}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            if a not in parent or b not in parent:
                return
            ra = find(a)
            rb = find(b)
            if ra != rb:
                parent[rb] = ra

        for wire in self.wires:
            union(wire["a"], wire["b"])

        groups = {}
        for node in nodes:
            root = find(node)
            groups.setdefault(root, []).append(node)

        roots = {node: find(node) for node in nodes}
        return groups, roots

    def _base_net_value(self, root, groups):
        """
        Returns the logic value supplied directly by input switches,
        power rails (+5V / GND), clock oscillators, and logic pulser.
        """
        values = []
        for node in groups.get(root, []):
            if node.startswith("I") and node[1:].isdigit():
                index = int(node[1:])
                values.append(self.input_values[index])
            elif node == "VCC":
                values.append(1)
            elif node == "GND":
                values.append(0)
            elif node == "PULSE":
                values.append(self.pulse_state)
            elif node.startswith("C") and node[1:].isdigit():
                c_idx = int(node[1:])
                values.append(self.clock_states.get(c_idx, 0))

        if not values:
            return None
        if 0 in values and 1 in values:
            return "X"
        return values[0]

    def _resolve_net(self, root, groups, drivers):
        values = []
        base = self._base_net_value(root, groups)
        if base is not None:
            values.append(base)

        if root in drivers:
            for driver_value in drivers[root]:
                if driver_value is not None:
                    values.append(driver_value)

        if not values:
            return None
        if "X" in values:
            return "X"
        if 0 in values and 1 in values:
            return "X"
        return values[0]

    def _read_pin(self, ic, pin, groups, roots, drivers):
        node = self._pin_node(ic, pin)
        root = roots.get(node)
        if root is None:
            return None
        return self._resolve_net(root, groups, drivers)

    def _ic_power_status(self, ic, groups, roots, drivers):
        """
        Returns:
            "POWERED"   - Explicit +5V on VCC and GND on GND
            "AUTO"      - Auto-powered (no conflicting rail on VCC/GND)
            "FAULT"     - Reverse polarity or wrong logic level on VCC/GND
            "UNPOWERED" - Strict mode active and VCC/GND not both wired
        """
        spec = IC_SPECS[ic["type"]]
        vcc = self._read_pin(ic, spec["vcc"], groups, roots, drivers)
        gnd = self._read_pin(ic, spec["gnd"], groups, roots, drivers)

        if vcc == 1 and gnd == 0:
            return "POWERED"
        if vcc in (0, "X") or gnd in (1, "X"):
            return "FAULT"
        if self.auto_power:
            return "AUTO"
        return "UNPOWERED"

    def _evaluate_ic(self, ic, groups, roots, drivers):
        typ = ic["type"]
        pwr = self._ic_power_status(ic, groups, roots, drivers)

        if pwr not in ("POWERED", "AUTO"):
            return {}

        outputs = {}

        # ----------------------------------------------------
        # 7404 HEX INVERTER
        # ----------------------------------------------------
        if typ == "7404":
            pairs = [
                (1, 2),
                (3, 4),
                (5, 6),
                (9, 8),
                (11, 10),
                (13, 12),
            ]
            for input_pin, output_pin in pairs:
                value = self._read_pin(ic, input_pin, groups, roots, drivers)
                if value in (0, 1):
                    outputs[output_pin] = 1 - value
                elif value == "X":
                    outputs[output_pin] = "X"
                else:
                    outputs[output_pin] = None

        # ----------------------------------------------------
        # 7408 AND, 7432 OR, 7486 XOR
        # ----------------------------------------------------
        elif typ in ("7408", "7432", "7486"):
            gates = [
                (1, 2, 3),
                (4, 5, 6),
                (9, 10, 8),
                (12, 13, 11),
            ]
            for a_pin, b_pin, output_pin in gates:
                a = self._read_pin(ic, a_pin, groups, roots, drivers)
                b = self._read_pin(ic, b_pin, groups, roots, drivers)

                if a == "X" or b == "X":
                    outputs[output_pin] = "X"
                elif a not in (0, 1) or b not in (0, 1):
                    # Standard deterministic dominance even when only one input is driven,
                    # or require both inputs if neither dominates:
                    if typ == "7408" and (a == 0 or b == 0):
                        outputs[output_pin] = 0
                    elif typ == "7432" and (a == 1 or b == 1):
                        outputs[output_pin] = 1
                    else:
                        outputs[output_pin] = None
                elif typ == "7408":
                    outputs[output_pin] = a & b
                elif typ == "7432":
                    outputs[output_pin] = a | b
                else:
                    outputs[output_pin] = a ^ b

        # ----------------------------------------------------
        # 74151 8-TO-1 MULTIPLEXER
        # ----------------------------------------------------
        elif typ == "74151":
            enable = self._read_pin(ic, 7, groups, roots, drivers)
            # In Auto-Power mode, if active-low Strobe (/G, Pin 7) is left
            # floating, default it to enabled (0) so students can test MUX
            # selection immediately; if wired to 1, it disables outputs (Y=0, W=1).
            if enable is None and self.auto_power:
                enable = 0

            select_c = self._read_pin(ic, 11, groups, roots, drivers)
            select_b = self._read_pin(ic, 10, groups, roots, drivers)
            select_a = self._read_pin(ic, 9, groups, roots, drivers)

            data_pins = [4, 3, 2, 1, 15, 14, 13, 12]
            data_values = [
                self._read_pin(ic, pin, groups, roots, drivers)
                for pin in data_pins
            ]

            y = None
            if enable == 1:
                # Strobe HIGH disables the 74151: output Y is forced LOW (0), W is HIGH (1)
                y = 0
            elif enable == 0:
                select_values = (select_c, select_b, select_a)
                if all(value in (0, 1) for value in select_values):
                    index = (select_c << 2) | (select_b << 1) | select_a
                    y = data_values[index]

            outputs[5] = y
            if y in (0, 1):
                outputs[6] = 1 - y
            else:
                outputs[6] = None

        return outputs

    def _evaluate(self):
        """
        Iteratively evaluates all nets and ICs until steady state.
        """
        groups, roots = self._net_map()
        drivers = {}

        max_iterations = max(10, len(self.ics) * 6 + 10)
        for _ in range(max_iterations):
            new_drivers = {}
            for ic in self.ics:
                outputs = self._evaluate_ic(ic, groups, roots, drivers)
                for pin, value in outputs.items():
                    node = self._pin_node(ic, pin)
                    root = roots.get(node)
                    if root is None:
                        continue
                    new_drivers.setdefault(root, []).append(value)

            if new_drivers == drivers:
                drivers = new_drivers
                break
            drivers = new_drivers

        net_states = {}
        for root in groups:
            net_states[root] = self._resolve_net(root, groups, drivers)

        errors = []
        for ic in self.ics:
            spec = IC_SPECS[ic["type"]]
            pwr = self._ic_power_status(ic, groups, roots, drivers)
            if pwr == "FAULT":
                errors.append(
                    f"IC{ic['id']} ({ic['type']}): Power fault! "
                    f"Ensure Pin {spec['vcc']} is connected to +5V and Pin {spec['gnd']} to GND."
                )
            elif pwr == "UNPOWERED":
                errors.append(
                    f"IC{ic['id']} ({ic['type']}): Unpowered in STRICT mode. "
                    f"Connect Pin {spec['vcc']} to +5V and Pin {spec['gnd']} to GND."
                )

        for root, values in drivers.items():
            base = self._base_net_value(root, groups)
            active_values = [v for v in values if v is not None]
            if base == "X":
                errors.append(
                    f"Short-circuit conflict on net {root}: "
                    "net connects both logic 0 and logic 1 sources."
                )
            elif base in (0, 1) and any(v != base for v in active_values):
                errors.append(
                    f"Driver conflict on net {root}: "
                    "an IC output conflicts with a switch or power rail."
                )
            if 0 in active_values and 1 in active_values:
                errors.append(f"Multiple IC outputs conflict on net {root}.")

        return groups, roots, drivers, net_states, errors

    def _net_value(self, out_node):
        try:
            if not getattr(self, "output_jacks", None):
                self._compute_geometry()
            _groups, roots, _drivers, net_states, _errors = self._evaluate()
            root = roots.get(f"O{out_node[1]}")
            if root is None:
                return None
            return net_states.get(root)
        except Exception:
            return None

    # ========================================================
    # STATUS REPORT DIALOG
    # ========================================================

    def show_status(self):
        self._compute_geometry()
        groups, roots, drivers, net_states, errors = self._evaluate()

        messages = []
        if errors:
            messages.extend(errors)
        else:
            if not self.ics:
                messages.append("No ICs placed on the board yet.")
            else:
                for ic in self.ics:
                    spec = IC_SPECS[ic["type"]]
                    pwr = self._ic_power_status(ic, groups, roots, drivers)
                    if pwr == "POWERED":
                        messages.append(
                            f"IC{ic['id']} ({ic['type']}): Powered via physical +5V/GND wires (OK)."
                        )
                    elif pwr == "AUTO":
                        messages.append(
                            f"IC{ic['id']} ({ic['type']}): Operating in Auto-Power mode "
                            f"(Pin {spec['vcc']}=+5V, Pin {spec['gnd']}=GND optional)."
                        )

        messages.append("")
        messages.append("LED / OUTPUT JACK STATES:")

        output_states = []
        for i in range(1, 17):
            root = roots.get(f"O{i}")
            state = net_states.get(root) if root is not None else None
            state_text = "Z" if state is None else str(state)
            output_states.append(f"L{i}={state_text}")

        messages.append("   ".join(output_states[:8]))
        messages.append("   ".join(output_states[8:]))
        messages.append("")
        messages.append(
            "Legend: 0 = LOW (0V), 1 = HIGH (+5V), Z = Floating/Unconnected, X = Conflict."
        )

        messagebox.showinfo("Trainer Status & Wiring Diagnostic", "\n".join(messages))
        self.status_text.set("Status check complete.")


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    root = tk.Tk()
    DigitalTrainer(root)
    root.mainloop()


if __name__ == "__main__":
    main()