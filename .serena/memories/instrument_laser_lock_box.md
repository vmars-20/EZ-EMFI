# Laser Lock Box - Instrument API Reference

## Purpose
Specialized instrument for **laser frequency stabilization** using Pound-Drever-Hall (PDH) locking. Provides dual PID controllers (fast + slow) with scan oscillator and demodulation for optical cavity locking.

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
            instrument='LaserLockBox',
            settings={
                'scan_oscillator': {
                    'enable': True,
                    'shape': 'PositiveRamp',
                    'frequency': 10,
                    'amplitude': 0.5
                },
                'demodulation': {
                    'source': 'Internal',
                    'frequency': 1e6,
                    'phase': 0
                }
            }
        )
    },
    connections=[...]
)
```

**Note**: Testing requires Moku device with appropriate license/entitlement.

---

## Key Python API Methods

### Initialization
```python
from moku.instruments import LaserLockBox
i = LaserLockBox('192.168.1.100', force_connect=True)
```

### Frontend Configuration
```python
# Set input channels (DC coupling for photodiode signals)
i.set_frontend(channel=1, coupling='DC', impedance='1MOhm', gain='0dB')
i.set_frontend(channel=2, coupling='DC', impedance='1MOhm', gain='-20dB')
```

### Scan Oscillator (Cavity Scanning)
```python
# Generate ramp signal for laser frequency scanning
i.set_scan_oscillator(
    enable=True,
    shape='PositiveRamp',      # or 'NegativeRamp', 'Triangle'
    frequency=10,              # Hz (scan rate)
    amplitude=0.5,             # Vpp (scan range)
    output='Output1'           # Route to laser PZT input
)
```

### Demodulation (PDH Error Signal)
```python
# Configure demodulation for PDH lock
i.set_demodulation(
    source='Internal',         # or 'External' for external LO
    frequency=1e6,             # Hz (modulation frequency)
    phase=0                    # degrees (phase offset)
)
```

### Filtering (Error Signal Conditioning)
```python
# Low-pass filter for error signal
i.set_filter(
    shape='Lowpass',
    low_corner=100e3,          # Hz
    order=4                    # Filter order (2, 4, 6, 8)
)
```

### PID Controllers (Laser Lock)
```python
# Fast PID (fine frequency control)
i.set_pid_by_frequency(
    channel=1,                 # Fast PID output
    proportional_gain=-10,     # dB
    int_crossover=3e3          # Hz (integrator crossover)
)

# Slow PID (coarse frequency control)
i.set_pid_by_frequency(
    channel=2,                 # Slow PID output
    proportional_gain=-10,     # dB
    int_crossover=50           # Hz (slow drift correction)
)
```

## Routing Patterns

### Pattern 1: Standalone PDH Lock
```python
# Typical optical setup: Photodiode → LaserLockBox → Laser PZT
llb = m.set_instrument(1, LaserLockBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),    # Photodiode signal
    dict(source="Slot1OutA", destination="Output1"),  # Fast PID → Laser PZT
    dict(source="Slot1OutB", destination="Output2"),  # Slow PID → Laser current
]
m.set_connections(connections=connections)

# Configure for PDH locking
llb.set_frontend(1, coupling='DC', impedance='1MOhm', gain='0dB')
llb.set_scan_oscillator(enable=True, shape='PositiveRamp', frequency=10, amplitude=0.5, output='Output1')
llb.set_demodulation('Internal', frequency=15e6, phase=0)
llb.set_filter(shape='Lowpass', low_corner=100e3, order=4)
llb.set_pid_by_frequency(1, proportional_gain=-10, int_crossover=3e3)
llb.set_pid_by_frequency(2, proportional_gain=-10, int_crossover=50)
```

### Pattern 2: Multi-Instrument Monitoring
```python
# Monitor lock performance with oscilloscope
osc = m.set_instrument(1, Oscilloscope)
llb = m.set_instrument(2, LaserLockBox)

