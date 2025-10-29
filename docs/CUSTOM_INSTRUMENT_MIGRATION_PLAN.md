# CustomInstrument Migration Plan

**Branch**: `feature/CustomInstrument`
**Date**: 2025-10-29
**Status**: Planning Phase
**Breaking Change**: MCC CustomWrapper (32 registers) → CustomInstrument (16 registers)

---

## Executive Summary

The upstream MCC vendor has released a breaking change to the core VHDL entity that our entire project is built around:

1. **Entity name change**: `CustomWrapper` → `SimpleCustomInstrument`
2. **Register reduction**: 32 control registers → 16 control registers (Control0-Control15)

This migration treats the compatibility break as an opportunity to refine the codebase with modern naming conventions and cleaner architecture.

### Migration Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Register Allocation** | Control0 (VOLO_READY), Control1-5 (BRAM), Control6-15 (app regs) | Preserves infrastructure, provides 10 app registers |
| **Architecture** | Keep 3-layer (Loader → Shim → Main) | Maintains separation of concerns and code generation |
| **Naming Convention** | Rename all 'volo' → 'custom_inst' | Clean break, aligns with new MCC entity name |
| **Backward Compatibility** | Clean break - no legacy support | `feature/CustomInstrument` becomes the new standard |

---

## New Register Map

### Overview

With only 16 control registers available, the register allocation changes significantly:

```
OLD CustomWrapper (32 registers):
├─ Control0      : VOLO_READY control bits (volo_ready, user_enable, clk_enable)
├─ Control1-9    : Available (unused in current design)
├─ Control10-14  : BRAM loader protocol
├─ Control15-19  : Available (unused)
└─ Control20-30  : Application registers (11 registers)

NEW CustomInstrument (16 registers):
├─ Control0      : VOLO_READY control bits (unchanged)
├─ Control1-5    : BRAM loader protocol (moved from Control10-14)
├─ Control6-15   : Application registers (10 registers, reduced from 11)
```

### Detailed Register Allocation

| Register | Old Usage | New Usage | Notes |
|----------|-----------|-----------|-------|
| Control0 | VOLO_READY bits | VOLO_READY bits | **Unchanged**: [31]=volo_ready, [30]=user_enable, [29]=clk_enable |
| Control1 | Unused | BRAM Start + Count | **New**: BRAM loader protocol (was Control10) |
| Control2 | Unused | BRAM Address | **New**: BRAM loader protocol (was Control11) |
| Control3 | Unused | BRAM Data | **New**: BRAM loader protocol (was Control12) |
| Control4 | Unused | BRAM Write Strobe | **New**: BRAM loader protocol (was Control13) |
| Control5 | Unused | BRAM Reserved | **New**: BRAM loader protocol (was Control14) |
| Control6 | Unused | **App Register 0** | **New**: First app register (was Control20) |
| Control7 | Unused | **App Register 1** | **New**: Second app register (was Control21) |
| Control8 | Unused | **App Register 2** | **New**: Third app register (was Control22) |
| Control9 | Unused | **App Register 3** | **New**: Fourth app register (was Control23) |
| Control10 | BRAM Start | **App Register 4** | **Changed**: Now app register (was Control24) |
| Control11 | BRAM Address | **App Register 5** | **Changed**: Now app register (was Control25) |
| Control12 | BRAM Data | **App Register 6** | **Changed**: Now app register (was Control26) |
| Control13 | BRAM Strobe | **App Register 7** | **Changed**: Now app register (was Control27) |
| Control14 | BRAM Reserved | **App Register 8** | **Changed**: Now app register (was Control28) |
| Control15 | Unused | **App Register 9** | **New**: Last app register (was Control29) |
| ~~Control16-30~~ | App regs 16-30 | **REMOVED** | **No longer available** |

### Breaking Changes

1. **Maximum app registers reduced**: 11 → 10 (removed 1 register)
2. **App register numbering changed**: CR20-30 → CR6-15
3. **BRAM protocol registers moved**: Control10-14 → Control1-5
4. **DS1140_PD impact**: Currently uses 9 registers (CR20-28), fits in new 10-register limit ✓

---

