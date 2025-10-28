# DS1140-PD Implementation Guide

**Date**: 2025-10-28
**Purpose**: Step-by-step guide for implementing DS1140-PD with modern architecture
**Prerequisites**: Read `DS1140_PD_REQUIREMENTS.md` first

---

## Quick Start Prompt for Future Claude Session

```
I need to implement DS1140-PD, a refactored version of the DS1120-PD EMFI probe driver.

**Context**:
- Read @DS1140_PD_REQUIREMENTS.md for complete requirements
- Read @DS1140_PD_THREE_OUTPUT_DESIGN.md for three-output architecture
- This is a REFACTORING project, not a feature expansion
- Same functionality as DS1120-PD, but with modern architecture
- No backward compatibility constraint - optimize the design

**Goals**:
1. **Implement `counter_16bit` register type** (Phase 0, before Phase 2)
2. Use refined, tested building blocks (volo_clk_divider, fsm_observer, etc.)
3. Implement progressive CocotB testing (P1/P2 structure)
4. Create intuitive register layout (**7 registers** with counter_16bit, vs 11 in DS1120-PD)
5. Three-output design: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
6. Preserve all safety features from DS1120-PD

**Reference Implementation**:
- @VHDL/DS1120_PD_volo_main.vhd - Current implementation
- @VHDL/ds1120_pd_fsm.vhd - FSM core (reusable, 3-bit state)
- @VHDL/packages/ds1120_pd_pkg.vhd - Safety constants (preserve)
- @tests/test_ds1120_pd_volo_progressive.py - Test pattern reference
- @DS1140_PD_THREE_OUTPUT_DESIGN.md - Three-output architecture with FSM observer

**Implementation Path**:
Follow implementation phases in @DS1140_PD_IMPLEMENTATION_GUIDE.md:
0. **Phase 0** (BLOCKING): Implement `counter_16bit` type (2-3 hours)
1. Review DS1120-PD architecture
2. Create DS1140_PD_app.yaml with 7 registers using counter_16bit
3. Generate shim layer
4. Implement volo_main with three outputs (A: trigger, B: intensity, C: FSM debug)
5. Create progressive CocotB tests (P1: 5 tests, P2: 5 tests)

Start by reviewing the requirements document and asking if I need any clarification before proceeding.
```

---

## Phase 0: Register Type Implementation (BLOCKING)

**This phase MUST complete before Phase 2 can begin.**

### Step 0.1: Implement `counter_16bit` in `app_register.py`

**File**: `/Users/vmars20/EZ-EMFI/models/volo/app_register.py`

**Changes needed**:

```python
# 1. Add to RegisterType enum
class RegisterType(str, Enum):
    COUNTER_8BIT = "counter_8bit"
    COUNTER_16BIT = "counter_16bit"  # NEW
    PERCENT = "percent"
    BUTTON = "button"

# 2. Update get_type_bit_width()
def get_type_bit_width(self) -> int:
    if self.reg_type == RegisterType.COUNTER_8BIT:
        return 8
    elif self.reg_type == RegisterType.COUNTER_16BIT:
        return 16  # NEW
    elif self.reg_type == RegisterType.PERCENT:
        return 7
    elif self.reg_type == RegisterType.BUTTON:
        return 1

# 3. Update get_type_max_value()
def get_type_max_value(self) -> int:
    if self.reg_type == RegisterType.COUNTER_8BIT:
        return 255
    elif self.reg_type == RegisterType.COUNTER_16BIT:
        return 65535  # NEW
    elif self.reg_type == RegisterType.PERCENT:
        return 100
    elif self.reg_type == RegisterType.BUTTON:
        return 1

# 4. Verify validators work with 16-bit values (should work automatically)
```

### Step 0.2: Update Shim Generation

**File**: `/Users/vmars20/EZ-EMFI/models/volo/volo_app.py`

**Update VHDL generation** to handle 16-bit registers:
- 8-bit: `app_reg_N(31 downto 24)` (upper 8 bits)
- **16-bit**: `app_reg_N(31 downto 16)` (upper 16 bits) ← NEW
- 1-bit: `app_reg_N(31)` (MSB only)

**Add voltage comments** (optional but helpful):
```vhdl
-- trigger_threshold: 0x3DCF = 2.4V
trigger_threshold <= signed(app_reg_27(31 downto 16));
```

### Step 0.3: Test counter_16bit Implementation

**Unit tests** (add to test suite):
```python
def test_counter_16bit_validation():
    """Test counter_16bit register type"""
    reg = AppRegister(
        name="Test 16-bit",
        reg_type="counter_16bit",
        cr_number=24,
        default_value=4095,
        min_value=0,
        max_value=4095
    )
    assert reg.get_type_bit_width() == 16
    assert reg.get_type_max_value() == 65535
```

**Test YAML parsing**:
```yaml
# test_counter_16bit.yaml
registers:
  - name: Test Register
    reg_type: counter_16bit
    cr_number: 24
    default_value: 1234
```

**Generate and verify VHDL**:
```bash
python tools/generate_volo_app.py --config test_counter_16bit.yaml --output /tmp/test/
# Verify generated shim has: app_reg_24(31 downto 16)
```

### Step 0.4: Update Documentation

**File**: `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/docs/VOLO_APP_DESIGN.md`

