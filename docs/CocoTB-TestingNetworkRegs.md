# CocotB Testing Plan: Network Register Handshaking

**Goal:** Validate atomic register update handshaking protocol (HandShakeProtocol.md v2.0)
**Testing Framework:** CocotB with Progressive Testing (P1/P2 levels)
**Reference:** `docs/COCOTB_PATTERNS.md`, `docs/BasicNetworkRegSafety_plan.md`
**Date:** 2025-01-31

---

## Overview

This document describes the CocotB test strategy for validating the `ready_for_updates` handshaking protocol. Tests are organized in progressive levels (P1/P2) following established patterns.

**What we're testing:**
1. **Shim layer** gates register updates based on `ready_for_updates` signal
2. **Main layer** controls when updates are safe via FSM states
3. **Reset behavior** loads YAML-defined default values
4. **Atomic updates** - all registers latch together in same cycle
5. **Integration** - DS1140_PD FSM prevents mid-operation glitches

---

## Test Organization

### Directory Structure

```
tests/
├── handshake_tests/                      # NEW test suite
│   ├── __init__.py
│   ├── handshake_constants.py            # Shared constants
│   └── test_fixtures.py                  # Shared test utilities
├── test_handshake_shim_progressive.py    # Shim layer tests
├── test_handshake_integration.py         # Integration tests
└── test_ds1140_pd_handshake.py          # DS1140_PD-specific tests
```

### Test Hierarchy

```
P1 Tests (Essential - Fast)
├── Shim Layer
│   ├── Gates updates when ready='0'
│   ├── Applies updates when ready='1'
│   └── Loads defaults on reset
└── Integration
    └── Simple always-ready pattern works

P2 Tests (Comprehensive)
├── Shim Layer
│   ├── Atomic multi-register updates
│   ├── Rapid ready toggling
│   └── Network writes while gate closed
└── Integration
    ├── FSM-gated pattern (DS1140_PD)
    └── Lock config during critical states
```

---

## Test Suite 1: Shim Layer Tests

**File:** `tests/test_handshake_shim_progressive.py`

### Test Configuration

**Constants file:** `tests/handshake_tests/handshake_constants.py`

```python
"""Constants for handshaking protocol tests"""
from pathlib import Path

MODULE_NAME = "handshake_shim"

# HDL sources
PROJECT_ROOT = Path(__file__).parent.parent.parent
VHDL_DIR = PROJECT_ROOT / "VHDL"
SHARED_DIR = PROJECT_ROOT / "shared" / "custom_inst"

HDL_SOURCES = [
    SHARED_DIR / "custom_inst_common_pkg.vhd",
    VHDL_DIR / "test_shim_handshake.vhd",  # Test fixture (to be created)
]

HDL_TOPLEVEL = "test_shim_handshake"  # Lowercase!

# Test timing
class TestTiming:
    """Clock and timing parameters"""
    CLOCK_PERIOD_NS = 10  # 100MHz
    RESET_CYCLES = 2
    SETTLE_CYCLES = 1

    P1_WAIT_CYCLES = 5    # P1: Short waits
    P2_WAIT_CYCLES = 20   # P2: Longer validation

# Test values
class TestValues:
    """Register test values"""
    # Intensity values (16-bit signed)
    INTENSITY_DEFAULT = 0x2666  # 9830 (2.0V default from HandShakeProtocol.md)
    INTENSITY_NEW_1   = 0x3DCF  # 15823 (2.4V from timing diagram)
    INTENSITY_NEW_2   = 0x1999  # 6553 (1.0V)

    # Threshold values (16-bit signed)
    THRESHOLD_DEFAULT = 0x2E0E  # 11796 (2.4V default)
    THRESHOLD_NEW_1   = 0x3333  # 13107 (2.67V)

    # Control register packing (CR6 = app_reg_6)
    # Format: CR[31:16] = intensity, CR[15:0] = unused
    @staticmethod
    def pack_cr6(intensity: int) -> int:
        """Pack intensity into CR6 format"""
        return (intensity << 16) & 0xFFFF_0000

    @staticmethod
    def pack_cr7(threshold: int) -> int:
        """Pack threshold into CR7 format"""
        return (threshold << 16) & 0xFFFF_0000

# Error messages
class ErrorMessages:
    UPDATE_WHEN_NOT_READY = "Shim updated when ready='0'! Expected {}, got {} after {} cycles"
    NO_UPDATE_WHEN_READY = "Shim did not update when ready='1'! Expected {}, got {}"
    DEFAULT_NOT_LOADED = "Default not loaded on reset! Expected {:#06x}, got {:#06x}"
    NON_ATOMIC_UPDATE = "Registers did not update atomically! intensity updated but threshold did not"
    UNEXPECTED_CHANGE = "Signal changed unexpectedly from {} to {} while gate closed"
```

