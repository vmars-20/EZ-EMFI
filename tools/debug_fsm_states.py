#!/usr/bin/env python3
"""
DS1140-PD FSM State Machine Debugger

Connects to an EXISTING Moku setup (does NOT push new config).
Assumption: User has manually loaded:
  - Slot 1: Oscilloscope
  - Slot 2: CloudCompile (DS1140-PD bitstream)
  - Routing: Slot2 OutputA → Slot1 InA (FSM debug signal)

Usage:
    uv run python tools/debug_fsm_states.py

Controls:
    - Reads FSM state from Oscilloscope Ch1 (monitoring OutputA)
    - Twiddles Control0-Control8 to step through state machine
    - Displays real-time state transitions

Control Register Map (DS1140-PD):
    Control0  = Arm Probe (button, bit 31)
    Control1  = Force Fire (button, bit 31)
    Control2  = Reset FSM (button, bit 31)
    Control3  = Clock Divider (16-bit counter value)
    Control4  = Arm Timeout (16-bit milliseconds)
    Control5  = Firing Duration (16-bit microseconds)
    Control6  = Cooling Duration (16-bit milliseconds)
    Control7  = Trigger Threshold (16-bit voltage scaled)
    Control8  = Intensity (16-bit voltage scaled)
    Control15 = VOLO_READY bits [31:29]
"""

import time
import sys
from typing import Optional, Tuple

try:
    from moku.instruments import MultiInstrument
except ImportError:
    print("ERROR: moku package not found. Run: uv sync")
    sys.exit(1)


# FSM State Decoding (from OutputA via oscilloscope)
# Based on OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md voltage levels
STATE_MAP = {
    "READY":     0.36,   # 0x0000 → ~0.36V
    "ARMED":     0.71,   # 0x0001 → ~0.71V
    "FIRING":    1.07,   # 0x0002 → ~1.07V
    "COOLING":   1.43,   # 0x0003 → ~1.43V
    "DONE":      1.79,   # 0x0004 → ~1.79V
    "TIMEDOUT":  2.14,   # 0x0005 → ~2.14V
    "HARDFAULT": -2.5,   # Negative voltage = fault condition
}

# Reverse lookup with tolerance
def decode_fsm_state(voltage: float, tolerance: float = 0.15) -> Optional[str]:
    """Decode FSM state from oscilloscope voltage reading."""
    for state, expected_v in STATE_MAP.items():
        if abs(voltage - expected_v) < tolerance:
            return state
    return f"UNKNOWN({voltage:.2f}V)"