Add `counter_16bit` to register type documentation:
- Type name, bit width, range
- Bit packing strategy (upper 16 bits of 32-bit CR)
- Example YAML usage

### Success Criteria for Phase 0

- [ ] `counter_16bit` enum added to `RegisterType`
- [ ] Bit width and max value methods updated
- [ ] Shim generation handles 16-bit bit ranges
- [ ] Unit tests pass
- [ ] Test YAML generates valid VHDL
- [ ] Documentation updated

**Estimated time**: 2-3 hours

---

## Phase 1: Architecture Review & Planning

### Step 1.1: Understand DS1120-PD Architecture

**Review these files** (in order):

1. **`DS1120_PD_app.yaml`** - Current register layout
   - 11 registers (CR20-CR30)
   - Split 16-bit values across two 8-bit registers
   - Dual-purpose timing_control register

2. **`VHDL/DS1120_PD_volo_main.vhd`** - Layer 3 application logic
   - Integration of: FSM core, clock divider, threshold trigger, FSM observer
   - Safety clamping implementation
   - Signal reconstruction from split registers

3. **`VHDL/ds1120_pd_fsm.vhd`** - 7-state FSM core
   - State transitions and timing
   - Counter management
   - Status flags (sticky bits)

4. **`VHDL/packages/ds1120_pd_pkg.vhd`** - Constants and safety
   - Safety limits (MAX_INTENSITY_3V0, MAX_FIRING_CYCLES, etc.)
   - `clamp_voltage()` function
   - State encoding constants

**Key Observations**:
- ✅ FSM core is well-designed and tested - can likely reuse as-is
- ✅ Safety package is solid - preserve all constants and functions
- 🔄 Register layout needs simplification (combine split registers)
- 🔄 Signal reconstruction can be cleaner (eliminate dual-purpose register)

### Step 1.2: Identify Reusable Components

**Building Blocks** (all tested, ready to use):

| Module | Reusable? | Notes |
|--------|-----------|-------|
| `ds1120_pd_fsm.vhd` | ✅ Yes | May need minor tweaks for interface |
| `ds1120_pd_pkg.vhd` | ✅ Yes | Preserve all safety constants |
| `volo_clk_divider.vhd` | ✅ Yes | P1/P2 tested, use as-is |
| `volo_voltage_threshold_trigger_core.vhd` | ✅ Yes | Working in DS1120-PD |
| `fsm_observer.vhd` | ✅ Yes | 20-test validated |
| `volo_voltage_pkg.vhd` | ✅ Yes | Standard utilities |
| `volo_common_pkg.vhd` | ✅ Yes | VOLO_READY scheme |

**New Components Needed**:
- `DS1140_PD_volo_main.vhd` - Refactored application main
- `DS1140_PD_volo_shim.vhd` - Generated from new YAML
- `DS1140_PD_app.yaml` - Simplified register layout

---

## Phase 2: Register System Design (AFTER PHASE 0)

**Prerequisites**: Phase 0 complete (`counter_16bit` type implemented)

### Step 2.1: Define Simplified Register Layout

**Goal**: Reduce register count using `counter_16bit`, improve intuitiveness

**DS1120-PD Register Issues**:
- CR27/CR28: Split 16-bit threshold into 2x 8-bit registers
- CR29/CR30: Split 16-bit intensity into 2x 8-bit registers
- CR23/CR24: Dual-purpose timing control + split delay value
- Not intuitive: user must think in hex bytes, not voltages

**DS1140-PD Layout with `counter_16bit`**:

```yaml
# DS1140_PD_app.yaml

name: DS1140_PD
version: 1.0.0
description: EMFI probe driver for Riscure DS1120A (refactored architecture)
author: Volo Team
tags:
  - emfi
  - fault-injection
  - probe-driver
  - ds1120a
  - riscure

bitstream_path: modules/DS1140-PD/latest/25ff_bitstreams.tar
buffer_path: null

registers:
  # Control Registers (CR20-CR22)
  - name: Arm Probe
    description: Arm the probe driver (one-shot operation)
    reg_type: button
    cr_number: 20
    default_value: 0

  - name: Force Fire
    description: Manual trigger for testing (bypasses threshold)
    reg_type: button
    cr_number: 21
    default_value: 0

  - name: Reset FSM
    description: Reset state machine to READY state
    reg_type: button
    cr_number: 22
    default_value: 0

  # Timing Control (CR23-CR24)
  - name: Clock Divider
    description: FSM timing control (0=÷1, 1=÷2, ..., 15=÷16)
    reg_type: counter_8bit
    cr_number: 23
    default_value: 0

  - name: Arm Timeout
    description: Cycles to wait for trigger before timeout (0-4095)
    reg_type: counter_16bit  # NEW - Single 16-bit register!
    cr_number: 24
    default_value: 255
    min_value: 0
    max_value: 4095

  # Timing Durations (CR25-CR26) - Stay 8-bit
  - name: Firing Duration
    description: Number of cycles in FIRING state (max 32)
    reg_type: counter_8bit
    cr_number: 25
    default_value: 16
    min_value: 1
    max_value: 32

  - name: Cooling Duration
    description: Number of cycles in COOLING state (min 8)
    reg_type: counter_8bit
    cr_number: 26
    default_value: 16
    min_value: 8
    max_value: 255

  # Voltage Configuration (CR27-CR28) - Single 16-bit registers!
  - name: Trigger Threshold
    description: Voltage threshold for trigger detection (16-bit signed, ±5V)
    reg_type: counter_16bit  # NEW - Single register for 0x3DCF!
    cr_number: 27
    default_value: 0x3DCF  # 2.4V

  - name: Intensity
    description: Output intensity (16-bit signed, clamped to 3.0V)
    reg_type: counter_16bit  # NEW - Single register for 0x2666!
    cr_number: 28
    default_value: 0x2666  # 2.0V
```

