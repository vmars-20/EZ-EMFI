#!/usr/bin/env python3
"""
Simple voltage check - just see if we can read ANY voltage from outputs
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("SIMPLE VOLTAGE CHECK")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Get CloudCompile reference
print("Getting CloudCompile reference...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Get Oscilloscope reference
print("Getting Oscilloscope reference...")
osc = m.set_instrument(1, Oscilloscope)
print("✓ Got Oscilloscope")

# Configure routing
print("\nConfiguring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},
    {'source': 'Slot2OutA', 'destination': 'Output1'},
    {'source': 'Slot2OutB', 'destination': 'Output2'},
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Configure oscilloscope
print("\nConfiguring oscilloscope...")
osc.set_timebase(-0.01, 0.01)  # 20ms window
print("✓ Oscilloscope configured")

# Helper functions
def voltage_to_raw(voltage: float) -> int:
    return int((voltage / 5.0) * 32767.0) & 0xFFFF

def pack_16bit(value: int) -> int:
    return (value & 0xFFFF) << 16

def pack_8bit(value: int) -> int:
    return (value & 0xFF) << 24

# Initialize ALL registers
print("\nInitializing ALL control registers...")
cc.set_control(15, 0xE0000000)  # VOLO_READY first
print("  ✓ Control15: VOLO_READY")

cc.set_control(3, pack_8bit(0))  # Clock divider
print("  ✓ Control3: Clock divider = 0")

cc.set_control(4, pack_16bit(4095))  # Arm timeout
print("  ✓ Control4: Arm timeout = 4095")

cc.set_control(5, pack_8bit(16))  # Firing duration
print("  ✓ Control5: Firing duration = 16")

cc.set_control(6, pack_8bit(16))  # Cooling duration
print("  ✓ Control6: Cooling duration = 16")

threshold_raw = voltage_to_raw(2.4)
cc.set_control(7, pack_16bit(threshold_raw))  # Trigger threshold
print(f"  ✓ Control7: Trigger threshold = 2.4V (raw=0x{threshold_raw:04X})")

intensity_raw = voltage_to_raw(2.0)
cc.set_control(8, pack_16bit(intensity_raw))  # Intensity
print(f"  ✓ Control8: Intensity = 2.0V (raw=0x{intensity_raw:04X}, packed=0x{pack_16bit(intensity_raw):08X})")

print("\n✓ All registers initialized")

# Wait for settings to take effect
print("\nWaiting 2 seconds for settings to propagate...")
time.sleep(2)

# Capture multiple times
print("\n" + "=" * 70)
print("READING OSCILLOSCOPE (5 samples over 2 seconds)")
print("=" * 70)

for i in range(5):
    data = osc.get_data()
    ch1 = data['ch1']
    ch2 = data['ch2']

    print(f"\nSample {i+1}:")
    print(f"  Ch1 (OutputA): min={min(ch1):.4f}V, max={max(ch1):.4f}V, avg={sum(ch1)/len(ch1):.4f}V")
    print(f"  Ch2 (OutputB): min={min(ch2):.4f}V, max={max(ch2):.4f}V, avg={sum(ch2)/len(ch2):.4f}V")

    time.sleep(0.4)

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

print("\nIf all values are 0V:")
print("  1. Check bitstream - maybe outputs are conditional on FSM state")
print("  2. Check VHDL - maybe intensity only active during FIRING state")
print("  3. Try arming the probe to change FSM state")

print("\nLet's try ARM + FORCE_FIRE to see if that activates outputs...")
print("\nARMING...")
cc.set_control(0, 0x80000000)  # ARM
time.sleep(0.01)
cc.set_control(0, 0x00000000)
time.sleep(0.5)

print("CHECKING AFTER ARM...")
data = osc.get_data()
print(f"  Ch1: avg={sum(data['ch1'])/len(data['ch1']):.4f}V")
print(f"  Ch2: avg={sum(data['ch2'])/len(data['ch2']):.4f}V")

print("\nFIRING...")
cc.set_control(1, 0x80000000)  # FORCE_FIRE
time.sleep(0.01)
cc.set_control(1, 0x00000000)
time.sleep(0.1)

print("CHECKING DURING/AFTER FIRE...")
data = osc.get_data()
ch1 = data['ch1']
ch2 = data['ch2']
print(f"  Ch1: min={min(ch1):.4f}V, max={max(ch1):.4f}V")
print(f"  Ch2: min={min(ch2):.4f}V, max={max(ch2):.4f}V")

if max(ch1) > 0.1 or max(ch2) > 0.1:
    print("\n✅ GOT VOLTAGE! Outputs are conditional on FSM state!")
else:
    print("\n❌ Still 0V even after firing")
    print("   Possible issues:")
    print("   - Bitstream not working")
    print("   - Register packing incorrect")
    print("   - VHDL module issue")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
