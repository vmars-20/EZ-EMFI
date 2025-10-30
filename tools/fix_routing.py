#!/usr/bin/env python3
"""
Quick script to fix DS1140-PD routing connections

This connects the Cloud Compile outputs to physical outputs.
"""

import sys

try:
    from moku.instruments import MultiInstrument
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

# Connect to Moku
print("Connecting to Moku at 192.168.13.159...")
m = MultiInstrument('192.168.13.159', platform_id=2, force_connect=True)
print("✓ Connected")

# Set routing connections
print("\nConfiguring routing...")
print("Note: Slot 1 = Oscilloscope, Slot 2 = Cloud Compile")

# Try just the output connections first
connections = [
    # Cloud Compile outputs → Physical outputs
    dict(source="Slot2OutA", destination="Output1"),  # Trigger output
    dict(source="Slot2OutB", destination="Output2"),  # Intensity output

    # Cloud Compile OutputC → Oscilloscope Ch1 (FSM debug)
    dict(source="Slot2OutC", destination="Slot1InA"),
]

print("Attempting to set connections...")
for conn in connections:
    print(f"  {conn['source']} → {conn['destination']}")

m.set_connections(connections=connections)
print("✓ Routing configured!")

print("\nConnections:")
print("  Input1 → Cloud Compile InputA (trigger input)")
print("  Cloud Compile OutputA → Output1 (trigger)")
print("  Cloud Compile OutputB → Output2 (intensity)")
print("  Cloud Compile OutputC → Oscilloscope Ch1 (FSM debug)")

print("\nDone! Check the Moku GUI routing diagram.")
input("\nPress Enter to disconnect...")
m.relinquish_ownership()
