# Digital Filter Box - Instrument API Reference

## Purpose
Real-time **IIR digital filtering** with configurable filter types (Butterworth, Elliptic, Chebyshev, Bessel). Provides up to 4 independent filter channels (platform-dependent) with control matrix for flexible signal routing.

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
            instrument='DigitalFilterBox',
            settings={
                'filter': {
                    'channel': 1,
                    'sampling_rate': '3.906MHz',
                    'shape': 'Lowpass',
                    'type': 'Butterworth',
                    'low_corner': 1e3,
                    'order': 8
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
from moku.instruments import DigitalFilterBox
i = DigitalFilterBox('192.168.1.100', force_connect=True)
```

### Frontend Configuration
```python
# Configure input channels
i.set_frontend(channel=1, coupling='DC', impedance='1MOhm', attenuation='0dB')
i.set_frontend(channel=2, coupling='DC', impedance='1MOhm', attenuation='0dB')
```

### Control Matrix (Input Routing)
```python
# Route physical inputs to filter channels with gain control
# Channel 1 = Input1 only
i.set_control_matrix(channel=1, input_gain1=1, input_gain2=0)

# Channel 2 = Input1 + Input2 (summed)
i.set_control_matrix(channel=2, input_gain1=1, input_gain2=1)

# Channel 3 = Input2 only
i.set_control_matrix(channel=3, input_gain1=0, input_gain2=1)
```

### Filter Configuration
```python
# Configure IIR filter
i.set_filter(
    channel=1,
    sampling_rate='3.906MHz',      # Platform-specific (Moku:Go example)
    shape='Lowpass',               # 'Lowpass', 'Highpass', 'Bandpass', 'Bandstop'
    type='Butterworth',            # 'Butterworth', 'Elliptic', 'Chebyshev', 'Bessel'
    low_corner=1e3,                # Hz (for lowpass/bandpass)
    high_corner=100e3,             # Hz (for highpass/bandpass)
    order=8                        # Filter order (2, 4, 6, 8)
)

# Example: Highpass Elliptic filter
i.set_filter(
    channel=2,
    sampling_rate='3.906MHz',
    shape='Highpass',
    type='Elliptic',
    high_corner=100e3,
    order=8
)
```

### Monitor Configuration
```python
# Route filter outputs to monitoring probes
i.set_monitor(channel=1, source="Output1")  # Monitor Output1
i.set_monitor(channel=2, source="Output2")  # Monitor Output2
```

### Output Enable
```python
# Enable physical DAC outputs
i.enable_output(channel=1, signal=True, output=True)
i.enable_output(channel=2, signal=True, output=True)
```

### Data Acquisition
```python
# Set timebase for oscilloscope-like monitoring
i.set_timebase(t1=-0.5e-3, t2=0.5e-3)  # View ±0.5 ms window

# Get filtered data
data = i.get_data()
filtered_ch1 = data['ch1']
filtered_ch2 = data['ch2']
timestamps = data['time']
```

## Routing Patterns

### Pattern 1: Dual Filter Channels
```python
# Filter two independent signals
dfb = m.set_instrument(1, DigitalFilterBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),   # Signal 1 → Filter Ch1
    dict(source="Input2", destination="Slot1InB"),   # Signal 2 → Filter Ch2
    dict(source="Slot1OutA", destination="Output1"), # Filtered 1 → Output
    dict(source="Slot1OutB", destination="Output2"), # Filtered 2 → Output
]
m.set_connections(connections=connections)

dfb.set_control_matrix(1, input_gain1=1, input_gain2=0)  # Ch1 = Input1
dfb.set_control_matrix(2, input_gain1=0, input_gain2=1)  # Ch2 = Input2
dfb.set_filter(1, '3.906MHz', shape='Lowpass', type='Butterworth', low_corner=1e3, order=8)
dfb.set_filter(2, '3.906MHz', shape='Highpass', type='Elliptic', high_corner=100e3, order=8)
dfb.enable_output(1, signal=True, output=True)
dfb.enable_output(2, signal=True, output=True)
```

### Pattern 2: Custom Module + Filter
```python
# Filter custom VHDL module output
mcc = m.set_instrument(1, CloudCompile, bitstream="signal_generator.tar.gz")
dfb = m.set_instrument(2, DigitalFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Custom module → Filter
    dict(source="Slot2OutA", destination="Output1"),   # Filtered signal → Output
]
m.set_connections(connections=connections)

dfb.set_filter(1, '3.906MHz', shape='Lowpass', type='Butterworth', low_corner=10e3, order=4)
dfb.enable_output(1, signal=True, output=True)
```

### Pattern 3: Summed Inputs with Filtering
```python
# Sum two inputs and apply bandpass filter
dfb = m.set_instrument(1, DigitalFilterBox)

connections = [
    dict(source="Input1", destination="Slot1InA"),
    dict(source="Input2", destination="Slot1InB"),
    dict(source="Slot1OutA", destination="Output1"),
]
m.set_connections(connections=connections)

# Sum inputs with equal gain
dfb.set_control_matrix(1, input_gain1=1, input_gain2=1)
dfb.set_filter(1, '3.906MHz', shape='Bandpass', type='Chebyshev', 
               low_corner=1e3, high_corner=100e3, order=6)
dfb.enable_output(1, signal=True, output=True)
```

## Multi-Instrument Scenarios

### Waveform Generator + Digital Filter
```python
# Generate signal and apply digital filtering
wg = m.set_instrument(1, WaveformGenerator)
dfb = m.set_instrument(2, DigitalFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → Filter
    dict(source="Slot2OutA", destination="Output1"),   # Filtered → Output
]
m.set_connections(connections=connections)

wg.generate_waveform(1, type='Square', frequency=1e3, amplitude=1.0)
dfb.set_filter(1, '3.906MHz', shape='Lowpass', type='Butterworth', low_corner=5e3, order=8)
```

### Filter + Oscilloscope Monitoring
```python
# Apply filter and monitor with oscilloscope
dfb = m.set_instrument(1, DigitalFilterBox)
osc = m.set_instrument(2, Oscilloscope)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Raw signal → Filter
    dict(source="Slot1OutA", destination="Slot2InA"),  # Filtered → Oscilloscope
    dict(source="Input1", destination="Slot2InB"),     # Raw signal → Oscilloscope (comparison)
]
m.set_connections(connections=connections)
```

## VHDL Integration

### Custom Module + Digital Filter Cascade
```python
# VHDL module generates signal, Digital Filter Box processes it
mcc = m.set_instrument(1, CloudCompile, bitstream="custom_waveform.tar.gz")
dfb = m.set_instrument(2, DigitalFilterBox)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Custom signal → Filter
    dict(source="Slot2OutA", destination="Output1"),   # Filtered output
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Example:**
```vhdl
-- Example: Noisy signal generator (to be filtered by DigitalFilterBox)
architecture NoisyGenerator of CustomWrapper is
begin
    process(Clk)
    begin
        if rising_edge(Clk) then
            -- Generate signal with high-frequency noise
            OutputA <= signal_with_noise;  -- → DigitalFilterBox removes noise
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Test custom signal generator locally
await RisingEdge(dut.Clk)
assert dut.OutputA.value == expected_noisy_signal
```

**Hardware Validation (Digital Filter Box):**
```python
# Deploy and apply real-time filtering
dfb.set_filter(1, '3.906MHz', shape='Lowpass', type='Butterworth', low_corner=10e3, order=8)
data = dfb.get_data()
# Verify noise components above 10 kHz are attenuated
```

## Common Use Cases

1. **Anti-Aliasing Filters**: Lowpass filtering before ADC sampling
2. **Noise Reduction**: Remove high-frequency noise from sensor signals
3. **Bandpass Extraction**: Isolate specific frequency bands
4. **Signal Conditioning**: Prepare signals for analysis or control systems
5. **Custom Module Post-Processing**: Filter outputs from VHDL-generated signals

## Related Instruments
- **FIR Filter Builder**: Alternative filter design (linear phase response)
- **Spectrum Analyzer**: Analyze filter frequency response
- **Oscilloscope**: Monitor filtered signals in time domain
- **CloudCompile**: Custom pre-filtering or signal generation