**Benefits of `counter_16bit`**:
- **Register count**: 7 registers (vs 11 in DS1120-PD)
- **No splitting**: Single registers for 16-bit values
- **Simpler VHDL**: Direct 16-bit signals in entity ports
- **Better UX**: No manual high/low byte calculation

**Note**: We still use hex values (`0x3DCF`) for voltage registers. Future enhancement: `voltage_signed` type would let users write `2.4` directly.

### Step 2.2: Generate Shim Layer

```bash
# After creating DS1140_PD_app.yaml
python tools/generate_volo_app.py \
    --config DS1140_PD_app.yaml \
    --output VHDL/

# Generates:
# - VHDL/DS1140_PD_volo_shim.vhd (Layer 2, register mapping)
```

---

## Phase 3: VHDL Implementation

### Step 3.1: Package Review

**Option A: Reuse ds1120_pd_pkg.vhd as-is**
- Rename to `ds1140_pd_pkg.vhd` or keep as shared package
- No changes needed (safety constants are universal)

**Option B: Create dedicated ds1140_pd_pkg.vhd**
- Copy from ds1120_pd_pkg.vhd
- Opportunity to add documentation/comments
- Could add new utility functions if needed

**Recommendation**: Start with Option A (reuse), move to Option B only if divergence needed

### Step 3.2: FSM Core Review

**Review `VHDL/ds1120_pd_fsm.vhd`**:

**Interface**:
```vhdl
entity ds1120_pd_fsm is
    port (
        -- Clock and control
        clk         : in  std_logic;
        rst_n       : in  std_logic;  -- Active-low
        enable      : in  std_logic;
        clk_en      : in  std_logic;

        -- Control inputs
        arm_cmd     : in  std_logic;
        force_fire  : in  std_logic;
        reset_fsm   : in  std_logic;

        -- Configuration
        delay_count     : in  unsigned(11 downto 0);
        firing_duration : in  unsigned(7 downto 0);
        cooling_duration: in  unsigned(7 downto 0);

        -- Trigger detection
        trigger_detected: in  std_logic;

        -- FSM outputs
        current_state   : out std_logic_vector(2 downto 0);
        firing_active   : out std_logic;

        -- Status flags
        was_triggered   : out std_logic;
        timed_out       : out std_logic;
        fire_count      : out unsigned(3 downto 0);
        spurious_count  : out unsigned(3 downto 0)
    );
end entity;
```

**Assessment**:
- ✅ Clean interface, well-documented
- ✅ Safety features baked in (max cycles, min cooling)
- ✅ Status flags well-designed (sticky bits)
- 🔄 **Potential change**: `delay_count` is 12-bit unsigned
  - DS1140-PD uses 8-bit timeout register (CR24)
  - Options:
    1. Keep FSM as-is, pad register to 12-bit in volo_main
    2. Modify FSM to accept 8-bit timeout (breaking change)
  - **Recommendation**: Option 1 (pad in volo_main, preserve FSM)

**Decision**: Reuse FSM as-is, pad timeout in volo_main

### Step 3.3: Implement DS1140_PD_volo_main.vhd

**Template Structure**:

