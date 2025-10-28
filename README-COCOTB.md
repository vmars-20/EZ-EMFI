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

### 3. **Progressive Test Levels** (Coming in Phase 2)
- **P1 (Basic)**: 3-5 essential tests, <50 tokens output
- **P2 (Intermediate)**: Standard tests with edge cases
- **P3 (Comprehensive)**: Full validation with stress tests
- **P4 (Exhaustive)**: Debug-level testing

## Architecture

```
tests/
├── run.py              # Test runner with bulletproof filtering
├── test_base.py        # Progressive test framework (P1/P2/P3)
├── test_configs.py     # Simple test registration (dict-based)
├── conftest.py         # Shared test utilities (MCC helpers)
└── test_*.py           # Individual test files
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

---

**Phase 1 Complete:** Infrastructure works. Phase 2: Progressive test structure.