---

### P1 Tests (Essential)

**Class:** `HandshakeShimTests(TestBase)`

```python
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from handshake_tests.handshake_constants import *


class HandshakeShimTests(TestBase):
    """Progressive tests for shim layer handshaking"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        # Start clock
        cocotb.start_soon(Clock(
            self.dut.Clk,
            TestTiming.CLOCK_PERIOD_NS,
            units="ns"
        ).start())

        # Reset
        self.dut.Reset.value = 1
        self.dut.ready_for_updates.value = 0
        self.dut.app_reg_6.value = 0
        self.dut.app_reg_7.value = 0
        await ClockCycles(self.dut.Clk, TestTiming.RESET_CYCLES)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        self.log("Setup complete", VerbosityLevel.VERBOSE)

    # ========================================================================
    # P1 Tests - Essential Functionality
    # ========================================================================

    async def run_p1_basic(self):
        """P1: Essential shim handshaking tests"""
        await self.setup()

        await self.test(
            "P1.1: Shim gates updates when ready='0'",
            self.test_gates_when_not_ready
        )

        await self.test(
            "P1.2: Shim applies updates when ready='1'",
            self.test_updates_when_ready
        )

        await self.test(
            "P1.3: Reset loads default values",
            self.test_reset_defaults
        )

    async def test_gates_when_not_ready(self):
        """Verify shim holds values when ready_for_updates='0'"""

        # Gate is CLOSED (ready='0')
        self.dut.ready_for_updates.value = 0
        await ClockCycles(self.dut.Clk, TestTiming.SETTLE_CYCLES)

        # Record initial value (should be default from reset)
        initial_intensity = int(self.dut.intensity.value)
        self.log(f"Initial intensity: {initial_intensity:#06x}", VerbosityLevel.VERBOSE)

        # Write new value to CR6 (app_reg_6)
        new_cr6 = TestValues.pack_cr6(TestValues.INTENSITY_NEW_1)
        self.dut.app_reg_6.value = new_cr6
        self.log(f"Writing CR6={new_cr6:#010x}", VerbosityLevel.VERBOSE)

        # Wait and verify NO change
        await ClockCycles(self.dut.Clk, TestTiming.P1_WAIT_CYCLES)

        current_intensity = int(self.dut.intensity.value)
        assert current_intensity == initial_intensity, \
            ErrorMessages.UPDATE_WHEN_NOT_READY.format(
                initial_intensity, current_intensity, TestTiming.P1_WAIT_CYCLES
            )

        self.log("✓ Gate held values while ready='0'", VerbosityLevel.NORMAL)

    async def test_updates_when_ready(self):
        """Verify shim latches values when ready_for_updates='1'"""

        # Write value to CR6
        new_intensity = TestValues.INTENSITY_NEW_1
        self.dut.app_reg_6.value = TestValues.pack_cr6(new_intensity)
        self.dut.ready_for_updates.value = 0  # Gate closed initially
        await ClockCycles(self.dut.Clk, 2)

        # Open gate
        self.dut.ready_for_updates.value = 1
        await RisingEdge(self.dut.Clk)

        # Verify update occurred
        current_intensity = int(self.dut.intensity.value)
        assert current_intensity == new_intensity, \
            ErrorMessages.NO_UPDATE_WHEN_READY.format(new_intensity, current_intensity)

        self.log(f"✓ Shim updated to {current_intensity:#06x} when ready='1'",
                 VerbosityLevel.NORMAL)

    async def test_reset_defaults(self):
        """Verify reset loads YAML-defined defaults"""

        # Write non-default values
        self.dut.app_reg_6.value = 0xFFFF_FFFF
        self.dut.app_reg_7.value = 0xFFFF_FFFF
        self.dut.ready_for_updates.value = 1
        await ClockCycles(self.dut.Clk, 2)

        # Reset
        self.dut.Reset.value = 1
        await RisingEdge(self.dut.Clk)

        # Verify defaults loaded (from HandShakeProtocol.md example)
        intensity_default = int(self.dut.intensity.value)
        threshold_default = int(self.dut.threshold.value)

        assert intensity_default == TestValues.INTENSITY_DEFAULT, \
            ErrorMessages.DEFAULT_NOT_LOADED.format(
                TestValues.INTENSITY_DEFAULT, intensity_default
            )

        assert threshold_default == TestValues.THRESHOLD_DEFAULT, \
            ErrorMessages.DEFAULT_NOT_LOADED.format(
                TestValues.THRESHOLD_DEFAULT, threshold_default
            )

        self.log(
            f"✓ Defaults loaded: intensity={intensity_default:#06x}, "
            f"threshold={threshold_default:#06x}",
            VerbosityLevel.NORMAL
        )


@cocotb.test()
async def test_handshake_shim(dut):
    """CocotB entry point for shim handshaking tests"""
    tester = HandshakeShimTests(dut)
    await tester.run_all_tests()
```

