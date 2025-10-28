# EZ-EMFI Phase 2: Create CustomWrapper Top Layer

**Context**: I just completed Phase 1 (VoloApp framework migration). Now I need to create the top-level CustomWrapper architecture for DS1120-PD.

---

## Quick Situation Report

### What Was Done (Phase 1)
- ✅ Migrated complete VoloApp framework from volo_vhdl_external_
- ✅ Python models working (models/volo/)
- ✅ VHDL infrastructure ready (shared/volo/)
- ✅ Generation tool functional (tools/generate_volo_app.py)
- ✅ Compared existing files with generated output
- ✅ Everything committed to main branch

### Current Status
We have Layers 2 & 3 of the VoloApp architecture, but missing Layer 1:
- ❌ **Layer 1**: Top.vhd (CustomWrapper architecture) - **NEEDS CREATION**
- ✅ **Layer 2**: DS1120_PD_volo_shim.vhd (register mapping, generated)
- ✅ **Layer 3**: DS1120_PD_volo_main.vhd (application logic, hand-written)

### Critical Issue Found
**Naming convention mismatch**:
- YAML config has: `name: DS1120-PD` (with hyphen)
- VHDL needs: `DS1120_PD` (with underscore)
- **MUST FIX FIRST** before proceeding

---

## What I Need You To Do

### Phase 2 Tasks (in order):

**Task 1: Fix Naming Convention** (5 minutes) - **START HERE**
```bash
cd /Users/vmars20/EZ-EMFI

# Fix the YAML
sed -i '' 's/name: DS1120-PD/name: DS1120_PD/' DS1120-PD_app.yaml
mv DS1120-PD_app.yaml DS1120_PD_app.yaml

# Verify it works
uv run python tools/generate_volo_app.py \
    --config DS1120_PD_app.yaml \
    --output test_verify/

# Compare with existing (should only differ by timestamp)
diff VHDL/DS1120_PD_volo_shim.vhd test_verify/DS1120_PD_volo_shim.vhd

# Clean up
rm -rf test_verify/

# Commit the fix
git add DS1120_PD_app.yaml
git rm DS1120-PD_app.yaml
git commit -m "fix: Use underscore in app name for VHDL compatibility"
```

**Task 2: Create Top.vhd (Layer 1)** (30 minutes)

Copy the template and customize:
```bash
cd /Users/vmars20/EZ-EMFI

# Copy template
cp shared/volo/MCC_TOP_volo_loader.vhd VHDL/Top.vhd
```

Then edit `VHDL/Top.vhd`:
1. Go to lines 133-173 (the APP_SHIM_INST section)
2. Uncomment the example instantiation
3. Change entity name to: `DS1120_PD_volo_shim` (with underscore)
4. Make sure all 11 app_reg_XX ports are mapped (CR20-CR30)
5. Remove the placeholder pass-through on lines 172-173

Key port mappings to verify:
```vhdl
APP_SHIM_INST: entity WORK.DS1120_PD_volo_shim
    port map (
        Clk         => Clk,
        Reset       => Reset,
        volo_ready  => volo_ready,
        user_enable => user_enable,
        clk_enable  => clk_enable,
        loader_done => loader_done,
        app_reg_20  => app_reg_20,
        app_reg_21  => app_reg_21,
        -- ... through app_reg_30
        bram_addr   => bram_addr,
        bram_data   => bram_data,
        bram_we     => bram_we,
        InputA      => InputA,
        InputB      => InputB,
        OutputA     => OutputA,
        OutputB     => OutputB
    );
```

**Task 3: Add CustomWrapper Stub** (2 minutes)
```bash
cp DCSequencer/CustomWrapper_test_stub.vhd VHDL/
```

**Task 4: Test 3-Layer Architecture** (15 minutes)
```bash
# Run existing tests
uv run python tests/run.py ds1120_pd_volo

# Expected: Tests should pass with new top layer
# If they fail, check entity name matches and all ports connected
```

**Task 5: Commit Everything**
```bash
git add VHDL/Top.vhd VHDL/CustomWrapper_test_stub.vhd
git commit -m "feat: Add Layer 1 (CustomWrapper top) for DS1120-PD VoloApp

Complete 3-layer VoloApp architecture:
- Layer 1: Top.vhd (CustomWrapper, BRAM loader, VOLO_READY)
- Layer 2: DS1120_PD_volo_shim.vhd (register mapping)
- Layer 3: DS1120_PD_volo_main.vhd (application logic)

Includes CustomWrapper test stub for CocotB simulation."
```

---

## Key Documentation to Reference

**Start with these** (in order):
1. `PHASE2_QUICK_START.md` - Your detailed task guide
2. `COMPARISON_ANALYSIS.md` - Understanding the naming issue
3. `SESSION_SUMMARY.md` - What was accomplished in Phase 1

