# BasicNetworkRegSafety Implementation Prompt

**Date:** 2025-01-31
**Branch:** `feature/CustomInstrument`
**Task:** Implement atomic register update handshaking in VHDL templates
**Plan:** `docs/BasicNetworkRegSafety_plan.md`

---

## Quick Start

**Goal:** Add `ready_for_updates` handshaking signal to prevent mid-operation configuration changes.

**Files to modify:**
1. `shared/custom_inst/templates/custom_inst_shim_template.vhd`
2. `shared/custom_inst/templates/custom_inst_main_template.vhd`

**Time estimate:** 1.5 hours (template updates + basic testing)

---

## Context

### What We've Done (Phases 1-3)

✅ Renamed `volo` → `custom_inst` (mechanical renaming)
✅ Updated entity: `CustomWrapper` → `SimpleCustomInstrument`
✅ Updated register map: CR20-30 → CR6-15
✅ Updated Python models and code generator

**Commit:** `dd505cd` (feat: Complete Phase 1-3 of CustomInstrument migration)

### What We're Doing Now (Phase 4A-4B)

**Problem:** Current templates use direct combinatorial assignment from Control Registers to application signals. Network writes propagate immediately, causing potential glitches during FSM critical operations (e.g., EMFI firing).

**Solution:** Implement gated latching controlled by `ready_for_updates` signal from main application.

**Specification:** `HandShakeProtocol.md` (complete v2.0 architecture spec)

---

## The HandShakeProtocol Specification

**Key excerpt from HandShakeProtocol.md (lines 92-140):**

### Shim Layer Behavior (Target Implementation)

```vhdl
-- Shim → Main: Stable, latched values
signal intensity : out signed(15 downto 0);

-- Main → Shim: Safe update indicator
ready_for_updates : in std_logic;

-- Shim latching process
process(clk)
begin
  if rising_edge(clk) then
    if rst = '1' then
      -- Load defaults from YAML
      intensity <= to_signed(9830, 16);  -- 2.0V default
    elsif ready_for_updates = '1' then
      -- Update all latched outputs from current CR values
      intensity <= signed(app_reg_9(31 downto 16));
      threshold <= signed(app_reg_8(31 downto 16));
    end if;
    -- else: hold previous values (gate closed)
  end if;
end process;
```

### Main Application Pattern (Target Implementation)

```vhdl
-- Main controls when updates are safe
process(clk)
begin
  if rising_edge(clk) then
    case fsm_state is
      when IDLE | READY =>
        ready_for_updates <= '1';  -- Safe to reconfigure

      when ARMED | ACTIVE | CLEANUP =>
        ready_for_updates <= '0';  -- Lock configuration
    end case;
  end if;
end process;

-- Use signals directly (they're stable)
dac_output <= intensity;  -- No double-latching needed
```

**Key Properties:**
- No buffering: Shim always converts latest CR value
- Gated latching: Updates only when `ready='1'`
- Atomic updates: All registers update together in same cycle
- Stable outputs: Main sees constant values between updates

---

## Current Template State

### Shim Template (Lines 112-119)

**Current (UNSAFE):**
```vhdl
----------------------------------------------------------------------------
-- Register Mapping: Control Registers → Friendly Signals
----------------------------------------------------------------------------
{% for reg in registers %}
    {{ reg.friendly_name }} <= app_reg_{{ reg.cr_number }}{{ reg.bit_range }};
{% endfor %}
```

**Issues:**
- ❌ Direct combinatorial assignment
- ❌ No gating mechanism
- ❌ No reset defaults
- ❌ Network writes propagate immediately

### Main Template (No Handshaking)

**Current:**
- ❌ No `ready_for_updates` signal defined
- ❌ No handshaking interface
- ❌ No guidance for developers

---

## Implementation Tasks

### Phase 4A: Shim Template Updates

**File:** `shared/custom_inst/templates/custom_inst_shim_template.vhd`

#### Task 4A.1: Add ready_for_updates Port

**Location:** After line 51 (loader_done port)

**Add:**
```vhdl
------------------------------------------------------------------------
-- Handshaking Protocol
-- Main application controls when register updates are safe
------------------------------------------------------------------------
ready_for_updates : in  std_logic;  -- From main application
```