---

### P2 Tests (Comprehensive)

**Add to same class:**

```python
    # ========================================================================
    # P2 Tests - Comprehensive Validation
    # ========================================================================

    async def run_p2_intermediate(self):
        """P2: Comprehensive shim tests"""
        await self.setup()

        await self.test(
            "P2.1: Atomic multi-register updates",
            self.test_atomic_updates
        )

        await self.test(
            "P2.2: Network writes while gate closed are held",
            self.test_multiple_writes_gated
        )

        await self.test(
            "P2.3: Rapid ready toggling",
            self.test_rapid_toggling
        )

    async def test_atomic_updates(self):
        """Verify all registers update together in same cycle"""

        # Set different values in CR6 and CR7
        new_intensity = TestValues.INTENSITY_NEW_1
        new_threshold = TestValues.THRESHOLD_NEW_1

        self.dut.app_reg_6.value = TestValues.pack_cr6(new_intensity)
        self.dut.app_reg_7.value = TestValues.pack_cr7(new_threshold)
        self.dut.ready_for_updates.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # Record pre-update values
        old_intensity = int(self.dut.intensity.value)
        old_threshold = int(self.dut.threshold.value)

        # Open gate - both should update in SAME cycle
        self.dut.ready_for_updates.value = 1
        await RisingEdge(self.dut.Clk)

        # Verify BOTH updated (atomic)
        current_intensity = int(self.dut.intensity.value)
        current_threshold = int(self.dut.threshold.value)

        assert current_intensity == new_intensity and current_threshold == new_threshold, \
            ErrorMessages.NON_ATOMIC_UPDATE

        self.log(
            f"✓ Atomic update: both intensity and threshold updated in same cycle",
            VerbosityLevel.NORMAL
        )

    async def test_multiple_writes_gated(self):
        """Verify only LATEST value is latched when gate opens"""

        self.dut.ready_for_updates.value = 0
        await ClockCycles(self.dut.Clk, 1)

        # Write sequence while gate CLOSED
        self.dut.app_reg_6.value = TestValues.pack_cr6(TestValues.INTENSITY_NEW_1)
        await ClockCycles(self.dut.Clk, 2)

        self.dut.app_reg_6.value = TestValues.pack_cr6(TestValues.INTENSITY_NEW_2)
        await ClockCycles(self.dut.Clk, 2)

        # Open gate - should latch LATEST value (NEW_2)
        self.dut.ready_for_updates.value = 1
        await RisingEdge(self.dut.Clk)

        current = int(self.dut.intensity.value)
        assert current == TestValues.INTENSITY_NEW_2, \
            f"Expected latest value {TestValues.INTENSITY_NEW_2:#06x}, got {current:#06x}"

        self.log("✓ Latest value latched (no buffering)", VerbosityLevel.NORMAL)

    async def test_rapid_toggling(self):
        """Verify shim handles rapid ready toggling correctly"""

        for i in range(5):
            # Set value
            value = TestValues.INTENSITY_DEFAULT + (i * 100)
            self.dut.app_reg_6.value = TestValues.pack_cr6(value)

            # Ready high for 1 cycle
            self.dut.ready_for_updates.value = 1
            await RisingEdge(self.dut.Clk)

            # Verify update
            current = int(self.dut.intensity.value)
            assert current == value, \
                f"Iteration {i}: expected {value:#06x}, got {current:#06x}"

            # Ready low for 1 cycle
            self.dut.ready_for_updates.value = 0
            await RisingEdge(self.dut.Clk)

        self.log("✓ Shim handled rapid ready toggling correctly", VerbosityLevel.NORMAL)
```

