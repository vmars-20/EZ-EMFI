# Testing Infrastructure Context

You are now working in the **testing and validation domain**.

---

## Files In Scope

**CocotB Tests:**
- `tests/test_*_progressive.py` - Progressive test files
- `tests/*_tests/` - Test infrastructure directories
- `tests/*_constants.py` - Test constants
- `tests/*_tb_wrapper.vhd` - VHDL test wrappers

**Test Infrastructure:**
- `tests/conftest.py` - Shared utilities and fixtures
- `tests/test_base.py` - Base test class
- `tests/test_configs.py` - Test configuration
- `tests/run.py` - Test runner

**Documentation:**
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - ⚠️ **CRITICAL READING**
- `tests/README.md` - Testing framework guide

---

## Files Out of Scope

**VHDL Source** (use `/vhdl` for implementation):
- `VHDL/**/*.vhd` (except test wrappers)

**Python Tools** (use `/python` for TUI development):
- `tools/` - TUI apps
- `models/` - Data models
- `scripts/` - Build scripts

---

## ⚠️ CRITICAL: Read This First

**Before writing or debugging ANY test:**

```bash
cat docs/VHDL_COCOTB_LESSONS_LEARNED.md
```

This document contains **hard-won knowledge** that will save you hours of debugging.

**Top 5 Lessons:**
1. **Function overloading with subtypes** - VHDL doesn't support it (use base types)
2. **Hex literal type inference** - Use `x"HHHH"` not `16#HHHH#`
3. **Python/VHDL arithmetic rounding** - Match VHDL's integer division exactly
4. **Signal persistence between tests** - Reset control signals before each test
5. **LUT generation** - Use Python scripts, not manual typing

---

## Progressive Testing Philosophy

### Test Levels

**P1 - Basic (Default):**
- **Goal:** Fast validation, minimal output
- **Criteria:** 2-4 essential tests, <20 lines output, <5s runtime
- **Purpose:** Smoke test during development
- **Run:** `uv run python tests/run.py <module>`

**P2 - Intermediate:**
- **Goal:** Full coverage
- **Criteria:** All edge cases, error conditions, boundary testing
- **Purpose:** Pre-commit validation
- **Run:** `TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module>`

**P3+ - Comprehensive (Future):**
- **Goal:** Exhaustive testing
- **Criteria:** Stress testing, random stimulus, long-running tests
- **Purpose:** CI/CD, release validation

### Why Progressive Testing?

**For LLMs (Claude Code):**
- Keeps output token count low
- Faster iteration during development
- Clear pass/fail signals

**For Humans:**
- Quick feedback loop
- Comprehensive validation when needed
- Scalable to CI/CD

---

## Test Runner

### Basic Usage

```bash
# Run P1 tests (default)
uv run python tests/run.py volo_clk_divider

# Run P2 tests (comprehensive)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider

# Run specific category
uv run python tests/run.py --category volo_modules
uv run python tests/run.py --category ds1120_pd

# Run all tests
uv run python tests/run.py --all

# With verbosity control
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py <module>
COCOTB_VERBOSITY=VERBOSE uv run python tests/run.py <module>
```

### Available Test Modules

**Volo Utilities:**
- `volo_clk_divider` - Programmable clock divider (P1/P2)
- `volo_voltage_pkg` - Voltage conversion utilities (P1)
- `volo_lut_pkg` - Percentage-indexed LUTs (P1/P2)

**DS1120/DS1140 Probe Drivers:**
- `ds1120_pd_volo` - Complete DS1120-PD application (P1/P2)
- `ds1140_pd_volo` - Refactored DS1140-PD (P1/P2)

---

## Test Structure Pattern

### Directory Layout

```
tests/
├── run.py                           # Test runner
├── test_configs.py                  # Test configuration
├── conftest.py                      # Shared utilities
├── test_base.py                     # Base test class
│
├── test_<module>_progressive.py    # Progressive test file
│
└── <module>_tests/                  # Test infrastructure
    ├── __init__.py
    └── <module>_constants.py        # Test values, error messages
```

### Progressive Test File Template

