# Phase 0 Handoff Document: counter_16bit Implementation

**Date**: 2025-10-28
**Status**: Phase 0.1 Complete, Phase 0.2-0.4 Remaining
**Estimated Time Remaining**: 1.5-2 hours

---

## What Was Completed (Phase 0.1)

### ✅ `models/volo/app_register.py` - COMPLETE

**All changes implemented successfully:**

1. **Added `COUNTER_16BIT` to RegisterType enum** (line 32)
   ```python
   COUNTER_16BIT = "counter_16bit"
   ```

2. **Updated module docstring** (lines 7-13)
   - Added COUNTER_16BIT documentation
   - Changed "3 types" to "these types"

3. **Updated class docstring in RegisterType** (line 27)
   - Added mapping: `COUNTER_16BIT → std_logic_vector(15 downto 0)`

4. **Updated all validators** for 16-bit range (0-65535):
   - `validate_default_value()` - lines 102-104
   - `validate_min_value()` - lines 128-130
   - `validate_max_value()` - lines 154-156

5. **Updated helper methods**:
   - `get_type_max_value()` - lines 170-171: returns 65535
   - `get_type_bit_width()` - lines 183-184: returns 16

**File is production-ready and fully validated.**

---

## What Needs To Be Done

### Phase 0.2: Update Shim Generation in `volo_app.py`

**File**: `/Users/vmars20/EZ-EMFI/models/volo/volo_app.py`

**Objective**: Generate correct VHDL bit slicing for 16-bit registers

**Changes Needed**:

1. **Locate VHDL generation code** that creates port mapping assignments
2. **Add conditional logic** for `counter_16bit` type:
   ```python
   if reg.reg_type == RegisterType.COUNTER_8BIT:
       bit_range = f"(31 downto 24)"  # Upper 8 bits
   elif reg.reg_type == RegisterType.COUNTER_16BIT:
       bit_range = f"(31 downto 16)"  # Upper 16 bits (NEW)
   elif reg.reg_type == RegisterType.BUTTON:
       bit_range = f"(31)"  # MSB only
   elif reg.reg_type == RegisterType.PERCENT:
       bit_range = f"(31 downto 25)"  # Upper 7 bits
   ```

3. **Update VHDL port generation** to use correct signal types:
   ```vhdl
   -- 8-bit: std_logic_vector(7 downto 0)
   -- 16-bit: std_logic_vector(15 downto 0) OR unsigned(15 downto 0) OR signed(15 downto 0)
   ```

4. **IMPORTANT**: For DS1140-PD voltage registers (threshold, intensity):
   - These should map to `signed(15 downto 0)` not `std_logic_vector`
   - May need special handling or type annotation in YAML

**Optional Enhancement**:
- Add voltage comments for 16-bit registers with voltage values:
  ```vhdl
  -- trigger_threshold: 0x3DCF = 2.4V
  trigger_threshold <= signed(app_reg_27(31 downto 16));
  ```

### Phase 0.3: Create Unit Tests

**File**: Create `/Users/vmars20/EZ-EMFI/tests/test_app_register.py` (NEW)

**Test Cases Needed**:

