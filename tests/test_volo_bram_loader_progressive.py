"""
Progressive CocotB Testbench for volo_bram_loader with FSM Observer

Tests both BRAM loading functionality AND FSM observer integration.
Uses TestBase framework for progressive testing (P1/P2).

Test level controlled by TEST_LEVEL environment variable:
- P1_BASIC (default): Essential tests, <20 lines output
- P2_INTERMEDIATE: Full test suite with edge cases

Usage:
    # P1 only (minimal output)
    uv run python tests/run.py volo_bram_loader

    # P2 (all tests)
    TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py volo_bram_loader

Author: EZ-EMFI Team
Date: 2025-01-28
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from conftest import setup_clock
from test_base import TestBase, TestLevel, VerbosityLevel
from volo_bram_loader_tests.volo_bram_loader_constants import *


class VoloBramLoaderTests(TestBase):
    """Progressive tests for volo_bram_loader module with FSM observer"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut)

        # Initialize control registers
        self.dut.Control10.value = 0
        self.dut.Control11.value = 0
        self.dut.Control12.value = 0
        self.dut.Control13.value = 0
        self.dut.Control14.value = 0

        # Reset
        self.dut.Reset.value = 1
        await ClockCycles(self.dut.Clk, Timing.RESET_CYCLES)
        self.dut.Reset.value = 0
        await ClockCycles(self.dut.Clk, Timing.SETUP_CYCLES)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def get_observer_voltage(self) -> int:
        """Read FSM observer voltage output (signed)"""
        raw = int(self.dut.voltage_debug_out.value)
        # Convert to signed 16-bit
        if raw > 32767:
            return raw - 65536
        return raw

    def check_observer_voltage(self, expected: int, tolerance: int = ObserverVoltages.TOLERANCE):
        """Assert observer voltage matches expected value"""
        actual = self.get_observer_voltage()
        assert voltages_match(expected, actual, tolerance), \
            ErrorMessages.OBSERVER_VOLTAGE_MISMATCH.format(expected, tolerance, actual)

    async def write_word(self, address: int, data: int):
        """
        Write a single word to BRAM using the control register protocol.

        Args:
            address: BRAM address (12-bit)
            data: Data word (32-bit)
        """
        # Set address and data
        self.dut.Control11.value = address & ControlBits.ADDR_MASK
        self.dut.Control12.value = data
        await ClockCycles(self.dut.Clk, 1)

        # Assert write strobe
        self.dut.Control13.value = ControlBits.WRITE_STROBE_MASK
        await ClockCycles(self.dut.Clk, Timing.STROBE_HOLD_CYCLES)

        # Deassert write strobe
        self.dut.Control13.value = 0
        await ClockCycles(self.dut.Clk, Timing.POST_WRITE_CYCLES)

    async def start_loading(self, word_count: int):
        """
        Start BRAM loading sequence.

        Args:
            word_count: Number of words to load (16-bit)
        """
        control10_val = (word_count << ControlBits.WORD_COUNT_SHIFT) | ControlBits.START_MASK
        self.dut.Control10.value = control10_val
        await ClockCycles(self.dut.Clk, Timing.STATE_TRANSITION_CYCLES)

    # ========================================================================
    # P1 - Basic Tests (REQUIRED, runs by default)
    # ========================================================================

    async def run_p1_basic(self):
        """P1 - Basic tests (minimal output, essential validation)"""
        await self.setup()

        await self.test("Reset behavior", self.test_reset)
        await self.test("FSM observer in IDLE", self.test_observer_idle)
        await self.test("Single word write", self.test_single_word_write)

    async def test_reset(self):
        """Test reset puts module in known state"""
        await self.setup()

        # Check done flag is clear
        done = int(self.dut.done.value)
        assert done == 0, ErrorMessages.RESET_DONE.format(done)

        # Check BRAM write enable is clear
        bram_we = int(self.dut.bram_we.value)
        assert bram_we == 0, ErrorMessages.RESET_BRAM_WE.format(bram_we)

        self.log("Reset: done=0, bram_we=0", VerbosityLevel.VERBOSE)

    async def test_observer_idle(self):
        """Test FSM observer shows IDLE state voltage"""
        await self.setup()

        # Module should be in IDLE state
        self.check_observer_voltage(ObserverVoltages.IDLE)

        self.log(f"Observer IDLE: {self.get_observer_voltage()} digital", VerbosityLevel.VERBOSE)

    async def test_single_word_write(self):
        """Test basic single word BRAM write"""
        await self.setup()

        # Start loading 1 word
        await self.start_loading(1)

        # Check observer shows LOADING state
        self.check_observer_voltage(ObserverVoltages.LOADING)
        self.log(f"Observer LOADING: {self.get_observer_voltage()}", VerbosityLevel.VERBOSE)

        # Write word to address 0
        test_addr = 0x000
        test_data = TestPatterns.PATTERN_DEADBEEF

        await self.write_word(test_addr, test_data)

        # Wait for FSM to transition to DONE
        await ClockCycles(self.dut.Clk, Timing.STATE_TRANSITION_CYCLES)

        # Check done flag
        done = int(self.dut.done.value)
        assert done == 1, ErrorMessages.DONE_NOT_ASSERTED.format(1)

        # Check observer shows DONE state
        self.check_observer_voltage(ObserverVoltages.DONE)
        self.log(f"Observer DONE: {self.get_observer_voltage()}", VerbosityLevel.VERBOSE)

    # ========================================================================
    # P2 - Intermediate Tests (full functionality)
    # ========================================================================

    async def run_p2_intermediate(self):
        """P2 - Intermediate tests (full test coverage)"""
        await self.setup()

        await self.test("Multiple word writes", self.test_multiple_words)
        await self.test("BRAM interface signals", self.test_bram_interface)
        await self.test("Observer voltage transitions", self.test_observer_transitions)
        await self.test("Edge case: zero words", self.test_zero_words)
        await self.test("Edge case: max address", self.test_max_address)

    async def test_multiple_words(self):
        """Test writing multiple words sequentially"""
        await self.setup()

        word_count = 4
        test_pattern = TestPatterns.sequential(start=0x1000, count=word_count)

        await self.start_loading(word_count)

        for i, data in enumerate(test_pattern):
            await self.write_word(i, data)
            self.log(f"Wrote word {i}: 0x{data:08X}", VerbosityLevel.VERBOSE)

        # Wait for DONE state
        await ClockCycles(self.dut.Clk, Timing.STATE_TRANSITION_CYCLES)

        # Verify completion
        done = int(self.dut.done.value)
        assert done == 1, ErrorMessages.DONE_NOT_ASSERTED.format(word_count)

        self.log(f"Completed {word_count} word writes", VerbosityLevel.VERBOSE)

    async def test_bram_interface(self):
        """Test BRAM interface signals during write"""
        await self.setup()

        await self.start_loading(1)

        test_addr = 0x123
        test_data = 0xABCD1234

        # Set address and data
        self.dut.Control11.value = test_addr
        self.dut.Control12.value = test_data
        await ClockCycles(self.dut.Clk, 1)

        # Assert write strobe
        self.dut.Control13.value = ControlBits.WRITE_STROBE_MASK
        await ClockCycles(self.dut.Clk, 1)

        # Check BRAM signals on next cycle
        bram_addr = int(self.dut.bram_addr.value)
        bram_data = int(self.dut.bram_data.value)
        bram_we = int(self.dut.bram_we.value)

        assert bram_addr == test_addr, ErrorMessages.BRAM_ADDR_MISMATCH.format(test_addr, bram_addr)
        assert bram_data == test_data, ErrorMessages.BRAM_DATA_MISMATCH.format(test_data, bram_data)
        assert bram_we == 1, ErrorMessages.BRAM_WE_NOT_PULSED.format(bram_we)

        self.log(f"BRAM signals: addr=0x{bram_addr:03X}, data=0x{bram_data:08X}, we={bram_we}",
                 VerbosityLevel.VERBOSE)

        # Deassert strobe
        self.dut.Control13.value = 0
        await ClockCycles(self.dut.Clk, 1)

        # BRAM WE should be deasserted
        bram_we = int(self.dut.bram_we.value)
        assert bram_we == 0, ErrorMessages.BRAM_WE_STUCK_HIGH

    async def test_observer_transitions(self):
        """Test FSM observer voltage changes through state transitions"""
        await self.setup()

        # Initial: IDLE
        voltage_idle = self.get_observer_voltage()
        self.check_observer_voltage(ObserverVoltages.IDLE)
        self.log(f"IDLE voltage: {voltage_idle}", VerbosityLevel.VERBOSE)

        # Transition to LOADING
        await self.start_loading(1)
        voltage_loading = self.get_observer_voltage()
        self.check_observer_voltage(ObserverVoltages.LOADING)
        self.log(f"LOADING voltage: {voltage_loading}", VerbosityLevel.VERBOSE)

        # Voltage should have changed
        assert voltage_loading != voltage_idle, ErrorMessages.VOLTAGE_NO_CHANGE

        # Write word
        await self.write_word(0, 0x11223344)

        # Transition to DONE
        await ClockCycles(self.dut.Clk, Timing.STATE_TRANSITION_CYCLES)
        voltage_done = self.get_observer_voltage()
        self.check_observer_voltage(ObserverVoltages.DONE)
        self.log(f"DONE voltage: {voltage_done}", VerbosityLevel.VERBOSE)

        # Voltage should have changed again
        assert voltage_done != voltage_loading, ErrorMessages.VOLTAGE_NO_CHANGE

        self.log("All state transitions showed distinct voltages", VerbosityLevel.VERBOSE)

    async def test_zero_words(self):
        """Test edge case: start loading with word count = 0"""
        await self.setup()

        # Start with word count = 0 (should immediately transition to DONE)
        await self.start_loading(0)

        # Wait for state transition
        await ClockCycles(self.dut.Clk, Timing.STATE_TRANSITION_CYCLES * 2)

        # Should be in DONE state
        done = int(self.dut.done.value)
        assert done == 1, ErrorMessages.DONE_NOT_ASSERTED.format(0)

        self.check_observer_voltage(ObserverVoltages.DONE)
        self.log("Zero-word loading completed correctly", VerbosityLevel.VERBOSE)

    async def test_max_address(self):
        """Test edge case: write to maximum BRAM address"""
        await self.setup()

        await self.start_loading(1)

        # Maximum 12-bit address (4095)
        max_addr = 0xFFF
        test_data = 0x55555555

        await self.write_word(max_addr, test_data)

        # Check address was correctly passed to BRAM
        bram_addr = int(self.dut.bram_addr.value)
        assert bram_addr == max_addr, ErrorMessages.BRAM_ADDR_MISMATCH.format(max_addr, bram_addr)

        self.log(f"Max address 0x{max_addr:03X} handled correctly", VerbosityLevel.VERBOSE)


# ============================================================================
# CocotB Test Entry Point
# ============================================================================

@cocotb.test()
async def volo_bram_loader_progressive_test(dut):
    """Main test entry point - runs all progressive tests"""
    test_runner = VoloBramLoaderTests(dut)
    await test_runner.run_all_tests()
