# TTL Digital Logic Trainer Simulator

An interactive single-file Python/Tkinter desktop simulator modeled after a physical hardware digital logic lab trainer kit. Built for designing, wiring, and testing combinational TTL integrated circuits with real-time 4-state logic resolution (`0`, `1`, `X`, `Z`), live signal flow animations, and an interactive logic probe HUD.

## Key Features

* **4-State Digital Logic Engine (`0`, `1`, `X`, `Z`)**: Iterative net solver using union-find connectivity to resolve low (`0`), high (`1`), floating/high-impedance (`Z`), and bus contention (`X`) states across cascaded multi-IC circuits.
* **Full 10-IC TTL Suite**:
  * **Basic Logic Gates (14-Pin DIP)**: `7404` (NOT / Hex Inverter), `7408` (Quad AND), `7432` (Quad OR), `7400` (Quad NAND), `7402` (Quad NOR), `7486` (Quad XOR), `74266` (Quad XNOR).
  * **MSI Combinational ICs (16-Pin DIP)**: `74151` (8-to-1 Multiplexer), `74138` (3-to-8 Line Decoder / Demultiplexer), `7483` (4-Bit Binary Full Adder with fast carry).
* **Dual Power Supply Modes (`AUTO` & `STRICT`)**:
  * **Auto-Power Mode**: Evaluates gate outputs immediately for rapid circuit prototyping while still flagging reverse-polarity power faults.
  * **Strict Power Mode**: Enforces physical `+5V (VCC)` and `GND` patch-wire connections on every IC (`Pin 14/7` for 14-pin ICs, `Pin 16/8` for `74151`/`74138`, and `Pin 5/12` for `7483`).
* **Interactive Breadboard & Wire Routing**:
  * **Draggable Patch Cords**: Click and drag the middle of any wire to curve it cleanly around IC packages and pins.
  * **Smart X-Ray Net Highlighting**: Hovering over any pin or jack illuminates all wires on that net while dimming unrelated crossing wires.
  * **Live Logic Probe HUD**: Floating tooltip displays exact IC pinout designations, Boolean expressions, and real-time logic voltage levels on hover.
* **Built-In Lab Peripherals**:
  * **16 Animated Input Toggle Switches (`S1`–`S16`)**
  * **16 Glowing Output LEDs (`L1`–`L16`)** positioned to the right of their jacks for unobstructed visibility
  * **6 Live Clock Oscillators (`0.1Hz` to `500Hz`)** and a single-shot **Logic Pulser (`PULSE`)**
  * **Dual Hexadecimal 7-Segment Displays (`DISPLAY A` & `DISPLAY B`)** with 4-bit BCD/Hex inputs (`D3`–`D0`)

## Getting Started

### Prerequisites

* Python 3.8+ (uses standard library `tkinter`, `math`, and `time`—no external `pip` packages required).

### Running the Simulator

```bash
python mhf.py
```

## Controls & Usage

| Action | Control |
| :--- | :--- |
| **Place an IC** | Click an IC in the top palette, then click inside the central breadboard area |
| **Toggle Input Switch** | Left-click any switch `S1`–`S16` |
| **Create Patch Wire** | Left-click a source pin/jack, then left-click a destination pin/jack (`Esc` to cancel) |
| **Bend / Route a Wire** | Left-click and drag the middle of any existing wire to curve it out of the way |
| **Move an IC** | Left-click and drag the IC body across the breadboard |
| **Remove Wire or IC** | Right-click (or `Ctrl` + Left-click) on any wire or IC body |
| **Switch Power Mode** | Click **`PWR: AUTO`** / **`PWR: STRICT`** in the top toolbar |
| **Run Wiring Diagnostic** | Click **`STATUS`** to inspect IC power states, floating outputs, and short-circuit conflicts |