connections = [
    dict(source="Input1", destination="Slot2InA"),    # Photodiode → LaserLockBox
    dict(source="Slot2OutA", destination="Output1"),  # LaserLockBox PID → Laser
    dict(source="Slot2OutB", destination="Slot1InA"), # Error signal → Oscilloscope
]
m.set_connections(connections=connections)
```

## Multi-Instrument Scenarios

### Dual Laser Lock System
```python
# Lock two lasers to separate cavities (requires 4-slot platform like Moku:Pro)
llb1 = m.set_instrument(1, LaserLockBox)  # Laser 1
llb2 = m.set_instrument(2, LaserLockBox)  # Laser 2

connections = [
    dict(source="Input1", destination="Slot1InA"),    # Cavity 1 photodiode
    dict(source="Input2", destination="Slot2InA"),    # Cavity 2 photodiode
    dict(source="Slot1OutA", destination="Output1"),  # Laser 1 control
    dict(source="Slot2OutA", destination="Output2"),  # Laser 2 control
]
m.set_connections(connections=connections)
```

### Lock + Spectrum Analysis
```python
# Monitor locked laser with spectrum analyzer
llb = m.set_instrument(1, LaserLockBox)
sa = m.set_instrument(2, SpectrumAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),    # Photodiode signal
    dict(source="Slot1OutA", destination="Output1"),  # PID output → Laser
    dict(source="Slot1OutB", destination="Slot2InA"), # Error signal → Spectrum Analyzer
]
m.set_connections(connections=connections)
```

## VHDL Integration

### Custom Error Signal Processing
When building custom optical lock modules, route signals through LaserLockBox for established PDH infrastructure:

```python
# Custom VHDL module preprocesses photodiode signal
mcc = m.set_instrument(1, CloudCompile, bitstream="optical_preprocessor.tar.gz")
llb = m.set_instrument(2, LaserLockBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),         # Raw photodiode
    dict(source="Slot1OutA", destination="Slot2InA"),      # Preprocessed signal → LaserLockBox
    dict(source="Slot2OutA", destination="Output1"),       # LaserLockBox PID → Laser
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Integration:**
```vhdl
-- Example: Optical signal preprocessor for LaserLockBox
architecture OpticalPreprocessor of CustomWrapper is
begin
    process(Clk)
    begin
        if rising_edge(Clk) then
            -- Preprocess photodiode signal (filtering, gain adjustment)
            OutputA <= preprocessed_signal;  -- → LaserLockBox Input
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Simulate optical signal preprocessing
dut.InputA.value = photodiode_adc_value   # Simulated photodiode
await RisingEdge(dut.Clk)
assert dut.OutputA.value == expected_preprocessed
```

**Hardware Validation (LaserLockBox):**
```python
# Deploy to hardware and route to LaserLockBox for real optical locking
mcc = m.set_instrument(1, CloudCompile, bitstream="optical_preprocessor.tar.gz")
llb = m.set_instrument(2, LaserLockBox)
# Route preprocessed signal to LaserLockBox for PID control
connections = [dict(source="Slot1OutA", destination="Slot2InA")]
m.set_connections(connections=connections)
```

## Common Use Cases

1. **PDH Laser Locking**: Lock laser to optical cavity using Pound-Drever-Hall technique
2. **Dual-Stage PID**: Fast + slow PID for multi-timescale frequency stabilization
3. **Cavity Scanning**: Ramp laser frequency to characterize cavity modes
4. **Modulation Transfer Spectroscopy**: Lock to atomic transitions
5. **Optical Phase Lock Loops**: Stabilize laser relative phase

## Related Instruments
- **Oscilloscope**: Monitor error signals and lock performance
- **Spectrum Analyzer**: Analyze laser frequency noise
- **PID Controller**: Alternative for non-optical PID applications
- **CloudCompile**: Custom optical signal processing before locking
