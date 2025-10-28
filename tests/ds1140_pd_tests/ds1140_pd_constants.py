"""
Test constants and error messages for DS1140-PD progressive testing

DS1140-PD is a refactored version of DS1120-PD with:
- Simplified register layout (7 registers with counter_16bit type)
- Direct 16-bit signals (no high/low byte splits)
- Three outputs: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
- 6-bit FSM observer standard compliance

Author: EZ-EMFI Team
Date: 2025-10-28
"""

MODULE_NAME = "DS1140-PD"

# Default clock period
DEFAULT_CLK_PERIOD_NS = 10  # 100 MHz

class TestValues:
    """Test values for DS1140-PD (keep P1 values SMALL for fast tests)"""

    # Clock
    DEFAULT_CLK_PERIOD_NS = 10  # 100 MHz

    # P1 Test Values (minimal, fast)
    P1_FIRING_DURATION = 4
    P1_COOLING_DURATION = 4
    P1_TRIGGER_VALUE = 0x4000  # Above 2.4V threshold (0x3DCF)
    P1_WAIT_CYCLES = 20
    P1_TIMEOUT_CYCLES = 10

    # P2 Test Values (realistic)
    P2_FIRING_DURATION = 16
    P2_COOLING_DURATION = 16
    P2_WAIT_CYCLES = 50

    # Voltage values (16-bit signed, ±5V full scale)
    DEFAULT_THRESHOLD = 0x3DCF  # 2.4V
    DEFAULT_INTENSITY = 0x2666  # 2.0V
    INTENSITY_ABOVE_CLAMP = 0x7000  # Way above 3.0V limit
    MAX_INTENSITY_3V0 = 0x4CCD  # 3.0V clamp limit

    # FSM state voltages (from fsm_observer, NUM_STATES=8, V_MAX=2.5V)
    # Voltage = state * (2.5V / 7) for states 0-6
    FSM_VOLTAGE_READY = 0.0      # State 0
    FSM_VOLTAGE_ARMED = 0.357    # State 1: ~2.5/7
    FSM_VOLTAGE_FIRING = 0.714   # State 2: ~2*2.5/7
    FSM_VOLTAGE_COOLING = 1.071  # State 3: ~3*2.5/7
    FSM_VOLTAGE_DONE = 1.429     # State 4: ~4*2.5/7
    FSM_VOLTAGE_TIMEDOUT = 1.786 # State 5: ~5*2.5/7

class ErrorMessages:
    """Error message templates"""
    OUTPUT_MISMATCH = "Expected output {}, got {}"
    ENABLE_FAILED = "Enable control failed: {} state expected output {}"
    VOLTAGE_OUT_OF_RANGE = "Voltage {} out of expected range [{}, {}]"
    OUTPUT_NOT_CLAMPED = "Intensity should be clamped to {}V, got {}V"
    THREE_OUTPUTS_FAILED = "Three outputs test failed: OutputA={}, OutputB={}, OutputC={}"
