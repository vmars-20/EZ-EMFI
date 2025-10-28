# Examples Directory

Educational examples and demonstrations for EZ-EMFI CocotB testing patterns.

## Files

### test_fsm_example.py
Demonstrates the FSM observer pattern used in the DS1120-PD design.

**What it shows:**
- How to test FSM state progression
- Voltage-based debug output pattern
- Sign-flip fault indication
- Automatic voltage spreading across states

**Usage:**
```bash
# Run as a standalone test
cocotb-run test_fsm_example.py --toplevel=fsm_observer
```

**Key Patterns:**
- Helper functions for voltage/digital conversion
- State-based voltage calculation
- Fault state testing

### test_verbosity_demo.py
Demonstrates the dramatic difference between old and new verbosity approaches.

**What it shows:**
- Old CocotB output (100+ lines per test)
- New progressive output (< 20 lines for P1)
- Why verbosity control matters for LLM context

**Usage:**
```bash
# Run the demo
python examples/test_verbosity_demo.py
```

**Purpose:**
Shows why we implemented progressive testing with verbosity control - context preservation for LLM-assisted development.

## Purpose

These files serve as:
1. **Learning materials** - Show testing patterns in practice
2. **Reference implementations** - Copy patterns to new tests
3. **Documentation** - Demonstrate why design decisions were made

## Note

These are **not** part of the main test suite (not in `test_configs.py`). They're educational examples only.

For the actual test suite, see:
- `tests/test_ds1120_pd_volo_progressive.py`
- `tests/test_volo_clk_divider_progressive.py`
- `tests/test_volo_voltage_pkg_progressive.py`
