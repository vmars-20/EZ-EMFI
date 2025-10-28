"""
Progressive CocotB Test for volo_voltage_pkg

Validates voltage package constants and conversion functions.

Author: EZ-EMFI Team
Date: 2025-01-27
"""

import cocotb
from cocotb.triggers import Timer
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from volo_voltage_pkg_tests.volo_voltage_pkg_constants import *


class VoloVoltagePkgTests(TestBase):
    """Progressive tests for volo_voltage_pkg"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup"""
        await Timer(1, units='ns')

    # ========================================================================
    # P1 - Basic Tests
    # ========================================================================

    async def run_p1_basic(self):
        """P1 - Basic validation of constants and conversions"""
        await self.setup()

        await self.test("Voltage constants", self.test_constants)
        await self.test("Conversion sanity", self.test_conversions)

    async def test_constants(self):
        """Verify voltage package constants"""
        constants_map = {
            "DIGITAL_1V": (self.dut.const_digital_1v, ExpectedConstants.DIGITAL_1V),
            "DIGITAL_2V5": (self.dut.const_digital_2v5, ExpectedConstants.DIGITAL_2V5),
            "DIGITAL_3V3": (self.dut.const_digital_3v3, ExpectedConstants.DIGITAL_3V3),
            "DIGITAL_5V": (self.dut.const_digital_5v, ExpectedConstants.DIGITAL_5V),
            "DIGITAL_NEG_1V": (self.dut.const_digital_neg_1v, ExpectedConstants.DIGITAL_NEG_1V),
            "DIGITAL_NEG_2V5": (self.dut.const_digital_neg_2v5, ExpectedConstants.DIGITAL_NEG_2V5),
            "DIGITAL_ZERO": (self.dut.const_digital_zero, ExpectedConstants.DIGITAL_ZERO),
        }

        for name, (signal, expected) in constants_map.items():
            actual = int(signal.value.signed_integer)
            assert actual == expected, ErrorMessages.CONSTANT_MISMATCH.format(
                name, expected, actual
            )
            self.log(f"{name}: {actual}", VerbosityLevel.VERBOSE)

    async def test_conversions(self):
        """Basic conversion sanity checks"""
        for label, input_val, expected_val in TestConversions.CASES:
            self.dut.test_digital_passthrough.value = input_val
            await Timer(1, units='ns')
            actual = int(self.dut.test_digital_result.value.signed_integer)

            assert actual == expected_val, ErrorMessages.CONVERSION_FAILED.format(
                label, input_val, actual, expected_val
            )
            self.log(f"{label}: {input_val} → {actual}", VerbosityLevel.VERBOSE)


@cocotb.test()
async def test_volo_voltage_pkg(dut):
    """Progressive volo_voltage_pkg tests"""
    tester = VoloVoltagePkgTests(dut)
    await tester.run_all_tests()