## Architecture Changes

### 3-Layer Architecture (Preserved)

The 3-layer architecture is **preserved** with updated nomenclature:

```
Layer 1: MCC_TOP_custom_inst_loader.vhd (was MCC_TOP_volo_loader.vhd)
         ├─ Implements SimpleCustomInstrument architecture
         ├─ Extracts VOLO_READY bits from Control0
         ├─ Instantiates custom_inst_bram_loader (Control1-5)
         └─ Routes Control6-15 to shim as app_reg_6 through app_reg_15

Layer 2: <AppName>_custom_inst_shim.vhd (was <AppName>_volo_shim.vhd)
         ├─ Maps app_reg_6..15 to friendly signal names
         ├─ Computes global_enable from VOLO_READY bits
         └─ Instantiates <AppName>_custom_inst_main

Layer 3: <AppName>_custom_inst_main.vhd (was <AppName>_volo_main.vhd)
         ├─ Implements application logic
         └─ Uses friendly signal names (no CR knowledge)
```

### VHDL Entity Changes

**Old Entity (CustomWrapper)**:
```vhdl
-- Provided by MCC, 32 control registers
-- Control0-Control30 available
architecture volo_loader of CustomWrapper is
```

**New Entity (SimpleCustomInstrument)**:
```vhdl
-- Provided by MCC, 16 control registers
-- Control0-Control15 available
entity SimpleCustomInstrument is
    Port (
        Clk : in std_logic;
        Reset : in std_logic;
        InputA, InputB, InputC : in signed(15 downto 0);
        OutputA, OutputB, OutputC : out signed(15 downto 0);
        Control0 : in std_logic_vector(31 downto 0);
        Control1 : in std_logic_vector(31 downto 0);
        -- ... Control2-15 ...
        Control15 : in std_logic_vector(31 downto 0)
    );
end SimpleCustomInstrument;

architecture Behavioral of SimpleCustomInstrument is
    -- User implementation here
end Behavioral;
```

---

## File Structure Changes

### Directory Renaming

```bash
# VHDL shared components
shared/volo/                      → shared/custom_inst/
shared/volo/MCC_TOP_volo_loader.vhd           → shared/custom_inst/MCC_TOP_custom_inst_loader.vhd
shared/volo/volo_bram_loader.vhd              → shared/custom_inst/custom_inst_bram_loader.vhd
shared/volo/volo_common_pkg.vhd               → shared/custom_inst/custom_inst_common_pkg.vhd
shared/volo/templates/                        → shared/custom_inst/templates/
shared/volo/templates/volo_shim_template.vhd  → shared/custom_inst/templates/custom_inst_shim_template.vhd
shared/volo/templates/volo_main_template.vhd  → shared/custom_inst/templates/custom_inst_main_template.vhd

# Python models
models/volo/                      → models/custom_inst/
models/volo/__init__.py           → models/custom_inst/__init__.py
models/volo/volo_app.py           → models/custom_inst/custom_inst_app.py
models/volo/app_register.py       → models/custom_inst/app_register.py (same name, content updated)

# Tools
tools/generate_volo_app.py        → tools/generate_custom_inst.py
```

### Generated File Naming

```bash
# Old naming (volo)
DS1140_PD_volo_shim.vhd
DS1140_PD_volo_main.vhd

# New naming (custom_inst)
DS1140_PD_custom_inst_shim.vhd
DS1140_PD_custom_inst_main.vhd
```

---

## Code Changes Detail

### 1. VHDL Layer Changes

#### 1.1 MCC_TOP_custom_inst_loader.vhd (was MCC_TOP_volo_loader.vhd)

**Entity Change**:
```vhdl
-- OLD:
architecture volo_loader of CustomWrapper is

-- NEW:
architecture Behavioral of SimpleCustomInstrument is
```

