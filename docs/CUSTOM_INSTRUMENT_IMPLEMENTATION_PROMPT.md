# CustomInstrument Migration Implementation Prompt

**Purpose**: This document provides a copy-paste prompt for Claude Code to execute the CustomInstrument migration.

**Usage**: Copy the prompt below and paste it into a new Claude Code session to execute the migration plan step-by-step.

---

## Implementation Prompt

```
Claude, I need you to execute the CustomInstrument migration plan documented in docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md.

## Context

We're migrating from MCC's CustomWrapper entity (32 control registers) to SimpleCustomInstrument entity (16 control registers). This is a breaking change that requires updating:

1. VHDL shared components (rename volo → custom_inst)
2. Python models (VoloApp → CustomInstApp, register validation)
3. Code generator tool (generate_volo_app.py → generate_custom_inst.py)
4. Register allocation (Control20-30 → Control6-15 for app registers)
5. BRAM loader (Control10-14 → Control1-5)

## Migration Decisions (Already Made)

- **Register Map**: Control0 (VOLO_READY), Control1-5 (BRAM), Control6-15 (app regs, max 10)
- **Architecture**: Keep 3-layer (Loader → Shim → Main)
- **Naming**: Rename all 'volo' → 'custom_inst'
- **Compatibility**: Clean break - no backward compatibility

## Your Task

Execute the migration in phases using the detailed checklist in docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md.

### Phase 1: Core Infrastructure (Shared VHDL Components)

**Step 1.1**: Rename directory
- Use Bash to: `mv shared/volo shared/custom_inst`
- Verify with: `ls shared/custom_inst`

**Step 1.2**: Update MCC_TOP_custom_inst_loader.vhd (was MCC_TOP_volo_loader.vhd)
- Read the current file: shared/custom_inst/MCC_TOP_volo_loader.vhd
- Update entity declaration:
  - Change: `architecture volo_loader of CustomWrapper` → `architecture Behavioral of SimpleCustomInstrument`
  - Note: The entity SimpleCustomInstrument is now defined in the new VHDL/CustomInstrument.vhd file
- Update BRAM loader instantiation:
  - Change port map: Control10-14 → Control1-5
  - Update entity name: `volo_bram_loader` → `custom_inst_bram_loader`
- Update app register signal declarations:
  - Change: `signal app_reg_20..app_reg_30` → `signal app_reg_6..app_reg_15`
- Update app register mapping:
  - Change: `app_reg_20 <= Control20;` → `app_reg_6 <= Control6;`
  - Continue for all registers through app_reg_15 <= Control15
  - Remove mappings for app_reg_16 through app_reg_30 (no longer exist)
- Update shim instantiation:
  - Change entity name: `<AppName>_volo_shim` → `<AppName>_custom_inst_shim`
  - Update port map: app_reg_20..28 → app_reg_6..14
- Save renamed file as: shared/custom_inst/MCC_TOP_custom_inst_loader.vhd

**Step 1.3**: Update custom_inst_bram_loader.vhd (was volo_bram_loader.vhd)
- Read: shared/custom_inst/volo_bram_loader.vhd
- Update entity name: `volo_bram_loader` → `custom_inst_bram_loader`
- Update port declarations:
  - Change: Control10, Control11, Control12, Control13, Control14
  - To: Control1, Control2, Control3, Control4, Control5
- Update signal extraction:
  - Change: `start_loading <= Control10(0);` → `start_loading <= Control1(0);`
  - Change: `word_count <= unsigned(Control10(31 downto 16));` → `word_count <= unsigned(Control1(31 downto 16));`
  - Change: `write_strobe <= Control13(0);` → `write_strobe <= Control4(0);`
  - Change: `bram_addr <= Control11(11 downto 0);` → `bram_addr <= Control2(11 downto 0);`
  - Change: `bram_data <= Control12;` → `bram_data <= Control3;`
- Update documentation comments to reference Control1-5 instead of Control10-14
- Save renamed file as: shared/custom_inst/custom_inst_bram_loader.vhd

**Step 1.4**: Update custom_inst_common_pkg.vhd (was volo_common_pkg.vhd)
- Read: shared/custom_inst/volo_common_pkg.vhd
- Update package name: `volo_common_pkg` → `custom_inst_common_pkg`
- Update header comments:
  - Change: "VoloApp Common Package" → "CustomInstrument Common Package"
  - Change: "volo-app infrastructure" → "custom_inst infrastructure"
- Update BRAM protocol comments:
  - Change references from Control10-14 → Control1-5
- Update app register comments:
  - Change references from CR20-30 → CR6-15
- Save renamed file as: shared/custom_inst/custom_inst_common_pkg.vhd

**Step 1.5**: Update templates
- Read: shared/custom_inst/templates/volo_shim_template.vhd
- Update comments:
  - Change: "from CustomWrapper" → "from SimpleCustomInstrument"
  - Change: "Raw Control Registers CR20-CR30" → "Raw Control Registers CR6-CR15"
  - Change: "MCC_TOP_volo_loader" → "MCC_TOP_custom_inst_loader"
- Update entity instantiation comment:
  - Change: `{{ app_name }}_volo_main` → `{{ app_name }}_custom_inst_main`
- Save renamed file as: shared/custom_inst/templates/custom_inst_shim_template.vhd
- Read: shared/custom_inst/templates/volo_main_template.vhd
- Update header comments to reference custom_inst instead of volo
- Save renamed file as: shared/custom_inst/templates/custom_inst_main_template.vhd
- Remove old volo_*.vhd template files

**Verification**: After Phase 1, run:
```bash
# Verify directory structure
ls -la shared/custom_inst/
ls -la shared/custom_inst/templates/