```python
"""
P1 - Basic Tests for <Module>

MINIMAL output, FAST execution, ESSENTIAL validation only.
Target: 2-4 tests, <100ms runtime, <50 tokens output.
"""

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from test_base import TestBase
from conftest import setup_clock, reset_active_low, run_with_timeout
from <module>_tests.<module>_constants import *

# Test level from environment
TEST_LEVEL = os.getenv("TEST_LEVEL", "P1_BASIC")

class <Module>Tests(TestBase):
    """Progressive test suite for <Module>."""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def test_reset(self):
        """T1: Reset behavior."""
        await setup_clock(self.dut)
        await reset_active_low(self.dut)
        assert self.dut.output.value == 0, "Output should be 0 after reset"

    async def test_basic_operation(self):
        """T2: Basic operation."""
        await setup_clock(self.dut)
        await reset_active_low(self.dut)
        # Test logic here

    async def run_p1_basic(self):
        """Run P1 basic tests."""
        await self.test("T1: Reset", self.test_reset)
        await self.test("T2: Basic operation", self.test_basic_operation)

    async def run_p2_intermediate(self):
        """Run P2 intermediate tests (includes P1)."""
        await self.run_p1_basic()
        # Additional P2 tests here

@cocotb.test()
async def test_<module>_progressive(dut):
    """Entry point - CocotB discovers this."""
    async def test_logic():
        tester = <Module>Tests(dut)

        if TEST_LEVEL == "P1_BASIC":
            await tester.run_p1_basic()
        elif TEST_LEVEL == "P2_INTERMEDIATE":
            await tester.run_p2_intermediate()

        tester.print_summary()

    await run_with_timeout(test_logic(), timeout_sec=30, test_name="<Module>")
```

### Constants File Pattern

```python
"""
Test Constants for <Module>

Single source of truth for test configuration.
"""

from pathlib import Path

# Module identification
MODULE_NAME = "<module>"
MODULE_PATH = Path("../VHDL")

# HDL configuration
HDL_SOURCES = [
    MODULE_PATH / "<module>.vhd",
]
HDL_TOPLEVEL = "<module>_tb_wrapper"

# Test values
EXPECTED_RESET_VALUE = 0x0000
EXPECTED_MAX_VALUE = 0xFFFF

# Error messages
ERROR_RESET_FAILED = "Reset did not clear output"
ERROR_ENABLE_FAILED = "Enable did not activate module"
```

---

## Shared Test Utilities (conftest.py)

### Clock and Reset

```python
await setup_clock(dut, clk_signal="clk", clk_period_ns=10)
await reset_active_high(dut, rst_signal="reset")
await reset_active_low(dut, rst_signal="rst_n")
```

### Timeouts

```python
await run_with_timeout(test_logic(), timeout_sec=5, test_name="MyTest")
```

### Signal Helpers

```python
# Count pulses on a signal
count = await count_pulses(dut.output, num_cycles=100, clk=dut.clk)

# Wait for condition
await wait_for_value(dut.ready, expected=1, timeout_cycles=100, clk=dut.clk)
```

### MCC Test Primitives

```python
# Initialize MCC inputs
await init_mcc_inputs(dut)

# Set MCC registers
await mcc_set_regs(dut, {
    0: 0xE0000000,  # Control0 with MCC_READY
    1: 0x12345678,
}, set_mcc_ready=True)

# Helper for Control0
cr0_value = mcc_cr0(divider=240)  # Returns 0xEEF00000
```

---

## Common Test Patterns

### Testing FSM State Transitions

```python
# Start in IDLE
assert dut.state.value == STATE_IDLE

# Trigger transition
dut.start.value = 1
await ClockCycles(dut.clk, 1)
dut.start.value = 0

# Verify new state
await ClockCycles(dut.clk, 2)
assert dut.state.value == STATE_ACTIVE
```

### Testing Voltage Conversion

```python
from conftest import voltage_to_digital_approx, digital_to_voltage_approx

# Test conversion
voltage_in = 2.4
digital = voltage_to_digital_approx(voltage_in)
dut.voltage_input.value = digital

await ClockCycles(dut.clk, 2)

# Verify output
output_voltage = digital_to_voltage_approx(int(dut.voltage_output.value.signed))
assert abs(output_voltage - expected_voltage) < 0.1  # Within tolerance
```