#### Task 4A.2: Replace Combinatorial Assignment

**Location:** Lines 112-119

**Delete entire section:**
```vhdl
----------------------------------------------------------------------------
-- Register Mapping: Control Registers → Friendly Signals
...
{% for reg in registers %}
    {{ reg.friendly_name }} <= app_reg_{{ reg.cr_number }}{{ reg.bit_range }};
{% endfor %}
```

**Replace with:**
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

#### Task 4A.3: Update Main Instantiation

**Location:** Line 131 (port map for APP_MAIN_INST)

**Add after Enable port:**
```vhdl
Enable  => global_enable,
ClkEn   => clk_enable,

-- Handshaking Protocol
ready_for_updates => ready_for_updates,  -- To shim for gating updates

-- Friendly Application Signals
```

---

### Phase 4B: Main Template Updates

**File:** `shared/custom_inst/templates/custom_inst_main_template.vhd`

#### Task 4B.1: Add ready_for_updates Port

**Location:** After line 47 (ClkEn port)

**Add:**
```vhdl
------------------------------------------------------------------------
-- Handshaking Protocol
-- Signal to shim layer when register updates are safe
------------------------------------------------------------------------
ready_for_updates : out std_logic;  -- To shim layer
```

#### Task 4B.2: Add Documentation Section

**Location:** After line 102 (before TODO section)

**Add complete handshaking documentation** (see plan document for full text):
- Pattern A: Always Ready (simple apps)
- Pattern B: FSM-Gated (complex apps)
- Usage examples and notes

#### Task 4B.3: Add Default Implementation

**Location:** Before placeholder outputs (line 141)

**Add:**
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
```

---

## Verification Steps

### After Each Template Modification

```bash
# 1. Verify Jinja2 syntax
python -c "from jinja2 import Template; Template(open('shared/custom_inst/templates/custom_inst_shim_template.vhd').read())"
python -c "from jinja2 import Template; Template(open('shared/custom_inst/templates/custom_inst_main_template.vhd').read())"

# 2. Generate test files (requires default_value in YAML - use workaround if needed)
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output /tmp/test_handshake/ \
    --force

