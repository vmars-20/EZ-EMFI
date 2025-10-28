"""
Test constants and utilities for volo_lut_pkg tests

Contains test values, expected results, and error messages for
progressive testing (P1/P2/P3).

Author: Claude Code
Date: 2025-01-28
"""

# =============================================================================
# Test Indices and Expected Values
# =============================================================================

# Basic test indices (P1 - boundary conditions)
TEST_INDEX_MIN = 0
TEST_INDEX_MAX = 100
TEST_INDEX_MID = 50

# Out-of-bounds test indices (should saturate)
TEST_INDEX_UNDERFLOW = -10  # Should clamp to 0
TEST_INDEX_OVERFLOW = 150   # Should clamp to 100
TEST_INDEX_WAY_OVER = 255   # Should clamp to 100

# =============================================================================
# Linear LUT Expected Values (0x0000 to 0xFFFF)
# =============================================================================

# For TEST_LUT_UNSIGNED (linear 0-0xFFFF mapping)
# Formula: value = int((index / 100) * 0xFFFF)
EXPECTED_LUT_UNSIGNED = {
    0:   0x0000,
    1:   0x028F,
    10:  0x1999,
    25:  0x3FFF,
    50:  0x7FFF,
    75:  0xBFFF,
    100: 0xFFFF,
}

# For TEST_LUT_SIGNED (linear -32768 to +32767 mapping)
# Formula: value = -32768 + (index / 100) * 65535
EXPECTED_LUT_SIGNED = {
    0:   -32768,
    25:  -16395,
    50:  0,
    75:  16377,
    100: 32767,
}

# =============================================================================
# Voltage Conversion Test Values
# =============================================================================

# Moku voltage scale: ±5V full scale, 16-bit signed
# Resolution: ~152.59 µV per LSB (10V / 65536)
VOLTAGE_SCALE_FULL = 5.0  # ±5V
VOLTAGE_SCALE_3V3 = 3.3   # 0-3.3V

# Test voltage values (as signed 16-bit digital codes)
# voltage_to_digital(V) ≈ (V / 5.0) * 32767
TEST_VOLTAGES = {
    "0V":     0,        # 0x0000
    "1.65V":  10813,    # 50% of 3.3V (for pct_index test)
    "2.5V":   16384,    # 50% of 5V
    "3.3V":   21627,    # 66% of 5V
    "5V":     32767,    # Max positive
    "-5V":   -32768,    # Max negative
}

# Expected percentage indices for voltage_to_pct_index tests
# Range: 0-3.3V → 0-100%
EXPECTED_VOLTAGE_TO_PCT = {
    0:      0,    # 0V → 0%
    10813:  50,   # 1.65V → 50% (of 3.3V range)
    21627:  100,  # 3.3V → 100%
}

# =============================================================================
# Voltage Conversion Helper (define before use)
# =============================================================================

def voltage_to_digital_approx(voltage):
    """
    Approximate voltage_to_digital conversion for test validation

    Matches volo_voltage_pkg.vhd formula:
    digital = round(voltage / 5.0 * 32767)
    """
    if voltage > 5.0:
        voltage = 5.0
    elif voltage < -5.0:
        voltage = -5.0

    return int(round((voltage / 5.0) * 32767.0))


# =============================================================================
# Predefined LUT Test Values
# =============================================================================

# LINEAR_5V_LUT: 0-5V using voltage_to_digital conversion
# Index 50 should be ≈ 2.5V ≈ 16384
LINEAR_5V_EXPECTED = {
    0:   voltage_to_digital_approx(0.0),
    50:  voltage_to_digital_approx(2.5),
    100: voltage_to_digital_approx(5.0),
}

# LINEAR_3V3_LUT: 0-3.3V using voltage_to_digital conversion
# Index 50 should be ≈ 1.65V ≈ 10813
LINEAR_3V3_EXPECTED = {
    0:   voltage_to_digital_approx(0.0),
    50:  voltage_to_digital_approx(1.65),
    100: voltage_to_digital_approx(3.3),
}

# =============================================================================
# Test Level Configuration
# =============================================================================

