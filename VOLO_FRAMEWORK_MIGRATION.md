# VoloApp Framework Migration - Phase 1 Complete

**Date**: 2025-10-27
**Status**: Phase 1 Complete ✓

---

## What Was Done

Successfully migrated the VoloApp framework from `volo_vhdl_external_/` into EZ-EMFI project.

### Files Copied

#### 1. Pydantic Models (`models/volo/`)
- `__init__.py` - Package initialization
- `app_register.py` - Register type system (RegisterType, AppRegister)
- `volo_app.py` - VoloApp model with VHDL generation

**Purpose**: Python infrastructure for defining VoloApps in YAML and generating VHDL

#### 2. VHDL Infrastructure (`shared/volo/`)
- `volo_common_pkg.vhd` - Common constants (VOLO_READY bits, register ranges)
- `volo_bram_loader.vhd` - BRAM loading FSM (CR10-CR14 protocol)
- `MCC_TOP_volo_loader.vhd` - Layer 1 CustomWrapper architecture (static, shared)
- `templates/volo_shim_template.vhd` - Jinja2 template for shim generation
- `templates/volo_main_template.vhd` - Jinja2 template for main skeleton

**Purpose**: VHDL components for 3-layer VoloApp architecture

#### 3. Generation Tool (`tools/`)
- `generate_volo_app.py` - CLI tool for generating VHDL from YAML

**Purpose**: Automates shim layer generation and main template creation

#### 4. Configuration (`./`)
- `DS1120-PD_app.yaml` - Complete DS1120-PD VoloApp definition (11 registers)

**Purpose**: Single source of truth for DS1120-PD interface

### Dependencies Added

Updated `pyproject.toml` with:
- `pydantic >=2.0.0` - Data validation and model definition
- `jinja2 >=3.0.0` - Template rendering
- `pyyaml >=6.0.0` - YAML parsing
- `rich >=13.0.0` - Fancy console output

All dependencies installed successfully with `uv sync`.

---

## Testing Results

### ✓ YAML Loading
```bash
uv run python -c "from models.volo import VoloApp; VoloApp.load_from_yaml('DS1120-PD_app.yaml')"
# Result: Successfully loaded DS1120-PD v1.0.0 with 11 registers
```

### ✓ VHDL Generation
```bash
uv run python tools/generate_volo_app.py --config DS1120-PD_app.yaml --output test_gen/
# Result: Generated shim (9.2KB) and main template (9.2KB) successfully
```

### ✓ Framework Integration
- Pydantic models import correctly
- Jinja2 templates render without errors
- Generated VHDL has proper headers and structure
- All 11 registers mapped correctly (CR20-CR30)

---

## Current Project Structure

```
EZ-EMFI/
├── models/
│   └── volo/                           # NEW: Pydantic models
│       ├── __init__.py
│       ├── app_register.py
│       └── volo_app.py
│
├── shared/
│   └── volo/                           # NEW: VoloApp VHDL infrastructure
│       ├── MCC_TOP_volo_loader.vhd
│       ├── volo_bram_loader.vhd
│       ├── volo_common_pkg.vhd
│       └── templates/
│           ├── volo_shim_template.vhd
│           └── volo_main_template.vhd
│
├── tools/
│   └── generate_volo_app.py           # NEW: Code generation tool
│
├── VHDL/                               # EXISTING: Current DS1120-PD files
│   ├── DS1120_PD_volo_main.vhd        #   (hand-written, from volo_vhdl)
│   ├── DS1120_PD_volo_shim.vhd        #   (generated, from volo_vhdl)
│   ├── ds1120_pd_fsm.vhd
│   ├── ds1120_pd_pkg.vhd
│   ├── volo_clk_divider.vhd
│   ├── volo_voltage_pkg.vhd
│   └── ... (other utility modules)
│
├── DS1120-PD_app.yaml                 # NEW: VoloApp definition
├── pyproject.toml                     # UPDATED: Added dependencies
└── uv.lock                            # UPDATED: Locked dependencies
```

---

## What's Different from volo_vhdl_external_

### Simplified Structure
- No `modules/DS1120-PD/` directory yet (keeping flat for now)
- DS1120-PD_app.yaml at root (not in module subdirectory)
- Existing VHDL files remain in `VHDL/` (not moved to `modules/`)

### Dependencies Only
- Did NOT copy: test files, documentation, example apps
- Did NOT copy: other shared modules (volo_clk_divider, etc. already exist in VHDL/)
- Did NOT copy: build scripts (will integrate later)

---

## Phase 2: Next Steps

### 1. Verify Existing Files Match Generated Output

**Goal**: Ensure current `VHDL/DS1120_PD_volo_shim.vhd` matches what framework generates

