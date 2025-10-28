# DS1140-PD Layer 1 (Top.vhd) Implementation - Session Handoff

**Date**: 2025-10-28
**Status**: Ready for Layer 1 (CustomWrapper/Top.vhd) implementation
**Context**: Fresh session recommended (current at 75% token usage)

---

## Quick Start Prompt for New Session

```
I need to create Layer 1 (Top.vhd) for DS1140-PD, the CustomWrapper architecture file.

**CONTEXT:**
DS1140-PD Layers 2 & 3 are COMPLETE and ALL TESTS PASSING (10/10).
Now I need to create the Top.vhd file (Layer 1) for MCC deployment.

**Read these files:**
1. @DS1140_PD_PROJECT_SUMMARY.md - Project overview
2. @VHDL/Top.vhd - DS1120-PD Layer 1 (reference implementation)
3. @VHDL/DS1140_PD_volo_shim.vhd - Layer 2 (entity ports)
4. @VHDL/DS1140_PD_volo_main.vhd - Layer 3 (entity ports)
5. @DS1140_PD_app.yaml - Register configuration

**IMPLEMENTATION STATUS:**
✅ Phase 0: counter_16bit type implemented (commit fe7a5c9)
✅ Phase 1-3: VHDL implementation complete (commits 959d1c8, 1af4cf3)
  - ds1140_pd_pkg.vhd - Safety constants
  - DS1140_PD_app.yaml - 7 registers
  - DS1140_PD_volo_shim.vhd - Generated shim
  - DS1140_PD_volo_main.vhd - Three outputs + 6-bit FSM observer
✅ Phase 4: Progressive CocotB tests - ALL 10 TESTS PASSING
  - P1 tests (5/5 pass): Reset, arm/trigger, three outputs, FSM observer, VOLO_READY
  - P2 tests (5/5 pass): Timeout, full cycle, clock divider, intensity clamp, debug mux

**TASK:**
Create VHDL/Top.vhd (CustomWrapper architecture) for DS1140-PD.

**KEY CHANGES FROM DS1120-PD:**
1. Architecture name: `DS1140_PD` (not DS1120_PD)
2. Entity instantiation: `DS1140_PD_volo_shim` (not DS1120_PD_volo_shim)
3. **Three outputs**: Wire OutputC to shim (DS1120-PD only used A and B)
4. Component library: `WORK.DS1140_PD_volo_shim` (updated entity name)

Start by reading the reference files, then create Top.vhd following the three-output pattern.
```

---

## Implementation Status Summary

### ✅ Completed (Phases 0-4)

**Phase 0: Register Type Implementation**
- ✅ `counter_16bit` type in `models/volo/app_register.py`
- ✅ Shim generation for 16-bit registers
- ✅ Unit tests passing
- ✅ Commit: fe7a5c9

**Phase 1-3: VHDL Implementation**
- ✅ `ds1140_pd_pkg.vhd` - Safety constants package
- ✅ `DS1140_PD_app.yaml` - 7 registers using counter_16bit
- ✅ `DS1140_PD_volo_shim.vhd` - Auto-generated register mapping
- ✅ `DS1140_PD_volo_main.vhd` - Application logic with three outputs
- ✅ Commits: 959d1c8, 1af4cf3

**Phase 4: Progressive CocotB Testing**
- ✅ Test structure: `tests/ds1140_pd_tests/`
- ✅ Test implementation: `test_ds1140_pd_progressive.py`
- ✅ Test config: Added to `test_configs.py`
- ✅ **ALL 10 TESTS PASSING** (P1: 5/5, P2: 5/5)
- ✅ Commit: 959d1c8

### 🔄 Next Phase

**Phase 5: Layer 1 (Top.vhd) - THIS SESSION**
- [ ] Create `VHDL/Top.vhd` with DS1140_PD architecture
- [ ] Wire three outputs (A, B, C) to shim
- [ ] Test compilation with GHDL
- [ ] Commit changes

**Phase 6: MCC Package & Deployment**
- [ ] Build MCC package
- [ ] CloudCompile synthesis
- [ ] Deploy to Moku:Go
- [ ] Hardware testing

---

## Key Implementation Details

### Three-Output Architecture (CRITICAL!)

DS1140-PD requires **three functional outputs**:

