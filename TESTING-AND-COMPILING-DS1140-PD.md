# Testing and Compiling DS1140-PD

**Date**: 2025-10-28
**Project**: DS1140-PD EMFI Probe Driver
**Audience**: New users wanting to test and compile DS1140-PD

---

## Overview

This guide walks you through:
1. **Running CocotB simulation tests** (P1 and P2 test levels)
2. **Compiling VHDL with GHDL** (verification before CloudCompile)
3. **Understanding the test structure**
4. **Interpreting test results**

**Prerequisites:**
- Python 3.9+ with `uv` package manager
- GHDL 5.0+ (VHDL simulator)
- CocotB 2.0+ (installed via `uv`)

---

## Quick Start: Run Tests

### P1 Tests (Basic, 5 tests, <25 lines output)

**Default behavior** - runs quickly for rapid iteration:

```bash
cd /Users/vmars20/EZ-EMFI/tests
uv run python run.py ds1140_pd_volo
```

**Expected output:**
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Arm and trigger
  ✓ PASS
T3: Three outputs functioning
  ✓ PASS
T4: FSM observer on OutputC
  ✓ PASS
T5: VOLO_READY scheme
  ✓ PASS
ALL 5 TESTS PASSED
```

### P2 Tests (Intermediate, 10 tests total, comprehensive)

**Full validation** - includes all P1 tests plus 5 additional tests:

```bash
cd /Users/vmars20/EZ-EMFI/tests
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py ds1140_pd_volo
```

**Expected output:**
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Arm and trigger
  ✓ PASS
T3: Three outputs functioning
  ✓ PASS
T4: FSM observer on OutputC
  ✓ PASS
T5: VOLO_READY scheme
  ✓ PASS

P2 - INTERMEDIATE TESTS
T6: Timeout behavior
  ✓ PASS
T7: Full operational cycle
  ✓ PASS
T8: Clock divider integration
  ✓ PASS
T9: Intensity clamping on OutputB
  ✓ PASS
T10: Debug mux view switching
  ✓ PASS
ALL 10 TESTS PASSED
```

---

## Understanding the Test Structure

### Progressive Testing Philosophy

DS1140-PD uses **progressive testing** to preserve LLM context:

- **P1 (Basic)**: Essential validation, minimal output (<25 lines)
  - Runs by default
  - Fast execution (~1 second)
  - Catches major issues quickly

- **P2 (Intermediate)**: Comprehensive validation
  - Runs with `TEST_LEVEL=P2_INTERMEDIATE`
  - Longer execution (~2-3 seconds)
  - Full coverage of all features

### Test Categories

| Test | Level | What It Tests |
|------|-------|---------------|
| T1: Reset behavior | P1 | Module enters safe state on reset |
| T2: Arm and trigger | P1 | Basic FSM state transitions |
| T3: Three outputs functioning | P1 | OutputA, OutputB, OutputC all work |
| T4: FSM observer on OutputC | P1 | Debug voltage tracks FSM state |
| T5: VOLO_READY scheme | P1 | MCC enable control works |
| T6: Timeout behavior | P2 | Armed timeout detection |
| T7: Full operational cycle | P2 | Complete READY→ARMED→FIRING→COOLING→DONE |
| T8: Clock divider integration | P2 | FSM timing scales with divider |
| T9: Intensity clamping on OutputB | P2 | Safety clamping to 3.0V max |
| T10: Debug mux view switching | P2 | Debug multiplexer (if implemented) |

---

## Test File Structure

```
tests/
├── run.py                              # Main test runner
├── test_configs.py                     # Test configuration registry
├── conftest.py                         # Shared test utilities
├── test_base.py                        # Progressive test base class
│
├── ds1140_pd_tests/                    # DS1140-PD test module
│   ├── __init__.py
│   └── ds1140_pd_constants.py          # Test constants and error messages
│
└── test_ds1140_pd_progressive.py       # Main test implementation
```

### Key Test Files

**1. Test Configuration** (`test_configs.py`):
```python
"ds1140_pd_volo": {
    "toplevel": "ds1140_pd_volo_main",  # Entity name (lowercase)
    "sources": [
        # Packages
        "../VHDL/packages/volo_voltage_pkg.vhd",
        "../VHDL/packages/volo_common_pkg.vhd",
        "../VHDL/packages/ds1140_pd_pkg.vhd",

        # Building blocks
        "../VHDL/volo_clk_divider.vhd",
        "../VHDL/volo_voltage_threshold_trigger_core.vhd",
        "../VHDL/fsm_observer.vhd",
        "../VHDL/ds1120_pd_fsm.vhd",

        # DS1140-PD application
        "../VHDL/DS1140_PD_volo_main.vhd",
    ],
    "category": "ds1140_pd",
}
```

