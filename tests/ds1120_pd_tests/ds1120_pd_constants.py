"""
DS1120-PD VOLO Application Test Constants

Defines test parameters, constants, and error messages for DS1120-PD progressive tests.
Single source of truth for all DS1120-PD test configuration.

Author: EZ-EMFI Team
Date: 2025-01-27
"""

from pathlib import Path

# Module identification
MODULE_NAME = "ds1120_pd_volo"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"

HDL_SOURCES = [
    # Shared volo modules
    VHDL_DIR / "volo_voltage_pkg.vhd",
    VHDL_DIR / "volo_clk_divider.vhd",
    VHDL_DIR / "volo_voltage_threshold_trigger_core.vhd",
    VHDL_DIR / "fsm_observer.vhd",
    VHDL_DIR / "volo_common_pkg.vhd",
    VHDL_DIR / "volo_bram_loader.vhd",
    # DS1120-PD specific
    VHDL_DIR / "ds1120_pd_pkg.vhd",
    VHDL_DIR / "ds1120_pd_fsm.vhd",
    VHDL_DIR / "DS1120_PD_volo_main.vhd",
    VHDL_DIR / "DS1120_PD_volo_shim.vhd",
]

HDL_TOPLEVEL = "ds1120_pd_volo_main"  # lowercase for GHDL

# Test parameters
DEFAULT_CLK_PERIOD_NS = 8  # 125 MHz

# FSM State encodings (from ds1120_pd_pkg.vhd)
STATE_READY = 0b000
STATE_ARMED = 0b001
STATE_FIRING = 0b010
STATE_COOLING = 0b011
STATE_DONE = 0b100
STATE_TIMEDOUT = 0b101
STATE_HARDFAULT = 0b111

# Voltage constants (16-bit signed, ±5V full scale)
VOLTAGE_0V = 0x0000
VOLTAGE_2V0 = 0x3333
VOLTAGE_2V4 = 0x3DCF  # Default trigger threshold
VOLTAGE_3V0 = 0x4CCD  # Maximum intensity (safety limit)
VOLTAGE_5V0 = 0x7FFF

# Test value sets for different phases
class TestValues:
    """Test value sets for different test phases"""

    # P1 - Keep timing short for speed (fast validation)
    P1_WAIT_CYCLES = 10
    P1_FIRING_DURATION = 4
    P1_COOLING_DURATION = 4
    P1_TIMEOUT_CYCLES = 16

    # P2 - Realistic operational values (comprehensive testing)
    P2_WAIT_CYCLES = 30
    P2_FIRING_DURATION = 16
    P2_COOLING_DURATION = 12
    P2_TIMEOUT_CYCLES = 255

    # Test voltages
    P1_TRIGGER_VALUE = 0x4000  # Above 2.4V threshold
    P1_INTENSITY = 0x3000      # Safe 2V intensity
    P2_INTENSITY = 0x4000      # Higher intensity for P2


# Control Register addresses (CR20-CR30)
class ControlRegs:
    """Standard control register addresses"""
    ARM = 20
    FORCE_FIRE = 21
    RESET_FSM = 22
    TIMING_CONTROL = 23
    DELAY_LOWER = 24
    FIRING_DURATION = 25
    COOLING_DURATION = 26
    TRIGGER_THRESH_HIGH = 27
    TRIGGER_THRESH_LOW = 28
    INTENSITY_HIGH = 29
    INTENSITY_LOW = 30


# Error messages with format placeholders
class ErrorMessages:
    """Standardized error messages for consistent test output"""
    RESET_FAILED = "Reset check failed: expected {}, got {}"
    OUTPUT_MISMATCH = "Output mismatch: expected {}, got {}"
    TIMEOUT = "Operation timed out after {} cycles"
    STATE_MISMATCH = "FSM state mismatch: expected {}, got {}"
    CLAMPING_FAILED = "Intensity clamping failed: value {} exceeds 3.0V limit"
    ENABLE_FAILED = "Module should be {} when CR0={:#x}"
    TRIGGER_FAILED = "Trigger detection failed after {} cycles"