# Verify no 'CustomWrapper' references remain
grep -r "CustomWrapper" shared/custom_inst/ || echo "✓ No CustomWrapper references"

# Verify no 'volo' entity names remain (except in comments)
grep -r "entity volo_" shared/custom_inst/ || echo "✓ No volo entity names"

# Verify BRAM loader uses Control1-5
grep "Control1" shared/custom_inst/custom_inst_bram_loader.vhd
```

---

### Phase 2: Python Models

**Step 2.1**: Rename directory
- Use Bash to: `mv models/volo models/custom_inst`
- Verify with: `ls models/custom_inst`

**Step 2.2**: Update custom_inst_app.py (was volo_app.py)
- Read: models/custom_inst/volo_app.py
- Update class name: `class VoloApp(BaseModel):` → `class CustomInstApp(BaseModel):`
- Update docstrings:
  - Module docstring: "VoloApp Model" → "CustomInstApp Model"
  - Class docstring: References to "VoloApp" → "CustomInstApp"
  - Architecture comments: "CustomWrapper" → "SimpleCustomInstrument"
  - Architecture comments: "CR20-CR30" → "CR6-CR15"
- Update register validation:
  - Change: `max_length=11` → `max_length=10`
  - Change validator message: "Maximum 11 registers allowed (got {len(v)})" → "Maximum 10 registers allowed (got {len(v)})"
  - Change validator comment: "(CR20-CR30)" → "(CR6-CR15)"
- Update template paths:
  - Change: `"shared" / "volo" / "templates" / "volo_shim_template.vhd"`
  - To: `"shared" / "custom_inst" / "templates" / "custom_inst_shim_template.vhd"`
  - Same for main template
- Update generated file naming in generate_vhdl_shim() and generate_vhdl_main_template():
  - Comments referencing "_volo_shim.vhd" → "_custom_inst_shim.vhd"
  - Comments referencing "_volo_main.vhd" → "_custom_inst_main.vhd"
- Update all method docstrings that reference volo or CustomWrapper
- Save renamed file as: models/custom_inst/custom_inst_app.py

**Step 2.3**: Update app_register.py
- Read: models/custom_inst/app_register.py
- Update cr_number field:
  - Change: `cr_number: int = Field(..., ge=20, le=30)` → `cr_number: int = Field(..., ge=6, le=15)`
- Update cr_number validator:
  - Change: `if not (20 <= v <= 30):` → `if not (6 <= v <= 15):`
  - Change: `raise ValueError(f"cr_number must be 20-30 (got {v})")` → `raise ValueError(f"cr_number must be 6-15 (got {v})")`
  - Change validator docstring: "(20-30)" → "(6-15)"
- Update class docstring:
  - Change: "VoloApp interface" → "CustomInstApp interface"
  - Change: "(CR20-CR30)" → "(CR6-CR15)"
  - Change: "must be 20-30 inclusive" → "must be 6-15 inclusive"
- Update module docstring if it references volo

**Step 2.4**: Update __init__.py
- Read: models/custom_inst/__init__.py
- Update import:
  - Change: `from .volo_app import VoloApp` → `from .custom_inst_app import CustomInstApp`
- Update __all__:
  - Change: `__all__ = ['VoloApp', 'AppRegister', 'RegisterType']`
  - To: `__all__ = ['CustomInstApp', 'AppRegister', 'RegisterType']`
- Update module docstring:
  - Change: "VoloApp models" → "CustomInstApp models"

**Verification**: After Phase 2, run:
```bash
# Verify directory structure
ls -la models/custom_inst/

