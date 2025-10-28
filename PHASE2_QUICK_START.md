# Phase 2 Quick Start Guide

**Context**: Phase 1 complete (VoloApp framework migrated)
**Commit**: 4f346ad
**Date**: 2025-10-27

---

## What Was Accomplished (Phase 1)

✓ Complete VoloApp framework migrated from volo_vhdl_external_
✓ Python models (Pydantic) working
✓ VHDL infrastructure copied (shared/volo/)
✓ Code generation tool functional
✓ Comparison analysis completed
✓ Dependencies installed and locked

**Key Discovery**: Existing VHDL files were properly generated from framework!
- Shim: Generated (minor naming difference)
- Main: Fully implemented (hand-written as intended)

---

## Critical Issue: Naming Convention

### Problem
YAML uses `DS1120-PD` (hyphen), but VHDL needs `DS1120_PD` (underscore)

### Solution Options

**Option 1: Update YAML** (RECOMMENDED)
```bash
# Change app name to use underscore
sed -i '' 's/name: DS1120-PD/name: DS1120_PD/' DS1120-PD_app.yaml
mv DS1120-PD_app.yaml DS1120_PD_app.yaml
git add DS1120_PD_app.yaml
git rm DS1120-PD_app.yaml
git commit -m "fix: Use underscore in app name for VHDL compatibility"
```

**Option 2: Update Generator**
Modify `models/volo/volo_app.py` to sanitize hyphens from entity names

---

## Phase 2 Tasks (Priority Order)

### Task 1: Fix Naming Convention (5 min)
```bash
# Choose Option 1 (simplest)
sed -i '' 's/name: DS1120-PD/name: DS1120_PD/' DS1120-PD_app.yaml
mv DS1120-PD_app.yaml DS1120_PD_app.yaml

# Regenerate to verify
uv run python tools/generate_volo_app.py \
    --config DS1120_PD_app.yaml \
    --output test_regen/

# Compare with existing (should be identical now)
diff VHDL/DS1120_PD_volo_shim.vhd test_regen/DS1120_PD_volo_shim.vhd
```

**Expected**: Only timestamp difference

### Task 2: Create Top.vhd (Layer 1) (30 min)

**Goal**: Implement CustomWrapper architecture that instantiates volo_loader

**Approach A** (Copy and customize):
```bash
cp shared/volo/MCC_TOP_volo_loader.vhd VHDL/Top.vhd
```

Then edit `VHDL/Top.vhd` lines 133-173 to:
1. Uncomment DS1120_PD_volo_shim instantiation
2. Update entity name: `DS1120_PD_volo_shim` (with underscore)
3. Remove placeholder pass-through (lines 172-173)

**Key ports to map**:
```vhdl
APP_SHIM_INST: entity WORK.DS1120_PD_volo_shim
    port map (
        -- Clock and Reset
        Clk         => Clk,
        Reset       => Reset,

        -- VOLO Control Signals
        volo_ready  => volo_ready,
        user_enable => user_enable,
        clk_enable  => clk_enable,
        loader_done => loader_done,

        -- Application Registers (all 11)
        app_reg_20  => app_reg_20,
        app_reg_21  => app_reg_21,
        -- ... through app_reg_30

        -- BRAM Interface
        bram_addr   => bram_addr,
        bram_data   => bram_data,
        bram_we     => bram_we,

        -- MCC I/O
        InputA      => InputA,
        InputB      => InputB,
        OutputA     => OutputA,
        OutputB     => OutputB
    );
```

### Task 3: Add CustomWrapper Stub (5 min)

For CocotB testing:
```bash
cp DCSequencer/CustomWrapper_test_stub.vhd VHDL/
```

### Task 4: Test 3-Layer Architecture (15 min)

```bash
# Run existing DS1120-PD tests
uv run python tests/run.py ds1120_pd_volo

# Expected: All tests pass with new architecture
```

