# BasicNetworkRegSafety Implementation Plan

**Goal:** Implement atomic register update handshaking as specified in HandShakeProtocol.md
**Scope:** VHDL template updates only (Phases 4A-4B)
**Status:** Planning
**Date:** 2025-01-31

---

## Executive Summary

**Problem:** Current implementation uses direct combinatorial assignment from Control Registers to application signals. This means register values can change at any time during application operation, causing mid-operation glitches.

**Solution:** Implement gated latching in the shim layer controlled by a `ready_for_updates` signal from the main application logic.

**Reference:** `HandShakeProtocol.md` lines 106-140 (complete specification)

---

## Current State vs Target State

### Current Implementation (❌ UNSAFE)

**Shim Template** (`custom_inst_shim_template.vhd:117-119`):
```vhdl
-- Direct combinatorial assignment - NO GATING
{% for reg in registers %}
    {{ reg.friendly_name }} <= app_reg_{{ reg.cr_number }}{{ reg.bit_range }};
{% endfor %}
```

**Main Template** (`custom_inst_main_template.vhd`):
```vhdl
-- No handshaking interface defined
```

**Problems:**
- Network writes propagate immediately to application
- FSM cannot lock configuration during critical operations
- Glitches possible during ARMED/FIRING states
- No clean reset defaults

---

### Target Implementation (✅ SAFE)

**Shim Template:**
```vhdl
-- Gated latching process with reset defaults
process(Clk)
begin
  if rising_edge(Clk) then
    if Reset = '1' then
      -- Load defaults from YAML
      intensity <= to_signed(9830, 16);
      threshold <= to_signed(11796, 16);
      -- ... other defaults
    elsif ready_for_updates = '1' then
      -- Atomic update: latch all registers together
      intensity <= signed(app_reg_6(31 downto 16));
      threshold <= signed(app_reg_7(31 downto 16));
      -- ... other registers
    end if;
    -- else: Hold previous values (gate closed)
  end if;
end process;
```

**Main Template:**
```vhdl
-- Handshaking signal to control when updates are safe
signal ready_for_updates : std_logic;

-- FSM-controlled gating (example)
process(Clk)
begin
  if rising_edge(Clk) then
    case fsm_state is
      when IDLE | READY =>
        ready_for_updates <= '1';  -- Safe to reconfigure
      when ARMED | ACTIVE | CLEANUP =>
        ready_for_updates <= '0';  -- Lock configuration
    end case;
  end if;
end process;
```

**Benefits:**
- ✅ Atomic updates (all registers change together)
- ✅ Application controls when changes are safe
- ✅ No mid-operation glitches
- ✅ Clean reset behavior with YAML-defined defaults
- ✅ Spec-compliant with HandShakeProtocol.md v2.0

---

## Phase 4A: Shim Template Updates

**File:** `shared/custom_inst/templates/custom_inst_shim_template.vhd`

### Step 4A.1: Add ready_for_updates Port

**Location:** Shim entity port declaration (after line 51)

```vhdl
entity {{ app_name }}_custom_inst_shim is
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk         : in  std_logic;
        Reset       : in  std_logic;

        ------------------------------------------------------------------------
        -- VOLO Control Signals (from MCC_TOP_custom_inst_loader)
        ------------------------------------------------------------------------
        volo_ready  : in  std_logic;
        user_enable : in  std_logic;
        clk_enable  : in  std_logic;
        loader_done : in  std_logic;

        ------------------------------------------------------------------------
        -- Handshaking Protocol (NEW)
        -- Main application controls when register updates are safe
        ------------------------------------------------------------------------
        ready_for_updates : in  std_logic;  -- From main application

        -- ... existing ports continue ...
```

---

### Step 4A.2: Replace Combinatorial Assignment with Latching Process

**Location:** Lines 100-119 (Register Mapping section)

**DELETE:**
```vhdl
    ----------------------------------------------------------------------------
    -- Register Mapping: Control Registers → Friendly Signals
    --
    -- Extract appropriate bit ranges from raw Control Registers
    -- based on register type (COUNTER_8BIT, PERCENT, BUTTON)
    ----------------------------------------------------------------------------
{% for reg in registers %}
    {{ reg.friendly_name }} <= app_reg_{{ reg.cr_number }}{{ reg.bit_range }};  -- {{ reg.original_name }}
{% endfor %}
```

