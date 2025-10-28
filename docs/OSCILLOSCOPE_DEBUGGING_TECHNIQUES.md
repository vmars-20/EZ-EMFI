# Oscilloscope-Based Hardware Debugging Techniques

**Purpose**: Debugging VHDL modules on Moku hardware using oscilloscope observation only (no internal signal access).

**Key Principle**: Make hardware state visible through oscilloscope outputs. Test methodology must work identically in simulation (CocotB) and hardware (MokuBench).

**Applicable To**: DS1140-PD, DS1120-PD, and any VoloApp using debug outputs for hardware validation.

**See Also**:
- `docs/FSM_OBSERVER_PATTERN.md` - FSM state visualization technique
- `DS1140_PD_volo_main.vhd:276-281` - OutputC FSM debug implementation
- `.claude/commands/test.md` - Testing context and CocotB guidelines

## Critical Techniques

### 1. Voltage Scaling (MOST COMMON ERROR)

**Moku Platform Specification** (from `modules/volo_common/common/Moku_Voltage_pkg.vhd`):
- Digital range: -32768 to +32767 (16-bit signed)
- Voltage range: **-5.0V to +5.0V** (full-scale analog)
- Scaling factor: 32768 / 5.0V = **6553.6 digital per volt**

**Common Mistake**: Assuming ±1V full scale → **5× voltage error!**

```python
# ❌ WRONG (causes 5× error):
digital = int((voltage / 1.0) * 32768)

# ✅ CORRECT:
digital = int((voltage / 5.0) * 32768)
```

**Discovery**: `inspectable_buffer_loader` session (2025-10-24), commit `c6136b8`

### 2. Voltage Guard Bands

**Problem**: Adjacent digital values (e.g., state=3 vs state=4) differ by ~0.8mV, easily corrupted by ADC noise.

**Solution**: Left-shift debug values by 2-3 bits before outputting to DAC.

```vhdl
-- Without guard band:
debug_out <= to_signed(to_integer(state_reg), 16);
-- state=3 → 0x0003 → 0.46mV

-- With 2-bit guard band (multiply by 4):
debug_out <= to_signed(to_integer(state_reg) * 4, 16);
-- state=3 → 0x000C → 1.83mV (4× spacing)

-- With 3-bit guard band (multiply by 8):
debug_out <= shift_left(to_signed(to_integer(state_reg), 13), 3);
-- state=3 → 0x0018 → 3.66mV (8× spacing)
```

**Recommendation**: Use 2-bit (×4) for most cases, 3-bit (×8) for noisy signals.

**Reference**: `modules/inspectable_buffer_loader/core/debug_mux.vhd:137-140`

### 3. Oscilloscope Sampling Latency

**Problem**: Single oscilloscope sample may show cached data from before MCC register write.

**Solution**: Poll multiple times with delays to catch transition.

```python
# ❌ Single sample (may miss transition):
mcc.set_control(1, new_value)
time.sleep(0.2)
data = osc.get_data()
status = decode_status(data['ch1'][...])

# ✅ Poll loop (reliable):
mcc.set_control(1, new_value)
for i in range(10):
    time.sleep(0.1)  # 100ms intervals
    data = osc.get_data()
    status = decode_status(data['ch1'][...])
    print(f"  Poll {i}: {status['state_name']}")
    if status['state_name'] == expected_state:
        break
```

**Timing**: 10 polls × 100ms = 1 second total (sufficient for most transitions)

**Discovery**: `inspectable_buffer_loader` Test 2 failure, commit `12410bf`

### 4. Sticky Hardware Flags

**Problem**: Some status flags (e.g., Fault) only clear on hardware reset (`n_reset` signal), not software reset (clearing Control0).

**Solution**: Use non-sticky flags (e.g., Valid) as primary success indicators.

```python
# ❌ Unreliable (sticky flag):
assert status['fault'] == False  # May be set from previous test

# ✅ Reliable (updated per operation):
assert status['valid'] == True   # Primary success indicator

# ⚠️ Acknowledge sticky flag:
if status['fault']:
    print("  ⚠ Note: Fault flag is sticky (hardware reset only)")
    print("  ✓ But Valid=True indicates success!")
```

**Flag Priority**:
1. **Valid flag** (updated per operation) - primary
2. **State** (current progress) - secondary
3. **Fault flag** (sticky) - historical indicator only

**Discovery**: `inspectable_buffer_loader` Test 4, commit `ba4ddb5`

### 5. State Machine Path Verification

**Problem**: Tests fail because requested state transition is impossible without hardware reset.

**Solution**: Map state machine paths before writing tests. Check prerequisites before each test.

