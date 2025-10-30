#!/usr/bin/env python3
"""
Debug oscilloscope data acquisition
"""

import sys
import time
from pathlib import Path

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)


print("Connecting to Moku at 192.168.8.98...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)

# Re-deploy instruments
bitstream = str(Path(__file__).parent.parent / "DS1140_debug_bits.tar")
mcc = m.set_instrument(2, CloudCompile, bitstream=bitstream)
osc = m.set_instrument(1, Oscilloscope)

# Reapply routing
m.set_connections(connections=[
    {'source': 'Input1', 'destination': 'Slot2InA'},
    {'source': 'Slot2OutA', 'destination': 'Output1'},
    {'source': 'Slot2OutB', 'destination': 'Output2'},
    {'source': 'Slot2OutC', 'destination': 'Slot1InA'},
])

print("✓ Connected")

# Check oscilloscope configuration
print("\n" + "=" * 70)
print("OSCILLOSCOPE DIAGNOSTICS")
print("=" * 70)

print("\nAttempting to read data...")
try:
    data = osc.get_data()
    print(f"✓ Data acquired")
    print(f"  Keys: {list(data.keys())}")

    if 'ch1' in data:
        print(f"  Ch1 samples: {len(data['ch1'])}")
        print(f"  Ch1 range: {min(data['ch1']):.3f}V to {max(data['ch1']):.3f}V")
        print(f"  Ch1 midpoint: {data['ch1'][len(data['ch1'])//2]:.3f}V")

        # Show first 10 samples
        print(f"  Ch1 first 10 samples: {[f'{v:.3f}' for v in data['ch1'][:10]]}")
    else:
        print("  ✗ No 'ch1' data!")

    if 'ch2' in data:
        print(f"  Ch2 samples: {len(data['ch2'])}")
        print(f"  Ch2 range: {min(data['ch2']):.3f}V to {max(data['ch2']):.3f}V")
    else:
        print("  Ch2: not present")

    if 'time' in data:
        print(f"  Time samples: {len(data['time'])}")
        print(f"  Time range: {min(data['time'])*1e3:.1f}ms to {max(data['time'])*1e3:.1f}ms")

except Exception as e:
    print(f"✗ Failed to read data: {e}")
    import traceback
    traceback.print_exc()

# Try pressing arm button and reading again
print("\n" + "=" * 70)
print("TESTING ARM BUTTON")
print("=" * 70)

print("\nPressing arm button (Control0)...")
mcc.set_control(0, 0x80000000)
time.sleep(0.01)
mcc.set_control(0, 0x00000000)

print("Waiting 0.5s for state change...")
time.sleep(0.5)

print("Reading oscilloscope data...")
try:
    data = osc.get_data()
    if 'ch1' in data:
        midpoint = data['ch1'][len(data['ch1'])//2]
        print(f"  Ch1 midpoint: {midpoint:.3f}V")

        # Decode state
        if abs(midpoint - 0.0) < 0.15:
            print(f"  State: READY (expected ARMED!)")
        elif abs(midpoint - 0.5) < 0.15:
            print(f"  State: ARMED (correct!)")
        else:
            print(f"  State: UNKNOWN")
    else:
        print("  ✗ No ch1 data!")
except Exception as e:
    print(f"✗ Failed: {e}")

# Reset
print("\nResetting FSM...")
mcc.set_control(2, 0x80000000)
time.sleep(0.01)
mcc.set_control(2, 0x00000000)

print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done")
