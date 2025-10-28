# DS1140-PD Register Type Implementation Plan

**Date**: 2025-10-28
**Purpose**: Implementation plan for `counter_16bit` register type to support DS1140-PD
**Status**: COMMITTED - Will be implemented before DS1140-PD Phase 2

---

## Executive Summary

We are **committing to implementing** the `counter_16bit` register type **before** starting DS1140-PD Phase 2. This eliminates the awkward 8-bit high/low register splits currently required for 16-bit values.

**Impact on DS1140-PD**:
- **Register count**: 9 → **7 registers** (22% reduction)
- **User experience**: Single registers for 16-bit values (no manual splitting)
- **Implementation**: Simpler signal reconstruction in VHDL

---

## Current Register Type System

**Location**: `models/volo/app_register.py`

**Supported Types** (intentionally limited to 3):

| Type | VHDL Type | Bit Width | Value Range | Use Case |
|------|-----------|-----------|-------------|----------|
| `counter_8bit` | `std_logic_vector(7:0)` | 8 bits | 0-255 | General counters, byte values |
| `percent` | `std_logic_vector(6:0)` | 7 bits | 0-100 | Duty cycles, percentages |
| `button` | `std_logic` | 1 bit | 0 or 1 | Boolean controls, one-shot triggers |

**Design Philosophy** (from `app_register.py:12`):
> "Start simple, extend later. These 3 types cover 80% of use cases."

---

## Problem: Split 16-Bit Registers in DS1140-PD

### Current Approach (DS1120-PD Pattern)

```yaml
# Two separate 8-bit registers for 16-bit voltage threshold
- name: Trigger Threshold High
  reg_type: counter_8bit
  cr_number: 27
  default_value: 0x3D  # High byte of 0x3DCF (2.4V)

- name: Trigger Threshold Low
  reg_type: counter_8bit
  cr_number: 28
  default_value: 0xCF  # Low byte of 0x3DCF (2.4V)

# Two separate 8-bit registers for 16-bit intensity
- name: Intensity High
  reg_type: counter_8bit
  cr_number: 29
  default_value: 0x26  # High byte of 0x2666 (2.0V)

- name: Intensity Low
  reg_type: counter_8bit
  cr_number: 30
  default_value: 0x66  # Low byte of 0x2666 (2.0V)
```

### VHDL Signal Reconstruction (Awkward)

```vhdl
-- In DS1120_PD_volo_main.vhd
signal trigger_threshold_high : std_logic_vector(7 downto 0);
signal trigger_threshold_low  : std_logic_vector(7 downto 0);
signal trigger_threshold_16bit: signed(15 downto 0);

-- Manual reconstruction
trigger_threshold_16bit <= signed(trigger_threshold_high & trigger_threshold_low);
```

### User Experience Issues
- ❌ User must convert 2.4V → 0x3DCF hex
- ❌ Must split into high/low bytes manually
- ❌ Easy to make mistakes (endianness, calculation errors)
- ❌ Not intuitive for voltage configuration
- ❌ Clutters register layout with high/low pairs

---

## Solution: `counter_16bit` Register Type

### Implementation in `app_register.py`

```python
# Add new enum value
class RegisterType(str, Enum):
    COUNTER_8BIT = "counter_8bit"
    COUNTER_16BIT = "counter_16bit"  # NEW
    PERCENT = "percent"
    BUTTON = "button"

# Update bit width method
def get_type_bit_width(self) -> int:
    if self.reg_type == RegisterType.COUNTER_8BIT:
        return 8
    elif self.reg_type == RegisterType.COUNTER_16BIT:
        return 16  # NEW
    elif self.reg_type == RegisterType.PERCENT:
        return 7
    elif self.reg_type == RegisterType.BUTTON:
        return 1

# Update max value method
def get_type_max_value(self) -> int:
    if self.reg_type == RegisterType.COUNTER_8BIT:
        return 255
    elif self.reg_type == RegisterType.COUNTER_16BIT:
        return 65535  # NEW
    elif self.reg_type == RegisterType.PERCENT:
        return 100
    elif self.reg_type == RegisterType.BUTTON:
        return 1

# Validation (existing validators work, just check range)
@field_validator('default_value')
@classmethod
def validate_default_value(cls, v, info):
    # ... existing validation logic ...
    max_val = get_type_max_value(reg_type)
    if v > max_val:
        raise ValueError(f"{reg_type} default_value {v} exceeds max {max_val}")
    return v
```

### Shim Generation Updates

**Current shim generation** (uses upper bits of 32-bit Control Register):
```vhdl
-- For counter_8bit (uses upper 8 bits of CR)
arm_timeout <= unsigned(app_reg_24(31 downto 24));
```

**New shim generation** (for counter_16bit):
```vhdl
-- For counter_16bit (uses upper 16 bits of CR)
trigger_threshold <= signed(app_reg_27(31 downto 16));
intensity <= signed(app_reg_28(31 downto 16));
```

