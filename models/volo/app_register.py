"""
VoloApp Register Type System

Defines register types and application register models for the VoloApp abstraction.
This module provides a limited but validated type system for FPGA register interfaces.

Register Types (Limited by Design):
- COUNTER_8BIT: 8-bit unsigned counter (0-255)
- PERCENT: Percentage value (0-100)
- BUTTON: Boolean push-button (0 or 1)

Design Principle: Start simple, extend later. These 3 types cover 80% of use cases.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RegisterType(str, Enum):
    """
    Supported register types for VoloApp interface.

    Each type maps to a specific VHDL signal type:
    - COUNTER_8BIT → std_logic_vector(7 downto 0)
    - PERCENT      → std_logic_vector(6 downto 0)  # 0-100 requires 7 bits
    - BUTTON       → std_logic
    """
    COUNTER_8BIT = "counter_8bit"
    PERCENT = "percent"
    BUTTON = "button"


class AppRegister(BaseModel):
    """
    Application register definition for VoloApp interface.

    Defines a single control register (CR20-CR30) with human-friendly naming
    and automatic validation of value ranges.

    Attributes:
        name: Human-readable name (e.g., "Pulse Width")
              Converted to VHDL signal name via to_vhdl_signal_name()
        description: What this register controls
        reg_type: Register type (determines bit width and range)
        cr_number: Control Register number (must be 20-30 inclusive)
        default_value: Default value on reset (optional)
        min_value: Minimum allowed value (optional, type-dependent)
        max_value: Maximum allowed value (optional, type-dependent)

    Example:
        >>> reg = AppRegister(
        ...     name="Pulse Width",
        ...     description="Pulse duration in clock cycles",
        ...     reg_type=RegisterType.COUNTER_8BIT,
        ...     cr_number=20,
        ...     default_value=100,
        ...     min_value=1,
        ...     max_value=255
        ... )
        >>> reg.name
        'Pulse Width'
        >>> reg.cr_number
        20
    """

    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)
    reg_type: RegisterType
    cr_number: int = Field(..., ge=20, le=30)
    default_value: Optional[int] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None

    @field_validator('cr_number')
    @classmethod
    def validate_cr_number(cls, v: int) -> int:
        """Validate Control Register number is in application range (20-30)."""
        if not (20 <= v <= 30):
            raise ValueError(f"cr_number must be 20-30 (got {v})")
        return v

    @field_validator('default_value')
    @classmethod
    def validate_default_value(cls, v: Optional[int], info) -> Optional[int]:
        """Validate default_value matches register type constraints."""
        if v is None:
            return None

        # Get reg_type from validation context
        reg_type = info.data.get('reg_type')
        if reg_type is None:
            return v  # Can't validate without type

        # Type-specific validation
        if reg_type == RegisterType.COUNTER_8BIT:
            if not (0 <= v <= 255):
                raise ValueError(f"COUNTER_8BIT default_value must be 0-255 (got {v})")
        elif reg_type == RegisterType.PERCENT:
            if not (0 <= v <= 100):
                raise ValueError(f"PERCENT default_value must be 0-100 (got {v})")
        elif reg_type == RegisterType.BUTTON:
            if v not in (0, 1):
                raise ValueError(f"BUTTON default_value must be 0 or 1 (got {v})")

        return v

    @field_validator('min_value')
    @classmethod
    def validate_min_value(cls, v: Optional[int], info) -> Optional[int]:
        """Validate min_value is within register type constraints."""
        if v is None:
            return None

        reg_type = info.data.get('reg_type')
        if reg_type is None:
            return v

        if reg_type == RegisterType.COUNTER_8BIT:
            if not (0 <= v <= 255):
                raise ValueError(f"COUNTER_8BIT min_value must be 0-255 (got {v})")
        elif reg_type == RegisterType.PERCENT:
            if not (0 <= v <= 100):
                raise ValueError(f"PERCENT min_value must be 0-100 (got {v})")
        elif reg_type == RegisterType.BUTTON:
            if v not in (0, 1):
                raise ValueError(f"BUTTON min_value must be 0 or 1 (got {v})")

        return v

    @field_validator('max_value')
    @classmethod
    def validate_max_value(cls, v: Optional[int], info) -> Optional[int]:
        """Validate max_value is within register type constraints."""
        if v is None:
            return None

        reg_type = info.data.get('reg_type')
        if reg_type is None:
            return v

        if reg_type == RegisterType.COUNTER_8BIT:
            if not (0 <= v <= 255):
                raise ValueError(f"COUNTER_8BIT max_value must be 0-255 (got {v})")
        elif reg_type == RegisterType.PERCENT:
            if not (0 <= v <= 100):
                raise ValueError(f"PERCENT max_value must be 0-100 (got {v})")
        elif reg_type == RegisterType.BUTTON:
            if v not in (0, 1):
                raise ValueError(f"BUTTON max_value must be 0 or 1 (got {v})")

        return v

    def get_type_max_value(self) -> int:
        """Get maximum possible value for this register type."""
        if self.reg_type == RegisterType.COUNTER_8BIT:
            return 255
        elif self.reg_type == RegisterType.PERCENT:
            return 100
        elif self.reg_type == RegisterType.BUTTON:
            return 1
        else:
            raise ValueError(f"Unknown register type: {self.reg_type}")

    def get_type_bit_width(self) -> int:
        """Get bit width for this register type."""
        if self.reg_type == RegisterType.COUNTER_8BIT:
            return 8
        elif self.reg_type == RegisterType.PERCENT:
            return 7  # 0-100 requires 7 bits
        elif self.reg_type == RegisterType.BUTTON:
            return 1
        else:
            raise ValueError(f"Unknown register type: {self.reg_type}")
