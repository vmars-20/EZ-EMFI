# VOLO CocotB Testing Standard
*The Authoritative Guide for Progressive, LLM-Optimized VHDL Testing*

## Executive Summary

All VOLO modules use **Progressive CocotB Testing** with **Aggressive Output Suppression** to preserve LLM context windows while maintaining thorough validation. This document defines the mandatory structure and execution patterns.

**Key Principle**: Start minimal (P1), escalate only when needed. Default to silent operation.

## Test Structure (Mandatory)

### Directory Organization
```
tests/
├── test_base.py                          # Base class (DO NOT MODIFY)
├── ghdl_output_filter.py                 # Output filter (DO NOT MODIFY)
├── <module_name>_tests/                  # Per-module directory (REQUIRED)
│   ├── <module_name>_constants.py        # Shared constants (REQUIRED)
│   ├── P1_<module_name>_basic.py         # Minimal tests (REQUIRED)
│   ├── P2_<module_name>_intermediate.py  # Standard tests (OPTIONAL)
│   ├── P3_<module_name>_comprehensive.py # Full tests (OPTIONAL)
│   └── P4_<module_name>_exhaustive.py    # Debug tests (OPTIONAL)
└── run.py                                 # Test runner (AUTO-OPTIMIZED)
```

### P1 - Basic Tests (REQUIRED, LLM-DEFAULT)
```python
# P1_<module_name>_basic.py
"""
P1 - Basic Tests for <module_name>

MINIMAL output, FAST execution, ESSENTIAL validation only.
Target: <10 tests, <100ms runtime, <50 tokens output.
"""

import cocotb
from conftest import setup_clock, reset_active_low
from test_base import TestBase
from <module_name>_tests.<module_name>_constants import *

class <ModuleName>BasicTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def run_p1_basic(self):
        # 3-5 ESSENTIAL tests only
        await self.test("Reset", self.test_reset)
        await self.test("Basic operation", self.test_basic_op)
        await self.test("Enable control", self.test_enable)

@cocotb.test()
async def test_<module_name>_p1(dut):
    """Entry point - CocotB discovers this"""
    tester = <ModuleName>BasicTests(dut)
    await tester.run_all_tests()
```

### Constants File (REQUIRED)
```python
# <module_name>_constants.py
"""Shared constants - Single source of truth"""

MODULE_NAME = "<module_name>"
HDL_SOURCES = [
    Path("../modules/<category>/<module>/core/<module>.vhd"),
]
HDL_TOPLEVEL = "<entity_name>"

# Test parameters (use SMALL values in P1!)
class TestValues:
    P1_MAX_VALUES = [10, 15, 20]      # SMALL for speed
    P2_MAX_VALUES = [100, 255, 1000]  # Realistic
    P3_MAX_VALUES = [2**12-1, 2**16-1] # Boundaries
```

## Execution Commands

### Default (LLM-Optimized)
```bash
# Automatic: P1 tests, MINIMAL output, GHDL suppression
uv run python tests/run.py <module_name>

# Result: ~10 lines, ~100 tokens TOTAL
```

### Progressive Escalation
```bash
# P2: When P1 passes but you need more coverage
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module_name>

# P3: Pre-commit validation
TEST_LEVEL=P3_COMPREHENSIVE COCOTB_VERBOSITY=NORMAL uv run python tests/run.py <module_name>

# P4: Debug mode (maximum output)
TEST_LEVEL=P4_EXHAUSTIVE COCOTB_VERBOSITY=DEBUG uv run python tests/run.py <module_name>
```

### Environment Control
```bash
# Test Progression (what runs)
export TEST_LEVEL=P1_BASIC        # Minimal (DEFAULT)
export TEST_LEVEL=P2_INTERMEDIATE # + edge cases
export TEST_LEVEL=P3_COMPREHENSIVE # + stress tests
export TEST_LEVEL=P4_EXHAUSTIVE   # + random/debug

# Output Verbosity (how much prints)
export COCOTB_VERBOSITY=SILENT    # Failures only
export COCOTB_VERBOSITY=MINIMAL   # + PASS/FAIL (DEFAULT)
export COCOTB_VERBOSITY=NORMAL    # + progress
export COCOTB_VERBOSITY=VERBOSE   # + details
export COCOTB_VERBOSITY=DEBUG     # Everything

# GHDL Filtering (automatic in run.py)
export GHDL_FILTER_LEVEL=aggressive # Maximum suppression
```

