# Moku Instrument: Data Logger

## Purpose
Time-series data recording and streaming. Captures continuous data to file or streams to network. Useful for **long-term monitoring**, recording custom module behavior over extended periods, or exporting data for offline analysis.

---

## MokuBench Quick Reference

**Test Script**: `tests/mokubench_datalogger_test.py`

**Run Example**:
```bash
uv run python tests/mokubench_datalogger_test.py --ip 192.168.13.159 --duration 10 --sample-rate 1000
```

**What It Demonstrates**:
- Deploy CloudCompile (simple_counter) + Datalogger
- Configure streaming at 1 kSa/s
- Capture time-series data continuously
- Collect 252 samples over 5 seconds

**Status**: ✅ Validated on Moku:Go hardware

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Settings: `streaming` configuration (duration, sample_rate)
- Data collection: `get_stream_data()` returns time/ch1/ch2 arrays
- Note: Deprecated `set_samplerate()` API handled automatically

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, Datalogger

m = MultiInstrument('192.168.1.100', platform_id=2)
dl = m.set_instrument(1, Datalogger)
```

### Configuration Methods

**Set Sample Rate**:
```python
dl.set_samplerate(rate)
# Example: dl.set_samplerate(1e6)  # 1 MSa/s
```

**Generate Waveform** (Data Logger can also generate!):
```python
dl.generate_waveform(channel, waveform_type, **kwargs)
# Example: dl.generate_waveform(1, "Sine", frequency=1000)
```

### Data Acquisition

**Log to File** (on Moku device):
```python
dl.start_logging(duration=10)  # Log for 10 seconds
dl.stop_logging()
```

**Stream to Network**:
```python
dl.start_streaming(duration=10, sample_rate=1e3)

# Read streaming data in loop
while True:
    data = dl.get_stream_data()
    if data:
        print("Time:", data['time'])
        print("Ch1:", data['ch1'])
        print("Ch2:", data['ch2'])
```

**Stream to File** (on host computer):
```python
dl.start_streaming(duration=10, sample_rate=1e3)
dl.stream_to_file()  # Auto-saves to file
```

---

## Routing Patterns

### Pattern 1: Log Custom Module Output
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="my_module.tar.gz")
dl = m.set_instrument(1, Datalogger)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module output → Data Logger
]
m.set_connections(connections=connections)

# Record 60 seconds of module behavior
dl.start_logging(duration=60)
```

### Pattern 2: Stream Data While Monitoring
```python
connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module → Data Logger
    dict(source="Slot2OutA", destination="Output1"),   # Module → Physical OUT1 (parallel)
]
m.set_connections(connections=connections)

# Stream data to network for real-time analysis
dl.start_streaming(duration=30, sample_rate=100e3)
while True:
    data = dl.get_stream_data()
    # Process data in real-time
```

---

## Multi-Instrument Scenarios

### Scenario: Data Logger + Lock-in Amplifier (Long-Term Demodulation Recording)
```python
dl = m.set_instrument(1, Datalogger)
lia = m.set_instrument(2, LockInAmp)

connections = [
    dict(source="Input1", destination="Slot1InA"),      # External signal → Data Logger (raw)
    dict(source="Slot1OutA", destination="Slot2InA"),   # Data Logger → Lock-in (for processing)
    dict(source="Slot2OutA", destination="Output1"),    # Lock-in output → Physical OUT1
]
m.set_connections(connections=connections)

# Generate stimulus via Data Logger
dl.generate_waveform(1, "Sine", frequency=1000)

# Stream demodulated data
dl.start_streaming(duration=60, sample_rate=1e3)
dl.stream_to_file()
```

---

## References
- **Examples**: `mcc_py_api_examples/datalogger_*.py`, `mcc_py_api_examples/mim_dl_lia_streaming.py`