**REPLACE WITH:**
```vhdl
    ----------------------------------------------------------------------------
    -- Atomic Register Update Process
    --
    -- Implements gated latching controlled by ready_for_updates signal.
    -- When ready_for_updates='0', shim holds previous values (gate closed).
    -- When ready_for_updates='1', shim latches current CR values atomically.
    --
    -- Reference: HandShakeProtocol.md v2.0 (lines 106-122)
    ----------------------------------------------------------------------------
    REGISTER_UPDATE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                -- Load default values from YAML specification
                -- These ensure safe startup state before network writes
{% for reg in registers %}
                {{ reg.friendly_name }} <= {{ reg.default_value }};  -- {{ reg.original_name }}
{% endfor %}
            elsif ready_for_updates = '1' then
                -- Atomic update: Latch all registers together in same cycle
                -- Main application has signaled it's safe to apply changes
{% for reg in registers %}
                {{ reg.friendly_name }} <= app_reg_{{ reg.cr_number }}{{ reg.bit_range }};  -- {{ reg.original_name }}
{% endfor %}
            end if;
            -- else: Hold previous values (gate closed, main app is busy)
        end if;
    end process REGISTER_UPDATE_PROC;
```

---

### Step 4A.3: Update Main Instantiation

**Location:** Line 126-153 (APP_MAIN_INST instantiation)

**ADD** `ready_for_updates` to port map (after Enable port):

```vhdl
    APP_MAIN_INST: entity WORK.{{ app_name }}_custom_inst_main
        port map (
            -- Standard Control Signals
            Clk     => Clk,
            Reset   => Reset,
            Enable  => global_enable,
            ClkEn   => clk_enable,

            -- Handshaking Protocol (NEW)
            ready_for_updates => ready_for_updates,  -- To shim for gating updates

            -- Friendly Application Signals
{% for reg in registers %}
            {{ reg.friendly_name }} => {{ reg.friendly_name }},
{% endfor %}

            -- ... rest of port map unchanged ...
```

---

### Step 4A.4: Verification Steps

```bash
# 1. Verify template syntax (Jinja2)
python -c "from jinja2 import Template; Template(open('shared/custom_inst/templates/custom_inst_shim_template.vhd').read())"

# 2. Generate test shim file
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output /tmp/test_shim/ \
    --force

# 3. Compile with GHDL
ghdl -a --std=08 /tmp/test_shim/DS1140_PD_custom_inst_shim.vhd

# 4. Check for ready_for_updates signal
grep -n "ready_for_updates" /tmp/test_shim/DS1140_PD_custom_inst_shim.vhd
```

---

## Phase 4B: Main Template Updates

**File:** `shared/custom_inst/templates/custom_inst_main_template.vhd`

### Step 4B.1: Add ready_for_updates Port

**Location:** Main entity port declaration (after line 47)

```vhdl
entity {{ app_name }}_custom_inst_main is
    port (
        ------------------------------------------------------------------------
        -- Standard Control Signals
        -- Priority Order: Reset > ClkEn > Enable
        ------------------------------------------------------------------------
        Clk     : in  std_logic;
        Reset   : in  std_logic;  -- Active-high reset (forces safe state)
        Enable  : in  std_logic;  -- Functional enable (gates work)
        ClkEn   : in  std_logic;  -- Clock enable (freezes sequential logic)

        ------------------------------------------------------------------------
        -- Handshaking Protocol (NEW)
        -- Signal to shim layer when register updates are safe
        ------------------------------------------------------------------------
        ready_for_updates : out std_logic;  -- To shim layer

        -- ... existing ports continue ...
```

---

### Step 4B.2: Add Handshaking Documentation

**Location:** After line 102 (before TODO section)

