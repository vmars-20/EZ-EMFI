# Phasemeter - Instrument API Reference

## Purpose
Precision **phase and frequency measurement** for up to 4 independent signals. Measures relative phase, frequency, and amplitude with high resolution, ideal for phase-locked loop (PLL) characterization and multi-channel coherence analysis.

---

## MokuBench Quick Reference

**Test Script**: `tests/mokubench_phasemeter_test.py` (minimal deployment test)

**Run Example**:
```bash
uv run python tests/mokubench_phasemeter_test.py --ip 192.168.13.159
```

**Note**: Phasemeter requires specific license/entitlement - not available on all Moku devices.

**Status**: ⚠️ Framework support complete, requires license for hardware testing

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Settings: `pm_loop` configuration per channel (auto_acquire, frequency, bandwidth)
- Data collection: `get_data()` returns phase/frequency/amplitude arrays
- Multi-channel phase comparison supported

---

## Key Python API Methods

### Initialization
```python
from moku.instruments import Phasemeter
i = Phasemeter('192.168.1.100', force_connect=True)
```

### Frontend Configuration
```python
# Configure up to 4 input channels
i.set_frontend(channel=1, coupling='DC', impedance='1MOhm', range='400mVpp')
i.set_frontend(channel=2, coupling='DC', impedance='1MOhm', range='400mVpp')
i.set_frontend(channel=3, coupling='DC', impedance='1MOhm', range='400mVpp')
i.set_frontend(channel=4, coupling='DC', impedance='1MOhm', range='400mVpp')
```

### Phase Measurement Configuration
```python
# Configure phase-locked loop for each channel
i.set_pm_loop(
    channel=1,
    auto_acquire=False,        # Manual frequency setting
    frequency=2e6,             # Hz (center frequency)
    bandwidth='100Hz'          # Loop bandwidth ('10Hz', '100Hz', '1kHz', '10kHz')
)
i.set_pm_loop(channel=2, auto_acquire=False, frequency=2e6, bandwidth='100Hz')
i.set_pm_loop(channel=3, auto_acquire=False, frequency=2e6, bandwidth='100Hz')
i.set_pm_loop(channel=4, auto_acquire=False, frequency=2e6, bandwidth='100Hz')
```

### Acquisition Settings
```python
# Set measurement update rate
i.set_acquisition_speed('596Hz')  # Options: '10Hz', '119Hz', '596Hz', '2.98kHz'
```

### Output Generation (Auxiliary Features)
```python
# Generate reference signal on Output 1
i.generate_output(channel=1, type='Sine', amplitude=1.0, frequency=2e6)

# Generate phase-locked output on Output 2 (locked to Input 2)
i.generate_output(channel=2, type='Sine', amplitude=0.5, phase_locked=True)

# Generate measured phase on Output 3 (DAC outputs phase as voltage)
i.generate_output(channel=3, type='Phase', scaling=1)  # 1 V/cycle

# Generate measured phase on Output 4 with different scaling
i.generate_output(channel=4, type='Phase', scaling=10)  # 10 V/cycle
```

### Data Retrieval
```python
# Get phase, frequency, and amplitude data
data = i.get_data()
# data contains: phase, frequency, amplitude for each channel
print(data['phase'][0])      # Channel 1 phase (radians)
print(data['frequency'][0])  # Channel 1 frequency (Hz)
print(data['amplitude'][0])  # Channel 1 amplitude (V)
```

## Routing Patterns

### Pattern 1: Dual-Signal Phase Comparison
```python
# Measure phase difference between two signals (e.g., PLL characterization)
pm = m.set_instrument(1, Phasemeter)

connections = [
    dict(source="Input1", destination="Slot1InA"),  # Reference signal
    dict(source="Input2", destination="Slot1InB"),  # Test signal
]
m.set_connections(connections=connections)

pm.set_frontend(1, coupling='DC', impedance='1MOhm', range='1Vpp')
pm.set_frontend(2, coupling='DC', impedance='1MOhm', range='1Vpp')
pm.set_pm_loop(1, auto_acquire=False, frequency=10e6, bandwidth='100Hz')
pm.set_pm_loop(2, auto_acquire=False, frequency=10e6, bandwidth='100Hz')
pm.set_acquisition_speed('596Hz')

data = pm.get_data()
phase_diff = data['phase'][1] - data['phase'][0]  # Relative phase
```

### Pattern 2: Custom Module Phase Monitoring
```python
# Monitor phase of custom VHDL module output
mcc = m.set_instrument(1, CloudCompile, bitstream="phase_shifter.tar.gz")
pm = m.set_instrument(2, Phasemeter)

connections = [
    dict(source="Input1", destination="Slot1InA"),   # Input signal → Custom module
    dict(source="Slot1OutA", destination="Slot2InA"), # Module output → Phasemeter Ch1
    dict(source="Slot1OutB", destination="Slot2InB"), # Module reference → Phasemeter Ch2
    dict(source="Slot1OutA", destination="Output1"),  # Output to BNC
]
m.set_connections(connections=connections)
```

