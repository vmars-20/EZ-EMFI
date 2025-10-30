"""
CustomInstApp - Hardware Abstraction Layer for FPGA Applications

This package provides a Pydantic-based model for deploying FPGA applications
to Moku platform with human-friendly register interfaces.

Main Classes:
    CustomInstApp: Application definition model with VHDL generation
    AppRegister: Register interface definition
    RegisterType: Supported register types enum

Quick Start:
    >>> from models.custom_inst import CustomInstApp, AppRegister, RegisterType
    >>> from pathlib import Path
    >>>
    >>> # Load existing app
    >>> app = CustomInstApp.load_from_yaml(Path("DS1140_PD_app.yaml"))
    >>>
    >>> # Generate VHDL shim
    >>> shim_vhdl = app.generate_vhdl_shim(
    ...     Path("shared/custom_inst/templates/custom_inst_shim_template.vhd")
    ... )
    >>>
    >>> # Save to file
    >>> with open("DS1140_PD_custom_inst_shim.vhd", "w") as f:
    ...     f.write(shim_vhdl)

Architecture:
    CustomInstApp defines a 3-layer architecture:
    1. MCC_TOP_custom_inst_loader.vhd (static, shared)
    2. <AppName>_custom_inst_shim.vhd (generated)
    3. <AppName>_custom_inst_main.vhd (hand-written)

Register Map:
    - CR0[31:29]: VOLO_READY control scheme
    - CR1-CR5: BRAM loader protocol (4KB buffer)
    - CR6-CR15: Application registers (max 10)

For complete documentation, see:
    - docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md
    - models/custom_inst/README.md
"""

from .app_register import AppRegister, RegisterType
from .custom_inst_app import CustomInstApp

__all__ = [
    'CustomInstApp',
    'AppRegister',
    'RegisterType',
]

__version__ = '1.0.0'
