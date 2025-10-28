# FSM Observer Design Pattern

**Version:** 1.0
**Author:** VOLO Team
**Date:** 2025-01-28
**Status:** Production-Ready

## Overview

The FSM Observer is a **non-invasive monitoring pattern** that converts binary-encoded FSM states into oscilloscope-visible voltages for real-time debugging. It provides elegant fault detection via "sign-flip" indication while preserving debugging context.

### Key Features

- **Fixed 6-bit interface** - Single tested entity works with all FSMs
- **Zero runtime overhead** - Voltage LUT calculated at elaboration time
- **Sign-flip fault mode** - Negative voltage preserves "where did it fault from"
- **Generic configuration** - Customizable voltage ranges and state names
- **Non-invasive** - Parallel monitoring with no impact on FSM logic
- **Comprehensive testing** - 20 test cases covering core functionality and edge cases

### Design Philosophy

> "Make the invisible visible" - Convert abstract FSM states into physical voltages that can be measured, triggering on, and analyzed with standard test equipment.

---

## Pattern Architecture

### Three-Component System

```
┌─────────────┐
│   Your FSM  │──┐
│  (any size) │  │ state_vector (6-bit)
└─────────────┘  │
                 ├──→ ┌──────────────┐      ┌─────────────────┐
                 │    │ FSM Observer │─────→│  Oscilloscope   │
                 │    │   (Fixed)    │      │  (Moku DAC)     │
                 └──→ └──────────────┘      └─────────────────┘
                      clk, reset, generics   voltage_out (16-bit)
```

### Voltage Encoding Strategy

**Normal States:** Positive voltage stairstep (V_MIN → V_MAX)
```
IDLE     →  0.0V
ARMED    →  0.5V
FIRING   →  1.0V
COOLING  →  1.5V
DONE     →  2.0V
TIMEDOUT →  2.5V
```

**Fault States:** Sign-flipped magnitude of previous normal state
```
Example: ARMED(0.5V) → FIRING(1.0V) → HARDFAULT → output = -1.0V
                                         ↑
                            Magnitude preserves fault context
```

---

## Integration Guide

### Step 1: Design Your FSM with Fixed State Vector

**Rule:** Always use `std_logic_vector(5 downto 0)` for FSM state, even if your FSM has fewer states.

```vhdl
architecture rtl of my_fsm is
    -- FSM States (3-bit encoding, but declare as 6-bit for observer)
    constant STATE_IDLE   : std_logic_vector(5 downto 0) := "000000";
    constant STATE_ARMED  : std_logic_vector(5 downto 0) := "000001";
    constant STATE_FIRING : std_logic_vector(5 downto 0) := "000010";
    constant STATE_FAULT  : std_logic_vector(5 downto 0) := "000111";

    signal state_reg : std_logic_vector(5 downto 0);
    -- ... rest of your FSM
```

**Alternate Approach:** Pad smaller state vectors:
```vhdl
-- If your FSM uses 3-bit encoding internally
signal state_reg : std_logic_vector(2 downto 0);
signal state_6bit : std_logic_vector(5 downto 0);

-- Pad to 6 bits for observer
state_6bit <= "000" & state_reg;
```

### Step 2: Add Observer Port to Your Top-Level Entity

```vhdl
entity my_application is
    port (
        -- ... your existing ports

        -- Debug Output (FSM Observer)
        voltage_debug_out : out signed(15 downto 0)  -- Oscilloscope debug
    );
end entity;
```

### Step 3: Add Library Dependencies

```vhdl
library WORK;
use WORK.volo_voltage_pkg.all;  -- Required for voltage conversions
```

### Step 4: Instantiate the Observer

