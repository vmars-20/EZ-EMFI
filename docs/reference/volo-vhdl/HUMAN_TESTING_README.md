# 🧪 VOLO Testing Guide for Humans

> **TL;DR**: Run `uv run python tests/run.py <module_name>` to test any module. Tests are progressive: P1 (basic) → P2 (intermediate) → P3 (comprehensive).

---

## 🚀 Quick Start (30 seconds)

### Test ANY Module
```bash
# Clone and enter the repo
cd volo_vhdl

# Test a module (example: DS1120-PD EMFI driver)
uv run python tests/run.py ds1120_pd_volo
```

**Expected output (P1 default):**
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: VOLO_READY control
  ✓ PASS
T3: Basic arm/trigger
  ✓ PASS
ALL 3 TESTS PASSED
```
✅ **That's it!** You just ran tests.

---

## 📊 Understanding Test Levels

We use **Progressive Testing** - start simple, add complexity only when needed:

| Level | Purpose | Tests | Runtime | Output |
|-------|---------|-------|---------|--------|
| **P1** | Smoke test - does it work at all? | 3-5 | <1s | ~5 lines |
| **P2** | Real-world scenarios | 4-8 | <5s | ~10 lines |
| **P3** | Edge cases & stress | 2-5 | <10s | ~20 lines |
| **P4** | Debug/exhaustive | Many | Minutes | Verbose |

### Default = P1 (AI-Friendly)
- **Minimal output** preserves context windows
- **Fast execution** for rapid iteration
- **Essential tests** catch major breaks

---

## 🎮 Running Tests

### Run Default (P1)
```bash
uv run python tests/run.py ds1120_pd_volo
```

### Run Specific Level
```bash
# P2 - Intermediate tests with realistic values
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py ds1120_pd_volo

# P3 - Comprehensive with edge cases
TEST_LEVEL=P3_COMPREHENSIVE uv run python tests/run.py ds1120_pd_volo
```

### List Available Modules
```bash
uv run python tests/run.py --list
```
**Output:**
```
Available test modules:
  - clk_divider_core
  - ds1120_pd_volo
  - pulsestar_volo
  ...
```

### Run Multiple Modules
```bash
# Run all VOLO apps
uv run python tests/run.py --category volo

# Run everything (CI/CD style)
uv run python tests/run.py --all
```

---

## 🔊 Controlling Output Verbosity

### Minimal (Default)
```bash
# Just PASS/FAIL
uv run python tests/run.py ds1120_pd_volo
```

### Normal (Human Debugging)
```bash
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py ds1120_pd_volo
```
**Adds:** Progress indicators, timing info

### Verbose (Detailed Debugging)
```bash
COCOTB_VERBOSITY=VERBOSE uv run python tests/run.py ds1120_pd_volo
```
**Adds:** Individual assertions, state transitions

### Debug (Everything)
```bash
TEST_LEVEL=P3_COMPREHENSIVE COCOTB_VERBOSITY=DEBUG uv run python tests/run.py ds1120_pd_volo
```
**Adds:** GHDL output, signal changes, internal logs

### Combining Options
```bash
# P2 tests with normal verbosity
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL uv run python tests/run.py ds1120_pd_volo
```

---

## ➕ Adding Tests to Existing Modules

### Test Structure
Every module has tests in `tests/<module_name>_tests/`:
```
tests/ds1120_pd_volo_tests/
├── ds1120_pd_constants.py        # Shared config (edit this for parameters)
├── P1_ds1120_pd_basic.py        # Add essential tests here
├── P2_ds1120_pd_intermediate.py # Add normal tests here
└── P3_ds1120_pd_comprehensive.py # Add edge cases here
```

### Adding a Test to P1 (Example)
Open `P1_ds1120_pd_basic.py` and add your test method:

```python
async def test_my_new_feature(self):
    """T4: Test my new feature."""
    # Setup
    await setup_clock(self.dut, clk_signal="Clk")
    await reset_active_high(self.dut, rst_signal="Reset")

    # Your test logic
    self.dut.some_signal.value = 1
    await ClockCycles(self.dut.Clk, 10)

    # Assertion
    assert self.dut.output.value == expected, "Output mismatch"
```

Then add it to the run method:
```python
async def run_p1_basic(self):
    """Run all P1 basic tests."""
    await self.test("T1: Reset behavior", self.test_reset)
    await self.test("T2: VOLO_READY control", self.test_volo_ready)
    await self.test("T3: Basic arm/trigger", self.test_basic_arm_trigger)
    await self.test("T4: My new feature", self.test_my_new_feature)  # ADD THIS
```

### Which Level for Your Test?

| Add to P1 if... | Add to P2 if... | Add to P3 if... |
|-----------------|-----------------|-----------------|
| Core functionality | Safety features | Edge cases |
| Must always work | Real-world scenarios | Stress testing |
| <10 lines of test | <50 lines of test | Complex sequences |
| Tests one thing | Tests interactions | Tests limits |

---

## 📈 Generating Waveforms

### Enable Waveform Capture
```bash
WAVES=1 uv run python tests/run.py ds1120_pd_volo
```

### View Waveforms
```bash
cd tests/sim_build
gtkwave dump.vcd  # or your preferred viewer
```

**Note:** Waveforms are saved as `dump.vcd` in the `sim_build` directory.

---

## 🔧 Environment Setup

See [`docs/TEST_ENVIRONMENT_SETUP.md`](docs/TEST_ENVIRONMENT_SETUP.md) for:
- Installing Python and `uv`
- Setting up GHDL
- Configuring GTKWave
- Troubleshooting environment issues

---

## 📚 Quick Reference

### Essential Commands
```bash
# Most common - run basic tests
uv run python tests/run.py <module_name>

# Debug a failure
COCOTB_VERBOSITY=NORMAL uv run python tests/run.py <module_name>

# Full validation
TEST_LEVEL=P3_COMPREHENSIVE uv run python tests/run.py <module_name>

# List what's available
uv run python tests/run.py --list
```

### Environment Variables
| Variable | Options | Default |
|----------|---------|---------|
| `TEST_LEVEL` | P1_BASIC, P2_INTERMEDIATE, P3_COMPREHENSIVE, P4_EXHAUSTIVE | P1_BASIC |
| `COCOTB_VERBOSITY` | SILENT, MINIMAL, NORMAL, VERBOSE, DEBUG | MINIMAL |
| `WAVES` | 0, 1 | 1 |
| `GHDL_FILTER_LEVEL` | aggressive, normal, none | aggressive |

---

## 🎯 Philosophy

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

We optimize for:
1. **Fast feedback** - P1 runs in seconds
2. **Clear results** - PASS/FAIL is obvious
3. **Progressive detail** - Escalate verbosity only when debugging
4. **AI collaboration** - Minimal output preserves context

---

## 📖 More Information

- **Test Standard**: [`tests/README.md`](tests/README.md) - Full CocotB testing standard
- **Module Example**: [`tests/ds1120_pd_volo_tests/`](tests/ds1120_pd_volo_tests/) - Reference implementation
- **Base Classes**: [`tests/test_base.py`](tests/test_base.py) - Testing framework
- **Utilities**: [`tests/conftest.py`](tests/conftest.py) - Shared test helpers

---

*Last Updated: 2025-01-27*
*Testing Standard: VOLO CocotB v1.0*