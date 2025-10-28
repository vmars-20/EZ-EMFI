# Moku Instrument: Frequency Response Analyzer (FRA)

## Purpose
Measures transfer function (Bode plot: magnitude and phase vs frequency). Sweeps frequency while measuring input/output relationship. Useful for **characterizing custom module frequency response**, filter design verification, or control loop analysis.

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
            instrument='FrequencyResponseAnalyzer',
            settings={
                'sweep': {
                    'start_freq': 10,
                    'stop_freq': 10e6,
                    'num_points': 512,
                    'averaging_time': 1e-3
                }
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
from moku.instruments import MultiInstrument, FrequencyResponseAnalyzer

m = MultiInstrument('192.168.1.100', platform_id=2)
fra = m.set_instrument(1, FrequencyResponseAnalyzer)
```

### Configuration Methods

**Set Sweep Parameters**:
```python
fra.set_sweep(start_freq, stop_freq, num_points, averaging_time, **kwargs)
# Example: fra.set_sweep(10, 10e6, 512, averaging_time=1e-3)
# Sweeps from 10 Hz to 10 MHz with 512 points
```

**Set Output Amplitude**:
```python
fra.set_output(channel, amplitude)
# Example: fra.set_output(1, amplitude=0.5)  # 0.5V peak excitation signal
```

### Data Acquisition

**Get Transfer Function Data**:
```python
data = fra.get_data()
# Returns dict: {'frequency': [...], 'magnitude': [...], 'phase': [...]}
```

**Start Sweep**:
```python
fra.start_sweep()
```

---

## Routing Patterns

### Pattern 1: Measure Custom Module Transfer Function
```python
fra = m.set_instrument(1, FrequencyResponseAnalyzer)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_filter.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # FRA stimulus → Module input
    dict(source="Slot2OutA", destination="Slot1InB"),  # Module output → FRA response
]
m.set_connections(connections=connections)

# Measure filter response
fra.set_sweep(10, 100e3, 512, averaging_time=1e-3)
fra.set_output(1, amplitude=0.5)
fra.start_sweep()
data = fra.get_data()

# Plot Bode plot
import matplotlib.pyplot as plt
plt.subplot(2, 1, 1)
plt.semilogx(data['frequency'], data['magnitude'])
plt.ylabel('Magnitude (dB)')
plt.subplot(2, 1, 2)
plt.semilogx(data['frequency'], data['phase'])
plt.ylabel('Phase (deg)')
plt.xlabel('Frequency (Hz)')
plt.show()
```

---

## Multi-Instrument Scenarios

### Scenario: FRA + FIR Filter (Design Verification)
```python
fra = m.set_instrument(1, FrequencyResponseAnalyzer)
fir = m.set_instrument(2, FIRFilterBuilder)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),
    dict(source="Slot2OutA", destination="Slot1InB"),
]
m.set_connections(connections=connections)

# Design FIR filter
fir.design_filter(filter_type="LowPass", cutoff_freq=10e3)

# Measure actual response
fra.set_sweep(10, 100e3, 512)
data = fra.get_data()
```

---

## References
- **Examples**: `mcc_py_api_examples/freq_response_analyzer_*.py`, `mcc_py_api_examples/mim_fir_fra.ipynb`
