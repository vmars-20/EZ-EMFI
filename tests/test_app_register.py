"""
Unit tests for AppRegister and RegisterType (counter_16bit support).

Tests the new counter_16bit register type added for DS1140-PD project.
Verifies enum, validation, bit width, and max value functionality.
"""

import pytest
from models.volo.app_register import AppRegister, RegisterType


class TestCounter16BitEnum:
    """Test counter_16bit enum value exists."""

    def test_counter_16bit_enum_exists(self):
        """Verify counter_16bit enum value exists."""
        assert RegisterType.COUNTER_16BIT == "counter_16bit"

    def test_counter_16bit_in_enum(self):
        """Verify counter_16bit is a valid RegisterType member."""
        assert RegisterType.COUNTER_16BIT in RegisterType


class TestCounter16BitBitWidth:
    """Test bit width for counter_16bit type."""

    def test_counter_16bit_bit_width(self):
        """Test bit width for counter_16bit."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=4095
        )
        assert reg.get_type_bit_width() == 16


class TestCounter16BitMaxValue:
    """Test max value for counter_16bit type."""

    def test_counter_16bit_max_value(self):
        """Test max value for counter_16bit."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=4095
        )
        assert reg.get_type_max_value() == 65535


class TestCounter16BitValidation:
    """Test validation for counter_16bit values."""

    def test_counter_16bit_validation_in_range_low(self):
        """Test counter_16bit accepts minimum valid value."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=0,
            min_value=0,
            max_value=4095
        )
        assert reg.default_value == 0

    def test_counter_16bit_validation_in_range_mid(self):
        """Test counter_16bit accepts mid-range value (voltage example)."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=0x3DCF,  # 15823 (2.4V)
            min_value=0,
            max_value=65535
        )
        assert reg.default_value == 0x3DCF

    def test_counter_16bit_validation_in_range_high(self):
        """Test counter_16bit accepts maximum valid value."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=65535,
            min_value=0,
            max_value=65535
        )
        assert reg.default_value == 65535

    def test_counter_16bit_validation_out_of_range_high(self):
        """Test counter_16bit rejects out-of-range values (too high)."""
        with pytest.raises(ValueError, match="COUNTER_16BIT default_value must be 0-65535"):
            AppRegister(
                name="Test 16-bit",
                description="Test register",
                reg_type=RegisterType.COUNTER_16BIT,
                cr_number=24,
                default_value=70000  # > 65535
            )

    def test_counter_16bit_validation_out_of_range_negative(self):
        """Test counter_16bit rejects negative values."""
        with pytest.raises(ValueError, match="COUNTER_16BIT default_value must be 0-65535"):
            AppRegister(
                name="Test 16-bit",
                description="Test register",
                reg_type=RegisterType.COUNTER_16BIT,
                cr_number=24,
                default_value=-1
            )


class TestCounter16BitMinMaxValidation:
    """Test min/max value validation for counter_16bit."""

    def test_counter_16bit_min_max_validation(self):
        """Test counter_16bit min/max value validation."""
        reg = AppRegister(
            name="Test 16-bit",
            description="Test register",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=1000,
            min_value=0,
            max_value=4095
        )
        assert reg.min_value == 0
        assert reg.max_value == 4095

    def test_counter_16bit_min_value_out_of_range(self):
        """Test counter_16bit rejects invalid min_value."""
        with pytest.raises(ValueError, match="COUNTER_16BIT min_value must be 0-65535"):
            AppRegister(
                name="Test 16-bit",
                description="Test register",
                reg_type=RegisterType.COUNTER_16BIT,
                cr_number=24,
                default_value=1000,
                min_value=-1,
                max_value=4095
            )

    def test_counter_16bit_max_value_out_of_range(self):
        """Test counter_16bit rejects invalid max_value."""
        with pytest.raises(ValueError, match="COUNTER_16BIT max_value must be 0-65535"):
            AppRegister(
                name="Test 16-bit",
                description="Test register",
                reg_type=RegisterType.COUNTER_16BIT,
                cr_number=24,
                default_value=1000,
                min_value=0,
                max_value=70000  # > 65535
            )


class TestCounter16BitRealWorldExamples:
    """Test counter_16bit with real DS1140-PD register examples."""

    def test_arm_timeout_register(self):
        """Test arm timeout register (12-bit value in 16-bit field)."""
        reg = AppRegister(
            name="Arm Timeout",
            description="Cycles to wait for trigger before timeout (0-4095)",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=24,
            default_value=255,
            min_value=0,
            max_value=4095
        )
        assert reg.get_type_bit_width() == 16
        assert reg.get_type_max_value() == 65535
        assert reg.default_value == 255

    def test_trigger_threshold_voltage_register(self):
        """Test trigger threshold voltage register (2.4V = 0x3DCF)."""
        reg = AppRegister(
            name="Trigger Threshold",
            description="Voltage threshold for trigger detection (16-bit signed)",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=27,
            default_value=0x3DCF  # 2.4V
        )
        assert reg.get_type_bit_width() == 16
        assert reg.default_value == 15823  # 0x3DCF in decimal

    def test_intensity_voltage_register(self):
        """Test intensity voltage register (2.0V = 0x2666)."""
        reg = AppRegister(
            name="Intensity",
            description="Output intensity (16-bit signed, clamped to 3.0V)",
            reg_type=RegisterType.COUNTER_16BIT,
            cr_number=28,
            default_value=0x2666  # 2.0V
        )
        assert reg.get_type_bit_width() == 16
        assert reg.default_value == 9830  # 0x2666 in decimal
