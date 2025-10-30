#!/usr/bin/env python3
"""
Debug DS1140-PD outputs - comprehensive diagnostics
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("DS1140-PD OUTPUT DIAGNOSTICS")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Get CloudCompile reference
print("Getting CloudCompile reference (Slot 2)...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Get Oscilloscope reference
print("Getting Oscilloscope reference (Slot 1)...")
osc = m.set_instrument(1, Oscilloscope)
print("✓ Got Oscilloscope")

# Configure routing
print("\nConfiguring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},  # Trigger → Osc Ch1
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},  # Intensity → Osc Ch2
    {'source': 'Slot2OutA', 'destination': 'Output1'},   # Also to physical OUT1
    {'source': 'Slot2OutB', 'destination': 'Output2'},   # Also to physical OUT2
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Configure oscilloscope with auto trigger to see idle state
print("\nConfiguring oscilloscope (Auto trigger to see idle levels)...")
osc.set_timebase(-0.001, 0.001)  # 2ms window
# Use Auto mode so it captures even without trigger
print("✓ Oscilloscope configured")

# Initialize control registers (CRITICAL!)
print("\nInitializing control registers...")

# Helper functions
def voltage_to_raw(voltage: float) -> int:
    """Convert voltage to 16-bit raw (Moku ±5V scale)"""
    return int((voltage / 5.0) * 32767.0) & 0xFFFF

def pack_16bit(value: int) -> int:
    """Pack 16-bit value into upper bits of 32-bit register"""
    return (value & 0xFFFF) << 16

def pack_8bit(value: int) -> int:
    """Pack 8-bit value into upper bits of 32-bit register"""
    return (value & 0xFF) << 24

# Control3: Clock divider (0 = no division)
cc.set_control(3, pack_8bit(0))
# Control4: Arm timeout (4095 cycles max)
cc.set_control(4, pack_16bit(4095))
# Control5: Firing duration (16 cycles)
cc.set_control(5, pack_8bit(16))
# Control6: Cooling duration (16 cycles)
cc.set_control(6, pack_8bit(16))
# Control7: Trigger threshold (2.4V)
threshold_raw = voltage_to_raw(2.4)
cc.set_control(7, pack_16bit(threshold_raw))
# Control8: Intensity (2.0V)
intensity_raw = voltage_to_raw(2.0)
cc.set_control(8, pack_16bit(intensity_raw))
# Control15: VOLO_READY bits
cc.set_control(15, 0xE0000000)

print(f"✓ Registers initialized (Intensity={2.0}V, Threshold={2.4}V)")

# Check idle state BEFORE firing
print("\n" + "=" * 70)
print("CHECKING IDLE STATE (before fire)")
print("=" * 70)
time.sleep(0.5)
data_before = osc.get_data()

print("\nChannel 1 (Trigger - Idle):")
print(f"  Max: {max(data_before['ch1']):.4f} V")
print(f"  Min: {min(data_before['ch1']):.4f} V")
print(f"  Avg: {sum(data_before['ch1'])/len(data_before['ch1']):.4f} V")

print("\nChannel 2 (Intensity - Idle):")
print(f"  Max: {max(data_before['ch2']):.4f} V")
print(f"  Min: {min(data_before['ch2']):.4f} V")
print(f"  Avg: {sum(data_before['ch2'])/len(data_before['ch2']):.4f} V")

# Read CloudCompile monitor registers (status)
print("\n" + "=" * 70)
print("CLOUDCOMPILE STATUS REGISTERS")
print("=" * 70)
try:
    status0 = cc.get_monitor(0)
    status1 = cc.get_monitor(1)
    status2 = cc.get_monitor(2)
    print(f"Monitor0 (FSM State):     0x{status0:08X} ({status0})")
    print(f"Monitor1 (Delay Counter): 0x{status1:08X} ({status1})")
    print(f"Monitor2 (Debug):         0x{status2:08X} ({status2})")
except Exception as e:
    print(f"Error reading monitors: {e}")

# Fire the probe
print("\n" + "=" * 70)
print("FIRING PROBE...")
print("=" * 70)
print("ARM + FORCE_FIRE in 1 second...")
time.sleep(1)

# Set ARM button
cc.set_control(0, 0x80000000)  # Control0, bit 31 = ARM
# Set FORCE_FIRE button
cc.set_control(1, 0x80000000)  # Control1, bit 31 = FORCE_FIRE
time.sleep(0.05)  # Hold for 50ms

# Release buttons
cc.set_control(0, 0x00000000)
cc.set_control(1, 0x00000000)

print("✓ Fire sequence complete!")

# Capture immediately after fire
print("\n" + "=" * 70)
print("CHECKING STATE AFTER FIRE")
print("=" * 70)
time.sleep(0.2)
data_after = osc.get_data()

print("\nChannel 1 (Trigger - After Fire):")
ch1_after = data_after['ch1']
print(f"  Max: {max(ch1_after):.4f} V")
print(f"  Min: {min(ch1_after):.4f} V")
print(f"  Avg: {sum(ch1_after)/len(ch1_after):.4f} V")

print("\nChannel 2 (Intensity - After Fire):")
ch2_after = data_after['ch2']
print(f"  Max: {max(ch2_after):.4f} V")
print(f"  Min: {min(ch2_after):.4f} V")
print(f"  Avg: {sum(ch2_after)/len(ch2_after):.4f} V")

# Read status after fire
print("\n" + "=" * 70)
print("STATUS AFTER FIRE")
print("=" * 70)
try:
    status0 = cc.get_monitor(0)
    status1 = cc.get_monitor(1)
    status2 = cc.get_monitor(2)
    print(f"Monitor0 (FSM State):     0x{status0:08X} ({status0})")
    print(f"Monitor1 (Delay Counter): 0x{status1:08X} ({status1})")
    print(f"Monitor2 (Debug):         0x{status2:08X} ({status2})")

    # Decode FSM state
    fsm_state = status0 & 0xFF
    state_names = {
        0: "IDLE",
        1: "ARMED",
        2: "WAIT_DELAY",
        3: "FIRE_PULSE",
        4: "COOLDOWN"
    }
    print(f"\nFSM State: {state_names.get(fsm_state, 'UNKNOWN')} ({fsm_state})")
except Exception as e:
    print(f"Error reading monitors: {e}")

# Read control registers to verify settings
print("\n" + "=" * 70)
print("CONTROL REGISTER VERIFICATION")
print("=" * 70)
print("Current Control0 (should be 0 after button release): 0x00000000")
print("Current Control1 (should be 0 after button release): 0x00000000")

# Try reading back the delay and intensity settings
print("\n" + "=" * 70)
print("CHECKING DELAY AND INTENSITY SETTINGS")
print("=" * 70)
# These might be in Control registers 2-6 based on DS1140-PD spec
print("Reading configuration registers...")
# Note: Can't read back control registers via Moku API, only write

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

if max(ch2_after) < 0.1:
    print("❌ PROBLEM: Output2 (intensity) is still 0V!")
    print("   Possible causes:")
    print("   1. Intensity register not set (should be ~2.0V)")
    print("   2. Module not generating output")
    print("   3. Routing issue")
    print("   4. Bitstream problem")
    print("\n   Try setting intensity register explicitly:")
    print("   cc.set_control(3, 0x66666666)  # ~2.0V intensity")
else:
    print("✓ Output2 has voltage!")

if max(ch1_after) < 0.1:
    print("\n❌ PROBLEM: Output1 (trigger) showing no pulse!")
    print("   Either:")
    print("   - Pulse too short to capture (try faster timebase)")
    print("   - Pulse never generated (check FSM state)")
else:
    print("\n✓ Output1 showing trigger activity!")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
