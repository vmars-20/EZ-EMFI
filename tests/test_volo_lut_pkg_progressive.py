"""
Progressive CocotB tests for volo_lut_pkg

Test Levels:
- P1_BASIC: Essential functionality only (~4 tests, <20 lines output)
- P2_INTERMEDIATE: Comprehensive testing (all functions)
- P3_COMPREHENSIVE: Exhaustive testing (all indices 0-255)

Author: Claude Code
Date: 2025-01-28
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import os

# Import test utilities and constants
from volo_lut_pkg_tests.volo_lut_pkg_constants import (
    TEST_INDEX_MIN, TEST_INDEX_MAX, TEST_INDEX_MID,
    TEST_INDEX_OVERFLOW, TEST_INDEX_WAY_OVER,
    EXPECTED_LUT_UNSIGNED, EXPECTED_LUT_SIGNED,
    TEST_VOLTAGES, EXPECTED_VOLTAGE_TO_PCT,
    P1_TESTS, P2_TESTS,
    ERR_BOUNDS_OVERFLOW, ERR_LUT_UNSIGNED_MISMATCH, ERR_LUT_SIGNED_MISMATCH,
    get_expected_clamped_index, tolerance_match, voltage_to_digital_approx
)

# Test level from environment (default: P1_BASIC)
TEST_LEVEL = os.getenv("TEST_LEVEL", "P1_BASIC")

# Verbosity control
VERBOSITY = os.getenv("COCOTB_VERBOSITY", "MINIMAL")


# =============================================================================
# Test Utilities
# =============================================================================

async def setup_clock(dut, period_ns=10):
    """Start clock"""
    clock = Clock(dut.clk, period_ns, units="ns")
    cocotb.start_soon(clock.start())
    await RisingEdge(dut.clk)


async def reset_dut(dut):
    """Apply reset"""
    dut.reset.value = 1
    dut.test_index.value = 0
    dut.test_voltage.value = 0
    dut.sel_lut_lookup.value = 0
    dut.sel_lut_lookup_signed.value = 0
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)


async def test_lut_lookup_unsigned(dut, index, expected, test_name=""):
    """Test unsigned LUT lookup"""
    dut.test_index.value = index
    dut.sel_lut_lookup.value = 1
    dut.sel_lut_lookup_signed.value = 0
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Allow registered output to update

    actual = int(dut.lut_output_unsigned.value)

    if VERBOSITY in ["VERBOSE", "DEBUG"]:
        dut._log.info(f"{test_name}: Index={index}, Expected=0x{expected:04X}, Actual=0x{actual:04X}")

    assert actual == expected, ERR_LUT_UNSIGNED_MISMATCH.format(idx=index)


async def test_lut_lookup_signed(dut, index, expected, test_name=""):
    """Test signed LUT lookup"""
    dut.test_index.value = index
    dut.sel_lut_lookup.value = 0
    dut.sel_lut_lookup_signed.value = 1
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    actual = int(dut.lut_output_signed.value.signed_integer)

    if VERBOSITY in ["VERBOSE", "DEBUG"]:
        dut._log.info(f"{test_name}: Index={index}, Expected={expected}, Actual={actual}")

    assert actual == expected, ERR_LUT_SIGNED_MISMATCH.format(idx=index)


async def test_to_pct_index(dut, index, test_name=""):
    """Test to_pct_index clamping"""
    expected = get_expected_clamped_index(index)

    # Clear all selects first (prevent stale outputs)
    dut.sel_lut_lookup.value = 0
    dut.sel_lut_lookup_signed.value = 0
    dut.sel_to_pct_index.value = 0
    dut.sel_voltage_to_pct.value = 0
    await RisingEdge(dut.clk)

    # Now set input and select
    dut.test_index.value = index & 0xFF  # Mask to 8-bit
    dut.sel_to_pct_index.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    actual = int(dut.pct_index_output.value)

    if VERBOSITY in ["VERBOSE", "DEBUG"]:
        dut._log.info(f"{test_name}: Index={index}, Expected={expected}, Actual={actual}")

    assert actual == expected, f"to_pct_index({index}) should clamp to {expected}, got {actual}"


# =============================================================================
# P1 Tests (Basic - Minimal Output)
# =============================================================================

@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p1_t1_bounds_checking(dut):
    """T1: Bounds checking (saturation)"""
    if VERBOSITY != "SILENT":
        dut._log.info("=" * 70)
        dut._log.info("P1 - BASIC TESTS")
        dut._log.info("T1: Bounds checking (saturation)")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test index 0 (min boundary)
    await test_lut_lookup_unsigned(dut, 0, EXPECTED_LUT_UNSIGNED[0], "  Index 0")

    # Test index 100 (max boundary)
    await test_lut_lookup_unsigned(dut, 100, EXPECTED_LUT_UNSIGNED[100], "  Index 100")

    # Test index 150 (overflow - should saturate to 100)
    await test_lut_lookup_unsigned(dut, 150, EXPECTED_LUT_UNSIGNED[100], "  Index 150→100")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p1_t2_basic_lut_lookup(dut):
    """T2: Basic LUT lookup"""
    if VERBOSITY != "SILENT":
        dut._log.info("T2: Basic LUT lookup (unsigned)")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test key points
    for index in [0, 50, 100]:
        await test_lut_lookup_unsigned(dut, index, EXPECTED_LUT_UNSIGNED[index], f"  Index {index}")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p1_t3_signed_lut_lookup(dut):
    """T3: Signed LUT lookup"""
    if VERBOSITY != "SILENT":
        dut._log.info("T3: Signed LUT lookup (bipolar)")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test key points (bipolar: -32768 to +32767)
    for index in [0, 50, 100]:
        await test_lut_lookup_signed(dut, index, EXPECTED_LUT_SIGNED[index], f"  Index {index}")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P1_BASIC", "P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p1_t4_predefined_luts(dut):
    """T4: Predefined LUTs (LINEAR_5V_LUT, LINEAR_3V3_LUT)"""
    if VERBOSITY != "SILENT":
        dut._log.info("T4: Predefined LUTs")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test LINEAR_5V_LUT (always available output)
    for index in [0, 50, 100]:
        dut.test_index.value = index
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        actual_5v = int(dut.linear_5v_lut_out.value.signed_integer)
        expected_5v = voltage_to_digital_approx(index / 100.0 * 5.0)

        # Allow small tolerance for rounding
        assert tolerance_match(actual_5v, expected_5v, tolerance=10), \
            f"LINEAR_5V_LUT[{index}]: expected ≈{expected_5v}, got {actual_5v}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            dut._log.info(f"  LINEAR_5V_LUT[{index}] = {actual_5v} (expected ≈{expected_5v})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")
        dut._log.info("=" * 70)
        dut._log.info("ALL 4 P1 TESTS PASSED")


# =============================================================================
# P2 Tests (Intermediate - Comprehensive)
# =============================================================================

@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p2_t5_comprehensive_bounds(dut):
    """T5: Comprehensive bounds testing"""
    if VERBOSITY != "SILENT":
        dut._log.info("=" * 70)
        dut._log.info("P2 - INTERMEDIATE TESTS")
        dut._log.info("T5: Comprehensive bounds testing")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test boundary conditions extensively
    test_indices = [0, 1, 99, 100, 101, 150, 200, 255]

    for index in test_indices:
        # Expected: clamp to 100 if > 100
        if index <= 100:
            # Calculate expected value on-the-fly for indices not in dict
            if index in EXPECTED_LUT_UNSIGNED:
                expected = EXPECTED_LUT_UNSIGNED[index]
            else:
                expected = int((index / 100.0) * 0xFFFF)
        else:
            expected = EXPECTED_LUT_UNSIGNED[100]

        await test_lut_lookup_unsigned(dut, index, expected, f"  Index {index}")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p2_t6_index_conversion(dut):
    """T6: Index conversion (to_pct_index)"""
    if VERBOSITY != "SILENT":
        dut._log.info("T6: Index conversion (to_pct_index)")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test conversion with clamping
    test_values = list(range(0, 256, 25)) + [100, 101, 150, 200, 255]

    for index in test_values:
        await test_to_pct_index(dut, index, f"  to_pct_index({index})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p2_t7_voltage_integration(dut):
    """T7: Voltage integration (voltage_to_pct_index)"""
    if VERBOSITY != "SILENT":
        dut._log.info("T7: Voltage integration")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test voltage to percentage conversion (0-3.3V range)
    for voltage_name, digital_value in TEST_VOLTAGES.items():
        if digital_value in EXPECTED_VOLTAGE_TO_PCT:
            # Clear all selects first (prevent stale outputs)
            dut.sel_lut_lookup.value = 0
            dut.sel_lut_lookup_signed.value = 0
            dut.sel_to_pct_index.value = 0
            dut.sel_voltage_to_pct.value = 0
            await RisingEdge(dut.clk)

            # Now set input and select
            dut.test_voltage.value = digital_value
            dut.sel_voltage_to_pct.value = 1
            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)

            actual = int(dut.pct_index_output.value)
            expected = EXPECTED_VOLTAGE_TO_PCT[digital_value]

            # Allow ±1 tolerance for rounding
            assert tolerance_match(actual, expected, tolerance=1), \
                f"voltage_to_pct_index({voltage_name}): expected {expected}, got {actual}"

            if VERBOSITY in ["VERBOSE", "DEBUG"]:
                dut._log.info(f"  {voltage_name} → {actual}% (expected {expected}%)")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")


@cocotb.test(skip=(TEST_LEVEL not in ["P2_INTERMEDIATE", "P3_COMPREHENSIVE"]))
async def test_p2_t8_linear_lut_generation(dut):
    """T8: Linear LUT generation (create_linear_voltage_lut)"""
    if VERBOSITY != "SILENT":
        dut._log.info("T8: Linear LUT generation")

    await setup_clock(dut)
    await reset_dut(dut)

    # Test LINEAR_3V3_LUT across full range
    test_indices = list(range(0, 101, 10))

    for index in test_indices:
        dut.test_index.value = index
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        actual = int(dut.linear_3v3_lut_out.value.signed_integer)
        expected = voltage_to_digital_approx(index / 100.0 * 3.3)

        # Allow tolerance for rounding
        assert tolerance_match(actual, expected, tolerance=20), \
            f"LINEAR_3V3_LUT[{index}]: expected ≈{expected}, got {actual}"

        if VERBOSITY in ["VERBOSE", "DEBUG"]:
            voltage = index / 100.0 * 3.3
            dut._log.info(f"  Index {index:3d} ({voltage:.2f}V) = {actual:6d} (expected ≈{expected:6d})")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS")
        dut._log.info("=" * 70)
        dut._log.info("ALL 8 P2 TESTS PASSED (P1+P2)")


# =============================================================================
# P3 Tests (Comprehensive - Exhaustive)
# =============================================================================

@cocotb.test(skip=(TEST_LEVEL != "P3_COMPREHENSIVE"))
async def test_p3_exhaustive_lut_lookup(dut):
    """P3: Exhaustive LUT lookup (all indices 0-255)"""
    if VERBOSITY != "SILENT":
        dut._log.info("=" * 70)
        dut._log.info("P3 - COMPREHENSIVE TESTS")
        dut._log.info("T9: Exhaustive LUT lookup (0-255)")

    await setup_clock(dut)
    await reset_dut(dut)

    error_count = 0

    for index in range(256):
        # Expected: clamp to 100 if > 100
        if index <= 100:
            expected = EXPECTED_LUT_UNSIGNED.get(index, None)
            if expected is None:
                # Calculate for indices not in expected table
                expected = int((index / 100.0) * 0xFFFF)
        else:
            expected = EXPECTED_LUT_UNSIGNED[100]

        try:
            await test_lut_lookup_unsigned(dut, index, expected, f"Index {index}")
        except AssertionError as e:
            error_count += 1
            if VERBOSITY in ["VERBOSE", "DEBUG"]:
                dut._log.error(f"  FAIL at index {index}: {e}")

    if error_count > 0:
        raise AssertionError(f"P3: {error_count} failures out of 256 tests")

    if VERBOSITY != "SILENT":
        dut._log.info("  ✓ PASS (256/256 tests)")
        dut._log.info("=" * 70)
        dut._log.info("ALL P3 TESTS PASSED")