## Creating New Module Tests

### Step 1: Create Structure
```bash
mkdir tests/<module_name>_tests
```

### Step 2: Create Constants
```python
# tests/<module_name>_tests/<module_name>_constants.py
from pathlib import Path

MODULE_NAME = "<module_name>"
MODULE_PATH = Path("../modules/<category>/<module>")
HDL_SOURCES = [
    MODULE_PATH / "core" / "<module_name>.vhd",
]
HDL_TOPLEVEL = "<entity_name>"

# Small values for P1 speed!
DEFAULT_CLK_PERIOD_NS = 10
P1_TEST_CYCLES = 20  # Not 2000!
```

### Step 3: Create P1 Tests (Mandatory)
```python
# tests/<module_name>_tests/P1_<module_name>_basic.py
# COPY from counter_nbit_tests/P1_counter_nbit_basic.py as template
# MODIFY to test YOUR module's 3-5 core functions
```

### Step 4: Run Tests
```bash
# This automatically uses ALL optimizations
uv run python tests/run.py <module_name>
```

## Output Examples

### Good P1 Output (LLM-Friendly)
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Basic operation
  ✓ PASS
T3: Enable control
  ✓ PASS
ALL 3 TESTS PASSED
```
**5 lines, ~30 tokens** ✅

### Bad Output (Old Style)
```
0.00ns INFO cocotb.gpi ...
@0ms:(assertion warning): NUMERIC_STD.TO_INTEGER: metavalue detected...
[200+ lines of noise]
```
**250+ lines, 4000+ tokens** ❌

## Critical Rules

### DO's
1. **ALWAYS start with P1** - Get basics working first
2. **Use SMALL test values in P1** - 10, not 10000
3. **Default to MINIMAL verbosity** - Preserve context
4. **Inherit from TestBase** - Get verbosity control free
5. **Keep P1 under 10 tests** - Quality over quantity
6. **Use conftest utilities** - Don't reinvent wheels

### DON'Ts
1. **DON'T create old-style monolithic tests** - Use progressive levels
2. **DON'T use large values in P1** - Keep it fast
3. **DON'T print debug info by default** - Use log() with levels
4. **DON'T skip P1** - It's mandatory
5. **DON'T modify test_base.py** - It's the framework
6. **DON'T forget constants file** - Single source of truth

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: P1 Quick Tests (on every push)
  run: |
    export TEST_LEVEL=P1_BASIC
    export COCOTB_VERBOSITY=MINIMAL
    uv run python tests/run.py --all

- name: P2 Full Tests (on PR)
  if: github.event_name == 'pull_request'
  run: |
    export TEST_LEVEL=P2_INTERMEDIATE
    uv run python tests/run.py --all

- name: P3 Comprehensive (on main)
  if: github.ref == 'refs/heads/main'
  run: |
    export TEST_LEVEL=P3_COMPREHENSIVE
    uv run python tests/run.py --all
```

## Quick Reference Card

```bash
# Run single module test (LLM-optimized default)
uv run python tests/run.py volo_clk_divider

# Run with more detail (human debugging)
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py volo_clk_divider

# Run deeper tests (validation)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider

# Maximum detail (deep debugging)
TEST_LEVEL=P4_EXHAUSTIVE COCOTB_VERBOSITY=DEBUG uv run python tests/run.py volo_clk_divider

# List available tests
uv run python tests/run.py --list

# Run category
uv run python tests/run.py --category shared
```

## Why This Works

1. **Progressive Testing**: Start simple (P1), add complexity only when needed
2. **Context Preservation**: 98% reduction in output verbosity
3. **Fast Feedback**: P1 tests run in <1 second
4. **Debugging Power**: Can escalate to full verbosity when needed
5. **Single Source of Truth**: Constants file eliminates duplication
6. **Automatic Optimization**: Test runner handles all GHDL flags

## The Golden Rule

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

Default to silence. Escalate consciously. Preserve context religiously.

---
*Last Updated: 2025-01-26*
*Standard Version: 1.0*
*Enforcement: MANDATORY for all new modules*