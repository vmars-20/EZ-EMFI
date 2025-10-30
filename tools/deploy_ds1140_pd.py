#!/usr/bin/env python3
"""
DS1140-PD EMFI Probe Driver Deployment Script

Deploys the DS1140-PD refactored EMFI probe driver to Moku hardware with
real-time FSM monitoring and comprehensive testing utilities.

Features:
- Automatic Moku device discovery
- Multi-instrument setup (CloudCompile + Oscilloscope)
- FSM state monitoring via OutputC (voltage decoding)
- Control register initialization (Control0-Control8)
- Hardware validation patterns
- Interactive testing mode

Architecture:
    Moku:Go Platform
    ├─ Slot 1: Oscilloscope (FSM monitoring)
    └─ Slot 2: CloudCompile (DS1140-PD bitstream)
         ├─ InputA: External trigger signal
         ├─ InputB: Current monitor (optional)
         ├─ OutputA: Trigger output (to EMFI probe)
         ├─ OutputB: Intensity output (to EMFI probe)
         └─ OutputC: FSM debug (to Oscilloscope Ch1)

Usage:
    # Auto-discover Moku device
    python tools/deploy_ds1140_pd.py

    # Specify IP address
    python tools/deploy_ds1140_pd.py --ip 192.168.13.159

    # Skip interactive testing
    python tools/deploy_ds1140_pd.py --no-test

Author: EZ-EMFI Team
Date: 2025-01-28
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List

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
# DS1140-PD FSM States
# ============================================================================

class DS1140States:
    """DS1140-PD FSM states (3-bit encoding)"""
    READY = 0
    ARMED = 1
    FIRING = 2
    COOLING = 3
    DONE = 4
    TIMEDOUT = 5
    HARDFAULT = 7  # Negative voltage indicates fault


class DS1140Voltages:
    """
    Expected voltages from FSM observer (OutputC).

    Configuration (from ds1140_pd_volo_main.vhd):
        NUM_STATES = 8 (3-bit FSM)
        V_MIN = 0.0
        V_MAX = 2.5
        FAULT_STATE_THRESHOLD = 7 (HARDFAULT)

    Voltage calculation: V = V_MIN + (state_index * (V_MAX - V_MIN) / (num_normal - 1))
    6 normal states (0-5), so v_step = 2.5 / 5 = 0.5V
    State 6 is unused, State 7 is HARDFAULT (-2.5V sign-flip)
    """
    READY = 0.0       # State 0: 0.0V
    ARMED = 0.5       # State 1: 0.5V (approx 0.36V after DAC quantization)
    FIRING = 1.0      # State 2: 1.0V (approx 0.71V)
    COOLING = 1.5     # State 3: 1.5V (approx 1.07V)
    DONE = 2.0        # State 4: 2.0V (approx 1.43V)
    TIMEDOUT = 2.5    # State 5: 2.5V (approx 1.79V)
    HARDFAULT = -2.5  # State 7: -2.5V (sign-flip fault)

    # Tolerance for voltage comparisons (±0.15V for DAC quantization)
    TOLERANCE = 0.15


def decode_fsm_voltage(voltage: float) -> Dict:
    """
    Decode FSM observer voltage to state information.

    Args:
        voltage: Oscilloscope reading from OutputC (V)

    Returns:
        Dictionary with state information:
            - state_name: "READY", "ARMED", "FIRING", etc.
            - state_id: Numeric state ID (0-7)
            - voltage: Raw voltage reading
            - is_fault: Boolean indicating fault condition
    """
    # Check for fault state first (negative voltage)
    if voltage < 0:
        return {
            'state_name': 'HARDFAULT',
            'state_id': DS1140States.HARDFAULT,
            'voltage': voltage,
            'is_fault': True
        }

    # Map voltage to state with tolerance
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

    # Unknown state
    return {
        'state_name': f'UNKNOWN({voltage:.3f}V)',
        'state_id': None,
        'voltage': voltage,
        'is_fault': False
    }


# ============================================================================
# DS1140-PD Control Register Helpers
# ============================================================================

class DS1140Registers:
    """DS1140-PD control register definitions"""

    # Register numbers (Control0-Control8)
    ARM_PROBE = 0
    FORCE_FIRE = 1
    RESET_FSM = 2
    CLOCK_DIVIDER = 3
    ARM_TIMEOUT = 4
    FIRING_DURATION = 5
    COOLING_DURATION = 6
    TRIGGER_THRESHOLD = 7
    INTENSITY = 8

    # Special registers
    VOLO_READY = 15  # Control15[31:29] = volo_ready, user_enable, clk_enable

    @staticmethod
    def voltage_to_raw(voltage: float) -> int:
        """
        Convert voltage to 16-bit raw value for Moku platform.

        Moku uses ±5V full scale (NOT ±1V!):
            voltage = (raw_value / 32767.0) * 5.0
            raw_value = int((voltage / 5.0) * 32767.0)

        Args:
            voltage: Desired voltage (-5.0 to +5.0)

        Returns:
            16-bit raw value (0x0000 to 0x7FFF for positive voltages)
        """
        if voltage < -5.0 or voltage > 5.0:
            raise ValueError(f"Voltage {voltage}V out of range (±5V)")
        return int((voltage / 5.0) * 32767.0) & 0xFFFF

    @staticmethod
    def raw_to_voltage(raw_value: int) -> float:
        """
        Convert 16-bit raw value to voltage.

        Args:
            raw_value: 16-bit raw value

        Returns:
            Voltage in range ±5V
        """
        # Treat as signed 16-bit
        if raw_value > 32767:
            raw_value -= 65536
        return (raw_value / 32767.0) * 5.0

    @staticmethod
    def pack_16bit_register(value: int) -> int:
        """
        Pack 16-bit value into upper bits of 32-bit control register.

        DS1140-PD uses MSB-first packing:
            Control4: arm_timeout[15:0] -> app_reg_24[31:16]
            Control7: trigger_threshold[15:0] -> app_reg_27[31:16]
            Control8: intensity[15:0] -> app_reg_28[31:16]

        Args:
            value: 16-bit value (0x0000 to 0xFFFF)

        Returns:
            32-bit control register value
        """
        return (value & 0xFFFF) << 16

    @staticmethod
    def pack_8bit_register(value: int) -> int:
        """
        Pack 8-bit value into upper bits of 32-bit control register.

        DS1140-PD uses MSB-first packing:
            Control3: clock_divider[7:0] -> app_reg_23[31:24]
            Control5: firing_duration[7:0] -> app_reg_25[31:24]
            Control6: cooling_duration[7:0] -> app_reg_26[31:24]

        Args:
            value: 8-bit value (0x00 to 0xFF)

        Returns:
            32-bit control register value
        """
        return (value & 0xFF) << 24

    @staticmethod
    def pack_button(pressed: bool = True) -> int:
        """
        Pack button value into bit 31 of control register.

        DS1140-PD buttons:
            Control0: arm_probe -> app_reg_20[31]
            Control1: force_fire -> app_reg_21[31]
            Control2: reset_fsm -> app_reg_22[31]

        Args:
            pressed: True to press button, False to release

        Returns:
            32-bit control register value
        """
        return 0x80000000 if pressed else 0x00000000


# ============================================================================
# Moku Device Discovery
# ============================================================================

def discover_moku_devices() -> List[str]:
    """
    Discover Moku devices on local network.

    Returns:
        List of IP addresses for discovered Moku devices
    """
    print("Scanning for Moku devices on local network...")
    print("(This may take 10-15 seconds)")

    try:
        from moku import MokuClient
        devices = MokuClient.discover()

        if not devices:
            print("No Moku devices found on network")
            return []

        print(f"\nFound {len(devices)} Moku device(s):")
        for i, device in enumerate(devices, 1):
            print(f"  [{i}] {device['serial']} - {device['model']} - {device['ip_addr']}")

        return [d['ip_addr'] for d in devices]

    except ImportError:
        print("WARNING: MokuClient.discover() not available")
        print("Using manual IP entry")
        return []
    except Exception as e:
        print(f"WARNING: Discovery failed: {e}")
        return []


# ============================================================================
# DS1140-PD Deployment Class
# ============================================================================

class DS1140Deployment:
    """Main deployment class for DS1140-PD with FSM monitoring"""

    def __init__(self, moku_ip: str, bitstream_path: Path):
        """
        Initialize deployment.

        Args:
            moku_ip: Moku device IP address
            bitstream_path: Path to DS1140-PD bitstream (.tar or .tar.gz)
        """
        self.moku_ip = moku_ip
        self.bitstream_path = bitstream_path

        self.multi_instrument = None
        self.cloud_compile = None
        self.oscilloscope = None

    def connect(self) -> bool:
        """Connect to Moku device"""
        print(f"Connecting to Moku at {self.moku_ip}...")
        try:
            self.multi_instrument = MultiInstrument(
                self.moku_ip,
                platform_id=2,  # Moku:Go (change to 1 for Moku:Lab, 4 for Moku:Pro)
                force_connect=True
            )
            print("✓ Connected to Moku")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def deploy_bitstream(self) -> bool:
        """Deploy DS1140-PD bitstream to Slot 2"""
        print(f"Deploying bitstream: {self.bitstream_path.name}")

        if not self.bitstream_path.exists():
            print(f"✗ Bitstream not found: {self.bitstream_path}")
            return False

        try:
            # CloudCompile requires bitstream parameter in set_instrument()
            self.cloud_compile = self.multi_instrument.set_instrument(
                2,
                CloudCompile,
                bitstream=str(self.bitstream_path)
            )
            print("✓ Bitstream deployed to Slot 2")
            return True

        except Exception as e:
            print(f"✗ Bitstream deployment failed: {e}")
            return False

    def setup_oscilloscope(self) -> bool:
        """Setup Oscilloscope in Slot 1 to monitor FSM output"""
        print("Setting up oscilloscope for FSM monitoring...")
        try:
            # Deploy oscilloscope (mimic moku_go.py approach)
            self.oscilloscope = self.multi_instrument.set_instrument(1, Oscilloscope)

            # Configure timebase only (frontend settings handled by Moku GUI)
            # Channel 1 = Slot2OutA = FSM debug output (DEBUG MODE!)
            # Channel 2 = Slot2OutB = Intensity output
            self.oscilloscope.set_timebase(-5e-3, 5e-3)  # ±5ms window

            print("✓ Oscilloscope configured (Ch1 = FSM debug)")
            print("  Note: Configure voltage scales (10Vpp) in Moku GUI")
            return True

        except Exception as e:
            print(f"✗ Oscilloscope setup failed: {e}")
            return False

    def setup_routing(self) -> bool:
        """Configure routing between slots and physical I/O"""
        print("Configuring routing...")

        # Detect if using debug bitstream
        is_debug = "debug" in str(self.bitstream_path).lower()

        try:
            connections = [
                # External trigger → DS1140-PD InputA
                dict(source="Input1", destination="Slot2InA"),

                # DS1140-PD outputs
                dict(source="Slot2OutA", destination="Output1"),    # OutputA → Physical Output1
                dict(source="Slot2OutB", destination="Output2"),    # OutputB → Physical Output2
                dict(source="Slot2OutC", destination="Slot1InA"),   # OutputC → Oscilloscope Ch1
            ]

            self.multi_instrument.set_connections(connections=connections)

            if is_debug:
                print("✓ Routing configured (DEBUG MODE)")
                print("  Input1 → DS1140-PD Trigger Input")
                print("  Output1 ← FSM Debug (OutputA swapped in debug bitstream)")
                print("  Output2 ← Intensity")
                print("  Osc Ch1 ← FSM Debug")
            else:
                print("✓ Routing configured (PRODUCTION MODE)")
                print("  Input1 → DS1140-PD Trigger Input")
                print("  Output1 ← Trigger Output (to EMFI probe)")
                print("  Output2 ← Intensity Output (to EMFI probe)")
                print("  Osc Ch1 ← FSM Debug (OutputC, internal)")
            return True

        except Exception as e:
            print(f"✗ Routing setup failed: {e}")
            return False

    def initialize_registers(self) -> bool:
        """Initialize DS1140-PD control registers with safe defaults"""
        print("Initializing control registers...")
        try:
            # Control15: VOLO_READY bits [31:29]
            self.cloud_compile.set_control(DS1140Registers.VOLO_READY, 0xE0000000)
            print("  Control15: VOLO_READY enabled")

            # Control3: Clock divider (0 = no division)
            self.cloud_compile.set_control(
                DS1140Registers.CLOCK_DIVIDER,
                DS1140Registers.pack_8bit_register(0)
            )
            print("  Control3: Clock divider = 0 (÷1)")

            # Control4: Arm timeout (4095 cycles max, accommodate network latency)
            self.cloud_compile.set_control(
                DS1140Registers.ARM_TIMEOUT,
                DS1140Registers.pack_16bit_register(4095)
            )
            print("  Control4: Arm timeout = 4095 cycles (max, for network latency)")

            # Control5: Firing duration (16 cycles)
            self.cloud_compile.set_control(
                DS1140Registers.FIRING_DURATION,
                DS1140Registers.pack_8bit_register(16)
            )
            print("  Control5: Firing duration = 16 cycles")

            # Control6: Cooling duration (16 cycles, min 8)
            self.cloud_compile.set_control(
                DS1140Registers.COOLING_DURATION,
                DS1140Registers.pack_8bit_register(16)
            )
            print("  Control6: Cooling duration = 16 cycles")

            # Control7: Trigger threshold (2.4V)
            threshold_raw = DS1140Registers.voltage_to_raw(2.4)
            self.cloud_compile.set_control(
                DS1140Registers.TRIGGER_THRESHOLD,
                DS1140Registers.pack_16bit_register(threshold_raw)
            )
            print(f"  Control7: Trigger threshold = 2.4V (0x{threshold_raw:04X})")

            # Control8: Intensity (2.0V safe default, will be clamped to 3.0V max)
            intensity_raw = DS1140Registers.voltage_to_raw(2.0)
            self.cloud_compile.set_control(
                DS1140Registers.INTENSITY,
                DS1140Registers.pack_16bit_register(intensity_raw)
            )
            print(f"  Control8: Intensity = 2.0V (0x{intensity_raw:04X})")

            print("✓ Control registers initialized with safe defaults")
            return True

        except Exception as e:
            print(f"✗ Register initialization failed: {e}")
            return False

    def monitor_fsm_state(self) -> Optional[Dict]:
        """
        Read current FSM state from oscilloscope.

        Returns:
            Dictionary with state information, or None if failed
        """
        try:
            # Get oscilloscope data
            data = self.oscilloscope.get_data()

            if 'ch1' not in data:
                print("WARNING: No data on Ch1 (FSM debug)")
                return None

            # Get midpoint voltage reading (most stable)
            midpoint = len(data['ch1']) // 2
            voltage = data['ch1'][midpoint]

            # Decode state
            state_info = decode_fsm_voltage(voltage)
            return state_info

        except Exception as e:
            print(f"WARNING: FSM monitoring failed: {e}")
            return None

    def wait_for_state(self, expected_state: str, timeout: float = 5.0, poll_interval: float = 0.1) -> bool:
        """
        Wait for FSM to reach expected state.

        Args:
            expected_state: State name to wait for (e.g., "READY", "DONE")
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between polls (seconds)

        Returns:
            True if state reached, False if timeout
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            state = self.monitor_fsm_state()
            if state and state['state_name'] == expected_state:
                return True
            time.sleep(poll_interval)

        return False

    def arm_probe(self) -> bool:
        """Arm the probe (READY → ARMED transition)"""
        print("\nArming probe...")
        try:
            # Press arm button (Control0)
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

            # Wait for ARMED state
            print("  Waiting for ARMED state...")
            if self.wait_for_state("ARMED", timeout=2.0):
                state = self.monitor_fsm_state()
                print(f"  ✓ Probe armed: {state['state_name']} ({state['voltage']:.3f}V)")
                return True
            else:
                print("  ✗ Timeout waiting for ARMED state")
                return False

        except Exception as e:
            print(f"  ✗ Arm failed: {e}")
            return False

    def force_fire(self) -> bool:
        """Manual fire for testing (bypasses threshold detection)"""
        print("\nForce firing probe...")
        try:
            # Press force fire button (Control1)
            self.cloud_compile.set_control(
                DS1140Registers.FORCE_FIRE,
                DS1140Registers.pack_button(True)
            )
            time.sleep(0.01)

            # Release button
            self.cloud_compile.set_control(
                DS1140Registers.FORCE_FIRE,
                DS1140Registers.pack_button(False)
            )

            # Wait for sequence (FIRING → COOLING → DONE)
            print("  Waiting for FIRING state...")
            if not self.wait_for_state("FIRING", timeout=1.0):
                print("  ✗ Timeout waiting for FIRING state")
                return False

            print("  Waiting for DONE state...")
            if self.wait_for_state("DONE", timeout=2.0):
                state = self.monitor_fsm_state()
                print(f"  ✓ Fire complete: {state['state_name']} ({state['voltage']:.3f}V)")
                return True
            else:
                print("  ✗ Timeout waiting for DONE state")
                return False

        except Exception as e:
            print(f"  ✗ Force fire failed: {e}")
            return False

    def reset_fsm(self) -> bool:
        """Reset FSM to READY state"""
        print("\nResetting FSM...")
        try:
            # Press reset button (Control2)
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

            # Wait for READY state
            print("  Waiting for READY state...")
            if self.wait_for_state("READY", timeout=1.0):
                state = self.monitor_fsm_state()
                print(f"  ✓ FSM reset: {state['state_name']} ({state['voltage']:.3f}V)")
                return True
            else:
                print("  ✗ Timeout waiting for READY state")
                return False

        except Exception as e:
            print(f"  ✗ Reset failed: {e}")
            return False

    def run_deployment(self, skip_test: bool = False) -> bool:
        """Execute full deployment sequence"""
        print("=" * 70)
        print("DS1140-PD EMFI PROBE DRIVER DEPLOYMENT")
        print("=" * 70)
        print()

        # Step 1: Connect
        print("[Step 1] Connecting to Moku...")
        print("-" * 70)
        if not self.connect():
            return False
        print()

        # Step 2: Deploy bitstream
        print("[Step 2] Deploying DS1140-PD Bitstream...")
        print("-" * 70)
        if not self.deploy_bitstream():
            self.disconnect()
            return False
        print()

        # Step 3: Setup oscilloscope
        print("[Step 3] Setting up Oscilloscope...")
        print("-" * 70)
        if not self.setup_oscilloscope():
            self.disconnect()
            return False
        print()

        # Step 4: Configure routing
        print("[Step 4] Configuring Routing...")
        print("-" * 70)
        if not self.setup_routing():
            self.disconnect()
            return False
        print()

        # Step 5: Initialize registers
        print("[Step 5] Initializing Control Registers...")
        print("-" * 70)
        if not self.initialize_registers():
            self.disconnect()
            return False
        print()

        # Step 6: Check initial state
        print("[Step 6] Checking Initial FSM State...")
        print("-" * 70)
        time.sleep(0.5)  # Allow oscilloscope to settle
        state = self.monitor_fsm_state()
        if state:
            print(f"FSM State: {state['state_name']} ({state['voltage']:.3f}V)")
            if state['state_name'] != 'READY':
                print("WARNING: Expected READY state initially")
                print("Attempting reset...")
                self.reset_fsm()
        print()

        # Step 7: Interactive testing
        if not skip_test:
            print("[Step 7] Interactive Testing...")
            print("-" * 70)
            self.interactive_test()
            print()

        # Summary
        print("=" * 70)
        print("DEPLOYMENT COMPLETE")
        print("=" * 70)
        print()
        # Detect bitstream type
        is_debug = "debug" in str(self.bitstream_path).lower()

        print("DS1140-PD Status:")
        print(f"  - Bitstream deployed to Slot 2 ({'DEBUG' if is_debug else 'PRODUCTION'} MODE)")
        print("  - Oscilloscope monitoring on Ch1 (FSM debug)")
        print("  - Control registers initialized with safe defaults")
        print()

        if is_debug:
            print("⚠️  DEBUG ROUTING ACTIVE:")
            print("  - Output1 = FSM Debug (NOT trigger!)")
            print("  - Output2 = Intensity (~2.0V)")
            print("  - OutputC = Trigger (internal only)")
            print()
            print("FSM State Voltages (on Output1):")
            print("  - READY:     0.0V  (waiting for arm)")
            print("  - ARMED:     0.5V  (waiting for trigger)")
            print("  - FIRING:    1.0V  (pulse active)")
            print("  - COOLING:   1.5V  (thermal management)")
            print("  - DONE:      2.0V  (operation complete)")
            print("  - TIMEDOUT:  2.5V  (no trigger detected)")
            print("  - HARDFAULT: <0V   (error condition)")
            print()
            print("Next Steps:")
            print("  1. Monitor Output1 on external scope (FSM states)")
            print("  2. Monitor Output2 on external scope (intensity voltage)")
            print("  3. Connect trigger source to Input1 (>2.4V to trigger)")
            print("  4. Use interactive commands to test FSM transitions")
        else:
            print("✅ PRODUCTION ROUTING:")
            print("  - Output1 = Trigger Output (connect to EMFI probe)")
            print("  - Output2 = Intensity Output (connect to EMFI probe)")
            print("  - OutputC = FSM Debug (monitored via oscilloscope)")
            print()
            print("Next Steps:")
            print("  1. Connect EMFI probe: Output1 → Trigger, Output2 → Intensity")
            print("  2. Connect trigger source to Input1 (>2.4V threshold)")
            print("  3. Monitor FSM debug on Moku oscilloscope (Ch1)")
            print("  4. Use test script for manual control:")
        print()

        return True

    def interactive_test(self):
        """Interactive testing mode"""
        print("Interactive Testing Mode")
        print("Commands:")
        print("  [a] Arm probe")
        print("  [f] Force fire")
        print("  [r] Reset FSM")
        print("  [s] Show FSM state")
        print("  [q] Quit testing")
        print()

        while True:
            try:
                cmd = input("Command [a/f/r/s/q]: ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'a':
                    self.arm_probe()
                elif cmd == 'f':
                    self.force_fire()
                elif cmd == 'r':
                    self.reset_fsm()
                elif cmd == 's':
                    state = self.monitor_fsm_state()
                    if state:
                        print(f"Current FSM State: {state['state_name']} ({state['voltage']:.3f}V)")
                        if state['is_fault']:
                            print("  ⚠ FAULT DETECTED")
                else:
                    print("Invalid command")

            except KeyboardInterrupt:
                print("\nExiting testing mode...")
                break
            except EOFError:
                break

    def disconnect(self):
        """Disconnect from Moku"""
        if self.multi_instrument:
            print("Disconnecting...")
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
        description="Deploy DS1140-PD EMFI probe driver to Moku hardware",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover Moku device
  python tools/deploy_ds1140_pd.py

  # Specify IP address
  python tools/deploy_ds1140_pd.py --ip 192.168.13.159

  # Skip interactive testing
  python tools/deploy_ds1140_pd.py --no-test
        """
    )

    parser.add_argument('--ip', type=str, help='Moku device IP address')
    parser.add_argument('--bitstream', type=Path, help='Path to DS1140-PD bitstream (.tar)')
    parser.add_argument('--no-test', action='store_true', help='Skip interactive testing')

    args = parser.parse_args()

    # Default bitstream path (DEBUG version with FSM on OutputA)
    if not args.bitstream:
        args.bitstream = Path(__file__).parent.parent / "DS1140_debug_bits.tar"

    # Device discovery
    if not args.ip:
        devices = discover_moku_devices()
        if devices:
            if len(devices) == 1:
                args.ip = devices[0]
                print(f"\nUsing discovered device: {args.ip}\n")
            else:
                print("\nMultiple devices found. Please select:")
                for i, ip in enumerate(devices, 1):
                    print(f"  [{i}] {ip}")
                try:
                    selection = int(input("Select device [1]: ") or "1")
                    args.ip = devices[selection - 1]
                except (ValueError, IndexError):
                    args.ip = devices[0]
        else:
            args.ip = input("Moku IP address [192.168.13.159]: ") or "192.168.13.159"

    # Validate inputs
    if not args.bitstream.exists():
        print(f"ERROR: Bitstream not found: {args.bitstream}")
        return False

    # Run deployment
    deployment = DS1140Deployment(args.ip, args.bitstream)
    success = deployment.run_deployment(skip_test=args.no_test)

    # Keep connection open
    if success:
        input("\nPress Enter to disconnect and exit...")

    deployment.disconnect()
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
