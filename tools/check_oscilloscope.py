#!/usr/bin/env python3
"""
Check oscilloscope readings after fire sequence
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("CHECKING OSCILLOSCOPE READINGS")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Get Oscilloscope reference
print("Getting Oscilloscope reference (Slot 1)...")
osc = m.set_instrument(1, Oscilloscope)
print("✓ Got Oscilloscope")

# Get CloudCompile reference
print("Getting CloudCompile reference (Slot 2)...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Configure routing: Slot2 outputs → Slot1 oscilloscope inputs + physical outputs
print("\nConfiguring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Slot1InA'},  # Trigger → Osc Ch1
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},  # Intensity → Osc Ch2
    {'source': 'Slot2OutA', 'destination': 'Output1'},   # Also to physical OUT1
    {'source': 'Slot2OutB', 'destination': 'Output2'},   # Also to physical OUT2
]
m.set_connections(connections=connections)
print("✓ Routing configured (fan-out to oscilloscope + physical outputs)")

# Configure oscilloscope
print("\nConfiguring oscilloscope...")
# Set timebase - 1ms window to catch the pulse
osc.set_timebase(-0.0005, 0.0005)  # ±500us window

print("✓ Oscilloscope configured")

# Fire the probe first
print("\n" + "=" * 70)
print("FIRING PROBE...")
print("=" * 70)
print("ARM + FORCE_FIRE in 1 second...")
time.sleep(1)

# Set ARM button
cc.set_control(0, 0x80000000)  # Control0, bit 31 = ARM
# Set FORCE_FIRE button
cc.set_control(1, 0x80000000)  # Control1, bit 31 = FORCE_FIRE
time.sleep(0.01)

# Release buttons
cc.set_control(0, 0x00000000)
cc.set_control(1, 0x00000000)

print("✓ Fire sequence complete!")

# Take a measurement
print("\nCapturing oscilloscope data...")
time.sleep(0.5)
data = osc.get_data()

print("\n" + "=" * 70)
print("OSCILLOSCOPE READINGS")
print("=" * 70)

# Analyze Channel 1 (Output1 - Trigger)
ch1_data = data['ch1']
ch1_max = max(ch1_data)
ch1_min = min(ch1_data)
ch1_avg = sum(ch1_data) / len(ch1_data)

print("\nChannel 1 (Output1 - Trigger Pulse):")
print(f"  Max: {ch1_max:.4f} V")
print(f"  Min: {ch1_min:.4f} V")
print(f"  Avg: {ch1_avg:.4f} V")
print(f"  Peak-to-Peak: {ch1_max - ch1_min:.4f} V")

# Analyze Channel 2 (Output2 - Intensity)
ch2_data = data['ch2']
ch2_max = max(ch2_data)
ch2_min = min(ch2_data)
ch2_avg = sum(ch2_data) / len(ch2_data)

print("\nChannel 2 (Output2 - Intensity):")
print(f"  Max: {ch2_max:.4f} V")
print(f"  Min: {ch2_min:.4f} V")
print(f"  Avg: {ch2_avg:.4f} V")
print(f"  Peak-to-Peak: {ch2_max - ch2_min:.4f} V")

print("\n" + "=" * 70)
print("EXPECTED vs ACTUAL")
print("=" * 70)
print("\nExpected:")
print("  Output1: Brief trigger pulse (~3.3V or logic high)")
print("  Output2: ~2.0V steady intensity")
print("\nActual:")
print(f"  Output1: {ch1_max:.4f}V max, {ch1_avg:.4f}V avg")
print(f"  Output2: {ch2_max:.4f}V max, {ch2_avg:.4f}V avg")

if abs(ch2_avg - 2.0) > 0.5:
    print("\n⚠️  WARNING: Output2 voltage differs significantly from expected 2.0V!")
    print(f"   Expected: ~2.0V, Got: {ch2_avg:.4f}V")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
