"""
Volo Voltage Package Test Constants

Author: EZ-EMFI Team
Date: 2025-01-27
"""

from pathlib import Path

# Module identification
MODULE_NAME = "volo_voltage_pkg"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"
TESTS_DIR = PROJECT_ROOT / "tests"

HDL_SOURCES = [
    VHDL_DIR / "volo_voltage_pkg.vhd",
    TESTS_DIR / "volo_voltage_pkg_tb_wrapper.vhd",  # Testbench wrapper
]

HDL_TOPLEVEL = "volo_voltage_pkg_tb_wrapper"

# Expected constant values (from volo_voltage_pkg.vhd)
class ExpectedConstants:
    """Expected digital voltage constants"""
    DIGITAL_1V = 6554
    DIGITAL_2V5 = 16384
    DIGITAL_3V3 = 21627
    DIGITAL_5V = 32767
    DIGITAL_NEG_1V = -6554
    DIGITAL_NEG_2V5 = -16384
    DIGITAL_ZERO = 0

# Test conversion values
class TestConversions:
    """Test case values for conversion sanity checks"""
    CASES = [
        ("Zero", 0, 0),
        ("Positive", 16384, 16384),  # 2.5V
        ("Negative", -16384, -16384),  # -2.5V
        ("Max", 32767, 32767),
        ("Min", -32767, -32767),
    ]

# Error messages
class ErrorMessages:
    """Standardized error messages"""
    CONSTANT_MISMATCH = "{} mismatch: expected {}, got {}"
    CONVERSION_FAILED = "{} conversion failed: {} → {} (expected {})"
