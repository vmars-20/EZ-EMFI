#!/usr/bin/env python3
"""
Quick FSM Validation Script for DS1140-PD

Tests basic FSM state transitions and validates hardware connectivity.
Non-interactive version for automated debugging.
"""

import sys
import time
from pathlib import Path

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("ERROR: Moku API not available")
    sys.exit(1)


class DS1140Validator:
    """Quick FSM validator"""

    def __init__(self, moku_ip: str):
        self.moku_ip = moku_ip
        self.multi = None
        self.mcc = None
        self.osc = None

    def connect(self):
        """Connect to deployed DS1140-PD"""
        print(f"Connecting to Moku at {self.moku_ip}...")
        self.multi = MultiInstrument(self.moku_ip, platform_id=2, force_connect=True)

        # Re-deploy to get handles (bitstream already loaded)
        bitstream_path = str(Path(__file__).parent.parent / "DS1140_debug_bits.tar")
        self.mcc = self.multi.set_instrument(2, CloudCompile, bitstream=bitstream_path)
        self.osc = self.multi.set_instrument(1, Oscilloscope)

        # Reapply routing (set_instrument clears it)
        self.multi.set_connections(connections=[
            {'source': 'Input1', 'destination': 'Slot2InA'},
            {'source': 'Slot2OutA', 'destination': 'Output1'},
            {'source': 'Slot2OutB', 'destination': 'Output2'},
            {'source': 'Slot2OutC', 'destination': 'Slot1InA'},
        ])

        print("✓ Connected and routing configured")

    def read_fsm_voltage(self) -> float:
        """Read FSM voltage from oscilloscope"""
        data = self.osc.get_data()
        if 'ch1' not in data:
            return None
        midpoint = len(data['ch1']) // 2
        return data['ch1'][midpoint]

    def decode_state(self, voltage: float) -> str:
        """Decode voltage to state name"""
        if voltage < 0:
            return "HARDFAULT"

        states = [
            (0.0, 0.15, "READY"),
            (0.5, 0.15, "ARMED"),
            (1.0, 0.15, "FIRING"),
            (1.5, 0.15, "COOLING"),
            (2.0, 0.15, "DONE"),
            (2.5, 0.15, "TIMEDOUT"),
        ]

        for expected, tol, name in states:
            if abs(voltage - expected) < tol:
                return name

        return f"UNKNOWN({voltage:.3f}V)"

    def wait_for_state(self, expected: str, timeout: float = 2.0) -> bool:
        """Wait for FSM to reach expected state"""
        start = time.time()
        while (time.time() - start) < timeout:
            voltage = self.read_fsm_voltage()
            if voltage is not None:
                state = self.decode_state(voltage)
                if state == expected:
                    print(f"    ✓ {expected}: {voltage:.3f}V")
                    return True
            time.sleep(0.05)

        voltage = self.read_fsm_voltage()
        state = self.decode_state(voltage) if voltage else "NO_DATA"
        print(f"    ✗ Timeout waiting for {expected}, got {state}")
        return False

    def press_button(self, reg_num: int):
        """Press and release button register"""
        self.mcc.set_control(reg_num, 0x80000000)
        time.sleep(0.01)
        self.mcc.set_control(reg_num, 0x00000000)

    def test_reset(self) -> bool:
        """Test FSM reset"""
        print("\n[Test 1] FSM Reset")
        self.press_button(2)  # Control2 = reset_fsm
        return self.wait_for_state("READY", timeout=1.0)

    def test_arm(self) -> bool:
        """Test arm transition"""
        print("\n[Test 2] Arm Probe")
        self.press_button(0)  # Control0 = arm_probe
        return self.wait_for_state("ARMED", timeout=2.0)

    def test_force_fire(self) -> bool:
        """Test force fire (arm + fire simultaneously)"""
        print("\n[Test 3] Force Fire")
        # Set both buttons simultaneously to avoid timeout
        self.mcc.set_control(0, 0x80000000)  # arm
        self.mcc.set_control(1, 0x80000000)  # force_fire
        time.sleep(0.01)
        self.mcc.set_control(0, 0x00000000)
        self.mcc.set_control(1, 0x00000000)

        # Watch for FIRING state (may be fast)
        time.sleep(0.05)
        voltage = self.read_fsm_voltage()
        print(f"    Mid-sequence: {self.decode_state(voltage)} ({voltage:.3f}V)")

        # Wait for DONE
        return self.wait_for_state("DONE", timeout=2.0)

    def test_timeout(self) -> bool:
        """Test arm timeout (no trigger provided)"""
        print("\n[Test 4] Arm Timeout")

        # First reset to READY
        self.press_button(2)
        time.sleep(0.1)

        # Set very short timeout for testing
        timeout_cycles = 10  # Very short (will timeout almost immediately)
        self.mcc.set_control(4, (timeout_cycles << 16))
        print(f"    Set timeout to {timeout_cycles} cycles")

        # Arm and wait for timeout
        self.press_button(0)
        time.sleep(0.5)  # Wait a bit longer than timeout

        voltage = self.read_fsm_voltage()
        state = self.decode_state(voltage)
        print(f"    Result: {state} ({voltage:.3f}V)")

        # Reset timeout to normal
        self.mcc.set_control(4, (4095 << 16))
        print(f"    Reset timeout to 4095 cycles")

        return state == "TIMEDOUT"

    def run_validation(self):
        """Run full validation suite"""
        print("=" * 70)
        print("DS1140-PD FSM VALIDATION")
        print("=" * 70)

        # Check initial state
        print("\nInitial state check...")
        voltage = self.read_fsm_voltage()
        state = self.decode_state(voltage)
        print(f"  Current: {state} ({voltage:.3f}V)")

        # Run tests
        results = {
            "Reset": self.test_reset(),
            "Arm": self.test_arm(),
            "Force Fire": self.test_force_fire(),
            "Timeout": self.test_timeout(),
        }

        # Reset to clean state
        print("\n[Cleanup] Resetting to READY...")
        self.press_button(2)
        time.sleep(0.1)

        # Summary
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        for test, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {test:20s} {status}")

        all_passed = all(results.values())
        print()
        if all_passed:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed")

        return all_passed

    def disconnect(self):
        """Disconnect from Moku"""
        if self.multi:
            self.multi.relinquish_ownership()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate DS1140-PD FSM behavior")
    parser.add_argument('--ip', type=str, default='192.168.8.98', help='Moku IP address')
    args = parser.parse_args()

    validator = DS1140Validator(args.ip)

    try:
        validator.connect()
        success = validator.run_validation()
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        validator.disconnect()

    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
