# Progressive Testing Guide for EZ-EMFI

**How to convert existing CocotB tests to LLM-optimized progressive structure**

## Table of Contents
- [Overview](#overview)
- [Why Progressive Testing?](#why-progressive-testing)
- [Quick Start](#quick-start)
- [Step-by-Step Conversion](#step-by-step-conversion)
- [Code Templates](#code-templates)
- [Examples](#examples)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

Progressive testing splits test suites into levels:
- **P1 (Basic)**: 2-4 essential tests, <20 lines output, runs by default
- **P2 (Intermediate)**: Full test coverage, runs when `TEST_LEVEL=P2_INTERMEDIATE`
- **P3 (Comprehensive)**: Edge cases and stress tests (future)
- **P4 (Exhaustive)**: Debug and random testing (future)

**Goal:** Preserve LLM context by minimizing test output while maintaining thorough validation.

---

## Why Progressive Testing?

### Before (Monolithic)
```bash
$ uv run python tests/run.py volo_clk_divider
# Output: 250+ lines of logs, warnings, debug info
# LLM context consumed: ~4000 tokens
```

### After (Progressive)
```bash
$ uv run python tests/run.py volo_clk_divider
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Divide by 2
  ✓ PASS
T3: Enable control
  ✓ PASS
ALL 3 TESTS PASSED

# Output: 8 lines
# LLM context consumed: ~50 tokens (98% reduction!)
```

**When you need more detail:**
```bash
$ TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider
# Runs all 7 tests (P1 + P2)
```

---

## Quick Start

**Converting a module in 5 steps:**

1. Create test directory: `tests/<module>_tests/`
2. Create constants file
3. Create progressive test file
4. Update `test_configs.py`
5. Test and commit!

**Time:** ~30-45 minutes per module

---

## Step-by-Step Conversion

### Step 1: Create Test Directory

```bash
mkdir tests/<module_name>_tests
```

Example: `tests/volo_clk_divider_tests/`

### Step 2: Create Constants File

**File:** `tests/<module_name>_tests/<module_name>_constants.py`

**Template:**

```python
"""
<Module Name> Test Constants

Author: EZ-EMFI Team
Date: YYYY-MM-DD
"""

from pathlib import Path

# Module identification
MODULE_NAME = "<module_name>"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"

HDL_SOURCES = [
    VHDL_DIR / "<module_name>.vhd",
    # Add dependencies here
]

HDL_TOPLEVEL = "<entity_name>"

# Test parameters
DEFAULT_CLK_PERIOD_NS = 10

# Test value sets for different phases
class TestValues:
    """Test value sets for different test phases"""

    # P1 - Keep small for speed!
    P1_TEST_CYCLES = 20
    P1_DIV_VALUES = [2]

    # P2 - Realistic values
    P2_TEST_CYCLES = 100
    P2_DIV_VALUES = [1, 10, 255]

# Error messages
class ErrorMessages:
    """Standardized error messages"""
    RESET_FAILED = "Reset should set output to {}, got {}"
    COUNT_MISMATCH = "Expected count {}, got {}"
```

**Key Points:**
- Keep P1 values SMALL (fast tests)
- Use classes to organize constants
- Standardize error messages

### Step 3: Create Progressive Test File

**File:** `tests/test_<module_name>_progressive.py`

**Template:**

```python
"""
Progressive CocotB Test for <module_name>

P1 (Basic): Reset, basic operation, enable control
P2 (Intermediate): Edge cases, boundaries, special modes

Author: EZ-EMFI Team
Date: YYYY-MM-DD
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_low
from test_base import TestBase, VerbosityLevel
from <module_name>_tests.<module_name>_constants import *


class <ModuleName>Tests(TestBase):
    """Progressive tests for <module_name>"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut)
        self.dut.enable.value = 1
        # Add module-specific setup

    # ====================================================================
    # P1 - Basic Tests (REQUIRED - runs by default)
    # ====================================================================

    async def run_p1_basic(self):
        """P1 - Essential validation (2-4 tests)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("Basic operation", self.test_basic)
        # Add 1-2 more essential tests

    async def test_reset(self):
        """Test reset puts module in known state"""
        await reset_active_low(self.dut)

        # Verify reset state
        output = int(self.dut.output.value)
        assert output == 0, ErrorMessages.RESET_FAILED.format(0, output)

        self.log("Reset verified", VerbosityLevel.VERBOSE)

    async def test_basic(self):
        """Test basic functionality"""
        await reset_active_low(self.dut)

        # Your test logic here

        self.log("Basic operation verified", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P2 - Intermediate Tests (runs when TEST_LEVEL=P2_INTERMEDIATE)
    # ====================================================================

    async def run_p2_intermediate(self):
        """P2 - Comprehensive validation"""
        await self.setup()

        await self.test("Edge case 1", self.test_edge_case_1)
        await self.test("Edge case 2", self.test_edge_case_2)
        # Add more comprehensive tests

    async def test_edge_case_1(self):
        """Test edge case or boundary condition"""
        await reset_active_low(self.dut)

        # Your test logic

        self.log("Edge case verified", VerbosityLevel.VERBOSE)


# CocotB entry point
@cocotb.test()
async def test_<module_name>(dut):
    """Progressive <module_name> tests"""
    tester = <ModuleName>Tests(dut)
    await tester.run_all_tests()
```

**Key Points:**
- Inherit from `TestBase` for automatic verbosity control
- Use `self.log()` with `VerbosityLevel.VERBOSE` for optional debug output
- Keep P1 to 2-4 ESSENTIAL tests
- P2 adds comprehensive coverage

### Step 4: Create `__init__.py`

**File:** `tests/<module_name>_tests/__init__.py`

```python
"""
<Module Name> Progressive Test Suite

Author: EZ-EMFI Team
Date: YYYY-MM-DD
"""

__all__ = ["<module_name>_constants"]
```

### Step 5: Update `test_configs.py`

**Edit:** `tests/test_configs.py`

```python
"<module_name>": TestConfig(
    name="<module_name>",
    sources=[
        VHDL / "<module_name>.vhd",
        # Add dependencies
    ],
    toplevel="<entity_name>",
    test_module="test_<module_name>_progressive",  # Progressive tests
    category="<category>",  # volo_modules, ds1120_pd, examples
),
```

### Step 6: Test It!

```bash
# Test P1 (should be <20 lines output)
uv run python tests/run.py <module_name>

# Test P2 (full suite)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module_name>
```

### Step 7: Clean Up Old Files

```bash
# Remove old monolithic test
rm tests/test_<module_name>.py
```

### Step 8: Commit

```bash
git add tests/<module_name>_tests/ tests/test_<module_name>_progressive.py tests/test_configs.py
git commit -m "feat: Add progressive tests for <module_name>"
```

---

## Code Templates

### Minimal Constants File

```python
from pathlib import Path

MODULE_NAME = "my_module"
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"

HDL_SOURCES = [VHDL_DIR / "my_module.vhd"]
HDL_TOPLEVEL = "my_module"

class ErrorMessages:
    RESET_FAILED = "Reset check failed: {}"
```

### Minimal Test File

```python
import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_low
from test_base import TestBase
from my_module_tests.my_module_constants import *

class MyModuleTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def run_p1_basic(self):
        await setup_clock(self.dut)
        await self.test("Reset", self.test_reset)

    async def test_reset(self):
        await reset_active_low(self.dut)
        assert int(self.dut.output.value) == 0

@cocotb.test()
async def test_my_module(dut):
    tester = MyModuleTests(dut)
    await tester.run_all_tests()
```

---

## Examples

### Example 1: volo_clk_divider (Simple Module)

**Structure:**
```
tests/
├── volo_clk_divider_tests/
│   ├── __init__.py
│   └── volo_clk_divider_constants.py
└── test_volo_clk_divider_progressive.py
```

**P1 Tests (3 tests):**
1. Reset behavior
2. Divide by 2
3. Enable control

**P2 Tests (adds 4 more):**
4. Divide by 1 (bypass)
5. Divide by 10
6. Maximum division (255)
7. Status register

**Results:**
- P1: 8 lines output
- P2: All 7 tests pass

### Example 2: volo_voltage_pkg (Package Test)

**Structure:**
```
tests/
├── volo_voltage_pkg_tests/
│   ├── __init__.py
│   └── volo_voltage_pkg_constants.py
└── test_volo_voltage_pkg_progressive.py
```

**P1 Tests (2 tests):**
1. Voltage constants
2. Conversion sanity

**Results:**
- P1: 6 lines output

---

## Common Patterns

### Pattern 1: Counting Pulses

```python
from conftest import count_pulses

async def test_divide_by_2(self):
    await reset_active_low(self.dut)

    self.dut.div_sel.value = 2
    await ClockCycles(self.dut.clk, 2)

    # Count pulses using utility function
    pulse_count = await count_pulses(self.dut.clk_en, self.dut.clk, 20)

    assert pulse_count == 10, f"Expected 10 pulses, got {pulse_count}"
```

### Pattern 2: Asserting Pulse Count

```python
from conftest import assert_pulse_count

async def test_divide_by_10(self):
    await reset_active_low(self.dut)

    self.dut.div_sel.value = 10
    await ClockCycles(self.dut.clk, 2)

    # Combined count + assert
    await assert_pulse_count(self.dut.clk_en, self.dut.clk, cycles=100, expected=10)
```

### Pattern 3: Verbose Logging

```python
async def test_something(self):
    # This only prints when COCOTB_VERBOSITY >= VERBOSE
    self.log(f"Counter value: {count}", VerbosityLevel.VERBOSE)

    # This only prints when COCOTB_VERBOSITY >= NORMAL
    self.log("Test starting", VerbosityLevel.NORMAL)
```

### Pattern 4: Conditional Test Execution

P2 tests automatically run only when `TEST_LEVEL=P2_INTERMEDIATE`:

```python
async def run_p2_intermediate(self):
    # This method only runs if TEST_LEVEL >= P2_INTERMEDIATE
    await self.test("Advanced test", self.test_advanced)
```

---

## Troubleshooting

### Issue: Tests produce too much output in P1

**Solution:** Reduce logging in test functions:
```python
# BAD - prints unconditionally
dut._log.info("Debug info")

# GOOD - only prints in verbose mode
self.log("Debug info", VerbosityLevel.VERBOSE)
```

### Issue: Tests take too long in P1

**Solution:** Use smaller test values in constants:
```python
class TestValues:
    # BAD - slow!
    P1_TEST_CYCLES = 10000

    # GOOD - fast!
    P1_TEST_CYCLES = 20
```

### Issue: Can't access module signals

**Solution:** Check entity name matches toplevel in test_configs.py:
```python
# GHDL lowercases entity names!
toplevel="my_module",  # Not "My_Module"
```

### Issue: Import errors

**Solution:** Make sure `sys.path.insert(0, ...)` is present:
```python
import sys
from pathlib import Path

# Required for imports to work!
sys.path.insert(0, str(Path(__file__).parent))
```

### Issue: P2 tests don't run

**Solution:** Set environment variable:
```bash
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module>
```

---

## Best Practices

### ✅ DO:
- Keep P1 to 2-4 essential tests
- Use small test values in P1 (cycles=20, not 10000)
- Use `self.log()` with verbosity levels
- Put all magic numbers in constants file
- Test after each step
- Commit incrementally

### ❌ DON'T:
- Add debug prints without verbosity control
- Use large test values in P1
- Skip creating constants file
- Forget to update test_configs.py
- Commit untested code

---

## Environment Variables

Control test execution and verbosity:

```bash
# Test level (what runs)
export TEST_LEVEL=P1_BASIC        # Only P1 (default)
export TEST_LEVEL=P2_INTERMEDIATE # P1 + P2
export TEST_LEVEL=P3_COMPREHENSIVE # P1 + P2 + P3
export TEST_LEVEL=P4_EXHAUSTIVE   # All tests

# Output verbosity (how much prints)
export COCOTB_VERBOSITY=SILENT    # Errors only
export COCOTB_VERBOSITY=MINIMAL   # Test names + PASS/FAIL (default)
export COCOTB_VERBOSITY=NORMAL    # + progress
export COCOTB_VERBOSITY=VERBOSE   # + details
export COCOTB_VERBOSITY=DEBUG     # Everything

# Example: Full tests with normal output
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL uv run python tests/run.py my_module
```

---

## Summary

**Progressive testing gives you:**
- ✅ 98% reduction in test output (LLM-friendly!)
- ✅ Fast default tests (P1)
- ✅ Comprehensive validation when needed (P2)
- ✅ Clean, maintainable test structure
- ✅ Easy to add new tests

**Next steps:**
1. Pick a module to convert
2. Follow the step-by-step guide
3. Test it works
4. Commit!

**Need help?** Check the examples in `tests/volo_clk_divider_tests/` or `tests/volo_voltage_pkg_tests/`.