# 3. Check generated files
ls -lh /tmp/test_handshake/
grep -n "ready_for_updates" /tmp/test_handshake/*.vhd
grep -n "REGISTER_UPDATE_PROC" /tmp/test_handshake/DS1140_PD_custom_inst_shim.vhd

# 4. Compile with GHDL (may fail if default_value not in YAML yet)
ghdl -a --std=08 shared/custom_inst/custom_inst_common_pkg.vhd
ghdl -a --std=08 /tmp/test_handshake/DS1140_PD_custom_inst_shim.vhd
ghdl -a --std=08 /tmp/test_handshake/DS1140_PD_custom_inst_main.vhd
```

---

## Known Issues / Workarounds

### Issue 1: default_value Not in YAML Yet

**Problem:** Templates reference `{{ reg.default_value }}` but Python models don't support this field yet.

**Workaround A (Type-based defaults):**
Modify template to use type-based defaults temporarily:

```vhdl
{% for reg in registers %}
    {% if reg.reg_type == 'BUTTON' %}
            {{ reg.friendly_name }} <= '0';  -- {{ reg.original_name }}
    {% elif reg.reg_type == 'COUNTER_8BIT' or reg.reg_type == 'COUNTER_16BIT' %}
            {{ reg.friendly_name }} <= (others => '0');  -- {{ reg.original_name }}
    {% else %}
            {{ reg.friendly_name }} <= (others => '0');  -- {{ reg.original_name }} [unknown type]
    {% endif %}
{% endfor %}
```

**Workaround B (Hardcode for testing):**
Use known DS1140_PD defaults for initial testing:

```vhdl
-- Hardcoded DS1140_PD defaults (temporary)
intensity <= to_signed(9830, 16);   -- CR6: 2.0V
threshold <= to_signed(11796, 16);  -- CR7: 2.4V
-- ... etc
```

**Permanent Fix (Phase 4C):**
Add `default_value` field to Python models and YAML schema.

---

## Testing Plan

### Minimal Verification (Phase 4A-4B only)

```bash
# 1. Templates compile without errors
uv run python tools/generate_custom_inst.py \
    --config DS1140_PD_app.yaml \
    --output /tmp/test/ \
    --force

# 2. Generated VHDL compiles
ghdl -a --std=08 /tmp/test/*.vhd

# 3. ready_for_updates signal exists in both files
grep "ready_for_updates" /tmp/test/DS1140_PD_custom_inst_shim.vhd
grep "ready_for_updates" /tmp/test/DS1140_PD_custom_inst_main.vhd
```

### Full Validation (After Phase 4C-4D)

Create CocotB tests:
- `tests/test_handshake_shim.py` - Verify gating behavior
- `tests/test_handshake_defaults.py` - Verify reset defaults
- `tests/test_ds1140_pd_handshake.py` - Integration test

---

## Success Criteria

**Phase 4A-4B is complete when:**

✅ **Shim template:**
- Has `ready_for_updates` input port
- Uses latching process (not combinatorial assignment)
- Has reset branch with defaults (even if type-based)
- Passes ready signal to main

✅ **Main template:**
- Has `ready_for_updates` output port
- Includes handshaking documentation (Pattern A & B)
- Has default implementation (always ready)

✅ **Verification:**
- Both templates pass Jinja2 syntax check
- Generated files compile with GHDL
- `ready_for_updates` signal present in both generated files
- REGISTER_UPDATE_PROC exists in generated shim

---

## File References

**Template files:**
- `shared/custom_inst/templates/custom_inst_shim_template.vhd`
- `shared/custom_inst/templates/custom_inst_main_template.vhd`

**Specification:**
- `HandShakeProtocol.md` - Lines 92-165 (core protocol)
- `docs/BasicNetworkRegSafety_plan.md` - Detailed implementation plan

**Python files (Phase 4C - future work):**
- `models/custom_inst/app_register.py` - Add default_value field
- `tools/generate_custom_inst.py` - Add default rendering logic

**Test files (Phase 5 - future work):**
- `tests/test_handshake_shim.py` - Unit tests
- `tests/test_ds1140_pd_handshake.py` - Integration tests

---

## Next Session Prompt

```
Continue implementing BasicNetworkRegSafety (Phases 4A-4B).

Task: Modify VHDL templates to add ready_for_updates handshaking signal.

Files:
- shared/custom_inst/templates/custom_inst_shim_template.vhd
- shared/custom_inst/templates/custom_inst_main_template.vhd

Plan: docs/BasicNetworkRegSafety_plan.md
Context: docs/BasicNetworkRegSafety_plan_prompt.md (this file)

Start with Phase 4A.1: Add ready_for_updates port to shim template.

Workaround for default_value: Use type-based defaults temporarily
(add proper YAML support in Phase 4C).
```

---

## Appendix: Current vs Target Comparison

### Shim Layer Data Flow

**Current (Unsafe):**
```
Network Write → CR6
                ↓ (combinatorial, immediate)
              intensity signal
                ↓
              Main App (sees glitches during FSM transitions)
```

**Target (Safe):**
```
Network Write → CR6
                ↓ (combinatorial path)
              app_reg_6 internal signal
                ↓
              Latching Process (gated by ready_for_updates)
                ↓
              intensity signal (stable)
                ↓
              Main App (sees atomic updates only when ready='1')
```

### Timing Comparison

**Current Behavior:**
```
Cycle:  0    1    2    3    4    5
CR6:    0x2666 (2.0V)  │ 0x3DCF (2.4V)
                       └─────────────┘ Network write
intensity: 2.0V        │ 2.4V ← Immediate change (UNSAFE!)
FSM:    IDLE   ARMED  │ ARMED (Config changed mid-operation!)
```

**Target Behavior:**
```
Cycle:  0    1    2    3    4    5    6
CR6:    0x2666 (2.0V)  │ 0x3DCF (2.4V)
                       └─────────────┘ Network write
ready:  1    1    0    │ 0    0    1
                       │              └─ FSM returns to IDLE
intensity: 2.0V        │ 2.0V (held)  │ 2.4V ← Update when safe
FSM:    IDLE   ARMED  │ ARMED        │ IDLE (Safe!)
```

---

**Status:** Ready to implement
**Estimated time:** 1.5 hours
**Blocker:** None (use type-based defaults workaround)