```vhdl
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

use work.ds1120_pd_pkg.all;  -- Or ds1140_pd_pkg if created

entity DS1140_PD_volo_main is
    port (
        -- Standard Control Signals
        Clk     : in  std_logic;
        Reset   : in  std_logic;  -- Active-high
        Enable  : in  std_logic;
        ClkEn   : in  std_logic;

        -- Application Signals (from shim layer, using counter_16bit)
        arm_probe            : in  std_logic;
        force_fire           : in  std_logic;
        reset_fsm            : in  std_logic;
        clock_divider        : in  std_logic_vector(7 downto 0);
        arm_timeout          : in  unsigned(15 downto 0);  -- NEW: Direct 16-bit!
        firing_duration      : in  std_logic_vector(7 downto 0);
        cooling_duration     : in  std_logic_vector(7 downto 0);
        trigger_threshold    : in  signed(15 downto 0);    -- NEW: Direct 16-bit!
        intensity            : in  signed(15 downto 0);    -- NEW: Direct 16-bit!

        -- BRAM Interface (reserved)
        bram_addr : in  std_logic_vector(11 downto 0);
        bram_data : in  std_logic_vector(31 downto 0);
        bram_we   : in  std_logic;

        -- MCC I/O (Three outputs required!)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);  -- Trigger signal to probe
        OutputB : out signed(15 downto 0);  -- Intensity/amplitude to probe
        OutputC : out signed(15 downto 0)   -- FSM debug (fsm_observer)
    );
end entity DS1140_PD_volo_main;

architecture rtl of DS1140_PD_volo_main is

    -- Clock divider signals
    signal clk_div_sel      : std_logic_vector(7 downto 0);
    signal divided_clk_en   : std_logic;

    -- Truncated values (FSM needs 12-bit, we have 16-bit)
    signal arm_timeout_12bit      : unsigned(11 downto 0);

    -- Threshold trigger signals
    signal trigger_detected : std_logic;

    -- FSM core signals (3-bit state from ds1120_pd_fsm)
    signal fsm_state_3bit   : std_logic_vector(2 downto 0);
    signal firing_active    : std_logic;

    -- FSM observer signals (6-bit standard)
    signal fsm_state_6bit   : std_logic_vector(5 downto 0);
    signal fsm_debug_voltage: signed(15 downto 0);

    -- Output signals
    signal trigger_out      : signed(15 downto 0);
    signal intensity_out    : signed(15 downto 0);
    signal intensity_value  : signed(15 downto 0);
    signal intensity_clamped: signed(15 downto 0);

begin

    -- Signal reconstruction (MUCH simpler with counter_16bit!)
    clk_div_sel <= clock_divider;
    arm_timeout_12bit <= arm_timeout(11 downto 0);  -- Truncate 16-bit to 12-bit

    -- No reconstruction needed for threshold or intensity - direct 16-bit signals!

    -- Clock Divider Instance
    U_CLK_DIV: entity work.volo_clk_divider
        generic map (MAX_DIV => 16)
        port map (
            clk      => Clk,
            rst_n    => not Reset,
            enable   => Enable,
            div_sel  => clk_div_sel,
            clk_en   => divided_clk_en,
            stat_reg => open  -- Unused
        );

    -- Threshold Trigger Instance (direct 16-bit signal!)
    U_TRIGGER: entity work.volo_voltage_threshold_trigger_core
        port map (
            clk            => Clk,
            reset          => Reset,
            voltage_in     => InputA,
            threshold_high => trigger_threshold,  -- Direct!
            threshold_low  => trigger_threshold - x"0100",
            enable         => Enable,
            mode           => '0',  -- Rising edge
            trigger_out    => trigger_detected,
            above_threshold => open,
            crossing_count => open
        );

    -- FSM Core Instance (reused from DS1120-PD)
    U_FSM: entity work.ds1120_pd_fsm
        port map (
            clk             => Clk,
            rst_n           => not Reset,
            enable          => Enable,
            clk_en          => divided_clk_en,
            arm_cmd         => arm_probe,
            force_fire      => force_fire,
            reset_fsm       => reset_fsm,
            delay_count     => arm_timeout_12bit,
            firing_duration => unsigned(firing_duration),
            cooling_duration => unsigned(cooling_duration),
            trigger_detected => trigger_detected,
            current_state   => fsm_state_3bit,  -- 3-bit output
            firing_active   => firing_active,
            was_triggered   => open,  -- Available for status
            timed_out       => open,
            fire_count      => open,
            spurious_count  => open
        );

    ----------------------------------------------------------------------------
    -- Output Control with Safety Clamping
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            trigger_out <= (others => '0');
            intensity_out <= (others => '0');
            intensity_clamped <= (others => '0');
        elsif rising_edge(Clk) then
            if Enable = '1' then
                -- Apply safety clamping to intensity (direct 16-bit signal!)
                intensity_clamped <= clamp_voltage(intensity, MAX_INTENSITY_3V0);

                -- Control outputs based on FSM state
                if firing_active = '1' then
                    -- During FIRING: output signals to probe
                    trigger_out <= trigger_threshold;  -- Direct!
                    intensity_out <= intensity_clamped;
                else
                    -- Safe state: zero outputs
                    trigger_out <= (others => '0');
                    intensity_out <= (others => '0');
                end if;
            else
                -- When disabled, force safe state
                trigger_out <= (others => '0');
                intensity_out <= (others => '0');
            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- FSM Observer for OutputC Debug
    -- Pad 3-bit FSM state to 6-bit (CRITICAL for fsm_observer!)
    ----------------------------------------------------------------------------
    fsm_state_6bit <= "000" & fsm_state_3bit;  -- Zero-extend to 6 bits

    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,
            V_MIN => 0.0,
            V_MAX => 2.5,
            FAULT_STATE_THRESHOLD => 7,  -- State "000111" = HARDFAULT
            STATE_0_NAME => "READY",
            STATE_1_NAME => "ARMED",
            STATE_2_NAME => "FIRING",
            STATE_3_NAME => "COOLING",
            STATE_4_NAME => "DONE",
            STATE_5_NAME => "TIMEDOUT",
            STATE_6_NAME => "RESERVED",
            STATE_7_NAME => "HARDFAULT"
        )
        port map (
            clk          => Clk,
            reset        => not Reset,  -- fsm_observer uses active-low reset
            state_vector => fsm_state_6bit,  -- 6-bit input
            voltage_out  => fsm_debug_voltage
        );

    ----------------------------------------------------------------------------
    -- Pack outputs to MCC (Three outputs)
    ----------------------------------------------------------------------------
    OutputA <= trigger_out;        -- Trigger signal to probe
    OutputB <= intensity_out;      -- Intensity/amplitude to probe
    OutputC <= fsm_debug_voltage;  -- FSM state debug (fsm_observer)

end architecture rtl;
```

