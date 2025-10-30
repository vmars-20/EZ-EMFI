#!/usr/bin/env python3
"""
Quick script to fire DS1140-PD immediately
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("DS1140-PD IMMEDIATE FIRE")
print("=" * 70)
print("\n👁️ WATCH YOUR OSCILLOSCOPE NOW!\n")

# Connect
print("Connecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Get CloudCompile reference
print("Getting CloudCompile reference...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Reapply routing (set_instrument clears it)
# Skip oscilloscope routing for now - just connect outputs
print("Reapplying routing (outputs only)...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Output1'},
    {'source': 'Slot2OutB', 'destination': 'Output2'},
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Initialize control registers (THIS WAS MISSING!)
print("Initializing control registers...")

# Helper functions from deploy_ds1140_pd.py
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
print("  ✓ Clock divider = 0")

# Control4: Arm timeout (4095 cycles max)
cc.set_control(4, pack_16bit(4095))
print("  ✓ Arm timeout = 4095 cycles")

# Control5: Firing duration (16 cycles)
cc.set_control(5, pack_8bit(16))
print("  ✓ Firing duration = 16 cycles")

# Control6: Cooling duration (16 cycles)
cc.set_control(6, pack_8bit(16))
print("  ✓ Cooling duration = 16 cycles")

# Control7: Trigger threshold (2.4V)
threshold_raw = voltage_to_raw(2.4)
cc.set_control(7, pack_16bit(threshold_raw))
print(f"  ✓ Trigger threshold = 2.4V (0x{threshold_raw:04X})")

# Control8: Intensity (2.0V)
intensity_raw = voltage_to_raw(2.0)
cc.set_control(8, pack_16bit(intensity_raw))
print(f"  ✓ Intensity = 2.0V (0x{intensity_raw:04X})")

# Control15: VOLO_READY bits
cc.set_control(15, 0xE0000000)
print("  ✓ VOLO_READY enabled")

# Control10: Start BRAM loader with word_count=0 (no data to load)
# This is CRITICAL - without this, loader_done stays 0 and module never enables!
cc.set_control(10, 0x00000001)  # start=1, word_count=0
print("  ✓ BRAM loader started (no data)")

print("✓ All registers initialized!")

# Wait for loader to finish (should be instant since word_count=0)
time.sleep(0.1)

# Fire sequence: ARM + FORCE_FIRE simultaneously
print("\n" + "=" * 70)
print("FIRING IN 3 SECONDS...")
print("=" * 70)
time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)

print("\n🔥 FIRING NOW! 🔥\n")

# Set ARM button
cc.set_control(0, 0x80000000)  # Control0, bit 31 = ARM
# Set FORCE_FIRE button
cc.set_control(1, 0x80000000)  # Control1, bit 31 = FORCE_FIRE
time.sleep(0.01)

# Release buttons
cc.set_control(0, 0x00000000)
cc.set_control(1, 0x00000000)

print("✓ Fire sequence complete!")
print("\nYou should have seen:")
print("  - Output1: Trigger pulse (to EMFI probe)")
print("  - Output2: ~2.0V intensity")
print("  - Moku oscilloscope: FSM state transitions")

print("\n" + "=" * 70)
print("Fire again? Run: uv run python tools/fire_now.py")
print("=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
