# VHDL Development Context

You are now working in the **VHDL/EMFI probe driver domain**.

---

## Files In Scope

**VHDL Source:**
- `VHDL/**/*.vhd` - All VHDL source files
- `VHDL/packages/*.vhd` - Shared packages (volo_*, ds1120_pd_*)

**Tests:**
- `tests/test_*_progressive.py` - CocotB progressive tests
- `tests/*_tests/` - Test infrastructure
- `tests/*_tb_wrapper.vhd` - VHDL test wrappers

**Documentation:**
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` ⚠️ **READ THIS FIRST**
- `docs/volo_lut_pkg_migration/` - LUT package docs
- `docs/FSM_OBSERVER_PATTERN.md` - FSM debugging pattern
- `docs/CLAUDE_FULL_BACKUP.md` - Complete VHDL reference

---

## Files Out of Scope

**Python Tooling** (use `/python` instead):
- `tools/` - TUI apps and utilities
- `models/` - YAML parsers
- `scripts/` - Build scripts

---

## Quick Reference

### 3-Layer VoloApp Architecture

**Layer 1: MCC_TOP_volo_loader.vhd** (provided by Moku platform)
- Bitstream loading and BRAM initialization
- Control Register (CR0-CR30) interface

**Layer 2: *_volo_shim.vhd** (AUTO-GENERATED - DO NOT EDIT)
- Maps Control Registers to friendly signal names
- Example: `DS1120_PD_volo_shim.vhd`

**Layer 3: *_volo_main.vhd** (APPLICATION LOGIC - EDIT THIS)
- MCC-agnostic interface
- Contains FSM, business logic
- Example: `DS1120_PD_volo_main.vhd`

### Core Components

**Probe Drivers:**
- `ds1120_pd_fsm.vhd` - 7-state FSM (READY → ARMED → FIRING → COOLING → DONE)
- `ds1120_pd_pkg.vhd` - Safety constants, types, utilities
- `DS1120_PD_volo_main.vhd` - DS1120-PD application (11 registers)
- `DS1140_PD_volo_main.vhd` - DS1140-PD refactored version (7 registers)

**Utility Packages:**
- `volo_common_pkg.vhd` - VOLO_READY scheme, BRAM interface
- `volo_voltage_pkg.vhd` - Voltage conversion (±5V ↔ 16-bit signed)
- `volo_lut_pkg.vhd` - Percentage-indexed lookup tables (0-100)

**Support Components:**
- `volo_clk_divider.vhd` - Programmable clock divider
- `volo_voltage_threshold_trigger_core.vhd` - Threshold crossing detection
- `fsm_observer.vhd` - FSM state → voltage (oscilloscope debug)
- `volo_bram_loader.vhd` - BRAM loading FSM

### Safety Features

Defined in `ds1120_pd_pkg.vhd`:
- **MAX_INTENSITY_3V0**: Maximum output intensity (3.0V)
- **MAX_FIRING_CYCLES**: 32 cycles max in FIRING state
- **MIN_COOLING_CYCLES**: 8 cycles min in COOLING state
- **MAX_ARM_TIMEOUT**: 4095 cycles (12-bit)

Voltage scale: 16-bit signed ±5V (resolution ~305µV/bit)

---

## CocotB Testing

### ⚠️ CRITICAL: Read This First

**Before writing or debugging tests:**
```bash
cat docs/VHDL_COCOTB_LESSONS_LEARNED.md
```

**Top 5 pitfalls:**
1. Subtype overloading doesn't work (use base types)
2. Hex literals need `x""` notation (not `16##`)
3. Python/VHDL arithmetic rounding mismatches
4. Signal persistence between tests (reset selects!)
5. LUT generation (use Python scripts, not manual typing)

### Progressive Test Structure

**P1 (Basic):** 2-4 tests, <20 lines output, <5s runtime
**P2 (Intermediate):** Full coverage, all edge cases
**P3+ (Future):** Exhaustive/stress tests

### Running Tests

```bash
# Quick P1 validation (default)
uv run python tests/run.py <module_name>

# Full P2 validation
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module_name>

# With verbosity
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py <module_name>

# Run all tests
uv run python tests/run.py --all
```

### Available Test Modules

- `volo_clk_divider` - Programmable clock divider (P1/P2)
- `volo_voltage_pkg` - Voltage conversion utilities (P1)
- `volo_lut_pkg` - Percentage-indexed LUTs (P1/P2)
- `ds1120_pd_volo` - DS1120-PD application (P1/P2)

### Test Structure Pattern

```
tests/
├── <module>_tests/
│   ├── __init__.py
│   └── <module>_constants.py     # Test values, error messages
└── test_<module>_progressive.py  # Progressive test implementation
```

### Test Principles

1. Keep P1 tests minimal (<20 lines output)
2. Use constants file for test values and error messages
3. Inherit from TestBase for verbosity control
4. Tests Layer 3 (application logic) directly with friendly signals
5. Reference: `tests/test_volo_clk_divider_progressive.py`

---

## Control Register Interface

### VOLO_READY Scheme

Global enable requires ALL four conditions:
```vhdl
global_enable <= volo_ready AND user_enable AND clk_enable AND loader_done;
```