**BRAM Loader Port Map**:
```vhdl
-- OLD:
BRAM_LOADER_INST: entity WORK.volo_bram_loader
    port map (
        Control10 => Control10,
        Control11 => Control11,
        Control12 => Control12,
        Control13 => Control13,
        Control14 => Control14,
        -- ...
    );

-- NEW:
BRAM_LOADER_INST: entity WORK.custom_inst_bram_loader
    port map (
        Control1 => Control1,  -- Start + count (was Control10)
        Control2 => Control2,  -- Address (was Control11)
        Control3 => Control3,  -- Data (was Control12)
        Control4 => Control4,  -- Write strobe (was Control13)
        Control5 => Control5,  -- Reserved (was Control14)
        -- ...
    );
```

**App Register Mapping**:
```vhdl
-- OLD:
app_reg_20 <= Control20;
app_reg_21 <= Control21;
-- ... app_reg_22 through app_reg_30

-- NEW:
app_reg_6  <= Control6;
app_reg_7  <= Control7;
app_reg_8  <= Control8;
app_reg_9  <= Control9;
app_reg_10 <= Control10;
app_reg_11 <= Control11;
app_reg_12 <= Control12;
app_reg_13 <= Control13;
app_reg_14 <= Control14;
app_reg_15 <= Control15;
```

**Shim Instantiation**:
```vhdl
-- OLD:
APP_SHIM_INST: entity WORK.DS1140_PD_volo_shim
    port map (
        app_reg_20 => app_reg_20,
        app_reg_21 => app_reg_21,
        -- ... app_reg_22 through app_reg_28
    );

-- NEW:
APP_SHIM_INST: entity WORK.DS1140_PD_custom_inst_shim
    port map (
        app_reg_6  => app_reg_6,
        app_reg_7  => app_reg_7,
        -- ... app_reg_8 through app_reg_15
    );
```

#### 1.2 custom_inst_bram_loader.vhd (was volo_bram_loader.vhd)

**Port Declaration**:
```vhdl
-- OLD:
entity volo_bram_loader is
    port (
        Control10 : in std_logic_vector(31 downto 0);  -- Start + count
        Control11 : in std_logic_vector(31 downto 0);  -- Address
        Control12 : in std_logic_vector(31 downto 0);  -- Data
        Control13 : in std_logic_vector(31 downto 0);  -- Write strobe
        Control14 : in std_logic_vector(31 downto 0);  -- Reserved
        -- ...
    );
end volo_bram_loader;

-- NEW:
entity custom_inst_bram_loader is
    port (
        Control1 : in std_logic_vector(31 downto 0);  -- Start + count
        Control2 : in std_logic_vector(31 downto 0);  -- Address
        Control3 : in std_logic_vector(31 downto 0);  -- Data
        Control4 : in std_logic_vector(31 downto 0);  -- Write strobe
        Control5 : in std_logic_vector(31 downto 0);  -- Reserved
        -- ...
    );
end custom_inst_bram_loader;
```

**Signal Extraction**:
```vhdl
-- OLD:
start_loading <= Control10(0);
word_count    <= unsigned(Control10(31 downto 16));
write_strobe  <= Control13(0);
bram_addr     <= Control11(11 downto 0);
bram_data     <= Control12;

-- NEW:
start_loading <= Control1(0);
word_count    <= unsigned(Control1(31 downto 16));
write_strobe  <= Control4(0);
bram_addr     <= Control2(11 downto 0);
bram_data     <= Control3;
```

#### 1.3 custom_inst_common_pkg.vhd (was volo_common_pkg.vhd)

**Package Rename**:
```vhdl
-- OLD:
package volo_common_pkg is

-- NEW:
package custom_inst_common_pkg is
```

**Updated Comments**:
```vhdl
-- OLD:
-- VoloApp Common Package
-- Shared constants and functions for volo-app infrastructure

-- NEW:
-- CustomInstrument Common Package
-- Shared constants and functions for custom_inst infrastructure
```

**BRAM Protocol Documentation**:
```vhdl
-- OLD:
-- The custom_inst_bram_loader FSM uses Control10-Control14 to stream data

-- NEW:
-- The custom_inst_bram_loader FSM uses Control1-Control5 to stream data
```

#### 1.4 Template Changes (custom_inst_shim_template.vhd)

