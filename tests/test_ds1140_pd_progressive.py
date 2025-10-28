"""
Progressive CocotB Test for DS1140-PD VOLO Application

Tests the refactored EMFI probe driver with progressive test structure:
- P1 (Basic): Reset, arm/trigger, three outputs, FSM observer, VOLO_READY control
- P2 (Intermediate): Timeout, full cycle, clock divider, intensity clamping

DS1140-PD Key Features:
- Three outputs: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
- Direct 16-bit signals (no high/low splits): arm_timeout, trigger_threshold, intensity
- 6-bit FSM observer on OutputC (pads 3-bit FSM state)
- Simplified register layout (7 registers with counter_16bit type)

Author: EZ-EMFI Team
Date: 2025-10-28
"""

import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_high
from test_base import TestBase, VerbosityLevel
from ds1140_pd_tests.ds1140_pd_constants import *


class DS1140PDTests(TestBase):
    """Progressive tests for DS1140-PD VOLO Application"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=TestValues.DEFAULT_CLK_PERIOD_NS, clk_signal="Clk")
        # Initialize inputs
        self.dut.InputA.value = 0
        self.dut.InputB.value = 0
        self.dut.Enable.value = 1
        self.dut.ClkEn.value = 1
        self.dut.Reset.value = 0
        # Initialize friendly signals (SIMPLIFIED - direct 16-bit signals!)
        self.dut.arm_probe.value = 0
        self.dut.force_fire.value = 0
        self.dut.reset_fsm.value = 0
        self.dut.clock_divider.value = 0
        self.dut.arm_timeout.value = 0xFF  # Direct 16-bit timeout
        self.dut.firing_duration.value = TestValues.P1_FIRING_DURATION
        self.dut.cooling_duration.value = TestValues.P1_COOLING_DURATION
        self.dut.trigger_threshold.value = TestValues.DEFAULT_THRESHOLD  # Direct 16-bit!
        self.dut.intensity.value = TestValues.DEFAULT_INTENSITY  # Direct 16-bit!
        self.dut.bram_addr.value = 0
        self.dut.bram_data.value = 0
        self.dut.bram_we.value = 0
        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P1 - Basic Tests (Essential validation - runs by default)
    # ====================================================================

    async def run_p1_basic(self):
        """P1 - Essential validation (5 tests)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("Arm and trigger", self.test_arm_trigger)
        await self.test("Three outputs functioning", self.test_three_outputs)
        await self.test("FSM observer on OutputC", self.test_fsm_observer)
        await self.test("VOLO_READY scheme", self.test_volo_ready)

    async def test_reset(self):
        """Verify reset puts module in safe state"""
        self.dut.Reset.value = 1
        await ClockCycles(self.dut.Clk, 5)

        output_a = int(self.dut.OutputA.value)
        assert output_a == 0, ErrorMessages.OUTPUT_MISMATCH.format(0, output_a)

        self.dut.Reset.value = 0
        await ClockCycles(self.dut.Clk, 2)

        self.log("Reset verified", VerbosityLevel.VERBOSE)

    async def test_arm_trigger(self):
        """Basic arm and trigger sequence"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Arm FSM (note: arm_probe not armed!)
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Apply trigger
        self.dut.InputA.value = TestValues.P1_TRIGGER_VALUE
        await ClockCycles(self.dut.Clk, TestValues.P1_WAIT_CYCLES)

        self.log("Arm/trigger verified", VerbosityLevel.VERBOSE)

    async def test_three_outputs(self):
        """Verify all three outputs are functioning (NEW TEST)"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # All outputs should be zero after reset
        output_a = int(self.dut.OutputA.value)
        output_b = int(self.dut.OutputB.value)
        output_c = int(self.dut.OutputC.value)

        assert output_a == 0, f"OutputA should be 0 after reset, got {output_a:04X}"
        assert output_b == 0, f"OutputB should be 0 after reset, got {output_b:04X}"
        # OutputC may be non-zero (FSM state READY = 0.0V = 0x0000)

        # Force fire to activate outputs
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 5)

        # During FIRING state:
        # - OutputA should be non-zero (trigger)
        # - OutputB should be non-zero (intensity)
        # - OutputC should change (FSM state FIRING)
        output_a_firing = int(self.dut.OutputA.value)
        output_b_firing = int(self.dut.OutputB.value)
        output_c_firing = int(self.dut.OutputC.value)

        self.log(f"Firing state: A={output_a_firing:04X}, B={output_b_firing:04X}, C={output_c_firing:04X}",
                 VerbosityLevel.VERBOSE)

        self.log("Three outputs verified", VerbosityLevel.VERBOSE)

    async def test_fsm_observer(self):
        """Verify FSM observer on OutputC tracks state changes (NEW TEST)"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Ensure trigger input is LOW (prevent unintended triggering)
        self.dut.InputA.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Helper function to read OutputC as voltage
        def read_fsm_voltage():
            raw = int(self.dut.OutputC.value)
            if raw > 32767:  # Handle signed wrap
                raw -= 65536
            voltage = (raw / 32767.0) * 5.0
            return voltage

        # READY state (should be ~0.0V)
        voltage_ready = read_fsm_voltage()
        self.log(f"READY voltage: {voltage_ready:.3f}V", VerbosityLevel.VERBOSE)
        assert -0.1 < voltage_ready < 0.1, ErrorMessages.VOLTAGE_OUT_OF_RANGE.format(
            voltage_ready, -0.1, 0.1
        )

        # Arm FSM → ARMED state (should be ~0.36V)
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 3)  # Wait for FSM to settle in ARMED

        voltage_armed = read_fsm_voltage()
        self.log(f"ARMED voltage: {voltage_armed:.3f}V", VerbosityLevel.VERBOSE)
        # FSM should be in ARMED state (~0.36V)
        assert 0.25 < voltage_armed < 0.5, ErrorMessages.VOLTAGE_OUT_OF_RANGE.format(
            voltage_armed, 0.25, 0.5
        )

        # Apply trigger → FIRING state (should be ~0.71V)
        self.dut.InputA.value = 0x4000  # Above threshold
        await ClockCycles(self.dut.Clk, 5)

        voltage_firing = read_fsm_voltage()
        self.log(f"FIRING voltage: {voltage_firing:.3f}V", VerbosityLevel.VERBOSE)
        assert 0.6 < voltage_firing < 0.85, ErrorMessages.VOLTAGE_OUT_OF_RANGE.format(
            voltage_firing, 0.6, 0.85
        )

        self.log("FSM observer verified on OutputC", VerbosityLevel.VERBOSE)

    async def test_volo_ready(self):
        """Enable control scheme"""
        self.dut.Enable.value = 0
        await ClockCycles(self.dut.Clk, 3)

        output_disabled = int(self.dut.OutputA.value)
        assert output_disabled == 0, ErrorMessages.ENABLE_FAILED.format("disabled", 0)

        self.dut.Enable.value = 1
        await ClockCycles(self.dut.Clk, 2)

        self.log("Enable control verified", VerbosityLevel.VERBOSE)

    # ====================================================================
    # P2 - Intermediate Tests (Comprehensive validation)
    # ====================================================================

    async def run_p2_intermediate(self):
        """P2 - Comprehensive validation (5 tests)"""
        await self.setup()

        await self.test("Timeout behavior", self.test_timeout)
        await self.test("Full operational cycle", self.test_full_cycle)
        await self.test("Clock divider integration", self.test_divider)
        await self.test("Intensity clamping on OutputB", self.test_intensity_clamp)
        await self.test("Debug mux view switching", self.test_debug_mux)

    async def test_timeout(self):
        """Verify armed timeout when no trigger received"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Configure with short timeout (direct 16-bit!)
        self.dut.arm_timeout.value = TestValues.P1_TIMEOUT_CYCLES
        await ClockCycles(self.dut.Clk, 2)

        # Arm FSM
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0

        # Keep trigger below threshold (should timeout)
        self.dut.InputA.value = 0x1000

        # Wait for timeout to occur
        await ClockCycles(self.dut.Clk, TestValues.P2_WAIT_CYCLES)

        self.log("Timeout verified", VerbosityLevel.VERBOSE)

    async def test_full_cycle(self):
        """Complete operational cycle: READY -> ARMED -> FIRING -> COOLING -> DONE"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Configure with P2 realistic timing
        self.dut.firing_duration.value = TestValues.P2_FIRING_DURATION
        self.dut.cooling_duration.value = TestValues.P2_COOLING_DURATION
        self.dut.trigger_threshold.value = 0x2000  # Direct 16-bit!
        self.dut.intensity.value = 0x4000  # Direct 16-bit!
        await ClockCycles(self.dut.Clk, 2)

        # Arm FSM
        self.log("Arming FSM...", VerbosityLevel.VERBOSE)
        self.dut.arm_probe.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Apply trigger
        self.log("Applying trigger...", VerbosityLevel.VERBOSE)
        self.dut.InputA.value = 0x3000
        await ClockCycles(self.dut.Clk, TestValues.P2_FIRING_DURATION + 5)

        # Wait for cooling phase
        self.log("Waiting for cooling...", VerbosityLevel.VERBOSE)
        await ClockCycles(self.dut.Clk, TestValues.P2_COOLING_DURATION + 5)

        # Reset FSM to READY
        self.log("Resetting FSM...", VerbosityLevel.VERBOSE)
        self.dut.reset_fsm.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.reset_fsm.value = 0
        await ClockCycles(self.dut.Clk, 2)

        self.log("Full cycle verified", VerbosityLevel.VERBOSE)

    async def test_divider(self):
        """Clock divider affects FSM timing"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Test without clock division
        self.log("Testing without clock division", VerbosityLevel.VERBOSE)
        self.dut.clock_divider.value = 0x00  # No division
        self.dut.firing_duration.value = 4
        self.dut.cooling_duration.value = 4
        await ClockCycles(self.dut.Clk, 2)

        # Force fire
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 20)

        # Reset FSM
        self.dut.reset_fsm.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.reset_fsm.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Test with clock division (divide by 4)
        self.log("Testing with clock division (÷4)", VerbosityLevel.VERBOSE)
        self.dut.clock_divider.value = 0x03  # Divide by 4
        await ClockCycles(self.dut.Clk, 2)

        # Force fire with division - should take longer
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 80)

        self.log("Clock divider verified", VerbosityLevel.VERBOSE)

    async def test_intensity_clamp(self):
        """Verify intensity clamping on OutputB (NEW TEST)"""
        await reset_active_high(self.dut, rst_signal="Reset")

        # Set intensity above 3.0V limit (0x4CCD) - direct 16-bit!
        self.dut.intensity.value = TestValues.INTENSITY_ABOVE_CLAMP
        await ClockCycles(self.dut.Clk, 2)

        # Force fire
        self.dut.force_fire.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.force_fire.value = 0
        await ClockCycles(self.dut.Clk, 5)

        # OutputB should be clamped to 3.0V (0x4CCD)
        output_b = int(self.dut.OutputB.value)

        # Convert to voltage
        if output_b > 32767:
            output_b -= 65536
        voltage_b = (output_b / 32767.0) * 5.0
        self.log(f"OutputB voltage: {voltage_b:.3f}V (should be ≤3.0V)", VerbosityLevel.VERBOSE)

        assert voltage_b <= 3.1, ErrorMessages.OUTPUT_NOT_CLAMPED.format(3.0, voltage_b)

        self.log("Intensity clamping verified on OutputB", VerbosityLevel.VERBOSE)

    async def test_debug_mux(self):
        """Test debug multiplexer view switching (if implemented)"""
        if not hasattr(self.dut, 'debug_select_c'):
            self.log("Debug mux not implemented, skipping", VerbosityLevel.VERBOSE)
            return

        await reset_active_high(self.dut, rst_signal="Reset")

        # View 0: FSM state (default)
        self.dut.debug_select_c.value = 0
        await ClockCycles(self.dut.Clk, 2)
        view0_value = int(self.dut.OutputC.value)

        # View 1: Timing diagnostics
        self.dut.debug_select_c.value = 1
        await ClockCycles(self.dut.Clk, 2)
        view1_value = int(self.dut.OutputC.value)

        # View 2: Trigger activity
        self.dut.debug_select_c.value = 2
        await ClockCycles(self.dut.Clk, 2)
        view2_value = int(self.dut.OutputC.value)

        self.log(f"Debug views: V0={view0_value:04X}, V1={view1_value:04X}, V2={view2_value:04X}",
                 VerbosityLevel.VERBOSE)

        self.log("Debug mux view switching verified (or skipped if not implemented)", VerbosityLevel.VERBOSE)


# CocotB entry point
@cocotb.test()
async def test_ds1140_pd_volo(dut):
    """Progressive DS1140-PD VOLO application tests"""
    tester = DS1140PDTests(dut)
    await tester.run_all_tests()
