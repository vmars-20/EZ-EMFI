# 🚀 Creating a New VOLO Module - Human Guide

> **TL;DR**: Run `/new-module MyAwesomeModule` (slash command) or follow the manual steps below. Modules have 4 layers: common → datadef → core → top. Tests are progressive: P1 → P2 → P3.

---

## ⚡ Quick Start (Automated - Coming Soon!)

### Using Slash Command (Proposed)
```bash
# Create complete module structure with templates
/new-module PulseStar --type standard --category instruments

# Create VOLO app (special type)
/new-volo-app DS1121-PD --description "Next-gen EMFI driver"
```

### Manual Quick Start
```bash
# 1. Create module structure
mkdir -p modules/MyModule/{common,datadef,core,top}

# 2. Create test structure
mkdir -p tests/mymodule_tests

# 3. Add to build system
echo "MyModule" >> modules/MODULE_LIST

# 4. Run first test
uv run python tests/run.py mymodule
```

---

## 📐 Module Architecture

### Standard Module Structure
```
modules/MyModule/
├── common/       # Shared utilities, packages
├── datadef/      # Data structures, LUTs, constants
├── core/         # Pure logic (FSMs, algorithms)
└── top/          # Platform integration (MCC wrapper)
```

### Layer Responsibilities

| Layer | Purpose | Rules | Example Files |
|-------|---------|-------|---------------|
| **common/** | Shared utilities | Strict RTL | `mymodule_pkg.vhd` |
| **datadef/** | Data structures | Records OK | `mymodule_luts.vhd` |
| **core/** | Business logic | No platform code | `mymodule_fsm.vhd` |
| **top/** | MCC integration | Direct instantiation | `MyModule.vhd`, `Top.vhd` |

---

## 📝 Step-by-Step Manual Creation

### Step 1: Create Directory Structure
```bash
MODULE_NAME="MyAwesomeModule"
MODULE_PATH="modules/$MODULE_NAME"

# Create directories
mkdir -p $MODULE_PATH/{common,datadef,core,top}
mkdir -p tests/${MODULE_NAME,,}_tests  # lowercase for tests
```

### Step 2: Create Package (common/mymodule_pkg.vhd)
```vhdl
--------------------------------------------------------------------------------
-- MyAwesomeModule Package
-- Common types, constants, and utilities
--------------------------------------------------------------------------------
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package myawesomemodule_pkg is
    -- Constants
    constant DATA_WIDTH : natural := 16;

    -- FSM States (use std_logic_vector, not enums!)
    constant STATE_IDLE   : std_logic_vector(1 downto 0) := "00";
    constant STATE_ACTIVE : std_logic_vector(1 downto 0) := "01";
    constant STATE_DONE   : std_logic_vector(1 downto 0) := "10";

    -- Status register bits
    constant STATUS_READY_BIT  : natural := 0;
    constant STATUS_BUSY_BIT   : natural := 1;
    constant STATUS_FAULT_BIT  : natural := 7;  -- Always bit 7

end package;
```

### Step 3: Create Core Logic (core/mymodule_core.vhd)
```vhdl
--------------------------------------------------------------------------------
-- MyAwesomeModule Core
-- Pure algorithmic logic - no platform dependencies
--------------------------------------------------------------------------------
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.myawesomemodule_pkg.all;

entity myawesomemodule_core is
    port (
        -- Standard controls (MANDATORY order)
        clk     : in  std_logic;
        rst_n   : in  std_logic;  -- Active low reset
        enable  : in  std_logic;  -- Functional enable
        clk_en  : in  std_logic;  -- Clock enable

        -- Data interface
        data_in : in  std_logic_vector(DATA_WIDTH-1 downto 0);
        data_out: out std_logic_vector(DATA_WIDTH-1 downto 0);

        -- Status
        busy    : out std_logic;
        done    : out std_logic
    );
end entity;

architecture rtl of myawesomemodule_core is
    signal state : std_logic_vector(1 downto 0);
begin

    MAIN_FSM: process(clk, rst_n)
    begin
        if rst_n = '0' then
            state <= STATE_IDLE;
            data_out <= (others => '0');
            busy <= '0';
            done <= '0';
        elsif rising_edge(clk) then
            if clk_en = '1' then  -- CRITICAL: Check clock enable!
                if enable = '1' then
                    -- Your logic here
                    case state is
                        when STATE_IDLE =>
                            if data_in /= x"0000" then
                                state <= STATE_ACTIVE;
                                busy <= '1';
                            end if;
                        when STATE_ACTIVE =>
                            data_out <= data_in;  -- Example processing
                            state <= STATE_DONE;
                            busy <= '0';
                            done <= '1';
                        when STATE_DONE =>
                            state <= STATE_IDLE;
                            done <= '0';
                        when others =>
                            state <= STATE_IDLE;
                    end case;
                end if;
            end if;
        end if;
    end process;

end architecture;
```

### Step 4: Create Top-Level Integration (top/Top.vhd)
```vhdl
--------------------------------------------------------------------------------
-- MCC CustomWrapper Architecture for MyAwesomeModule
-- MCC provides the entity - we only write the architecture
--------------------------------------------------------------------------------
architecture MyAwesomeModule of CustomWrapper is
    -- MCC 3-bit control signals (MANDATORY!)
    signal mcc_ready     : std_logic;
    signal user_enable   : std_logic;
    signal clk_enable    : std_logic;
    signal global_enable : std_logic;
begin

    -- Extract 3-bit control (CRITICAL for operation!)
    mcc_ready     <= Control0(31);
    user_enable   <= Control0(30);
    clk_enable    <= Control0(29);  -- Without this, module FREEZES!
    global_enable <= mcc_ready and user_enable and clk_enable;

    -- Instantiate core
    -- Note: MCC provides InputA/B as signed(15 downto 0) - native ADC type
    CORE: entity WORK.myawesomemodule_core
        port map (
            clk      => Clk,
            rst_n    => not Reset,  -- Convert to active-low
            enable   => global_enable,
            clk_en   => clk_enable,
            data_in  => std_logic_vector(InputA),  -- Type conversion if needed
            data_out => std_logic_vector(OutputA),  -- Direct pass-through
            busy     => OutputB(0),  -- Pack status into lower bits
            done     => OutputB(1)
        );

    -- Pack unused output bits
    OutputB(15 downto 2) <= (others => '0');

end architecture;
```

---

## 🧪 Creating Tests

### Step 1: Create Test Constants
```python
# tests/mymodule_tests/mymodule_constants.py
from pathlib import Path

MODULE_NAME = "mymodule"
MODULE_PATH = Path("../modules/MyAwesomeModule")

HDL_SOURCES = [
    MODULE_PATH / "common" / "myawesomemodule_pkg.vhd",
    MODULE_PATH / "core" / "myawesomemodule_core.vhd",
]
HDL_TOPLEVEL = "myawesomemodule_core"  # Test core directly first

class TestValues:
    P1_TEST_CYCLES = 20   # Keep P1 fast!
    P2_TEST_CYCLES = 100
    P3_TEST_CYCLES = 1000
```

### Step 2: Create P1 Basic Test
```python
# tests/mymodule_tests/P1_mymodule_basic.py
import cocotb
from cocotb.triggers import ClockCycles
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from test_base import TestBase
from conftest import setup_clock, reset_active_low, run_with_timeout
from mymodule_tests.mymodule_constants import *

class MyModuleBasicTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def test_reset(self):
        """T1: Reset clears all outputs."""
        await setup_clock(self.dut)
        await reset_active_low(self.dut)

        assert self.dut.data_out.value == 0, "Output not cleared"
        assert self.dut.busy.value == 0, "Busy not cleared"

    async def test_basic_operation(self):
        """T2: Data passes through when enabled."""
        await setup_clock(self.dut)
        await reset_active_low(self.dut)

        self.dut.enable.value = 1
        self.dut.clk_en.value = 1
        self.dut.data_in.value = 0x1234

        await ClockCycles(self.dut.clk, 5)
        assert self.dut.data_out.value == 0x1234, "Data mismatch"

    async def run_p1_basic(self):
        await self.test("T1: Reset", self.test_reset)
        await self.test("T2: Basic operation", self.test_basic_operation)

@cocotb.test()
async def test_mymodule_p1(dut):
    async def test_logic():
        tester = MyModuleBasicTests(dut)
        await tester.run_p1_basic()
        tester.print_summary()

    await run_with_timeout(test_logic(), timeout_sec=5, test_name="MyModule P1")
```

---

## 🔧 Integration with Build System

### Add to Module List
```bash
echo "MyAwesomeModule" >> modules/MODULE_LIST
```

### Add Dependencies (if needed)
```makefile
# modules/Makefile.deps
MyAwesomeModule: clk_divider volo_common
```

### Test Your Module
```bash
# Compile VHDL
cd modules
make compile-single-module MODULE_NAME=MyAwesomeModule

# Run tests
cd ../tests
uv run python run.py mymodule
```

---

## ✅ Module Checklist

Before committing your module:

### Code Quality
- [ ] No enumeration types in RTL (use `std_logic_vector`)
- [ ] FSM states use constants, not enums
- [ ] Direct instantiation in top layer (`entity WORK.`)
- [ ] Standard control signal order: reset > clk_en > enable
- [ ] Status bit 7 = FAULT (sticky)
- [ ] MCC 3-bit control implemented (CR0[31:29])

### Structure
- [ ] 4 directories: common, datadef, core, top
- [ ] Package in common/
- [ ] Core logic separated from platform
- [ ] Top.vhd is architecture only (no entity)

### Tests
- [ ] P1 tests created (3-5 tests)
- [ ] Constants file created
- [ ] Tests run in <1 second for P1
- [ ] Output is <20 lines for P1

### Documentation
- [ ] Header comments in all files
- [ ] Register map documented in Top.vhd
- [ ] Test descriptions clear

---

## 🎯 Common Patterns

### Pattern: Clock Divider Integration
```vhdl
-- In your core
generic (
    DIVIDER_WIDTH : natural := 8
);
port (
    clk_div : in std_logic_vector(DIVIDER_WIDTH-1 downto 0);
    -- ...
);

-- Instantiate divider
DIV: entity WORK.clk_divider
    generic map (WIDTH => DIVIDER_WIDTH)
    port map (
        clk => clk,
        rst_n => rst_n,
        enable => enable,
        divider => clk_div,
        clk_out => internal_clk_en
    );
```

### Pattern: Status Register Assembly
```vhdl
-- In top layer
Status0 <= (
    7 => fault_flag,      -- Bit 7: FAULT
    6 => alarm_flag,      -- Bit 6: ALARM
    1 => busy,
    0 => ready,
    others => '0'
);
```

### Pattern: Safe Parameter Extraction
```vhdl
-- Avoid synthesis issues with slicing
process(Control1)
    variable temp : std_logic_vector(31 downto 0);
begin
    temp := Control1;
    param_high <= temp(31 downto 16);
    param_low  <= temp(15 downto 0);
end process;
```

---

## 🚫 Common Mistakes to Avoid

1. **Forgetting Clock Enable (Bit 29)**
   ```vhdl
   -- WRONG - Module will freeze!
   global_enable <= Control0(31) and Control0(30);

   -- CORRECT - Include bit 29
   global_enable <= Control0(31) and Control0(30) and Control0(29);
   ```

2. **Using Enums in RTL**
   ```vhdl
   -- WRONG
   type state_type is (IDLE, ACTIVE, DONE);

   -- CORRECT
   constant IDLE : std_logic_vector(1 downto 0) := "00";
   ```

3. **Component Declaration in Top**
   ```vhdl
   -- WRONG
   component mycore is...

   -- CORRECT
   CORE: entity WORK.mycore
   ```

---

## 🔮 Proposed Automation: Slash Commands

### `/new-module` Command (Proposed .claude/commands/new-module.md)
```markdown
Create a new VOLO module with complete structure and templates.

Usage: /new-module <name> [options]

Options:
  --type      standard|mcc|volo (default: standard)
  --category  Category folder name
  --with-tests Create P1/P2/P3 test structure

This will:
1. Create 4-layer directory structure
2. Generate template VHDL files
3. Create test structure with constants
4. Add to MODULE_LIST
5. Generate P1 test template
```

Would you like me to create this slash command implementation?

---

## 📚 Next Steps

1. **Start Simple**: Create core first, test it, then add MCC wrapper
2. **Test Early**: Write P1 tests as you develop
3. **Use Templates**: Copy from existing modules (PulseStar, SimpleWaveGen)
4. **Ask Questions**: Module architecture is strict but for good reasons

---

## 🎓 Learning Path

1. **First Module**: Start with something simple (counter, PWM)
2. **Study Examples**:
   - `clk_divider` - Simplest shared module
   - `PulseStar` - Clean MCC integration
   - `SimpleWaveGen` - Complex with validation
3. **Test Everything**: P1 tests catch 80% of issues

---

*Last Updated: 2025-01-27*
*Module Standard: VOLO Architecture v2.0*