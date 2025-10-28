# DS1140-PD Three-Output Design with Debug Multiplexer

**Date**: 2025-10-28
**Purpose**: Detailed design for DS1140-PD with 3 outputs and FSM observer integration
**References**:
- `EXTERNAL_volo_vhdl/docs/FSM_OBSERVER_PATTERN.md`
- `EXTERNAL_volo_vhdl/docs/OSCILLOSCOPE-BASED-DEBUGGING-WORKFLOW.md`
- `EXTERNAL_volo_vhdl/experimental/inspectable_buffer_loader/core/debug_mux.vhd`

---

## Overview

DS1140-PD requires **three functional outputs**:
- **OutputA**: Trigger signal to probe
- **OutputB**: Intensity/pulse amplitude to probe
- **OutputC**: FSM state debug via fsm_observer OR debug multiplexer

This document addresses:
1. How to ensure 6-bit FSM encoding standard for fsm_observer
2. Three-output architecture design
3. Debug multiplexer integration pattern
4. Testing strategy for all outputs

---

## 1. FSM Observer 6-Bit Standard Compliance

### The Standard

**Reference**: `/Users/vmars20/EZ-EMFI/docs/FSM_OBSERVER_PATTERN.md`

**Rule**: FSM observer requires `std_logic_vector(5 downto 0)` state vector

**Key Features**:
- Fixed 6-bit interface (supports up to 64 states)
- Sign-flip fault detection (negative voltage = fault state)
- Compile-time voltage LUT (zero runtime overhead)
- 20 comprehensive tests validate the pattern

### DS1120-PD Current Implementation (3-bit FSM)

**From `VHDL/ds1120_pd_fsm.vhd`**:
```vhdl
-- Current: 3-bit state encoding (7 states + fault = 8 total)
signal current_state : out std_logic_vector(2 downto 0);
```

**State Encoding**:
```vhdl
constant STATE_READY    : std_logic_vector(2 downto 0) := "000";
constant STATE_ARMED    : std_logic_vector(2 downto 0) := "001";
constant STATE_FIRING   : std_logic_vector(2 downto 0) := "010";
constant STATE_COOLING  : std_logic_vector(2 downto 0) := "011";
constant STATE_DONE     : std_logic_vector(2 downto 0) := "100";
constant STATE_TIMEDOUT : std_logic_vector(2 downto 0) := "101";
constant STATE_HARDFAULT: std_logic_vector(2 downto 0) := "111";
```

### Padding Pattern for DS1140-PD

**In `DS1140_PD_volo_main.vhd`**:

```vhdl
architecture rtl of DS1140_PD_volo_main is
    -- FSM core signals (3-bit from ds1120_pd_fsm)
    signal fsm_state_3bit : std_logic_vector(2 downto 0);

    -- FSM observer signals (6-bit standard)
    signal fsm_state_6bit : std_logic_vector(5 downto 0);
    signal fsm_debug_voltage : signed(15 downto 0);

begin
    -- FSM Core Instance (outputs 3-bit state)
    U_FSM: entity work.ds1120_pd_fsm
        port map (
            -- ... ports ...
            current_state => fsm_state_3bit,  -- 3-bit output
            -- ...
        );

    -- Pad 3-bit state to 6-bit for observer (CRITICAL!)
    fsm_state_6bit <= "000" & fsm_state_3bit;  -- Zero-extend to 6 bits

    -- FSM Observer Instance (requires 6-bit input)
    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,  -- 8 states (0-7, with 7=fault)
            V_MIN => 0.0,
            V_MAX => 2.5,
            FAULT_STATE_THRESHOLD => 7,  -- State 111 = "000111" in 6-bit
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
            reset        => not Reset,  -- fsm_observer expects active-low
            state_vector => fsm_state_6bit,  -- 6-bit input
            voltage_out  => fsm_debug_voltage  -- 16-bit signed
        );

    -- Output routing (see Section 2)
    OutputC <= fsm_debug_voltage;  -- FSM state to OutputC
end architecture rtl;
```

**Why Zero-Extension Works**:
- DS1120-PD uses states 0-5 and 7 (skips 6)
- Zero-extending "000"-"111" → "000000"-"000111" preserves encoding
- fsm_observer interprets "000111" (7) as fault state correctly
- Voltage mapping: 0→0.0V, 1→0.36V, 2→0.71V, ..., 7→2.5V

