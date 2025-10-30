#!/usr/bin/env python3
"""Force disconnect from Moku (release ownership)"""

import sys

try:
    from moku.instruments import MultiInstrument
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("Attempting to connect with force_connect=True...")
try:
    m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
    print("✓ Connected")
    print("Releasing ownership...")
    m.relinquish_ownership()
    print("✓ Disconnected")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nIf force_connect didn't work, try:")
    print("  1. Close any open Moku GUI sessions")
    print("  2. Wait 60 seconds for session timeout")
    print("  3. Power cycle the Moku hardware")
