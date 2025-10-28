# FIR Filter Builder - Instrument API Reference

## Purpose
Design and deploy **custom FIR (Finite Impulse Response) filters** with configurable coefficients. Provides up to 4 independent filter channels (platform-dependent) with linear phase response and multiple window functions.

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
            instrument='FIRFilterBuilder',
            settings={
                'filter': {
                    'channel': 1,
                    'sample_rate': '15.63MHz',
                    'coefficient_count': 201,
                    'shape': 'Lowpass',
                    'low_corner': 0.1,
                    'window': 'Blackman'
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
from moku.instruments import FIRFilterBox
i = FIRFilterBox('192.168.1.100', force_connect=True)
```

### Frontend Configuration
```python
# Configure input channels
i.set_frontend(channel=1, impedance='1MOhm', attenuation='0dB', coupling='DC')
i.set_frontend(channel=2, impedance='1MOhm', attenuation='0dB', coupling='DC')
```

### Control Matrix and Gain
```python
# Route inputs to filter channels
i.set_control_matrix(channel=1, input_gain1=1, input_gain2=0)  # Ch1 = Input1
i.set_input_gain(channel=1, gain=0)   # dB (additional gain)
i.set_input_offset(channel=1, offset=0)  # V (DC offset)

i.set_output_gain(channel=1, gain=0)   # dB (output gain)
i.set_output_offset(channel=1, offset=0)  # V (output DC offset)
```

### FIR Filter Design by Frequency
```python
# Design FIR filter with frequency specification
i.set_by_frequency(
    channel=1,
    sample_rate='39.06MHz',        # Platform-specific (Moku:Pro: 39.06MHz, Moku:Lab/Go: 15.63MHz)
    coefficient_count=201,         # Number of FIR taps (more = sharper cutoff, higher latency)
    shape='Lowpass',               # 'Lowpass', 'Highpass', 'Bandpass', 'Bandstop'
    low_corner=0.1,                # Fraction of sample rate (0.1 = 10% of sample rate)
    high_corner=0.4,               # Fraction of sample rate (for bandpass/bandstop)
    window='Blackman'              # 'Blackman', 'Bartlett', 'Hann', 'Hamming'
)

# Example calculations:
# Sample Rate: 39.06 MHz
# low_corner=0.1  → 3.906 MHz cutoff
# high_corner=0.4 → 15.624 MHz cutoff
```

### Filter Shape Examples
```python
# Lowpass FIR filter
i.set_by_frequency(
    channel=1, sample_rate='39.06MHz', coefficient_count=201,
    shape='Lowpass', low_corner=0.1, window='Blackman'
)

# Highpass FIR filter
i.set_by_frequency(
    channel=2, sample_rate='39.06MHz', coefficient_count=201,
    shape='Highpass', high_corner=0.4, window='Bartlett'
)

# Bandpass FIR filter
i.set_by_frequency(
    channel=3, sample_rate='39.06MHz', coefficient_count=201,
    shape='Bandpass', low_corner=0.1, high_corner=0.4, window='Hann'
)

# Bandstop (Notch) FIR filter
i.set_by_frequency(
    channel=4, sample_rate='39.06MHz', coefficient_count=201,
    shape='Bandstop', low_corner=0.1, high_corner=0.4, window='Hamming'
)
```

### Window Functions
- **Blackman**: Excellent stopband attenuation, wider transition band
- **Bartlett**: Simple triangular window, moderate performance
- **Hann**: Good general-purpose window, balanced characteristics
- **Hamming**: Similar to Hann, slightly better stopband

### Output Enable
```python
# Enable physical DAC outputs
i.enable_output(channel=1, signal=True, output=True)
i.enable_output(channel=2, signal=True, output=True)
```

## Routing Patterns

### Pattern 1: Multi-Channel FIR Filtering
```python
# Apply different FIR filters to multiple signals
fir = m.set_instrument(1, FIRFilterBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),   # Signal 1 → FIR Ch1 (Lowpass)
    dict(source="Input2", destination="Slot1InB"),   # Signal 2 → FIR Ch2 (Highpass)
    dict(source="Slot1OutA", destination="Output1"), # Filtered 1 → Output
    dict(source="Slot1OutB", destination="Output2"), # Filtered 2 → Output
]
m.set_connections(connections=connections)

# Moku:Pro example (39.06 MHz sample rate)
fir.set_by_frequency(1, '39.06MHz', 201, shape='Lowpass', low_corner=0.1, window='Blackman')
fir.set_by_frequency(2, '39.06MHz', 201, shape='Highpass', high_corner=0.4, window='Bartlett')
fir.enable_output(1, signal=True, output=True)
fir.enable_output(2, signal=True, output=True)
```

### Pattern 2: Custom Module + FIR Filter
```python
# Filter custom VHDL module output with linear-phase FIR
mcc = m.set_instrument(1, CloudCompile, bitstream="signal_source.tar.gz")
fir = m.set_instrument(2, FIRFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Custom signal → FIR
    dict(source="Slot2OutA", destination="Output1"),   # Filtered → Output
]
m.set_connections(connections=connections)

fir.set_by_frequency(1, '39.06MHz', 201, shape='Lowpass', low_corner=0.2, window='Blackman')
fir.enable_output(1, signal=True, output=True)
```

### Pattern 3: Notch Filter (Bandstop)
```python
# Remove specific frequency band (e.g., 60 Hz power line noise)
fir = m.set_instrument(1, FIRFilterBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),
    dict(source="Slot1OutA", destination="Output1"),
]
m.set_connections(connections=connections)