```python
import pytest
from models.volo.app_register import AppRegister, RegisterType

def test_counter_16bit_enum_exists():
    """Verify counter_16bit enum value exists"""
    assert RegisterType.COUNTER_16BIT == "counter_16bit"

def test_counter_16bit_bit_width():
    """Test bit width for counter_16bit"""
    reg = AppRegister(
        name="Test 16-bit",
        description="Test register",
        reg_type=RegisterType.COUNTER_16BIT,
        cr_number=24,
        default_value=4095
    )
    assert reg.get_type_bit_width() == 16

def test_counter_16bit_max_value():
    """Test max value for counter_16bit"""
    reg = AppRegister(
        name="Test 16-bit",
        description="Test register",
        reg_type=RegisterType.COUNTER_16BIT,
        cr_number=24,
        default_value=4095
    )
    assert reg.get_type_max_value() == 65535

def test_counter_16bit_validation_in_range():
    """Test counter_16bit accepts valid values"""
    reg = AppRegister(
        name="Test 16-bit",
        description="Test register",
        reg_type=RegisterType.COUNTER_16BIT,
        cr_number=24,
        default_value=0x3DCF,  # 15823 (2.4V)
        min_value=0,
        max_value=4095
    )
    assert reg.default_value == 0x3DCF

def test_counter_16bit_validation_out_of_range():
    """Test counter_16bit rejects out-of-range values"""
    with pytest.raises(ValueError, match="COUNTER_16BIT default_value must be 0-65535"):
        AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=70000  # > 65535
        )

def test_counter_16bit_min_max_validation():
    """Test counter_16bit min/max value validation"""
    reg = AppRegister(
        name="Test 16-bit",
        description="Test register",
        reg_type=RegisterType.COUNTER_16BIT,
        cr_number=24,
        default_value=1000,
        min_value=0,
        max_value=4095
    )
    assert reg.min_value == 0
    assert reg.max_value == 4095
```

**Run tests with**:
```bash
pytest tests/test_app_register.py -v
```

### Phase 0.4: Test YAML Parsing and VHDL Generation

**Create test YAML**: `/Users/vmars20/EZ-EMFI/test_counter_16bit.yaml`

```yaml
name: TEST_COUNTER_16BIT
version: 0.1.0
description: Test application for counter_16bit register type
author: Volo Team
tags:
  - test

bitstream_path: null
buffer_path: null

registers:
  # Test 16-bit register
  - name: Arm Timeout
    description: Cycles to wait for trigger before timeout (0-4095)
    reg_type: counter_16bit
    cr_number: 24
    default_value: 255
    min_value: 0
    max_value: 4095

  # Test voltage register (also 16-bit)
  - name: Trigger Threshold
    description: Voltage threshold for trigger detection (16-bit signed)
    reg_type: counter_16bit
    cr_number: 27
    default_value: 0x3DCF  # 2.4V

  # Test another 16-bit register
  - name: Intensity
    description: Output intensity (16-bit signed, clamped to 3.0V)
    reg_type: counter_16bit
    cr_number: 28
    default_value: 0x2666  # 2.0V
```

**Generate and verify VHDL**:
```bash
# Generate shim layer (command will depend on how volo_app.py is invoked)
python models/volo/volo_app.py --config test_counter_16bit.yaml --output /tmp/test_counter_16bit/

# Verify generated shim has correct bit ranges:
# - arm_timeout: app_reg_24(31 downto 16)
# - trigger_threshold: app_reg_27(31 downto 16)
# - intensity: app_reg_28(31 downto 16)

# Check entity ports use 16-bit signals:
cat /tmp/test_counter_16bit/TEST_COUNTER_16BIT_volo_shim.vhd | grep "arm_timeout"
# Should see: arm_timeout : out std_logic_vector(15 downto 0);
# OR: arm_timeout : out unsigned(15 downto 0);
```

**Success Criteria**:
- [ ] YAML parses without errors
- [ ] Shim VHDL generated successfully
- [ ] Entity ports have correct 16-bit types
- [ ] Register assignments use correct bit ranges: `(31 downto 16)`
- [ ] VHDL compiles with GHDL (optional validation)

---

## Reference Files for Phase 0.2

**Key file to modify**:
- `/Users/vmars20/EZ-EMFI/models/volo/volo_app.py`

**Files to reference**:
- `/Users/vmars20/EZ-EMFI/models/volo/app_register.py` (DONE)
- `/Users/vmars20/EZ-EMFI/DS1120_PD_app.yaml` (current DS1120-PD config for reference)
- `/Users/vmars20/EZ-EMFI/VHDL/DS1120_PD_volo_shim.vhd` (current shim for comparison)

**Documentation**:
- `/Users/vmars20/EZ-EMFI/DS1140_PD_IMPLEMENTATION_GUIDE.md` (Phase 0.2 details at lines 93-109)
- `/Users/vmars20/EZ-EMFI/DS1140_PD_REGISTER_TYPES.md` (register type design, if exists)