# Verify no 'VoloApp' class references remain
grep -r "class VoloApp" models/custom_inst/ || echo "✓ No VoloApp class"

# Verify cr_number validation is 6-15
grep "ge=6, le=15" models/custom_inst/app_register.py

# Verify max registers is 10
grep "max_length=10" models/custom_inst/custom_inst_app.py

# Test import
python -c "from models.custom_inst import CustomInstApp; print('✓ Import successful')"
```

---

### Phase 3: Code Generator Tool

**Step 3.1**: Rename file
- Use Bash to: `mv tools/generate_volo_app.py tools/generate_custom_inst.py`
- Verify with: `ls tools/generate_custom_inst.py`

**Step 3.2**: Update imports and references
- Read: tools/generate_custom_inst.py
- Update import:
  - Change: `from models.volo import VoloApp` → `from models.custom_inst import CustomInstApp`
- Update variable usage:
  - Change all: `VoloApp.load_from_yaml()` → `CustomInstApp.load_from_yaml()`
  - Change all: `app: VoloApp` → `app: CustomInstApp`
- Update banner in print_banner():
  - Change: "[bold cyan]VoloApp Code Generator[/bold cyan]"
  - To: "[bold cyan]CustomInstrument Code Generator[/bold cyan]"
  - Change: "Generate VHDL shim and main template from VoloApp definition"
  - To: "Generate VHDL shim and main template from CustomInstApp definition"
- Update console messages:
  - Change: "Loading VoloApp from" → "Loading CustomInstApp from"
- Update CLI help text:
  - Change: "Generate VoloApp VHDL files" → "Generate CustomInstApp VHDL files"
- Update examples in epilog:
  - Change all references to "generate_volo_app.py" → "generate_custom_inst.py"
  - Update output directory examples if they reference "volo_main/" → "custom_inst_main/"
- Update module docstring:
  - Change: "VoloApp Code Generator" → "CustomInstrument Code Generator"
  - Change: "VoloApp YAML definition" → "CustomInstApp YAML definition"

**Verification**: After Phase 3, run:
```bash
# Verify file renamed
ls tools/generate_custom_inst.py

# Verify no VoloApp imports
grep "from models.volo" tools/generate_custom_inst.py && echo "✗ Still importing from models.volo" || echo "✓ No volo imports"

# Verify CustomInstApp import
grep "from models.custom_inst import CustomInstApp" tools/generate_custom_inst.py

# Test CLI help
python tools/generate_custom_inst.py --help | grep "CustomInstApp"
```

---

### Phase 4: Application Files (DS1140_PD Example)

**Step 4.1**: Update DS1140_PD_app.yaml
- Read: DS1140_PD_app.yaml
- Update register cr_number fields:
  - Register 0 "Arm Probe": cr_number: 20 → cr_number: 6
  - Register 1 "Force Fire": cr_number: 21 → cr_number: 7
  - Register 2 "Reset FSM": cr_number: 22 → cr_number: 8
  - Register 3 "Clock Divider": cr_number: 23 → cr_number: 9
  - Register 4 "Arm Timeout": cr_number: 24 → cr_number: 10
  - Register 5 "Firing Duration": cr_number: 25 → cr_number: 11
  - Register 6 "Cooling Duration": cr_number: 26 → cr_number: 12
  - Register 7 "Trigger Threshold": cr_number: 27 → cr_number: 13
  - Register 8 "Intensity": cr_number: 28 → cr_number: 14
- Update comments in YAML:
  - Change: "Control Registers (Control20-Control28)" → "Control Registers (Control6-Control14)"
  - Change: "CR20-CR28" references → "CR6-CR14"
  - Change: "app_reg_20..28" → "app_reg_6..14"
  - Change: "Control20-Control28" in bit packing → "Control6-Control14"
  - Change: "MCC CustomWrapper only provides Control0-Control15" note
- Update generated signal name comments:
  - Change: "app_reg_20(31)" → "app_reg_6(31)" for Arm Probe
  - Continue for all registers

**Step 4.2**: Regenerate DS1140_PD VHDL files
- Run code generator with updated YAML:
  ```bash
  python tools/generate_custom_inst.py \
      --config DS1140_PD_app.yaml \
      --output VHDL/ \
      --force
  ```
- Verify generated files:
  - `VHDL/DS1140_PD_custom_inst_shim.vhd` (new)
  - `VHDL/DS1140_PD_custom_inst_main.vhd` (new)
- Read generated shim and verify:
  - Uses `app_reg_6` through `app_reg_14`
  - Instantiates `DS1140_PD_custom_inst_main`
  - References `custom_inst_common_pkg`

**Step 4.3**: Migrate existing DS1140_PD main logic
- Option A: Copy existing logic from VHDL/DS1140_PD_volo_main.vhd to new file
- Option B: Let code generator create fresh template and re-implement
- Recommendation: Option A if logic is complex, Option B if starting fresh

**Step 4.4**: Update or create MCC_TOP loader for DS1140_PD
- Create: VHDL/DS1140_PD_MCC_TOP.vhd
- Copy from: shared/custom_inst/MCC_TOP_custom_inst_loader.vhd
- Update shim instantiation to use "DS1140_PD_custom_inst_shim"
- Ensure port map passes app_reg_6 through app_reg_14 (DS1140_PD uses 9 registers)

**Verification**: After Phase 4, run:
```bash
# Verify YAML updated
grep "cr_number: 6" DS1140_PD_app.yaml