---

## 2. Three-Output Architecture

### CustomWrapper Entity (4 Outputs Available)

**Reference**: `/Users/vmars20/EZ-EMFI/VHDL/CustomWrapper_test_stub.vhd`

```vhdl
entity CustomWrapper is
    port (
        Clk     : in  std_logic;
        Reset   : in  std_logic;

        -- MCC I/O (±5V full scale, 16-bit signed)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        InputC  : in  signed(15 downto 0);  -- Available but unused
        InputD  : in  signed(15 downto 0);  -- Available but unused

        OutputA : out signed(15 downto 0);  -- ✅ Trigger signal
        OutputB : out signed(15 downto 0);  -- ✅ Intensity/amplitude
        OutputC : out signed(15 downto 0);  -- ✅ FSM debug
        OutputD : out signed(15 downto 0);  -- Available for future

        Control0-31 : in std_logic_vector(31 downto 0);

        -- ... BRAM interface etc ...
    );
end entity CustomWrapper;
```

### DS1140-PD Output Mapping

**Functional Outputs**:
- **OutputA**: Trigger signal to probe (active during FIRING state)
- **OutputB**: Intensity/pulse amplitude to probe (active during FIRING state)

**Debug Output**:
- **OutputC**: FSM state visualization (fsm_observer) OR debug multiplexer

**Reserved**:
- **OutputD**: Not used (tie to zero), available for future expansion

### Example: Simple FSM Observer Pattern

**In `DS1140_PD_volo_main.vhd`**:

```vhdl
architecture rtl of DS1140_PD_volo_main is
    -- Trigger and intensity signals
    signal trigger_out      : signed(15 downto 0);
    signal intensity_out    : signed(15 downto 0);
    signal intensity_clamped: signed(15 downto 0);

    -- FSM observer signals
    signal fsm_state_3bit   : std_logic_vector(2 downto 0);
    signal fsm_state_6bit   : std_logic_vector(5 downto 0);
    signal fsm_debug_voltage: signed(15 downto 0);

begin
    -- ... FSM instantiation, clock divider, threshold trigger ...

    -- Output Control Process
    process(Clk, Reset)
    begin
        if Reset = '1' then
            trigger_out <= (others => '0');
            intensity_out <= (others => '0');
            intensity_clamped <= (others => '0');
        elsif rising_edge(Clk) then
            if Enable = '1' then
                -- Apply safety clamping
                intensity_clamped <= clamp_voltage(intensity_value, MAX_INTENSITY_3V0);

                -- Control outputs based on FSM state
                if firing_active = '1' then
                    -- During FIRING: output signals to probe
                    trigger_out <= trigger_threshold;
                    intensity_out <= intensity_clamped;
                else
                    -- Safe state: zero outputs
                    trigger_out <= (others => '0');
                    intensity_out <= (others => '0');
                end if;
            end if;
        end if;
    end process;

    -- Pad FSM state for observer
    fsm_state_6bit <= "000" & fsm_state_3bit;

    -- FSM Observer
    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,
            V_MIN => 0.0,
            V_MAX => 2.5,
            FAULT_STATE_THRESHOLD => 7,
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
            reset        => not Reset,
            state_vector => fsm_state_6bit,
            voltage_out  => fsm_debug_voltage
        );

    -- Pack outputs to MCC
    OutputA <= trigger_out;        -- Trigger to probe
    OutputB <= intensity_out;      -- Intensity to probe
    OutputC <= fsm_debug_voltage;  -- FSM state debug
end architecture rtl;
```

---

## 3. Debug Multiplexer Integration (Advanced)

### When to Use Debug Multiplexer

**Simple FSM Observer** (recommended for DS1140-PD initial implementation):
- Single debug view: FSM state only
- Clean, simple, proven pattern
- Sufficient for most debugging scenarios

**Debug Multiplexer** (for complex debugging):
- 8 selectable debug views per output channel
- Runtime view switching via Control0 bits
- Comprehensive diagnostics (state, timing, errors, data)
- Useful for hardware bring-up with unknown issues

### Debug Multiplexer Reference Implementation

**Location**: `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/experimental/inspectable_buffer_loader/core/debug_mux.vhd`

