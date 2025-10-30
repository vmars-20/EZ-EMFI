#!/usr/bin/env python3
"""
DS1140-PD Intensity Ramp with SLOW Firing

Steps through intensity values from 2.0V down to 0V in 0.2V steps.
Uses maximum clock divider (÷16) and long firing duration (32 cycles)
to slow everything down so you can observe on scope.

Each fire sequence takes much longer, making it easier to track.
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


def pack_8bit_register(value: int) -> int:
    """Pack 8-bit value into upper bits of 32-bit control register"""
    return (value & 0xFF) << 24


print("=" * 80)
print("DS1140-PD INTENSITY RAMP - SLOW MOTION MODE")
print("=" * 80)
print()
print("Configuration:")
print("  - Clock divider: 15 (÷16 - SLOWEST)")
print("  - Firing duration: 32 cycles (LONGEST)")
print("  - Cooling duration: 32 cycles")
print("  - Pause between shots: 3 seconds")
print()
print("This makes each firing sequence take ~5 seconds total")
print()
print("👁️  WATCH YOUR OSCILLOSCOPE:")
print("   - Output1: Long trigger pulses (easier to see)")
print("   - Output2: Intensity stepping down slowly")
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

# Initialize registers with SLOW settings
print("Initializing control registers (SLOW MODE)...")
cc.set_control(15, 0xE0000000)  # VOLO_READY
cc.set_control(3, pack_8bit_register(15))  # Clock divider = 15 (÷16 - SLOWEST!)
cc.set_control(4, 0x0FFF0000)   # Arm timeout = 4095 (max)
cc.set_control(5, pack_8bit_register(32))  # Firing duration = 32 (LONGEST!)
cc.set_control(6, pack_8bit_register(32))  # Cooling duration = 32
cc.set_control(7, 0x3D700000)   # Trigger threshold = 2.4V
print("✓ Registers initialized")
print()
print("⏱️  Timing (with ÷16 clock divider):")
print("   - Each firing cycle: ~32 slow cycles")
print("   - Cooling cycle: ~32 slow cycles")
print("   - Total per shot: ~64 slow cycles + delays")
print()

print("\n" + "=" * 80)
print("STARTING SLOW INTENSITY RAMP")
print("=" * 80)
print()

# Ramp from 2.0V down to 0V in 0.2V steps
test_voltages = [2.0 - (i * 0.2) for i in range(11)]  # 2.0, 1.8, 1.6, ..., 0.0

print("Step  Intensity  Raw Value   Packed Reg   Status")
print("-" * 70)

for idx, target_v in enumerate(test_voltages, 1):
    print(f"\n{idx:2d}.   {target_v:4.1f}V     0x{voltage_to_raw(target_v):04X}      0x{pack_16bit_register(voltage_to_raw(target_v)):08X}")

    # Set intensity
    raw_value = voltage_to_raw(target_v)
    packed = pack_16bit_register(raw_value)
    cc.set_control(8, packed)
    print(f"     ↳ Intensity set to {target_v:.1f}V")
    time.sleep(0.5)  # Let voltage settle

    # Fire: ARM + FORCE_FIRE simultaneously
    print("     ↳ Arming + Firing...", end='', flush=True)
    cc.set_control(0, 0x80000000)  # ARM
    cc.set_control(1, 0x80000000)  # FORCE_FIRE
    time.sleep(0.01)

    # Release buttons
    cc.set_control(0, 0x00000000)
    cc.set_control(1, 0x00000000)
    print(" 🔥 FIRED!")

    # Show countdown
    print("     ↳ Waiting for FSM sequence to complete...")
    for t in range(3, 0, -1):
        print(f"     ↳ Next shot in {t}...", flush=True)
        time.sleep(1)

    # Reset FSM for next shot
    cc.set_control(2, 0x80000000)  # RESET
    time.sleep(0.01)
    cc.set_control(2, 0x00000000)
    time.sleep(0.1)
    print("     ↳ FSM reset to READY")

print()
print("=" * 80)
print("RAMP COMPLETE")
print("=" * 80)
print()
print("Analysis:")
print("  - Did you see 11 trigger pulses on Output1?")
print("  - Did Output2 voltage step down from 2.0V to 0V?")
print("  - Were the pulses long enough to observe clearly?")
print()
print("If Output2 didn't change:")
print("  → Problem is in VHDL intensity signal extraction")
print("  → Check app_reg_28(31 downto 16) usage in volo_shim")
print()

# Reset to 2.0V and normal speed
print("Resetting to normal speed...")
cc.set_control(3, pack_8bit_register(0))  # Clock divider = 0 (÷1)
cc.set_control(5, pack_8bit_register(16))  # Firing duration = 16
cc.set_control(6, pack_8bit_register(16))  # Cooling duration = 16
raw_value = voltage_to_raw(2.0)
packed = pack_16bit_register(raw_value)
cc.set_control(8, packed)
print("✓ Reset to 2.0V at normal speed")

print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
print()
print("To run again: uv run python tools/intensity_ramp_slow.py")
