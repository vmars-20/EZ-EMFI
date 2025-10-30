#!/usr/bin/env python3
"""
DS1140-PD Voltage Sweep Diagnostic

Steps through intensity values to debug MSB extraction and verify
voltage output on both Output2 (intensity) and observe on oscilloscope.

This helps diagnose issues with 16-bit register packing where voltages
might be coming out negative or incorrect.
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)


def voltage_to_raw(voltage: float) -> int:
    """
    Convert voltage to 16-bit raw value for Moku platform.
    Moku uses ±5V full scale.
    """
    if voltage < -5.0 or voltage > 5.0:
        raise ValueError(f"Voltage {voltage}V out of range (±5V)")
    return int((voltage / 5.0) * 32767.0) & 0xFFFF


def pack_16bit_register(value: int) -> int:
    """
    Pack 16-bit value into upper bits of 32-bit control register.
    DS1140-PD uses MSB-first packing: value[15:0] -> reg[31:16]
    """
    return (value & 0xFFFF) << 16


print("=" * 80)
print("DS1140-PD VOLTAGE SWEEP DIAGNOSTIC")
print("=" * 80)
print()
print("This script will step through intensity values from 0V to 3V")
print("to help debug MSB extraction issues.")
print()
print("👁️  WATCH YOUR OSCILLOSCOPES:")
print("   - External scope Output2: Should show stepping voltage")
print("   - Moku internal scope: Can also monitor outputs")
print()

# Connect
print("Connecting to Moku at 192.168.13.159...")
m = MultiInstrument('192.168.13.159', platform_id=2, force_connect=True)
print("✓ Connected")

# Get CloudCompile reference
print("Getting CloudCompile reference...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Setup oscilloscope for monitoring
print("Setting up Oscilloscope...")
osc = m.set_instrument(1, Oscilloscope)
osc.set_timebase(-5e-3, 5e-3)  # ±5ms window
print("✓ Got Oscilloscope")

# Reapply routing
print("Configuring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Output1'},  # Trigger
    {'source': 'Slot2OutB', 'destination': 'Output2'},  # Intensity (we're testing this!)
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Initialize other registers
print("\nInitializing control registers...")
cc.set_control(15, 0xE0000000)  # VOLO_READY
cc.set_control(3, 0x00000000)   # Clock divider = 0
cc.set_control(4, 0x0FFF0000)   # Arm timeout = 4095
cc.set_control(5, 0x10000000)   # Firing duration = 16
cc.set_control(6, 0x10000000)   # Cooling duration = 16
cc.set_control(7, 0x3D700000)   # Trigger threshold = 2.4V
print("✓ Registers initialized")

print("\n" + "=" * 80)
print("VOLTAGE SWEEP TEST")
print("=" * 80)
print()

# Test voltages from 0V to 3V in 0.2V steps
test_voltages = [i * 0.2 for i in range(16)]  # 0.0, 0.2, 0.4, ..., 3.0

print("Testing voltages (Intensity on Output2):")
print()
print("Target    Raw Value   Packed Reg   Control8")
print("-" * 60)

for target_v in test_voltages:
    # Convert voltage to raw value
    raw_value = voltage_to_raw(target_v)

    # Pack into Control8
    packed = pack_16bit_register(raw_value)

    # Set the control register
    cc.set_control(8, packed)

    # Display info
    print(f"{target_v:5.2f}V    0x{raw_value:04X}      0x{packed:08X}   Control8")

    # Wait for voltage to settle
    time.sleep(0.5)

    # Try to read oscilloscope to verify
    try:
        data = osc.get_data()
        if 'ch2' in data and len(data['ch2']) > 0:
            midpoint = len(data['ch2']) // 2
            measured_v = data['ch2'][midpoint]
            error = measured_v - target_v
            print(f"         Measured: {measured_v:5.2f}V  (error: {error:+5.2f}V)")
    except Exception as e:
        print(f"         (Oscilloscope read failed: {e})")

    print()

print("=" * 80)
print("SWEEP COMPLETE")
print("=" * 80)
print()
print("Analysis:")
print("  - Check if voltages stepped smoothly from 0V to 3V")
print("  - Look for sign flips (negative voltages)")
print("  - Verify MSB extraction in VHDL is correct")
print()
print("Expected behavior:")
print("  Output2 should show clean voltage steps")
print("  No negative voltages should appear")
print()
print("If you see negative voltages:")
print("  - Check bit extraction in DS1140_PD_volo_shim.vhd")
print("  - Verify app_reg_28(31 downto 16) is used correctly")
print("  - Check if sign extension is happening incorrectly")
print()

# Cleanup
print("Resetting intensity to 2.0V...")
raw_value = voltage_to_raw(2.0)
packed = pack_16bit_register(raw_value)
cc.set_control(8, packed)
print("✓ Reset to 2.0V")

print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
