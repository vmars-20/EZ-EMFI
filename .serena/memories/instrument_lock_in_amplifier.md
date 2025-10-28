# Moku Instrument: Lock-in Amplifier

## Purpose
Phase-sensitive detection and demodulation. Extracts signal amplitude and phase at a specific frequency from noisy background. Useful for **precision measurements**, analyzing custom module AC response, or implementing phase-locked loops.

---

## MokuBench Quick Reference

**Status**: ⚠️ Framework support complete, hardware testing pending (license/entitlement required)

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Instrument registered and importable
- Ready for BenchConfig deployment
- Settings handlers inherit from base patterns
- Data collection follows established patterns

**To Use**:
```python
from bench_framework import BenchConfig, SlotConfig

config = MokuPlatformConfig(
    platform=MOKU_GO,
    slots={
        1: SlotConfig(
            instrument='LockInAmp',
            settings={
                'demodulation': {'frequency': 1e3, 'source': 'Internal'},
                'filter': {'frequency': 10, 'order': 8}
            }
        )
    },
    connections=[...]
)
```

**Note**: Testing requires Moku device with appropriate license/entitlement.

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, LockInAmp

m = MultiInstrument('192.168.1.100', platform_id=2)
lia = m.set_instrument(1, LockInAmp)
```

### Configuration Methods

**Set Demodulation Frequency**:
```python
lia.set_demodulation(frequency, source)
# Example: lia.set_demodulation(1e3, source="Internal")  # 1 kHz internal oscillator
# Example: lia.set_demodulation(1e3, source="External")  # Lock to external reference
```

**Set Low-Pass Filter**:
```python
lia.set_filter(frequency, order)
# Example: lia.set_filter(10, order=8)  # 10 Hz cutoff, 8th order filter
```

**Set Monitor Output**:
```python
lia.set_monitor(channel, source)
# Example: lia.set_monitor(1, "Input1")    # Monitor input signal
# Example: lia.set_monitor(1, "X")         # Monitor X component
# Example: lia.set_monitor(1, "R")         # Monitor amplitude (R)
```

**PID Controller** (for feedback/locking):
```python
lia.set_pid_controller(enable=True, kp=1.0, ki=0.1, kd=0.01)
```

### Data Acquisition

**Get Demodulated Data**:
```python
data = lia.get_data()
# Returns dict with 'X', 'Y', 'R', 'theta' (amplitude and phase)
```

**Stream Data**:
```python
lia.start_streaming(duration=10, rate=1e3)
while True:
    data = lia.get_stream_data()
    if data:
        print("X component:", data['ch1'])
```

---

## Routing Patterns

### Pattern 1: Demodulate External Signal
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),  # Signal to demodulate → Lock-in
]
m.set_connections(connections=connections)

lia.set_demodulation(1e3, source="Internal")  # Demodulate at 1 kHz
lia.set_filter(10, order=8)
data = lia.get_data()
print("Amplitude (R):", data['R'])
print("Phase (theta):", data['theta'])
```

### Pattern 2: Analyze Custom Module Output
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="modulator.tar.gz")
lia = m.set_instrument(1, LockInAmp)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module output → Lock-in
]
m.set_connections(connections=connections)

# Demodulate module output
lia.set_demodulation(10e3, source="Internal")
data = lia.get_data()
```

---

## Multi-Instrument Scenarios

### Scenario: Data Logger + Lock-in (Streaming Demodulated Data)
```python
dl = m.set_instrument(1, Datalogger)
lia = m.set_instrument(2, LockInAmp)

connections = [
    dict(source="Input1", destination="Slot1InA"),
    dict(source="Slot1OutA", destination="Slot2InA"),
    dict(source="Slot2OutA", destination="Output1"),
]
m.set_connections(connections=connections)

# Generate test signal via Data Logger
dl.generate_waveform(1, "Sine", frequency=1000)

# Demodulate via Lock-in
lia.set_monitor(1, "Input1")
lia.start_streaming(duration=10, rate=1e3)
```

---

## References
- **Examples**: `mcc_py_api_examples/lock_in_amplifier_*.py`, `mcc_py_api_examples/mim_dl_lia_streaming.py`