# Verify generated files exist
ls VHDL/DS1140_PD_custom_inst_shim.vhd
ls VHDL/DS1140_PD_custom_inst_main.vhd

# Verify files compile with GHDL
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_shim.vhd
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_main.vhd
```

---

### Phase 5: Testing Infrastructure

**Step 5.1**: Create CustomInstrument test stub
- Read: VHDL/CustomWrapper_test_stub.vhd (for reference)
- Create new: VHDL/SimpleCustomInstrument_test_stub.vhd
- Define entity SimpleCustomInstrument with:
  - Clk, Reset
  - InputA, InputB, InputC : in signed(15 downto 0)
  - OutputA, OutputB, OutputC : out signed(15 downto 0)
  - Control0 through Control15 : in std_logic_vector(31 downto 0)
- Create simple behavioral architecture (pass-through or loopback for testing)

**Step 5.2**: Update CocotB test configuration
- Read: tests/conftest.py
- Update DUT references:
  - If using CustomWrapper stub, change to SimpleCustomInstrument
  - Update source file lists to include new stub
- Update VHDL source paths:
  - Change references from shared/volo → shared/custom_inst
  - Update package includes: volo_common_pkg → custom_inst_common_pkg

**Step 5.3**: Update test files
- Identify tests that reference Control20-30:
  ```bash
  grep -r "Control2[0-9]" tests/
  grep -r "Control30" tests/
  ```
- Update test files to use Control6-15 instead
- Update BRAM loader tests to use Control1-5 instead of Control10-14

**Step 5.4**: Run tests
```bash
# Run all tests
uv run python tests/run.py --all

# Or run specific test modules
uv run python tests/run.py volo_clk_divider
uv run python tests/run.py ds1140_pd_volo_progressive
```

**Verification**: After Phase 5, tests should pass

---

### Phase 6: Documentation

**Step 6.1**: Update CLAUDE.md
- Read: CLAUDE.md
- Update references:
  - "VoloApp" → "CustomInstApp"
  - "CustomWrapper" → "SimpleCustomInstrument"
  - "/vhdl" slash command context (if it mentions volo specifics)
  - Update register allocation documentation if present
- Update examples that reference generate_volo_app.py → generate_custom_inst.py

**Step 6.2**: Update README.md
- Read: README.md
- Update code generator examples
- Update register map documentation
- Update architecture diagrams if present

**Step 6.3**: Update reference documentation
- Check for docs that reference:
  - VOLO_APP_DESIGN.md
  - VOLO_APP_FRESH_CONTEXT.md
- Either update these docs or mark them as legacy
- Update architecture diagrams

**Step 6.4**: Create migration record (already done in CUSTOM_INSTRUMENT_MIGRATION_PLAN.md)

**Verification**: After Phase 6, run:
```bash
# Check for remaining volo references in docs
grep -r "VoloApp" docs/ CLAUDE.md README.md

# Check for CustomWrapper references
grep -r "CustomWrapper" docs/ CLAUDE.md README.md
```

---

### Phase 7: Cleanup and Final Verification

**Step 7.1**: Comprehensive grep for legacy terms
```bash
# Find remaining 'volo' references (excluding historical docs and this migration plan)
grep -r "volo" --include="*.py" --include="*.vhd" --include="*.yaml" \
    --exclude-dir=".git" --exclude-dir=".venv" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    . | grep -v "# OLD:" | grep -v "was volo"

