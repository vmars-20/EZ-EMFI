#!/usr/bin/env python3
"""
Test with explicit FSM RESET first
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("TEST WITH EXPLICIT FSM RESET")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Deploy DEBUG bitstream
print("\nDeploying DEBUG bitstream...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_debug_bits.tar")
print("✓ Got CloudCompile (DEBUG)")

# Setup oscilloscope
osc = m.set_instrument(1, Oscilloscope)
osc.set_timebase(-0.01, 0.01)
print("✓ Got Oscilloscope")

# Configure routing
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},
    {'source': 'Slot2OutA', 'destination': 'Output1'},
    {'source': 'Slot2OutB', 'destination': 'Output2'},
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Helper functions
def voltage_to_raw(voltage: float) -> int:
    return int((voltage / 5.0) * 32767.0) & 0xFFFF

def pack_16bit(value: int) -> int:
    return (value & 0xFFFF) << 16

def pack_8bit(value: int) -> int:
    return (value & 0xFF) << 24

# STEP 1: Set VOLO_READY FIRST (critical!)
print("\nStep 1: Enabling VOLO_READY (Control15)...")
cc.set_control(15, 0xE0000000)
time.sleep(0.1)
print("✓ VOLO_READY enabled")

# STEP 2: Initialize all other registers
print("\nStep 2: Initializing control registers...")
cc.set_control(3, pack_8bit(0))  # Clock divider
cc.set_control(4, pack_16bit(4095))  # Arm timeout
cc.set_control(5, pack_8bit(16))  # Firing duration
cc.set_control(6, pack_8bit(16))  # Cooling duration
cc.set_control(7, pack_16bit(voltage_to_raw(2.4)))  # Threshold
cc.set_control(8, pack_16bit(voltage_to_raw(2.0)))  # Intensity (2.0V)
print("✓ All registers initialized")

# STEP 3: RESET the FSM explicitly
print("\nStep 3: Resetting FSM (Control2)...")
cc.set_control(2, 0x80000000)  # RESET button
time.sleep(0.01)
cc.set_control(2, 0x00000000)  # Release
time.sleep(0.5)
print("✓ FSM reset complete")

# Check state after reset
print("\n" + "=" * 70)
print("CHECKING STATE AFTER RESET")
print("=" * 70)
time.sleep(1)
data = osc.get_data()
ch1 = data['ch1']
ch2 = data['ch2']

print(f"Ch1 (FSM Debug): min={min(ch1):.4f}V, max={max(ch1):.4f}V, avg={sum(ch1)/len(ch1):.4f}V")
print(f"Ch2 (Intensity): min={min(ch2):.4f}V, max={max(ch2):.4f}V, avg={sum(ch2)/len(ch2):.4f}V")

ch1_avg = sum(ch1)/len(ch1)
ch2_avg = sum(ch2)/len(ch2)

if ch1_avg > 0.01 or ch2_avg > 0.01:
    print(f"\n🎉 GOT VOLTAGE! The reset worked!")
    print(f"   FSM: {ch1_avg:.4f}V, Intensity: {ch2_avg:.4f}V")
else:
    print("\n❌ Still 0V after reset")
    print("\nTrying manual voltage test on Control8...")
    # Try different intensity values to see if ANY work
    for test_v in [1.0, 2.0, 3.0]:
        print(f"\nSetting intensity to {test_v}V...")
        cc.set_control(8, pack_16bit(voltage_to_raw(test_v)))
        time.sleep(0.5)
        data = osc.get_data()
        avg = sum(data['ch2'])/len(data['ch2'])
        print(f"  Result: {avg:.4f}V")

    print("\n❌ Intensity control not working")
    print("\nPossible root causes:")
    print("  1. VHDL module not wired to DAC outputs correctly")
    print("  2. Register connections broken in bitstream")
    print("  3. Clock not running to module")
    print("  4. VoloApp wrapper issue")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