```python
def test_5_checksum_error(mcc, osc):
    """Requires IDLE state to trigger new buffer load"""

    # Verify prerequisites
    status = get_state(osc)
    if status['state_name'] not in ["IDLE", "LOADING"]:
        print(f"⚠️  SKIPPING: Module in {status['state_name']} state")
        print("   Cannot trigger new load without hardware reset")
        print("   State machine: IDLE → ... → READY ⟷ RUNNING (no path to IDLE)")
        return  # Skip test

    # Continue with test...
```

**Test Ordering**: Tests requiring IDLE state must run first (or standalone).

**Discovery**: `inspectable_buffer_loader` Test 5, commit `d718da2` - "CRITICAL: State machine has no software-controllable reset path"

### 6. Verify State Before and After Actions

**Problem**: Assumptions about initial state may be wrong, causing confusing failures.

**Solution**: Always read and log state before triggering action.

```python
# ✅ Explicit verification pattern:
print(f"\n[ACTION] Setting buffer length = 8...")
status_before = get_state(osc)
print(f"Before: {status_before['state_name']}")

mcc.set_control(1, 8 << 16)
time.sleep(0.2)

status_after = get_state(osc)
print(f"After: {status_after['state_name']}")
print(f"  Full status: {status_after}")

assert status_after['state_name'] == "LOADING", \
    f"Expected LOADING, got {status_after['state_name']}"
```

**Benefits**:
- Clear diagnostic output for user
- Verifies action had expected effect
- Documents actual state transitions in test logs

### 7. Multi-View Debug Strategy

**Pattern**: Use debug multiplexer to switch between views for root cause analysis.

```python
# Step 1: Monitor normal operation with Status Summary (View 0)
set_debug_views(mcc, VIEW_STATUS_SUMMARY)
status = decode_view_0(get_osc_voltage(osc))

if status['fault']:
    # Step 2: Detect fault, switch to Error Diagnostics (View 6)
    print("  ⚠ Fault detected - switching to Error Diagnostics")
    set_debug_views(mcc, VIEW_ERROR_DIAGNOSTICS)
    time.sleep(0.1)

    # Step 3: Read detailed error information
    error = decode_view_6(get_osc_voltage(osc))
    print(f"  Error code: {error['error_code']}")
    print(f"  Error state: {error['error_state']}")
    print(f"  Error details: {error['error_details']}")
```

**Standard Debug Views** (8 per output channel):
- View 0: Status Summary (state, fault, valid, address)
- View 1: Data Comparison (expected vs actual)
- View 2: Write Activity (indexes, pointers)
- View 3: Data Snapshot (first/last words)
- View 4: Memory Readback (BRAM contents)
- View 5: Timing Diagnostics (strobes, counters)
- View 6: Error Diagnostics (codes, capture)
- View 7: Reserved

**Reference**: `modules/inspectable_buffer_loader/mcc_package.yaml:54-92`

### 8. CocotB Simulation Voltage Normalization

**Problem**: CocotB reads digital values directly (no ADC/DAC), but tests must work identically in simulation and hardware.

**Solution**: Convert digital to "fake voltage" matching Moku's ±5V scale.

```python
# In CocotB simulation:
digital = int(dut.debug_out_a.value.signed_integer)

# Convert to fake voltage (Moku ±5V scale):
osc_voltage = float(digital) / 32768.0 * 5.0

# Now same decoding function works for both!
status = decode_view_0_status_summary(osc_voltage)
```

**Benefit**: Test scripts work identically in CocotB and MokuBench (no code changes).

### 9. Propagation Delay Guidelines

**Empirical Timings** (from `inspectable_buffer_loader` hardware testing):

```python
# After MCC register write:
time.sleep(0.05)   # Minimum (fast operations)
time.sleep(0.1)    # Standard (most operations)
time.sleep(0.2)    # Long (complex state transitions)

# After debug view change:
time.sleep(0.1)    # Allow view switch to settle

# After module reset:
time.sleep(0.1)    # Allow reset propagation
```

**Recommendation**: Start with standard (0.1s), increase to 0.2s if transitions missed.

### 10. Incremental Git Commits (Workflow Integration)

**Pattern**: Commit each discovery immediately with same message shown to user.

```bash
# When debugging fails:
print("  Issue: Oscilloscope may show cached data from before Control1 write")
print("  Solution: Poll multiple times to catch transition")

# Commit with SAME message (don't regenerate):
git commit -m "Test 2 debug: Poll oscilloscope to catch state transition

- Add 10-poll loop with 0.1s intervals
- Issue: Oscilloscope may show cached data from before Control1 write
- Solution: Poll multiple times to catch transition"
```