**Template Context Variables**:
```jinja2
{# OLD: #}
{% for cr_num in cr_numbers_used %}
        app_reg_{{ cr_num }} : in  std_logic_vector(31 downto 0);
{% endfor %}
{# cr_numbers_used = [20, 21, 22, ...] #}

{# NEW: #}
{% for cr_num in cr_numbers_used %}
        app_reg_{{ cr_num }} : in  std_logic_vector(31 downto 0);
{% endfor %}
{# cr_numbers_used = [6, 7, 8, ...] #}
```

**Register Mapping Comments**:
```jinja2
{# OLD: #}
-- Application Registers (from MCC_TOP_volo_loader)
-- Raw Control Registers CR20-CR30

{# NEW: #}
-- Application Registers (from MCC_TOP_custom_inst_loader)
-- Raw Control Registers CR6-CR15
```

**MCC I/O Comments**:
```jinja2
{# OLD: #}
-- MCC I/O (from CustomWrapper)

{# NEW: #}
-- MCC I/O (from SimpleCustomInstrument)
```

**Entity Instantiation**:
```jinja2
{# OLD: #}
APP_MAIN_INST: entity WORK.{{ app_name }}_volo_main

{# NEW: #}
APP_MAIN_INST: entity WORK.{{ app_name }}_custom_inst_main
```

---

### 2. Python Model Changes

#### 2.1 custom_inst_app.py (was volo_app.py)

**Class Rename**:
```python
# OLD:
class VoloApp(BaseModel):
    """
    VoloApp application definition.
    """

# NEW:
class CustomInstApp(BaseModel):
    """
    CustomInstrument application definition.
    """
```

**Register Validation**:
```python
# OLD:
registers: List[AppRegister] = Field(..., min_length=1, max_length=11)

@field_validator('registers')
@classmethod
def validate_max_registers(cls, v: List[AppRegister]) -> List[AppRegister]:
    """Validate maximum 11 registers (CR20-CR30)."""
    if len(v) > 11:
        raise ValueError(f"Maximum 11 registers allowed (got {len(v)})")
    return v

# NEW:
registers: List[AppRegister] = Field(..., min_length=1, max_length=10)

@field_validator('registers')
@classmethod
def validate_max_registers(cls, v: List[AppRegister]) -> List[AppRegister]:
    """Validate maximum 10 registers (CR6-CR15)."""
    if len(v) > 10:
        raise ValueError(f"Maximum 10 registers allowed (got {len(v)})")
    return v
```

**Template Path References**:
```python
# OLD:
shim_template_path = project_root / "shared" / "volo" / "templates" / "volo_shim_template.vhd"
main_template_path = project_root / "shared" / "volo" / "templates" / "volo_main_template.vhd"

# NEW:
shim_template_path = project_root / "shared" / "custom_inst" / "templates" / "custom_inst_shim_template.vhd"
main_template_path = project_root / "shared" / "custom_inst" / "templates" / "custom_inst_main_template.vhd"
```

**Generated File Naming**:
```python
# OLD:
shim_output_path = output_dir / f"{app.name}_volo_shim.vhd"
main_output_path = output_dir / f"{app.name}_volo_main.vhd"

# NEW:
shim_output_path = output_dir / f"{app.name}_custom_inst_shim.vhd"
main_output_path = output_dir / f"{app.name}_custom_inst_main.vhd"
```

**Docstring Updates**:
```python
# OLD:
"""
VoloApp is a hardware abstraction layer for deploying FPGA applications to Moku
platform with human-friendly register interfaces.

A VoloApp consists of:
1. MCC bitstream (.tar) - Implements CustomWrapper interface
2. 4KB BRAM buffer (.bin) - Loaded via network protocol (optional)
3. Application registers (CR20-CR30) - Human-friendly controls

Architecture (3 Layers):
1. MCC_TOP_volo_loader.vhd (static, shared)
2. <AppName>_volo_shim.vhd (generated from this model)
3. <AppName>_volo_main.vhd (hand-written app logic)
"""

# NEW:
"""
CustomInstApp is a hardware abstraction layer for deploying FPGA applications to Moku
platform with human-friendly register interfaces.

A CustomInstApp consists of:
1. MCC bitstream (.tar) - Implements SimpleCustomInstrument interface
2. 4KB BRAM buffer (.bin) - Loaded via network protocol (optional)
3. Application registers (CR6-CR15) - Human-friendly controls

Architecture (3 Layers):
1. MCC_TOP_custom_inst_loader.vhd (static, shared)
2. <AppName>_custom_inst_shim.vhd (generated from this model)
3. <AppName>_custom_inst_main.vhd (hand-written app logic)
"""
```