# Find remaining CustomWrapper references
grep -r "CustomWrapper" --include="*.py" --include="*.vhd" --include="*.md" \
    --exclude-dir=".git" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    .

# Find Control20-30 references
grep -r "Control2[0-9]\|Control30" --include="*.py" --include="*.vhd" --include="*.yaml" \
    --exclude-dir=".git" \
    --exclude="CUSTOM_INSTRUMENT_MIGRATION_PLAN.md" \
    .
```

**Step 7.2**: Update .gitignore if needed
- Check if any new file patterns need exclusion

**Step 7.3**: Final compilation test
```bash
# Compile all VHDL files in shared/custom_inst
ghdl -a --std=08 shared/custom_inst/*.vhd

# Compile DS1140_PD files
ghdl -a --std=08 VHDL/DS1140_PD_custom_inst_*.vhd
```

**Step 7.4**: Final test suite run
```bash
# Run full test suite
uv run python tests/run.py --all
```

**Step 7.5**: Git status check
```bash
# Review all changes
git status

# Review diff
git diff HEAD

# Expected changes:
# - shared/volo → shared/custom_inst (renamed directory)
# - models/volo → models/custom_inst (renamed directory)
# - tools/generate_volo_app.py → tools/generate_custom_inst.py (renamed file)
# - DS1140_PD_app.yaml (modified, cr_number changes)
# - VHDL/DS1140_PD_custom_inst_shim.vhd (new/regenerated)
# - VHDL/DS1140_PD_custom_inst_main.vhd (new/regenerated)
# - Various documentation updates
# - New test stub: VHDL/SimpleCustomInstrument_test_stub.vhd
```

---

## Success Criteria Checklist

After completing all phases, verify:

- [ ] All files renamed from `volo` → `custom_inst`
- [ ] Entity changed from `CustomWrapper` → `SimpleCustomInstrument`
- [ ] Register map updated: Control0 (VOLO), Control1-5 (BRAM), Control6-15 (app)
- [ ] Python models support max 10 app registers with CR6-15 range
- [ ] Code generator creates `_custom_inst_shim.vhd` and `_custom_inst_main.vhd` files
- [ ] DS1140_PD successfully regenerated with new architecture
- [ ] All VHDL files compile with GHDL
- [ ] All CocotB tests pass
- [ ] Documentation updated to reflect new naming and architecture
- [ ] No references to legacy "volo" or "CustomWrapper" (except in historical docs)

---

## Important Notes for Implementation

1. **Work incrementally**: Complete each phase fully before moving to the next
2. **Test frequently**: After each major change, verify compilation and run tests
3. **Use TodoWrite**: Track progress with the TodoWrite tool for visibility
4. **Commit strategically**: Consider committing after each phase for easy rollback
5. **Preserve history**: Don't delete old files until new files are verified working
6. **Ask questions**: If anything is ambiguous, ask for clarification

---

## Rollback Strategy

If issues arise during migration:

1. **Git reset**: Use `git reset --hard HEAD` to revert uncommitted changes
2. **Branch reset**: Use `git reset --hard origin/feature/CustomInstrument` to revert to remote state
3. **Selective revert**: Use `git checkout HEAD -- <file>` to revert specific files
4. **Stash changes**: Use `git stash` to temporarily save work in progress

---

## Post-Migration Tasks

After successful migration:

1. Update any CI/CD pipelines that reference old file names
2. Update any deployment scripts that use `generate_volo_app.py`
3. Consider creating a "migration complete" commit message documenting the changes
4. Update project README with new quick start guide
5. Archive or update legacy documentation

---

**End of Implementation Prompt**
```

---

## How to Use This Prompt

1. **Copy the entire prompt** from the code block above
2. **Paste into Claude Code** in a fresh session
3. **Let Claude execute** the migration step-by-step, tracking progress with TodoWrite
4. **Review each phase** before moving to the next
5. **Test frequently** to catch issues early

---

## Expected Execution Time

- **With Claude Code**: 2-4 hours (automated execution with verification)
- **Manual execution**: 8-11 hours (as estimated in migration plan)

---

**Document Version**: 1.0
**Created**: 2025-10-29
**Companion Document**: CUSTOM_INSTRUMENT_MIGRATION_PLAN.md
