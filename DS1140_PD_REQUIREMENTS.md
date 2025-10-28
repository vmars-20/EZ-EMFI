# DS1140-PD Requirements Document

**Date**: 2025-10-28
**Project**: DS1140-PD EMFI Probe Driver
**Purpose**: Refactoring/modernization of DS1120-PD with improved testing and enhanced register types

---

## Executive Summary

DS1140-PD is a **refactoring project**, not a feature expansion. The goal is to rebuild DS1120-PD using:
- Refined, tested building block modules
- Modern progressive CocotB testing framework
- **`counter_16bit` register type** (eliminates awkward 8-bit high/low splits)
- Optimized register layout (**7 registers** vs 11, no backward compatibility constraint)

**Same hardware target**: Riscure DS1120A EMFI probe on Moku:Go platform
**Same core functionality**: Single-shot EMFI pulse generation with safety features
**Different implementation**: Cleaner architecture, better testing, more intuitive configuration

---

## DS1120-PD Reverse-Engineered Requirements

### Core Functional Requirements

**FR1: Single-Shot EMFI Pulse Generation**
- Generate electromagnetic fault injection pulses on demand
- One-shot operation: READY → ARMED → FIRING → COOLING → DONE cycle
- 7-state FSM: READY, ARMED, FIRING, COOLING, DONE, TIMEDOUT, HARDFAULT
- Configurable pulse intensity (0-3.0V, safety clamped)
- Configurable pulse duration (up to 32 cycles)

**FR2: Trigger Detection & Control**
- External voltage threshold trigger (InputA ADC channel, 16-bit signed ±5V)
- Configurable threshold voltage (16-bit, default 2.4V = 0x3DCF)
- Small hysteresis (threshold - 0x0100)
- Manual force-fire capability for testing (bypasses threshold)
- Timeout protection if no trigger received while armed (12-bit counter, 0-4095 cycles)

**FR3: Safety & Thermal Management**
- Mandatory cooling period after each pulse (minimum 8 cycles, configurable)
- Maximum intensity clamping at 3.0V (0x4CCD) - hardware enforced in `ds1120_pd_pkg.vhd`
- Fire count limiting (max 15 per session, 4-bit counter)
- Spurious trigger detection and counting (triggers detected when not ARMED)
- Hard fault state (111) for error conditions
- All safety constants defined in `ds1120_pd_pkg.vhd`

**FR4: Timing Control**
- Programmable clock divider (÷1 to ÷16) via `volo_clk_divider` module
- 12-bit arm timeout counter (CR23[3:0] + CR24[7:0], up to 4095 cycles)
- Configurable firing duration (up to 32 cycles, enforced by FSM)
- Configurable cooling duration (minimum 8 cycles, enforced by FSM)
- Clock divider affects FSM timing, not system clock

**FR5: Monitoring & Debug**
- FSM state visualization via OutputB using `fsm_observer` module
- 3-bit FSM state padded to 6-bit for observer interface
- Voltage mapping: 0.0V to 2.5V linear, fault states negative (sign-flip)
- Current monitor input (InputB, 16-bit signed) - available but unused
- Status flags: was_triggered (sticky), timed_out (sticky), fire_count, spurious_count

---

## Available Building Blocks (All Tested)

### Core Modules

| Module | Status | Test Coverage | Purpose |
|--------|--------|---------------|---------|
| `volo_clk_divider` | ✅ Tested | P1/P2 (7 tests) | Programmable clock divider (÷1 to ÷MAX_DIV) |
| `volo_voltage_threshold_trigger_core` | ✅ Used | Integration tested | Voltage threshold crossing detection |
| `fsm_observer` | ✅ Validated | 20 tests | FSM state → oscilloscope voltage visualization |
| `volo_bram_loader` | ✅ Tested | P1/P2 | BRAM loading FSM (for future waveform storage) |
| `ds1120_pd_fsm` | ✅ Tested | Integration tested | 7-state probe control FSM |

### Utility Packages

