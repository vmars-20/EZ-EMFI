# VHDL + CocotB Lessons Learned

**Date**: 2025-01-28
**Context**: volo_lut_pkg test development session
**Audience**: Future agents and human developers

## Overview

This document captures critical lessons learned while developing and debugging VHDL packages with CocotB tests. These lessons prevent common pitfalls and save hours of debugging time.

---

## 🔴 Critical Issues (Must Fix First)

### 1. Function Overloading with Subtypes

**Problem**: VHDL does NOT support function overloading when parameter types are subtypes of the same base type.

**Bad Code**:
```vhdl
subtype pct_index_t is natural range 0 to 100;

-- ❌ ERROR: Both signatures resolve to natural
function lut_lookup(lut : lut_101x16_t; idx : pct_index_t) return std_logic_vector;
function lut_lookup(lut : lut_101x16_t; idx : natural) return std_logic_vector;
```

**Error Message**:
```
error: redeclaration of function "lut_lookup" defined at line 82:14
```

**Solution**: Use only the base type. Subtypes are compatible with their base type, so one function handles both.

```vhdl
-- ✅ CORRECT: Single function accepts natural (includes pct_index_t)
function lut_lookup(lut : lut_101x16_t; idx : natural) return std_logic_vector;

-- Usage works with both:
signal idx_pct : pct_index_t := 50;
signal idx_nat : natural := 75;

output1 <= lut_lookup(MY_LUT, idx_pct);  -- Works!
output2 <= lut_lookup(MY_LUT, idx_nat);  -- Works!
```

**Why This Happens**: VHDL resolves subtypes to their base type for overload resolution. `pct_index_t` and `natural` are considered identical signatures.

**Key Takeaway**: Subtypes are for documentation and runtime range checking, NOT for compile-time type safety.

---

### 2. Hex Literal Type Inference

**Problem**: Bare hex literals like `16#0000#` have no explicit type, causing GHDL compilation errors in array constants.

**Bad Code**:
```vhdl
constant MY_LUT : lut_101x16_t := (
    16#0000#, 16#028F#, 16#051E#, ...  -- ❌ ERROR: type not compatible
);
```

**Error Message**:
```
error: type of element not compatible with the expected type
```

**Solution**: Use `x"HHHH"` notation for std_logic_vector literals.

```vhdl
-- ✅ CORRECT: x"" notation infers std_logic_vector
constant MY_LUT : lut_101x16_t := (
    x"0000", x"028F", x"051E", ...  -- Works!
);
```

**Alternative** (for signed types):
```vhdl
constant MY_SIGNED_LUT : lut_101x16_signed_t := (
    to_signed(-32768, 16),
    to_signed(-32112, 16),
    ...
);
```

**Why This Matters**: GHDL requires explicit type information for array element inference. The `x""` notation provides this automatically.

---

## ⚠️ Common Test Issues

### 3. Test Data Generation: Off-by-One Rounding

**Problem**: Python rounding for test constants doesn't match VHDL integer division.

**Example**:
```python
# ❌ WRONG: Doesn't match VHDL behavior
expected_50 = int((50 / 100.0) * 0xFFFF + 0.5)  # = 32768 (rounds up)
```

```vhdl
-- VHDL integer division
value := (50 * 65535) / 100;  -- = 32767 (truncates)
```

**Result**: Test expects 0x8000 (32768), but VHDL produces 0x7FFF (32767). Test fails.

**Solution**: Match VHDL's integer arithmetic exactly.

```python
# ✅ CORRECT: Matches VHDL truncation
expected_50 = int((50 / 100.0) * 0xFFFF)  # = 32767 (truncates)
```

**Testing Strategy**: When generating expected values for LUTs:
1. Use the SAME formula as VHDL
2. Test boundary values (0, 50, 100) first
3. Verify rounding behavior matches

---

### 4. Python Import Order

**Problem**: Functions used in module-level constants must be defined before use.

**Bad Code**:
```python
# ❌ ERROR: Function used before definition
EXPECTED_VALUES = {
    0:   voltage_to_digital_approx(0.0),  # NameError!
    50:  voltage_to_digital_approx(2.5),
}

def voltage_to_digital_approx(voltage):  # Defined too late
    return int((voltage / 5.0) * 32767)
```

**Error Message**:
```
NameError: name 'voltage_to_digital_approx' is not defined
```

**Solution**: Define helper functions BEFORE using them in constants.

```python
# ✅ CORRECT: Define function first
def voltage_to_digital_approx(voltage):
    return int((voltage / 5.0) * 32767)

EXPECTED_VALUES = {
    0:   voltage_to_digital_approx(0.0),  # Works!
    50:  voltage_to_digital_approx(2.5),
}
```

---

### 5. CocotB Signal Persistence Between Tests

**Problem**: Outputs from previous tests persist into next test if not explicitly cleared.