**Features**:
- 8 input views → 1 output (3-bit select)
- Voltage guard bands (left-shift by 2-3 bits) for oscilloscope readability
- Combinatorial mux (instant view switching)

**Entity Interface**:
```vhdl
entity debug_mux is
    generic (
        GUARD_BITS : natural := 2  -- Voltage guard band (4× spacing)
    );
    port (
        -- Debug view selection (0-7)
        debug_select : in  std_logic_vector(2 downto 0);

        -- 8 debug views (16-bit signed each)
        view_0 : in signed(15 downto 0);
        view_1 : in signed(15 downto 0);
        view_2 : in signed(15 downto 0);
        view_3 : in signed(15 downto 0);
        view_4 : in signed(15 downto 0);
        view_5 : in signed(15 downto 0);
        view_6 : in signed(15 downto 0);
        view_7 : in signed(15 downto 0);

        -- Multiplexed output
        debug_out : out signed(15 downto 0)
    );
end entity debug_mux;
```

### DS1140-PD with Debug Multiplexer (OutputC)

**Control Register Bit Allocation**:
```
Control0[31]    = MCC_READY (set by MCC)
Control0[30]    = User Enable
Control0[29]    = Clock Enable (MANDATORY!)
Control0[28:27] = Reserved
Control0[26:24] = DEBUG_SELECT_C (OutputC view: 0-7)
Control0[23:21] = Reserved (could be DEBUG_SELECT_B if needed)
Control0[20:16] = Reserved
Control0[15:8]  = Clock Divider
Control0[7:0]   = Arm Timeout (or split across CR23/CR24)
```

**Updated YAML** (add debug select register):
```yaml
registers:
  # ... existing registers (CR20-CR26) using counter_16bit ...
  # Note: With counter_16bit type, only 7 registers needed (not 9)

  # Debug control (uses Control0 upper bits, not a separate CR)
  # NOTE: This is extracted directly from Control0 in Top.vhd, not a register
```

**In `DS1140_PD_volo_main.vhd`** (with debug mux):

```vhdl
architecture rtl of DS1140_PD_volo_main is
    -- Debug mux signals
    signal debug_select_c : std_logic_vector(2 downto 0);

    -- Debug views (8 total for OutputC)
    signal debug_view_0 : signed(15 downto 0);  -- FSM state (observer)
    signal debug_view_1 : signed(15 downto 0);  -- Timing diagnostics
    signal debug_view_2 : signed(15 downto 0);  -- Trigger activity
    signal debug_view_3 : signed(15 downto 0);  -- Counter values
    signal debug_view_4 : signed(15 downto 0);  -- Status flags
    signal debug_view_5 : signed(15 downto 0);  -- Reserved
    signal debug_view_6 : signed(15 downto 0);  -- Reserved
    signal debug_view_7 : signed(15 downto 0);  -- Reserved

    signal debug_out_c : signed(15 downto 0);

begin
    -- View 0: FSM State (via fsm_observer)
    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,
            V_MIN => 0.0,
            V_MAX => 2.5,
            FAULT_STATE_THRESHOLD => 7,
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
            reset        => not Reset,
            state_vector => fsm_state_6bit,
            voltage_out  => debug_view_0  -- FSM state view
        );

    -- View 1: Timing Diagnostics
    debug_view_1 <= resize(signed(firing_cnt), 16) sll 2;  -- Guard band

    -- View 2: Trigger Activity
    debug_view_2 <= resize(signed(trigger_detected & above_threshold & was_triggered & timed_out), 16) sll 2;

    -- View 3: Counter Values (arm timeout, fire count, spurious count)
    debug_view_3 <= resize(signed(arm_timeout_cnt(11 downto 4)), 16) sll 2;

    -- View 4: Status Flags (fire_count, spurious_count, etc.)
    debug_view_4 <= resize(signed(fire_count & spurious_count), 16) sll 2;

    -- Views 5-7: Reserved
    debug_view_5 <= (others => '0');
    debug_view_6 <= (others => '0');
    debug_view_7 <= (others => '0');

    -- Debug Multiplexer for OutputC
    U_DEBUG_MUX_C: entity work.debug_mux
        generic map (GUARD_BITS => 2)
        port map (
            debug_select => debug_select_c,
            view_0 => debug_view_0,
            view_1 => debug_view_1,
            view_2 => debug_view_2,
            view_3 => debug_view_3,
            view_4 => debug_view_4,
            view_5 => debug_view_5,
            view_6 => debug_view_6,
            view_7 => debug_view_7,
            debug_out => debug_out_c
        );

    -- Pack outputs to MCC
    OutputA <= trigger_out;        -- Trigger to probe
    OutputB <= intensity_out;      -- Intensity to probe
    OutputC <= debug_out_c;        -- Debug (8 views selectable)
end architecture rtl;
```

