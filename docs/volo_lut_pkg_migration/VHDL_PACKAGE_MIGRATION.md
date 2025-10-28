# VHDL Package Migration Plan

**Date**: 2025-01-28
**Status**: DRAFT - Ready for execution
**Effort**: ~30 minutes (low risk, high value)

## Executive Summary

Reorganize VHDL packages into a dedicated `VHDL/packages/` directory for better code organization, clearer dependency tracking, and alignment with industry best practices.

## Current State

```
VHDL/
├── ds1120_pd_pkg.vhd               # Package (application-specific)
├── volo_common_pkg.vhd             # Package (shared infrastructure)
├── volo_voltage_pkg.vhd            # Package (shared utilities)
├── ds1120_pd_fsm.vhd               # Entity
├── DS1120_PD_volo_main.vhd         # Entity
├── DS1120_PD_volo_shim.vhd         # Entity
├── fsm_observer.vhd                # Entity
├── volo_bram_loader.vhd            # Entity
├── volo_clk_divider.vhd            # Entity
├── volo_voltage_threshold_trigger_core.vhd  # Entity
├── Top.vhd                         # Entity
└── CustomWrapper_test_stub.vhd     # Entity
```

**Problem**: Packages mixed with entities - no clear separation of concerns.

## Target State

```
VHDL/
├── packages/
│   ├── ds1120_pd_pkg.vhd           # Application constants/types
│   ├── volo_common_pkg.vhd         # Shared infrastructure (VOLO_READY, BRAM)
│   ├── volo_voltage_pkg.vhd        # Voltage conversion utilities
│   └── volo_lut_pkg.vhd            # NEW: Generic 0-100 indexed LUTs
├── ds1120_pd_fsm.vhd
├── DS1120_PD_volo_main.vhd
├── DS1120_PD_volo_shim.vhd
├── fsm_observer.vhd
├── volo_bram_loader.vhd
├── volo_clk_divider.vhd
├── volo_voltage_threshold_trigger_core.vhd
├── Top.vhd
└── CustomWrapper_test_stub.vhd
```

**Benefits**:
- ✓ Clear separation: libraries vs implementations
- ✓ Easier dependency tracking (packages compiled first)
- ✓ Matches EXTERNAL_volo_vhdl structure (`modules/shared/packages/`)
- ✓ Scalable for future packages

## Migration Steps

### Step 1: Create Directory Structure
```bash
cd /Users/vmars20/EZ-EMFI/VHDL
mkdir -p packages
```

### Step 2: Move Package Files
```bash
# Move existing packages
git mv ds1120_pd_pkg.vhd packages/
git mv volo_common_pkg.vhd packages/
git mv volo_voltage_pkg.vhd packages/

# Verify structure
ls -la packages/
```

### Step 3: Update Test Configuration

**File**: `tests/test_configs.py`

**Changes** (Lines 20, 55-56, 66-67, 87-88, 95, 110, 123):

```python
# Line 20 - Add packages path
PROJECT_ROOT = Path(__file__).parent.parent
VHDL = PROJECT_ROOT / "VHDL"
VHDL_PKG = VHDL / "packages"  # NEW
TESTS = PROJECT_ROOT / "tests"

# Update all package references:
# Before:  VHDL / "volo_voltage_pkg.vhd"
# After:   VHDL_PKG / "volo_voltage_pkg.vhd"

# Example (volo_voltage_pkg test):
"volo_voltage_pkg": TestConfig(
    name="volo_voltage_pkg",
    sources=[
        VHDL_PKG / "volo_voltage_pkg.vhd",  # Updated path
        TESTS / "volo_voltage_pkg_tb_wrapper.vhd",
    ],
    toplevel="volo_voltage_pkg_tb_wrapper",
    test_module="test_volo_voltage_pkg_progressive",
    category="volo_modules",
),

# Update 7 more references in:
# - volo_bram_loader (line 66-67)
# - ds1120_pd_volo (line 87-88, 95)
# - fsm_example (line 110)
# - verbosity_demo (line 123)
```