| Output | Purpose | Connected to |
|--------|---------|--------------|
| OutputA | Trigger signal to probe | trigger_out signal |
| OutputB | Intensity/amplitude to probe | intensity_out signal |
| OutputC | FSM state debug | fsm_debug_voltage from fsm_observer |

**DS1120-PD (reference) only used OutputA and OutputB.**

### 6-Bit FSM Observer Compliance ✅

```vhdl
-- Line 252 of DS1140_PD_volo_main.vhd
-- Pads 3-bit ds1120_pd_fsm state to 6-bit for fsm_observer
fsm_state_6bit <= "000" & fsm_state_3bit;
```

This ensures compatibility with the fixed 6-bit `fsm_observer.vhd` entity.

### Register Layout Simplification

**DS1120-PD**: 11 registers (split 16-bit values into high/low bytes)
**DS1140-PD**: **7 registers** (direct 16-bit values using counter_16bit)

**Example simplification:**
```yaml
# DS1120-PD (2 registers for threshold):
- name: Trigger Thresh High  # CR27
- name: Trigger Thresh Low   # CR28

# DS1140-PD (1 register for threshold):
- name: Trigger Threshold    # CR27
  reg_type: counter_16bit
```

---

## Top.vhd Template Structure

### Entity Declaration (unchanged from DS1120-PD)

```vhdl
entity CustomWrapper is
    port (
        Clk     : in  std_logic;
        Reset   : in  std_logic;

        -- MCC I/O (4 inputs, 4 outputs available)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        InputC  : in  signed(15 downto 0);  -- Available but unused
        InputD  : in  signed(15 downto 0);  -- Available but unused

        OutputA : out signed(15 downto 0);  -- ✅ Trigger to probe
        OutputB : out signed(15 downto 0);  -- ✅ Intensity to probe
        OutputC : out signed(15 downto 0);  -- ✅ FSM debug (NEW!)
        OutputD : out signed(15 downto 0);  -- Available for future

        -- Control Registers (CR0-CR30)
        Control0-31 : in std_logic_vector(31 downto 0);

        -- BRAM interface
        -- ...
    );
end entity CustomWrapper;
```

### Architecture Changes

```vhdl
architecture DS1140_PD of CustomWrapper is  -- Changed from DS1120_PD
    -- Component declaration
    component DS1140_PD_volo_shim is  -- Changed from DS1120_PD_volo_shim
        port (
            -- Standard control
            Clk, Reset, Enable, ClkEn : in std_logic;

            -- VOLO control bits
            volo_ready, user_enable, clk_enable, loader_done : in std_logic;

            -- Application registers (CR20-CR28)
            app_reg_20, app_reg_21, app_reg_22, app_reg_23,
            app_reg_24, app_reg_25, app_reg_26, app_reg_27,
            app_reg_28 : in std_logic_vector(31 downto 0);

            -- BRAM interface
            bram_addr : in std_logic_vector(11 downto 0);
            bram_data : in std_logic_vector(31 downto 0);
            bram_we   : in std_logic;

            -- MCC I/O (THREE OUTPUTS!)
            InputA  : in  signed(15 downto 0);
            InputB  : in  signed(15 downto 0);
            OutputA : out signed(15 downto 0);
            OutputB : out signed(15 downto 0);
            OutputC : out signed(15 downto 0)  -- NEW!
        );
    end component;

    -- Internal signals (same as DS1120-PD)
    signal volo_ready    : std_logic;
    signal user_enable   : std_logic;
    signal clk_enable    : std_logic;
    signal loader_done   : std_logic;
    signal global_enable : std_logic;

begin
    -- Extract VOLO control bits from Control0
    volo_ready  <= Control0(31);
    user_enable <= Control0(30);
    clk_enable  <= Control0(29);

    -- Global enable requires all four conditions
    global_enable <= volo_ready and user_enable and clk_enable and loader_done;

    -- BRAM loader instance (same as DS1120-PD)
    -- ...

    -- Application shim instance
    DS1140_PD_SHIM: DS1140_PD_volo_shim  -- Changed component name
        port map (
            Clk          => Clk,
            Reset        => Reset,
            Enable       => global_enable,
            ClkEn        => clk_enable,

            volo_ready   => volo_ready,
            user_enable  => user_enable,
            clk_enable   => clk_enable,
            loader_done  => loader_done,

            -- Application registers
            app_reg_20   => Control20,
            app_reg_21   => Control21,
            app_reg_22   => Control22,
            app_reg_23   => Control23,
            app_reg_24   => Control24,
            app_reg_25   => Control25,
            app_reg_26   => Control26,
            app_reg_27   => Control27,
            app_reg_28   => Control28,

            -- BRAM interface
            bram_addr    => bram_addr_from_loader,
            bram_data    => bram_data_from_loader,
            bram_we      => bram_we_from_loader,

            -- MCC I/O (THREE OUTPUTS!)
            InputA       => InputA,
            InputB       => InputB,
            OutputA      => OutputA,
            OutputB      => OutputB,
            OutputC      => OutputC  -- NEW! Wire to CustomWrapper port
        );

    -- OutputD unused (tie to zero or leave unconnected)
    OutputD <= (others => '0');

end architecture DS1140_PD;
```

