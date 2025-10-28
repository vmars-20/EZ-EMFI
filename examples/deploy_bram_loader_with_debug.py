#!/usr/bin/env python3
"""
BRAM Loader Deployment Script with FSM Observer Monitoring

Demonstrates deploying the volo_bram_loader module with real-time
FSM observer voltage monitoring on oscilloscope.

Features:
- BRAM loading via Control Register protocol
- Real-time state visualization via FSM observer
- Voltage decoding (IDLE/LOADING/DONE states)
- Multi-instrument mode (CloudCompile + Oscilloscope)

Usage:
    # Interactive (prompts for IP and bitstream path)
    python examples/deploy_bram_loader_with_debug.py

    # Command-line arguments
    python examples/deploy_bram_loader_with_debug.py \\
        --ip 192.168.13.159 \\
        --bitstream path/to/bitstream.tar \\
        --buffer path/to/buffer.bin

Architecture:
    MCC Bitstream (CustomWrapper)
      └─> volo_bram_loader entity
            ├─> Control10-14 (BRAM loading protocol)
            ├─> bram_addr/data/we (to application BRAM)
            └─> voltage_debug_out (FSM observer → OutputB → Oscilloscope Ch2)

FSM States (visible on oscilloscope):
    IDLE:     0.0V  (waiting for start signal)
    LOADING:  1.0V  (writing words to BRAM)
    DONE:     2.0V  (loading complete)
    RESERVED: -2.0V (fault state, negative voltage indicates error)

Author: EZ-EMFI Team
Date: 2025-01-28
"""

import argparse
import sys
import time
import struct
from pathlib import Path
from typing import Optional, List, Dict

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
# FSM Observer Voltage Decoding
# ============================================================================

class BRAMLoaderStates:
    """BRAM Loader FSM states (2-bit encoding)"""
    IDLE = 0
    LOADING = 1
    DONE = 2
    RESERVED = 3  # Fault state


class ObserverVoltages:
    """
    Expected voltages from FSM observer.

    Configuration (from volo_bram_loader.vhd):
        NUM_STATES = 4
        V_MIN = 0.0
        V_MAX = 2.0
        FAULT_STATE_THRESHOLD = 3

    Voltage calculation: V = V_MIN + (state_index * (V_MAX - V_MIN) / (num_normal - 1))
    Only 3 normal states (0, 1, 2), so v_step = 2.0 / 2 = 1.0V
    """
    IDLE = 0.0      # State 0: 0.0V
    LOADING = 1.0   # State 1: 1.0V
    DONE = 2.0      # State 2: 2.0V
    FAULT = -2.0    # State 3: -2.0V (sign-flip fault)

    # Tolerance for voltage comparisons (±50mV)
    TOLERANCE = 0.05


def decode_observer_voltage(voltage: float) -> Dict:
    """
    Decode FSM observer voltage to state information.

    Args:
        voltage: Oscilloscope reading from voltage_debug_out (V)

    Returns:
        Dictionary with state information:
            - state_name: "IDLE", "LOADING", "DONE", or "FAULT"
            - state_id: Numeric state ID (0-3)
            - voltage: Raw voltage reading
            - is_fault: Boolean indicating fault condition
    """
    # Determine state based on voltage with tolerance
    if abs(voltage - ObserverVoltages.IDLE) < ObserverVoltages.TOLERANCE:
        return {
            'state_name': 'IDLE',
            'state_id': BRAMLoaderStates.IDLE,
            'voltage': voltage,
            'is_fault': False
        }
    elif abs(voltage - ObserverVoltages.LOADING) < ObserverVoltages.TOLERANCE:
        return {
            'state_name': 'LOADING',
            'state_id': BRAMLoaderStates.LOADING,
            'voltage': voltage,
            'is_fault': False
        }
    elif abs(voltage - ObserverVoltages.DONE) < ObserverVoltages.TOLERANCE:
        return {
            'state_name': 'DONE',
            'state_id': BRAMLoaderStates.DONE,
            'voltage': voltage,
            'is_fault': False
        }
    elif voltage < 0 and abs(voltage - ObserverVoltages.FAULT) < ObserverVoltages.TOLERANCE:
        return {
            'state_name': 'FAULT',
            'state_id': BRAMLoaderStates.RESERVED,
            'voltage': voltage,
            'is_fault': True
        }
    else:
        return {
            'state_name': f'UNKNOWN({voltage:.3f}V)',
            'state_id': None,
            'voltage': voltage,
            'is_fault': False
        }


# ============================================================================
# BRAM Loading Protocol
# ============================================================================