**2. Test Constants** (`ds1140_pd_tests/ds1140_pd_constants.py`):
```python
MODULE_NAME = "DS1140-PD"

class TestValues:
    DEFAULT_CLK_PERIOD_NS = 10  # 100 MHz
    P1_FIRING_DURATION = 4
    P1_COOLING_DURATION = 4
    P1_TRIGGER_VALUE = 0x4000  # Above 2.4V threshold
    # ...
```

---

## Running Tests with Verbosity Control

### Normal Output (Default)
```bash
uv run python run.py ds1140_pd_volo
```

### Verbose Output (Show all CocotB logs)
```bash
COCOTB_VERBOSITY=VERBOSE uv run python run.py ds1140_pd_volo
```

### Very Verbose (Debug level)
```bash
COCOTB_VERBOSITY=DEBUG uv run python run.py ds1140_pd_volo
```

---

## Compiling VHDL with GHDL

### Automated Compilation (Recommended)

**Use the build script** - GHDL automatically resolves dependencies:

```bash
cd /Users/vmars20/EZ-EMFI

# Import all VHDL sources (builds dependency graph)
python scripts/build_vhdl.py

# Build specific entity (GHDL compiles dependencies automatically)
python scripts/build_vhdl.py --entity ds1140_pd_volo_main

# Clean build artifacts
python scripts/build_vhdl.py --clean
```

**Features:**
- ✅ Auto-discovers all VHDL files in project
- ✅ GHDL resolves dependencies automatically (no manual ordering!)
- ✅ Skips testbenches and test wrappers
- ✅ Colored output with clear status messages

**Success output:**
```
🔍 Finding VHDL source files...
   Found 42 VHDL source files
   First few files:
     - VHDL/packages/volo_common_pkg.vhd
     - VHDL/packages/volo_voltage_pkg.vhd
     - VHDL/packages/ds1140_pd_pkg.vhd
     ... and 39 more
📦 Importing sources into GHDL work library...
✅ Import complete - GHDL has dependency information
✅ Dependency graph complete!
```

### Manual Compilation (Alternative)

If you prefer manual control, compile in this order:

```bash
cd /Users/vmars20/EZ-EMFI

# 1. Compile packages first (order matters!)
ghdl -a --std=08 --work=WORK VHDL/packages/volo_common_pkg.vhd
ghdl -a --std=08 --work=WORK VHDL/packages/volo_voltage_pkg.vhd
ghdl -a --std=08 --work=WORK VHDL/packages/ds1140_pd_pkg.vhd

# 2. Compile building blocks
ghdl -a --std=08 --work=WORK VHDL/fsm_observer.vhd
ghdl -a --std=08 --work=WORK VHDL/volo_clk_divider.vhd
ghdl -a --std=08 --work=WORK VHDL/volo_voltage_threshold_trigger_core.vhd
ghdl -a --std=08 --work=WORK VHDL/volo_bram_loader.vhd

# 3. Compile FSM core
ghdl -a --std=08 --work=WORK VHDL/packages/ds1120_pd_pkg.vhd
ghdl -a --std=08 --work=WORK VHDL/ds1120_pd_fsm.vhd

# 4. Compile DS1140-PD application layers
ghdl -a --std=08 --work=WORK VHDL/DS1140_PD_volo_main.vhd
ghdl -a --std=08 --work=WORK VHDL/DS1140_PD_volo_shim.vhd

# 5. Compile Top.vhd (Layer 1)
ghdl -a --std=08 --work=WORK VHDL/CustomWrapper_test_stub.vhd
ghdl -a --std=08 --work=WORK VHDL/Top.vhd
```

**Success:** No output means compilation succeeded!

**Error example:**
```
VHDL/DS1140_PD_volo_main.vhd:123:45:error: no declaration for "some_signal"
```

### Compilation Order Rules (Manual Mode Only)

**CRITICAL**: VHDL packages and dependencies must compile in order:

1. **Packages** (define types and functions)
   - `volo_common_pkg.vhd`
   - `volo_voltage_pkg.vhd`
   - `ds1140_pd_pkg.vhd`

2. **Building blocks** (use packages)
   - Clock divider, threshold trigger, fsm_observer, etc.

3. **Application** (uses building blocks)
   - FSM core → volo_main → volo_shim