**Module-Level Docstring**:
```python
# OLD:
"""
VoloApp Model - Hardware Abstraction Layer for FPGA Applications
"""

# NEW:
"""
CustomInstApp Model - Hardware Abstraction Layer for FPGA Applications
"""
```

#### 2.2 app_register.py

**CR Number Validation**:
```python
# OLD:
cr_number: int = Field(..., ge=20, le=30)

@field_validator('cr_number')
@classmethod
def validate_cr_number(cls, v: int) -> int:
    """Validate Control Register number is in application range (20-30)."""
    if not (20 <= v <= 30):
        raise ValueError(f"cr_number must be 20-30 (got {v})")
    return v

# NEW:
cr_number: int = Field(..., ge=6, le=15)

@field_validator('cr_number')
@classmethod
def validate_cr_number(cls, v: int) -> int:
    """Validate Control Register number is in application range (6-15)."""
    if not (6 <= v <= 15):
        raise ValueError(f"cr_number must be 6-15 (got {v})")
    return v
```

**Docstring Updates**:
```python
# OLD:
"""
Application register definition for VoloApp interface.

Defines a single control register (CR20-CR30) with human-friendly naming
and automatic validation of value ranges.

Attributes:
    cr_number: Control Register number (must be 20-30 inclusive)
"""

# NEW:
"""
Application register definition for CustomInstApp interface.

Defines a single control register (CR6-CR15) with human-friendly naming
and automatic validation of value ranges.

Attributes:
    cr_number: Control Register number (must be 6-15 inclusive)
"""
```

#### 2.3 models/custom_inst/__init__.py

```python
# OLD:
"""VoloApp models for FPGA application abstraction."""

from .volo_app import VoloApp
from .app_register import AppRegister, RegisterType

__all__ = ['VoloApp', 'AppRegister', 'RegisterType']

# NEW:
"""CustomInstApp models for FPGA application abstraction."""

from .custom_inst_app import CustomInstApp
from .app_register import AppRegister, RegisterType

__all__ = ['CustomInstApp', 'AppRegister', 'RegisterType']
```

---

### 3. Tool Changes

#### 3.1 tools/generate_custom_inst.py (was generate_volo_app.py)

**Import Changes**:
```python
# OLD:
from models.volo import VoloApp

# NEW:
from models.custom_inst import CustomInstApp
```

**Variable Naming**:
```python
# OLD:
app = VoloApp.load_from_yaml(config_path)

# NEW:
app = CustomInstApp.load_from_yaml(config_path)
```

**Banner and Help Text**:
```python
# OLD:
console.print(Panel.fit(
    "[bold cyan]VoloApp Code Generator[/bold cyan]\n"
    "Generate VHDL shim and main template from VoloApp definition",
    border_style="cyan"
))

# NEW:
console.print(Panel.fit(
    "[bold cyan]CustomInstrument Code Generator[/bold cyan]\n"
    "Generate VHDL shim and main template from CustomInstApp definition",
    border_style="cyan"
))
```

**CLI Arguments**:
```python
# OLD:
parser = argparse.ArgumentParser(
    description="Generate VoloApp VHDL files from YAML definition",
    epilog="""
Examples:
  python tools/generate_volo_app.py \\
      --config modules/PulseStar/PulseStar_app.yaml \\
      --output modules/PulseStar/volo_main/
    """
)

# NEW:
parser = argparse.ArgumentParser(
    description="Generate CustomInstApp VHDL files from YAML definition",
    epilog="""
Examples:
  python tools/generate_custom_inst.py \\
      --config modules/PulseStar/PulseStar_app.yaml \\
      --output modules/PulseStar/custom_inst_main/
    """
)
```