---

## Test Suite 2: Integration Tests

**File:** `tests/test_handshake_integration.py`

### Test Fixture: Simple Always-Ready Pattern

**VHDL Test Fixture:** `VHDL/test_main_always_ready.vhd`

```vhdl
-- Simple test fixture: Always-ready pattern (Pattern A)
entity test_main_always_ready is
    port (
        Clk     : in  std_logic;
        Reset   : in  std_logic;
        Enable  : in  std_logic;

        ready_for_updates : out std_logic;

        intensity : in  signed(15 downto 0);
        threshold : in  signed(15 downto 0);

        -- Outputs for verification
        intensity_out : out signed(15 downto 0);
        threshold_out : out signed(15 downto 0)
    );
end test_main_always_ready;

architecture rtl of test_main_always_ready is
begin
    -- Pattern A: Always ready
    ready_for_updates <= '1';

    -- Simple pass-through for verification
    intensity_out <= intensity;
    threshold_out <= threshold;
end architecture;
```

### P1 Integration Test

```python
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from handshake_tests.handshake_constants import *


class HandshakeIntegrationTests(TestBase):
    """Integration tests for shim + main handshaking"""

    def __init__(self, dut):
        super().__init__(dut, "handshake_integration")

    async def setup(self):
        """Common setup"""
        cocotb.start_soon(Clock(self.dut.Clk, 10, units="ns").start())

        self.dut.Reset.value = 1
        self.dut.Enable.value = 1
        self.dut.Control6.value = 0
        self.dut.Control7.value = 0
        await ClockCycles(self.dut.Clk, 2)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

    async def run_p1_basic(self):
        """P1: Basic integration tests"""
        await self.setup()

        await self.test(
            "P1.1: Always-ready pattern works",
            self.test_always_ready_pattern
        )

    async def test_always_ready_pattern(self):
        """Verify Pattern A (always ready) allows immediate updates"""

        # Write to CR6
        new_value = TestValues.INTENSITY_NEW_1
        self.dut.Control6.value = TestValues.pack_cr6(new_value)

        # Should update immediately (ready is always '1')
        await RisingEdge(self.dut.Clk)

        # Verify main app received update
        current = int(self.dut.intensity_out.value)
        assert current == new_value, \
            f"Always-ready pattern failed: expected {new_value:#06x}, got {current:#06x}"

        self.log("✓ Always-ready pattern (Pattern A) working", VerbosityLevel.NORMAL)


@cocotb.test()
async def test_handshake_integration(dut):
    """CocotB entry point for integration tests"""
    tester = HandshakeIntegrationTests(dut)
    await tester.run_all_tests()
```

---

## Test Suite 3: DS1140_PD FSM-Gated Tests

**File:** `tests/test_ds1140_pd_handshake.py`

### P1 Test: FSM Locks Config During ARMED State

