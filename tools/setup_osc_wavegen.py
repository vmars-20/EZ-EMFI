#!/usr/bin/env python3
"""
Setup Oscilloscope + Waveform Generator on Moku:Go

Connects to Moku at 192.168.8.98 and configures:
- Slot 1: Oscilloscope (monitoring waveform generator outputs)
- Slot 2: Waveform Generator (1 kHz sine wave, 1Vpp)
- Routing: WaveGen outputs to both physical outputs and oscilloscope inputs
"""

import time
from moku import Moku
from moku.instruments import MultiInstrument, Oscilloscope, WaveformGenerator


def connect_via_base_moku(ip: str, platform_id: int) -> MultiInstrument:
    """Connect using base Moku class first, then upgrade to MultiInstrument."""
    # First establish connection with base Moku
    base_moku = Moku(ip=ip, force_connect=True, connect_timeout=10)
    base_moku.relinquish_ownership()

    # Small delay before creating MultiInstrument
    time.sleep(0.5)

    # Now create MultiInstrument
    return MultiInstrument(ip, platform_id=platform_id, force_connect=True)


def main():
    print("=" * 60)
    print("Moku Multi-Instrument Setup: Oscilloscope + Waveform Generator")
    print("=" * 60)

    # Connect to Moku:Go
    moku_ip = "192.168.8.98"
    platform_id = 2  # Moku:Go

    print(f"\n[1/5] Connecting to Moku:Go at {moku_ip}...")

    # Try multiple connection strategies
    m = None
    strategies = [
        ("Standard force_connect", lambda: MultiInstrument(moku_ip, platform_id=platform_id, force_connect=True)),
        ("Base Moku first", lambda: connect_via_base_moku(moku_ip, platform_id)),
        ("Without force_connect", lambda: MultiInstrument(moku_ip, platform_id=platform_id, force_connect=False)),
    ]

    for strategy_name, connect_fn in strategies:
        try:
            print(f"    Trying: {strategy_name}...")
            m = connect_fn()
            print(f"✓ Connected successfully using: {strategy_name}")
            break
        except Exception as e:
            print(f"    ✗ {strategy_name} failed: {e}")
            continue

    if m is None:
        print("\n✗ All connection attempts failed")
        print("\nTroubleshooting:")
        print("  1. Check if Moku app is open and connected")
        print("  2. Try rebooting the Moku device")
        print("  3. Wait 60 seconds for session timeout")
        return

    try:
        # Deploy Oscilloscope in Slot 1
        print("\n[2/5] Deploying Oscilloscope in Slot 1...")
        osc = m.set_instrument(1, Oscilloscope)

        # Configure oscilloscope
        osc.set_timebase(-0.001, 0.001)  # ±1ms window (2ms total)
        osc.set_trigger(type='Edge', source='Input1', level=0.0)
        osc.disable_trigger()  # Auto-trigger mode (free-running)

        # Set input ranges to ±5V
        osc.set_frontend(channel=1, impedance='1MOhm', coupling='DC', range='10Vpp')
        osc.set_frontend(channel=2, impedance='1MOhm', coupling='DC', range='10Vpp')

        print("✓ Oscilloscope configured")

        # Deploy Waveform Generator in Slot 2
        print("\n[3/5] Deploying Waveform Generator in Slot 2...")
        wg = m.set_instrument(2, WaveformGenerator)

        # Configure waveform generator - 1 kHz sine wave, 1Vpp
        wg.generate_waveform(channel=1, type='Sine', amplitude=1.0, frequency=1e3)
        wg.generate_waveform(channel=2, type='Sine', amplitude=1.0, frequency=1e3, phase=90)  # 90° phase shift

        print("✓ Waveform Generator configured (1 kHz sine, 1Vpp)")

        # Configure routing
        print("\n[4/5] Configuring routing connections...")
        connections = [
            # WaveGen outputs → Oscilloscope inputs (internal monitoring)
            dict(source="Slot2OutA", destination="Slot1InA"),  # WaveGen Ch1 → Osc Ch1
            dict(source="Slot2OutB", destination="Slot1InB"),  # WaveGen Ch2 → Osc Ch2

            # WaveGen outputs → Physical outputs (external access)
            dict(source="Slot2OutA", destination="Output1"),   # WaveGen Ch1 → Output1
            dict(source="Slot2OutB", destination="Output2"),   # WaveGen Ch2 → Output2
        ]

        m.set_connections(connections=connections)
        print("✓ Routing configured:")
        print("  - WaveGen Ch1 → Osc Ch1 + Output1")
        print("  - WaveGen Ch2 → Osc Ch2 + Output2")

        # Test data acquisition
        print("\n[5/5] Testing oscilloscope data acquisition...")
        time.sleep(0.5)  # Allow instruments to stabilize

        data = osc.get_data()
        ch1_samples = len(data['ch1'])
        ch2_samples = len(data['ch2'])

        # Calculate measured amplitudes
        ch1_pk = max(abs(max(data['ch1'])), abs(min(data['ch1'])))
        ch2_pk = max(abs(max(data['ch2'])), abs(min(data['ch2'])))

        print(f"✓ Data acquired successfully")
        print(f"  - Ch1: {ch1_samples} samples, peak amplitude: {ch1_pk:.3f}V")
        print(f"  - Ch2: {ch2_samples} samples, peak amplitude: {ch2_pk:.3f}V")

        # Success summary
        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print("\nInstrument Configuration:")
        print("  • Slot 1: Oscilloscope (±1ms timebase, auto-trigger)")
        print("  • Slot 2: Waveform Generator (1 kHz sine, 1Vpp)")
        print("\nSignal Flow:")
        print("  • WaveGen Ch1 → Osc Ch1 + Output1")
        print("  • WaveGen Ch2 → Osc Ch2 + Output2 (90° phase)")
        print("\nNext Steps:")
        print("  - View oscilloscope in Moku app GUI")
        print("  - Measure outputs on external scope")
        print("  - Modify waveform parameters as needed")
        print("\nKeep connection alive? (Ctrl+C to disconnect)")

        # Keep alive loop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nDisconnecting...")

    finally:
        m.relinquish_ownership()
        print("✓ Connection closed")


if __name__ == "__main__":
    main()
