# CustomInstrument Migration - Phase 4 Pickup Point

**Session Date:** 2025-10-29
**Progress:** Phases 1-3 COMPLETE (60% done)
**Token Usage:** 169k/200k (84%) - Fresh session recommended

---

## ✅ COMPLETED: Phases 1-3 (Core Infrastructure)

### Phase 1: VHDL Core Infrastructure ✓
- **Directory renamed:** `shared/volo` → `shared/custom_inst`
- **Files updated:**
  - `MCC_TOP_custom_inst_loader.vhd` - Architecture changed to `Behavioral of SimpleCustomInstrument`
    - App registers: Control6-15 (max 10, was Control20-30)
    - BRAM loader: Control1-5 (was Control10-14)
  - `custom_inst_bram_loader.vhd` - Updated to use Control1-5
  - `custom_inst_common_pkg.vhd` - APP_REG_MIN=6, APP_REG_MAX=15
  - Templates: `custom_inst_shim_template.vhd`, `custom_inst_main_template.vhd`
- **Verification:** No `CustomWrapper` or `entity volo_` references remain in shared/

### Phase 2: Python Models ✓
- **Directory renamed:** `models/volo` → `models/custom_inst`
- **Files updated:**
  - `custom_inst_app.py` (was volo_app.py)
    - Class: `VoloApp` → `CustomInstApp`
    - Max registers: 11 → 10
    - Validation: `max_length=10`
  - `app_register.py`
    - `cr_number` field: `ge=6, le=15` (was `ge=20, le=30`)
    - Validator: checks 6-15 range
  - `__init__.py` - Updated imports/exports

### Phase 3: Code Generator ✓
- **File renamed:** `tools/generate_volo_app.py` → `tools/generate_custom_inst.py`
- **Updates:**
  - Import: `from models.custom_inst import CustomInstApp`
  - All references: `volo_shim` → `custom_inst_shim`, `volo_main` → `custom_inst_main`
  - CLI help and messages updated

---

## 🎯 TODO: Phases 4-7 (Application Files & Verification)

### Phase 4: DS1140_PD Application Update

**Goal:** Migrate DS1140_PD from CR20-28 to CR6-14

#### Step 4.1: Update DS1140_PD_app.yaml
```bash
# Current register assignments (CR20-28):
# - CR20: Arm Probe (BUTTON)
# - CR21: Force Fire (BUTTON)
# - CR22: Reset FSM (BUTTON)
# - CR23: Clock Divider (COUNTER_16BIT)
# - CR24: Arm Timeout (COUNTER_16BIT)
# - CR25: Firing Duration (COUNTER_16BIT)
# - CR26: Cooling Duration (COUNTER_16BIT)
# - CR27: Trigger Threshold (COUNTER_16BIT)
# - CR28: Intensity (COUNTER_8BIT)

# NEW assignments (CR6-14) - subtract 14 from each:
# - CR6: Arm Probe
# - CR7: Force Fire
# - CR8: Reset FSM
# - CR9: Clock Divider
# - CR10: Arm Timeout
# - CR11: Firing Duration
# - CR12: Cooling Duration
# - CR13: Trigger Threshold
# - CR14: Intensity
```

**Action:**
```bash
# Edit DS1140_PD_app.yaml
# Change all cr_number: 20-28 → cr_number: 6-14
# Update comments referencing Control20-28 → Control6-14
```

#### Step 4.2: Regenerate VHDL Files
```bash
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output VHDL/ \
    --force
```

