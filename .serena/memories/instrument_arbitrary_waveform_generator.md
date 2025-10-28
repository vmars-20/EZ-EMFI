# Arbitrary Waveform Generator (AWG) - Instrument API Reference

## Purpose
Generate **custom arbitrary waveforms** from user-defined lookup tables (LUTs). Provides precise waveform generation with modulation capabilities (pulse, burst) for specialized signal testing.

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
import numpy as np

# Define custom waveform
custom_wave = np.sin(2 * np.pi * np.linspace(0, 3, 300))

config = MokuPlatformConfig(
    platform=MOKU_GO,
    slots={
        1: SlotConfig(
            instrument='ArbitraryWaveformGenerator',
            settings={
                'waveform': {
                    'channel': 1,
                    'lut_data': list(custom_wave),
                    'frequency': 1e3,
                    'amplitude': 1.0
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
from moku.instruments import ArbitraryWaveformGenerator
i = ArbitraryWaveformGenerator('192.168.1.100', force_connect=True)
```

### Waveform Definition (Python/NumPy)
```python
import numpy as np

# Define waveform as NumPy array (normalized to [-1, 1])
t = np.linspace(0, 1, 100)  # 100 sample points

# Example 1: Square wave
sq_wave = np.array([-1.0 if x < 0.5 else 1.0 for x in t])

# Example 2: Fourier synthesis (custom shape)
custom_wave = np.zeros(len(t))
for h in np.arange(1, 15, 2):  # Add harmonics
    custom_wave += (4 / (np.pi * h)) * np.cos(2 * np.pi * h * t)
custom_wave = custom_wave / max(abs(custom_wave))  # Normalize to [-1, 1]
```

### Waveform Generation
```python
# Upload waveform to AWG and configure output
i.generate_waveform(
    channel=1,
    sample_rate='Auto',        # Auto-optimize sample rate
    lut_data=list(sq_wave),    # Python list of waveform samples
    frequency=10e3,            # Hz (output frequency)
    amplitude=1                # Vpp (peak-to-peak amplitude)
)

i.generate_waveform(
    channel=2,
    sample_rate='Auto',
    lut_data=list(custom_wave),
    frequency=10e3,
    amplitude=1
)
```

### Pulse Modulation
```python
# Generate pulsed waveform (on/off cycling)
i.pulse_modulate(
    channel=1,
    dead_cycles=2,       # Number of cycles at dead_voltage between pulses
    dead_voltage=0       # Voltage during dead cycles (Vpp)
)
```

### Burst Modulation
```python
# Generate triggered bursts of waveform
i.burst_modulate(
    channel=2,
    trigger_source='Input1',    # Trigger from Input1 BNC
    trigger_mode='NCycle',      # 'NCycle' or 'Gated'
    burst_cycles=3,             # Number of waveform cycles per trigger
    trigger_level=0.1           # Trigger threshold (V)
)
```

## Routing Patterns

### Pattern 1: Dual Custom Waveforms
```python
# Generate two independent arbitrary waveforms
awg = m.set_instrument(1, ArbitraryWaveformGenerator)

connections = [
    dict(source="Slot1OutA", destination="Output1"),  # AWG Ch1 → Output1
    dict(source="Slot1OutB", destination="Output2"),  # AWG Ch2 → Output2
]
m.set_connections(connections=connections)

# Define waveforms
pulse_wave = np.array([1.0 if 0.2 < x < 0.8 else -1.0 for x in np.linspace(0, 1, 100)])
ramp_wave = np.linspace(-1, 1, 100)

awg.generate_waveform(1, 'Auto', list(pulse_wave), frequency=1e3, amplitude=1.0)
awg.generate_waveform(2, 'Auto', list(ramp_wave), frequency=1e3, amplitude=0.5)
```

### Pattern 2: AWG → Custom Module
```python
# Drive custom VHDL module with arbitrary waveform
awg = m.set_instrument(1, ArbitraryWaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="signal_processor.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # AWG → Custom module input
    dict(source="Slot2OutA", destination="Output1"),   # Processed signal → Output
]
m.set_connections(connections=connections)

# Generate test waveform to drive custom module
test_waveform = np.sin(2 * np.pi * np.linspace(0, 1, 1000))  # 1000-point sine
awg.generate_waveform(1, 'Auto', list(test_waveform), frequency=10e3, amplitude=1.0)
```

### Pattern 3: Triggered Burst Mode
```python
# Generate burst of waveform on external trigger
awg = m.set_instrument(1, ArbitraryWaveformGenerator)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Trigger input
    dict(source="Slot1OutA", destination="Output1"),   # Burst output
]
m.set_connections(connections=connections)

chirp_wave = np.sin(2 * np.pi * np.linspace(0, 10, 200))  # Frequency sweep
awg.generate_waveform(1, 'Auto', list(chirp_wave), frequency=1e3, amplitude=1.0)
awg.burst_modulate(1, trigger_source='Input1', trigger_mode='NCycle', 
                   burst_cycles=5, trigger_level=0.1)
```

## Multi-Instrument Scenarios

### AWG + Oscilloscope (Waveform Validation)
```python
# Generate custom waveform and verify with oscilloscope
awg = m.set_instrument(1, ArbitraryWaveformGenerator)
osc = m.set_instrument(2, Oscilloscope)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # AWG → Oscilloscope
    dict(source="Slot1OutA", destination="Output1"),   # AWG → BNC output
]
m.set_connections(connections=connections)

custom_waveform = np.sin(2 * np.pi * np.linspace(0, 3, 300))  # 3 cycles
awg.generate_waveform(1, 'Auto', list(custom_waveform), frequency=1e3, amplitude=1.0)
```

### AWG + Spectrum Analyzer (Harmonic Analysis)
```python
# Generate custom waveform and analyze frequency content
awg = m.set_instrument(1, ArbitraryWaveformGenerator)
sa = m.set_instrument(2, SpectrumAnalyzer)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # AWG → Spectrum Analyzer
]
m.set_connections(connections=connections)

# Generate waveform with specific harmonic content
t = np.linspace(0, 1, 500)
waveform = 0.5 * np.sin(2 * np.pi * t) + 0.3 * np.sin(6 * np.pi * t)  # Fundamental + 3rd harmonic
awg.generate_waveform(1, 'Auto', list(waveform), frequency=1e6, amplitude=1.0)
```

## VHDL Integration

### AWG Driving Custom Signal Processor
```python
# Use AWG to test custom VHDL signal processing module
awg = m.set_instrument(1, ArbitraryWaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="adaptive_filter.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Test signal → Custom module
    dict(source="Slot2OutA", destination="Output1"),   # Filtered output
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Example:**
```vhdl
-- Example: Adaptive filter module tested with AWG stimulus
architecture AdaptiveFilter of CustomWrapper is
begin
    process(Clk)
    begin
        if rising_edge(Clk) then
            -- Process arbitrary waveform from AWG
            OutputA <= filtered_signal;  -- Filtered version of InputA
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Test with simple sine wave stimulus
for i in range(100):
    dut.InputA.value = int(32767 * math.sin(2 * math.pi * i / 100))
    await RisingEdge(dut.Clk)
    # Verify filter response
```

**Hardware Validation (AWG):**
```python
# Deploy and test with real arbitrary waveform
complex_waveform = generate_complex_test_pattern()  # Custom test pattern
awg.generate_waveform(1, 'Auto', list(complex_waveform), frequency=1e3, amplitude=1.0)
# Observe actual hardware behavior with challenging stimulus
```

## Common Use Cases

1. **Custom Test Signal Generation**: Create specific test patterns for module validation
2. **Fourier Synthesis**: Generate waveforms with precise harmonic content
3. **Pulse Sequences**: Create complex timing patterns (radar, lidar, communications)
4. **Modulation Testing**: Test demodulation circuits with custom modulated signals
5. **Chirp Signals**: Frequency sweeps for system identification

## Waveform Design Tips

### Normalization
Always normalize waveforms to **[-1, 1]** range:
```python
waveform = waveform / max(abs(waveform))
```

### Sample Count
More samples = smoother waveform, but slower update rate:
- **100 samples**: Fast updates, coarse waveform
- **1000 samples**: Balanced
- **10000 samples**: High fidelity, slower updates

### Frequency Calculation
Output frequency = `sample_rate / num_samples * frequency_param`

## Related Instruments
- **WaveformGenerator**: Standard waveforms (sine, square, triangle)
- **Oscilloscope**: Verify generated waveforms
- **Spectrum Analyzer**: Analyze harmonic content
- **CloudCompile**: Custom signal processing driven by AWG
