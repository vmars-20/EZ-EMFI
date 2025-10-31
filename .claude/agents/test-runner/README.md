# Test Runner Agent

**Purpose:** Autonomous CocotB progressive test execution, generation, and debugging

---

## Quick Start

### In Claude Code

```
@test-runner Run P1 tests for volo_clk_divider
@test-runner Find all failing tests
@test-runner Generate P1/P2 tests for new_module
```

### In Cursor / Other IDEs

1. Copy contents of `agent.md`
2. Paste into chat context
3. Ask: "Run P1 tests for volo_clk_divider"

---

## Common Use Cases

### Running Tests

```
@test-runner Run P1 tests for volo_clk_divider
@test-runner Run P2 tests for volo_lut_pkg
@test-runner Run all tests
```

### Writing Tests

```
@test-runner Generate P1/P2 progressive tests for my_new_module
@test-runner Add edge case tests to volo_voltage_pkg
```

### Debugging Tests

```
@test-runner Fix failing test in test_volo_clk_divider_progressive.py
@test-runner Debug timeout in ds1120_pd_volo test
@test-runner Why is voltage conversion test failing?
```

### Exploring Tests

```
@test-runner Find all P1 tests
@test-runner Show test coverage for ds1140_pd
@test-runner What tests exist for voltage conversion?
```

---

## What This Agent Can Do

✅ **Read & Write:**
- `tests/**/*.py` - Progressive test files
- `tests/**/*_tests/` - Test infrastructure
- `tests/**/*_tb_wrapper.vhd` - VHDL test wrappers

✅ **Read-Only (for context):**
- `tools/**/*.py` - Deployment patterns, voltage utilities
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - Critical pitfalls

✅ **Execute:**
- Run CocotB tests via `uv run python tests/run.py`
- GHDL compilation checks

---

## What This Agent Cannot Do

❌ **Modify Python tooling** → Use `@python-dev` agent
❌ **Modify VHDL source** → Use `@vhdl-dev` agent (when available)
❌ **Deploy to hardware** → Use `@moku-deploy` agent

---

## Key Features

### Progressive Testing
- **P1 (Basic):** Fast smoke tests (2-4 tests, <5s, <20 lines output)
- **P2 (Intermediate):** Comprehensive coverage (all edge cases)

### Templates
- Auto-generates test files from templates
- Creates test constants files
- Generates VHDL test wrappers

### Pitfall Awareness
- Knows top 5 CocotB/VHDL pitfalls
- References `docs/VHDL_COCOTB_LESSONS_LEARNED.md`
- Avoids common mistakes (subtypes, hex literals, arithmetic)

---

## Integration with Slash Commands

Use `/test` to enter testing mode, then invoke agent:

```
/test
@test-runner Run all P1 tests
```

---

## Files

- `agent.md` - Standalone agent instructions (portable)
- `README.md` - This file (usage guide)

---

**Version:** 1.0
**Last Updated:** 2025-01-28