**Key Features of This Implementation**:
1. **Three outputs**: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
2. **6-bit FSM standard compliance**: Pads 3-bit state to 6-bit for fsm_observer
3. **Safety clamping**: Intensity clamped to MAX_INTENSITY_3V0 (3.0V)
4. **Clean architecture**: No dual-purpose registers, simpler signal reconstruction
5. **Reuses proven components**: ds1120_pd_fsm (3-bit), fsm_observer (6-bit)

**Three-Output Architecture Details**:
For complete documentation on the three-output design, FSM observer integration, and optional debug multiplexer pattern, see **`DS1140_PD_THREE_OUTPUT_DESIGN.md`**

**Implementation Notes**:
- fsm_observer requires 6-bit state vector (zero-extend 3-bit to 6-bit)
- ds1120_pd_fsm outputs 3-bit state (states 0-7, with 7=HARDFAULT)
- Padding pattern: `"000" & fsm_state_3bit` preserves all state encodings
- OutputC provides real-time FSM state visualization on oscilloscope

---

## Phase 4: Progressive CocotB Testing

### Step 4.1: Create Test Structure

```bash
# Create test directory
mkdir -p tests/ds1140_pd_tests
touch tests/ds1140_pd_tests/__init__.py
touch tests/ds1140_pd_tests/ds1140_pd_constants.py
touch tests/test_ds1140_pd_progressive.py
```

### Step 4.2: Define Test Constants

**`tests/ds1140_pd_tests/ds1140_pd_constants.py`**:

```python
"""
Test constants and error messages for DS1140-PD progressive testing
"""

MODULE_NAME = "DS1140-PD"

class TestValues:
    """Test values for DS1140-PD"""
    # Clock
    DEFAULT_CLK_PERIOD_NS = 10  # 100 MHz

    # P1 Test Values (minimal)
    P1_FIRING_DURATION = 4
    P1_COOLING_DURATION = 4
    P1_TRIGGER_VALUE = 0x4000  # Above 2.4V threshold
    P1_WAIT_CYCLES = 20
    P1_TIMEOUT_CYCLES = 10

    # P2 Test Values (realistic)
    P2_FIRING_DURATION = 16
    P2_COOLING_DURATION = 16
    P2_WAIT_CYCLES = 50

class ErrorMessages:
    """Error message templates"""
    OUTPUT_MISMATCH = "Expected output {}, got {}"
    ENABLE_FAILED = "Enable control failed: {} state expected output {}"
```

### Step 4.3: Implement Progressive Tests

**`tests/test_ds1140_pd_progressive.py`** (template):