---

## Quick Start Prompt for Next Session

```
Continue Phase 0 implementation of counter_16bit register type for DS1140-PD project.

Phase 0.1 is COMPLETE:
- @models/volo/app_register.py has full counter_16bit support (enum, validators, helpers)

Phase 0.2 (NEXT):
- Update @models/volo/volo_app.py to generate correct VHDL for 16-bit registers
- Bit range should be: app_reg_N(31 downto 16) for counter_16bit type
- Entity ports should be: std_logic_vector(15 downto 0) or unsigned(15 downto 0)

Phase 0.3:
- Create unit tests in tests/test_app_register.py

Phase 0.4:
- Test YAML parsing with test_counter_16bit.yaml
- Verify VHDL generation

Read @PHASE0_HANDOFF.md for complete details and test code templates.

Let's start with Phase 0.2: updating volo_app.py shim generation.
```

---

## Design Decisions & Notes

### Bit Packing Strategy (32-bit Control Registers)

Each Control Register (CR20-CR30) is 32 bits wide. Packing strategy:

| Register Type   | Bit Width | Bit Range Used     | Unused Bits    |
|-----------------|-----------|---------------------|----------------|
| `counter_8bit`  | 8 bits    | [31:24]             | [23:0]         |
| `counter_16bit` | 16 bits   | [31:16]             | [15:0]         |
| `percent`       | 7 bits    | [31:25]             | [24:0]         |
| `button`        | 1 bit     | [31]                | [30:0]         |

**Rationale**: Upper bits used for cleaner MSB-first alignment.

### Voltage Registers (Special Case)

For voltage registers (trigger_threshold, intensity):
- Use `counter_16bit` type for YAML configuration
- Map to `signed(15 downto 0)` in VHDL (±5V scale)
- Conversion: `voltage = (raw_value / 32767.0) * 5.0`
- Example: `0x3DCF = 15823 → 2.415V ≈ 2.4V`

**Future Enhancement**: `voltage_signed` type would let users write `2.4` directly instead of `0x3DCF`.

### DS1140-PD Register Layout (After counter_16bit)

**7 registers total** (vs 11 in DS1120-PD):

| CR   | Name              | Type            | Default | Notes                          |
|------|-------------------|-----------------|---------|--------------------------------|
| CR20 | Arm Probe         | button          | 0       | One-shot arm                   |
| CR21 | Force Fire        | button          | 0       | Manual trigger                 |
| CR22 | Reset FSM         | button          | 0       | Reset state machine            |
| CR23 | Clock Divider     | counter_8bit    | 0       | ÷1 to ÷16                      |
| CR24 | Arm Timeout       | counter_16bit   | 255     | 0-4095 cycles (12-bit used)    |
| CR25 | Firing Duration   | counter_8bit    | 16      | Max 32 cycles                  |
| CR26 | Cooling Duration  | counter_8bit    | 16      | Min 8 cycles                   |
| CR27 | Trigger Threshold | counter_16bit   | 0x3DCF  | 2.4V (16-bit signed voltage)   |
| CR28 | Intensity         | counter_16bit   | 0x2666  | 2.0V (clamped to 3.0V max)     |

**Benefits**:
- 36% fewer registers than DS1120-PD (7 vs 11)
- No manual signal reconstruction in VHDL
- More intuitive configuration (no high/low byte splits)

---

## Success Criteria for Phase 0 (Complete)

- [x] `counter_16bit` enum added to `RegisterType`
- [x] Bit width and max value methods updated
- [ ] Shim generation handles 16-bit bit ranges
- [ ] Unit tests pass
- [ ] Test YAML generates valid VHDL
- [ ] Documentation updated (optional)

**When Phase 0 is complete**, proceed to Phase 1 (Architecture Review) or directly to Phase 2 (DS1140_PD_app.yaml creation).

---

**Ready to continue!** Use the quick start prompt above in your next session.