**Console Messages**:
```python
# OLD:
console.print(f"\n[cyan]→[/cyan] Loading VoloApp from {config_path}")

# NEW:
console.print(f"\n[cyan]→[/cyan] Loading CustomInstApp from {config_path}")
```

---

### 4. YAML Configuration Changes

**DS1140_PD_app.yaml** (example migration):

```yaml
# OLD:
# Application Registers (Control20-Control28)
# Total: 9 registers (MCC CustomWrapper provides Control0-Control30)
registers:
  - name: Arm Probe
    reg_type: button
    cr_number: 20

  - name: Force Fire
    reg_type: button
    cr_number: 21
  # ... (cr_number: 22, 23, 24, 25, 26, 27, 28)

# Register Bit Packing:
#   Control20: app_reg_20(31)
#   Control21: app_reg_21(31)
#   ...

# NEW:
# Application Registers (Control6-Control14)
# Total: 9 registers (MCC CustomInstrument provides Control0-Control15)
registers:
  - name: Arm Probe
    reg_type: button
    cr_number: 6

  - name: Force Fire
    reg_type: button
    cr_number: 7
  # ... (cr_number: 8, 9, 10, 11, 12, 13, 14)

# Register Bit Packing:
#   Control6: app_reg_6(31)
#   Control7: app_reg_7(31)
#   ...
```

---

## Migration Checklist

### Phase 1: Core Infrastructure (Shared Components)

- [ ] **1.1** Rename directory: `shared/volo/` → `shared/custom_inst/`
- [ ] **1.2** Update `MCC_TOP_volo_loader.vhd` → `MCC_TOP_custom_inst_loader.vhd`
  - [ ] Change entity: `architecture volo_loader of CustomWrapper` → `architecture Behavioral of SimpleCustomInstrument`
  - [ ] Update BRAM loader instantiation: Control10-14 → Control1-5
  - [ ] Update app register mapping: Control20-30 → Control6-15
  - [ ] Update signal names: app_reg_20..30 → app_reg_6..15
  - [ ] Update shim instantiation: `volo_shim` → `custom_inst_shim`
- [ ] **1.3** Update `volo_bram_loader.vhd` → `custom_inst_bram_loader.vhd`
  - [ ] Rename entity: `volo_bram_loader` → `custom_inst_bram_loader`
  - [ ] Update port map: Control10-14 → Control1-5
  - [ ] Update signal extraction: Control10-14 → Control1-5
  - [ ] Update documentation comments
- [ ] **1.4** Update `volo_common_pkg.vhd` → `custom_inst_common_pkg.vhd`
  - [ ] Rename package: `volo_common_pkg` → `custom_inst_common_pkg`
  - [ ] Update BRAM protocol comments: Control10-14 → Control1-5
  - [ ] Update app register comments: CR20-30 → CR6-15
- [ ] **1.5** Update templates
  - [ ] Rename `volo_shim_template.vhd` → `custom_inst_shim_template.vhd`
  - [ ] Update template comments: CustomWrapper → SimpleCustomInstrument
  - [ ] Update register range comments: CR20-30 → CR6-15
  - [ ] Update entity instantiation: `volo_main` → `custom_inst_main`
  - [ ] Rename `volo_main_template.vhd` → `custom_inst_main_template.vhd`
  - [ ] Update template comments

### Phase 2: Python Models

- [ ] **2.1** Rename directory: `models/volo/` → `models/custom_inst/`
- [ ] **2.2** Update `volo_app.py` → `custom_inst_app.py`
  - [ ] Rename class: `VoloApp` → `CustomInstApp`
  - [ ] Update register validation: max 11 → max 10
  - [ ] Update template paths: `shared/volo/templates` → `shared/custom_inst/templates`
  - [ ] Update generated file naming: `_volo_shim.vhd` → `_custom_inst_shim.vhd`
  - [ ] Update all docstrings and comments
  - [ ] Update module docstring
- [ ] **2.3** Update `app_register.py`
  - [ ] Update cr_number field: ge=20, le=30 → ge=6, le=15
  - [ ] Update cr_number validator: 20-30 → 6-15
  - [ ] Update docstrings
