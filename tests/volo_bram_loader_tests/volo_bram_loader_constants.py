"""
Constants for volo_bram_loader CocotB tests.

Includes:
- Test values (addresses, data patterns)
- Expected FSM observer voltages
- Error messages
- State definitions

Author: EZ-EMFI Team
Date: 2025-01-28
"""

# Module identification
MODULE_NAME = "volo_bram_loader"

# ==================================================================================
# FSM State Definitions
# ==================================================================================

class FSMStates:
    """BRAM Loader FSM states (2-bit encoding)"""
    IDLE = 0b00
    LOADING = 0b01
    DONE = 0b10
    RESERVED = 0b11  # Fault state


# ==================================================================================
# FSM Observer Voltage Expectations
# ==================================================================================

# Observer configuration (from volo_bram_loader.vhd):
#   NUM_STATES = 4
#   V_MIN = 0.0
#   V_MAX = 2.0
#   FAULT_STATE_THRESHOLD = 3  (states 0-2 are normal, state 3 is fault)

class ObserverVoltages:
    """Expected voltages from FSM observer (±5V scale, 16-bit signed)"""

    # Voltage calculation: V = V_MIN + (state_index * (V_MAX - V_MIN) / (num_normal - 1))
    # Only 3 normal states (0, 1, 2), so v_step = 2.0 / 2 = 1.0V
    # Digital = round(V * 32767 / 5.0)  [Note: VOLO_DIGITAL_SCALE_FACTOR = 32767/5 = 6553.4]

    IDLE = 0              # State 0: 0.0V → 0 digital
    LOADING = 6553        # State 1: 1.0V → 6553 digital
    DONE = 13107          # State 2: 2.0V → 13107 digital
    RESERVED_FAULT = -13107  # State 3: -2.0V (sign-flip fault from previous state)

    # Tolerance for voltage comparisons (±50 digital counts ≈ ±7.6mV)
    TOLERANCE = 50


# ==================================================================================
# Test Data Patterns
# ==================================================================================

class TestPatterns:
    """Common test data patterns for BRAM writes"""

    # Simple patterns for P1 tests
    PATTERN_ZEROS = 0x00000000
    PATTERN_ONES = 0xFFFFFFFF
    PATTERN_AA55 = 0xAA5555AA
    PATTERN_DEADBEEF = 0xDEADBEEF

    # Sequential patterns for P2 tests
    @staticmethod
    def sequential(start=0, count=4):
        """Generate sequential pattern starting at value"""
        return [start + i for i in range(count)]

    @staticmethod
    def alternating(count=4):
        """Generate alternating 0x00/0xFF pattern"""
        return [0x00000000 if i % 2 == 0 else 0xFFFFFFFF for i in range(count)]


# ==================================================================================
# Control Register Bit Positions
# ==================================================================================

class ControlBits:
    """Control register bit positions and masks"""

    # Control10 - Start + Word Count
    START_BIT = 0
    START_MASK = 0x00000001
    WORD_COUNT_SHIFT = 16
    WORD_COUNT_MASK = 0xFFFF0000

    # Control11 - Address (12-bit, 0-4095)
    ADDR_MASK = 0x00000FFF

    # Control13 - Write Strobe
    WRITE_STROBE_BIT = 0
    WRITE_STROBE_MASK = 0x00000001


# ==================================================================================
# Timing Constants
# ==================================================================================

class Timing:
    """Timing constants for simulation"""

    CLOCK_PERIOD_NS = 8  # 125 MHz clock
    RESET_CYCLES = 5
    SETUP_CYCLES = 2
    STROBE_HOLD_CYCLES = 1
    POST_WRITE_CYCLES = 2
    STATE_TRANSITION_CYCLES = 2


# ==================================================================================
# Error Messages
# ==================================================================================

class ErrorMessages:
    """Standardized error messages for test failures"""

    # Reset errors
    RESET_DONE = "After reset, done should be 0 but got {}"
    RESET_BRAM_WE = "After reset, bram_we should be 0 but got {}"

    # FSM state errors
    FSM_STATE_MISMATCH = "Expected FSM state {} but got {}"
    FSM_STUCK_IN_STATE = "FSM stuck in state {} for {} cycles"

    # Observer voltage errors
    OBSERVER_VOLTAGE_MISMATCH = "Expected observer voltage {} (±{}) but got {}"
    OBSERVER_IDLE_VOLTAGE = "Observer should output {} in IDLE state, got {}"
    OBSERVER_LOADING_VOLTAGE = "Observer should output {} in LOADING state, got {}"
    OBSERVER_DONE_VOLTAGE = "Observer should output {} in DONE state, got {}"

    # BRAM interface errors
    BRAM_ADDR_MISMATCH = "Expected BRAM addr {} but got {}"
    BRAM_DATA_MISMATCH = "Expected BRAM data 0x{:08X} but got 0x{:08X}"
    BRAM_WE_NOT_PULSED = "BRAM write enable should pulse but stayed {}"
    BRAM_WE_STUCK_HIGH = "BRAM write enable stuck high"

    # Loading protocol errors
    DONE_NOT_ASSERTED = "Done signal should be 1 after loading {} words"
    DONE_PREMATURE = "Done signal asserted prematurely at word {}/{}"
    WORD_COUNT_MISMATCH = "Loaded {} words but expected {}"

    # Voltage transition errors
    VOLTAGE_NO_CHANGE = "Observer voltage should change on state transition"
    VOLTAGE_SIGN_UNEXPECTED = "Expected {} voltage but got {} voltage"


# ==================================================================================
# Helper Functions
# ==================================================================================

def voltage_to_digital(voltage: float) -> int:
    """
    Convert voltage to 16-bit signed digital value.

    Args:
        voltage: Voltage in range ±5V

    Returns:
        16-bit signed integer (-32768 to 32767)
    """
    # Digital = round(V * 32768 / 5.0)
    digital = round(voltage * 32768.0 / 5.0)

    # Clamp to 16-bit signed range
    if digital > 32767:
        digital = 32767
    elif digital < -32768:
        digital = -32768

    return digital


def digital_to_voltage(digital: int) -> float:
    """
    Convert 16-bit signed digital value to voltage.

    Args:
        digital: 16-bit signed integer

    Returns:
        Voltage in range ±5V
    """
    return (digital * 5.0) / 32768.0


def voltages_match(expected: int, actual: int, tolerance: int = ObserverVoltages.TOLERANCE) -> bool:
    """
    Check if two voltages match within tolerance.

    Args:
        expected: Expected digital value
        actual: Actual digital value
        tolerance: Allowed difference (default ±50 counts)

    Returns:
        True if values match within tolerance
    """
    return abs(expected - actual) <= tolerance
