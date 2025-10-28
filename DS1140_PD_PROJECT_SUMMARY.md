# DS1140-PD Project Summary

**Date**: 2025-10-28
**Status**: Documentation Complete, Ready for Implementation

---

## Project Overview

DS1140-PD is a **refactoring/modernization project** of the DS1120-PD EMFI probe driver with:
- Same functionality (single-shot EMFI pulse generation with safety features)
- Modern architecture (refined building blocks, progressive testing)
- **Three-output design** (trigger, intensity, FSM debug)
- **16-bit register type** (`counter_16bit`) eliminates awkward register splits
- Simplified register layout (**7 registers** vs 11 in DS1120-PD)
- No backward compatibility constraints

**Hardware Target**: Riscure DS1120A EMFI probe on Moku:Go platform

---

## Documentation Deliverables

### 1. **DS1140_PD_REQUIREMENTS.md** - Requirements Document
**Purpose**: Reverse-engineered requirements from DS1120-PD

**Contents**:
- Core functional requirements (FR1-FR5)
- Available building blocks (all tested)
- Proposed register layout (9 registers)
- Safety constraints (must preserve)
- Progressive testing requirements (P1/P2)
- Success criteria

**Key Insights**:
- DS1120-PD FSM core is excellent - reuse as-is (3-bit state)
- Safety package solid - preserve all constants
- Register layout needs simplification (eliminate split 16-bit registers)

### 2. **DS1140_PD_THREE_OUTPUT_DESIGN.md** - Three-Output Architecture (CRITICAL)
**Purpose**: Detailed design for three outputs with FSM observer integration

**Contents**:
- How to ensure 6-bit FSM encoding standard (padding pattern)
- Three-output architecture (OutputA/B/C)
- Debug multiplexer integration (optional, advanced)
- Testing strategy for all outputs
- Complete code examples

**Key Decisions**:
- **OutputA**: Trigger signal to probe
- **OutputB**: Intensity/amplitude to probe
- **OutputC**: FSM state debug via fsm_observer
- **Padding pattern**: `fsm_state_6bit <= "000" & fsm_state_3bit` (CRITICAL!)
- fsm_observer has 20 comprehensive tests validating the pattern

**Implementation Options**:
- **Phase 1**: Simple FSM observer on OutputC (recommended)
- **Phase 2**: Debug multiplexer with 8 selectable views (optional)

### 3. **DS1140_PD_IMPLEMENTATION_GUIDE.md** - Step-by-Step Guide
**Purpose**: Complete implementation roadmap

**Contents**:
- Quick start prompt for next Claude session
- 6 implementation phases with detailed steps
- Complete code templates (YAML, VHDL, CocotB)
- Success checklist for each phase
- Common issues & solutions
- Complete reference file listing

**Phases**:
1. Architecture review & planning
2. Register system design
3. VHDL implementation (with three outputs)
4. Progressive CocotB testing (P1: 5 tests, P2: 5 tests)
5. Extended register types (optional)
6. Hardware deployment

### 4. **DS1140_PD_REGISTER_TYPES.md** - Register Type Implementation Plan (COMMITTED)
**Purpose**: Implementation plan for `counter_16bit` register type

**Contents**:
- `counter_16bit` implementation details
- Impact on DS1140-PD register layout (9 → 7 registers)
- VHDL implementation changes (eliminates manual signal reconstruction)
- Complete implementation checklist (Phase 0: before DS1140-PD Phase 2)
- Future enhancement: `voltage_signed` type (after counter_16bit proven)

**Key Decision**: Implement `counter_16bit` **before** DS1140-PD Phase 2
- Eliminates split 16-bit registers (threshold high/low, intensity high/low)
- Simpler YAML configuration (single registers for 16-bit values)
- Cleaner VHDL ports (direct 16-bit signals, no reconstruction)

---

## Key Design Decisions

### 1. Three-Output Architecture ✅
**Decision**: Use OutputA, OutputB, OutputC (not just A/B like DS1120-PD)

**Rationale**:
- OutputA: Functional (trigger to probe)
- OutputB: Functional (intensity to probe)
- OutputC: Debug (FSM state visualization)
- CustomWrapper provides 4 outputs (A/B/C/D), use 3 for DS1140-PD

**Benefits**:
- Real-time FSM state visualization on oscilloscope
- No impact on functional outputs
- Proven pattern (see EMFI-Seq, PulseStar examples)

### 2. 6-Bit FSM Standard Compliance ✅
**Decision**: Pad ds1120_pd_fsm 3-bit output to 6-bit for fsm_observer

**Implementation**: `fsm_state_6bit <= "000" & fsm_state_3bit`

**Rationale**:
- fsm_observer requires 6-bit state vector (standard interface)
- ds1120_pd_fsm outputs 3-bit state (states 0-7)
- Zero-extending "000"-"111" → "000000"-"000111" preserves all encodings
- No FSM modification needed (proven design preserved)

**Testing**: fsm_observer has 20 comprehensive tests validating this pattern

### 3. Reuse ds1120_pd_fsm.vhd ✅
**Decision**: Reuse FSM core as-is (no modifications)

