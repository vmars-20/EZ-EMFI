"""
P1 - Basic Tests for volo_clk_divider

Minimal, fast tests with reduced verbosity for LLM-friendly output.
These tests verify core functionality with small values and minimal logging.

Test Coverage:
1. Reset behavior
2. Basic divide by 2
3. Enable control

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


class VoloClkDividerBasicTests(TestBase):
    """P1 - Basic tests for volo_clk_divider module"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut)
        self.dut.enable.value = 1
        self.dut.div_sel.value = 0

    async def run_p1_basic(self):
        """Run all P1 basic tests"""
        await self.setup()

        # Test 1: Reset behavior
        await self.test("Reset behavior", self.test_reset)

        # Test 2: Divide by 2
        await self.test("Divide by 2", self.test_divide_by_2)

        # Test 3: Enable control
        await self.test("Enable control", self.test_enable)

    async def test_reset(self):
        """Test reset puts module in known state"""
        await reset_active_low(self.dut)

        # Check reset state
        clk_en = int(self.dut.clk_en.value)
        stat_reg = int(self.dut.stat_reg.value)

        assert clk_en == 0, ErrorMessages.RESET_CLK_EN.format(clk_en)
        assert stat_reg == 0, ErrorMessages.RESET_STATUS.format(stat_reg)

        self.log("Reset: clk_en=0, stat_reg=0", VerbosityLevel.VERBOSE)

    async def test_divide_by_2(self):
        """Test basic divide by 2 operation"""
        await reset_active_low(self.dut)

        # Set divide by 2
        self.dut.div_sel.value = 2
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 2)  # Wait for it to load

        # Count pulses - should get 10 pulses in 20 cycles
        clk_en_count = await count_pulses(self.dut.clk_en, self.dut.clk, 20)

        expected_pulses = 10
        assert clk_en_count == expected_pulses, ErrorMessages.PULSE_COUNT.format(
            expected_pulses, clk_en_count
        )

        self.log(f"Divide by 2: {clk_en_count} pulses in 20 cycles", VerbosityLevel.VERBOSE)

    async def test_enable(self):
        """Test counter freezes when disabled"""
        await reset_active_low(self.dut)

        # Set divide by 5
        self.dut.div_sel.value = 5
        self.dut.enable.value = 1
        await ClockCycles(self.dut.clk, 1)

        # Let it count a bit
        await ClockCycles(self.dut.clk, 3)
        counter_before = int(self.dut.stat_reg.value)

        # Disable (freeze)
        self.dut.enable.value = 0
        await ClockCycles(self.dut.clk, 2)

        # clk_en should go low
        clk_en = int(self.dut.clk_en.value)
        assert clk_en == 0, ErrorMessages.ENABLE_IGNORED.format(clk_en)

        # Counter should hold for several cycles
        for i in range(5):
            await ClockCycles(self.dut.clk, 1)
            counter_check = int(self.dut.stat_reg.value)
            assert counter_check == counter_before, ErrorMessages.COUNTER_FROZEN.format(
                counter_before, counter_check
            )

        self.log(f"Counter frozen at {counter_before} while disabled", VerbosityLevel.VERBOSE)


# CocotB test entry point
@cocotb.test()
async def test_volo_clk_divider_p1(dut):
    """P1 - Basic volo_clk_divider tests"""
    tester = VoloClkDividerBasicTests(dut)
    await tester.run_all_tests()