- [ ] **2.4** Update `__init__.py`
  - [ ] Update import: `volo_app` → `custom_inst_app`
  - [ ] Update export: `VoloApp` → `CustomInstApp`
  - [ ] Update module docstring

### Phase 3: Code Generator Tool

- [ ] **3.1** Rename file: `tools/generate_volo_app.py` → `tools/generate_custom_inst.py`
- [ ] **3.2** Update imports
  - [ ] Change: `from models.volo import VoloApp` → `from models.custom_inst import CustomInstApp`
- [ ] **3.3** Update CLI
  - [ ] Update banner text
  - [ ] Update help text
  - [ ] Update examples in epilog
- [ ] **3.4** Update console messages
  - [ ] Update "Loading VoloApp" → "Loading CustomInstApp"
  - [ ] Update all user-facing messages

### Phase 4: Application-Specific Files

- [ ] **4.1** Regenerate DS1140_PD VHDL files
  - [ ] Update `DS1140_PD_app.yaml`: cr_number 20-28 → 6-14
  - [ ] Run: `python tools/generate_custom_inst.py --config DS1140_PD_app.yaml --output VHDL/`
  - [ ] Review generated `DS1140_PD_custom_inst_shim.vhd`
  - [ ] Migrate `DS1140_PD_volo_main.vhd` → `DS1140_PD_custom_inst_main.vhd` (or regenerate template)
- [ ] **4.2** Update DS1120_PD if needed (or mark as legacy)

### Phase 5: Testing Infrastructure

- [ ] **5.1** Create CustomInstrument test stub
  - [ ] Create `VHDL/CustomInstrument_test_stub.vhd` (similar to CustomWrapper_test_stub.vhd)
  - [ ] Define `SimpleCustomInstrument` entity with 16 control registers
- [ ] **5.2** Update CocotB tests
  - [ ] Update `tests/conftest.py`: CustomWrapper → SimpleCustomInstrument
  - [ ] Update test fixtures to use Control0-15
  - [ ] Update BRAM loader tests: Control10-14 → Control1-5
  - [ ] Update app register tests: Control20-30 → Control6-15
- [ ] **5.3** Run test suite
  - [ ] Verify all tests pass with new entity

### Phase 6: Documentation

- [ ] **6.1** Update CLAUDE.md
  - [ ] Update VoloApp references → CustomInstApp
  - [ ] Update register allocation documentation
  - [ ] Update slash command examples if needed
- [ ] **6.2** Update README.md
  - [ ] Update code generator examples
  - [ ] Update register map documentation
- [ ] **6.3** Update reference docs
  - [ ] Mark old VOLO_APP_DESIGN.md as legacy or update
  - [ ] Update any architecture diagrams
- [ ] **6.4** Create migration guide (for historical reference)
  - [ ] Document the CustomWrapper → CustomInstrument transition
  - [ ] Include register mapping conversion table

### Phase 7: Cleanup

- [ ] **7.1** Remove legacy files from feature branch
  - [ ] Consider removing old `shared/volo/` if fully migrated
  - [ ] Consider removing old `models/volo/` if fully migrated
  - [ ] Keep old DS1120_PD files for reference or mark as legacy
- [ ] **7.2** Update .gitignore if needed
- [ ] **7.3** Final review
  - [ ] Grep for remaining "volo" references that should be "custom_inst"
  - [ ] Grep for remaining "CustomWrapper" references
  - [ ] Grep for remaining "Control20" or "Control30" references

---

## Testing Strategy

### Unit Tests

1. **Python Model Tests**
   - [ ] Test `CustomInstApp` loads from YAML
   - [ ] Test register validation: max 10 registers
   - [ ] Test cr_number validation: 6-15 range
   - [ ] Test template generation produces valid VHDL
   - [ ] Test file naming: `_custom_inst_shim.vhd`, `_custom_inst_main.vhd`

2. **VHDL Syntax Tests**
   - [ ] Test `MCC_TOP_custom_inst_loader.vhd` compiles with GHDL
   - [ ] Test `custom_inst_bram_loader.vhd` compiles
   - [ ] Test generated shim files compile
   - [ ] Test entity `SimpleCustomInstrument` can be instantiated