**Rationale**:
- Well-designed, tested, proven in DS1120-PD
- Safety features baked in (max cycles, min cooling)
- Status flags well-designed (sticky bits)
- Only minor interface difference: 12-bit delay_count (pad 8-bit register in volo_main)

### 4. Simplified Register Layout with `counter_16bit` ✅
**Decision**: **7 registers** (vs 11 in DS1120-PD) using `counter_16bit` type

**Changes**:
- Eliminate dual-purpose timing_control register
- **Implemented `counter_16bit` type** (before DS1140-PD Phase 2)
- Single registers for 16-bit values (arm_timeout, trigger_threshold, intensity)
- Cleaner organization by function (control, timing, voltage)

**Benefits**:
- No manual signal reconstruction in VHDL
- More intuitive configuration (no high/low byte splits)
- 22% fewer registers (7 vs 9 with splits, 36% vs DS1120-PD)
- Better documentation

### 5. Progressive Testing Structure ✅
**Decision**: P1 (5 tests) + P2 (5 tests) structure

**P1 Tests** (<25 lines output, runs by default):
1. Reset behavior
2. Arm and trigger
3. **Three outputs functioning** ← NEW
4. **FSM observer on OutputC** ← NEW
5. VOLO_READY scheme

**P2 Tests** (comprehensive, runs with TEST_LEVEL=P2_INTERMEDIATE):
6. Timeout behavior
7. Full operational cycle
8. Clock divider integration
9. **Intensity clamping on OutputB** ← NEW
10. **Debug mux view switching** (if implemented) ← NEW

---

## Implementation Roadmap

### Phase 0: Register Type Implementation (BLOCKING, BEFORE PHASE 2)
- [ ] Implement `counter_16bit` type in `models/volo/app_register.py`
- [ ] Update shim generation for 16-bit registers in `models/volo/volo_app.py`
- [ ] Add unit tests for `counter_16bit` validation
- [ ] Test YAML parsing and VHDL generation
- [ ] Update documentation in `EXTERNAL_volo_vhdl/docs/VOLO_APP_DESIGN.md`
- **Estimated time**: 2-3 hours (blocking)

### Phase 1: Requirements & Architecture (COMPLETE ✅)
- [x] Reverse-engineer DS1120-PD requirements
- [x] Identify reusable components
- [x] Design three-output architecture
- [x] Document FSM observer integration
- [x] Create implementation guide
- [x] Commit to `counter_16bit` implementation

### Phase 2: Implementation (AFTER PHASE 0)
- [ ] Create `DS1140_PD_app.yaml` with 7 registers using `counter_16bit`
- [ ] Generate shim layer (`DS1140_PD_volo_shim.vhd`)
- [ ] Implement `DS1140_PD_volo_main.vhd` with three outputs
- [ ] Add FSM observer integration (6-bit padding)
- [ ] Implement safety clamping and output control

### Phase 3: Testing
- [ ] Create test structure (`tests/ds1140_pd_tests/`)
- [ ] Implement P1 tests (5 tests, <25 lines output)
- [ ] Implement P2 tests (5 tests, comprehensive)
- [ ] Validate in GHDL simulation
- [ ] All tests pass

### Phase 4: Hardware Deployment
- [ ] Build MCC package
- [ ] CloudCompile synthesis
- [ ] Deploy to Moku:Go
- [ ] Hardware testing on DS1120A probe

### Phase 5: Optional Enhancements (FUTURE)
- [ ] `voltage_signed` register type (lets users write `2.4` instead of `0x3DCF`)
- [ ] Debug multiplexer (8 selectable views on OutputC)
- [ ] Additional test coverage

---

## Success Criteria

✅ **Functional Equivalence**: DS1140-PD matches DS1120-PD behavior exactly
✅ **Code Quality**: Cleaner architecture, better documentation
✅ **Test Coverage**: P1 tests <25 lines output, P2 tests comprehensive
✅ **Three Outputs Working**: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
✅ **FSM Observer Validated**: OutputC tracks FSM state changes correctly
✅ **Safety Preserved**: All DS1120-PD safety features intact
✅ **Hardware Validated**: Successful deployment and operation on Moku:Go

---

## Quick Start for Next Session

Use this prompt in your next Claude session:

```
I need to implement DS1140-PD, a refactored version of the DS1120-PD EMFI probe driver.

Read these documents in order:
1. @DS1140_PD_PROJECT_SUMMARY.md - This summary
2. @DS1140_PD_REQUIREMENTS.md - Complete requirements
3. @DS1140_PD_THREE_OUTPUT_DESIGN.md - Three-output architecture (CRITICAL)
4. @DS1140_PD_IMPLEMENTATION_GUIDE.md - Step-by-step guide

This is a REFACTORING project with modern architecture:
- Same functionality as DS1120-PD
- Use refined, tested building blocks
- Progressive CocotB testing (P1/P2 structure)
- THREE OUTPUTS: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
- 6-bit FSM standard compliance via padding: "000" & fsm_state_3bit
- Simplified register layout (9 registers instead of 11)
- Preserve all safety features

Start by confirming you've read all four documents, then ask if I need clarification before proceeding.
```

