#!/usr/bin/env python3
"""
Test DEBUG bitstream - should show FSM state voltages on OutputA
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("TESTING DS1140-PD DEBUG BITSTREAM")
print("=" * 70)
print("\nDebug bitstream mapping:")
print("  OutputA = FSM Debug (voltages: 0V=READY, 0.5V=ARMED, 1.0V=FIRING, etc.)")
print("  OutputB = Intensity (should be 2.0V)")
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
print("Setting up oscilloscope...")
osc = m.set_instrument(1, Oscilloscope)
print("✓ Got Oscilloscope")

# Configure routing
print("\nConfiguring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},  # FSM debug → Osc Ch1
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},  # Intensity → Osc Ch2
    {'source': 'Slot2OutA', 'destination': 'Output1'},   # FSM debug → Physical Out1
    {'source': 'Slot2OutB', 'destination': 'Output2'},   # Intensity → Physical Out2
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Configure oscilloscope
osc.set_timebase(-0.01, 0.01)
print("✓ Oscilloscope configured")

# Helper functions
def voltage_to_raw(voltage: float) -> int:
    return int((voltage / 5.0) * 32767.0) & 0xFFFF

def pack_16bit(value: int) -> int:
    return (value & 0xFFFF) << 16

def pack_8bit(value: int) -> int:
    return (value & 0xFF) << 24

# Initialize registers
print("\nInitializing registers...")
cc.set_control(15, 0xE0000000)  # VOLO_READY
cc.set_control(3, pack_8bit(0))  # Clock divider
cc.set_control(4, pack_16bit(4095))  # Arm timeout
cc.set_control(5, pack_8bit(16))  # Firing duration
cc.set_control(6, pack_8bit(16))  # Cooling duration
cc.set_control(7, pack_16bit(voltage_to_raw(2.4)))  # Threshold
cc.set_control(8, pack_16bit(voltage_to_raw(2.0)))  # Intensity
print("✓ All registers initialized")

# Wait for propagation
print("\nWaiting 1 second...")
time.sleep(1)

# Check READY state
print("\n" + "=" * 70)
print("CHECKING READY STATE")
print("=" * 70)
data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"Ch1 (FSM Debug): {ch1_avg:.4f}V (expected: ~0.0V for READY)")
print(f"Ch2 (Intensity): {ch2_avg:.4f}V (expected: ~2.0V)")

# ARM the probe
print("\n" + "=" * 70)
print("ARMING PROBE")
print("=" * 70)
cc.set_control(0, 0x80000000)  # ARM
time.sleep(0.01)
cc.set_control(0, 0x00000000)
time.sleep(0.5)

data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"Ch1 (FSM Debug): {ch1_avg:.4f}V (expected: ~0.5V for ARMED)")
print(f"Ch2 (Intensity): {ch2_avg:.4f}V (expected: ~2.0V)")

# FIRE the probe
print("\n" + "=" * 70)
print("FORCE FIRING")
print("=" * 70)
cc.set_control(1, 0x80000000)  # FORCE_FIRE
time.sleep(0.01)
cc.set_control(1, 0x00000000)
time.sleep(0.2)

data = osc.get_data()
ch1 = data['ch1']
ch2 = data['ch2']
print(f"Ch1 (FSM Debug): min={min(ch1):.4f}V, max={max(ch1):.4f}V, avg={sum(ch1)/len(ch1):.4f}V")
print(f"Ch2 (Intensity): min={min(ch2):.4f}V, max={max(ch2):.4f}V, avg={sum(ch2)/len(ch2):.4f}V")
print("\nExpected FSM transitions:")
print("  READY(0V) → ARMED(0.5V) → FIRING(1.0V) → COOLING(1.5V) → DONE(2.0V)")

# Check final state
time.sleep(0.5)
data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"\nFinal state:")
print(f"Ch1 (FSM Debug): {ch1_avg:.4f}V (expected: ~2.0V for DONE)")
print(f"Ch2 (Intensity): {ch2_avg:.4f}V (expected: ~2.0V)")

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

if ch1_avg > 0.1:
    print(f"✅ SUCCESS! FSM debug showing voltage: {ch1_avg:.4f}V")
else:
    print("❌ FAILED: FSM debug still 0V")

if ch2_avg > 0.1:
    print(f"✅ SUCCESS! Intensity showing voltage: {ch2_avg:.4f}V")
else:
    print("❌ FAILED: Intensity still 0V")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
