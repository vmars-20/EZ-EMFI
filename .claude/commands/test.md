# Testing Mode

You are now in **testing and validation mode**.

---

## Autonomous Testing

For test exploration, execution, and debugging, use the specialized agent:

```
@test-runner Run P1 tests for volo_clk_divider
@test-runner Generate tests for new_module
@test-runner Fix failing test in test_ds1140_pd.py
```

The test-runner agent has:
- Full access to `tests/**` (read/write)
- Read-only access to `tools/**` (for context)
- Knowledge of progressive testing (P1/P2)
- Awareness of top 5 testing pitfalls

---

## Key Files in Scope

**Tests:**
- `tests/test_*_progressive.py` - Progressive test files
- `tests/*_tests/` - Test infrastructure
- `tests/*_tb_wrapper.vhd` - VHDL test wrappers

**Documentation:**
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - ⚠️ CRITICAL READING
- `tests/README.md` - Testing framework guide

---

## Quick Reference

**Run tests:**
```bash
uv run python tests/run.py <module>                    # P1 tests
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module>  # P2 tests
uv run python tests/run.py --all                       # All tests
```

**Progressive levels:**
- **P1 (Basic):** 2-4 tests, <5s runtime, <20 lines output
- **P2 (Intermediate):** Full coverage, all edge cases

**Available modules:**
- `volo_clk_divider`, `volo_voltage_pkg`, `volo_lut_pkg`
- `ds1120_pd_volo`, `ds1140_pd_volo`

---

## Context Switching

**Working on VHDL?** → `/vhdl` (when available)
**Working on Python tools?** → `/python`
**Deploying to hardware?** → `/moku`

---

Now in testing mode. Use `@test-runner` for autonomous test work.
