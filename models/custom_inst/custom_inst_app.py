"""
CustomInstApp Model - Hardware Abstraction Layer for FPGA Applications

CustomInstApp is a hardware abstraction layer for deploying FPGA applications to Moku
platform with human-friendly register interfaces.

A CustomInstApp consists of:
1. MCC bitstream (.tar) - Implements SimpleCustomInstrument interface
2. 4KB BRAM buffer (.bin) - Loaded via network protocol (optional)
3. Application registers (CR6-CR15) - Human-friendly controls (max 10)

Architecture (3 Layers):
1. MCC_TOP_custom_inst_loader.vhd (static, shared)
2. <AppName>_custom_inst_shim.vhd (generated from this model)
3. <AppName>_custom_inst_main.vhd (hand-written app logic)

Usage:
    >>> app = CustomInstApp.load_from_yaml("PulseStar_app.yaml")
    >>> shim_vhdl = app.generate_vhdl_shim(Path("templates/custom_inst_shim_template.vhd"))
    >>> app.save_to_yaml(Path("output/config.yaml"))
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from jinja2 import Environment, FileSystemLoader, Template

from .app_register import AppRegister, RegisterType


class CustomInstApp(BaseModel):
    """
    CustomInstApp application definition.

    Single source of truth for:
    - Application metadata
    - Register interface specification
    - Deployment artifacts (bitstream, buffer)
    - VHDL code generation

    Attributes:
        name: Application name (e.g., "DS1140_PD")
        version: Semantic version (e.g., "1.0.0")
        description: Human-readable description
        bitstream_path: Path to MCC bitstream (.tar file)
        buffer_path: Optional path to 4KB BRAM buffer (.bin file)
        registers: List of application registers (max 10, CR6-CR15)
        author: Optional author/team name
        tags: Optional list of tags for categorization

    Example:
        >>> app = CustomInstApp(
        ...     name="DS1140_PD",
        ...     version="1.0.0",
        ...     description="EMFI probe driver",
        ...     bitstream_path=Path("modules/DS1140_PD/latest/25ff_bitstreams.tar"),
        ...     buffer_path=Path("modules/DS1140_PD/buffers/timing_lut.bin"),
        ...     registers=[
        ...         AppRegister(
        ...             name="Arm Probe",
        ...             description="Arm the probe",
        ...             reg_type=RegisterType.BUTTON,
        ...             cr_number=6,
        ...             default_value=0
        ...         )
        ...     ],
        ...     author="Volo Team",
        ...     tags=["emfi", "probe"]
        ... )
    """

    name: str = Field(..., min_length=1, max_length=50)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(..., min_length=1, max_length=500)
    bitstream_path: Path
    buffer_path: Optional[Path] = None
    registers: List[AppRegister] = Field(..., min_length=1, max_length=10)
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    num_inputs: int = Field(default=2, ge=2, le=4, description="Number of MCC inputs (2-4, default 2)")
    num_outputs: int = Field(default=2, ge=2, le=4, description="Number of MCC outputs (2-4, default 2)")

    @field_validator('registers')
    @classmethod
    def validate_max_registers(cls, v: List[AppRegister]) -> List[AppRegister]:
        """Validate maximum 10 registers (CR6-CR15)."""
        if len(v) > 10:
            raise ValueError(f"Maximum 10 registers allowed (got {len(v)})")
        return v

    @model_validator(mode='after')
    def validate_no_duplicate_cr_numbers(self):
        """Validate no duplicate CR numbers."""
        cr_numbers = [reg.cr_number for reg in self.registers]
        if len(cr_numbers) != len(set(cr_numbers)):
            duplicates = [cr for cr in cr_numbers if cr_numbers.count(cr) > 1]
            raise ValueError(f"Duplicate CR numbers found: {set(duplicates)}")
        return self

    @staticmethod
    def to_vhdl_signal_name(friendly_name: str) -> str:
        """
        Convert friendly register name to VHDL signal name.

        Algorithm:
        1. Convert to lowercase
        2. Replace spaces with underscores
        3. Remove special characters (keep alphanumeric and underscore)
        4. Remove consecutive underscores
        5. Strip leading/trailing underscores

        Examples:
            >>> CustomInstApp.to_vhdl_signal_name("Pulse Width")
            'pulse_width'
            >>> CustomInstApp.to_vhdl_signal_name("Enable Output")
            'enable_output'
            >>> CustomInstApp.to_vhdl_signal_name("PWM Duty %")
            'pwm_duty'
        """
        # Convert to lowercase
        name = friendly_name.lower()

        # Replace spaces with underscores
        name = name.replace(' ', '_')

        # Remove special characters (keep alphanumeric and underscore)
        name = re.sub(r'[^a-z0-9_]', '', name)

        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)

        # Strip leading/trailing underscores
        name = name.strip('_')

        return name

    @staticmethod
    def get_vhdl_bit_range(reg: AppRegister) -> str:
        """
        Get VHDL bit range for extracting signal from 32-bit Control Register.

        Uses MSB-first alignment (upper bits) for cleaner bit packing:
        - COUNTER_8BIT  → "(31 downto 24)" - Upper 8 bits
        - COUNTER_16BIT → "(31 downto 16)" - Upper 16 bits (NEW)
        - PERCENT       → "(31 downto 25)" - Upper 7 bits
        - BUTTON        → "(31)"           - MSB only

        Note: This returns the extraction range from app_reg_N, NOT the signal type.

        Examples:
            COUNTER_8BIT  → "arm_timeout <= app_reg_24(31 downto 24);"
            COUNTER_16BIT → "trigger_threshold <= app_reg_27(31 downto 16);"
            PERCENT       → "duty_cycle <= app_reg_20(31 downto 25);"
            BUTTON        → "armed <= app_reg_20(31);"
        """
        bit_width = reg.get_type_bit_width()
        if bit_width == 1:
            return "(31)"
        else:
            # Use upper bits: [31 downto (32 - bit_width)]
            return f"(31 downto {32 - bit_width})"

    @staticmethod
    def get_vhdl_type_declaration(reg: AppRegister) -> str:
        """
        Get VHDL type declaration for register signal.

        Examples:
            COUNTER_8BIT  → "std_logic_vector(7 downto 0)"
            COUNTER_16BIT → "std_logic_vector(15 downto 0)" (NEW)
            PERCENT       → "std_logic_vector(6 downto 0)"
            BUTTON        → "std_logic"
        """
        bit_width = reg.get_type_bit_width()
        if bit_width == 1:
            return "std_logic"
        else:
            return f"std_logic_vector({bit_width - 1} downto 0)"

    def generate_vhdl_shim(self, template_path: Path) -> str:
        """
        Generate VHDL shim layer from Jinja2 template.

        The shim maps raw Control Registers (CR6-CR15) to friendly signal names
        and instantiates the application main entity.

        Args:
            template_path: Path to custom_inst_shim_template.vhd

        Returns:
            Generated VHDL code as string

        Template Variables:
            app_name: Application name (e.g., "DS1140_PD")
            registers: List of register mappings with:
                - friendly_name: VHDL signal name (e.g., "arm_probe")
                - cr_number: Control Register number (e.g., 20)
                - vhdl_type: Type declaration (e.g., "std_logic_vector(7 downto 0)")
                - bit_range: Bit extraction range (e.g., "(7 downto 0)")
                - description: Human-readable description
            cr_numbers_used: List of CR numbers used (for port map)
        """
        # Prepare template context
        register_mappings = []
        for reg in self.registers:
            register_mappings.append({
                'friendly_name': self.to_vhdl_signal_name(reg.name),
                'cr_number': reg.cr_number,
                'vhdl_type': self.get_vhdl_type_declaration(reg),
                'bit_range': self.get_vhdl_bit_range(reg),
                'description': reg.description,
                'original_name': reg.name
            })

        cr_numbers_used = sorted([reg.cr_number for reg in self.registers])

        context = {
            'app_name': self.name,
            'registers': register_mappings,
            'cr_numbers_used': cr_numbers_used,
            'num_inputs': self.num_inputs,
            'num_outputs': self.num_outputs,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Load and render template
        template_dir = template_path.parent
        template_name = template_path.name
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)

        return template.render(context)

    def generate_vhdl_main_template(self, template_path: Path) -> str:
        """
        Generate VHDL main template from Jinja2 template.

        The main template provides a skeleton for application logic with
        friendly signal names and no Control Register knowledge.

        Args:
            template_path: Path to volo_main_template.vhd

        Returns:
            Generated VHDL code as string

        Template Variables:
            app_name: Application name (e.g., "PulseStar")
            friendly_ports: List of port declarations with:
                - name: Signal name (e.g., "pulse_width")
                - vhdl_type: Type (e.g., "std_logic_vector(7 downto 0)")
                - description: Comment (e.g., "Pulse duration in clock cycles")
        """
        # Prepare friendly port list
        friendly_ports = []
        for reg in self.registers:
            friendly_ports.append({
                'name': self.to_vhdl_signal_name(reg.name),
                'vhdl_type': self.get_vhdl_type_declaration(reg),
                'description': reg.description
            })

        context = {
            'app_name': self.name,
            'friendly_ports': friendly_ports,
            'num_inputs': self.num_inputs,
            'num_outputs': self.num_outputs,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Load and render template
        template_dir = template_path.parent
        template_name = template_path.name
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)

        return template.render(context)

    def to_deployment_config(self) -> Dict:
        """
        Generate deployment configuration dictionary.

        Returns a dictionary suitable for the volo_loader.py deployment script.

        Returns:
            Dictionary with deployment parameters:
            - name: Application name
            - version: Semantic version
            - bitstream_path: Path to bitstream (as string)
            - buffer_path: Optional path to buffer (as string)
            - registers: List of register configurations with CR numbers and defaults
        """
        return {
            'name': self.name,
            'version': self.version,
            'bitstream_path': str(self.bitstream_path),
            'buffer_path': str(self.buffer_path) if self.buffer_path else None,
            'registers': [
                {
                    'name': reg.name,
                    'cr_number': reg.cr_number,
                    'default_value': reg.default_value
                }
                for reg in self.registers
            ]
        }

    def save_to_yaml(self, path: Path) -> None:
        """
        Save VoloApp configuration to YAML file.

        Args:
            path: Output file path

        Example:
            >>> app.save_to_yaml(Path("PulseStar_app.yaml"))
        """
        # Convert to dict, handling Path objects
        data = self.model_dump(mode='python')
        data['bitstream_path'] = str(self.bitstream_path)
        if self.buffer_path:
            data['buffer_path'] = str(self.buffer_path)

        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load_from_yaml(cls, path: Path) -> 'VoloApp':
        """
        Load VoloApp configuration from YAML file.

        Args:
            path: Input YAML file path

        Returns:
            VoloApp instance

        Example:
            >>> app = VoloApp.load_from_yaml(Path("PulseStar_app.yaml"))
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        # Convert path strings to Path objects
        if 'bitstream_path' in data:
            data['bitstream_path'] = Path(data['bitstream_path'])
        if 'buffer_path' in data and data['buffer_path']:
            data['buffer_path'] = Path(data['buffer_path'])

        # Convert register dicts to AppRegister objects
        if 'registers' in data:
            data['registers'] = [AppRegister(**reg) for reg in data['registers']]

        return cls(**data)
