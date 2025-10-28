# Migration Plan: Package Reorganization

**Goal**: Move packages to `VHDL/packages/` directory

## Quick Migration (10 minutes)

### Step 1: Create Directory
```bash
cd /Users/vmars20/EZ-EMFI/VHDL
mkdir -p packages
```

### Step 2: Move Packages (git mv preserves history)
```bash
git mv ds1120_pd_pkg.vhd packages/
git mv volo_common_pkg.vhd packages/
git mv volo_voltage_pkg.vhd packages/
```

### Step 3: Update test_configs.py

Add line 21:
```python
VHDL_PKG = VHDL / "packages"  # NEW
```

Replace 8 occurrences (lines 55, 66-67, 87-88, 95, 110, 123):
```python
# Before: VHDL / "volo_voltage_pkg.vhd"
# After:  VHDL_PKG / "volo_voltage_pkg.vhd"
```

### Step 4: Validate
```bash
cd tests
python test_configs.py  # Should show: ✅ All test files validated

# Run tests
uv run python run.py volo_voltage_pkg
uv run python run.py volo_clk_divider
uv run python run.py ds1120_pd_volo
```

### Step 5: Commit
```bash
git add tests/test_configs.py
git commit -m "refactor: Organize VHDL packages into dedicated directory

- Create VHDL/packages/ directory
- Move 3 packages: ds1120_pd_pkg, volo_common_pkg, volo_voltage_pkg
- Update test_configs.py paths

Testing: All tests pass (validated)"
```

## Result

```
VHDL/
├── packages/               # NEW
│   ├── ds1120_pd_pkg.vhd
│   ├── volo_common_pkg.vhd
│   ├── volo_voltage_pkg.vhd
│   └── volo_lut_pkg.vhd   # Already here!
└── *.vhd                   # Entities (unchanged)
```

## Rollback (if needed)
```bash
git revert HEAD
```

---
**Effort**: 10 minutes | **Risk**: LOW | **Status**: Ready to execute