```python
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_base import TestBase, VerbosityLevel
from handshake_tests.handshake_constants import *


class DS1140PDHandshakeTests(TestBase):
    """DS1140_PD FSM-gated handshaking tests"""

    def __init__(self, dut):
        super().__init__(dut, "ds1140_pd_handshake")

    async def setup(self):
        """Setup DS1140_PD test environment"""
        cocotb.start_soon(Clock(self.dut.Clk, 10, units="ns").start())

        # Reset
        self.dut.Reset.value = 1
        await ClockCycles(self.dut.Clk, 2)
        self.dut.Reset.value = 0
        await RisingEdge(self.dut.Clk)

        # Initialize control registers
        self.dut.Control6.value = TestValues.pack_cr6(TestValues.INTENSITY_DEFAULT)
        self.dut.Control7.value = TestValues.pack_cr7(TestValues.THRESHOLD_DEFAULT)
        await ClockCycles(self.dut.Clk, 2)

    async def run_p1_basic(self):
        """P1: Essential FSM gating tests"""
        await self.setup()

        await self.test(
            "P1.1: FSM locks config when ARMED",
            self.test_fsm_locks_during_armed
        )

    async def test_fsm_locks_during_armed(self):
        """Verify DS1140_PD locks config when entering ARMED state"""

        # Verify initial state: IDLE (ready='1')
        initial_ready = int(self.dut.ready_for_updates.value)
        assert initial_ready == 1, f"Initial ready should be 1, got {initial_ready}"

        # Record initial intensity
        old_intensity = int(self.dut.intensity.value)
        self.log(f"Initial intensity: {old_intensity:#06x}", VerbosityLevel.VERBOSE)

        # Arm the probe (transitions FSM to ARMED)
        self.dut.arm_probe.value = 1
        await RisingEdge(self.dut.Clk)
        self.dut.arm_probe.value = 0
        await ClockCycles(self.dut.Clk, 2)

        # FSM should lock config (ready='0')
        current_ready = int(self.dut.ready_for_updates.value)
        assert current_ready == 0, \
            f"Config not locked in ARMED state! ready={current_ready}"

        self.log("✓ FSM locked config (ready='0')", VerbosityLevel.VERBOSE)

        # Try to change intensity (should be blocked by shim)
        new_intensity = TestValues.INTENSITY_NEW_1
        self.dut.Control6.value = TestValues.pack_cr6(new_intensity)
        await ClockCycles(self.dut.Clk, 5)

        # Verify change was BLOCKED
        current_intensity = int(self.dut.intensity.value)
        assert current_intensity == old_intensity, \
            f"Config changed during ARMED! Old={old_intensity:#06x}, New={current_intensity:#06x}"

        self.log("✓ Config change blocked during ARMED state", VerbosityLevel.NORMAL)

        # TODO: Wait for FSM to return to IDLE and verify gate reopens
        # (Depends on DS1140_PD FSM timeout/trigger logic)


@cocotb.test()
async def test_ds1140_pd_handshake(dut):
    """CocotB entry point for DS1140_PD handshaking tests"""
    tester = DS1140PDHandshakeTests(dut)
    await tester.run_all_tests()
```

---

## Test Fixtures (VHDL)

### Fixture 1: Shim-Only Test Harness

**File:** `VHDL/test_shim_handshake.vhd`

```vhdl
-- Test harness for shim layer handshaking validation
-- Exposes shim internals for direct testing
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity test_shim_handshake is
    port (
        -- Clock and Reset
        Clk   : in  std_logic;
        Reset : in  std_logic;

        -- Handshaking control
        ready_for_updates : in  std_logic;

        -- Control register inputs (simulating network writes)
        app_reg_6 : in  std_logic_vector(31 downto 0);
        app_reg_7 : in  std_logic_vector(31 downto 0);

        -- Friendly signal outputs (for verification)
        intensity : out signed(15 downto 0);
        threshold : out signed(15 downto 0)
    );
end test_shim_handshake;

architecture rtl of test_shim_handshake is
begin
    -- Atomic register update process (from shim template)
    REGISTER_UPDATE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                -- Load defaults (from HandShakeProtocol.md)
                intensity <= to_signed(9830, 16);   -- 0x2666 (2.0V)
                threshold <= to_signed(11796, 16);  -- 0x2E0E (2.4V)
            elsif ready_for_updates = '1' then
                -- Latch current CR values
                intensity <= signed(app_reg_6(31 downto 16));
                threshold <= signed(app_reg_7(31 downto 16));
            end if;
            -- else: Hold previous values (gate closed)
        end if;
    end process;
end architecture;
```