**If tests fail**, check:
1. Entity name matches (underscore vs hyphen)
2. All ports connected in Top.vhd
3. CustomWrapper stub included in compilation

### Task 5: Update Build System (30 min)

Create/update `scripts/build_mcc_package.py`:

**Files to include**:
```
MCC Package Contents:
├── Top.vhd                         # Layer 1 (CustomWrapper architecture)
├── DS1120_PD_volo_shim.vhd        # Layer 2 (generated)
├── DS1120_PD_volo_main.vhd        # Layer 3 (hand-written)
├── volo_bram_loader.vhd           # BRAM loader FSM
├── volo_common_pkg.vhd            # Common constants
├── ds1120_pd_fsm.vhd              # Application FSM
├── ds1120_pd_pkg.vhd              # Application package
├── volo_clk_divider.vhd           # Utility
├── volo_voltage_pkg.vhd           # Utility
├── volo_voltage_threshold_trigger_core.vhd  # Utility
└── fsm_observer.vhd               # Debug utility
```

---

## Success Criteria (Phase 2)

- [ ] Naming convention fixed (underscore in entity names)
- [ ] Top.vhd created and compiles
- [ ] 3-layer architecture instantiated correctly
- [ ] CocotB tests pass
- [ ] MCC package builds successfully

---

## Common Issues & Solutions

### Issue 1: Entity Name Mismatch
**Symptom**: "entity DS1120-PD_volo_shim not found"
**Solution**: Use underscore: `DS1120_PD_volo_shim`

### Issue 2: Port Map Incomplete
**Symptom**: "unconnected port" warnings
**Solution**: Map all 11 app_reg_XX ports in Top.vhd

### Issue 3: Missing Dependencies
**Symptom**: "package volo_common_pkg not found"
**Solution**: Include shared/volo/*.vhd in compilation

---

## Files to Review Before Starting

1. `COMPARISON_ANALYSIS.md` - Detailed comparison findings
2. `VOLO_FRAMEWORK_MIGRATION.md` - Phase 1 summary
3. `shared/volo/MCC_TOP_volo_loader.vhd` - Template for Top.vhd
4. `VHDL/DS1120_PD_volo_shim.vhd` - Current shim (reference)

---

## Useful Commands

```bash
# Verify framework is working
uv run python -c "from models.volo import VoloApp; \
    app = VoloApp.load_from_yaml('DS1120_PD_app.yaml'); \
    print(f'{app.name}: {len(app.registers)} registers')"

# Generate VHDL
uv run python tools/generate_volo_app.py \
    --config DS1120_PD_app.yaml \
    --output test_output/

# Run tests
uv run python tests/run.py ds1120_pd_volo

# Check VHDL syntax (if ghdl installed)
ghdl -s --std=08 VHDL/Top.vhd
```

---

## Time Estimate

- Task 1 (naming): 5 minutes
- Task 2 (Top.vhd): 30 minutes
- Task 3 (stub): 5 minutes
- Task 4 (testing): 15 minutes
- Task 5 (build): 30 minutes

**Total**: ~90 minutes for complete Phase 2

---

## Next Session Checklist

1. [ ] Read COMPARISON_ANALYSIS.md
2. [ ] Fix naming convention
3. [ ] Create Top.vhd
4. [ ] Test with CocotB
5. [ ] Update build system

**Start with**: Task 1 (naming fix) - it's quick and unblocks everything else.

---

## Questions to Ask in Next Session

1. Should we rename the YAML file? (DS1120-PD → DS1120_PD)
2. Do we want to keep both naming conventions? (hyphen for metadata, underscore for VHDL)
3. Should we migrate other shared utilities from volo_vhdl_external_ now?
4. Is there a build script we should update?

---

## References

- Commit: `4f346ad` (Phase 1 complete)
- Branch: `feature/mcc-top`
- Framework source: `volo_vhdl_external_/`
- Reference example: `DCSequencer/`