**Control bits (CR0[31:29]):**
- Bit 31: `volo_ready` - Set by loader after deployment
- Bit 30: `user_enable` - User-controlled enable/disable
- Bit 29: `clk_enable` - Clock gating for sequential logic

### Enable Hierarchy (Priority Order)

1. **Reset** - Forces safe state unconditionally
2. **ClkEn** - Freezes sequential logic (clock gating)
3. **Enable** - Disables functional operation

```vhdl
if Reset = '1' then
    -- Force safe state
elsif rising_edge(Clk) then
    if ClkEn = '1' then
        if Enable = '1' then
            -- Normal operation
        end if
    end if
end if;
```

---

## FSM Observer Pattern

**Purpose:** Non-invasive FSM debugging via oscilloscope

**Features:**
- Fixed 6-bit interface (works with all FSMs)
- Sign-flip fault detection (negative voltages)
- Zero overhead (LUT calculated at elaboration)
- 20-test validation

**Quick Integration:**
```vhdl
use WORK.volo_voltage_pkg.all;

-- Pad state vector to 6-bit
signal state_6bit : std_logic_vector(5 downto 0);
state_6bit <= "000" & fsm_state;

-- Instantiate observer
U_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 8,
        V_MIN => 0.0,
        V_MAX => 2.5,
        FAULT_STATE_THRESHOLD => 7,
        STATE_0_NAME => "IDLE",
        STATE_1_NAME => "ARMED"
        -- ... (continue for all states)
    )
    port map (
        clk          => Clk,
        reset        => Reset,
        state_vector => state_6bit,
        voltage_out  => voltage_debug_out
    );
```

**Detailed guide:** `docs/FSM_OBSERVER_PATTERN.md`

---

## Common Patterns

### Voltage Clamping

```vhdl
use work.ds1120_pd_pkg.all;

intensity_clamped <= clamp_voltage(intensity_raw, MAX_INTENSITY_3V0);
```

### Signal Naming

- `ctrl_*` - Control signals (enable, reset)
- `cfg_*` - Configuration parameters
- `stat_*` - Status and monitoring signals

### Status Register

- **Bit 7**: FAULT (sticky, cleared only on reset)
- **Bit 6**: ALARM (sticky, cleared only on reset)
- Update: Synchronous on rising edge
- Reset: All bits cleared

---

## File Organization

```
VHDL/
├── DS1120_PD_volo_main.vhd    # Layer 3 (application logic)
├── DS1120_PD_volo_shim.vhd    # Layer 2 (GENERATED)
├── DS1140_PD_volo_main.vhd    # Layer 3 (refactored)
├── DS1140_PD_volo_shim.vhd    # Layer 2 (GENERATED)
├── ds1120_pd_fsm.vhd          # State machine core
├── ds1120_pd_pkg.vhd          # Application constants/types
├── volo_common_pkg.vhd        # Shared VoloApp infrastructure
├── volo_voltage_pkg.vhd       # Voltage utilities
├── volo_clk_divider.vhd       # Clock divider
├── volo_voltage_threshold_trigger_core.vhd
├── fsm_observer.vhd
├── volo_bram_loader.vhd
└── packages/
    └── volo_lut_pkg.vhd       # LUT infrastructure
```

---

## Development Workflow

### VHDL Development

1. **Check auto-generated files** - Don't edit shim layers
2. **Edit application logic** - Only edit `*_volo_main.vhd`
3. **Follow safety constraints** - Use constants from `*_pkg.vhd`
4. **Test early** - Run CocotB tests frequently

### When Modifying Register Mappings

1. Find/create YAML application descriptor
2. Regenerate shim using generator tool
3. Edit application logic in `*_volo_main.vhd` only

### GHDL Compatibility

- Entity names lowercased by GHDL (use lowercase in `test_configs.py`)
- Tests require `uv` for Python environment
- Simulation artifacts: `tests/sim_build/` (ignored by git)

---

## Quick Troubleshooting

**Test failing?** Check lessons learned first (docs/VHDL_COCOTB_LESSONS_LEARNED.md)

**Subtype error?** Use base types (natural, not pct_index_t)

**Hex literal error?** Use `x"HHHH"` not `16#HHHH#`

**Test expects X, got X+1?** Python/VHDL rounding mismatch (see lessons learned)

**Output stale?** Reset control signals between tests

**GHDL build fails?** Check compilation order (packages → core → top)

---

## Success Checklist

Before committing VHDL code:
- [ ] No subtype overloading (use base types)
- [ ] All hex literals use `x""` notation
- [ ] Test expected values match VHDL arithmetic
- [ ] Signal selects reset between tests
- [ ] P1 tests run in <5s with <20 lines output
- [ ] GHDL compiles with `--std=08` without warnings
- [ ] Safety constraints enforced (intensity, timing)

---

**Reference Examples:**
- `tests/test_volo_clk_divider_progressive.py` - Clean P1/P2 structure
- `tests/test_volo_lut_pkg_progressive.py` - Package testing pattern
- `tests/volo_lut_pkg_tb_wrapper.vhd` - Minimal wrapper design

**Full Documentation:** `docs/CLAUDE_FULL_BACKUP.md` (306 lines)

---

Now working in VHDL context. Use `/python` to switch to Python tooling, or `/test` for testing infrastructure.