```vhdl
    ----------------------------------------------------------------------------
    -- Handshaking Protocol
    --
    -- The ready_for_updates signal controls when the shim layer applies
    -- network register updates. Your application logic determines when
    -- configuration changes are safe to apply.
    --
    -- Two common patterns:
    --
    -- Pattern A: Always Ready (Simple Applications)
    -- ────────────────────────────────────────────
    -- Use when your application can safely handle configuration changes
    -- at any time (e.g., simple signal generators, filters).
    --
    --     ready_for_updates <= '1';  -- Always accept updates
    --
    --
    -- Pattern B: FSM-Gated (Complex Applications)
    -- ────────────────────────────────────────────
    -- Use when certain FSM states must lock configuration to prevent
    -- mid-operation glitches (e.g., EMFI probe firing, pulse generation).
    --
    --     signal fsm_state : state_t;
    --     signal ready_for_updates_reg : std_logic;
    --
    --     process(Clk)
    --     begin
    --         if rising_edge(Clk) then
    --             if Reset = '1' then
    --                 ready_for_updates_reg <= '1';  -- Safe at reset
    --             else
    --                 case fsm_state is
    --                     when IDLE | READY | WAITING =>
    --                         ready_for_updates_reg <= '1';  -- Safe states
    --
    --                     when ARMED | ACTIVE | FIRING | CLEANUP =>
    --                         ready_for_updates_reg <= '0';  -- Lock config
    --
    --                     when others =>
    --                         ready_for_updates_reg <= '1';  -- Safe default
    --                 end case;
    --             end if;
    --         end if;
    --     end process;
    --
    --     ready_for_updates <= ready_for_updates_reg;
    --
    --
    -- Important Notes:
    -- ────────────────
    -- 1. Updates are atomic: When ready='1', ALL registers update together
    -- 2. Shim holds values when ready='0': Main sees stable config
    -- 3. Network writes are NOT buffered: Latest CR value is latched
    -- 4. Default pattern: ready='1' (always safe, opt into gating)
    --
    -- Reference: HandShakeProtocol.md v2.0 (complete specification)
    ----------------------------------------------------------------------------

    ----------------------------------------------------------------------------
    -- TODO: Implement Your Application Logic Here
```

---

### Step 4B.3: Add Default Ready Implementation

**Location:** Before placeholder outputs (line 141)

```vhdl
    ----------------------------------------------------------------------------
    -- Default Handshaking Implementation
    --
    -- TODO: Customize for your application's needs
    --
    -- Default: Always ready (Pattern A)
    -- Change to FSM-gated (Pattern B) if you need to lock config during
    -- critical operations.
    ----------------------------------------------------------------------------
    ready_for_updates <= '1';  -- Default: Always accept updates

    -- TODO: If using Pattern B (FSM-gated), replace with FSM logic

    ----------------------------------------------------------------------------
    -- Placeholder Outputs
    -- TODO: Remove when implementing
    ----------------------------------------------------------------------------
    OutputA <= (others => '0');
    OutputB <= (others => '0');
```

---

### Step 4B.4: Verification Steps

```bash
# 1. Verify template syntax (Jinja2)
python -c "from jinja2 import Template; Template(open('shared/custom_inst/templates/custom_inst_main_template.vhd').read())"

# 2. Generate test main file
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output /tmp/test_main/ \
    --force

# 3. Compile with GHDL
ghdl -a --std=08 /tmp/test_main/DS1140_PD_custom_inst_main.vhd

# 4. Check for ready_for_updates signal
grep -n "ready_for_updates" /tmp/test_main/DS1140_PD_custom_inst_main.vhd
```

---

## Testing Strategy

### Unit Test: Shim Latching Behavior

**File:** `tests/test_handshake_shim.py` (NEW)

```python
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.clock import Clock

@cocotb.test()
async def test_shim_gates_updates_when_not_ready(dut):
    """Verify shim holds values when ready_for_updates='0'."""

    # Start clock
    cocotb.start_soon(Clock(dut.Clk, 10, units="ns").start())

    # Reset
    dut.Reset.value = 1
    dut.ready_for_updates.value = 0
    await ClockCycles(dut.Clk, 2)
    dut.Reset.value = 0
    await RisingEdge(dut.Clk)

    # Record initial value
    initial_value = dut.intensity.value

    # Write new value to CR6 while gate is CLOSED
    dut.app_reg_6.value = 0x1234_5678
    await ClockCycles(dut.Clk, 3)

    # Verify shim output did NOT change (gate closed)
    assert dut.intensity.value == initial_value, \
        f"Shim updated when ready='0'! Expected {initial_value}, got {dut.intensity.value}"

    # Open gate
    dut.ready_for_updates.value = 1
    await RisingEdge(dut.Clk)

    # Verify shim output DID update atomically
    expected = 0x5678  # Upper 16 bits of app_reg_6
    assert dut.intensity.value == expected, \
        f"Shim did not update when ready='1'! Expected {expected}, got {dut.intensity.value}"


@cocotb.test()
async def test_shim_loads_defaults_on_reset(dut):
    """Verify shim loads YAML default values on reset."""

    cocotb.start_soon(Clock(dut.Clk, 10, units="ns").start())

    # Set non-default values in CRs
    dut.app_reg_6.value = 0xFFFF_FFFF
    dut.app_reg_7.value = 0xFFFF_FFFF
    dut.ready_for_updates.value = 1
    await ClockCycles(dut.Clk, 2)

    # Reset
    dut.Reset.value = 1
    await RisingEdge(dut.Clk)

    # Verify defaults loaded (from YAML)
    # intensity default: to_signed(9830, 16) = 0x2666
    assert dut.intensity.value == 0x2666, \
        f"Default not loaded! Expected 0x2666, got {hex(dut.intensity.value)}"
```

