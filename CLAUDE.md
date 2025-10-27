# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EZ-EMFI is an EMFI (Electromagnetic Fault Injection) probe driver for the Riscure DS1120-PD probe, designed to run on Moku hardware using VHDL. The project integrates with Liquid Instruments' Moku platform through their Multi-instrument Cloud Compile (MCC) framework.

## Architecture

### 3-Layer VoloApp Architecture

The VHDL design follows a strict 3-layer architecture pattern:

**Layer 1: MCC_TOP_volo_loader.vhd** (static, shared infrastructure)
- Not present in this repo (provided by Moku platform)
- Handles bitstream loading and BRAM initialization
- Provides Control Register (CR0-CR30) interface

**Layer 2: DS1120_PD_volo_shim.vhd** (generated, register mapping)
- Location: `VHDL/DS1120_PD_volo_shim.vhd`
- **AUTO-GENERATED - DO NOT EDIT MANUALLY**
- Maps raw Control Registers (CR20-CR30) to application-friendly signal names
- Combines VOLO_READY control bits into `global_enable`
- Would typically be regenerated from a YAML config (not present in repo)

**Layer 3: DS1120_PD_volo_main.vhd** (hand-written application logic)
- Location: `VHDL/DS1120_PD_volo_main.vhd`
- **THIS IS WHERE APPLICATION LOGIC LIVES**
- MCC-agnostic interface using friendly signal names only
- Contains the actual probe driver functionality

### Core VHDL Components

**State Machine Core: `ds1120_pd_fsm.vhd`**
- 7-state FSM: READY → ARMED → FIRING → COOLING → DONE (or TIMEDOUT/HARDFAULT)
- Safety features: fire count limiting (max 15), spurious trigger detection
- Timing constraints: max 32 firing cycles, min 8 cooling cycles
- All state constants defined in `ds1120_pd_pkg.vhd`

**Application Main: `DS1120_PD_volo_main.vhd`**
- Integrates FSM core, clock divider, threshold trigger, and FSM observer
- Implements voltage clamping for safety (max 3.0V intensity)
- MCC I/O mapping:
  - InputA: External trigger signal (16-bit signed)
  - InputB: Probe current monitor (16-bit signed)
  - OutputA: Trigger output to probe
  - OutputB: Debug voltage from FSM observer

**Utility Packages**
- `ds1120_pd_pkg.vhd`: Application-specific constants, types, and state definitions
- `volo_common_pkg.vhd`: Shared VoloApp infrastructure (VOLO_READY scheme, BRAM interface)
- `volo_voltage_pkg.vhd`: Voltage conversion utilities for oscilloscope visualization

**Support Components**
- `volo_clk_divider.vhd`: Programmable clock divider for FSM timing control
- `volo_voltage_threshold_trigger_core.vhd`: Voltage threshold crossing detection
- `fsm_observer.vhd`: Maps FSM states to oscilloscope-visible voltages for debugging
- `volo_bram_loader.vhd`: BRAM loading FSM (for future waveform storage)

### Control Register Interface

The shim layer maps these Control Registers to friendly signals:
- CR20: `armed` - Arms the probe driver
- CR21: `force_fire` - Manual trigger (bypasses threshold)
- CR22: `reset_fsm` - Resets state machine
- CR23: `timing_control[7:0]` - Clock divider [7:4] + delay upper [3:0]
- CR24: `delay_lower[7:0]` - Armed timeout (combines with CR23[3:0] for 12-bit value)
- CR25: `firing_duration[7:0]` - Cycles in FIRING state
- CR26: `cooling_duration[7:0]` - Cycles in COOLING state
- CR27-28: `trigger_threshold[15:0]` - Voltage threshold (default 2.4V)
- CR29-30: `intensity[15:0]` - Output intensity (clamped to 3.0V max)

VOLO_READY control bits (CR0[31:29]):
- Bit 31: `volo_ready` - Set by loader after deployment
- Bit 30: `user_enable` - User-controlled enable/disable
- Bit 29: `clk_enable` - Clock gating for sequential logic

Global enable requires ALL four conditions: `volo_ready AND user_enable AND clk_enable AND loader_done`