### Fixture 2: Full Stack Test Harness

**File:** `VHDL/test_handshake_full_stack.vhd`

```vhdl
-- Full stack test: Loader → Shim → Main (always-ready pattern)
-- Tests complete handshaking flow
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity test_handshake_full_stack is
    port (
        Clk    : in  std_logic;
        Reset  : in  std_logic;
        Enable : in  std_logic;

        -- Control register inputs
        Control6 : in  std_logic_vector(31 downto 0);
        Control7 : in  std_logic_vector(31 downto 0);

        -- Outputs for verification
        ready_for_updates : out std_logic;
        intensity_out     : out signed(15 downto 0);
        threshold_out     : out signed(15 downto 0)
    );
end test_handshake_full_stack;

architecture rtl of test_handshake_full_stack is
    -- Shim → Main signals
    signal intensity : signed(15 downto 0);
    signal threshold : signed(15 downto 0);

    -- Main → Shim signal
    signal ready_internal : std_logic;
begin
    -- Shim layer (simplified)
    SHIM_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                intensity <= to_signed(9830, 16);
                threshold <= to_signed(11796, 16);
            elsif ready_internal = '1' then
                intensity <= signed(Control6(31 downto 16));
                threshold <= signed(Control7(31 downto 16));
            end if;
        end if;
    end process;

    -- Main layer (Pattern A: always ready)
    ready_internal <= '1';
    ready_for_updates <= ready_internal;

    -- Output verification
    intensity_out <= intensity;
    threshold_out <= threshold;
end architecture;
```

---

## Test Configuration

### Update `test_configs.py`

```python
# tests/test_configs.py

TESTS_CONFIG = {
    # ... existing tests ...

    # Handshaking protocol tests
    "handshake_shim": TestConfig(
        test_module="test_handshake_shim_progressive",
        sources=[
            shared_dir / "custom_inst" / "custom_inst_common_pkg.vhd",
            vhdl_dir / "test_shim_handshake.vhd",
        ],
        toplevel="test_shim_handshake",  # Lowercase!
        category="handshake",
    ),

    "handshake_integration": TestConfig(
        test_module="test_handshake_integration",
        sources=[
            shared_dir / "custom_inst" / "custom_inst_common_pkg.vhd",
            vhdl_dir / "test_handshake_full_stack.vhd",
        ],
        toplevel="test_handshake_full_stack",
        category="handshake",
    ),

    # NOTE: DS1140_PD handshake test added after Phase 4 complete
}
```

---

## Execution Plan

### Phase 1: Shim Tests (After 4A complete)

```bash
# Create test fixtures
# 1. Write VHDL/test_shim_handshake.vhd
# 2. Write tests/handshake_tests/handshake_constants.py
# 3. Write tests/test_handshake_shim_progressive.py

# Run P1 tests
uv run python tests/run.py handshake_shim

# Expected output (P1):
# T1: P1.1: Shim gates updates when ready='0'
#   ✓ PASS
# T2: P1.2: Shim applies updates when ready='1'
#   ✓ PASS
# T3: P1.3: Reset loads default values
#   ✓ PASS

# Run P2 tests
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py handshake_shim
```

### Phase 2: Integration Tests (After 4B complete)

```bash
# Create integration test
# 1. Write VHDL/test_handshake_full_stack.vhd
# 2. Write tests/test_handshake_integration.py

# Run test
uv run python tests/run.py handshake_integration
```

### Phase 3: DS1140_PD Tests (After app migration)

```bash
# After DS1140_PD implements FSM-gated ready logic
uv run python tests/run.py ds1140_pd_handshake
```

---

## Success Criteria

### Shim Layer Tests Pass When:
- ✅ P1.1: Updates blocked when `ready='0'` (verified over 5+ cycles)
- ✅ P1.2: Updates applied when `ready='1'` (single cycle)
- ✅ P1.3: Reset loads YAML defaults (intensity=0x2666, threshold=0x2E0E)
- ✅ P2.1: Multi-register updates are atomic (same cycle)
- ✅ P2.2: Only latest CR value latched (no buffering)
- ✅ P2.3: Rapid toggling handled correctly