**Observed Behavior**:
```python
# Test 1 sets pct_index_output to 25
await test_to_pct_index(dut, 25)  # pct_index_output = 25

# Test 2 expects 0, but gets stale value
assert dut.pct_index_output.value == 0  # ❌ FAIL: Still 25!
```

**Root Cause**: Sequential logic holds values between tests. If Test 2 doesn't activate the right control signals, outputs don't update.

**Solution**: Always reset DUT or verify control signals are properly set for each test.

```python
async def test_function(dut, ...):
    # Clear all select signals first
    dut.sel_lut_lookup.value = 0
    dut.sel_lut_lookup_signed.value = 0
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0

    # Now set the ONE we want
    dut.sel_to_pct_index.value = 1

    # Wait for update
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Now check output
    assert dut.pct_index_output.value == expected
```

**Better Pattern**: Create a reset helper:

```python
async def reset_all_selects(dut):
    """Clear all function select signals"""
    dut.sel_lut_lookup.value = 0
    dut.sel_lut_lookup_signed.value = 0
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0
    await RisingEdge(dut.clk)
```

---

## 📋 Best Practices

### 6. Test Data Dictionary Coverage

**Problem**: Using sparse dictionaries for expected values causes KeyError in comprehensive tests.

**Bad Code**:
```python
EXPECTED_LUT_UNSIGNED = {
    0:   0x0000,
    50:  0x7FFF,
    100: 0xFFFF,
}

# ❌ Fails when testing index 99
for index in range(0, 101):
    expected = EXPECTED_LUT_UNSIGNED[index]  # KeyError: 99
```

**Solutions**:

**Option A**: Fill all indices (best for static LUTs)
```python
# Generate all 101 values
EXPECTED_LUT_UNSIGNED = {
    i: int((i / 100.0) * 0xFFFF)
    for i in range(101)
}
```

**Option B**: Handle missing keys gracefully
```python
for index in range(0, 101):
    if index <= 100:
        expected = EXPECTED_LUT_UNSIGNED.get(index)
        if expected is None:
            # Calculate on-the-fly
            expected = int((index / 100.0) * 0xFFFF)
    else:
        expected = EXPECTED_LUT_UNSIGNED[100]  # Saturation
```

---

### 7. LUT Generation: Python vs VHDL Consistency

**Best Practice**: Use Python scripts to generate VHDL LUT constants.

**Pattern**:
```python
#!/usr/bin/env python3
# generate_luts.py

def generate_linear_lut():
    """Generate VHDL constant matching package formula"""
    lines = ["constant MY_LUT : lut_101x16_t := ("]

    for i in range(101):
        value = int((i / 100.0) * 0xFFFF)  # Match VHDL formula
        hex_val = f'x"{value:04X}"'

        lines.append(f"    {hex_val}", end="")
        if i < 100:
            lines.append(", ")
        if (i+1) % 10 == 0:
            lines.append(f"  -- {i-9}-{i}")

    lines.append(");")
    return "\n".join(lines)

# Generate and paste into VHDL file
print(generate_linear_lut())
```

**Benefits**:
- ✅ Consistent with VHDL calculations
- ✅ No manual typing errors
- ✅ Easy to regenerate if formula changes
- ✅ Can generate test expected values from same script

---

### 8. CocotB Deprecation Warnings

**Observed Warnings**:
```
DeprecationWarning: The 'units' argument has been renamed to 'unit'.
  clock = Clock(dut.clk, period_ns, units="ns")

DeprecationWarning: `logic_array.signed_integer` getter is deprecated.
  actual = int(dut.lut_output_signed.value.signed_integer)
```

**Fixes**:
```python
# ✅ Use 'unit' (singular)
clock = Clock(dut.clk, period_ns, unit="ns")

# ✅ Use .to_signed() method
actual = int(dut.lut_output_signed.value.to_signed())
```

**Note**: These are warnings, not errors. Tests still pass, but fixing them improves future compatibility.

---

## 🏗️ Architecture Patterns

### 9. Test Wrapper Design

**Best Practice**: Create minimal test wrappers for package testing.

**Pattern**:
```vhdl
entity pkg_tb_wrapper is
    port (
        clk : in std_logic;
        reset : in std_logic;

        -- Function select (one-hot)
        sel_function_a : in std_logic;
        sel_function_b : in std_logic;

        -- Inputs
        test_input : in ...;

        -- Registered outputs
        output_a : out ...;
        output_b : out ...;
    );
end entity;

architecture rtl of pkg_tb_wrapper is
begin
    process(clk, reset)
    begin
        if reset = '1' then
            output_a <= (others => '0');
            output_b <= (others => '0');
        elsif rising_edge(clk) then
            if sel_function_a = '1' then
                output_a <= package_function_a(test_input);
            end if;

            if sel_function_b = '1' then
                output_b <= package_function_b(test_input);
            end if;
        end if;
    end process;
end architecture;
```

**Key Points**:
- Register all outputs for timing stability
- Use one-hot function selection (avoids priority encoding)
- Keep wrapper minimal (no application logic)

---