## Development Workflow

### Python Environment

The project uses Python (>= 3.9) with the Moku API:

```bash
# Install dependencies
pip install moku

# With development tools
pip install 'moku[dev]'
```

Dependencies managed via `pyproject.toml` using Ruff for linting/formatting.

### Linting and Formatting

```bash
# Run Ruff linter
ruff check .

# Run Ruff formatter
ruff format .

# Type checking (optional)
mypy .
```

Ruff config in `pyproject.toml`:
- Line length: 99
- Target: Python 3.9+
- Ignores E501 (line too long), E731 (lambda assignment), F841 (unused vars in examples)

### VHDL Development

**Important:** The shim layer (`DS1120_PD_volo_shim.vhd`) is auto-generated. When modifying register mappings:
1. Find or create the YAML application descriptor (not currently in repo)
2. Regenerate the shim using the generator tool (reference: line 4 of shim file)
3. Edit application logic in `DS1120_PD_volo_main.vhd` only

**Safety Constraints** (defined in `ds1120_pd_pkg.vhd`):
- Maximum intensity: 3.0V (`MAX_INTENSITY_3V0`)
- Maximum firing cycles: 32 (`MAX_FIRING_CYCLES`)
- Minimum cooling cycles: 8 (`MIN_COOLING_CYCLES`)
- Maximum arm timeout: 4095 cycles (12-bit)

**Voltage Scale:** 16-bit signed with ±5V full scale (resolution: ~305µV per bit)

### Testing with Moku Hardware

Examples in `moku-examples/` directory demonstrate Moku API usage. **Before running:**
1. Edit example files to set your Moku device IP address
2. Update any device-specific configuration (sample rates, channels, etc.)

Common example patterns:
- `*_basic.py` - Simple getting-started examples
- `*_plotting.py` - Data visualization examples
- `*_streaming.py` - Real-time data streaming
- `mim_*.py` - Multi-instrument mode examples

## File Organization

```
EZ-EMFI/
├── VHDL/                       # All VHDL source files
│   ├── DS1120_PD_volo_main.vhd    # Application logic (Layer 3)
│   ├── DS1120_PD_volo_shim.vhd    # Register mapping (Layer 2, GENERATED)
│   ├── ds1120_pd_fsm.vhd          # State machine core
│   ├── ds1120_pd_pkg.vhd          # Application constants/types
│   ├── volo_common_pkg.vhd        # Shared VoloApp infrastructure
│   ├── volo_voltage_pkg.vhd       # Voltage utilities
│   ├── volo_clk_divider.vhd       # Clock divider
│   ├── volo_voltage_threshold_trigger_core.vhd  # Threshold detection
│   ├── fsm_observer.vhd           # Debug visualization
│   └── volo_bram_loader.vhd       # BRAM loader FSM
├── moku-examples/              # Moku API examples (submodule)
├── pyproject.toml             # Python dependencies and Ruff config
└── README.md                  # (Currently minimal)
```

## Key Design Patterns

### Signal Naming Convention
- Control Registers: Raw hardware interface (`app_reg_20`, `app_reg_21`, ...)
- Friendly Signals: Application-meaningful names (`armed`, `force_fire`, `trigger_threshold`)
- Internal Signals: Suffixed with `_int`, `_reg`, `_next` for registers/state

### Reset Strategy
- Active-high `Reset` at top level
- Active-low `rst_n` in FSM core (historical convention)
- Reset forces FSM to safe state (all outputs = 0)

### Enable Hierarchy
Priority order: `Reset > ClkEn > Enable`
- `Reset = '1'`: Forces safe state unconditionally
- `Enable = '0'`: Disables functional operation
- `ClkEn = '0'`: Freezes sequential logic (clock gating)

### Safety Features
- Voltage clamping on intensity output (function: `clamp_voltage` in `ds1120_pd_pkg.vhd`)
- Automatic enforcement of timing limits (min cooling, max firing)
- Spurious trigger counting (triggers detected when not armed)
- Fire count limiting (prevents excessive use)
- Fault state (STATE_HARDFAULT = "111") for error conditions