class BRAMLoader:
    """
    BRAM loading implementation using Control Register protocol.

    Protocol (CR10-CR14):
        Control10[0]     : Start signal (write 1 to begin loading)
        Control10[31:16] : Word count (number of 32-bit words, max 1024)
        Control11[11:0]  : Address to write (12-bit, 0-4095 bytes / 4 = 0-1023 words)
        Control12[31:0]  : Data to write (32-bit word)
        Control13[0]     : Write strobe (pulse high to commit write)
        Control14        : Reserved
    """

    def __init__(self, cloud_compile: CloudCompile):
        """
        Initialize BRAM loader.

        Args:
            cloud_compile: Moku CloudCompile instrument instance
        """
        self.cc = cloud_compile

    def load_buffer(self, data: List[int], progress_callback=None) -> bool:
        """
        Load data buffer to BRAM.

        Args:
            data: List of 32-bit integers to write
            progress_callback: Optional callback(word_index, total) for progress updates

        Returns:
            True if successful, False otherwise
        """
        if len(data) > 1024:
            print(f"ERROR: Buffer too large ({len(data)} words, max 1024)")
            return False

        if len(data) == 0:
            print("WARNING: Empty buffer, nothing to load")
            return True

        try:
            # Step 1: Set start signal + word count
            print(f"Starting BRAM load ({len(data)} words)...")
            control10 = (len(data) << 16) | 0x0001
            self.cc.set_control_matrix(0, 10, control10)
            time.sleep(0.01)  # Allow FSM to transition to LOADING

            # Step 2: Write each word
            for addr, word in enumerate(data):
                # Set address
                self.cc.set_control_matrix(0, 11, addr)

                # Set data
                self.cc.set_control_matrix(0, 12, word)

                # Pulse write strobe (high)
                self.cc.set_control_matrix(0, 13, 0x0001)
                time.sleep(0.001)  # Hold strobe

                # Deassert strobe (low)
                self.cc.set_control_matrix(0, 13, 0x0000)
                time.sleep(0.001)  # Post-write delay

                # Progress callback
                if progress_callback:
                    progress_callback(addr + 1, len(data))

            print(f"✓ Loaded {len(data)} words to BRAM")
            return True

        except Exception as e:
            print(f"✗ BRAM load failed: {e}")
            return False

    def load_from_file(self, buffer_path: Path, progress_callback=None) -> bool:
        """
        Load buffer from binary file.

        Args:
            buffer_path: Path to .bin file (must be multiple of 4 bytes)
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        if not buffer_path.exists():
            print(f"ERROR: Buffer file not found: {buffer_path}")
            return False

        # Read binary file
        with open(buffer_path, 'rb') as f:
            raw_bytes = f.read()

        # Check size
        if len(raw_bytes) % 4 != 0:
            print(f"ERROR: Buffer size must be multiple of 4 bytes (got {len(raw_bytes)})")
            return False

        if len(raw_bytes) > 4096:
            print(f"WARNING: Buffer truncated to 4KB (was {len(raw_bytes)} bytes)")
            raw_bytes = raw_bytes[:4096]

        # Unpack to 32-bit words (little-endian)
        word_count = len(raw_bytes) // 4
        data = list(struct.unpack(f'<{word_count}I', raw_bytes))

        print(f"Loaded {len(data)} words ({len(raw_bytes)} bytes) from {buffer_path.name}")
        return self.load_buffer(data, progress_callback)


# ============================================================================
# BRAM Loader Deployment Class
# ============================================================================

class BRAMLoaderDeployment:
    """Main deployment class for BRAM loader with FSM observer monitoring"""

    def __init__(self, moku_ip: str, bitstream_path: Path, buffer_path: Optional[Path] = None):
        """
        Initialize deployment.

        Args:
            moku_ip: Moku device IP address
            bitstream_path: Path to MCC bitstream (.tar)
            buffer_path: Optional path to BRAM buffer (.bin)
        """
        self.moku_ip = moku_ip
        self.bitstream_path = bitstream_path
        self.buffer_path = buffer_path

        self.multi_instrument = None
        self.cloud_compile = None
        self.oscilloscope = None
        self.bram_loader = None

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
        """Deploy CloudCompile bitstream to Slot 1"""
        print(f"Deploying bitstream: {self.bitstream_path.name}")

        if not self.bitstream_path.exists():
            print(f"✗ Bitstream not found: {self.bitstream_path}")
            return False

        try:
            self.cloud_compile = self.multi_instrument.set_instrument(1, CloudCompile)
            self.cloud_compile.load_bitstream(str(self.bitstream_path))
            print("✓ Bitstream deployed to Slot 1")

            # Initialize BRAM loader helper
            self.bram_loader = BRAMLoader(self.cloud_compile)
            return True

        except Exception as e:
            print(f"✗ Bitstream deployment failed: {e}")
            return False

    def setup_oscilloscope(self) -> bool:
        """Setup Oscilloscope in Slot 2 to monitor FSM observer output"""
        print("Setting up oscilloscope for FSM observer monitoring...")
        try:
            self.oscilloscope = self.multi_instrument.set_instrument(2, Oscilloscope)

            # Configure oscilloscope
            # Channel 2 = OutputB = voltage_debug_out (FSM observer)
            self.oscilloscope.set_timebase(-5e-3, 5e-3)  # ±5ms window
            self.oscilloscope.set_source(1, 'Input1')  # Ch1 = Input signal
            self.oscilloscope.set_source(2, 'Output2')  # Ch2 = FSM observer debug

            # Set voltage scales
            self.oscilloscope.set_frontend(1, impedance='1MOhm', coupling='DC', range='10Vpp')
            self.oscilloscope.set_frontend(2, impedance='1MOhm', coupling='DC', range='10Vpp')

            # Trigger on FSM observer state transitions (Ch2)
            self.oscilloscope.set_trigger(type='Edge', source='Output2', level=0.5)

            print("✓ Oscilloscope configured (Ch2 = FSM observer)")
            return True

        except Exception as e:
            print(f"✗ Oscilloscope setup failed: {e}")
            return False

    def monitor_fsm_state(self, duration: float = 1.0) -> Optional[Dict]:
        """
        Monitor FSM observer voltage for specified duration.

        Args:
            duration: Monitoring duration in seconds

        Returns:
            Dictionary with state information, or None if failed
        """
        try:
            # Get oscilloscope data
            data = self.oscilloscope.get_data()

            if 'ch2' not in data:
                print("WARNING: No data on Ch2 (FSM observer)")
                return None

            # Get latest voltage reading
            voltage = data['ch2'][-1]  # Most recent sample

            # Decode state
            state_info = decode_observer_voltage(voltage)
            return state_info

        except Exception as e:
            print(f"WARNING: FSM monitoring failed: {e}")
            return None

    def run_deployment(self) -> bool:
        """Execute full deployment sequence"""
        print("=" * 70)
        print("BRAM LOADER DEPLOYMENT WITH FSM OBSERVER")
        print("=" * 70)
        print()

        # Step 1: Connect
        print("[Step 1] Connecting to Moku...")
        print("-" * 70)
        if not self.connect():
            return False
        print()

        # Step 2: Deploy bitstream
        print("[Step 2] Deploying Bitstream...")
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

        # Step 4: Monitor initial state (should be IDLE)
        print("[Step 4] Checking Initial FSM State...")
        print("-" * 70)
        time.sleep(0.5)  # Allow oscilloscope to settle
        state = self.monitor_fsm_state()
        if state:
            print(f"FSM State: {state['state_name']} ({state['voltage']:.3f}V)")
            if state['state_name'] != 'IDLE':
                print("WARNING: Expected IDLE state initially")
        print()

        # Step 5: Load BRAM buffer (if provided)
        if self.buffer_path:
            print("[Step 5] Loading BRAM Buffer...")
            print("-" * 70)

            def progress_callback(current, total):
                if current % 50 == 0 or current == total:
                    print(f"  Progress: {current}/{total} words ({100*current//total}%)")

            success = self.bram_loader.load_from_file(self.buffer_path, progress_callback)

            # Monitor state during/after loading
            time.sleep(0.1)
            state = self.monitor_fsm_state()
            if state:
                print(f"FSM State after load: {state['state_name']} ({state['voltage']:.3f}V)")
                if state['state_name'] != 'DONE':
                    print("WARNING: Expected DONE state after loading")

            if not success:
                self.disconnect()
                return False
            print()
        else:
            print("[Step 5] No buffer specified, skipping BRAM load")
            print()

        # Step 6: Summary
        print("=" * 70)
        print("DEPLOYMENT COMPLETE")
        print("=" * 70)
        print()
        print("FSM Observer Monitoring:")
        print("  - Channel 2 (Output2) shows FSM state voltages")
        print("  - IDLE:    0.0V (waiting for data)")
        print("  - LOADING: 1.0V (writing to BRAM)")
        print("  - DONE:    2.0V (loading complete)")
        print("  - FAULT:  <0V (error condition)")
        print()
        print("Next steps:")
        print("  1. View Ch2 on oscilloscope to see state transitions")
        print("  2. Use Control10-14 registers to load additional data")
        print("  3. Read BRAM contents via application logic")
        print()

        return True

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
        description="Deploy BRAM loader with FSM observer monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for inputs)
  python examples/deploy_bram_loader_with_debug.py

  # Command-line mode
  python examples/deploy_bram_loader_with_debug.py \\
      --ip 192.168.13.159 \\
      --bitstream builds/bram_loader_bitstream.tar \\
      --buffer buffers/test_data.bin
        """
    )

    parser.add_argument('--ip', type=str, help='Moku device IP address')
    parser.add_argument('--bitstream', type=Path, help='Path to MCC bitstream (.tar)')
    parser.add_argument('--buffer', type=Path, help='Optional path to BRAM buffer (.bin)')

    args = parser.parse_args()

    # Interactive prompts if arguments not provided
    if not args.ip:
        args.ip = input("Moku IP address [192.168.13.159]: ") or "192.168.13.159"

    if not args.bitstream:
        bitstream_str = input("Bitstream path (.tar): ")
        args.bitstream = Path(bitstream_str) if bitstream_str else None

    if not args.buffer:
        buffer_str = input("Buffer path (.bin) [optional]: ")
        args.buffer = Path(buffer_str) if buffer_str else None

    # Validate inputs
    if not args.bitstream:
        print("ERROR: Bitstream path required")
        return False

    # Run deployment
    deployment = BRAMLoaderDeployment(args.ip, args.bitstream, args.buffer)
    success = deployment.run_deployment()

    # Keep connection open for manual testing
    if success:
        input("\nPress Enter to disconnect and exit...")

    deployment.disconnect()
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