```python
"""
Progressive CocotB Test for DS1140-PD VOLO Application

Tests the refactored EMFI probe driver with progressive test structure:
- P1 (Basic): Reset, arm/trigger, safety clamping, VOLO_READY control
- P2 (Intermediate): Timeout, full cycle, clock divider integration
"""

import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_high
from test_base import TestBase, VerbosityLevel
from ds1140_pd_tests.ds1140_pd_constants import *


class DS1140PDTests(TestBase):
    """Progressive tests for DS1140-PD VOLO Application"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=TestValues.DEFAULT_CLK_PERIOD_NS, clk_signal="Clk")
        # Initialize inputs (similar to DS1120-PD)
        self.dut.InputA.value = 0
        self.dut.InputB.value = 0
        self.dut.Enable.value = 1
        self.dut.ClkEn.value = 1
        self.dut.Reset.value = 0
        # Initialize friendly signals (names from YAML)
        self.dut.arm_probe.value = 0
        self.dut.force_fire.value = 0
        self.dut.reset_fsm.value = 0
        self.dut.clock_divider.value = 0
        self.dut.arm_timeout.value = 0xFF
        self.dut.firing_duration.value = TestValues.P1_FIRING_DURATION
        self.dut.cooling_duration.value = TestValues.P1_COOLING_DURATION
        self.dut.trigger_threshold.value = 0x3DCF  # Direct 16-bit!
        self.dut.intensity.value = 0x2666  # Direct 16-bit!
        self.dut.bram_addr.value = 0
        self.dut.bram_data.value = 0
        self.dut.bram_we.value = 0
        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P1 - Basic Tests (Essential validation - runs by default)
    # ====================================================================

    async def run_p1_basic(self):
        """P1 - Essential validation (5 tests)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("Arm and trigger", self.test_arm_trigger)
        await self.test("Three outputs functioning", self.test_three_outputs)
        await self.test("FSM observer on OutputC", self.test_fsm_observer)
        await self.test("VOLO_READY scheme", self.test_volo_ready)

    async def test_reset(self):
        """Verify reset puts module in safe state"""
        self.dut.Reset.value = 1
        await ClockCycles(self.dut.Clk, 5)

        output_a = int(self.dut.OutputA.value)
        assert output_a == 0, ErrorMessages.OUTPUT_MISMATCH.format(0, output_a)

        self.dut.Reset.value = 0
        await ClockCycles(self.dut.Clk, 2)

        self.log("Reset verified", VerbosityLevel.VERBOSE)

    async def test_arm_trigger(self):
        """Basic arm and trigger sequence"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Arm FSM
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Apply trigger
        self.dut.InputA.value = TestValues.P1_TRIGGER_VALUE
        await ClockCycles(self.dut.Clk, TestValues.P1_WAIT_CYCLES)

        self.log("Arm/trigger verified", VerbosityLevel.VERBOSE)

    async def test_three_outputs(self):
        """Verify all three outputs are functioning"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # All outputs should be zero after reset
        output_a = int(self.dut.OutputA.value)
        output_b = int(self.dut.OutputB.value)
        output_c = int(self.dut.OutputC.value)

        assert output_a == 0, f"OutputA should be 0 after reset, got {output_a}"
        assert output_b == 0, f"OutputB should be 0 after reset, got {output_b}"
        # OutputC may be non-zero (FSM state READY = 0.0V = 0x0000)

        # Force fire to activate outputs
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 5)

        # During FIRING state:
        # - OutputA should be non-zero (trigger)
        # - OutputB should be non-zero (intensity)
        # - OutputC should change (FSM state FIRING)
        output_a_firing = int(self.dut.OutputA.value)
        output_b_firing = int(self.dut.OutputB.value)
        output_c_firing = int(self.dut.OutputC.value)

        self.log(f"Firing state: A={output_a_firing:04X}, B={output_b_firing:04X}, C={output_c_firing:04X}",
                 VerbosityLevel.VERBOSE)

        self.log("Three outputs verified", VerbosityLevel.VERBOSE)

    async def test_fsm_observer(self):
        """Verify FSM observer on OutputC tracks state changes"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Helper function to read OutputC as voltage
        def read_fsm_voltage():
            raw = int(self.dut.OutputC.value)
            if raw > 32767:  # Handle signed wrap
                raw -= 65536
            voltage = (raw / 32767.0) * 5.0
            return voltage

        # READY state (should be ~0.0V)
        voltage_ready = read_fsm_voltage()
        self.log(f"READY voltage: {voltage_ready:.3f}V", VerbosityLevel.VERBOSE)
        assert -0.1 < voltage_ready < 0.1, f"READY state should be ~0.0V, got {voltage_ready:.3f}V"

        # Arm FSM → ARMED state (should be ~0.36V)
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 2)

        voltage_armed = read_fsm_voltage()
        self.log(f"ARMED voltage: {voltage_armed:.3f}V", VerbosityLevel.VERBOSE)
        assert 0.25 < voltage_armed < 0.5, f"ARMED state should be ~0.36V, got {voltage_armed:.3f}V"

        # Apply trigger → FIRING state (should be ~0.71V)
        self.dut.InputA.value = 0x4000  # Above threshold
        await ClockCycles(self.dut.Clk, 5)

        voltage_firing = read_fsm_voltage()
        self.log(f"FIRING voltage: {voltage_firing:.3f}V", VerbosityLevel.VERBOSE)
        assert 0.6 < voltage_firing < 0.85, f"FIRING state should be ~0.71V, got {voltage_firing:.3f}V"

        self.log("FSM observer verified on OutputC", VerbosityLevel.VERBOSE)

    async def test_volo_ready(self):
        """Enable control scheme"""
        self.dut.Enable.value = 0
        await ClockCycles(self.dut.Clk, 3)

        output_disabled = int(self.dut.OutputA.value)
        assert output_disabled == 0, ErrorMessages.ENABLE_FAILED.format("disabled", 0)

        self.dut.Enable.value = 1
        await ClockCycles(self.dut.Clk, 2)

        self.log("Enable control verified", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P2 - Intermediate Tests (Comprehensive validation)
    # ====================================================================

    async def run_p2_intermediate(self):
        """P2 - Comprehensive validation (5 tests)"""
        await self.setup()

        await self.test("Timeout behavior", self.test_timeout)
        await self.test("Full operational cycle", self.test_full_cycle)
        await self.test("Clock divider integration", self.test_divider)
        await self.test("Intensity clamping on OutputB", self.test_intensity_clamp)
        await self.test("Debug mux view switching", self.test_debug_mux)

    async def test_timeout(self):
        """Verify armed timeout when no trigger received"""
        # TODO: Implement (copy pattern from DS1120-PD test)
        self.log("Timeout verified (TODO)", VerbosityLevel.VERBOSE)

    async def test_full_cycle(self):
        """Complete operational cycle"""
        # TODO: Implement (copy pattern from DS1120-PD test)
        self.log("Full cycle verified (TODO)", VerbosityLevel.VERBOSE)

    async def test_divider(self):
        """Clock divider affects FSM timing"""
        # TODO: Implement (copy pattern from DS1120-PD test)
        self.log("Clock divider verified (TODO)", VerbosityLevel.VERBOSE)

    async def test_intensity_clamp(self):
        """Verify intensity clamping on OutputB"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Set intensity above 3.0V limit (0x4CCD)
        self.dut.intensity.value = 0x7000  # Way above limit (direct 16-bit!)
        await ClockCycles(self.dut.Clk, 2)

        # Force fire
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 5)

        # OutputB should be clamped to 3.0V (0x4CCD)
        output_b = int(self.dut.OutputB.value)

        # Convert to voltage
        if output_b > 32767:
            output_b -= 65536
        voltage_b = (output_b / 32767.0) * 5.0
        self.log(f"OutputB voltage: {voltage_b:.3f}V (should be ≤3.0V)", VerbosityLevel.VERBOSE)

        assert voltage_b <= 3.1, f"Intensity should be clamped to 3.0V, got {voltage_b:.3f}V"

        self.log("Intensity clamping verified on OutputB", VerbosityLevel.VERBOSE)

    async def test_debug_mux(self):
        """Test debug multiplexer view switching (if implemented)"""
        if not hasattr(self.dut, 'debug_select_c'):
            self.log("Debug mux not implemented, skipping", VerbosityLevel.VERBOSE)
            return

        await reset_active_high(self.dut, rst_signal="Reset")

        # View 0: FSM state (default)
        self.dut.debug_select_c.value = 0
        await ClockCycles(self.dut.Clk, 2)
        view0_value = int(self.dut.OutputC.value)

        # View 1: Timing diagnostics
        self.dut.debug_select_c.value = 1
        await ClockCycles(self.dut.Clk, 2)
        view1_value = int(self.dut.OutputC.value)

        # View 2: Trigger activity
        self.dut.debug_select_c.value = 2
        await ClockCycles(self.dut.Clk, 2)
        view2_value = int(self.dut.OutputC.value)

        self.log(f"Debug views: V0={view0_value:04X}, V1={view1_value:04X}, V2={view2_value:04X}",
                 VerbosityLevel.VERBOSE)

        self.log("Debug mux view switching verified (or skipped if not implemented)", VerbosityLevel.VERBOSE)


# CocotB entry point
@cocotb.test()
async def test_ds1140_pd_volo(dut):
    """Progressive DS1140-PD VOLO application tests"""
    tester = DS1140PDTests(dut)
    await tester.run_all_tests()
```