# P1 (Basic) - Essential functionality only
P1_TEST_INDICES = [0, 50, 100, 150]  # Min, mid, max, overflow

# P2 (Intermediate) - Comprehensive boundary testing
P2_TEST_INDICES = [0, 1, 10, 25, 50, 75, 90, 99, 100, 101, 150, 255]

# P3 (Comprehensive) - Exhaustive testing
P3_TEST_INDICES = list(range(0, 256))  # All possible 8-bit values

# =============================================================================
# Error Messages (for clear test failures)
# =============================================================================

ERR_BOUNDS_OVERFLOW = "Index > 100 should saturate to LUT[100]"
ERR_BOUNDS_UNDERFLOW = "Index < 0 should saturate to LUT[0]"
ERR_BOUNDS_VALID = "Valid index {idx} should return LUT[{idx}]"

ERR_LUT_UNSIGNED_MISMATCH = "Unsigned LUT lookup mismatch at index {idx}"
ERR_LUT_SIGNED_MISMATCH = "Signed LUT lookup mismatch at index {idx}"

ERR_TO_PCT_INDEX = "to_pct_index({idx}) should clamp to 0-100 range"
ERR_VOLTAGE_TO_PCT = "voltage_to_pct_index failed for {voltage}V"

ERR_PREDEFINED_LUT = "Predefined LUT {name} mismatch at index {idx}"

# =============================================================================
# Test Utilities
# =============================================================================

def get_expected_clamped_index(index):
    """
    Get expected index after clamping to 0-100 range
    """
    if index < 0:
        return 0
    elif index > 100:
        return 100
    else:
        return index

def tolerance_match(actual, expected, tolerance=1):
    """
    Check if actual value matches expected within tolerance
    Useful for voltage conversions with rounding
    """
    return abs(actual - expected) <= tolerance

# =============================================================================
# P1 Test Configuration (Minimal Output)
# =============================================================================

P1_TESTS = [
    {
        "name": "T1: Bounds checking (saturation)",
        "indices": [0, 100, 150],
        "description": "Test that out-of-range indices saturate correctly"
    },
    {
        "name": "T2: Basic LUT lookup",
        "indices": [0, 50, 100],
        "description": "Test basic unsigned LUT lookup at key points"
    },
    {
        "name": "T3: Signed LUT lookup",
        "indices": [0, 50, 100],
        "description": "Test signed LUT lookup (bipolar values)"
    },
    {
        "name": "T4: Predefined LUTs",
        "indices": [0, 50, 100],
        "description": "Test LINEAR_5V_LUT and LINEAR_3V3_LUT"
    },
]

# =============================================================================
# P2 Test Configuration (Comprehensive)
# =============================================================================

P2_TESTS = [
    {
        "name": "T5: Comprehensive bounds testing",
        "indices": [0, 1, 99, 100, 101, 150, 200, 255],
        "description": "Extensive boundary condition testing"
    },
    {
        "name": "T6: Index conversion (to_pct_index)",
        "indices": list(range(0, 256, 10)),
        "description": "Test std_logic_vector to pct_index_t conversion"
    },
    {
        "name": "T7: Voltage integration",
        "test_voltages": [0.0, 1.65, 3.3],
        "description": "Test voltage_to_pct_index for 0-3.3V range"
    },
    {
        "name": "T8: Linear LUT generation",
        "indices": list(range(0, 101, 10)),
        "description": "Validate create_linear_voltage_lut results"
    },
]

# =============================================================================
# Summary Statistics
# =============================================================================

def print_test_summary(level="P1"):
    """Print test configuration summary"""
    if level == "P1":
        num_tests = len(P1_TESTS)
        total_checks = sum(len(t.get("indices", [])) for t in P1_TESTS)
    elif level == "P2":
        num_tests = len(P1_TESTS) + len(P2_TESTS)
        total_checks = (
            sum(len(t.get("indices", [])) for t in P1_TESTS) +
            sum(len(t.get("indices", [])) for t in P2_TESTS)
        )
    else:
        num_tests = 0
        total_checks = 0

    print(f"{level} Configuration:")
    print(f"  Tests: {num_tests}")
    print(f"  Total checks: {total_checks}")