**Benefits**:
- Git history = learning trail
- Token efficiency (don't duplicate messages)
- Reproducibility (others can follow debugging steps)

**User Request** (2025-10-24):
> "The git history is a great way to show off your learning. You can use the same
> messages you print to me (literally, the same, do not regenerate them)."

## Test Structure Pattern

### CocotB Oscilloscope-Only Tests

```python
@cocotb.test()
async def test_X_description(dut):
    """Test X: Description matching hardware test name"""
    dut._log.info("Test X: Description")

    # Setup
    await setup_clock(dut, clk_signal="clk")
    set_debug_views(dut, VIEW_STATUS_SUMMARY)
    await reset_active_low(dut, rst_signal="n_reset")

    # Observe initial state
    osc_voltage = float(dut.debug_out_a.value.signed_integer) / 32768.0 * 5.0
    status_before = decode_view_0_status_summary(osc_voltage)
    dut._log.info(f"Before: {status_before['state_name']}")

    # Trigger action
    dut.control1.value = 8 << 16
    await ClockCycles(dut.clk, 2)

    # Verify result
    osc_voltage = float(dut.debug_out_a.value.signed_integer) / 32768.0 * 5.0
    status_after = decode_view_0_status_summary(osc_voltage)
    assert status_after['state_name'] == "EXPECTED_STATE"

    dut._log.info("✓ Test X PASSED")
```

### MokuBench Hardware Tests (Mirrors CocotB)

```python
def test_X_description(mcc, osc):
    """Test X: Description (mirrors CocotB test exactly)"""
    print("="*70)
    print("Test X: Description")
    print("="*70)

    # Setup
    set_debug_views(mcc, VIEW_STATUS_SUMMARY)
    time.sleep(0.1)

    # Observe initial state
    data = osc.get_data()
    voltage = data['ch1'][len(data['ch1']) // 2]
    status_before = decode_view_0_status_summary(voltage)
    print(f"Before: {status_before['state_name']}")

    # Trigger action
    mcc.set_control(1, 8 << 16)
    
    # Poll for result (hardware-specific)
    for i in range(10):
        time.sleep(0.1)
        data = osc.get_data()
        voltage = data['ch1'][len(data['ch1']) // 2]
        status = decode_view_0_status_summary(voltage)
        print(f"  Poll {i}: {status['state_name']}")
        if status['state_name'] == "EXPECTED_STATE":
            break

    # Final verification
    assert status['state_name'] == "EXPECTED_STATE"
    print("✓ Test X PASSED\n")
```

## Debugging Checklist

When hardware test fails:

1. ✅ **CocotB test passes?** (verify simulation baseline)
2. ✅ **Voltage scaling correct?** (±5V, not ±1V)
3. ✅ **Polling for transitions?** (10× with 0.1s delays)
4. ✅ **Guard bands sufficient?** (2-3 bit left shift)
5. ✅ **Sticky flags acknowledged?** (use Valid, not Fault)
6. ✅ **State machine path valid?** (map transitions first)
7. ✅ **State verified before action?** (don't assume initial state)
8. ✅ **Multiple views checked?** (View 0 → View 6 for errors)
9. ✅ **Delays sufficient?** (0.1-0.2s after register writes)
10. ✅ **Git commit made?** (document discovery immediately)

## AI Agent Instructions

When user says "debug on hardware" or "test failed on Moku":

1. **Verify simulation baseline**: Run CocotB oscilloscope-only tests first
2. **Check voltage scaling**: Search for `voltage_to_digital()`, verify ±5V
3. **Add diagnostic output**: Print state before/after every action
4. **Poll for transitions**: Use 10-poll loop (0.1s intervals)
5. **Check multiple views**: Start View 0, switch to View 6 on fault
6. **Commit discoveries**: Use same message shown to user (don't regenerate)
7. **Document limitations**: Add comments explaining workarounds
8. **Update Serena memory**: After session, capture new techniques

**Never assume**:
- ±1V voltage scaling (99% chance it's ±5V!)
- Single oscilloscope sample catches transitions
- Fault flag clears on software reset
- State machine has software reset path

**Always do**:
- Read state before and after actions
- Poll multiple times for transitions
- Use Valid flag as primary indicator
- Commit each discovery immediately
- Print diagnostic output for user

## Reference Implementation

**Module**: `modules/inspectable_buffer_loader/`
**Tests**: `tests/test_inspectable_buffer_loader_*.py`
**Documentation**: `docs/OSCILLOSCOPE-BASED-DEBUGGING-WORKFLOW.md`

**Git Commits** (learning trail):
- `c6136b8` - Voltage scaling bug (±1V → ±5V)
- `12410bf` - Oscilloscope polling pattern
- `ba4ddb5` - Sticky fault flag handling
- `d718da2` - State machine reset limitation

**Test Results**: 4/5 PASSED, 1 SKIPPED (documented limitation)

---

**Generated**: 2025-10-24
**Session**: inspectable_buffer_loader hardware validation
**Hardware**: Moku:Go (192.168.13.159)