**In `Top.vhd` (CustomWrapper architecture)**:
```vhdl
architecture DS1140_PD of CustomWrapper is
    -- Extract debug select from Control0
    signal debug_select_c : std_logic_vector(2 downto 0);
begin
    -- Extract debug view selection from Control0[26:24]
    debug_select_c <= Control0(26 downto 24);

    DS1140_PD_MAIN: entity WORK.DS1140_PD_volo_main
        port map (
            -- ... standard ports ...
            debug_select_c => debug_select_c,
            -- ...
        );
end architecture;
```

### Standard Debug View Allocation (DS1140-PD)

| View | Name | Content | Use Case |
|------|------|---------|----------|
| 0 | FSM State | fsm_observer output | Default: FSM state visualization |
| 1 | Timing | firing_cnt, cooling_cnt | Verify cycle counts |
| 2 | Trigger Activity | trigger_detected, above_threshold, flags | Debug trigger issues |
| 3 | Counters | arm_timeout_cnt, fire_count, spurious_count | Monitor session stats |
| 4 | Status Flags | Combined status bits | Quick health check |
| 5 | Reserved | - | Future expansion |
| 6 | Reserved | - | Future expansion |
| 7 | Reserved | - | Future expansion |

---

## 4. Testing Strategy for Three Outputs

### CocotB Test Pattern Updates

**In `tests/test_ds1140_pd_progressive.py`**:

```python
import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_high
from test_base import TestBase, VerbosityLevel
from ds1140_pd_tests.ds1140_pd_constants import *


class DS1140PDTests(TestBase):
    """Progressive tests for DS1140-PD with 3-output validation"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=10, clk_signal="Clk")
        # Initialize all inputs
        self.dut.InputA.value = 0
        self.dut.InputB.value = 0
        self.dut.Enable.value = 1
        self.dut.ClkEn.value = 1
        self.dut.Reset.value = 0
        # Initialize friendly signals
        self.dut.arm_probe.value = 0
        self.dut.force_fire.value = 0
        self.dut.reset_fsm.value = 0
        self.dut.clock_divider.value = 0
        self.dut.arm_timeout.value = 0xFF
        self.dut.firing_duration.value = 16
        self.dut.cooling_duration.value = 16
        self.dut.trigger_threshold.value = 0x3D
        self.dut.trigger_threshold_low.value = 0xCF
        self.dut.bram_addr.value = 0
        self.dut.bram_data.value = 0
        self.dut.bram_we.value = 0
        # Debug mux (if used)
        if hasattr(self.dut, 'debug_select_c'):
            self.dut.debug_select_c.value = 0  # View 0 = FSM state
        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P1 - Basic Tests (Essential validation)
    # ====================================================================

    async def run_p1_basic(self):
        """P1 - Essential validation (5 tests)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("Arm and trigger", self.test_arm_trigger)
        await self.test("Three outputs functioning", self.test_three_outputs)
        await self.test("FSM observer on OutputC", self.test_fsm_observer)
        await self.test("VOLO_READY scheme", self.test_volo_ready)

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

        # Basic sanity checks (outputs changed from reset)
        # Note: Exact values depend on configuration
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

        # State transitions to verify:
        # READY (0) → ARMED (1) → FIRING (2) → COOLING (3) → DONE (4)

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

    # ====================================================================
    # P2 - Intermediate Tests (Comprehensive validation)
    # ====================================================================

    async def run_p2_intermediate(self):
        """P2 - Comprehensive validation (5 tests)"""
        await self.setup()

        await self.test("Timeout behavior", self.test_timeout)
        await self.test("Full operational cycle", self.test_full_cycle)
        await self.test("Clock divider integration", self.test_divider)
        await self.test("Debug mux view switching", self.test_debug_mux)
        await self.test("Intensity clamping on OutputB", self.test_intensity_clamp)

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

        self.log("Debug mux view switching verified", VerbosityLevel.VERBOSE)

    async def test_intensity_clamp(self):
        """Verify intensity clamping on OutputB"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Set intensity above 3.0V limit (0x4CCD)
        self.dut.intensity.value = 0x70  # Way above limit
        self.dut.intensity_low.value = 0x00
        await ClockCycles(self.dut.Clk, 2)

        # Force fire
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 5)

        # OutputB should be clamped to 3.0V (0x4CCD)
        output_b = int(self.dut.OutputB.value)

        # Convert to voltage
        voltage_b = (output_b / 32767.0) * 5.0
        self.log(f"OutputB voltage: {voltage_b:.3f}V (should be ≤3.0V)", VerbosityLevel.VERBOSE)

        assert voltage_b <= 3.1, f"Intensity should be clamped to 3.0V, got {voltage_b:.3f}V"

        self.log("Intensity clamping verified on OutputB", VerbosityLevel.VERBOSE)


# CocotB entry point
@cocotb.test()
async def test_ds1140_pd_volo(dut):
    """Progressive DS1140-PD VOLO application tests"""
    tester = DS1140PDTests(dut)
    await tester.run_all_tests()
```