```vhdl
architecture rtl of my_application is
    -- ... your signals
    signal fsm_state_vector : std_logic_vector(5 downto 0);
begin
    -- ... your FSM instantiation

    ----------------------------------------------------------------------------
    -- FSM Observer for Debug Visualization
    ----------------------------------------------------------------------------
    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,              -- Total states (normal + fault)
            V_MIN => 0.0,                 -- First state voltage
            V_MAX => 2.5,                 -- Last normal state voltage
            FAULT_STATE_THRESHOLD => 7,   -- States >= 7 are faults
            STATE_0_NAME => "IDLE",
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
            reset        => Reset,        -- Active-high reset
            state_vector => fsm_state_vector,
            voltage_out  => voltage_debug_out
        );
end architecture;
```

---

## Configuration Examples

### Example 1: Simple 4-State FSM (No Faults)

```vhdl
U_SIMPLE_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 4,
        V_MIN => 0.0,
        V_MAX => 1.5,
        FAULT_STATE_THRESHOLD => 4,  -- Disable fault mode (>= NUM_STATES)
        STATE_0_NAME => "IDLE",
        STATE_1_NAME => "ACTIVE",
        STATE_2_NAME => "DONE",
        STATE_3_NAME => "RESET"
    )
    port map ( /* ... */ );
```

**Result:** Purely combinational, no clock required
- IDLE(0.0V), ACTIVE(0.5V), DONE(1.0V), RESET(1.5V)

### Example 2: Complex FSM with Fault Detection

```vhdl
U_COMPLEX_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 10,
        V_MIN => 0.0,
        V_MAX => 2.5,
        FAULT_STATE_THRESHOLD => 8,  -- States 8-9 are faults
        STATE_0_NAME => "INIT",
        STATE_1_NAME => "CALIBRATE",
        STATE_2_NAME => "READY",
        STATE_3_NAME => "ACQUIRE",
        STATE_4_NAME => "PROCESS",
        STATE_5_NAME => "TRANSMIT",
        STATE_6_NAME => "VERIFY",
        STATE_7_NAME => "COMPLETE",
        STATE_8_NAME => "TIMEOUT_FAULT",
        STATE_9_NAME => "ERROR_FAULT"
    )
    port map ( /* ... */ );
```

**Result:** Normal states use 0.0V-2.5V, faults flip sign
- READY(0.71V) → TIMEOUT_FAULT → output = -0.71V

### Example 3: BRAM Loader (3 States + 1 Reserved)

```vhdl
-- 2-bit FSM: IDLE="00", LOADING="01", DONE="10", RESERVED="11"
signal state_6bit : std_logic_vector(5 downto 0);

state_6bit <= "0000" & state;  -- Pad 2-bit to 6-bit

U_BRAM_OBSERVER: entity work.fsm_observer
    generic map (
        NUM_STATES => 4,
        V_MIN => 0.0,
        V_MAX => 2.0,
        FAULT_STATE_THRESHOLD => 3,  -- RESERVED="11" treated as fault
        STATE_0_NAME => "IDLE",
        STATE_1_NAME => "LOADING",
        STATE_2_NAME => "DONE",
        STATE_3_NAME => "RESERVED"
    )
    port map (
        clk          => Clk,
        reset        => Reset,
        state_vector => state_6bit,
        voltage_out  => voltage_debug_out
    );
```

---

## Oscilloscope Setup Guide

### Moku Connection

1. **Connect Debug Output** to Moku Input Channel
   - Example: `voltage_debug_out` → Input 2

2. **Configure Oscilloscope Settings**
   - Vertical scale: 1V/div
   - Vertical offset: Adjust to center waveform
   - Time scale: Based on FSM transition rate
   - Trigger: Edge trigger on state transitions

3. **Set Up Trigger Table** (Optional)
   ```
   Voltage Range    | State Name   | Trigger Action
   ------------------|--------------|----------------
   -0.1V to +0.1V   | IDLE         | None
   +0.4V to +0.6V   | ARMED        | Save waveform
   +0.9V to +1.1V   | FIRING       | Trigger scope
   -2.6V to -2.4V   | HARDFAULT    | Alert + save
   ```

### Interpreting Voltages