**For reference**:
4. `shared/volo/MCC_TOP_volo_loader.vhd` - Template to copy
5. `VHDL/DS1120_PD_volo_shim.vhd` - Layer 2 (what you're instantiating)
6. `DCSequencer/Top.vhd` - Simple CustomWrapper example

---

## Understanding the Architecture

### CustomWrapper Entity (provided by MCC)
```vhdl
entity CustomWrapper is
    port (
        Clk, Reset : in std_logic;
        InputA, InputB, InputC, InputD : in signed(15 downto 0);
        OutputA, OutputB, OutputC, OutputD : out signed(15 downto 0);
        Control0..Control31 : in std_logic_vector(31 downto 0);
    );
end entity;
```

### Our VoloApp Architecture (implements CustomWrapper)
```vhdl
architecture volo_loader of CustomWrapper is
    -- Extract VOLO_READY bits from CR0[31:29]
    -- Instantiate volo_bram_loader (CR10-CR14)
    -- Pass app registers (CR20-CR30) to shim
    -- Instantiate DS1120_PD_volo_shim
end architecture;
```

### Register Map
- **CR0[31:29]**: VOLO_READY control (volo_ready, user_enable, clk_enable)
- **CR10-CR14**: BRAM loader protocol (4KB buffer streaming)
- **CR20-CR30**: Application registers (11 total for DS1120-PD)

---

## What You'll Create

By end of Phase 2, you'll have:
```
VHDL/
├── Top.vhd                         # NEW - Layer 1 (CustomWrapper arch)
├── DS1120_PD_volo_shim.vhd        # Existing - Layer 2 (generated)
├── DS1120_PD_volo_main.vhd        # Existing - Layer 3 (hand-written)
├── CustomWrapper_test_stub.vhd    # NEW - For CocotB testing
└── ... (other support modules)
```

---

## Common Issues & Solutions

### Issue: "entity DS1120-PD_volo_shim not found"
**Fix**: Use underscore: `DS1120_PD_volo_shim`

### Issue: "unconnected port app_reg_XX"
**Fix**: Map all 11 app_reg ports (app_reg_20 through app_reg_30)

### Issue: "package volo_common_pkg not found"
**Fix**: Add shared/volo/*.vhd to compilation order

### Issue: Tests fail with "architecture not found"
**Fix**: Ensure Top.vhd defines `architecture volo_loader of CustomWrapper`

---

## Time Estimate

- Task 1 (naming): 5 minutes
- Task 2 (Top.vhd): 30 minutes
- Task 3 (stub): 2 minutes
- Task 4 (testing): 15 minutes
- Task 5 (commit): 2 minutes

**Total**: ~55 minutes

---

## Success Criteria

Phase 2 complete when:
- [ ] YAML uses underscore naming (DS1120_PD)
- [ ] Top.vhd created and compiles
- [ ] CustomWrapper stub added
- [ ] All 3 layers properly instantiated
- [ ] CocotB tests pass
- [ ] Changes committed to git

---

## If You Get Stuck

**Check these**:
1. Entity name in Top.vhd matches: `DS1120_PD_volo_shim` (underscore!)
2. All 11 app_reg ports mapped (20-30)
3. Architecture name is: `architecture volo_loader of CustomWrapper`
4. Include volo_common_pkg in library path

**Ask these questions**:
- "Show me the instantiation section in shared/volo/MCC_TOP_volo_loader.vhd"
- "What entity name should I use in Top.vhd?"
- "Compare Top.vhd structure with DCSequencer/Top.vhd"

---

## Quick Commands Reference

```bash
# Verify framework works
uv run python -c "from models.volo import VoloApp; \
    app = VoloApp.load_from_yaml('DS1120_PD_app.yaml'); \
    print(f'{app.name}: {len(app.registers)} regs')"

# Generate fresh VHDL
uv run python tools/generate_volo_app.py \
    --config DS1120_PD_app.yaml \
    --output test_out/

# Run tests
uv run python tests/run.py ds1120_pd_volo

# Check git status
git status
git log --oneline -3
```

---

## Context Window Saver

**If running low on tokens**, tell Claude:

> "I'm continuing Phase 2 of EZ-EMFI VoloApp migration. Phase 1 (framework migration) is complete and merged to main. I need to create Top.vhd (Layer 1) for DS1120-PD. Start by reading PHASE2_QUICK_START.md and help me with Task 1 (fix naming convention)."

---

## Ready to Go!

**Your first command**:
```bash
cd /Users/vmars20/EZ-EMFI
cat PHASE2_QUICK_START.md | head -60
```

**Then say**: "Let's start with Task 1 - fix the naming convention in the YAML file"

Good luck! 🚀