**Task**:
```bash
# Generate fresh copy
uv run python tools/generate_volo_app.py \
    --config DS1120-PD_app.yaml \
    --output VHDL_new/

# Compare with existing
diff VHDL/DS1120_PD_volo_shim.vhd VHDL_new/DS1120-PD_volo_shim.vhd
```

**Questions**:
- Are there differences?
- Is the existing file hand-edited or purely generated?
- Should we regenerate or keep existing?

### 2. Create CustomWrapper Top File

**Goal**: Implement Layer 1 (MCC_TOP) for DS1120-PD

**Current Problem**:
- We have Layer 2 (shim) and Layer 3 (main) in `VHDL/`
- Missing Layer 1 that implements `CustomWrapper` architecture

**Options**:

**Option A**: Copy `MCC_TOP_volo_loader.vhd` and customize
```bash
# Create Top.vhd that instantiates DS1120-PD_volo_shim
cp shared/volo/MCC_TOP_volo_loader.vhd VHDL/Top.vhd
# Edit line 140-167 to uncomment DS1120-PD shim instantiation
```

**Option B**: Create from DCSequencer pattern
```vhdl
-- VHDL/Top.vhd
architecture DS1120_PD of CustomWrapper is
begin
    -- Instantiate volo_bram_loader
    -- Instantiate DS1120_PD_volo_shim
end architecture;
```

### 3. Test with CocotB

**Goal**: Verify 3-layer architecture works in simulation

**Task**:
```bash
# Add CustomWrapper stub to test
cp DCSequencer/CustomWrapper_test_stub.vhd VHDL/

# Run existing DS1120-PD tests
uv run python tests/run.py ds1120_pd
```

**Expected Result**: All tests pass with new top-level structure

### 4. Update Build System

**Goal**: Package VoloApp for MCC CloudCompile

**Tasks**:
- Update `scripts/build_mcc_package.py` (if it exists)
- Include all 3 layers + utilities in package
- Generate deployment .tar file

### 5. Create Documentation

**Goal**: Document VoloApp usage for EZ-EMFI

**Files to Create**:
- `outside_docs_helpme/VOLOAPP_QUICKSTART.md` - How to use framework
- Update `CLAUDE.md` - Add VoloApp architecture section
- Update `README.md` - Mention VoloApp pattern

---

## Key Design Decisions

### Why Phase 1 Only?

**Conservative approach**: Migrate framework first, verify it works, THEN reorganize

**Benefits**:
- Can test each step
- Easy to roll back if problems
- Understand framework before restructuring

### Why Not Move VHDL/ Files Yet?

**Risk management**:
- Current files work
- Don't know if they're hand-edited
- Framework may generate slightly different output

**Better approach**: Generate fresh, compare, then decide

### Why DS1120-PD_app.yaml at Root?

**Simplicity**:
- Easy to find for testing
- Not committed to directory structure yet
- Can move to `modules/DS1120-PD/` later

---

## Questions for Next Session

1. **Existing files**: Should we trust them or regenerate?
2. **Top.vhd**: Option A (copy MCC_TOP) or Option B (minimal wrapper)?
3. **Directory structure**: When to reorganize into `modules/DS1120-PD/`?
4. **Shared utilities**: When to migrate other volo_* modules from volo_vhdl_external_?
5. **Testing**: Run tests before or after creating Top.vhd?

---

## Success Criteria (Phase 1)

- [x] Pydantic models import without errors
- [x] YAML config loads successfully
- [x] VHDL generation produces valid output
- [x] Dependencies installed and locked
- [x] Generation tool runs with `--help`
- [x] Test generation completes successfully
- [x] Documentation created

**Phase 1 Status**: ✓ COMPLETE

**Ready for Phase 2**: Yes! Framework is functional and tested.

---

## Useful Commands

```bash
# Load and inspect app config
uv run python -c "from models.volo import VoloApp; from pathlib import Path; \
    app = VoloApp.load_from_yaml(Path('DS1120-PD_app.yaml')); \
    print(f'{app.name} v{app.version}: {len(app.registers)} registers')"

# Generate VHDL files
uv run python tools/generate_volo_app.py \
    --config DS1120-PD_app.yaml \
    --output <target_dir>/

# Test framework integration
uv run pytest tests/models/ -v  # (if model tests were copied)
```

---

## References

- `volo_vhdl_external_/` - Source of framework files
- `outside_docs_helpme/VOLO_APP_DESIGN.md` - Architecture documentation (from attachments)
- `outside_docs_helpme/VOLO_APP_FRESH_CONTEXT.md` - Implementation guide (from attachments)
- `DCSequencer/` - Simple 2-layer CustomWrapper reference