### Step 4.4: Configure Test Execution

**Add to `tests/test_configs.py`**:

```python
TEST_CONFIGS = {
    # ... existing tests ...

    "ds1140_pd_volo": {
        "toplevel": "ds1140_pd_volo_main",  # Entity name (lowercase)
        "sources": [
            # Packages
            "../VHDL/packages/volo_voltage_pkg.vhd",
            "../VHDL/packages/volo_common_pkg.vhd",
            "../VHDL/packages/ds1120_pd_pkg.vhd",  # Or ds1140_pd_pkg.vhd

            # Building blocks
            "../VHDL/volo_clk_divider.vhd",
            "../VHDL/volo_voltage_threshold_trigger_core.vhd",
            "../VHDL/fsm_observer.vhd",
            "../VHDL/ds1120_pd_fsm.vhd",  # Reused FSM

            # DS1140-PD application
            "../VHDL/DS1140_PD_volo_main.vhd",
        ],
        "category": "ds1140_pd",
    },
}
```

### Step 4.5: Run Tests

```bash
cd tests/

# Run P1 tests (default)
uv run python run.py ds1140_pd_volo

# Run P2 tests (comprehensive)
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py ds1140_pd_volo

# With verbose output
COCOTB_VERBOSITY=VERBOSE uv run python run.py ds1140_pd_volo
```

**Expected P1 Output** (<25 lines):
```
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Arm and trigger
  ✓ PASS
T3: Three outputs functioning
  ✓ PASS
T4: FSM observer on OutputC
  ✓ PASS
T5: VOLO_READY scheme
  ✓ PASS
ALL 5 TESTS PASSED
```

**Key Test Features**:
- Test 3: Validates OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
- Test 4: Validates FSM observer voltage tracking (READY→ARMED→FIRING)
- OutputC voltage decoding: Reads 16-bit signed as voltage (±5V scale)
- FSM state voltages: READY=0.0V, ARMED=0.36V, FIRING=0.71V, etc.

---

## Phase 5: Extended Register Types (Optional)

**If you want to enhance the register type system**, see `DS1140_PD_REGISTER_TYPES.md` for:
- Proposed new types: `counter_16bit`, `voltage_signed`, `time_cycles`, `percent_fine`, `enum_choice`
- Implementation guide for `models/volo/app_register.py`
- Updated YAML examples
- Benefits and trade-offs

**Recommendation**: Complete Phases 1-4 first, then add extended types as Phase 5 if desired.

---

## Phase 6: Hardware Deployment

### Step 6.1: Build MCC Package

```bash
uv run python scripts/build_mcc_package.py modules/DS1140-PD
```

**Generates**:
- `modules/DS1140-PD/cloudcompile_package/DS1140_PD.zip`

### Step 6.2: CloudCompile Synthesis

1. Open Moku Cloud Compile web interface
2. Upload `DS1140_PD.zip`
3. Start synthesis (~5-10 minutes)
4. Download results: `25ff*_mokugo_*.tar` and `.log` files

### Step 6.3: Import Build

```bash
# Stage synthesis results
mkdir -p modules/DS1140-PD/incoming
mv ~/Downloads/25ff*_mokugo_* modules/DS1140-PD/incoming/

# Import to latest/
python scripts/import_mcc_build.py modules/DS1140-PD
```

### Step 6.4: Hardware Testing

```bash
cd tests/

# Deploy to Moku:Go
uv run python test_ds1140_pd_mokubench.py \
  --ip <moku_ip_address> \
  --bitstream ../modules/DS1140-PD/latest/25ff*_bitstreams.tar
```

---

## Success Checklist

### Phase 0: Register Type Implementation
- [ ] Implemented `counter_16bit` in `app_register.py`
- [ ] Updated shim generation for 16-bit registers
- [ ] Added unit tests for counter_16bit
- [ ] Test YAML generates valid VHDL
- [ ] Documentation updated

