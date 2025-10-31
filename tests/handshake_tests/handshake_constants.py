"""Constants for handshaking protocol tests

Reference: docs/CocoTB-TestingNetworkRegs.md
"""
from pathlib import Path

MODULE_NAME = "handshake_shim"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"
SHARED_DIR = PROJECT_ROOT / "shared" / "custom_inst"

HDL_SOURCES = [
    SHARED_DIR / "custom_inst_common_pkg.vhd",
    VHDL_DIR / "test_shim_handshake.vhd",
]

HDL_TOPLEVEL = "test_shim_handshake"  # Lowercase!

# Test timing
class TestTiming:
    """Clock and timing parameters"""
    CLOCK_PERIOD_NS = 10  # 100MHz
    RESET_CYCLES = 2
    SETTLE_CYCLES = 1

    P1_WAIT_CYCLES = 5    # P1: Short waits
    P2_WAIT_CYCLES = 20   # P2: Longer validation


# Test values
class TestValues:
    """Register test values"""
    # Intensity values (16-bit signed)
    INTENSITY_DEFAULT = 0x2666  # 9830 (2.0V default from HandShakeProtocol.md)
    INTENSITY_NEW_1   = 0x3DCF  # 15823 (2.4V from timing diagram)
    INTENSITY_NEW_2   = 0x1999  # 6553 (1.0V)

    # Threshold values (16-bit signed)
    THRESHOLD_DEFAULT = 0x2E14  # 11796 (2.4V default) - corrected hex value
    THRESHOLD_NEW_1   = 0x3333  # 13107 (2.67V)

    # Control register packing (CR6 = app_reg_6)
    # Format: CR[31:16] = intensity, CR[15:0] = unused
    @staticmethod
    def pack_cr6(intensity: int) -> int:
        """Pack intensity into CR6 format"""
        return (intensity << 16) & 0xFFFF_0000

    @staticmethod
    def pack_cr7(threshold: int) -> int:
        """Pack threshold into CR7 format"""
        return (threshold << 16) & 0xFFFF_0000


# Error messages
class ErrorMessages:
    UPDATE_WHEN_NOT_READY = "Shim updated when ready='0'! Expected {}, got {} after {} cycles"
    NO_UPDATE_WHEN_READY = "Shim did not update when ready='1'! Expected {}, got {}"
    DEFAULT_NOT_LOADED = "Default not loaded on reset! Expected {:#06x}, got {:#06x}"
    NON_ATOMIC_UPDATE = "Registers did not update atomically! intensity updated but threshold did not"
    UNEXPECTED_CHANGE = "Signal changed unexpectedly from {} to {} while gate closed"
