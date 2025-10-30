#!/usr/bin/env python3
"""
DS1140-PD Intensity Ramp with Firing

Steps through intensity values from 2.0V down to 0V in 0.2V steps,
firing the probe at each step with 0.1s intervals.

This helps observe intensity voltage on Output2 while seeing actual
trigger pulses on Output1.
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)


def voltage_to_raw(voltage: float) -> int:
    """Convert voltage to 16-bit raw value (±5V full scale)"""
    if voltage < -5.0 or voltage > 5.0:
        raise ValueError(f"Voltage {voltage}V out of range (±5V)")
    return int((voltage / 5.0) * 32767.0) & 0xFFFF


def pack_16bit_register(value: int) -> int:
    """Pack 16-bit value into upper bits of 32-bit control register"""
    return (value & 0xFFFF) << 16


print("=" * 80)
print("DS1140-PD INTENSITY RAMP WITH FIRING")
print("=" * 80)
print()
print("This will step intensity from 2.0V → 0V in 0.2V steps")
print("Firing the probe at each step with 0.1s intervals")
print()
print("👁️  WATCH YOUR OSCILLOSCOPE:")
print("   - Output1: Trigger pulses (should see repeated firing)")
print("   - Output2: Intensity ramping down from ~2.0V to 0V")
print()

# Connect
print("Connecting to Moku at 192.168.13.159...")
m = MultiInstrument('192.168.13.159', platform_id=2, force_connect=True)
print("✓ Connected")

# Get CloudCompile reference
print("Getting CloudCompile reference...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
print("✓ Got CloudCompile")

# Reapply routing
print("Configuring routing...")
connections = [
    {'source': 'Slot2OutA', 'destination': 'Output1'},  # Trigger
    {'source': 'Slot2OutB', 'destination': 'Output2'},  # Intensity
]
m.set_connections(connections=connections)
print("✓ Routing configured")

# Initialize other registers
print("Initializing control registers...")
cc.set_control(15, 0xE0000000)  # VOLO_READY
cc.set_control(3, 0x00000000)   # Clock divider = 0
cc.set_control(4, 0x0FFF0000)   # Arm timeout = 4095 (max)
cc.set_control(5, 0x10000000)   # Firing duration = 16
cc.set_control(6, 0x10000000)   # Cooling duration = 16
cc.set_control(7, 0x3D700000)   # Trigger threshold = 2.4V
print("✓ Registers initialized")

print("\n" + "=" * 80)
print("STARTING INTENSITY RAMP + FIRE")
print("=" * 80)
print()

# Ramp from 2.0V down to 0V in 0.2V steps
test_voltages = [2.0 - (i * 0.2) for i in range(11)]  # 2.0, 1.8, 1.6, ..., 0.0

print("Step  Intensity  Raw Value   Packed Reg   Status")
print("-" * 70)

for idx, target_v in enumerate(test_voltages, 1):
    # Set intensity
    raw_value = voltage_to_raw(target_v)
    packed = pack_16bit_register(raw_value)
    cc.set_control(8, packed)

    print(f"{idx:2d}.   {target_v:4.1f}V     0x{raw_value:04X}      0x{packed:08X}   ", end='', flush=True)

    # Fire: ARM + FORCE_FIRE simultaneously
    cc.set_control(0, 0x80000000)  # ARM
    cc.set_control(1, 0x80000000)  # FORCE_FIRE
    time.sleep(0.001)  # Brief hold

    # Release buttons
    cc.set_control(0, 0x00000000)
    cc.set_control(1, 0x00000000)

    print("🔥 FIRED", flush=True)

    # Wait 0.1s before next step
    time.sleep(0.1)

    # Reset FSM for next shot
    cc.set_control(2, 0x80000000)  # RESET
    time.sleep(0.001)
    cc.set_control(2, 0x00000000)
    time.sleep(0.01)

print()
print("=" * 80)
print("RAMP COMPLETE")
print("=" * 80)
print()
print("You should have observed:")
print("  - Output1: 11 trigger pulses (one per step)")
print("  - Output2: Intensity voltage stepping down from 2.0V to 0V")
print()
print("Did Output2 show voltage changes?")
print("  YES → MSB extraction working correctly")
print("  NO  → Check VHDL intensity signal extraction")
print()

# Reset to 2.0V
print("Resetting intensity to 2.0V...")
raw_value = voltage_to_raw(2.0)
packed = pack_16bit_register(raw_value)
cc.set_control(8, packed)
print("✓ Reset to 2.0V")

print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
print()
print("To run again: uv run python tools/intensity_ramp_fire.py")