### Integration Tests

1. **Code Generation Tests**
   - [ ] Run `generate_custom_inst.py` on DS1140_PD_app.yaml
   - [ ] Verify generated files compile with GHDL
   - [ ] Verify port map connects correctly

2. **CocotB Tests**
   - [ ] Test BRAM loader FSM with Control1-5
   - [ ] Test VOLO_READY extraction from Control0
   - [ ] Test app register routing: Control6-15 → app_reg_6..15
   - [ ] Test DS1140_PD FSM with new register map

3. **End-to-End Tests**
   - [ ] Build DS1140_PD with new architecture
   - [ ] Simulate full system in CocotB
   - [ ] Verify MCC I/O routing works (InputA/B/C, OutputA/B/C)

### Validation Tests

1. **Register Map Validation**
   - [ ] Manually verify Control0[31:29] = VOLO_READY bits
   - [ ] Manually verify Control1-5 = BRAM loader
   - [ ] Manually verify Control6-15 = app registers
   - [ ] Verify DS1140_PD uses only 9 registers (fits in 10 limit)

2. **Backward Compatibility Tests** (for reference)
   - [ ] Document differences between old and new register maps
   - [ ] Create conversion table: CR20-30 → CR6-15

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Breaking existing designs** | High | High | Clean break strategy - keep legacy on `main` branch |
| **Register limit too restrictive** | Medium | Low | DS1140_PD uses 9 regs (fits in 10 limit), careful planning for future apps |
| **BRAM loader issues** | High | Medium | Thorough testing of Control1-5 FSM, keep protocol identical |
| **Missed renames** | Low | Medium | Comprehensive grep for "volo", "CustomWrapper", "Control20-30" |
| **Template generation bugs** | Medium | Medium | Test code generator extensively before deploying |
| **CocotB test failures** | Medium | High | Update tests incrementally, verify each component |

---

## Implementation Prompt

See `CUSTOM_INSTRUMENT_IMPLEMENTATION_PROMPT.md` for a detailed prompt that can be used to execute this migration plan.

---

## Success Criteria

The migration is considered complete when:

1. ✅ All files renamed from `volo` → `custom_inst`
2. ✅ Entity changed from `CustomWrapper` → `SimpleCustomInstrument`
3. ✅ Register map updated: Control0 (VOLO), Control1-5 (BRAM), Control6-15 (app)
4. ✅ Python models support max 10 app registers with CR6-15 range
5. ✅ Code generator creates `_custom_inst_shim.vhd` and `_custom_inst_main.vhd` files
6. ✅ DS1140_PD successfully regenerated with new architecture
7. ✅ All VHDL files compile with GHDL
8. ✅ All CocotB tests pass
9. ✅ Documentation updated to reflect new naming and architecture
10. ✅ No references to legacy "volo" or "CustomWrapper" in feature branch (except historical docs)

---

## Timeline Estimate

| Phase | Estimated Time | Notes |
|-------|----------------|-------|
| Phase 1: Core Infrastructure | 2-3 hours | VHDL file updates, most critical |
| Phase 2: Python Models | 1-2 hours | Straightforward rename and validation updates |
| Phase 3: Code Generator Tool | 1 hour | Simple import and message updates |
| Phase 4: Application Files | 1 hour | Regenerate DS1140_PD |
| Phase 5: Testing Infrastructure | 2-3 hours | CocotB test updates, debugging |
| Phase 6: Documentation | 1 hour | Update docs and examples |
| Phase 7: Cleanup | 30 minutes | Final grep and review |
| **Total** | **8-11 hours** | Can be broken into smaller sessions |

---

## References

- **MCC Documentation**: CustomWrapper → SimpleCustomInstrument entity transition
- **Current VHDL Files**: `VHDL/CustomInstrument.vhd` (new entity definition)
- **Current Architecture Docs**: `docs/VOLO_APP_DESIGN.md` (legacy, to be updated)
- **Python Models**: `models/volo/` (to be migrated to `models/custom_inst/`)
- **Code Generator**: `tools/generate_volo_app.py` (to be migrated)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-29
**Author**: vmars20
**Status**: Ready for Implementation
