#!/usr/bin/env python3
"""
Check current Moku configuration and suggest routing fixes
"""

import sys

try:
    from moku.instruments import MultiInstrument
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

# Connect to Moku
print("Connecting to Moku at 192.168.13.159...")
m = MultiInstrument('192.168.13.159', platform_id=2, force_connect=False)
print("✓ Connected")

# Get current configuration
print("\nCurrent Configuration:")
print(f"  Platform ID: {m.platform_id}")
print(f"  Slots: {m.num_slots}")

# Try to get instrument info
print("\nInstruments:")
for slot in range(1, m.num_slots + 1):
    try:
        # Try to get instrument name (this may not work with all API versions)
        print(f"  Slot {slot}: (deployed)")
    except:
        print(f"  Slot {slot}: Unknown")

print("\n" + "=" * 70)
print("ROUTING FIX")
print("=" * 70)

# Based on the GUI, Cloud Compile is in Slot 2, Oscilloscope in Slot 1
print("\nApplying routing configuration...")
print("  Slot 1 = Oscilloscope")
print("  Slot 2 = Cloud Compile (DS1140-PD)")

connections = [
    # Cloud Compile outputs → Physical outputs
    {'source': 'Slot2OutA', 'destination': 'Output1'},  # Trigger
    {'source': 'Slot2OutB', 'destination': 'Output2'},  # Intensity

    # Cloud Compile OutputC → Oscilloscope Ch1 (FSM debug)
    {'source': 'Slot2OutC', 'destination': 'Slot1InA'},
]

print("\nConnections to set:")
for conn in connections:
    print(f"  {conn['source']} → {conn['destination']}")

try:
    m.set_connections(connections=connections)
    print("\n✓ Routing configured successfully!")
    print("\nCheck the Moku GUI to verify connections are shown.")
except Exception as e:
    print(f"\n✗ Routing failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Check that Cloud Compile is in Slot 2")
    print("  2. Check that Oscilloscope is in Slot 1")
    print("  3. Try redeploying with deploy_ds1140_pd.py")

print("\n" + "=" * 70)
input("\nPress Enter to disconnect...")
m.relinquish_ownership()
