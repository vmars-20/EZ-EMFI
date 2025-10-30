#!/usr/bin/env python3
"""
DS1140-PD Interactive FSM Testing Script

Simple interactive tool to step through DS1140-PD FSM states while
observing voltage transitions on an external oscilloscope.

Features:
- Connect to already-deployed DS1140-PD instance
- Step-by-step FSM state transitions
- Real-time state monitoring via Moku oscilloscope
- Clear prompts for external oscilloscope observation

Usage:
    # Connect to deployed DS1140-PD instance
    python tools/test_ds1140_pd.py --ip 192.168.13.159

    # Skip state verification (faster, less accurate)
    python tools/test_ds1140_pd.py --ip 192.168.13.159 --no-verify

Author: EZ-EMFI Team
Date: 2025-01-28
"""

import argparse
import sys
import time
from typing import Optional, Dict

# Check for Moku API
try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
    MOKU_AVAILABLE = True
except ImportError:
    print("ERROR: Moku API not available")
    print("Install with: pip install moku")
    MOKU_AVAILABLE = False
    sys.exit(1)


# ============================================================================
# FSM State Definitions (copied from deploy_ds1140_pd.py)
# ============================================================================

class DS1140States:
    """DS1140-PD FSM states (3-bit encoding)"""
    READY = 0
    ARMED = 1
    FIRING = 2
    COOLING = 3
    DONE = 4
    TIMEDOUT = 5
    HARDFAULT = 7


class DS1140Voltages:
    """Expected voltages from FSM observer (OutputC → OutputA in debug mode)"""
    READY = 0.0
    ARMED = 0.5
    FIRING = 1.0
    COOLING = 1.5
    DONE = 2.0
    TIMEDOUT = 2.5
    HARDFAULT = -2.5
    TOLERANCE = 0.15


def decode_fsm_voltage(voltage: float) -> Dict:
    """Decode FSM observer voltage to state information"""
    if voltage < 0:
        return {
            'state_name': 'HARDFAULT',
            'state_id': DS1140States.HARDFAULT,
            'voltage': voltage,
            'is_fault': True
        }

    voltage_map = [
        (DS1140Voltages.READY, 'READY', DS1140States.READY),
        (DS1140Voltages.ARMED, 'ARMED', DS1140States.ARMED),
        (DS1140Voltages.FIRING, 'FIRING', DS1140States.FIRING),
        (DS1140Voltages.COOLING, 'COOLING', DS1140States.COOLING),
        (DS1140Voltages.DONE, 'DONE', DS1140States.DONE),
        (DS1140Voltages.TIMEDOUT, 'TIMEDOUT', DS1140States.TIMEDOUT),
    ]

    for expected_v, name, state_id in voltage_map:
        if abs(voltage - expected_v) < DS1140Voltages.TOLERANCE:
            return {
                'state_name': name,
                'state_id': state_id,
                'voltage': voltage,
                'is_fault': False
            }

    return {
        'state_name': f'UNKNOWN({voltage:.3f}V)',
        'state_id': None,
        'voltage': voltage,
        'is_fault': False
    }


# ============================================================================
# Control Register Helpers
# ============================================================================

class DS1140Registers:
    """DS1140-PD control register definitions"""
    ARM_PROBE = 0
    FORCE_FIRE = 1
    RESET_FSM = 2
    VOLO_READY = 15

    @staticmethod
    def pack_button(pressed: bool = True) -> int:
        """Pack button value into bit 31 of control register"""
        return 0x80000000 if pressed else 0x00000000


# ============================================================================
# Interactive Testing Class
# ============================================================================

