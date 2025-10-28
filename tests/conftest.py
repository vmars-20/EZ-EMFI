"""
CocotB Test Fixtures and Utilities for Volo VHDL Project

This file provides shared test utilities that eliminate code duplication
across all testbenches. pytest automatically loads this file.

Usage in tests:
    from conftest import setup_clock, reset_active_low, count_pulses

    @cocotb.test()
    async def test_something(dut):
        await setup_clock(dut)
        await reset_active_low(dut)
        # ... your test logic

Author: Claude Code (CocotB migration)
Date: 2025-01-22
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, with_timeout


# Default clock period for all tests
DEFAULT_CLK_PERIOD_NS = 10

# Default wall-clock timeout for all tests (prevents infinite loops)
DEFAULT_TEST_TIMEOUT_SEC = 10


# =============================================================================
# Timeout Management
# =============================================================================

async def run_with_timeout(test_coro, timeout_sec=DEFAULT_TEST_TIMEOUT_SEC, test_name="test"):
    """
    Run a test coroutine with wall-clock timeout to prevent infinite loops

    This wraps test logic with a timeout that triggers after a fixed amount of
    real (wall-clock) time, not simulation cycles. Use this to prevent tests
    from hanging indefinitely if the simulation enters an infinite loop.

    Args:
        test_coro: Coroutine to run (the test logic)
        timeout_sec: Wall-clock timeout in seconds (default: 10)
        test_name: Name of test for error messages (optional)

    Raises:
        cocotb.result.SimTimeoutError: If timeout expires before test completes

    Example - Basic usage:
        @cocotb.test()
        async def test_something(dut):
            async def test_logic():
                await setup_clock(dut, clk_signal="Clk")
                await reset_active_high(dut, rst_signal="Reset")
                # ... your test code ...

            await run_with_timeout(test_logic(), timeout_sec=10)

    Example - Custom timeout:
        await run_with_timeout(test_logic(), timeout_sec=30, test_name="long_test")

    Note: This uses wall-clock time, NOT simulation time. A 10-second timeout
    means 10 real seconds, regardless of how many simulation cycles run.
    """
    try:
        result = await with_timeout(test_coro, timeout_time=timeout_sec, timeout_unit="sec")
        return result
    except Exception as e:
        # Check if it's a timeout error
        if "Timeout" in str(e) or "timeout" in str(type(e).__name__).lower():
            raise AssertionError(
                f"Test '{test_name}' TIMEOUT after {timeout_sec}s wall-clock time. "
                f"Possible infinite loop or simulation stuck. Original error: {e}"
            )
        else:
            # Re-raise other exceptions unchanged
            raise


# =============================================================================
# MCC Control0 Bit Scheme (CRITICAL for all MCC modules!)
# =============================================================================
#
# ⚠️ WARNING: Missing Clock Enable (bit 29) is the #1 cause of frozen modules!
#
# ALL MCC modules require THREE control bits in Control0[31:29]:
#   Control0[31] = MCC_READY (active-high) - Set by MCC after deployment
#   Control0[30] = Enable (active-high) - User-controlled enable/disable
#   Control0[29] = ClkEn (active-high) - ⚠️ MANDATORY for clocked logic
#
# Correct pattern: 0xE0000000 (bits 31+30+29 all set)
# WRONG pattern:   0xC0000000 (missing bit 29) → MODULE FREEZES!
#
# Reference: mcc_debugging_techniques.md (Serena memory)
# =============================================================================

MCC_READY_BIT = 31  # Set by MCC after deployment
ENABLE_BIT = 30     # User-controlled enable/disable
CLK_EN_BIT = 29     # ⚠️ MANDATORY for clocked modules!

MCC_CR0_BASE = (1 << MCC_READY_BIT) | (1 << ENABLE_BIT) | (1 << CLK_EN_BIT)  # 0xE0000000


def validate_control0(cr0_value: int, context: str = ""):
    """Validate Control0 has all 3 required control bits.

    Warns if Clock Enable (bit 29) is missing, which causes modules
    to freeze even when "enabled".

    Args:
        cr0_value: Control0 register value
        context: Description of where this value is being used (for warnings)

    Example:
        validate_control0(0xC0000000)  # Warns: missing bit 29!
        validate_control0(0xE0000000)  # OK: all 3 bits present
    """
    mcc_ready = (cr0_value >> MCC_READY_BIT) & 1
    enable = (cr0_value >> ENABLE_BIT) & 1
    clk_en = (cr0_value >> CLK_EN_BIT) & 1

    if enable and not clk_en:
        import warnings
        warnings.warn(
            f"\n{'='*70}\n"
            f"⚠️  WARNING: Control0={cr0_value:#010x} missing Clock Enable (bit 29)!\n"
            f"{'='*70}\n"
            f"  Bit 31 (MCC_READY): {mcc_ready}\n"
            f"  Bit 30 (Enable):    {enable}\n"
            f"  Bit 29 (ClkEn):     {clk_en}  ← ⚠️ MUST BE 1 for clocked modules!\n"
            f"{'='*70}\n"
            f"Module will FREEZE without Clock Enable!\n"
            f"Use: {(cr0_value | (1 << CLK_EN_BIT)):#010x} instead\n"
            f"Context: {context}\n"
            f"{'='*70}",
            stacklevel=3
        )


def mcc_cr0(divider: int = 0, extra_bits: int = 0) -> int:
    """Construct Control0 with mandatory 3-bit control scheme.

    Always includes bits 31+30+29 (MCC_READY + Enable + ClkEn).

    Args:
        divider: Clock divider value (0-255), placed in bits 23:16
        extra_bits: Additional bits to OR in (e.g., mode flags)

    Returns:
        Control0 value with all 3 control bits set

    Example:
        cr0 = mcc_cr0()               # Returns 0xE0000000 (base)
        cr0 = mcc_cr0(divider=240)    # Returns 0xEEF00000
        cr0 = mcc_cr0(divider=1)      # Returns 0xEE010000
    """
    value = MCC_CR0_BASE
    if divider > 0:
        value |= (divider & 0xFF) << 16  # Divider in bits 23:16
    value |= extra_bits
    return value


# =============================================================================
# Clock Management
# =============================================================================

async def setup_clock(dut, period_ns=DEFAULT_CLK_PERIOD_NS, clk_signal="clk"):
    """
    Start a clock on the DUT

    Args:
        dut: Device Under Test
        period_ns: Clock period in nanoseconds (default: 10ns = 100MHz)
        clk_signal: Name of clock signal (default: "clk")

    Returns:
        Clock object (can be ignored, runs in background)

    Example:
        await setup_clock(dut)
        await setup_clock(dut, period_ns=20)  # 50MHz clock
        await setup_clock(dut, clk_signal="Clk")  # MCC style
    """
    clk = getattr(dut, clk_signal)
    clock = cocotb.start_soon(Clock(clk, period_ns, units="ns").start())
    dut._log.info(f"✓ Clock started on '{clk_signal}' ({period_ns}ns period = {1000/period_ns:.1f}MHz)")
    return clock


# =============================================================================
# Reset Sequences
# =============================================================================

async def reset_active_low(dut, cycles=2, rst_signal="rst_n"):
    """
    Apply active-low reset sequence (standard for most modules)

    Args:
        dut: Device Under Test
        cycles: Number of clock cycles to hold reset (default: 2)
        rst_signal: Name of reset signal (default: "rst_n")

    Example:
        await reset_active_low(dut)
        await reset_active_low(dut, cycles=5)
        await reset_active_low(dut, rst_signal="nReset")
    """
    rst = getattr(dut, rst_signal)
    clk = dut.clk

    # Apply reset
    rst.value = 0
    await ClockCycles(clk, cycles)

    # Release reset
    rst.value = 1
    await ClockCycles(clk, 1)

    dut._log.info(f"✓ Reset complete (active-low, {cycles} cycles)")


async def reset_active_high(dut, cycles=2, rst_signal="rst"):
    """
    Apply active-high reset sequence (used by some MCC modules)

    Args:
        dut: Device Under Test
        cycles: Number of clock cycles to hold reset (default: 2)
        rst_signal: Name of reset signal (default: "rst", tries "Reset" if not found)

    Example:
        await reset_active_high(dut)
        await reset_active_high(dut, rst_signal="Reset")  # MCC style
    """
    # Try specified signal name first, fall back to common alternatives
    if hasattr(dut, rst_signal):
        rst = getattr(dut, rst_signal)
    elif hasattr(dut, "Reset"):
        rst = dut.Reset
        rst_signal = "Reset"
    else:
        rst = getattr(dut, rst_signal)  # Will raise AttributeError if not found

    clk = dut.clk if hasattr(dut, "clk") else dut.Clk

    # Apply reset
    rst.value = 1
    await ClockCycles(clk, cycles)

    # Release reset
    rst.value = 0
    await ClockCycles(clk, 1)

    dut._log.info(f"✓ Reset complete (active-high, {cycles} cycles)")


async def reset_dut(dut, active_low=True, cycles=2, rst_signal=None):
    """
    Apply reset sequence (auto-detects active-low vs active-high)

    Args:
        dut: Device Under Test
        active_low: True for active-low (rst_n), False for active-high (rst/Reset)
        cycles: Number of clock cycles to hold reset (default: 2)
        rst_signal: Optional signal name override

    Example:
        await reset_dut(dut)  # Active-low by default
        await reset_dut(dut, active_low=False)  # Active-high
    """
    if active_low:
        signal = rst_signal if rst_signal else "rst_n"
        await reset_active_low(dut, cycles=cycles, rst_signal=signal)
    else:
        signal = rst_signal if rst_signal else "rst"
        await reset_active_high(dut, cycles=cycles, rst_signal=signal)


# =============================================================================
# Signal Monitoring and Counting
# =============================================================================

async def count_pulses(signal, clk, num_cycles):
    """
    Count how many times a signal goes high (pulses) over a number of clock cycles

    Args:
        signal: Signal to monitor (e.g., dut.clk_en)
        clk: Clock signal to synchronize to (e.g., dut.clk)
        num_cycles: Number of clock cycles to observe

    Returns:
        int: Number of pulses detected

    Example:
        pulses = await count_pulses(dut.clk_en, dut.clk, 100)
        assert pulses == 10, f"Expected 10 pulses, got {pulses}"
    """
    count = 0
    for _ in range(num_cycles):
        await RisingEdge(clk)
        if signal.value == 1:
            count += 1
    return count


async def wait_for_value(signal, expected_value, clk, timeout_cycles=1000):
    """
    Wait for a signal to reach an expected value (with timeout)

    Args:
        signal: Signal to monitor
        expected_value: Value to wait for
        clk: Clock signal
        timeout_cycles: Maximum cycles to wait (default: 1000)

    Returns:
        bool: True if value reached, False if timeout

    Example:
        success = await wait_for_value(dut.done, 1, dut.clk)
        assert success, "Module never signaled done"
    """
    for cycle in range(timeout_cycles):
        await RisingEdge(clk)
        if signal.value == expected_value:
            return True
    return False


async def capture_signal_sequence(signal, clk, num_cycles):
    """
    Capture a sequence of signal values over multiple clock cycles

    Args:
        signal: Signal to capture
        clk: Clock signal
        num_cycles: Number of cycles to capture

    Returns:
        list: List of signal values

    Example:
        sequence = await capture_signal_sequence(dut.state, dut.clk, 20)
        assert sequence == [0, 0, 1, 2, 3, 0, 0, ...]  # Verify state transitions
    """
    values = []
    for _ in range(num_cycles):
        await RisingEdge(clk)
        values.append(int(signal.value))
    return values


# =============================================================================
# Initialization Helpers
# =============================================================================

async def init_dut(dut, clock_period_ns=DEFAULT_CLK_PERIOD_NS, active_low_reset=True):
    """
    Complete DUT initialization: start clock + apply reset

    This is the most common setup sequence. Use this for simple tests.

    Args:
        dut: Device Under Test
        clock_period_ns: Clock period in ns (default: 10ns)
        active_low_reset: True for rst_n, False for rst/Reset

    Example:
        await init_dut(dut)  # Standard init
        await init_dut(dut, clock_period_ns=20, active_low_reset=False)  # Custom
    """
    await setup_clock(dut, period_ns=clock_period_ns)
    await reset_dut(dut, active_low=active_low_reset)


# =============================================================================
# Division Ratio Testing (Specific to clk_divider modules)
# =============================================================================

async def verify_division_ratio(dut, div_sel, expected_ratio, observation_cycles=None):
    """
    Verify that a clock divider produces the expected division ratio

    Args:
        dut: Clock divider DUT (must have clk_en output)
        div_sel: Division select value
        expected_ratio: Expected division ratio
        observation_cycles: Cycles to observe (default: expected_ratio * 10)

    Returns:
        tuple: (actual_pulses, expected_pulses, passed)

    Example:
        actual, expected, passed = await verify_division_ratio(dut, 10, 10)
        assert passed, f"Division failed: {actual} != {expected}"
    """
    if observation_cycles is None:
        observation_cycles = expected_ratio * 10

    dut.div_sel.value = div_sel
    dut.enable.value = 1
    await ClockCycles(dut.clk, 2)  # Let div_sel load

    pulse_count = await count_pulses(dut.clk_en, dut.clk, observation_cycles)
    expected_pulses = observation_cycles // expected_ratio

    passed = (pulse_count == expected_pulses)

    if passed:
        dut._log.info(f"✓ Division ratio verified: div_sel={div_sel} → {pulse_count} pulses in {observation_cycles} cycles")
    else:
        dut._log.warning(f"✗ Division mismatch: expected {expected_pulses}, got {pulse_count}")

    return pulse_count, expected_pulses, passed


# =============================================================================
# Assertion Helpers
# =============================================================================

def assert_signal_value(signal, expected, message=""):
    """
    Assert a signal has expected value with helpful error message

    Args:
        signal: Signal to check
        expected: Expected value (int or string)
        message: Optional custom message

    Example:
        assert_signal_value(dut.output, 0x1234, "Output mismatch after reset")
    """
    actual = int(signal.value)
    if isinstance(expected, str):
        expected = int(expected, 0)  # Support "0x1234" format

    if actual != expected:
        msg = f"Signal value mismatch: expected {expected:#x}, got {actual:#x}"
        if message:
            msg = f"{message}: {msg}"
        assert False, msg


async def assert_pulse_count(signal, clk, cycles, expected, tolerance=0):
    """
    Assert that a signal pulses expected number of times (with optional tolerance)

    Args:
        signal: Signal to monitor
        clk: Clock signal
        cycles: Number of cycles to observe
        expected: Expected pulse count
        tolerance: Allowed deviation (default: 0)

    Example:
        await assert_pulse_count(dut.clk_en, dut.clk, 100, 10, tolerance=1)
    """
    actual = await count_pulses(signal, clk, cycles)

    if tolerance > 0:
        passed = abs(actual - expected) <= tolerance
        msg = f"Pulse count: expected {expected}±{tolerance}, got {actual}"
    else:
        passed = (actual == expected)
        msg = f"Pulse count: expected {expected}, got {actual}"

    assert passed, msg


# =============================================================================
# Waveform Helpers
# =============================================================================

def log_signal_table(dut, signal_names, title="Signal Values"):
    """
    Log a formatted table of signal values (useful for debugging)

    Args:
        dut: Device Under Test
        signal_names: List of signal names to display
        title: Table title

    Example:
        log_signal_table(dut, ["clk_en", "enable", "div_sel", "stat_reg"])
    """
    dut._log.info("=" * 60)
    dut._log.info(title)
    dut._log.info("-" * 60)
    for name in signal_names:
        signal = getattr(dut, name)
        value = signal.value
        dut._log.info(f"  {name:20s} = {value}")
    dut._log.info("=" * 60)


# =============================================================================
# MCC (Moku CustomWrapper) Helpers
# =============================================================================

async def init_mcc_inputs(dut):
    """
    Initialize all MCC input channels to zero

    Args:
        dut: Device Under Test (CustomWrapper)

    Example:
        await init_mcc_inputs(dut)
    """
    dut.InputA.value = 0
    dut.InputB.value = 0
    dut.InputC.value = 0
    dut.InputD.value = 0


async def mcc_set_regs(dut, control_regs,
                       set_mcc_ready=True,
                       simulate_network_delay=True,
                       total_delay_ms=None,
                       per_reg_delay_ms=None):
    """
    Set MCC control registers with realistic network latency simulation

    This simulates the real-world MCC register update process over network.
    Use this for BOTH initial configuration and runtime register updates.

    Network Latency Simulation:
    - Total delay before first write: 10-200ms (random if not specified)
    - Per-register delay: 1-10ms (random if not specified)
    - Realistic for Moku network communication

    MCC_READY Convention (CR0[31]):
    - CR0[31] = 0: Module disabled (safe during "all-zero" bitstream load)
    - CR0[31] = 1: Module enabled and ready for operation
    - set_mcc_ready=True will automatically set CR0[31]=1 after config

    Args:
        dut: Device Under Test (CustomWrapper entity)
        control_regs: Dict of {reg_num: value} to set
                      Note: CR0[31] (MCC_READY) is auto-handled if set_mcc_ready=True
        set_mcc_ready: If True, sets CR0[31]=1 after loading registers (default: True)
        simulate_network_delay: Enable network latency simulation (default: True)
        total_delay_ms: Total delay before first register write (default: 10-200ms random)
        per_reg_delay_ms: Delay between each register write (default: 1-10ms random)

    Example - Initial configuration with MCC_READY:
        await setup_clock(dut, clk_signal="Clk")
        await reset_active_high(dut, rst_signal="Reset")
        await init_mcc_inputs(dut)

        await mcc_set_regs(dut, {
            0: 0x40000000,  # User config bits (CR0[31] handled separately)
            1: 0x0000007F,  # DelayS1
            5: 0x0000199A   # Voltage level
        }, set_mcc_ready=True)  # Sets CR0[31]=1 to enable module

        await wait_for_mcc_ready(dut)  # Let module settle

    Example - Runtime update (module already enabled):
        await mcc_set_regs(dut, {
            5: 0x00001000   # Change voltage only
        }, set_mcc_ready=False, total_delay_ms=15.0)  # Explicit 15ms delay

    Example - Reproducible timing (no randomness):
        await mcc_set_regs(dut, {...},
                          simulate_network_delay=False)  # No delay, immediate update
    """
    import random
    from cocotb.triggers import Timer, ClockCycles

    # Total delay before starting register writes
    if simulate_network_delay and total_delay_ms is None:
        total_delay_ms = random.uniform(10, 200)  # 10-200ms realistic range

    if simulate_network_delay and total_delay_ms > 0:
        delay_ns = int(total_delay_ms * 1_000_000)
        dut._log.info(f"⏱  Network latency: {total_delay_ms:.1f}ms")
        await Timer(delay_ns, units="ns")

    # Write each register with optional per-register delay
    for reg_num, value in sorted(control_regs.items()):
        # Mask out bit 31 from CR0 if set_mcc_ready=True (we'll set it last)
        if reg_num == 0 and set_mcc_ready:
            value = value & 0x7FFFFFFF  # Clear bit 31

        getattr(dut, f"Control{reg_num}").value = value
        dut._log.info(f"  Control{reg_num} ← 0x{value:08X}")

        # Per-register delay (simulate sequential network writes)
        if simulate_network_delay:
            if per_reg_delay_ms is None:
                delay = random.uniform(1, 10)  # 1-10ms per register
            else:
                delay = per_reg_delay_ms

            if delay > 0:
                await Timer(int(delay * 1_000_000), units="ns")

    await ClockCycles(dut.Clk, 2)

    # Set MCC_READY flag (CR0[31]=1) to enable module
    if set_mcc_ready:
        cr0_current = int(dut.Control0.value)
        cr0_ready = cr0_current | 0x80000000  # Set bit 31

        # Validate Control0 has all 3 required bits (warns if ClkEn missing)
        validate_control0(cr0_ready, context="mcc_set_regs()")

        dut.Control0.value = cr0_ready
        dut._log.info(f"✓ MCC_READY asserted (CR0 = 0x{cr0_ready:08X})")
        await ClockCycles(dut.Clk, 2)


async def wait_for_mcc_ready(dut, settle_cycles=10):
    """
    Wait for module to stabilize after MCC_READY assertion

    After setting CR0[31]=1 (MCC_READY), modules may need time to:
    - Initialize internal state machines
    - Settle outputs to safe/default values
    - Complete any startup sequences

    This function provides a simple fixed-cycle settle time.

    Args:
        dut: Device Under Test
        settle_cycles: Number of clock cycles to wait (default: 10)

    Returns:
        None (always succeeds)

    Example:
        await mcc_set_regs(dut, {...}, set_mcc_ready=True)
        await wait_for_mcc_ready(dut)  # Default 10 cycles
        # Now safe to test module behavior

    Example - Longer settle time:
        await wait_for_mcc_ready(dut, settle_cycles=50)
    """
    clk = dut.Clk if hasattr(dut, "Clk") else dut.clk
    await ClockCycles(clk, settle_cycles)
    dut._log.info(f"✓ Module settled ({settle_cycles} cycles after MCC_READY)")


async def wait_for_first_clk_en(dut, clk_en_signal="clk_en", timeout_cycles=1000):
    """
    Wait for the first clock enable pulse (useful for clock divider modules)

    After initialization, modules with clock dividers may need time before
    their first clk_en pulse. This helper waits for that first pulse to
    ensure timing is stable before running tests.

    Args:
        dut: Device Under Test
        clk_en_signal: Name of clock enable signal (default: "clk_en")
        timeout_cycles: Maximum cycles to wait (default: 1000)

    Returns:
        bool: True if pulse detected, False if timeout

    Example:
        await mcc_set_regs(dut, {...}, set_mcc_ready=True)
        await wait_for_mcc_ready(dut)

        # Wait for clock divider to produce first pulse
        success = await wait_for_first_clk_en(dut)
        assert success, "Clock divider never produced clk_en pulse"

    Example - Custom signal name:
        success = await wait_for_first_clk_en(dut, clk_en_signal="ClkEn")
    """
    clk = dut.Clk if hasattr(dut, "Clk") else dut.clk
    clk_en = getattr(dut, clk_en_signal)

    for cycle in range(timeout_cycles):
        await RisingEdge(clk)
        if int(clk_en.value) == 1:
            dut._log.info(f"✓ First clk_en pulse detected (after {cycle} cycles)")
            return True

    dut._log.warning(f"✗ Timeout: No clk_en pulse detected in {timeout_cycles} cycles")
    return False


async def mcc_disable(dut, simulate_network_delay=True, delay_ms=None):
    """
    Safely disable MCC module by clearing CR0[31] (MCC_READY flag)

    This parks the module in a safe disabled state, useful for:
    - Testing enable/disable sequences
    - Preparing for configuration changes
    - Verifying safe shutdown behavior

    Args:
        dut: Device Under Test (CustomWrapper)
        simulate_network_delay: Enable network latency (default: True)
        delay_ms: Override delay (default: 1-10ms random)

    Returns:
        None

    Example:
        # Disable module to change configuration
        await mcc_disable(dut)
        await mcc_set_regs(dut, {...}, set_mcc_ready=True)  # Re-enable with new config

    Example - Immediate disable (no network delay):
        await mcc_disable(dut, simulate_network_delay=False)
    """
    import random
    from cocotb.triggers import Timer, ClockCycles

    if simulate_network_delay:
        if delay_ms is None:
            delay_ms = random.uniform(1, 10)
        await Timer(int(delay_ms * 1_000_000), units="ns")

    cr0_current = int(dut.Control0.value)
    cr0_disabled = cr0_current & 0x7FFFFFFF  # Clear bit 31
    dut.Control0.value = cr0_disabled

    clk = dut.Clk if hasattr(dut, "Clk") else dut.clk
    await ClockCycles(clk, 2)

    dut._log.info(f"✓ MCC_READY cleared (CR0 = 0x{cr0_disabled:08X}) - module disabled")


# =============================================================================
# Module-Specific Helpers (can be expanded as needed)
# =============================================================================

# TODO: Add EMFI-Seq specific helpers when migrating those tests
# TODO: Add SimpleWaveGen helpers when migrating those tests

# Example placeholder for future expansion:
# async def verify_fsm_sequence(dut, expected_states):
#     """Verify FSM goes through expected state sequence"""
#     pass