**Expected output:**
- `VHDL/DS1140_PD_custom_inst_shim.vhd` (generated)
- `VHDL/DS1140_PD_custom_inst_main.vhd` (template if doesn't exist)

#### Step 4.3: Migrate DS1140_PD Logic
**Option A:** Copy existing logic from `VHDL/DS1140_PD_volo_main.vhd` to new `DS1140_PD_custom_inst_main.vhd`
**Option B:** Start fresh with template (if logic is simple)

**Files to check:**
```bash
ls VHDL/DS1140_PD_*.vhd
# Old files (can be kept as reference):
# - DS1140_PD_volo_shim.vhd
# - DS1140_PD_volo_main.vhd
# New files (after regeneration):
# - DS1140_PD_custom_inst_shim.vhd
# - DS1140_PD_custom_inst_main.vhd
```

#### Step 4.4: Update Top-Level Loader (if needed)
Check if `VHDL/DS1140_PD_MCC_TOP.vhd` exists. If so, update to instantiate `DS1140_PD_custom_inst_shim` instead of `DS1140_PD_volo_shim`.

**Verification:**
```bash
# Compile with GHDL
ghdl -a --std=08 shared/custom_inst/custom_inst_common_pkg.vhd
ghdl -a --std=08 shared/custom_inst/custom_inst_bram_loader.vhd
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_shim.vhd
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_main.vhd
```

---

### Phase 5: Test Infrastructure Update

#### Step 5.1: Create SimpleCustomInstrument Test Stub
```bash
# Create VHDL/SimpleCustomInstrument_test_stub.vhd
# Based on VHDL/CustomWrapper_test_stub.vhd but with:
# - Entity: SimpleCustomInstrument (not CustomWrapper)
# - Control0-Control15 (16 registers, not 32)
# - InputC, OutputC (SimpleCustomInstrument has 3 I/O)
```

**Reference:**
- Check `VHDL/CustomInstrument.vhd` for exact entity definition
- SimpleCustomInstrument has Control0-15 (16 registers)
- Has InputA/B/C and OutputA/B/C

#### Step 5.2: Update tests/conftest.py
```bash
# Update DUT references:
# - Change entity from CustomWrapper → SimpleCustomInstrument
# - Update source file lists to include new stub
# - Update package includes: volo_common_pkg → custom_inst_common_pkg
```

#### Step 5.3: Update Test Files
```bash
# Find tests referencing Control20-30:
grep -r "Control2[0-9]\|Control30" tests/

# Update to use Control6-15 instead
# Update BRAM loader tests: Control10-14 → Control1-5
```

#### Step 5.4: Run Tests
```bash
uv run python tests/run.py --all
# Or specific tests:
uv run python tests/run.py volo_clk_divider
```

---

### Phase 6: Documentation Update

#### Update CLAUDE.md
```bash
# Check for references to:
# - "VoloApp" → "CustomInstApp"
# - "CustomWrapper" → "SimpleCustomInstrument"
# - "CR20-30" → "CR6-15"
# - "generate_volo_app.py" → "generate_custom_inst.py"
# - "/vhdl" slash command context (if it mentions volo specifics)
```

#### Update README.md
```bash
# Update:
# - Code generator examples
# - Register map documentation (CR6-15, not CR20-30)
# - Architecture diagrams if present
```

---

### Phase 7: Final Verification & Commit

#### Step 7.1: Comprehensive Grep
```bash
# Find remaining legacy references:
grep -r "volo" --include="*.py" --include="*.vhd" --include="*.yaml" \
    --exclude-dir=".git" --exclude-dir=".venv" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    --exclude="PHASE4_pickup_here.md" \
    . | grep -v "# OLD:" | grep -v "was volo"

grep -r "CustomWrapper" --include="*.py" --include="*.vhd" --include="*.md" \
    --exclude-dir=".git" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    --exclude="PHASE4_pickup_here.md" \
    .

grep -r "Control2[0-9]\|Control30" --include="*.py" --include="*.vhd" --include="*.yaml" \
    --exclude-dir=".git" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    --exclude="PHASE4_pickup_here.md" \
    .
```

#### Step 7.2: Final Compilation Test
```bash
# Compile all VHDL files in shared/custom_inst
ghdl -a --std=08 shared/custom_inst/*.vhd

# Compile DS1140_PD files
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_*.vhd
```

#### Step 7.3: Final Test Suite Run
```bash
uv run python tests/run.py --all
```

#### Step 7.4: Git Commit
```bash
git status
git add -A
git commit -m "$(cat <<'EOF'
feat: Complete CustomInstrument migration (Phases 1-7)

Breaking Changes:
✅ MCC entity: CustomWrapper → SimpleCustomInstrument
✅ Control registers: 32 → 16 (Control0-Control15)
✅ App registers: CR20-30 (11 max) → CR6-15 (10 max)
✅ BRAM protocol: CR10-14 → CR1-5

Core Infrastructure (Phases 1-3):
✅ Renamed shared/volo → shared/custom_inst
✅ Updated all VHDL files (loader, BRAM, package, templates)
✅ Renamed models/volo → models/custom_inst
✅ Updated Python models (CustomInstApp, validation 6-15)
✅ Renamed tools/generate_volo_app.py → generate_custom_inst.py

Application Updates (Phase 4):
✅ Updated DS1140_PD_app.yaml (CR6-14)
✅ Regenerated DS1140_PD VHDL files
✅ Migrated DS1140_PD main logic

Testing (Phase 5):
✅ Created SimpleCustomInstrument_test_stub.vhd
✅ Updated test infrastructure (conftest.py)
✅ Updated test files for new register map
✅ All CocotB tests passing

Documentation (Phase 6):
✅ Updated CLAUDE.md
✅ Updated README.md
✅ Updated slash command contexts

Verification (Phase 7):
✅ No legacy references remain
✅ All VHDL files compile
✅ All tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## 🔑 Key Migration Points

### Register Map Changes
```
OLD (CustomWrapper - 32 registers):
  CR0[31:29]: VOLO_READY control
  CR10-14:    BRAM loader (5 registers)
  CR20-30:    App registers (11 max)

NEW (SimpleCustomInstrument - 16 registers):
  CR0[31:29]: VOLO_READY control (unchanged)
  CR1-5:      BRAM loader (5 registers)
  CR6-15:     App registers (10 max)
```

### File Naming Convention
```
OLD: <AppName>_volo_shim.vhd, <AppName>_volo_main.vhd
NEW: <AppName>_custom_inst_shim.vhd, <AppName>_custom_inst_main.vhd
```

### Python Class Changes
```python
OLD: from models.volo import VoloApp
NEW: from models.custom_inst import CustomInstApp
```

---

## 📊 Migration Status

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| 1 | VHDL Infrastructure | ✅ Complete | shared/custom_inst/ |
| 2 | Python Models | ✅ Complete | models/custom_inst/ |
| 3 | Code Generator | ✅ Complete | tools/generate_custom_inst.py |
| 4 | DS1140_PD App | ⏳ Pending | Update YAML, regenerate |
| 5 | Test Infrastructure | ⏳ Pending | New stub, update tests |
| 6 | Documentation | ⏳ Pending | CLAUDE.md, README.md |
| 7 | Final Verification | ⏳ Pending | Grep, compile, commit |

**Estimated Time Remaining:** 1-2 hours

---

## 🚀 Quick Start Next Session

```bash
# 1. Check git status (should see Phase 1-3 changes)
git status

# 2. Edit DS1140_PD_app.yaml
vim DS1140_PD_app.yaml
# Change: cr_number: 20-28 → cr_number: 6-14

# 3. Regenerate VHDL
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output VHDL/ \
    --force

# 4. Continue with Phase 5 (tests) following steps above
```

---

## 🐛 Known Issues / Gotchas

1. **Pydantic Import:** Python imports won't work outside `uv run` environment
2. **GHDL Order:** Must compile package before loader/shim
3. **Template Overwrite:** Use `--force` flag to regenerate main template
4. **CR Number Math:** Subtract 14 from old CR numbers (CR20 → CR6, CR30 → CR15 would be out of range)

---

## 📁 Files Modified (Phases 1-3)

### VHDL (shared/custom_inst/)
- MCC_TOP_custom_inst_loader.vhd
- custom_inst_bram_loader.vhd
- custom_inst_common_pkg.vhd
- templates/custom_inst_shim_template.vhd
- templates/custom_inst_main_template.vhd

### Python (models/custom_inst/)
- custom_inst_app.py
- app_register.py
- __init__.py

### Tools
- tools/generate_custom_inst.py

---

**Next Session Prompt:**
> "Continue the CustomInstrument migration from Phase 4. The handoff doc is at `docs/session_handoffs/PHASE4_pickup_here.md`. Start by updating DS1140_PD_app.yaml register numbers from CR20-28 to CR6-14."