4. **Top level** (uses application)
   - CustomWrapper stub → Top.vhd

**Note:** The automated script (`build_vhdl.py`) handles this automatically!

---

## Test Signal Names (Entity Ports)

DS1140-PD uses **simplified signal names** thanks to `counter_16bit` type:

### Register Signals (from YAML → VHDL entity)

```vhdl
-- Control registers (buttons)
arm_probe           : in  std_logic;                      -- CR20
force_fire          : in  std_logic;                      -- CR21
reset_fsm           : in  std_logic;                      -- CR22

-- Timing registers
clock_divider       : in  std_logic_vector(7 downto 0);   -- CR23
arm_timeout         : in  std_logic_vector(15 downto 0);  -- CR24 (16-bit direct!)
firing_duration     : in  std_logic_vector(7 downto 0);   -- CR25
cooling_duration    : in  std_logic_vector(7 downto 0);   -- CR26

-- Voltage registers (16-bit direct!)
trigger_threshold   : in  std_logic_vector(15 downto 0);  -- CR27
intensity           : in  std_logic_vector(15 downto 0);  -- CR28
```

**Key difference from DS1120-PD:**
- ❌ DS1120-PD: `trigger_thresh_high`, `trigger_thresh_low` (split 8-bit)
- ✅ DS1140-PD: `trigger_threshold` (direct 16-bit)

### MCC I/O Signals

```vhdl
-- Inputs (16-bit signed, ±5V scale)
InputA  : in  signed(15 downto 0);  -- External trigger signal
InputB  : in  signed(15 downto 0);  -- Probe current monitor

-- Outputs (16-bit signed, ±5V scale)
OutputA : out signed(15 downto 0);  -- Trigger to probe
OutputB : out signed(15 downto 0);  -- Intensity to probe
OutputC : out signed(15 downto 0);  -- FSM debug (NEW!)
```

---

## Common Test Patterns

### Setting Register Values in Tests

```python
# Setup method (runs before each test)
async def setup(self):
    await setup_clock(self.dut, period_ns=10, clk_signal="Clk")

    # Initialize all inputs
    self.dut.InputA.value = 0
    self.dut.InputB.value = 0
    self.dut.Enable.value = 1
    self.dut.ClkEn.value = 1
    self.dut.Reset.value = 0

    # Initialize friendly signals (16-bit direct!)
    self.dut.arm_probe.value = 0
    self.dut.force_fire.value = 0
    self.dut.reset_fsm.value = 0
    self.dut.clock_divider.value = 0
    self.dut.arm_timeout.value = 0xFF              # Direct 16-bit
    self.dut.firing_duration.value = 16
    self.dut.cooling_duration.value = 16
    self.dut.trigger_threshold.value = 0x3DCF      # Direct 16-bit (2.4V)
    self.dut.intensity.value = 0x2666              # Direct 16-bit (2.0V)
```

### Reading FSM Observer Voltage (OutputC)

```python
def read_fsm_voltage():
    """Convert OutputC raw value to voltage"""
    raw = int(self.dut.OutputC.value)

    # Handle signed 16-bit (two's complement)
    if raw > 32767:
        raw -= 65536

    # Convert to voltage (±5V scale)
    voltage = (raw / 32767.0) * 5.0
    return voltage

# Usage
voltage_ready = read_fsm_voltage()
assert -0.1 < voltage_ready < 0.1, f"READY state should be ~0.0V, got {voltage_ready:.3f}V"
```

### Triggering FSM State Transitions

```python
# Arm the FSM
self.dut.arm_probe.value = 1
await ClockCycles(self.dut.Clk, 2)
self.dut.arm_probe.value = 0
await ClockCycles(self.dut.Clk, 2)

# Apply trigger (above threshold)
self.dut.InputA.value = 0x4000  # ~2.5V (above 2.4V threshold)
await ClockCycles(self.dut.Clk, 10)

# Check FSM state changed
output_a = int(self.dut.OutputA.value)
assert output_a != 0, "OutputA should be active during FIRING"
```

---

## Troubleshooting

### Test Fails: "AttributeError: 'dut' object has no attribute 'signal_name'"

**Cause:** Signal name mismatch between test and VHDL entity

**Solution:** Check entity port names in `VHDL/DS1140_PD_volo_main.vhd`

Example:
```python
# ❌ Wrong (DS1120-PD style)
self.dut.armed.value = 1

# ✅ Correct (DS1140-PD style)
self.dut.arm_probe.value = 1
```

### GHDL Compilation Error: "entity not found"

**Cause:** Compilation order wrong or missing dependency