class DS1140Tester:
    """Interactive DS1140-PD FSM tester"""

    def __init__(self, moku_ip: str, verify_states: bool = True):
        """
        Initialize tester.

        Args:
            moku_ip: Moku device IP address
            verify_states: Enable state verification via oscilloscope
        """
        self.moku_ip = moku_ip
        self.verify_states = verify_states

        self.multi_instrument = None
        self.cloud_compile = None
        self.oscilloscope = None

    def connect(self) -> bool:
        """Connect to already-deployed DS1140-PD instance"""
        print(f"Connecting to Moku at {self.moku_ip}...")
        try:
            self.multi_instrument = MultiInstrument(
                self.moku_ip,
                platform_id=2,
                force_connect=True  # Force connection to take ownership
            )
            print("✓ Connected to Moku")

            # Get instrument references (instruments should already be deployed)
            # Slot 2 = CloudCompile, Slot 1 = Oscilloscope
            try:
                # Re-deploy instruments to get handles (bitstream already loaded)
                self.cloud_compile = self.multi_instrument.set_instrument(2, CloudCompile, bitstream="/Users/vmars20/EZ-EMFI/DS1140_bits.tar")
                self.oscilloscope = self.multi_instrument.set_instrument(1, Oscilloscope)
                print("✓ Got instrument references")
                print("  CloudCompile in Slot 2")
                print("  Oscilloscope in Slot 1")

                # IMPORTANT: Re-apply routing after set_instrument() calls
                # set_instrument() clears routing, so we must reapply it
                print("  Reapplying routing...")
                connections = [
                    {'source': 'Slot2OutA', 'destination': 'Output1'},
                    {'source': 'Slot2OutB', 'destination': 'Output2'},
                    {'source': 'Slot2OutC', 'destination': 'Slot1InA'},
                ]
                self.multi_instrument.set_connections(connections=connections)
                print("✓ Routing configured")

                return True
            except Exception as e:
                print(f"✗ Failed to get instrument references: {e}")
                import traceback
                traceback.print_exc()
                return False

        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def monitor_fsm_state(self) -> Optional[Dict]:
        """Read current FSM state from oscilloscope"""
        if not self.verify_states:
            return None

        # Note: Oscilloscope monitoring requires instrument handle
        # For now, skip automatic verification - user watches external scope
        return None

    def wait_for_state(self, expected_state: str, timeout: float = 5.0) -> bool:
        """Wait for FSM to reach expected state"""
        if not self.verify_states:
            time.sleep(0.1)  # Just a brief delay
            return True

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            state = self.monitor_fsm_state()
            if state and state['state_name'] == expected_state:
                return True
            time.sleep(0.1)

        return False

    def show_current_state(self):
        """Display current FSM state"""
        if self.verify_states:
            state = self.monitor_fsm_state()
            if state:
                print(f"  Current FSM State: {state['state_name']} ({state['voltage']:.3f}V)")
                if state['is_fault']:
                    print("  ⚠️  FAULT DETECTED!")
        else:
            print("  (State verification disabled)")

    def arm_probe(self):
        """Arm the probe (READY → ARMED)"""
        print("\n" + "=" * 70)
        print("ARM PROBE")
        print("=" * 70)
        print("This will transition from READY (0.0V) → ARMED (~0.5V)")
        print("\n👁️  Watch your oscilloscope Output1...")
        input("Press Enter when ready...")

        # Press arm button
        self.cloud_compile.set_control(
            DS1140Registers.ARM_PROBE,
            DS1140Registers.pack_button(True)
        )
        time.sleep(0.01)

        # Release button
        self.cloud_compile.set_control(
            DS1140Registers.ARM_PROBE,
            DS1140Registers.pack_button(False)
        )

        print("\n✓ Arm command sent")
        print("  Output1 should show ~0.5V (ARMED state)")

        if self.verify_states:
            print("  Waiting for ARMED state...")
            if self.wait_for_state("ARMED", timeout=2.0):
                self.show_current_state()
            else:
                print("  ⚠️  Timeout waiting for ARMED state")
                self.show_current_state()

        input("\nPress Enter to continue...")

    def force_fire(self):
        """Force fire the probe"""
        print("\n" + "=" * 70)
        print("FORCE FIRE (ARM + FIRE SIMULTANEOUSLY)")
        print("=" * 70)
        print("This will arm and immediately fire to avoid network latency timeout:")
        print("  READY → ARMED → FIRING (~1.0V) → COOLING (~1.5V) → DONE (~2.0V)")
        print("\n👁️  Watch your oscilloscope Output1...")
        print("    You should see trigger pulse and voltage transitions!")
        input("Press Enter when ready...")

        # Set both ARM and FORCE_FIRE buttons simultaneously to avoid timeout
        # This works around network latency that would otherwise cause timeout
        print("\n  Setting ARM + FORCE_FIRE simultaneously...")
        self.cloud_compile.set_control(
            DS1140Registers.ARM_PROBE,
            DS1140Registers.pack_button(True)
        )
        self.cloud_compile.set_control(
            DS1140Registers.FORCE_FIRE,
            DS1140Registers.pack_button(True)
        )
        time.sleep(0.01)

        # Release both buttons
        self.cloud_compile.set_control(
            DS1140Registers.ARM_PROBE,
            DS1140Registers.pack_button(False)
        )
        self.cloud_compile.set_control(
            DS1140Registers.FORCE_FIRE,
            DS1140Registers.pack_button(False)
        )

        print("\n✓ Arm + Force fire commands sent")
        print("  Output1 should show trigger pulse!")
        print("  Sequence: FIRING → COOLING → DONE")

        if self.verify_states:
            # Try to catch each state (may be too fast)
            print("\n  Monitoring state transitions...")
            time.sleep(0.1)
            for expected in ["FIRING", "COOLING", "DONE"]:
                state = self.monitor_fsm_state()
                if state:
                    print(f"    Observed: {state['state_name']} ({state['voltage']:.3f}V)")
                time.sleep(0.1)

            # Check final state
            if self.wait_for_state("DONE", timeout=2.0):
                print("\n  ✓ Firing sequence complete")
                self.show_current_state()
            else:
                print("\n  ⚠️  Did not reach DONE state")
                self.show_current_state()

        input("\nPress Enter to continue...")

    def reset_fsm(self):
        """Reset FSM to READY state"""
        print("\n" + "=" * 70)
        print("RESET FSM")
        print("=" * 70)
        print("This will reset to READY (0.0V)")
        print("\n👁️  Watch your oscilloscope Output1...")
        input("Press Enter when ready...")

        # Press reset button
        self.cloud_compile.set_control(
            DS1140Registers.RESET_FSM,
            DS1140Registers.pack_button(True)
        )
        time.sleep(0.01)

        # Release button
        self.cloud_compile.set_control(
            DS1140Registers.RESET_FSM,
            DS1140Registers.pack_button(False)
        )

        print("\n✓ Reset command sent")
        print("  Output1 should show 0.0V (READY state)")

        if self.verify_states:
            print("  Waiting for READY state...")
            if self.wait_for_state("READY", timeout=1.0):
                self.show_current_state()
            else:
                print("  ⚠️  Timeout waiting for READY state")
                self.show_current_state()

        input("\nPress Enter to continue...")

    def run_interactive_test(self):
        """Run interactive testing session"""
        print("\n" + "=" * 70)
        print("DS1140-PD INTERACTIVE FSM TESTING")
        print("=" * 70)
        print()
        print("This script will step through FSM state transitions.")
        print("You should monitor the following on your external oscilloscope:")
        print()
        print("📊 Output1 (BNC): FSM state voltage")
        print("   - READY:     0.0V")
        print("   - ARMED:    ~0.5V")
        print("   - FIRING:   ~1.0V")
        print("   - COOLING:  ~1.5V")
        print("   - DONE:     ~2.0V")
        print()
        print("📊 Output2 (BNC): Intensity voltage (~2.0V constant)")
        print()

        # Check initial state
        print("Checking initial state...")
        self.show_current_state()
        print()
        input("Press Enter to start testing...")

        while True:
            print("\n" + "=" * 70)
            print("TEST MENU")
            print("=" * 70)
            print("  [a] Arm probe (READY → ARMED)")
            print("  [f] Force fire (ARM + FIRE simultaneously to avoid timeout)")
            print("  [r] Reset FSM (→ READY)")
            print("  [s] Show current state")
            print("  [q] Quit")
            print()
            print("  Note: Network latency causes timeout if arm/fire done separately")

            try:
                cmd = input("Select test: ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'a':
                    self.arm_probe()
                elif cmd == 'f':
                    self.force_fire()
                elif cmd == 'r':
                    self.reset_fsm()
                elif cmd == 's':
                    print()
                    self.show_current_state()
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid command")

            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except EOFError:
                break

        print("\n" + "=" * 70)
        print("Testing complete!")
        print("=" * 70)

    def disconnect(self):
        """Disconnect from Moku"""
        if self.multi_instrument:
            print("\nDisconnecting...")
            try:
                self.multi_instrument.relinquish_ownership()
                print("✓ Disconnected")
            except Exception as e:
                print(f"WARNING: Disconnect error: {e}")


# ============================================================================
# Command-Line Interface
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Interactive DS1140-PD FSM testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect to deployed instance
  python tools/test_ds1140_pd.py --ip 192.168.13.159

  # Skip state verification (faster)
  python tools/test_ds1140_pd.py --ip 192.168.13.159 --no-verify
        """
    )

    parser.add_argument('--ip', type=str, required=True, help='Moku device IP address')
    parser.add_argument('--no-verify', action='store_true', help='Skip state verification via oscilloscope')

    args = parser.parse_args()

    # Create tester
    tester = DS1140Tester(args.ip, verify_states=not args.no_verify)

    # Connect
    if not tester.connect():
        return False

    # Run interactive tests
    try:
        tester.run_interactive_test()
    except Exception as e:
        print(f"\n✗ Testing error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        tester.disconnect()

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