# Example: Remove 60 Hz ± 10 Hz noise (assumes 15.63 MHz sample rate)
# low_corner = 50 Hz / 15.63 MHz ≈ 0.0000032
# high_corner = 70 Hz / 15.63 MHz ≈ 0.0000045
fir.set_by_frequency(1, '15.63MHz', 201, shape='Bandstop', 
                     low_corner=0.0000032, high_corner=0.0000045, window='Blackman')
fir.enable_output(1, signal=True, output=True)
```

## Multi-Instrument Scenarios

### Waveform Generator + FIR Filter
```python
# Generate test signal and apply FIR filtering
wg = m.set_instrument(1, WaveformGenerator)
fir = m.set_instrument(2, FIRFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → FIR
    dict(source="Slot2OutA", destination="Output1"),   # Filtered → Output
]
m.set_connections(connections=connections)

wg.generate_waveform(1, type='Square', frequency=1e3, amplitude=1.0)
fir.set_by_frequency(1, '39.06MHz', 201, shape='Lowpass', low_corner=0.05, window='Blackman')
```

### FIR Filter + Spectrum Analyzer
```python
# Design filter and verify frequency response
fir = m.set_instrument(1, FIRFilterBox)
sa = m.set_instrument(2, SpectrumAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Input signal → FIR
    dict(source="Slot1OutA", destination="Slot2InA"),  # Filtered → Spectrum Analyzer
    dict(source="Input1", destination="Slot2InB"),     # Raw → Spectrum Analyzer (comparison)
]
m.set_connections(connections=connections)
```

## VHDL Integration

### Custom Signal + FIR Post-Processing
```python
# VHDL module generates signal, FIR filter processes it
mcc = m.set_instrument(1, CloudCompile, bitstream="pulse_generator.tar.gz")
fir = m.set_instrument(2, FIRFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Pulses → FIR
    dict(source="Slot2OutA", destination="Output1"),   # Smoothed output
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Example:**
```vhdl
-- Example: Pulse generator with sharp edges (to be smoothed by FIR)
architecture PulseGen of CustomWrapper is
begin
    process(Clk)
    begin
        if rising_edge(Clk) then
            -- Generate square pulses with fast rise/fall times
            OutputA <= pulse_output;  -- → FIR filter smooths edges
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Test pulse generator locally
await RisingEdge(dut.Clk)
assert dut.OutputA.value == expected_pulse_state
```

**Hardware Validation (FIR Filter):**
```python
# Deploy and apply linear-phase lowpass filtering
fir.set_by_frequency(1, '39.06MHz', 201, shape='Lowpass', low_corner=0.1, window='Blackman')
# Measure rise time with oscilloscope to verify smoothing
```

## Common Use Cases

1. **Audio Filtering**: Equalization and noise reduction with linear phase
2. **Anti-Aliasing**: Pre-sampling lowpass filters
3. **Pulse Shaping**: Smooth sharp edges from digital signals
4. **Matched Filtering**: Optimal detection of known signal patterns
5. **Custom Spectral Shaping**: Arbitrary frequency response design

## Key Advantages of FIR Filters
- **Linear Phase Response**: No phase distortion (constant group delay)
- **Stable**: Always stable (no feedback)
- **Precise Frequency Response**: Exact control via coefficient design
- **Flexible**: Arbitrary magnitude response possible

## Related Instruments
- **Digital Filter Box**: IIR filtering (sharper cutoff, non-linear phase)
- **Spectrum Analyzer**: Verify filter frequency response
- **Oscilloscope**: Monitor time-domain filter output
- **CloudCompile**: Custom pre-filtering or signal generation
