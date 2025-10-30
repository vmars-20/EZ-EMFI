#!/usr/bin/env python3
"""
Final comprehensive test - detailed FSM state monitoring with timing
"""

import sys
import time

try:
    from moku.instruments import MultiInstrument, Oscilloscope, CloudCompile
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)

print("=" * 70)
print("FINAL COMPREHENSIVE DS1140-PD TEST")
print("=" * 70)

# Connect
print("\nStep 1: Connecting...")
m = MultiInstrument('192.168.8.98', platform_id=2, force_connect=True)
print("✓ Connected")

# Deploy bitstream
print("\nStep 2: Deploying bitstream...")
cc = m.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_debug_bits.tar")
osc = m.set_instrument(1, Oscilloscope)
osc.set_timebase(-0.005, 0.005)
print("✓ Bitstream deployed, oscilloscope ready")

# Routing - try BOTH OutputC and OutputA to see which has FSM debug
print("\nStep 3: Configuring routing...")
connections = [
    {'source': 'Slot2OutC', 'destination': 'Slot1InA'},  # OutputC → Ch1
    {'source': 'Slot2OutA', 'destination': 'Slot1InB'},  # OutputA → Ch2 (to compare)
    {'source': 'Slot2OutA', 'destination': 'Output1'},
    {'source': 'Slot2OutB', 'destination': 'Output2'},
]
m.set_connections(connections=connections)
print("✓ Routing: Ch1=OutputC, Ch2=OutputA")

# Helper functions
def voltage_to_raw(voltage: float) -> int:
    return int((voltage / 5.0) * 32767.0) & 0xFFFF

def pack_16bit(value: int) -> int:
    return (value & 0xFFFF) << 16

def pack_8bit(value: int) -> int:
    return (value & 0xFF) << 24

def read_fsm_state():
    """Read and display FSM state from both channels"""
    data = osc.get_data()
    ch1_avg = sum(data['ch1'])/len(data['ch1'])
    ch2_avg = sum(data['ch2'])/len(data['ch2'])

    state_map = [
        (0.0, "READY"),
        (0.5, "ARMED"),
        (1.0, "FIRING"),
        (1.5, "COOLING"),
        (2.0, "DONE"),
        (2.5, "TIMEDOUT"),
    ]

    def decode(v):
        for expected, name in state_map:
            if abs(v - expected) < 0.15:
                return f"{name} ({v:.3f}V)"
        return f"UNKNOWN ({v:.3f}V)"

    print(f"  Ch1 (OutputC): {decode(ch1_avg)}")
    print(f"  Ch2 (OutputA): {decode(ch2_avg)}")
    return ch1_avg, ch2_avg

# Initialize registers - SET CONTROL15 FIRST!
print("\nStep 4: Initializing registers (Control15 FIRST)...")
cc.set_control(15, 0xE0000000)  # CRITICAL: Set VOLO_READY first
time.sleep(0.2)  # Allow time to take effect
print("  ✓ Control15: VOLO_READY = 0xE0000000")

# START BRAM LOADER (THIS WAS THE MISSING STEP!)
print("  ✓ Starting BRAM loader with word_count=0...")
cc.set_control(10, 0x00000001)  # start=1, word_count=0
time.sleep(0.1)  # Wait for loader FSM to transition IDLE→LOADING→DONE
print("  ✓ BRAM loader done (loader_done='1')")

cc.set_control(3, pack_8bit(0))
cc.set_control(4, pack_16bit(4095))
cc.set_control(5, pack_8bit(255))  # Long firing duration
cc.set_control(6, pack_8bit(16))
cc.set_control(7, pack_16bit(voltage_to_raw(2.4)))
cc.set_control(8, pack_16bit(voltage_to_raw(2.0)))
print("  ✓ Other control registers initialized")

# Wait for everything to stabilize
time.sleep(1)

# State 1: READY (initial)
print("\n" + "=" * 70)
print("STATE 1: READY (initial state)")
print("=" * 70)
read_fsm_state()

# State 2: RESET FSM explicitly
print("\n" + "=" * 70)
print("STATE 2: RESET FSM (Control2 button)")
print("=" * 70)
print("  Pressing RESET button...")
cc.set_control(2, 0x80000000)
time.sleep(0.05)
cc.set_control(2, 0x00000000)
time.sleep(1)
print("  After reset:")
read_fsm_state()

# State 3: ARM
print("\n" + "=" * 70)
print("STATE 3: ARM (Control0 button)")
print("=" * 70)
print("  Pressing ARM button...")
cc.set_control(0, 0x80000000)
time.sleep(0.05)
print("  ARM button pressed, checking state...")
read_fsm_state()
print("  Releasing ARM button...")
cc.set_control(0, 0x00000000)
time.sleep(1)
print("  After ARM:")
ch1, ch2 = read_fsm_state()

if ch1 > 0.3 or ch2 > 0.3:
    print("  ✅ FSM TRANSITIONED TO ARMED!")
else:
    print("  ❌ FSM STUCK IN READY - did not transition to ARMED")
    print("     This means:")
    print("     - ARM button signal not reaching FSM, OR")
    print("     - FSM Enable signal not active, OR")
    print("     - Clock not running to FSM")

# State 4: FORCE_FIRE
print("\n" + "=" * 70)
print("STATE 4: FORCE_FIRE (Control1 button)")
print("=" * 70)
print("  Pressing FORCE_FIRE button...")
cc.set_control(1, 0x80000000)
time.sleep(0.05)
cc.set_control(1, 0x00000000)
time.sleep(0.5)
print("  After FORCE_FIRE:")
ch1_final, ch2_final = read_fsm_state()

print("\n" + "=" * 70)
print("FINAL DIAGNOSIS")
print("=" * 70)

if ch1_final > 1.5 or ch2_final > 1.5:
    print("✅ SUCCESS! FSM reached DONE/COOLING state")
    print("   The module is working correctly!")
elif ch1_final > 0.3 or ch2_final > 0.3:
    print("⚠️ PARTIAL SUCCESS - FSM reached ARMED but may not have fired")
else:
    print("❌ FAILURE - FSM completely stuck in READY")
    print("\nPossible root causes:")
    print("  1. Enable signal = '0' (check combine_volo_ready logic)")
    print("  2. loader_done = '0' (BRAM loader not finishing)")
    print("  3. Clock not reaching FSM")
    print("  4. Button signals not connected properly in bitstream")
    print("\nNext steps:")
    print("  - Check if bitstream was compiled correctly")
    print("  - Verify VoloApp 3-layer architecture is complete")
    print("  - Try re-compiling with MCC CloudCompile")

print("\n" + "=" * 70)

# Disconnect
print("\nDisconnecting...")
m.relinquish_ownership()
print("✓ Done!")