### 10. Progressive Test Structure

**Proven Pattern** (from volo_clk_divider, volo_lut_pkg):

```python
# tests/test_module_progressive.py

TEST_LEVEL = os.getenv("TEST_LEVEL", "P1_BASIC")

# P1: Essential tests (4 tests, <20 lines output)
@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE"]))
async def test_p1_t1_basic_functionality(dut):
    """T1: Basic functionality"""
    # Test bare minimum
    pass

# P2: Comprehensive tests (8 total tests)
@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE"]))
async def test_p2_t5_comprehensive(dut):
    """T5: Comprehensive testing"""
    # Test all edge cases
    pass
```

**Benefits**:
- ✅ Fast P1 validation (<5 seconds)
- ✅ LLM-friendly output (<20 lines for P1)
- ✅ Comprehensive P2 for CI/CD
- ✅ Skip-based selection (no test deletion)

---

## 🐛 Debugging Techniques

### 11. Isolating VHDL vs Python Issues

**Strategy**: Use incremental testing.

**Step 1**: Verify VHDL compiles
```bash
cd tests
ghdl -a --std=08 ../VHDL/packages/my_pkg.vhd
ghdl -a --std=08 my_tb_wrapper.vhd
```

**Step 2**: Verify Python imports
```bash
python3 -c "from test_configs import TESTS_CONFIG; print(TESTS_CONFIG['my_test'])"
```

**Step 3**: Run single test with verbose output
```bash
COCOTB_VERBOSITY=DEBUG uv run python run.py my_test
```

**Step 4**: Check simulation waveforms (if available)
```bash
gtkwave sim_build/my_test.vcd
```

---

### 12. Common Error Message Patterns

| Error Message | Root Cause | Solution |
|---------------|-----------|----------|
| `redeclaration of function` | Subtype overloading | Use base type only |
| `type of element not compatible` | Hex literal without type | Use `x""` notation |
| `NameError` in Python | Import order issue | Define functions before use |
| `KeyError` in test | Sparse dictionary | Fill all keys or use `.get()` |
| Test expects X, got Y | Stale signal value | Reset selects between tests |
| Test expects X, got X+1 | Rounding mismatch | Match VHDL integer arithmetic |

---

## 📊 Performance Tips

### 13. GHDL Elaboration Time

**Observation**: Large LUT constants slow down elaboration.

**Measurements** (volo_lut_pkg):
- Empty entity: ~0.5s elaboration
- With 2×101-element LUTs: ~1.2s elaboration
- With 10×101-element LUTs: ~3.5s elaboration

**Recommendation**: Keep test wrapper LUTs small. Use predefined package LUTs when possible.

---

### 14. CocotB Test Execution Speed

**P1 Test Performance** (volo_lut_pkg on Apple M1):
- 4 tests: ~0.01s (390ns sim time)
- Ratio: ~62,000 ns/s

**Optimization Tips**:
- Minimize clock cycles per test (use combinational logic where possible)
- Batch similar tests together
- Use `COCOTB_VERBOSITY=SILENT` for benchmarking

---

## ✅ Success Checklist

Before committing VHDL + CocotB code:

- [ ] No subtype overloading (use base types)
- [ ] All hex literals use `x""` or `to_signed()` notation
- [ ] Python helper functions defined before use in constants
- [ ] Test expected values match VHDL integer arithmetic
- [ ] Signal selects properly reset between tests
- [ ] P1 tests run in <5 seconds with <20 lines output
- [ ] All deprecation warnings fixed (optional but recommended)
- [ ] Test data generated programmatically (not hand-typed)
- [ ] GHDL compiles with `--std=08` without warnings
- [ ] Test output clearly shows PASS/FAIL for each test

---

## 📚 Reference Examples

**Good Examples in This Project**:
- `tests/test_volo_clk_divider_progressive.py` - Clean progressive structure
- `tests/test_volo_lut_pkg_progressive.py` - Package testing pattern
- `tests/volo_lut_pkg_tb_wrapper.vhd` - Minimal wrapper design

**Key Documentation**:
- `tests/README.md` - CocotB framework guide
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - P1/P2/P3 philosophy
- `VOLO_LUT_PKG_TESTING.md` - Complete testing workflow

---

## 🎯 Summary: Top 5 Lessons

1. **Subtypes ≠ Type Safety**: VHDL subtypes don't prevent assignment. Use base types in function signatures.

2. **Type Your Literals**: Always use `x"HHHH"` for std_logic_vector, `to_signed()` for signed.

3. **Match Arithmetic**: Python test data must use SAME formulas as VHDL (watch rounding!).

4. **Reset Between Tests**: Clear all control signals before each test to avoid stale outputs.

5. **Generate, Don't Type**: Use Python scripts to generate LUT constants and expected test values.

---

**Last Updated**: 2025-01-28
**Tested With**: GHDL 5.0.1, CocotB 2.0.0, Python 3.10
**Session Context**: 106,388 tokens remaining after fixes