**Full diff**:
```diff
--- a/tests/test_configs.py
+++ b/tests/test_configs.py
@@ -18,6 +18,7 @@ from typing import List
 # Project paths
 PROJECT_ROOT = Path(__file__).parent.parent
 VHDL = PROJECT_ROOT / "VHDL"
+VHDL_PKG = VHDL / "packages"
 TESTS = PROJECT_ROOT / "tests"


@@ -52,7 +53,7 @@ TESTS_CONFIG = {
     "volo_voltage_pkg": TestConfig(
         name="volo_voltage_pkg",
         sources=[
-            VHDL / "volo_voltage_pkg.vhd",
+            VHDL_PKG / "volo_voltage_pkg.vhd",
             TESTS / "volo_voltage_pkg_tb_wrapper.vhd",
         ],
         toplevel="volo_voltage_pkg_tb_wrapper",
@@ -63,8 +64,8 @@ TESTS_CONFIG = {
     "volo_bram_loader": TestConfig(
         name="volo_bram_loader",
         sources=[
-            VHDL / "volo_voltage_pkg.vhd",
-            VHDL / "volo_common_pkg.vhd",
+            VHDL_PKG / "volo_voltage_pkg.vhd",
+            VHDL_PKG / "volo_common_pkg.vhd",
             VHDL / "fsm_observer.vhd",
             VHDL / "volo_bram_loader.vhd",
         ],
@@ -84,8 +85,8 @@ TESTS_CONFIG = {
         name="ds1120_pd_volo",
         sources=[
             # Shared volo modules
-            VHDL / "volo_voltage_pkg.vhd",
-            VHDL / "volo_common_pkg.vhd",
+            VHDL_PKG / "volo_voltage_pkg.vhd",
+            VHDL_PKG / "volo_common_pkg.vhd",
             VHDL / "volo_clk_divider.vhd",
             VHDL / "volo_voltage_threshold_trigger_core.vhd",
             VHDL / "fsm_observer.vhd",
@@ -92,7 +93,7 @@ TESTS_CONFIG = {
             VHDL / "volo_bram_loader.vhd",

             # DS1120-PD specific
-            VHDL / "ds1120_pd_pkg.vhd",
+            VHDL_PKG / "ds1120_pd_pkg.vhd",
             VHDL / "ds1120_pd_fsm.vhd",
             VHDL / "DS1120_PD_volo_main.vhd",
             VHDL / "DS1120_PD_volo_shim.vhd",
@@ -107,7 +108,7 @@ TESTS_CONFIG = {
     "fsm_example": TestConfig(
         name="fsm_example",
         sources=[
-            VHDL / "volo_voltage_pkg.vhd",
+            VHDL_PKG / "volo_voltage_pkg.vhd",
             VHDL / "fsm_observer.vhd",
         ],
         toplevel="fsm_observer",
@@ -118,7 +119,7 @@ TESTS_CONFIG = {
     "verbosity_demo": TestConfig(
         name="verbosity_demo",
         sources=[
-            VHDL / "volo_voltage_pkg.vhd",
+            VHDL_PKG / "volo_voltage_pkg.vhd",
             VHDL / "fsm_observer.vhd",
         ],
         toplevel="fsm_observer",
```

### Step 4: Validation

```bash
# Validate configuration
cd tests
python test_configs.py

# Expected output:
# ✅ All test files validated successfully!

# Run tests to verify paths work
uv run python tests/run.py volo_voltage_pkg  # Package test
uv run python tests/run.py volo_clk_divider  # Entity test
uv run python tests/run.py ds1120_pd_volo    # Integration test
```

### Step 5: Update Documentation

**File**: `CLAUDE.md` (if exists in this repo)

Add note about package organization:

```markdown
## File Organization

```
VHDL/
├── packages/          # VHDL packages (compile first)
│   ├── ds1120_pd_pkg.vhd
│   ├── volo_common_pkg.vhd
│   ├── volo_voltage_pkg.vhd
│   └── volo_lut_pkg.vhd
├── *.vhd             # VHDL entities and architectures
```

**Compilation order**: Packages → Entities → Top-level
```

### Step 6: Commit Changes

```bash
cd /Users/vmars20/EZ-EMFI

# Stage changes
git add VHDL/packages/
git add tests/test_configs.py
git add CLAUDE.md  # If updated

# Commit with descriptive message
git commit -m "refactor: Organize VHDL packages into dedicated directory

- Create VHDL/packages/ directory
- Move 3 existing packages: ds1120_pd_pkg, volo_common_pkg, volo_voltage_pkg
- Update test_configs.py to use VHDL_PKG path constant
- Improves code organization and dependency tracking

Benefits:
- Clear separation of libraries vs implementations
- Aligns with EXTERNAL_volo_vhdl structure
- Scalable for future packages (e.g., volo_lut_pkg)

Testing:
- All tests validated successfully
- volo_voltage_pkg, volo_clk_divider, ds1120_pd_volo tests pass"
```

## Impact Analysis

### Files Modified
- **tests/test_configs.py** - 8 path updates
- **CLAUDE.md** (optional) - Documentation update

### Files Moved (via git mv)
- **VHDL/ds1120_pd_pkg.vhd** → **VHDL/packages/ds1120_pd_pkg.vhd**
- **VHDL/volo_common_pkg.vhd** → **VHDL/packages/volo_common_pkg.vhd**
- **VHDL/volo_voltage_pkg.vhd** → **VHDL/packages/volo_voltage_pkg.vhd**

### No Changes Required
- VHDL entity files (unchanged)
- Test Python files (unchanged - paths abstracted in test_configs.py)
- Build system (test runner uses test_configs.py)

### Risk Assessment
**Risk**: LOW
- Git tracks file moves correctly
- All path references centralized in test_configs.py
- Validation step catches any missed updates
- No VHDL source code changes

**Rollback**: Simple `git revert` if issues found

## Success Criteria

- [ ] All 3 packages moved to `VHDL/packages/`
- [ ] Git history preserved (using `git mv`)
- [ ] `python test_configs.py` shows ✅ validation
- [ ] All tests pass: `volo_voltage_pkg`, `volo_clk_divider`, `ds1120_pd_volo`
- [ ] Clean commit with descriptive message
- [ ] Documentation updated (optional but recommended)

## Timeline

**Estimated**: 30 minutes
- Directory creation: 1 min
- File moves: 5 min
- test_configs.py update: 10 min
- Validation & testing: 10 min
- Commit: 4 min

## Next Steps (Post-Migration)

After migration is complete and tested:

1. **Add volo_lut_pkg.vhd** (see VOLO_LUT_PKG_DESIGN.md)
2. **Consider migrating EXTERNAL_volo_vhdl packages** (separate effort)
3. **Update CLAUDE.md** with package development guidelines

## Notes

- This migration sets the foundation for adding `volo_lut_pkg.vhd`
- Follows industry best practice (separate libraries from implementations)
- Minimal disruption (all changes in one commit)
- Easily reversible if issues discovered

---

**Author**: Claude Code
**Reviewed**: Pending human approval
**Approved for execution**: ⬜ (awaiting sign-off)