---

### Integration Test: DS1140_PD FSM Gating

**File:** `tests/test_ds1140_pd_handshake.py` (NEW)

```python
@cocotb.test()
async def test_ds1140_locks_config_during_firing(dut):
    """Verify DS1140_PD locks config when FSM enters ARMED state."""

    # Setup
    cocotb.start_soon(Clock(dut.Clk, 10, units="ns").start())
    await reset_dut(dut)

    # Initial state: IDLE (ready='1')
    assert dut.ready_for_updates.value == 1

    # Arm the probe
    dut.arm_probe.value = 1
    await RisingEdge(dut.Clk)
    dut.arm_probe.value = 0

    # FSM should transition to ARMED and lock config
    await ClockCycles(dut.Clk, 2)
    assert dut.ready_for_updates.value == 0, \
        "Config not locked in ARMED state!"

    # Try to change intensity (should be ignored by shim)
    old_intensity = dut.intensity.value
    dut.Control6.value = 0x9999_9999
    await ClockCycles(dut.Clk, 3)

    # Verify change was blocked
    assert dut.intensity.value == old_intensity, \
        "Config changed during ARMED state!"

    # Fire completes, FSM returns to IDLE
    # (simulate trigger or timeout)
    await wait_for_idle(dut)

    # Verify gate reopened
    assert dut.ready_for_updates.value == 1, \
        "Config not unlocked after IDLE return!"
```

---

## Success Criteria

### Phase 4A Complete When:
- ✅ Shim template has `ready_for_updates` input port
- ✅ Combinatorial assignment replaced with latching process
- ✅ Reset branch loads YAML default values
- ✅ Main instantiation passes `ready_for_updates` signal
- ✅ Generated shim compiles with GHDL
- ✅ Test: Shim gates updates when `ready='0'`
- ✅ Test: Shim loads defaults on reset

### Phase 4B Complete When:
- ✅ Main template has `ready_for_updates` output port
- ✅ Handshaking patterns documented (Pattern A & B)
- ✅ Default implementation uses Pattern A (always ready)
- ✅ Generated main compiles with GHDL
- ✅ Test: Main can control shim gating behavior

---

## Out of Scope (Future Work)

**NOT included in this phase:**

1. **Python Model Updates** (Phase 4C)
   - Adding `default_value` field to AppRegister
   - YAML schema updates
   - Validation logic

2. **Code Generator Updates** (Phase 4D)
   - Default value rendering
   - Template context preparation
   - Type-based fallback defaults

3. **Full DS1140_PD Migration** (Phase 5)
   - FSM-gated ready logic implementation
   - Integration testing
   - Hardware validation

These will be addressed in subsequent phases after VHDL templates are validated.

---

## Timeline Estimate

| Task | Time | Notes |
|------|------|-------|
| 4A.1: Add ready port to shim | 5 min | Simple port addition |
| 4A.2: Replace with latching process | 15 min | Core logic change |
| 4A.3: Update main instantiation | 5 min | Port map addition |
| 4A.4: Verification | 5 min | GHDL compile check |
| 4B.1: Add ready port to main | 5 min | Simple port addition |
| 4B.2: Add documentation | 10 min | Pattern examples |
| 4B.3: Default implementation | 5 min | Simple assignment |
| 4B.4: Verification | 5 min | GHDL compile check |
| **Subtotal** | **55 min** | Template updates only |
| Testing | 30 min | Unit tests for gating |
| **Total** | **1.5 hours** | Phases 4A-4B complete |

---

## References

- **HandShakeProtocol.md** - Complete v2.0 specification (lines 1-282)
- **CUSTOM_INSTRUMENT_MIGRATION_PLAN.md** - Overall migration context
- **shared/custom_inst/templates/** - Current template files
- **docs/VHDL_COCOTB_LESSONS_LEARNED.md** - Testing best practices

---

**Status:** Ready for implementation
**Next Step:** Begin Phase 4A.1 (add ready_for_updates port to shim template)
**Blocker:** Need `default_value` in YAML (workaround: use type-based defaults)