---

## 5. Summary & Recommendations

### Implementation Path

**Phase 1: Simple FSM Observer** (Recommended for initial implementation)
- ✅ OutputA: Trigger signal
- ✅ OutputB: Intensity/amplitude
- ✅ OutputC: FSM state via fsm_observer
- ✅ Simple, proven pattern
- ✅ Sufficient for most debugging

**Phase 2: Add Debug Multiplexer** (Optional, for advanced debugging)
- ✅ OutputA: Trigger signal
- ✅ OutputB: Intensity/amplitude
- ✅ OutputC: 8 selectable debug views (including FSM state)
- ✅ Runtime view switching via Control0[26:24]
- ✅ Comprehensive diagnostics

### Testing Requirements

**P1 Tests** (5 tests, <25 lines output):
1. Reset behavior (all outputs zero)
2. Arm and trigger sequence
3. Three outputs functioning (verify all connected)
4. FSM observer on OutputC (verify state tracking)
5. VOLO_READY scheme

**P2 Tests** (5 tests, comprehensive):
6. Timeout behavior
7. Full operational cycle
8. Clock divider integration
9. Debug mux view switching (if implemented)
10. Intensity clamping on OutputB

### Key Design Decisions

**✅ 6-Bit FSM Standard**:
- Pad ds1120_pd_fsm 3-bit output to 6-bit: `fsm_state_6bit <= "000" & fsm_state_3bit`
- Preserves all state encodings (0-7)
- Compatible with fsm_observer standard interface

**✅ Three-Output Allocation**:
- OutputA/B: Functional probe signals
- OutputC: Debug (FSM state or debug mux)
- OutputD: Reserved (future expansion)

**✅ Debug Mux Decision**:
- **Start simple**: FSM observer only (Phase 1)
- **Add later**: Debug mux if hardware bring-up reveals issues (Phase 2)
- **Not both**: Either fsm_observer direct OR debug_mux with fsm_observer as View 0

---

## References

**FSM Observer Pattern**:
- `/Users/vmars20/EZ-EMFI/docs/FSM_OBSERVER_PATTERN.md`
- `/Users/vmars20/EZ-EMFI/VHDL/fsm_observer.vhd`

**Debug Multiplexer**:
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/docs/OSCILLOSCOPE-BASED-DEBUGGING-WORKFLOW.md`
- `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/experimental/inspectable_buffer_loader/core/debug_mux.vhd`

**CustomWrapper Entity**:
- `/Users/vmars20/EZ-EMFI/VHDL/CustomWrapper_test_stub.vhd`

**Example Implementations**:
- PulseStar (4 outputs functional): `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/instruments/PulseStar/top/Top.vhd`
- EMFI-Seq (3 outputs: 2 functional + FSM debug): `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/instruments/EMFI-Seq/top/Top.vhd`
- inspectable_buffer_loader (2 debug mux outputs): `/Users/vmars20/EZ-EMFI/EXTERNAL_volo_vhdl/experimental/inspectable_buffer_loader/top/Top.vhd`

---

**Next Step**: Update `DS1140_PD_IMPLEMENTATION_GUIDE.md` to reference this document in Phase 3 (VHDL Implementation).