### Integration Tests Pass When:
- ✅ P1.1: Always-ready pattern (Pattern A) allows immediate updates
- ✅ P2.1: Full stack (loader→shim→main) propagates updates correctly

### DS1140_PD Tests Pass When:
- ✅ P1.1: FSM locks config (`ready='0'`) in ARMED/FIRING states
- ✅ P1.2: Config changes blocked during locked states
- ✅ P2.1: Gate reopens when FSM returns to IDLE
- ✅ P2.2: Queued network writes applied after gate reopens

---

## Timeline

| Phase | Task | Time | Blocker |
|-------|------|------|---------|
| 1 | Create test fixtures (VHDL) | 30 min | Need Phase 4A complete |
| 2 | Write shim tests (P1) | 30 min | - |
| 3 | Write shim tests (P2) | 20 min | - |
| 4 | Write integration tests | 20 min | Need Phase 4B complete |
| 5 | Write DS1140_PD tests | 30 min | Need DS1140_PD FSM updated |
| **Total** | | **2 hours** | Phases 4A-4B complete |

---

## References

**Testing Framework:**
- `docs/COCOTB_PATTERNS.md` - CocotB patterns and conventions
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Progressive testing philosophy
- `tests/test_base.py` - TestBase class and utilities
- `tests/conftest.py` - Shared test utilities

**Specification:**
- `HandShakeProtocol.md` - Lines 106-165 (shim/main behavior)
- `docs/BasicNetworkRegSafety_plan.md` - Implementation plan

**Examples:**
- `tests/test_volo_clk_divider_progressive.py` - Complex progressive test
- `tests/test_volo_voltage_pkg_progressive.py` - Simple progressive test

---

## Appendix A: Test Output Examples

### Expected P1 Output (Minimal Verbosity)

```
Running handshake_shim tests...
T1: P1.1: Shim gates updates when ready='0'
  ✓ PASS
T2: P1.2: Shim applies updates when ready='1'
  ✓ PASS
T3: P1.3: Reset loads default values
  ✓ PASS

3/3 tests passed (100%)
```

### Expected P2 Output (Normal Verbosity)

```
Running handshake_shim tests (P2)...
T1: P1.1: Shim gates updates when ready='0'
  ✓ Gate held values while ready='0'
  ✓ PASS
T2: P1.2: Shim applies updates when ready='1'
  ✓ Shim updated to 0x3dcf when ready='1'
  ✓ PASS
T3: P1.3: Reset loads default values
  ✓ Defaults loaded: intensity=0x2666, threshold=0x2e0e
  ✓ PASS
T4: P2.1: Atomic multi-register updates
  ✓ Atomic update: both intensity and threshold updated in same cycle
  ✓ PASS
T5: P2.2: Network writes while gate closed are held
  ✓ Latest value latched (no buffering)
  ✓ PASS
T6: P2.3: Rapid ready toggling
  ✓ Shim handled rapid ready toggling correctly
  ✓ PASS

6/6 tests passed (100%)
```

---

## Appendix B: Debugging Tips

### Common Issues

**Issue 1: Signal not found**
```python
# Check signal exists before accessing
if hasattr(dut, 'ready_for_updates'):
    ready = dut.ready_for_updates.value
else:
    raise AttributeError("DUT missing ready_for_updates signal!")
```

**Issue 2: Timing mismatches**
```python
# Add extra settle cycle after reset
await ClockCycles(dut.Clk, TestTiming.RESET_CYCLES)
await RisingEdge(dut.Clk)  # Ensure clean edge
```

**Issue 3: Value packing errors**
```python
# Debug CR value packing
cr6_value = TestValues.pack_cr6(0x2666)
print(f"CR6 packed: {cr6_value:#010x}")  # Should be 0x2666_0000

# Extract and verify
extracted = (cr6_value >> 16) & 0xFFFF
assert extracted == 0x2666
```

---

**Status:** Ready to implement after Phase 4A-4B complete
**Next Step:** Create test fixtures once shim template is updated
**Estimated effort:** 2 hours