| Package | Purpose | Key Features |
|---------|---------|--------------|
| `volo_voltage_pkg` | Voltage conversions | 16-bit signed ±5V scale, ~305µV resolution |
| `volo_common_pkg` | VoloApp infrastructure | VOLO_READY scheme, BRAM interface, `combine_volo_ready()` |
| `ds1120_pd_pkg` | DS1120-PD constants | Safety limits, voltage constants, `clamp_voltage()` |

---

## DS1140-PD Design Goals

### 1. **Modernized Architecture**
- Use latest versions of tested building blocks
- Apply lessons learned from DS1120-PD development
- Optimize register layout (no CR20-CR30 backward compatibility)
- Follow 3-layer VoloApp pattern strictly

### 2. **Enhanced Testing Strategy**
- **Progressive CocotB Testing** (P1/P2/P3 structure)
  - P1 (Basic): 3-5 essential tests, <20 lines output, runs by default
  - P2 (Intermediate): Full validation, runs with `TEST_LEVEL=P2_INTERMEDIATE`
- **Test Structure Pattern**:
  ```
  tests/
  ├── ds1140_pd_tests/
  │   ├── __init__.py
  │   └── ds1140_pd_constants.py  # Test values, error messages
  └── test_ds1140_pd_progressive.py  # Progressive test implementation
  ```
- Test Layer 3 (volo_main) directly with friendly signals
- Use `conftest.py` utilities: `setup_clock()`, `reset_active_high()`, `TestBase`

### 3. **Enhanced Register Types**

**Current Register Types** (limited to 3):
- `counter_8bit` → `std_logic_vector(7 downto 0)` - 0-255
- `percent` → `std_logic_vector(6 downto 0)` - 0-100
- `button` → `std_logic` - 0 or 1

**New Type (COMMITTED - Phase 0)**: `counter_16bit`
- `counter_16bit` → `std_logic_vector(15 downto 0)` - 0-65535
- **Will be implemented BEFORE DS1140-PD Phase 2**
- Eliminates split 16-bit registers (no high/low byte pairs)
- Uses upper 16 bits of 32-bit Control Register: `app_reg_N(31 downto 16)`

**Future Enhancement Types** (see `DS1140_PD_REGISTER_TYPES.md`):
- `voltage_signed` → 16-bit signed voltage (±5V scale, user writes `2.4` instead of `0x3DCF`)
- Priority: Lower (after counter_16bit proven stable)

**Benefits of `counter_16bit`**:
- No manual register splitting in YAML (single register for 16-bit values)
- Simpler VHDL ports (direct 16-bit signals, no reconstruction)
- Reduced register count (7 vs 9 with splits)
- Better documentation (single register instead of high/low pairs)

---

## DS1140-PD Register Layout (with `counter_16bit`)

**Goal**: Organize registers by function, eliminate split 16-bit registers

### Control Registers (CR20-CR22)

| CR | Name | Type | Default | Description |
|----|------|------|---------|-------------|
| CR20 | Arm Probe | `button` | 0 | Arm the probe (one-shot, transitions READY→ARMED) |
| CR21 | Force Fire | `button` | 0 | Manual trigger (bypasses threshold) |
| CR22 | Reset FSM | `button` | 0 | Reset state machine to READY |

### Timing Registers (CR23-CR26)

| CR | Name | Type | Default | Description |
|----|------|------|---------|-------------|
| CR23 | Clock Divider | `counter_8bit` | 0 | FSM timing divider (0=÷1, 15=÷16) |
| CR24 | Arm Timeout | `counter_16bit` | 255 | Cycles to wait for trigger before timeout (0-4095) |
| CR25 | Firing Duration | `counter_8bit` | 16 | Cycles in FIRING state (max 32) |
| CR26 | Cooling Duration | `counter_8bit` | 16 | Cycles in COOLING state (min 8) |

### Voltage Registers (CR27-CR28)

| CR | Name | Type | Default | Description |
|----|------|------|---------|-------------|
| CR27 | Trigger Threshold | `counter_16bit` | 0x3DCF | Voltage threshold for trigger detection (2.4V) |
| CR28 | Intensity | `counter_16bit` | 0x2666 | Output intensity (clamped to 3.0V, 2.0V default) |