**Note**: MCC Control Registers are 32-bit. We pack values in upper bits:
- 8-bit values: `app_reg_N(31 downto 24)` (upper 8 bits)
- 16-bit values: `app_reg_N(31 downto 16)` (upper 16 bits)
- 1-bit values: `app_reg_N(31)` (MSB only)

---

## DS1140-PD Register Layout with `counter_16bit`

### New Simplified Layout (7 Registers Total)

```yaml
name: DS1140_PD
version: 1.0.0
description: EMFI probe driver for Riscure DS1120A (refactored architecture)

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
    default_value: 0x3DCF  # 2.4V (will document in comments)

  - name: Intensity
    description: Output intensity (16-bit signed, clamped to 3.0V)
    reg_type: counter_16bit  # NEW - Single register for 0x2666!
    cr_number: 28
    default_value: 0x2666  # 2.0V (will document in comments)
```

**Note**: We still use hex values (`0x3DCF`) for voltage registers until `voltage_signed` type is implemented (future enhancement).

### Comparison: Before vs After

| Register | Before (split) | After (counter_16bit) |
|----------|----------------|-----------------------|
| Arm Timeout | CR23 (upper 4 bits) + CR24 (8 bits) = 12-bit | CR24 (16-bit) |
| Trigger Threshold | CR27 (high) + CR28 (low) = 16-bit | CR27 (16-bit) |
| Intensity | CR29 (high) + CR30 (low) = 16-bit | CR28 (16-bit) |

**Register Count**:
- Before: 9 registers (CR20-CR28, with splits)
- After: **7 registers** (CR20-CR28, no splits)

---

## VHDL Implementation Changes

### Generated Shim Layer (DS1140_PD_volo_shim.vhd)

```vhdl
-- BEFORE (split registers)
signal trigger_threshold_high : std_logic_vector(7 downto 0);
signal trigger_threshold_low  : std_logic_vector(7 downto 0);
trigger_threshold_high <= app_reg_27(31 downto 24);
trigger_threshold_low  <= app_reg_28(31 downto 24);

-- AFTER (single 16-bit register)
signal trigger_threshold : signed(15 downto 0);  -- Direct 16-bit!
trigger_threshold <= signed(app_reg_27(31 downto 16));
```

### Application Layer (DS1140_PD_volo_main.vhd)

```vhdl
entity DS1140_PD_volo_main is
    port (
        -- Standard Control Signals
        Clk     : in  std_logic;
        Reset   : in  std_logic;
        Enable  : in  std_logic;
        ClkEn   : in  std_logic;

        -- Application Signals (from shim layer)
        arm_probe            : in  std_logic;
        force_fire           : in  std_logic;
        reset_fsm            : in  std_logic;
        clock_divider        : in  std_logic_vector(7 downto 0);
        arm_timeout          : in  unsigned(15 downto 0);  -- NEW: Direct 16-bit!
        firing_duration      : in  std_logic_vector(7 downto 0);
        cooling_duration     : in  std_logic_vector(7 downto 0);
        trigger_threshold    : in  signed(15 downto 0);    -- NEW: Direct 16-bit!
        intensity            : in  signed(15 downto 0);    -- NEW: Direct 16-bit!

        -- MCC I/O (Three outputs)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0)
    );
end entity DS1140_PD_volo_main;

architecture rtl of DS1140_PD_volo_main is
    -- No more manual reconstruction needed!
    signal arm_timeout_12bit : unsigned(11 downto 0);
begin
    -- Simple truncation to FSM's 12-bit interface
    arm_timeout_12bit <= arm_timeout(11 downto 0);

    -- Direct use of threshold and intensity
    U_TRIGGER: entity work.volo_voltage_threshold_trigger_core
        port map (
            threshold_high => trigger_threshold,  -- Direct!
            threshold_low  => trigger_threshold - x"0100",
            -- ...
        );

    -- Direct intensity clamping
    intensity_clamped <= clamp_voltage(intensity, MAX_INTENSITY_3V0);
end architecture rtl;
```

**Benefits**:
- ✅ No manual signal reconstruction
- ✅ Cleaner port list
- ✅ Direct use of 16-bit values
- ✅ Less error-prone

---

## Implementation Checklist

### Phase 0: Preparation (Before DS1140-PD Phase 2)

**Update `models/volo/app_register.py`**:
- [ ] Add `COUNTER_16BIT` to `RegisterType` enum
- [ ] Update `get_type_bit_width()` to return 16 for counter_16bit
- [ ] Update `get_type_max_value()` to return 65535 for counter_16bit
- [ ] Verify existing validators work with 16-bit values
- [ ] Add unit tests for counter_16bit validation

**Update `models/volo/volo_app.py` (Shim Generation)**:
- [ ] Update Jinja2 template to handle 16-bit bit ranges
- [ ] Generate `app_reg_N(31 downto 16)` for counter_16bit
- [ ] Add comments for voltage values (e.g., "0x3DCF = 2.4V")
- [ ] Test shim generation with example YAML

