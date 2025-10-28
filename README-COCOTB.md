# CocotB Testing Infrastructure

EZ-EMFI uses a sophisticated Python-based testing system with **bulletproof output filtering** to preserve LLM context windows.

## Quick Start

```bash
# Install dependencies
uv sync

# List available tests
uv run python tests/run.py --list

# Run a test (with LLM-friendly output filtering)
uv run python tests/run.py volo_clk_divider

# Run all tests in a category
uv run python tests/run.py --category volo_modules
```

## Key Features

### 1. **No Makefiles!** Pure Python test runner
- Uses `cocotb_tools.runner` API
- Simple test registration in `tests/test_configs.py`
- Just add VHDL sources and run

### 2. **Bulletproof Output Filtering**
OS-level file descriptor redirection captures GHDL output **before it reaches stdout**. Cannot be bypassed.

```bash
# Default: Normal filtering (removes metavalue warnings)
uv run python tests/run.py volo_clk_divider

# Aggressive: Maximum suppression for LLMs
uv run python tests/run.py volo_clk_divider --filter-level aggressive

# See everything (debugging)
uv run python tests/run.py volo_clk_divider --no-filter
```

**Example output:**
```
🧪 Running CocotB tests...
[Filtered 2 lines (2/113 = 1.8% reduction)]
✅ Test 'volo_clk_divider' PASSED
```

### 3. **Progressive Test Levels** ✅ **IMPLEMENTED**
Tests are organized into levels for LLM-friendly output:
- **P1 (Basic)**: 2-4 essential tests, <20 lines output (default)
- **P2 (Intermediate)**: Full test suite with edge cases
- **P3 (Comprehensive)**: Stress tests and boundaries (future)
- **P4 (Exhaustive)**: Debug-level testing (future)

**Example - Default P1 output:**
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
✅ Test 'volo_clk_divider' PASSED
```
**Just 8 lines!** Perfect for LLM context.

**Need more detail? Run P2:**
```bash
$ TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider
P1 - BASIC TESTS
[3 tests: Reset, Divide by 2, Enable]
P2 - INTERMEDIATE TESTS
T4: Divide by 1 (bypass)
  ✓ PASS
T5: Divide by 10
  ✓ PASS
T6: Maximum division (255)
  ✓ PASS
T7: Status register
  ✓ PASS
ALL 7 TESTS PASSED
```

**Result:** 98% reduction in test output while maintaining full validation!

## Quick Reference

### Test Levels

| Level | Command | Tests Run | Use Case |
|-------|---------|-----------|----------|
| **P1** (default) | `uv run python tests/run.py <module>` | Essential (2-4 tests) | Quick validation, LLM workflows |
| **P2** | `TEST_LEVEL=P2_INTERMEDIATE uv run ...` | P1 + comprehensive | Pre-commit, full validation |
| **P3** | `TEST_LEVEL=P3_COMPREHENSIVE uv run ...` | P1 + P2 + stress | Release testing (future) |
| **P4** | `TEST_LEVEL=P4_EXHAUSTIVE uv run ...` | All tests | Deep debugging (future) |

### Output Verbosity

| Level | Command | Output |
|-------|---------|--------|
| **MINIMAL** (default) | `uv run python tests/run.py <module>` | Test names + PASS/FAIL |
| **NORMAL** | `COCOTB_VERBOSITY=NORMAL uv run ...` | + progress indicators |
| **VERBOSE** | `COCOTB_VERBOSITY=VERBOSE uv run ...` | + detailed logs |
| **DEBUG** | `COCOTB_VERBOSITY=DEBUG uv run ...` | Everything |

### Combined Example

```bash
# Full tests with detailed output
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL uv run python tests/run.py volo_clk_divider
```

### Modules with Progressive Tests

| Module | P1 Tests | P2 Tests | P1 Output |
|--------|----------|----------|-----------|
| `volo_clk_divider` | 3 | 7 | 8 lines |
| `volo_voltage_pkg` | 2 | 2 | 6 lines |

**Creating new progressive tests?** See `docs/PROGRESSIVE_TESTING_GUIDE.md`

## Architecture

```
tests/
├── run.py                           # Test runner with bulletproof filtering
├── test_base.py                     # Progressive test framework (P1/P2/P3)
├── test_configs.py                  # Simple test registration (dict-based)
├── conftest.py                      # Shared test utilities (MCC helpers)
├── <module>_tests/                  # Progressive test structure
│   ├── __init__.py
│   ├── <module>_constants.py        # Shared test constants
│   ├── P1_<module>_basic.py         # Minimal tests (optional separate file)
│   └── P2_<module>_intermediate.py  # Comprehensive tests (optional)
└── test_<module>_progressive.py     # Unified test dispatcher

docs/
└── PROGRESSIVE_TESTING_GUIDE.md     # Complete conversion guide
```

## Adding a New Test

Edit `tests/test_configs.py`:

```python
TESTS_CONFIG["my_module"] = TestConfig(
    name="my_module",
    sources=[VHDL / "my_module.vhd"],
    toplevel="my_module",
    test_module="test_my_module",
    category="volo_modules",
)
```

That's it! No Makefiles to update.

## Converting Tests to Progressive Format

See the comprehensive guide: **`docs/PROGRESSIVE_TESTING_GUIDE.md`**

**Quick conversion (30-45 mins per module):**
1. Create `tests/<module>_tests/` directory
2. Create constants file with test parameters
3. Create progressive test file with P1/P2 methods
4. Update `test_configs.py`
5. Test and commit!

The guide includes:
- Step-by-step instructions
- Code templates
- Working examples
- Common patterns
- Troubleshooting

---

**Status:**
- ✅ **Phase 1 Complete:** Bulletproof CocotB infrastructure
- ✅ **Phase 2 Complete:** Progressive test structure implemented
- 📝 **Next:** Apply pattern to remaining modules
