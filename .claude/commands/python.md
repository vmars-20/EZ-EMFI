# Python Tooling Context

You are now working in the **Python TUI and tooling domain**.

---

## Files In Scope

**Python Source:**
- `tools/` - TUI apps and command-line utilities
- `models/` - Data models and YAML parsers
- `scripts/` - Build and deployment scripts
- `shared/` - Shared Python utilities
- `pyproject.toml` - Dependencies and project config

**Configuration:**
- `*.yaml` - Application descriptors (DS1140_PD_app.yaml, etc.)
- `*.json` - Configuration files

**Documentation:**
- Python-specific docs (to be created)

---

## Files Out of Scope

**VHDL Development** (use `/vhdl` instead):
- `VHDL/**` - VHDL source files
- `tests/*_tb_wrapper.vhd` - VHDL test wrappers
- VHDL-specific documentation

**CocotB Tests** (use `/test` instead):
- `tests/test_*_progressive.py`
- `tests/*_tests/` (unless working on Python test infrastructure)

---

## Current Project: DS1140-PD TUI Control App

### Goal
Create a Python TUI (Text User Interface) application that:
1. Reads `DS1140_PD_app.yaml` for register definitions
2. Generates an interactive control interface
3. Communicates with Moku hardware via Moku API
4. Provides real-time control of DS1140-PD EMFI probe driver

### DS1140-PD Register Overview

**Configuration:** `DS1140_PD_app.yaml`

**7 Registers (CR20-CR28):**

**Control (CR20-CR22):**
- `Arm Probe` (button) - One-shot arm operation
- `Force Fire` (button) - Manual trigger
- `Reset FSM` (button) - Reset state machine

**Timing (CR23-CR26):**
- `Clock Divider` (8-bit) - FSM timing (0-15 for ÷1-÷16)
- `Arm Timeout` (16-bit) - Trigger wait timeout (0-4095 cycles)
- `Firing Duration` (8-bit) - FIRING state duration (max 32)
- `Cooling Duration` (8-bit) - COOLING state duration (min 8)

**Voltage (CR27-CR28):**
- `Trigger Threshold` (16-bit signed) - Voltage threshold (±5V)
- `Intensity` (16-bit signed) - Output intensity (clamped to 3.0V)

**Register bit packing:**
- `button`: CR[31] (single bit)
- `counter_8bit`: CR[31:24] (upper 8 bits)
- `counter_16bit`: CR[31:16] (upper 16 bits)

**Voltage scale:** 16-bit signed ±5V
- `0x0000` = 0.0V
- `0x3DCF` = 2.4V (15823 decimal)
- `0x4CCD` = 3.0V (19661 decimal, MAX_INTENSITY)
- `0x7FFF` = 5.0V (32767 decimal, full scale)
- Conversion: `voltage = (raw_value / 32767.0) * 5.0`

---

## Python Environment

### Setup (UV)

```bash
# Install dependencies
uv sync

# Run Python scripts
uv run python tools/<script>.py

# Run with specific Python version
uv run --python 3.9 python tools/<script>.py
```

### Dependencies (pyproject.toml)

**Core:**
- Python >= 3.9
- `moku` - Moku API for hardware communication

**Development:**
- `ruff` - Linting and formatting
- `mypy` - Type checking (optional)

**Linting/Formatting:**
```bash
# Run Ruff linter
ruff check .

# Run Ruff formatter
ruff format .

# Type checking (optional)
mypy .
```

**Ruff config:**
- Line length: 99
- Target: Python 3.9+
- Ignores: E501 (line too long), E731 (lambda), F841 (unused vars)

---

## TUI Framework Options

**Framework TBD - Options to consider:**

### Option 1: Textual (Recommended)
**Pros:**
- Modern, actively maintained
- Rich components (buttons, inputs, tables)
- Async/await support
- Great documentation
- CSS-like styling

**Cons:**
- Newer, less battle-tested
- Slightly larger dependency

**Example:**
```python
from textual.app import App
from textual.widgets import Header, Footer, Button

class DS1140_TUI(App):
    def compose(self):
        yield Header()
        yield Button("Arm Probe", id="arm")
        yield Button("Force Fire", id="fire")
        yield Footer()
```

### Option 2: Rich + Prompt Toolkit
**Pros:**
- Rich for display, Prompt Toolkit for input
- Very flexible
- Good performance

**Cons:**
- More manual work
- Two libraries to learn

### Option 3: Curses (Standard Library)
**Pros:**
- No dependencies
- Battle-tested

**Cons:**
- Low-level, more code
- Less user-friendly API

### Recommendation: Start with Textual
- Good balance of features and ease of use
- YAML → UI mapping should be straightforward
- Async support for Moku API calls

---

## Architecture Patterns

### YAML-Driven UI Pattern

**Goal:** Generate UI automatically from `DS1140_PD_app.yaml`

**Approach:**
```python
import yaml
from pathlib import Path

def load_app_config(yaml_path):
    """Load DS1140_PD_app.yaml"""
    with open(yaml_path) as f:
        return yaml.safe_load(f)

def generate_ui_from_config(config):
    """Generate TUI widgets from YAML registers"""
    widgets = []
    for reg in config['registers']:
        if reg['reg_type'] == 'button':
            widgets.append(create_button_widget(reg))
        elif reg['reg_type'] == 'counter_8bit':
            widgets.append(create_slider_widget(reg, bits=8))
        elif reg['reg_type'] == 'counter_16bit':
            widgets.append(create_input_widget(reg, bits=16))
    return widgets
```

