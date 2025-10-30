#!/usr/bin/env python3
"""
Test with LONG firing duration so we can actually see the pulse
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("TEST WITH LONG FIRING DURATION")
print("=" * 70)
print("\nKey insight: Intensity output is ONLY active during FIRING state!")
print("Default firing duration: 16 cycles @ 100MHz = 160ns (too short to see)")
print("Solution: Set firing duration to 255 cycles = 2.55μs")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Deploy DEBUG bitstream
print("\nDeploying DEBUG bitstream...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_debug_bits.tar")
print("✓ Got CloudCompile (DEBUG)")

# Setup oscilloscope with FAST timebase
osc = m.set_instrument(1, Oscilloscope)
osc.set_timebase(-0.00001, 0.00001)  # ±10μs window (much faster!)
print("✓ Got Oscilloscope (±10μs timebase)")

# Configure routing
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},  # FSM debug
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},  # Intensity
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

# Initialize registers with LONG firing duration
print("\nInitializing registers...")
cc.set_control(15, 0xE0000000)  # VOLO_READY
cc.set_control(3, pack_8bit(0))  # Clock divider
cc.set_control(4, pack_16bit(4095))  # Arm timeout
cc.set_control(5, pack_8bit(255))  # LONG firing duration (255 cycles = 2.55μs)
cc.set_control(6, pack_8bit(16))  # Cooling duration
cc.set_control(7, pack_16bit(voltage_to_raw(2.4)))  # Threshold
cc.set_control(8, pack_16bit(voltage_to_raw(2.0)))  # Intensity = 2.0V
print("✓ Registers initialized")
print(f"   Firing duration: 255 cycles = 2.55μs @ 100MHz")
print(f"   Intensity: 2.0V")

# Reset FSM
print("\nResetting FSM...")
cc.set_control(2, 0x80000000)
time.sleep(0.01)
cc.set_control(2, 0x00000000)
time.sleep(0.5)
print("✓ FSM reset")

# ARM the probe
print("\nArming probe...")
cc.set_control(0, 0x80000000)
time.sleep(0.01)
cc.set_control(0, 0x00000000)
time.sleep(0.1)
print("✓ Probe armed")

# FIRE with continuous capturing
print("\n" + "=" * 70)
print("FIRING NOW (watch for 2.55μs pulse)...")
print("=" * 70)

cc.set_control(1, 0x80000000)  # FORCE_FIRE
time.sleep(0.01)
cc.set_control(1, 0x00000000)

# Capture multiple times to catch the pulse
time.sleep(0.05)

for i in range(3):
    data = osc.get_data()
    ch1 = data['ch1']
    ch2 = data['ch2']

    ch1_max = max(ch1)
    ch2_max = max(ch2)
    ch1_avg = sum(ch1)/len(ch1)
    ch2_avg = sum(ch2)/len(ch2)

    print(f"\nCapture {i+1}:")
    print(f"  Ch1 (FSM): max={ch1_max:.4f}V, avg={ch1_avg:.4f}V")
    print(f"  Ch2 (Intensity): max={ch2_max:.4f}V, avg={ch2_avg:.4f}V")

    if ch2_max > 0.1:
        print(f"  🎉 DETECTED INTENSITY PULSE: {ch2_max:.4f}V!")
        break

    time.sleep(0.05)

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

if ch2_max > 0.1:
    print(f"✅ SUCCESS! Intensity pulse detected: {ch2_max:.4f}V")
    print(f"   Expected: ~2.0V, Got: {ch2_max:.4f}V")
    if abs(ch2_max - 2.0) > 0.5:
        print(f"   ⚠️ Voltage mismatch - expected 2.0V but got {ch2_max:.4f}V")
else:
    print(f"❌ FAILED: Still no pulse detected (max={ch2_max:.4f}V)")
    print("\nTroubleshooting:")
    print("  1. Check that firing_active signal is working in VHDL")
    print("  2. Verify intensity register is actually connected")
    print("  3. Try even longer firing duration (try Control5=0xFF)")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
