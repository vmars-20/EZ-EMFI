"""
Volo Clock Divider Module Test Constants

Shared constants and configurations for all volo_clk_divider tests.
Single source of truth for test parameters.

Author: EZ-EMFI Team
Date: 2025-01-27
"""

from pathlib import Path


# Module identification
MODULE_NAME = "volo_clk_divider"

# HDL sources (relative to tests/ directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"

HDL_SOURCES = [
    VHDL_DIR / "volo_clk_divider.vhd",
]

# Top-level entity name
HDL_TOPLEVEL = "volo_clk_divider"

# Module parameters
MAX_DIV = 256

# Default test parameters
DEFAULT_CLK_PERIOD_NS = 10

# Test timing parameters
RESET_CYCLES = 5
SETTLE_CYCLES = 2

# Test value sets for different phases
class TestValues:
    """Test value sets for different test phases"""

    # P1 - Basic test values (small, fast)
    P1_DIV_VALUES = [2]  # Just test divide by 2
    P1_TEST_CYCLES = 20  # Short test cycles

    # P2 - Intermediate test values
    P2_DIV_VALUES = [1, 10, 255]  # Bypass, typical, maximum
    P2_TEST_CYCLES_SHORT = 20
    P2_TEST_CYCLES_LONG = 512  # For max division test

    # P3 - Comprehensive test values (for future expansion)
    P3_DIV_VALUES = [1, 2, 3, 5, 10, 16, 32, 64, 128, 255]
    P3_TEST_CYCLES = 1024


# Error messages for assertions
class ErrorMessages:
    """Standardized error messages for test assertions"""

    RESET_CLK_EN = "clk_en should be 0 after reset, got {}"
    RESET_STATUS = "stat_reg should be 0 after reset, got {}"
    DIV_BY_1_CLK_EN = "clk_en should be 1 for div_sel=0 (bypass), got {}"
    PULSE_COUNT = "Expected {} pulses, got {}"
    COUNTER_FROZEN = "Counter should be frozen at {}, got {}"
    ENABLE_IGNORED = "clk_en should be 0 when enable=0, got {}"


# Helper functions
def calculate_expected_pulses(div_value: int, total_cycles: int) -> int:
    """
    Calculate expected number of clk_en pulses.

    Args:
        div_value: Division value (0 = bypass, 1+ = divide by N)
        total_cycles: Total clock cycles to observe

    Returns:
        Expected number of clk_en pulses
    """
    if div_value == 0:
        # Bypass mode - clk_en always high
        return total_cycles
    else:
        # Divide mode - pulse every div_value cycles
        return total_cycles // div_value


def get_test_description(phase: int, test_name: str) -> str:
    """
    Generate consistent test descriptions.

    Args:
        phase: Test phase (1, 2, 3, 4)
        test_name: Name of the test

    Returns:
        Formatted test description string
    """
    return f"P{phase} - {test_name}"