**Register Count**: **7 registers** (DS1120-PD used 11)

**Changes from DS1120-PD**:
- **Uses `counter_16bit` type** (implemented in Phase 0)
- Combined threshold high/low into single 16-bit register (CR27)
- Combined intensity high/low into single 16-bit register (CR28)
- Combined timing control + delay into separate clean registers (CR23, CR24)
- Removed: Split high/low byte registers (was CR27/28/29/30 in DS1120)
- Timing durations stay 8-bit (sufficient range, simpler)

---

## MCC I/O Mapping

**Moku:Go Channels** (16-bit signed, ±5V full scale):
- **InputA**: External trigger signal (monitored by `volo_voltage_threshold_trigger_core`)
- **InputB**: Probe current monitor (reserved, currently unused)
- **OutputA**: Trigger output to probe (active during FIRING state)
- **OutputB**: FSM state debug voltage (via `fsm_observer`)

**BRAM Interface** (reserved for future use):
- Could store waveform patterns, calibration data, timing sequences
- Interface present but unused in current design

---

## Safety Constraints (Mandatory)

**From `ds1120_pd_pkg.vhd` (must preserve in DS1140-PD)**:

```vhdl
constant MAX_INTENSITY_3V0   : signed(15 downto 0) := x"4CCD";  -- 3.0V safety limit
constant MAX_FIRING_CYCLES   : natural := 32;   -- Hardware limit
constant MIN_COOLING_CYCLES  : natural := 8;    -- Minimum cooldown
constant MAX_ARM_TIMEOUT     : natural := 4095; -- 12-bit maximum
constant MAX_FIRE_COUNT      : natural := 15;   -- Session limit (4-bit)
constant MAX_SPURIOUS_COUNT  : natural := 15;   -- Spurious limit (4-bit)
```

**Safety Functions** (must preserve):
```vhdl
function clamp_voltage(
    voltage : signed(15 downto 0);
    max_val : signed(15 downto 0)
) return signed;
```

**FSM Safety Features**:
- Firing duration clamped to MAX_FIRING_CYCLES in FSM counter process
- Cooling duration enforced to MIN_COOLING_CYCLES minimum in FSM counter process
- Fire count saturates at 15 (no overflow)
- Spurious count saturates at 15
- STATE_HARDFAULT = "111" for error conditions

---

## Testing Requirements

### P1 - Basic Tests (Essential Validation)

**Goal**: <20 lines output, runs by default

1. **Test: Reset behavior**
   - Verify all outputs zero during reset
   - FSM in READY state after reset

2. **Test: Arm and trigger sequence**
   - Arm FSM, apply trigger above threshold
   - Verify transition READY → ARMED → FIRING

3. **Test: Intensity clamping (safety critical)**
   - Set intensity above 3.0V limit
   - Force fire, verify no errors (clamping happens internally)

4. **Test: VOLO_READY scheme (MCC 3-bit control)**
   - Test Enable/ClkEn/MCC_READY control bits
   - Verify module disabled when any bit low

### P2 - Intermediate Tests (Comprehensive Validation)

**Goal**: Full coverage, runs with `TEST_LEVEL=P2_INTERMEDIATE`

5. **Test: Timeout behavior**
   - Arm with short timeout, no trigger
   - Verify transition ARMED → TIMEDOUT

6. **Test: Full operational cycle**
   - Complete cycle: READY → ARMED → FIRING → COOLING → DONE
   - Verify timing constraints enforced

7. **Test: Clock divider integration**
   - Test FSM timing with different divider settings
   - Verify longer cycles with clock division

8. **Test: FSM observer debug visualization** (if time permits)
   - Verify voltage output tracks FSM state
   - Check fault state sign-flip behavior

---

## Implementation Phases