### Testing Timeout Behavior

```python
# Set short timeout
dut.timeout.value = 10

# Start operation
dut.start.value = 1
await ClockCycles(dut.clk, 1)
dut.start.value = 0

# Wait for timeout
for i in range(20):
    await RisingEdge(dut.clk)
    if dut.timeout_flag.value == 1:
        break

assert dut.timeout_flag.value == 1, "Timeout not detected"
```

---

## Test Wrapper Pattern

### Purpose
- Instantiate package functions for testing
- Register outputs for timing stability
- Provide one-hot function selection

### Template

```vhdl
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

use work.<module>_pkg.all;

entity <module>_tb_wrapper is
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        -- Function selects (one-hot)
        sel_func_a : in  std_logic;
        sel_func_b : in  std_logic;

        -- Inputs
        input_data : in  std_logic_vector(15 downto 0);

        -- Outputs
        output_a   : out std_logic_vector(15 downto 0);
        output_b   : out std_logic_vector(15 downto 0)
    );
end entity;

architecture rtl of <module>_tb_wrapper is
begin
    process(clk, reset)
    begin
        if reset = '1' then
            output_a <= (others => '0');
            output_b <= (others => '0');
        elsif rising_edge(clk) then
            if sel_func_a = '1' then
                output_a <= package_func_a(input_data);
            end if

            if sel_func_b = '1' then
                output_b <= package_func_b(input_data);
            end if;
        end if;
    end process;
end architecture;
```

---

## Debugging Tests

### Enable Verbose Output

```bash
COCOTB_VERBOSITY=DEBUG uv run python tests/run.py <module>
```

### Check GHDL Compilation

```bash
cd tests/sim_build/<module>
ghdl -a --std=08 ../../VHDL/<module>.vhd
```

### View Waveforms

```bash
# If GTKWave is installed
gtkwave tests/sim_build/<module>/<module>.vcd
```

### Common Debug Steps

1. **Test fails immediately** → Check VHDL compilation errors
2. **Wrong output value** → Check Python/VHDL arithmetic (see lessons learned)
3. **Timeout** → Check clock setup, increase timeout
4. **Stale values** → Reset control signals between tests
5. **Import errors** → Check `sys.path.append()` and module names

---

## GHDL Compatibility Notes

**Entity Names:**
- GHDL lowercases entity names
- Use lowercase in `test_configs.py`: `HDL_TOPLEVEL = "my_module_tb_wrapper"`

**VHDL-2008:**
- Always use `--std=08` flag
- Required for many VHDL-2008 features

**Simulation Artifacts:**
- Saved to `tests/sim_build/` (ignored by git)
- Clean with: `make clean` or `rm -rf sim_build/`

---

## Performance Guidelines

### P1 Test Performance Targets

- **Runtime:** <5 seconds
- **Output:** <20 lines
- **Simulation time:** <1000ns
- **Test count:** 2-4 tests

### Optimization Tips

1. Minimize clock cycles per test
2. Use combinational logic where possible
3. Batch similar tests together
4. Use `COCOTB_VERBOSITY=SILENT` for benchmarking

---

## Success Checklist

Before committing test code:
- [ ] Read `docs/VHDL_COCOTB_LESSONS_LEARNED.md`
- [ ] P1 tests run in <5s with <20 lines output
- [ ] All deprecation warnings fixed
- [ ] Test constants in separate file
- [ ] Error messages are descriptive
- [ ] Test wrapper uses registered outputs
- [ ] Reset signals cleared between tests
- [ ] Expected values match VHDL arithmetic
- [ ] GHDL compiles without warnings

---

## Reference Examples

**Best Practices:**
- `tests/test_volo_clk_divider_progressive.py` - Clean P1/P2 structure
- `tests/test_volo_lut_pkg_progressive.py` - Package testing
- `tests/volo_lut_pkg_tb_wrapper.vhd` - Minimal wrapper

**Shared Utilities:**
- `tests/conftest.py` - All helper functions
- `tests/test_base.py` - Base class for verbosity control

---

**Documentation:**
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - CRITICAL READING
- `tests/README.md` - Framework guide

---

Now working in testing context. Use `/vhdl` for VHDL development, or `/python` for Python tooling.