### Pattern 3: Multi-Channel Coherence Analysis
```python
# Measure phase relationships between 4 synchronized signals
pm = m.set_instrument(1, Phasemeter)

connections = [
    dict(source="Input1", destination="Slot1InA"),  # Signal 1
    dict(source="Input2", destination="Slot1InB"),  # Signal 2
    # For 4-input platforms (Moku:Pro):
    # dict(source="Input3", destination="Slot1InC"),
    # dict(source="Input4", destination="Slot1InD"),
]
m.set_connections(connections=connections)

# All channels locked to same frequency
pm.set_pm_loop(1, frequency=1e6, bandwidth='100Hz')
pm.set_pm_loop(2, frequency=1e6, bandwidth='100Hz')
pm.set_pm_loop(3, frequency=1e6, bandwidth='100Hz')
pm.set_pm_loop(4, frequency=1e6, bandwidth='100Hz')

data = pm.get_data()
# Analyze relative phases between all channels
```

## Multi-Instrument Scenarios

### Waveform Generator + Phasemeter (PLL Testing)
```python
# Generate test signal and measure phase response
wg = m.set_instrument(1, WaveformGenerator)
pm = m.set_instrument(2, Phasemeter)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → Phasemeter
    dict(source="Slot1OutB", destination="Slot2InB"),  # Reference → Phasemeter
]
m.set_connections(connections=connections)

wg.generate_waveform(1, type='Sine', frequency=1e6, amplitude=1.0)
pm.set_pm_loop(1, frequency=1e6, bandwidth='100Hz')
```

### Custom Module + Phasemeter (Phase Shifter Validation)
```python
# Test custom phase shifter VHDL module
mcc = m.set_instrument(1, CloudCompile, bitstream="digital_phase_shifter.tar.gz")
pm = m.set_instrument(2, Phasemeter)

connections = [
    dict(source="Input1", destination="Slot1InA"),    # Input → Custom module
    dict(source="Slot1OutA", destination="Slot2InA"), # Phase-shifted output
    dict(source="Input1", destination="Slot2InB"),    # Original signal (reference)
]
m.set_connections(connections=connections)

# Measure phase shift introduced by custom module
data = pm.get_data()
measured_phase_shift = data['phase'][0] - data['phase'][1]
```

## VHDL Integration

### Custom Phase Shifter Module
```python
# Deploy custom VHDL phase shifter and validate with Phasemeter
mcc = m.set_instrument(1, CloudCompile, bitstream="programmable_phase_shifter.tar.gz")
pm = m.set_instrument(2, Phasemeter)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Input signal
    dict(source="Slot1OutA", destination="Slot2InA"),  # Shifted signal → Phasemeter
    dict(source="Slot1OutB", destination="Slot2InB"),  # Reference → Phasemeter
    dict(source="Slot1OutA", destination="Output1"),   # Output to BNC
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Example:**
```vhdl
-- Example: Programmable digital phase shifter
architecture PhaseShifter of CustomWrapper is
    signal phase_offset : unsigned(15 downto 0);
begin
    phase_offset <= unsigned(Control0(15 downto 0));  -- Phase shift control
    
    process(Clk)
    begin
        if rising_edge(Clk) then
            -- Apply phase shift to input signal
            OutputA <= phase_shifted_signal;   -- → Phasemeter Ch1
            OutputB <= InputA;                 -- Reference → Phasemeter Ch2
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Test phase shifter logic locally
dut.Control0.value = 0x00001000  # Set phase offset
dut.InputA.value = sine_wave_sample
await RisingEdge(dut.Clk)
assert dut.OutputA.value == expected_shifted_sample
```

**Hardware Validation (Phasemeter):**
```python
# Deploy and measure actual phase shift with Phasemeter
pm.set_pm_loop(1, frequency=1e6, bandwidth='100Hz')
pm.set_pm_loop(2, frequency=1e6, bandwidth='100Hz')
data = pm.get_data()
measured_shift = data['phase'][0] - data['phase'][1]  # Validate against expected
```

## Common Use Cases

1. **Phase-Locked Loop (PLL) Characterization**: Measure lock acquisition and phase noise
2. **RF Phase Comparison**: Validate phase relationships in multi-channel RF systems
3. **Digital Phase Shifter Testing**: Measure phase shift accuracy for custom VHDL modules
4. **Coherent Signal Analysis**: Multi-channel phase coherence measurements
5. **Frequency Stability Monitoring**: Track frequency drift over time

## Related Instruments
- **WaveformGenerator**: Generate test signals for phase measurement
- **Lock-In Amplifier**: Phase-sensitive detection (related concept)
- **Time & Frequency Analyzer**: Allan deviation and timing jitter analysis
- **CloudCompile**: Custom phase manipulation modules