class DS1140PDDebugger:
    """Debug DS1140-PD FSM state machine via existing Moku setup."""

    def __init__(self, ip: str = "192.168.8.98", platform_id: int = 2):
        """
        Connect to existing MultiInstrument setup.
        Gets handles to already-deployed instruments (bitstream already loaded by user).
        """
        print(f"🔌 Connecting to Moku at {ip}...")
        self.m = MultiInstrument(ip, platform_id=platform_id, force_connect=True)

        # Import instrument classes
        from moku.instruments import Oscilloscope, CloudCompile

        print("📡 Getting instrument handles (no bitstream upload)...")

        # Get handles to existing instruments
        # Note: set_instrument() without bitstream parameter should connect to existing
        self.osc = self.m.set_instrument(1, Oscilloscope)
        self.mcc = self.m.set_instrument(2, CloudCompile)

        print("✅ Connected to existing setup")
        print(f"   Slot 1: Oscilloscope")
        print(f"   Slot 2: CloudCompile (DS1140-PD)")

    def read_fsm_state(self, poll_count: int = 5) -> Tuple[str, float]:
        """
        Read current FSM state from oscilloscope Ch1.

        Args:
            poll_count: Number of samples to average (handle latency)

        Returns:
            (state_name, voltage) tuple
        """
        voltages = []
        for _ in range(poll_count):
            data = self.osc.get_data()
            # Sample middle of waveform buffer
            midpoint = len(data['ch1']) // 2
            voltages.append(data['ch1'][midpoint])
            time.sleep(0.05)  # 50ms between samples

        avg_voltage = sum(voltages) / len(voltages)
        state = decode_fsm_state(avg_voltage)
        return state, avg_voltage

    def set_control(self, reg: int, value: int, description: str = ""):
        """Set control register and display action."""
        self.mcc.set_control(reg, value)
        desc_str = f" ({description})" if description else ""
        print(f"   📝 Control{reg} = 0x{value:08X}{desc_str}")

    def wait_and_check_state(self, expected_state: Optional[str] = None, timeout: float = 2.0):
        """Wait for state transition and verify."""
        time.sleep(0.2)  # Initial settling time

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            state, voltage = self.read_fsm_state(poll_count=3)

            if expected_state and state == expected_state:
                print(f"✅ State: {state} ({voltage:.2f}V)")
                return state
            elif not expected_state:
                print(f"📊 State: {state} ({voltage:.2f}V)")
                return state

            time.sleep(0.1)

        # Timeout
        state, voltage = self.read_fsm_state(poll_count=3)
        if expected_state:
            print(f"⚠️  Timeout waiting for {expected_state}, got {state} ({voltage:.2f}V)")
        return state

    def initialize_volo_ready(self):
        """Initialize VOLO_READY bits in Control15."""
        print("\n🚀 Initializing VOLO_READY...")
        self.set_control(15, 0xE0000000, "volo_ready | user_enable | clk_enable")
        time.sleep(0.1)
        state = self.wait_and_check_state()
        return state

    def reset_fsm(self):
        """Reset FSM to READY state."""
        print("\n🔄 Resetting FSM...")
        self.set_control(2, 0x80000000, "Reset FSM (pulse)")
        time.sleep(0.1)
        self.set_control(2, 0x00000000, "Clear reset")
        return self.wait_and_check_state("READY")

    def arm_probe(self, timeout_ms: int = 5000):
        """Arm the probe (transition READY → ARMED)."""
        print(f"\n🎯 Arming probe (timeout={timeout_ms}ms)...")

        # Set arm timeout
        timeout_value = int((timeout_ms / 1000.0) * 0xFFFF)  # Scale to 16-bit
        self.set_control(4, timeout_value << 16, f"Arm timeout {timeout_ms}ms")

        # Pulse arm button
        self.set_control(0, 0x80000000, "Arm probe (pulse)")
        time.sleep(0.1)
        self.set_control(0, 0x00000000, "Clear arm button")

        return self.wait_and_check_state("ARMED", timeout=1.0)

    def force_fire(self, firing_us: int = 100, cooling_ms: int = 1000, intensity_v: float = 2.0):
        """
        Force fire the probe (bypass trigger, transition ARMED → FIRING → COOLING → DONE).

        Args:
            firing_us: Firing duration in microseconds
            cooling_ms: Cooling duration in milliseconds
            intensity_v: Output intensity voltage (0-5V range)
        """
        print(f"\n🔥 Force firing (duration={firing_us}µs, cooling={cooling_ms}ms, intensity={intensity_v}V)...")

        # Set firing parameters
        firing_value = int((firing_us / 1000.0) * 0xFFFF)  # Scale to 16-bit
        cooling_value = int((cooling_ms / 1000.0) * 0xFFFF)
        intensity_value = int((intensity_v / 5.0) * 0xFFFF)  # Moku uses ±5V scale

        self.set_control(5, firing_value << 16, f"Firing duration {firing_us}µs")
        self.set_control(6, cooling_value << 16, f"Cooling duration {cooling_ms}ms")
        self.set_control(8, intensity_value << 16, f"Intensity {intensity_v}V")

        # Pulse force fire button
        self.set_control(1, 0x80000000, "Force fire (pulse)")
        time.sleep(0.1)
        self.set_control(1, 0x00000000, "Clear force fire button")

        # Watch state transitions (FIRING → COOLING → DONE)
        print("\n   Watching state transitions...")
        self.wait_and_check_state("FIRING", timeout=0.5)
        self.wait_and_check_state("COOLING", timeout=(firing_us / 1000.0) + 0.5)
        self.wait_and_check_state("DONE", timeout=(cooling_ms / 1000.0) + 0.5)

    def run_state_machine_demo(self):
        """Run complete state machine demonstration."""
        print("\n" + "="*60)
        print("DS1140-PD FSM State Machine Demo")
        print("="*60)

        # Initialize
        self.initialize_volo_ready()

        # Reset to READY
        self.reset_fsm()

        # Arm probe
        self.arm_probe(timeout_ms=10000)

        # Force fire with short pulse
        self.force_fire(firing_us=50, cooling_ms=500, intensity_v=1.5)

        # Reset back to READY
        self.reset_fsm()

        print("\n" + "="*60)
        print("✅ State machine demo complete!")
        print("="*60)

    def interactive_mode(self):
        """Interactive control register twiddling."""
        print("\n" + "="*60)
        print("Interactive FSM Control Mode")
        print("="*60)
        print("\nCommands:")
        print("  r     - Read current state")
        print("  init  - Initialize VOLO_READY")
        print("  reset - Reset FSM")
        print("  arm   - Arm probe")
        print("  fire  - Force fire probe")
        print("  demo  - Run full state machine demo")
        print("  q     - Quit")
        print("="*60)

        while True:
            try:
                cmd = input("\n> ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'r':
                    state, voltage = self.read_fsm_state()
                    print(f"📊 Current state: {state} ({voltage:.2f}V)")
                elif cmd == 'init':
                    self.initialize_volo_ready()
                elif cmd == 'reset':
                    self.reset_fsm()
                elif cmd == 'arm':
                    self.arm_probe()
                elif cmd == 'fire':
                    self.force_fire()
                elif cmd == 'demo':
                    self.run_state_machine_demo()
                else:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def close(self):
        """Close connection."""
        print("\n👋 Closing connection...")
        self.m.close()


def main():
    """Main entry point."""
    debugger = None
    try:
        debugger = DS1140PDDebugger(ip="192.168.8.98")

        # Run interactive mode by default
        debugger.interactive_mode()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if debugger:
            debugger.close()


if __name__ == "__main__":
    main()
