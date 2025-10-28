# Phase 2: Progressive Test Structure

Phase 1 ✅ Complete: Infrastructure works, filtering is bulletproof.

## Goals for Phase 2

### 1. Reorganize VHDL Files (30-45 min)
Separate reusable modules from application code:

```
VHDL/
├── volo_modules/           # Reusable building blocks
│   ├── volo_clk_divider.vhd
│   ├── volo_voltage_pkg.vhd
│   ├── volo_common_pkg.vhd
│   ├── volo_voltage_threshold_trigger_core.vhd
│   ├── volo_bram_loader.vhd
│   └── fsm_observer.vhd
└── ds1120_pd/              # Application-specific
    ├── ds1120_pd_pkg.vhd
    ├── ds1120_pd_fsm.vhd
    ├── DS1120_PD_volo_main.vhd
    └── DS1120_PD_volo_shim.vhd
```

**Action items:**
- [ ] Create directory structure
- [ ] Move files (use `git mv` to preserve history)
- [ ] Update `tests/test_configs.py` with new paths
- [ ] Verify tests still run: `uv run python tests/run.py volo_clk_divider`

### 2. Create Progressive Test Structure for volo_clk_divider (45-60 min)

**Goal:** Demonstrate hierarchical P1/P2/P3 pattern

```
tests/
└── volo_clk_divider_tests/
    ├── volo_clk_divider_constants.py  # Shared config (REQUIRED)
    ├── P1_volo_clk_divider_basic.py   # 3-5 essential tests
    └── P2_volo_clk_divider_intermediate.py  # Full test suite
```

**Action items:**
- [ ] Create `tests/volo_clk_divider_tests/` directory
- [ ] Create `volo_clk_divider_constants.py` (see example in volo_vhdl_external)
- [ ] Split existing `test_volo_clk_divider.py` into:
  - P1: Reset + divide-by-1 + divide-by-2 (essential, <10 lines output)
  - P2: All remaining tests (enable control, max division, status)
- [ ] Update `test_configs.py` to point to P1 by default
- [ ] Test both levels:
  ```bash
  uv run python tests/run.py volo_clk_divider  # Should run P1 only
  TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider
  ```

### 3. Create Progressive Tests for DS1120-PD (1-2 hours)

**Goal:** Full application test with P1/P2/P3 levels

```
tests/
└── ds1120_pd_volo_tests/
    ├── ds1120_pd_constants.py       # Port from volo_vhdl_external
    ├── P1_ds1120_pd_basic.py        # Reset + VOLO_READY + simple arm
    ├── P2_ds1120_pd_intermediate.py # Safety features + thresholds
    └── P3_ds1120_pd_comprehensive.py # FSM states + edge cases
```

**Action items:**
- [ ] Create directory structure
- [ ] Port constants from `volo_vhdl_external_/tests/ds1120_pd_volo_tests/`
- [ ] Split existing `test_ds1120_pd_volo.py` across P1/P2/P3
- [ ] Register in `test_configs.py`
- [ ] Test all levels

### 4. Update Documentation (15-30 min)

**Action items:**
- [ ] Update `CLAUDE.md` with testing workflow section
- [ ] Create `docs/TESTING.md` (simplified from HUMAN_TESTING_README.md)
- [ ] Update `README.md` with quick start
- [ ] Add testing examples to each doc

### 5. Cleanup (15 min)

**Action items:**
- [ ] Clean up `outside_docs_helpme/` (move to `archive/`)
- [ ] Remove unused test files (old flat tests)
- [ ] Clean up `.gitignore` (add `__pycache__/`, `sim_build/`)
- [ ] Final commit

## Success Criteria

✅ All tests run and pass
✅ P1 tests produce <20 lines of output (LLM-friendly)
✅ VHDL files logically organized (modules vs. application)
✅ Documentation is clear and concise
✅ Old structure cleaned up

## Estimated Time: 3-4 hours

## Context Preservation Notes

- Phase 1 consumed ~104k/200k tokens (52%)
- Phase 2 will be text-light (file moves, test splits)
- Should fit comfortably in new context window
- Key files to reference:
  - `volo_vhdl_external_/tests/ds1120_pd_volo_tests/` (examples)
  - `outside_docs_helpme/VOLO_COCOTB_TESTING_STANDARD.md` (patterns)