---

## Key Reference Files

**DS1120-PD Implementation** (source of truth):
- `/Users/vmars20/EZ-EMFI/DS1120_PD_app.yaml`
- `/Users/vmars20/EZ-EMFI/VHDL/DS1120_PD_volo_main.vhd`
- `/Users/vmars20/EZ-EMFI/VHDL/ds1120_pd_fsm.vhd` ← Reuse as-is
- `/Users/vmars20/EZ-EMFI/VHDL/packages/ds1120_pd_pkg.vhd` ← Preserve
- `/Users/vmars20/EZ-EMFI/tests/test_ds1120_pd_volo_progressive.py`

**Building Blocks** (all tested):
- `/Users/vmars20/EZ-EMFI/VHDL/volo_clk_divider.vhd` (P1/P2 tested)
- `/Users/vmars20/EZ-EMFI/VHDL/volo_voltage_threshold_trigger_core.vhd`
- `/Users/vmars20/EZ-EMFI/VHDL/fsm_observer.vhd` (20 tests)
- `/Users/vmars20/EZ-EMFI/VHDL/packages/volo_voltage_pkg.vhd`
- `/Users/vmars20/EZ-EMFI/VHDL/packages/volo_common_pkg.vhd`

**Documentation**:
- `/Users/vmars20/EZ-EMFI/docs/FSM_OBSERVER_PATTERN.md` (6-bit standard)
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/docs/OSCILLOSCOPE-BASED-DEBUGGING-WORKFLOW.md`
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/experimental/inspectable_buffer_loader/core/debug_mux.vhd` (reference)

**Three-Output Examples**:
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/instruments/PulseStar/top/Top.vhd` (4 outputs functional)
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/instruments/EMFI-Seq/top/Top.vhd` (3 outputs: 2 functional + FSM debug)

---

## Critical Implementation Details

### FSM Observer Integration (MOST CRITICAL)

```vhdl
-- CRITICAL: Pad 3-bit FSM state to 6-bit for fsm_observer
signal fsm_state_3bit : std_logic_vector(2 downto 0);  -- From ds1120_pd_fsm
signal fsm_state_6bit : std_logic_vector(5 downto 0);  -- For fsm_observer

-- Zero-extend (CRITICAL!)
fsm_state_6bit <= "000" & fsm_state_3bit;

-- FSM Observer
U_FSM_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 8,  -- States 0-7
        FAULT_STATE_THRESHOLD => 7,  -- State "000111" = HARDFAULT
        -- ... other generics
    )
    port map (
        state_vector => fsm_state_6bit,  -- 6-bit input
        voltage_out  => fsm_debug_voltage
    );

-- Route to OutputC
OutputC <= fsm_debug_voltage;
```

### Three-Output Entity Template

```vhdl
entity DS1140_PD_volo_main is
    port (
        -- ... standard ports ...

        -- MCC I/O (Three outputs!)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);  -- Trigger to probe
        OutputB : out signed(15 downto 0);  -- Intensity to probe
        OutputC : out signed(15 downto 0)   -- FSM debug
    );
end entity;
```

### Safety Features (MUST PRESERVE)

```vhdl
-- From ds1120_pd_pkg.vhd
constant MAX_INTENSITY_3V0   : signed(15 downto 0) := x"4CCD";  -- 3.0V limit
constant MAX_FIRING_CYCLES   : natural := 32;
constant MIN_COOLING_CYCLES  : natural := 8;

-- Apply clamping
intensity_clamped <= clamp_voltage(intensity_value, MAX_INTENSITY_3V0);
```

---

## Estimated Timeline

- **Phase 0** (Register Type): 2-3 hours (blocking, must complete first)
- **Phase 1** (Requirements & Architecture): ✅ Complete
- **Phase 2** (Implementation): 3-4 hours
- **Phase 3** (Testing): 2-3 hours
- **Phase 4** (Hardware): 1-2 hours (synthesis time)
- **Total**: ~8-12 hours for complete DS1140-PD implementation

**Critical Path**: Phase 0 must complete before Phase 2 can begin.

**Checkpoint**: After Phase 3 (testing), all functionality should be validated in simulation before hardware deployment.

---

## Notes for Future Development

1. **Register Type Implementation**: `counter_16bit` must be implemented in Phase 0 (before Phase 2). `voltage_signed` is a future enhancement after counter_16bit is proven stable.

2. **Debug Multiplexer**: Start with simple FSM observer on OutputC. Add debug mux later only if hardware debugging requires multiple views.

3. **Testing Strategy**: P1 tests should complete in <1 minute. P2 tests may take longer but provide comprehensive validation.

4. **Hardware Bring-Up**: First deployment should use simple FSM observer. Debug mux can be added in revision 2 if needed.

---

**Status**: All documentation complete. Ready for Phase 0 (register type implementation).
**Next Step**: Implement `counter_16bit` type (Phase 0), then begin Phase 2 following `DS1140_PD_IMPLEMENTATION_GUIDE.md`