**Update `tools/generate_volo_app.py`**:
- [ ] Test YAML parsing with counter_16bit type
- [ ] Verify VHDL generation correctness
- [ ] Run on test YAML with 16-bit registers

**Testing**:
- [ ] Unit tests for Pydantic validation (counter_16bit type)
- [ ] YAML round-trip tests (load → save → load)
- [ ] VHDL generation tests (verify `app_reg_N(31 downto 16)`)
- [ ] Integration test with simple test module

**Documentation**:
- [ ] Update `EXTERNAL_volo_vhdl/docs/VOLO_APP_DESIGN.md`
- [ ] Add counter_16bit examples to YAML templates
- [ ] Document bit packing strategy (upper 16 bits of 32-bit CR)

### Phase 1: DS1140-PD Integration

**Create DS1140_PD_app.yaml**:
- [ ] Use counter_16bit for arm_timeout (CR24)
- [ ] Use counter_16bit for trigger_threshold (CR27)
- [ ] Use counter_16bit for intensity (CR28)
- [ ] Keep firing_duration and cooling_duration as counter_8bit

**Generate Shim**:
- [ ] Run `generate_volo_app.py` on DS1140_PD_app.yaml
- [ ] Verify generated shim has correct bit ranges
- [ ] Verify signal types (signed vs unsigned)

**Implement DS1140_PD_volo_main.vhd**:
- [ ] Update entity ports to use direct 16-bit signals
- [ ] Remove manual signal reconstruction
- [ ] Simplify threshold and intensity usage
- [ ] Test compilation with GHDL

**CocotB Testing**:
- [ ] Update test setup to use 16-bit registers
- [ ] Test arm_timeout values (0-4095 range)
- [ ] Test trigger_threshold (0x3DCF = 2.4V)
- [ ] Test intensity (0x2666 = 2.0V)
- [ ] Verify all P1 and P2 tests pass

---

## Future Enhancement: `voltage_signed` Type

**After `counter_16bit` is proven stable**, we can add the `voltage_signed` type for even better UX:

```yaml
# Future enhancement (not in initial implementation)
- name: Trigger Threshold
  reg_type: voltage_signed  # FUTURE TYPE
  cr_number: 27
  default_value: 2.4  # Direct voltage in volts!
  description: Voltage threshold for trigger detection (±5V range)
```

**Benefits**:
- User writes `2.4` instead of `0x3DCF`
- Automatic conversion from volts to 16-bit signed
- Self-documenting (voltage value visible in YAML)

**Implementation**: See original DS1140_PD_REGISTER_TYPES.md (archived) for details.

**Priority**: Lower priority. `counter_16bit` solves the register split problem. `voltage_signed` is a UX enhancement.

---

## Success Criteria

**Phase 0 Complete** (before DS1140-PD Phase 2):
- ✅ `counter_16bit` type implemented in `app_register.py`
- ✅ Shim generation handles 16-bit registers correctly
- ✅ Unit tests pass
- ✅ Test YAML generates valid VHDL

**Phase 1 Complete** (DS1140-PD integration):
- ✅ DS1140_PD_app.yaml uses counter_16bit for 3 registers
- ✅ DS1140_PD_volo_shim.vhd generated correctly
- ✅ DS1140_PD_volo_main.vhd uses direct 16-bit signals
- ✅ All CocotB tests pass (P1 and P2)
- ✅ Register count reduced from 9 to 7

---

## Timeline

**Phase 0** (counter_16bit implementation):
- Estimated time: 2-3 hours
- Blocking: Must complete before DS1140-PD Phase 2

**Phase 1** (DS1140-PD integration):
- Estimated time: 1 hour (part of normal Phase 2 workflow)
- Benefits: Cleaner implementation, fewer registers

**Total Impact**: 3-4 hours upfront work, saves complexity in DS1140-PD implementation.

---

## References

**Current Implementation**:
- `/Users/vmars20/EZ-EMFI/models/volo/app_register.py` - Register type system
- `/Users/vmars20/EZ-EMFI/models/volo/volo_app.py` - VHDL generation
- `/Users/vmars20/EZ-EMFI/tools/generate_volo_app.py` - Generator script

**DS1120-PD Reference** (current pattern):
- `/Users/vmars20/EZ-EMFI/DS1120_PD_app.yaml` - Split register example
- `/Users/vmars20/EZ-EMFI/VHDL/DS1120_PD_volo_main.vhd` - Manual reconstruction

**Voltage Scale Reference**:
- MCC ADC/DAC: 16-bit signed, ±5V full scale
- Resolution: ~305µV per bit (10V / 65536)
- Formula: `voltage = (value / 32767) * 5.0`
- Inverse: `value = (voltage / 5.0) * 32767`
- Example: 2.4V = `(2.4 / 5.0) * 32767` = `15759` = `0x3D8F` ≈ `0x3DCF` (approx)

---

**Status**: COMMITTED - Implementation will proceed before DS1140-PD Phase 2 begins.