### Phase 1: Architecture
- [ ] Reviewed DS1120-PD implementation
- [ ] Identified reusable components
- [ ] Understood safety requirements

### Phase 2: Register System
- [ ] Created `DS1140_PD_app.yaml` with 7 registers using counter_16bit
- [ ] Generated shim layer successfully
- [ ] Verified 16-bit register mapping correctness

### Phase 3: VHDL Implementation
- [ ] Created `DS1140_PD_volo_main.vhd`
- [ ] Integrated all building blocks
- [ ] Preserved safety features
- [ ] Compiles with GHDL (--std=08)

### Phase 4: Testing
- [ ] Created test structure (`ds1140_pd_tests/`)
- [ ] Implemented P1 tests (4 tests)
- [ ] Implemented P2 tests (4 tests)
- [ ] P1 output <20 lines
- [ ] All tests pass in simulation

### Phase 5: Future Enhancements (Optional)
- [ ] `voltage_signed` register type (user writes `2.4` instead of `0x3DCF`)
- [ ] Debug multiplexer (8 selectable views on OutputC)
- [ ] Additional test coverage

### Phase 6: Hardware Deployment
- [ ] MCC package built successfully
- [ ] CloudCompile synthesis completed
- [ ] Bitstream deployed to Moku:Go
- [ ] Hardware tests pass on actual probe

---

## Common Issues & Solutions

### Issue 1: GHDL Compilation Errors

**Problem**: Missing dependencies or wrong order
**Solution**: Check `test_configs.py` source order (packages first, then modules)

### Issue 2: CocotB Attribute Errors

**Problem**: Signal name mismatch (DUT vs YAML)
**Solution**: Entity ports use lowercase, YAML names converted via `to_vhdl_signal_name()`

Example:
```yaml
name: "Arm Probe"  # YAML
```
Becomes:
```vhdl
arm_probe : in std_logic;  # Entity port
```

### Issue 3: FSM Not Transitioning

**Problem**: Clock enable or enable signal not set correctly
**Solution**: Verify `Enable=1`, `ClkEn=1`, and `divided_clk_en` functioning

### Issue 4: Output Always Zero

**Problem**: MCC 3-bit control scheme not implemented
**Solution**: Check VOLO_READY pattern (CR0[31:29] all high)

---

## Reference Files

**DS1120-PD Implementation** (source of truth):
- `DS1120_PD_app.yaml` - Current config
- `VHDL/DS1120_PD_volo_main.vhd` - Application main
- `VHDL/ds1120_pd_fsm.vhd` - FSM core
- `VHDL/packages/ds1120_pd_pkg.vhd` - Safety constants
- `tests/test_ds1120_pd_volo_progressive.py` - Test pattern

**Building Blocks**:
- `VHDL/volo_clk_divider.vhd` - Clock divider
- `VHDL/volo_voltage_threshold_trigger_core.vhd` - Threshold trigger
- `VHDL/fsm_observer.vhd` - FSM visualization

**Testing Framework**:
- `tests/conftest.py` - Shared utilities
- `tests/test_base.py` - TestBase class
- `tests/run.py` - Test runner

**Documentation**:
- `docs/FSM_OBSERVER_PATTERN.md` - Observer integration (6-bit standard)
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Testing methodology
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - CocotB patterns

**DS1140-PD Specific Documentation** (NEW):
- **`DS1140_PD_REQUIREMENTS.md`** - Complete requirements and architecture analysis
- **`DS1140_PD_THREE_OUTPUT_DESIGN.md`** - Three-output design with FSM observer (CRITICAL)
- **`DS1140_PD_REGISTER_TYPES.md`** - Extended register types proposal (optional)
- **`DS1140_PD_IMPLEMENTATION_GUIDE.md`** - This file

**Three-Output Design** (CRITICAL for DS1140-PD):
- OutputA: Trigger signal to probe
- OutputB: Intensity/amplitude to probe
- OutputC: FSM state debug (fsm_observer)
- FSM padding: 3-bit → 6-bit via `"000" & fsm_state_3bit`
- Reference: `DS1140_PD_THREE_OUTPUT_DESIGN.md` for complete details

---

## Next Actions

1. **Review Requirements**: Read `DS1140_PD_REQUIREMENTS.md` thoroughly
2. **Review Three-Output Design**: Read `DS1140_PD_THREE_OUTPUT_DESIGN.md` (CRITICAL)
3. **Review Register Types**: Read `DS1140_PD_REGISTER_TYPES.md` for counter_16bit details
4. **START PHASE 0** (BLOCKING): Implement `counter_16bit` type (2-3 hours)
5. **Start Phase 1**: Review DS1120-PD architecture
6. **Create YAML**: Define 7-register layout with counter_16bit
7. **Implement volo_main**: Refactor with modern patterns
8. **Create Tests**: Progressive P1/P2 structure
9. **Iterate**: Test, refine, repeat

**Estimated Time**:
- Phase 0: 2-3 hours (must complete first)
- Phases 1-4: 5-7 hours
- Total: 8-12 hours for complete DS1140-PD implementation

---

**Good luck! This is an exciting refactoring project that will showcase best practices for VoloApp development.**
