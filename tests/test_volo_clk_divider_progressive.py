"""
Progressive CocotB Testbench for volo_clk_divider

Uses TestBase framework for progressive testing (P1/P2/P3/P4).
Test level controlled by TEST_LEVEL environment variable:
- P1_BASIC (default): Minimal tests, <20 lines output
- P2_INTERMEDIATE: Full test suite

Usage:
    # P1 only (minimal output)
    uv run python tests/run.py volo_clk_divider

    # P2 (all tests)
    TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_clk_divider

Author: EZ-EMFI Team (adapted from volo-vhdl progressive testing standard)
Date: 2025-01-27
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock, reset_active_low, count_pulses, assert_pulse_count
from test_base import TestBase, TestLevel, VerbosityLevel
from volo_clk_divider_tests.volo_clk_divider_constants import *


class VoloClkDividerTests(TestBase):
    """Progressive tests for volo_clk_divider module"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut)
        self.dut.enable.value = 1
        self.dut.div_sel.value = 0

    # ========================================================================
    # P1 - Basic Tests (REQUIRED, runs by default)
    # ========================================================================

    async def run_p1_basic(self):
        """P1 - Basic tests (minimal output, essential validation)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("Divide by 2", self.test_divide_by_2)
        await self.test("Enable control", self.test_enable)

    async def test_reset(self):
        """Test reset puts module in known state"""
        await reset_active_low(self.dut)

        clk_en = int(self.dut.clk_en.value)
        stat_reg = int(self.dut.stat_reg.value)

        assert clk_en == 0, ErrorMessages.RESET_CLK_EN.format(clk_en)
        assert stat_reg == 0, ErrorMessages.RESET_STATUS.format(stat_reg)

        self.log("Reset: clk_en=0, stat_reg=0", VerbosityLevel.VERBOSE)

    async def test_divide_by_2(self):
        """Test basic divide by 2 operation"""
        await reset_active_low(self.dut)

        self.dut.div_sel.value = 2
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 2)

        clk_en_count = await count_pulses(self.dut.clk_en, self.dut.clk, 20)

        expected_pulses = 10
        assert clk_en_count == expected_pulses, ErrorMessages.PULSE_COUNT.format(
            expected_pulses, clk_en_count
        )

        self.log(f"Divide by 2: {clk_en_count} pulses", VerbosityLevel.VERBOSE)

    async def test_enable(self):
        """Test counter freezes when disabled"""
        await reset_active_low(self.dut)

        # Use larger div_sel to avoid wrap-around during test
        self.dut.div_sel.value = 100
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        # Let it count a bit
        await ClockCycles(self.dut.clk, 3)

        # Disable (freeze)
        self.dut.enable.value = 0
        await ClockCycles(self.dut.clk, 2)  # Wait for disable to take effect

        # clk_en should go low
        clk_en = int(self.dut.clk_en.value)
        assert clk_en == 0, ErrorMessages.ENABLE_IGNORED.format(clk_en)

        # Read counter value after disable has taken effect
        counter_frozen = int(self.dut.stat_reg.value)

        # Counter should hold for several cycles
        for i in range(5):
            await ClockCycles(self.dut.clk, 1)
            counter_check = int(self.dut.stat_reg.value)
            assert counter_check == counter_frozen, ErrorMessages.COUNTER_FROZEN.format(
                counter_frozen, counter_check
            )

        self.log(f"Counter frozen at {counter_frozen}", VerbosityLevel.VERBOSE)

    # ========================================================================
    # P2 - Intermediate Tests (runs when TEST_LEVEL >= P2_INTERMEDIATE)
    # ========================================================================

    async def run_p2_intermediate(self):
        """P2 - Intermediate tests (edge cases and special modes)"""
        await self.setup()

        await self.test("Divide by 1 (bypass)", self.test_divide_by_1)
        await self.test("Divide by 10", self.test_divide_by_10)
        await self.test("Maximum division (255)", self.test_max_division)
        await self.test("Status register", self.test_status_register)

    async def test_divide_by_1(self):
        """Test bypass mode where clk_en is always high"""
        await reset_active_low(self.dut)

        self.dut.div_sel.value = 0
        self.dut.enable.value = 1
        await reset_active_low(self.dut)

        for i in range(10):
            await RisingEdge(self.dut.clk)
            clk_en = int(self.dut.clk_en.value)
            assert clk_en == 1, ErrorMessages.DIV_BY_1_CLK_EN.format(clk_en)

        self.log("Bypass mode verified", VerbosityLevel.VERBOSE)

    async def test_divide_by_10(self):
        """Test divide by 10 operation"""
        await reset_active_low(self.dut)

        self.dut.div_sel.value = 10
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 2)

        await assert_pulse_count(self.dut.clk_en, self.dut.clk, cycles=100, expected=10)

        self.log("Divide by 10 verified", VerbosityLevel.VERBOSE)

    async def test_max_division(self):
        """Test maximum division (div_sel=255, divides by 256)"""
        await reset_active_low(self.dut)

        self.dut.div_sel.value = 255
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        clk_en_count = 0
        for i in range(512):
            await RisingEdge(self.dut.clk)
            if int(self.dut.clk_en.value) == 1:
                clk_en_count += 1

        expected_pulses = 2
        assert clk_en_count == expected_pulses, ErrorMessages.PULSE_COUNT.format(
            expected_pulses, clk_en_count
        )

        self.log(f"Max division: {clk_en_count} pulses in 512 cycles", VerbosityLevel.VERBOSE)

    async def test_status_register(self):
        """Test that stat_reg shows current counter value"""
        await reset_active_low(self.dut)

        self.dut.div_sel.value = 5
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        prev_counter = 0
        wrap_detected = False

        for i in range(20):
            await RisingEdge(self.dut.clk)
            current_counter = int(self.dut.stat_reg.value)

            if current_counter < prev_counter:
                wrap_detected = True
                self.log(
                    f"Counter wrapped: {prev_counter} → {current_counter}",
                    VerbosityLevel.VERBOSE
                )

            prev_counter = current_counter

        assert wrap_detected, "Counter should wrap during test"
        self.log("Status register verified", VerbosityLevel.VERBOSE)


# CocotB test entry point
@cocotb.test()
async def test_volo_clk_divider(dut):
    """
    Progressive volo_clk_divider tests.

    Automatically runs P1 (basic) by default, or P1+P2 when TEST_LEVEL=P2_INTERMEDIATE.
    """
    tester = VoloClkDividerTests(dut)
    await tester.run_all_tests()