### Phase 0: Register Type Implementation (BLOCKING)
1. Implement `counter_16bit` in `models/volo/app_register.py`
2. Update shim generation in `models/volo/volo_app.py`
3. Add unit tests for 16-bit register validation
4. Test YAML parsing and VHDL generation
5. Update documentation
**Estimated time**: 2-3 hours (must complete before Phase 2)

### Phase 1: Core Refactoring
1. Update `ds1120_pd_pkg.vhd` if needed (preserve safety constants)
2. Review and refine `ds1120_pd_fsm.vhd` (may be reusable as-is)
3. Create new `DS1140_PD_volo_main.vhd` with optimized architecture

### Phase 2: Register System & YAML (AFTER PHASE 0)
1. Create `DS1140_PD_app.yaml` with 7 registers using `counter_16bit`
2. Generate shim layer: `DS1140_PD_volo_shim.vhd`
3. Verify entity ports use direct 16-bit signals (no reconstruction)

### Phase 3: Progressive Testing
1. Create test structure: `tests/ds1140_pd_tests/`
2. Implement P1 tests (5 essential tests)
3. Implement P2 tests (5 comprehensive tests)
4. Validate on GHDL simulation

### Phase 4: Hardware Validation
1. Build MCC package
2. Deploy to Moku:Go via CloudCompile
3. Hardware testing on actual DS1120A probe

---

## Success Criteria

✅ **Functional Equivalence**: DS1140-PD matches DS1120-PD behavior exactly
✅ **Code Quality**: Cleaner architecture, better documentation
✅ **Test Coverage**: P1 tests <20 lines output, P2 tests comprehensive
✅ **Register UX**: More intuitive register types and layout
✅ **Safety Preserved**: All DS1120-PD safety features intact
✅ **Hardware Validated**: Successful deployment and operation on Moku:Go

---

## References

**DS1120-PD Implementation**:
- `/Users/vmars20/EZ-EMFI/DS1120_PD_app.yaml` - Current YAML config
- `/Users/vmars20/EZ-EMFI/VHDL/DS1120_PD_volo_main.vhd` - Layer 3 application logic
- `/Users/vmars20/EZ-EMFI/VHDL/DS1120_PD_volo_shim.vhd` - Layer 2 register mapping
- `/Users/vmars20/EZ-EMFI/VHDL/ds1120_pd_fsm.vhd` - FSM core
- `/Users/vmars20/EZ-EMFI/VHDL/packages/ds1120_pd_pkg.vhd` - Constants and safety functions
- `/Users/vmars20/EZ-EMFI/tests/test_ds1120_pd_volo_progressive.py` - Current tests (P1/P2)

**Building Blocks**:
- `/Users/vmars20/EZ-EMFI/VHDL/volo_clk_divider.vhd` - Clock divider
- `/Users/vmars20/EZ-EMFI/VHDL/volo_voltage_threshold_trigger_core.vhd` - Threshold trigger
- `/Users/vmars20/EZ-EMFI/VHDL/fsm_observer.vhd` - FSM visualization
- `/Users/vmars20/EZ-EMFI/VHDL/packages/volo_voltage_pkg.vhd` - Voltage utilities
- `/Users/vmars20/EZ-EMFI/VHDL/packages/volo_common_pkg.vhd` - VoloApp infrastructure

**Documentation**:
- `/Users/vmars20/EZ-EMFI/docs/FSM_OBSERVER_PATTERN.md` - FSM observer integration guide
- `/Users/vmars20/EZ-EMFI/docs/PROGRESSIVE_TESTING_GUIDE.md` - Progressive testing methodology
- `/Users/vmars20/EZ-EMFI/docs/COCOTB_PATTERNS.md` - CocotB testing patterns

**Vendor Documentation**:
- `/Users/vmars20/EZ-EMFI/vendor_docs/DS1120A Unidirectional Fault Injection Probe _ DS1121A Bidirectional Fault Injection Probe.pdf`
- `/Users/vmars20/EZ-EMFI/vendor_docs/Datasheet-MokuGo.pdf`

---

**Next Steps**: See `DS1140_PD_IMPLEMENTATION_GUIDE.md` for detailed step-by-step instructions.