### Moku API Integration Pattern

**Example:**
```python
from moku import MokuGo

def connect_to_device(ip_address):
    """Connect to Moku device"""
    moku = MokuGo(ip_address, force_connect=True)
    return moku

def set_register(moku, cr_number, value):
    """Set control register"""
    # Moku API call (exact method TBD)
    moku.set_custom_control(cr_number, value)

def get_status(moku):
    """Read status registers"""
    # Moku API call (exact method TBD)
    return moku.get_custom_status()
```

### Voltage Conversion Utilities

```python
def voltage_to_digital(voltage: float) -> int:
    """Convert voltage (-5V to +5V) to 16-bit signed"""
    if voltage < -5.0:
        voltage = -5.0
    if voltage > 5.0:
        voltage = 5.0
    return int((voltage / 5.0) * 32767)

def digital_to_voltage(raw_value: int) -> float:
    """Convert 16-bit signed to voltage"""
    return (raw_value / 32767.0) * 5.0
```

---

## Directory Structure (Proposed)

```
tools/
├── ds1140_tui/                # TUI application package
│   ├── __init__.py
│   ├── app.py                 # Main TUI application
│   ├── widgets.py             # Custom widgets
│   ├── moku_client.py         # Moku API wrapper
│   ├── config_loader.py       # YAML parsing
│   └── voltage_utils.py       # Voltage conversion
├── ds1140_tui_cli.py          # Command-line entry point
└── README.md                  # TUI usage guide

models/
├── volo/                      # Existing Volo models
│   ├── app_register.py        # Register type definitions
│   └── volo_app.py            # VHDL generator (if needed)
└── ds1140/                    # DS1140-specific models (if needed)

scripts/
├── build_mcc_package.py       # MCC package builder
└── deploy_to_moku.py          # Deployment script
```

---

## Development Workflow

### Step 1: YAML Parsing
1. Load `DS1140_PD_app.yaml`
2. Parse register definitions
3. Validate structure

### Step 2: UI Generation
1. Choose TUI framework (Textual recommended)
2. Generate widgets from register config
3. Handle different register types (button, counter_8bit, counter_16bit)

### Step 3: Moku Integration
1. Connect to Moku device (IP address)
2. Map UI controls to register writes
3. Poll status registers for feedback

### Step 4: Testing
1. Test UI rendering without hardware
2. Test with Moku simulator (if available)
3. Test with real hardware

---

## Code Style Guidelines

**Follow existing patterns:**
- Type hints for function signatures
- Docstrings for public functions
- Ruff-compliant formatting
- Line length ≤ 99 characters

**Example:**
```python
def set_arm_timeout(moku: MokuGo, timeout_cycles: int) -> None:
    """Set arm timeout in cycles (0-4095).

    Args:
        moku: Connected Moku device
        timeout_cycles: Timeout in cycles (0-4095)

    Raises:
        ValueError: If timeout_cycles out of range
    """
    if not 0 <= timeout_cycles <= 4095:
        raise ValueError(f"Timeout must be 0-4095, got {timeout_cycles}")

    # Pack into upper 16 bits of CR24
    cr24_value = (timeout_cycles & 0xFFFF) << 16
    moku.set_custom_control(24, cr24_value)
```

---

## Testing Strategy

**Unit Tests:**
- YAML parsing
- Voltage conversion utilities
- Register value packing/unpacking

**Integration Tests:**
- UI rendering (mock hardware)
- Moku API calls (use simulator or mock)

**Manual Testing:**
- Full workflow with real Moku device
- Edge cases (min/max values, invalid inputs)

---

## Next Steps (Suggested)

1. **Choose TUI framework** - Recommend Textual
2. **Create basic app structure** - `tools/ds1140_tui/`
3. **Implement YAML parser** - Load register definitions
4. **Generate simple UI** - One widget per register
5. **Add Moku client stub** - Mock API for testing
6. **Test UI without hardware** - Validate layout
7. **Integrate real Moku API** - Connect to device
8. **Add voltage conversion UI** - Helper for threshold/intensity
9. **Add status display** - Show FSM state, errors
10. **Document and polish** - README, help text

---

## Reference Documentation

**YAML Schema:**
- `DS1140_PD_app.yaml` - Complete register definitions
- `DS1120_PD_app.yaml` - Legacy 11-register design (for comparison)

**Moku API:**
- Moku Python API docs (https://apis.liquidinstruments.com/)
- Check `moku-examples/` in external repo (if accessible)

**Python Standards:**
- `pyproject.toml` - Ruff config and dependencies

---

## Common Pitfalls

1. **Don't mix VHDL and Python concerns** - TUI is pure Python
2. **Don't hardcode register numbers** - Use YAML definitions
3. **Don't forget voltage conversion** - User sees volts, hardware sees raw values
4. **Don't skip validation** - Check ranges before sending to hardware
5. **Don't block UI with API calls** - Use async for Moku communication

---

## Success Checklist

Before committing Python code:
- [ ] Ruff linting passes (`ruff check .`)
- [ ] Formatted with Ruff (`ruff format .`)
- [ ] Type hints for public functions
- [ ] Docstrings for public APIs
- [ ] YAML parsing tested
- [ ] Voltage conversion verified
- [ ] Works without hardware (mock mode)
- [ ] README updated with usage instructions

---

**Current Status:** Planning stage - framework selection needed

**Next Decision:** Choose TUI framework (recommend Textual)

---

Now working in Python context. Use `/vhdl` to switch to VHDL development, or `/test` for testing infrastructure.
