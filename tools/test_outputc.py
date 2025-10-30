#!/usr/bin/env python3
"""
Test OutputC - the ACTUAL FSM debug output!

VHDL mapping (DS1140_PD_volo_main.vhd line 279-281):
    OutputA <= trigger_out;
    OutputB <= intensity_out;
    OutputC <= fsm_debug_voltage;  ← This is FSM debug!
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("TEST OUTPUTC - THE REAL FSM DEBUG OUTPUT")
print("=" * 70)
print("\n✅ CORRECT MAPPING:")
print("   OutputA = Trigger pulse (only during firing)")
print("   OutputB = Intensity (only during firing)")
print("   OutputC = FSM Debug (always active!)")
print("=" * 70)

# Connect
print("\nConnecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Deploy bitstream
print("\nDeploying bitstream...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Setup oscilloscope
osc = m.set_instrument(1, Oscilloscope)
osc.set_timebase(-0.005, 0.005)  # ±5ms window
print("✓ Got Oscilloscope")

# Configure routing - monitor OutputC on Ch1!
print("\nConfiguring routing (OutputC → Slot1InA for FSM monitoring)...")
connections = [
    {'source': 'Slot2OutC', 'destination': 'Slot1InA'},  # FSM debug → Osc Ch1
    {'source': 'Slot2OutB', 'destination': 'Slot1InB'},  # Intensity → Osc Ch2
    {'source': 'Slot2OutA', 'destination': 'Output1'},   # Trigger → Physical
    {'source': 'Slot2OutB', 'destination': 'Output2'},   # Intensity → Physical
]
m.set_connections(connections=connections)
print("✓ Routing configured - Ch1=FSM, Ch2=Intensity")

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
cc.set_control(5, pack_8bit(255))  # LONG firing duration
cc.set_control(6, pack_8bit(16))  # Cooling duration
cc.set_control(7, pack_16bit(voltage_to_raw(2.4)))  # Threshold
cc.set_control(8, pack_16bit(voltage_to_raw(2.0)))  # Intensity = 2.0V
print("✓ Registers initialized (Intensity=2.0V, Firing=255 cycles)")

# Reset FSM
print("\nResetting FSM...")
cc.set_control(2, 0x80000000)
time.sleep(0.01)
cc.set_control(2, 0x00000000)
time.sleep(1)
print("✓ FSM reset")

# Check READY state
print("\n" + "=" * 70)
print("STATE 1: READY (after reset)")
print("=" * 70)
data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"Ch1 (FSM/OutputC): {ch1_avg:.4f}V (expected: ~0.0V for READY)")
print(f"Ch2 (Intensity/OutputB): {ch2_avg:.4f}V (expected: 0.0V when not firing)")

# ARM the probe
print("\n" + "=" * 70)
print("STATE 2: ARMING")
print("=" * 70)
cc.set_control(0, 0x80000000)
time.sleep(0.01)
cc.set_control(0, 0x00000000)
time.sleep(0.5)

data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"Ch1 (FSM/OutputC): {ch1_avg:.4f}V (expected: ~0.5V for ARMED)")
print(f"Ch2 (Intensity/OutputB): {ch2_avg:.4f}V (expected: 0.0V when not firing)")

# FIRE the probe
print("\n" + "=" * 70)
print("STATE 3: FIRING")
print("=" * 70)
cc.set_control(1, 0x80000000)
time.sleep(0.01)
cc.set_control(1, 0x00000000)
time.sleep(0.2)

data = osc.get_data()
ch1 = data['ch1']
ch2 = data['ch2']
print(f"Ch1 (FSM/OutputC): min={min(ch1):.4f}V, max={max(ch1):.4f}V, avg={sum(ch1)/len(ch1):.4f}V")
print(f"Ch2 (Intensity/OutputB): min={min(ch2):.4f}V, max={max(ch2):.4f}V, avg={sum(ch2)/len(ch2):.4f}V")
print("\nExpected FSM voltages:")
print("  READY(0V) → ARMED(0.5V) → FIRING(1.0V) → COOLING(1.5V) → DONE(2.0V)")

# Check final state
print("\n" + "=" * 70)
print("STATE 4: DONE (after cooling)")
print("=" * 70)
time.sleep(0.5)
data = osc.get_data()
ch1_avg = sum(data['ch1'])/len(data['ch1'])
ch2_avg = sum(data['ch2'])/len(data['ch2'])
print(f"Ch1 (FSM/OutputC): {ch1_avg:.4f}V (expected: ~2.0V for DONE)")
print(f"Ch2 (Intensity/OutputB): {ch2_avg:.4f}V (expected: 0.0V when not firing)")

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

if ch1_avg > 0.1:
    print(f"✅ SUCCESS! FSM is working - showing voltage: {ch1_avg:.4f}V")
    print(f"   This confirms OutputC has FSM debug output!")
else:
    print("❌ FAILED: FSM still showing 0V on OutputC")
    print("   This means the module/FSM is not running at all")

if max(ch2) > 0.5:
    print(f"\n✅ SUCCESS! Intensity pulse detected: {max(ch2):.4f}V during firing!")
    if abs(max(ch2) - 2.0) > 0.5:
        print(f"   ⚠️ Voltage discrepancy: expected 2.0V, got {max(ch2):.4f}V")
else:
    print(f"\n⚠️ Intensity pulse not detected (max={max(ch2):.4f}V)")
    print("   This is expected if firing duration is too short for oscilloscope")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
