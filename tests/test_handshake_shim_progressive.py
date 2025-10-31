"""
CocotB Progressive Tests: Shim Layer Handshaking Protocol

Validates the ready_for_updates handshaking protocol in the shim layer.
Tests that the shim correctly gates register updates based on the
ready_for_updates signal from the main application.

Reference:
- docs/CocoTB-TestingNetworkRegs.md (lines 61-397)
- HandShakeProtocol.md v2.0
- docs/BasicNetworkRegSafety_plan.md

Author: Volo Team
Date: 2025-01-31
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock
import sys
from pathlib import Path

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from handshake_tests.handshake_constants import *


class HandshakeShimTests(TestBase):
    """Progressive tests for shim layer handshaking"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        # Start clock
        cocotb.start_soon(Clock(
            self.dut.Clk,
            TestTiming.CLOCK_PERIOD_NS,
            units="ns"
        ).start())

        # Reset
        self.dut.Reset.value = 1
        self.dut.ready_for_updates.value = 0
        self.dut.app_reg_6.value = 0
        self.dut.app_reg_7.value = 0
        await ClockCycles(self.dut.Clk, TestTiming.RESET_CYCLES)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ========================================================================
    # P1 Tests - Essential Functionality
    # ========================================================================

    async def run_p1_basic(self):
        """P1: Essential shim handshaking tests"""
        await self.setup()

        await self.test(
            "P1.1: Shim gates updates when ready='0'",
            self.test_gates_when_not_ready
        )

        await self.test(
            "P1.2: Shim applies updates when ready='1'",
            self.test_updates_when_ready
        )

        await self.test(
            "P1.3: Reset loads default values",
            self.test_reset_defaults
        )

    async def test_gates_when_not_ready(self):
        """Verify shim holds values when ready_for_updates='0'"""

        # Gate is CLOSED (ready='0')
        self.dut.ready_for_updates.value = 0
        await ClockCycles(self.dut.Clk, TestTiming.SETTLE_CYCLES)

        # Record initial value (should be default from reset)
        initial_intensity = int(self.dut.intensity.value)
        self.log(f"Initial intensity: {initial_intensity:#06x}", VerbosityLevel.VERBOSE)

        # Write new value to CR6 (app_reg_6)
        new_cr6 = TestValues.pack_cr6(TestValues.INTENSITY_NEW_1)
        self.dut.app_reg_6.value = new_cr6
        self.log(f"Writing CR6={new_cr6:#010x}", VerbosityLevel.VERBOSE)

        # Wait and verify NO change
        await ClockCycles(self.dut.Clk, TestTiming.P1_WAIT_CYCLES)

        current_intensity = int(self.dut.intensity.value)
        assert current_intensity == initial_intensity, \
            ErrorMessages.UPDATE_WHEN_NOT_READY.format(
                initial_intensity, current_intensity, TestTiming.P1_WAIT_CYCLES
            )

        self.log("✓ Gate held values while ready='0'", VerbosityLevel.NORMAL)

    async def test_updates_when_ready(self):
        """Verify shim latches values when ready_for_updates='1'"""

        # Write value to CR6
        new_intensity = TestValues.INTENSITY_NEW_1
        self.dut.app_reg_6.value = TestValues.pack_cr6(new_intensity)
        self.dut.ready_for_updates.value = 0  # Gate closed initially
        await ClockCycles(self.dut.Clk, 2)

        # Open gate and wait for update to register
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 1)  # Wait for process to latch value
        await RisingEdge(self.dut.Clk)      # Wait for another edge to ensure stable

        # Verify update occurred
        current_intensity = int(self.dut.intensity.value)
        assert current_intensity == new_intensity, \
            ErrorMessages.NO_UPDATE_WHEN_READY.format(new_intensity, current_intensity)

        self.log(f"✓ Shim updated to {current_intensity:#06x} when ready='1'",
                 VerbosityLevel.NORMAL)

    async def test_reset_defaults(self):
        """Verify reset loads YAML-defined defaults"""

        # Write non-default values
        self.dut.app_reg_6.value = 0xFFFF_FFFF
        self.dut.app_reg_7.value = 0xFFFF_FFFF
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Reset
        self.dut.Reset.value = 1
        await RisingEdge(self.dut.Clk)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        # Verify defaults loaded (from HandShakeProtocol.md example)
        intensity_default = int(self.dut.intensity.value)
        threshold_default = int(self.dut.threshold.value)

        assert intensity_default == TestValues.INTENSITY_DEFAULT, \
            ErrorMessages.DEFAULT_NOT_LOADED.format(
                TestValues.INTENSITY_DEFAULT, intensity_default
            )

        assert threshold_default == TestValues.THRESHOLD_DEFAULT, \
            ErrorMessages.DEFAULT_NOT_LOADED.format(
                TestValues.THRESHOLD_DEFAULT, threshold_default
            )

        self.log(
            f"✓ Defaults loaded: intensity={intensity_default:#06x}, "
            f"threshold={threshold_default:#06x}",
            VerbosityLevel.NORMAL
        )


@cocotb.test()
async def test_handshake_shim(dut):
    """CocotB entry point for shim handshaking tests"""
    tester = HandshakeShimTests(dut)
    await tester.run_all_tests()