---

## Reference Files

**Layer 1 (CustomWrapper/Top.vhd):**
- `/Users/vmars20/EZ-EMFI/VHDL/Top.vhd` - DS1120-PD reference

**Layer 2 (Shim):**
- `/Users/vmars20/EZ-EMFI/VHDL/DS1140_PD_volo_shim.vhd` - Generated (lines 53-110 for entity)

**Layer 3 (Application):**
- `/Users/vmars20/EZ-EMFI/VHDL/DS1140_PD_volo_main.vhd` - Application logic

**Configuration:**
- `/Users/vmars20/EZ-EMFI/DS1140_PD_app.yaml` - Register layout

**Documentation:**
- `/Users/vmars20/EZ-EMFI/DS1140_PD_PROJECT_SUMMARY.md` - Project overview
- `/Users/vmars20/EZ-EMFI/DS1140_PD_THREE_OUTPUT_DESIGN.md` - Three-output architecture

---

## Testing Status

### P1 Tests (Basic) - ALL PASSING ✅
1. ✅ Reset behavior
2. ✅ Arm and trigger
3. ✅ Three outputs functioning (OutputA, OutputB, OutputC)
4. ✅ FSM observer on OutputC (voltage tracking)
5. ✅ VOLO_READY scheme

### P2 Tests (Intermediate) - ALL PASSING ✅
6. ✅ Timeout behavior
7. ✅ Full operational cycle
8. ✅ Clock divider integration
9. ✅ Intensity clamping on OutputB (safety)
10. ✅ Debug mux view switching (gracefully skipped if not implemented)

**Test command:**
```bash
# P1 tests (default)
uv run python tests/run.py ds1140_pd_volo

# P2 tests (comprehensive)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py ds1140_pd_volo
```

---

## Success Criteria for Top.vhd

- [ ] Top.vhd compiles with GHDL (--std=08)
- [ ] Three outputs wired correctly (A, B, C)
- [ ] Architecture name is `DS1140_PD`
- [ ] Component instantiation uses `DS1140_PD_volo_shim`
- [ ] BRAM loader integrated (copy from DS1120-PD)
- [ ] VOLO control bits extracted correctly
- [ ] File committed to git

---

## After Top.vhd Completion

**Phase 6: MCC Package & Deployment**
```bash
# 1. Build MCC package
uv run python scripts/build_mcc_package.py modules/DS1140-PD

# 2. Upload to CloudCompile (manual)
# 3. Download synthesis results
# 4. Import build
python scripts/import_mcc_build.py modules/DS1140-PD

# 5. Deploy to Moku:Go
cd tests
uv run python test_ds1140_pd_mokubench.py \
  --ip <moku_ip> \
  --bitstream ../modules/DS1140-PD/latest/25ff*_bitstreams.tar
```

---

## Estimated Timeline

- **Top.vhd creation**: 30-60 minutes
- **GHDL verification**: 5 minutes
- **MCC package build**: 5 minutes
- **CloudCompile synthesis**: 30-60 minutes (automated)
- **Hardware deployment**: 15-30 minutes
- **Total remaining**: ~2-3 hours to hardware-validated DS1140-PD

---

**Status**: Ready to start fresh session for Top.vhd implementation!
**Next**: Copy the "Quick Start Prompt" above into a new Claude Code window.