**Positive Voltages:** Normal state progression
- Monotonically increasing = forward progress
- Backward steps = state regression (may indicate issue)
- Rapid oscillation = FSM instability

**Negative Voltages:** Fault indication
- Magnitude tells you the previous normal state
- Example: -1.5V fault → FSM was in COOLING(1.5V) before fault

**Zero Voltage:** Typically IDLE or RESET state

---

## Testing Pattern

The FSM observer has been validated with **20 comprehensive tests** covering:

### Core Functionality (Tests 1-8)
1. Reset behavior → all states reset to V_MIN
2. State progression → correct voltage stepping
3. Voltage interpolation → linear spreading across range
4. Fault mode activation → sign-flip on fault entry
5. Fault magnitude preservation → correct previous voltage
6. Fault state hold → voltage stays negative while in fault
7. Recovery from fault → return to positive voltages
8. Sequential fault transitions → correct tracking

### Edge Cases (Tests 9-19)
9. Zero voltage faults (V_MIN = 0.0V)
10. Maximum voltage faults (V_MAX = 5.0V)
11. Single-state FSM (NUM_STATES = 1)
12. Maximum states (NUM_STATES = 64)
13. Inverted voltage range (V_MIN > V_MAX)
14. Rapid state transitions
15. Fault on first clock cycle
16. Fault-to-fault transitions
17. Invalid state indices (failsafe to 0.0V)
18. Extreme configurations (documented edge behavior)
19. Sticky fault behavior

**Test Reference:** See [test_fsm_example.py](../examples/test_fsm_example.py) for complete test suite.

---

## Design Patterns & Best Practices

### Pattern 1: Dedicated Debug Channel

**Recommended:** Reserve one Moku DAC output exclusively for FSM observer

```vhdl
-- OutputA: Functional output
OutputA <= trigger_out;

-- OutputB: Debug output (FSM observer)
OutputB <= debug_voltage;
```

**Why:** Preserves functional outputs while enabling debug visibility.

### Pattern 2: Voltage Range Allocation

**Multiple FSMs:** Use non-overlapping voltage ranges on same channel

```vhdl
-- FSM 1: 0.0V to 1.5V
U_OBS1: entity work.fsm_observer
    generic map (V_MIN => 0.0, V_MAX => 1.5, /* ... */);

-- FSM 2: 2.0V to 3.5V
U_OBS2: entity work.fsm_observer
    generic map (V_MIN => 2.0, V_MAX => 3.5, /* ... */);

-- Combine outputs
voltage_debug_out <= obs1_voltage when fsm1_active else obs2_voltage;
```

### Pattern 3: Conditional Compilation

**Production Removal:** Use generate statements to remove observer in production

```vhdl
GEN_DEBUG: if DEBUG_BUILD generate
    U_OBSERVER: entity work.fsm_observer
        generic map ( /* ... */ )
        port map ( /* ... */ );
end generate;

GEN_PRODUCTION: if not DEBUG_BUILD generate
    voltage_debug_out <= (others => '0');
end generate;
```

### Pattern 4: State Name Documentation

**Always Document:** Use STATE_*_NAME generics for self-documenting code

```vhdl
-- Good: State names match FSM design
STATE_0_NAME => "IDLE",
STATE_1_NAME => "ARMED",
STATE_2_NAME => "FIRING"

-- Bad: Generic names lose context
STATE_0_NAME => "STATE_0",
STATE_1_NAME => "STATE_1"
```

**Why:** State names are used by Python generators for trigger tables and decoders.

---

## Common Pitfalls & Solutions

### Pitfall 1: Active-Low Reset Confusion

**Problem:** Observer uses active-HIGH reset, but FSM uses active-LOW

**Solution:** Invert reset signal at observer
```vhdl
U_OBSERVER: entity work.fsm_observer
    port map (
        reset => not rst_n,  -- Invert active-low to active-high
        /* ... */
    );
```

### Pitfall 2: State Vector Width Mismatch