**Solution:** Compile packages first, then building blocks, then application

```bash
# Always compile in this order:
# 1. Packages
ghdl -a --std=08 --work=WORK VHDL/packages/*.vhd

# 2. Dependencies
ghdl -a --std=08 --work=WORK VHDL/volo_*.vhd

# 3. Application
ghdl -a --std=08 --work=WORK VHDL/DS1140_PD_*.vhd
```

### Test Timeout: "Simulation appears hung"

**Cause:** Clock not started or FSM stuck

**Solution:** Verify clock setup and Enable signals

```python
# Ensure clock is running
await setup_clock(self.dut, period_ns=10, clk_signal="Clk")

# Ensure Enable signals are high
self.dut.Enable.value = 1
self.dut.ClkEn.value = 1
```

### All Outputs Zero

**Cause:** VOLO_READY scheme not satisfied

**Solution:** Ensure Enable=1 and ClkEn=1 in test setup

```python
# VOLO_READY requires both Enable and ClkEn high
self.dut.Enable.value = 1
self.dut.ClkEn.value = 1
```

---

## Advanced: Running Specific Test Levels

### Run Only P1 Tests (Fast)
```bash
# Default behavior
uv run python run.py ds1140_pd_volo
```

### Run Only P2 Tests (Skip P1)
Not directly supported - P2 runs P1 first. Use grep to filter:

```bash
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py ds1140_pd_volo | grep "P2 -"
```

### Run All Tests in Category
```bash
# Run all ds1140_pd category tests
uv run python run.py --category ds1140_pd
```

### Run All Available Tests
```bash
# Run everything (volo_modules, ds1120_pd, ds1140_pd, etc.)
uv run python run.py --all
```

---

## Test Output Filtering

The test runner includes **GHDL output filtering** to reduce noise:

### Filter Levels

- **Aggressive**: Removes most GHDL messages (default)
- **Normal**: Removes common warnings
- **Minimal**: Only removes metavalue warnings
- **None**: Show all GHDL output

### Example Filtered Output
```
[Filtered 10 lines (10/58 = 17.2% reduction)]
```

This means 10 lines of GHDL metavalue warnings were removed.

---

## Performance Benchmarks

### DS1140-PD Test Performance (M1 Mac)

| Test Level | Tests | Sim Time | Real Time | Output Lines |
|------------|-------|----------|-----------|--------------|
| P1 (Basic) | 5 | 630 ns | 0.00s | ~25 |
| P2 (Full) | 10 | 3020 ns | 0.01s | ~50 |

**Ratio**: ~260,000 ns/s simulation speed

---

## Summary: Quick Command Reference

```bash
# Navigate to project
cd /Users/vmars20/EZ-EMFI

# Run P1 tests (fast, default)
cd tests && uv run python run.py ds1140_pd_volo

# Run P2 tests (comprehensive)
cd tests && TEST_LEVEL=P2_INTERMEDIATE uv run python run.py ds1140_pd_volo

# Run with verbose output
cd tests && COCOTB_VERBOSITY=VERBOSE uv run python run.py ds1140_pd_volo

# Compile VHDL automatically (RECOMMENDED)
python scripts/build_vhdl.py                           # Import all sources
python scripts/build_vhdl.py --entity ds1140_pd_volo_main  # Build specific entity
python scripts/build_vhdl.py --clean                   # Clean artifacts

# Compile VHDL manually (alternative, for manual control)
ghdl -a --std=08 --work=WORK VHDL/packages/*.vhd
ghdl -a --std=08 --work=WORK VHDL/fsm_observer.vhd
ghdl -a --std=08 --work=WORK VHDL/volo_*.vhd
ghdl -a --std=08 --work=WORK VHDL/DS1140_PD_*.vhd
ghdl -a --std=08 --work=WORK VHDL/Top.vhd

# Check test status
cd tests && uv run python run.py --list
```

---

## Next Steps After Testing

Once all tests pass:

1. **Build MCC package** (for CloudCompile deployment)
2. **Upload to CloudCompile** (synthesis to FPGA bitstream)
3. **Deploy to Moku:Go** (hardware testing on actual probe)

See `DS1140_PD_LAYER1_HANDOFF.md` for deployment instructions.

---

**Questions?** Check the main documentation:
- `DS1140_PD_PROJECT_SUMMARY.md` - Project overview
- `DS1140_PD_IMPLEMENTATION_GUIDE.md` - Complete implementation guide
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Progressive testing methodology
- `docs/COCOTB_PATTERNS.md` - CocotB best practices
