"""
P2 - Intermediate Tests for volo_clk_divider

Additional tests covering edge cases and special modes.
Runs after P1 tests when TEST_LEVEL >= P2_INTERMEDIATE.

Test Coverage:
1. Divide by 1 (bypass mode)
2. Divide by 10 (realistic division)
3. Maximum division (div_sel=255)
4. Status register counter visibility

Author: EZ-EMFI Team
Date: 2025-01-27
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from conftest import setup_clock, reset_active_low, count_pulses, assert_pulse_count
from test_base import TestBase, TestLevel, VerbosityLevel
from volo_clk_divider_tests.volo_clk_divider_constants import *


class VoloClkDividerIntermediateTests(TestBase):
    """P2 - Intermediate tests for volo_clk_divider module"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut)
        self.dut.enable.value = 1
        self.dut.div_sel.value = 0

    async def run_p2_intermediate(self):
        """Run all P2 intermediate tests"""
        await self.setup()

        # Test 1: Divide by 1 (bypass mode)
        await self.test("Divide by 1 (bypass)", self.test_divide_by_1)

        # Test 2: Divide by 10
        await self.test("Divide by 10", self.test_divide_by_10)

        # Test 3: Maximum division
        await self.test("Maximum division (255)", self.test_max_division)

        # Test 4: Status register
        await self.test("Status register", self.test_status_register)

    async def test_divide_by_1(self):
        """Test bypass mode where clk_en is always high"""
        await reset_active_low(self.dut)

        # Set divide by 1 (div_sel=0 is bypass mode)
        self.dut.div_sel.value = 0
        self.dut.enable.value = 1
        await reset_active_low(self.dut)

        # clk_en should be continuously high
        for i in range(10):
            await RisingEdge(self.dut.clk)
            clk_en = int(self.dut.clk_en.value)
            assert clk_en == 1, ErrorMessages.DIV_BY_1_CLK_EN.format(clk_en)

        self.log("Bypass mode: clk_en always high", VerbosityLevel.VERBOSE)

    async def test_divide_by_10(self):
        """Test divide by 10 operation"""
        await reset_active_low(self.dut)

        # Set divide by 10
        self.dut.div_sel.value = 10
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 2)

        # Use assert_pulse_count helper (combines count + assert)
        await assert_pulse_count(self.dut.clk_en, self.dut.clk, cycles=100, expected=10)

        self.log("Divide by 10: 10 pulses in 100 cycles", VerbosityLevel.VERBOSE)

    async def test_max_division(self):
        """Test maximum division (div_sel=255, divides by 256)"""
        await reset_active_low(self.dut)

        # Set maximum division
        self.dut.div_sel.value = 255
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        # Count clk_en pulses over 512 clock cycles (2 full periods)
        clk_en_count = 0
        for i in range(512):
            await RisingEdge(self.dut.clk)
            if int(self.dut.clk_en.value) == 1:
                clk_en_count += 1

        # Should see 2 pulses (every 256 cycles)
        expected_pulses = 2
        assert clk_en_count == expected_pulses, ErrorMessages.PULSE_COUNT.format(
            expected_pulses, clk_en_count
        )

        self.log(f"Max division: {clk_en_count} pulses in 512 cycles", VerbosityLevel.VERBOSE)

    async def test_status_register(self):
        """Test that stat_reg shows current counter value"""
        await reset_active_low(self.dut)

        # Set divide by 5
        self.dut.div_sel.value = 5
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        # Monitor counter incrementing and wrapping
        prev_counter = 0
        wrap_detected = False

        for i in range(20):
            await RisingEdge(self.dut.clk)
            current_counter = int(self.dut.stat_reg.value)

            # Check if counter wrapped (went from 4 to 0 for div_sel=5)
            if current_counter < prev_counter:
                wrap_detected = True
                self.log(
                    f"Counter wrapped: {prev_counter} → {current_counter}",
                    VerbosityLevel.VERBOSE
                )

            prev_counter = current_counter

        assert wrap_detected, "Counter should wrap during test"
        self.log("Status register correctly shows counter value", VerbosityLevel.VERBOSE)


# CocotB test entry point
@cocotb.test()
async def test_volo_clk_divider_p2(dut):
    """P2 - Intermediate volo_clk_divider tests"""
    tester = VoloClkDividerIntermediateTests(dut)
    await tester.run_all_tests()
