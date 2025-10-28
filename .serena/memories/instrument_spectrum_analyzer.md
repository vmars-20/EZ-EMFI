# Moku Instrument: Spectrum Analyzer

## Purpose
Frequency-domain signal analysis. Converts time-domain signals to frequency spectrum using FFT. Useful for **analyzing custom module frequency response**, detecting harmonics, or measuring signal bandwidth.

---

## MokuBench Quick Reference

**Test Script**: `tests/mokubench_spectrum_test.py`

**Run Example**:
```bash
uv run python tests/mokubench_spectrum_test.py --ip 192.168.13.159 --frequency 1000 --span-end 20000
```

**What It Demonstrates**:
- Deploy WaveformGenerator (1 kHz test tone) + SpectrumAnalyzer
- Route waveform to spectrum analyzer
- Capture 985 frequency points (DC to 20 kHz)
- Find peak frequency and verify against expected

**Status**: ✅ Validated on Moku:Go hardware

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Settings: `span`, `rbw` configuration (best applied post-deployment)
- Data collection: `get_data()` returns frequency/ch1/ch2 arrays
- FFT-based frequency analysis

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, SpectrumAnalyzer

m = MultiInstrument('192.168.1.100', platform_id=2)
sa = m.set_instrument(1, SpectrumAnalyzer)
```

### Configuration Methods

**Set Frequency Span**:
```python
sa.set_span(start_freq, stop_freq)
# Example: sa.set_span(0, 10e6)  # DC to 10 MHz
```

**Set RBW (Resolution Bandwidth)**:
```python
sa.set_rbw(rbw)
# Example: sa.set_rbw(1e3)  # 1 kHz resolution
```

### Data Acquisition

**Get Spectrum Data**:
```python
data = sa.get_data()
# Returns dict: {'frequency': [...], 'ch1': [...], 'ch2': [...]}
# Values in dBm or linear units depending on settings
```

---

## Routing Patterns

### Pattern 1: Analyze External Signal
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),  # Physical IN1 → Spectrum Analyzer
]
m.set_connections(connections=connections)

sa.set_span(0, 10e6)
data = sa.get_data()
print("Frequencies:", data['frequency'])
print("Power (dBm):", data['ch1'])
```

### Pattern 2: Analyze Custom Module Output
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="signal_gen.tar.gz")
sa = m.set_instrument(1, SpectrumAnalyzer)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module output → Spectrum Analyzer
]
m.set_connections(connections=connections)

# Analyze module frequency content
sa.set_span(0, 50e6)
data = sa.get_data()
```

---

## Multi-Instrument Scenarios

### Scenario: WaveformGen + Spectrum Analyzer (Frequency Verification)
```python
wg = m.set_instrument(2, WaveformGenerator)
sa = m.set_instrument(1, SpectrumAnalyzer)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),
]
m.set_connections(connections=connections)

# Generate 1 kHz + 10 kHz mixed signal
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)
# (Mix signals by generating harmonics or using dual channels)

# Verify spectrum
sa.set_span(0, 20e3)
data = sa.get_data()
# Look for peaks at 1 kHz and 10 kHz
```

---

## References
- **Examples**: `mcc_py_api_examples/spectrumanalyzer_*.py`
