"""
VoloApp - Hardware Abstraction Layer for FPGA Applications

This package provides a Pydantic-based model for deploying FPGA applications
to Moku platform with human-friendly register interfaces.

Main Classes:
    VoloApp: Application definition model with VHDL generation
    AppRegister: Register interface definition
    RegisterType: Supported register types enum

Quick Start:
    >>> from models.volo import VoloApp, AppRegister, RegisterType
    >>> from pathlib import Path
    >>>
    >>> # Load existing app
    >>> app = VoloApp.load_from_yaml(Path("PulseStar_app.yaml"))
    >>>
    >>> # Generate VHDL shim
    >>> shim_vhdl = app.generate_vhdl_shim(
    ...     Path("shared/volo/templates/volo_shim_template.vhd")
    ... )
    >>>
    >>> # Save to file
    >>> with open("PulseStar_volo_shim.vhd", "w") as f:
    ...     f.write(shim_vhdl)

Architecture:
    VoloApp defines a 3-layer architecture:
    1. MCC_TOP_volo_loader.vhd (static, shared)
    2. <AppName>_volo_shim.vhd (generated)
    3. <AppName>_volo_main.vhd (hand-written)

Register Map:
    - CR0[31:29]: VOLO_READY control scheme
    - CR10-CR14: BRAM loader protocol (4KB buffer)
    - CR20-CR30: Application registers (max 11)

For complete documentation, see:
    - docs/VOLO_APP_DESIGN.md
    - docs/VOLO_APP_FRESH_CONTEXT.md
    - models/volo/README.md
"""

from .app_register import AppRegister, RegisterType
from .volo_app import VoloApp

__all__ = [
    'VoloApp',
    'AppRegister',
    'RegisterType',
]

__version__ = '1.0.0'