**Problem:** FSM uses 3-bit state, observer expects 6-bit

**Solution:** Pad with zeros (MSBs or LSBs)
```vhdl
signal state_3bit : std_logic_vector(2 downto 0);
signal state_6bit : std_logic_vector(5 downto 0);

state_6bit <= "000" & state_3bit;  -- Pad MSBs
```

### Pitfall 3: Fault Threshold Misconfiguration

**Problem:** Normal states incorrectly treated as faults

**Solution:** Set `FAULT_STATE_THRESHOLD` correctly
```vhdl
-- For 8 states with last state as fault:
NUM_STATES => 8,
FAULT_STATE_THRESHOLD => 7  -- Only state 7 is fault

-- For 8 states with NO faults:
NUM_STATES => 8,
FAULT_STATE_THRESHOLD => 8  -- Disable fault mode (>= NUM_STATES)
```

### Pitfall 4: Missing Voltage Package

**Problem:** Compilation error: "voltage_to_digital not found"

**Solution:** Add library dependency
```vhdl
library WORK;
use WORK.volo_voltage_pkg.all;  -- Required!
```

---

## Performance Characteristics

### Resource Usage (Typical FPGA)

| Resource | No Faults Mode | With Faults Mode |
|----------|----------------|------------------|
| LUTs | ~50 | ~80 |
| Registers | 0 (combinational) | ~20 |
| Block RAM | 0 | 0 |
| Timing Impact | None | <1 ns setup |

### Timing Analysis

- **Combinational Path:** state_vector → voltage_out (single LUT lookup)
- **Critical Path:** None (purely output path, not in FSM feedback)
- **Clock Dependency:** Only required if `FAULT_STATE_THRESHOLD < NUM_STATES`

---

## Troubleshooting Guide

### Issue: Voltage output is always 0.0V

**Causes:**
1. FSM state is stuck in state 0
2. Observer reset signal is stuck high
3. Voltage range is too small (V_MIN ≈ V_MAX)

**Debug Steps:**
1. Verify FSM state transitions independently
2. Check reset signal polarity (active-high vs active-low)
3. Increase voltage range (e.g., V_MIN=0.0, V_MAX=2.5)

### Issue: Unexpected negative voltages

**Causes:**
1. FSM entering fault state unintentionally
2. State vector exceeding `FAULT_STATE_THRESHOLD`
3. Incorrect state padding (MSBs not zero)

**Debug Steps:**
1. Review FSM state encoding (states 0-6 normal, 7+ faults)
2. Verify `FAULT_STATE_THRESHOLD` configuration
3. Check state vector padding logic

### Issue: Voltage jumps/glitches

**Causes:**
1. Combinational glitches on state_vector
2. Clock domain crossing issues
3. Race conditions in FSM next-state logic

**Debug Steps:**
1. Register the state_vector before observer (add pipeline stage)
2. Ensure single clock domain for FSM and observer
3. Review FSM next-state logic for hazards

---

## References

- **Entity Definition:** [fsm_observer.vhd](../VHDL/fsm_observer.vhd)
- **Test Suite:** [test_fsm_example.py](../examples/test_fsm_example.py)
- **Example Integration:** [DS1120_PD_volo_main.vhd](../VHDL/DS1120_PD_volo_main.vhd) (lines 233-253)
- **BRAM Loader Integration:** [volo_bram_loader.vhd](../VHDL/volo_bram_loader.vhd) (lines 208-232)
- **Voltage Utilities:** [volo_voltage_pkg.vhd](../VHDL/volo_voltage_pkg.vhd)

---

## Changelog

**Version 1.0** (2025-01-28)
- Initial design pattern documentation
- Comprehensive integration guide
- 20-test validation suite
- Production deployments: DS1120-PD, BRAM Loader

---

## License

This pattern is part of the EZ-EMFI project and follows the same license terms.

---

**Questions or Issues?** File an issue or consult the [VHDL examples](../VHDL/) for reference implementations.
