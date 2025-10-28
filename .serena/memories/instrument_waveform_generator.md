# Moku Instrument: Waveform Generator

## Purpose
Signal generation for stimulus, testing, or reference signals. Generates standard waveforms (sine, square, ramp) or arbitrary waveforms. Useful for **driving custom module inputs** or providing test signals.

---

## MokuBench Quick Reference

**Test Script**: `tests/mokubench_waveformgen_test.py`

**Run Example**:
```bash
uv run python tests/mokubench_waveformgen_test.py --ip 192.168.13.159 --frequency 1000 --amplitude 1.0
```

**What It Demonstrates**:
- Deploy WaveformGenerator + CloudCompile (simple_counter)
- Generate 1 kHz sine wave on OUT1
- Route counter output to OUT2
- Continuous signal generation

**Status**: ✅ Validated on Moku:Go hardware

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Settings: `channel`, `type`, `frequency`, `amplitude` configuration
- Signal generation: `generate_waveform()` applied during setup
- Works with all waveform types (Sine, Square, Triangle, Ramp, etc.)

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, WaveformGenerator

m = MultiInstrument('192.168.1.100', platform_id=2)
wg = m.set_instrument(1, WaveformGenerator)  # Load into Slot 1
```

### Configuration Methods

**Generate Standard Waveform**:
```python
wg.generate_waveform(channel, waveform_type, **kwargs)

# Parameters:
# - channel: 1 or 2
# - waveform_type: "Sine", "Square", "Ramp", "Triangle", "DC", "Pulse"
# - kwargs: amplitude, frequency, offset, phase, duty (for square/pulse), symmetry (for ramp)

# Examples:
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)
wg.generate_waveform(2, "Square", amplitude=0.5, frequency=2e3, duty=50)
wg.generate_waveform(1, "Ramp", amplitude=2.0, frequency=500, symmetry=50)
wg.generate_waveform(2, "DC", amplitude=1.5)  # Constant voltage
```

**Modulation** (Amplitude/Frequency Modulation):
```python
# Amplitude Modulation (AM)
wg.generate_waveform(1, "Sine",
                     amplitude=1.0,
                     frequency=10e3,
                     am_enable=True,
                     am_depth=50,          # Modulation depth (%)
                     am_frequency=100)     # Modulation frequency (Hz)

# Frequency Modulation (FM) / Sweep
wg.generate_waveform(2, "Sine",
                     amplitude=1.0,
                     frequency=1e3,
                     sweep_enable=True,
                     sweep_start=100,      # Start frequency (Hz)
                     sweep_stop=10e3,      # Stop frequency (Hz)
                     sweep_time=1.0)       # Sweep duration (s)
```

**Triggered/Gated Output**:
```python
wg.generate_waveform(1, "Sine",
                     amplitude=1.0,
                     frequency=1e3,
                     trigger_enable=True,
                     trigger_source="Input1")  # Gate signal from physical input
```

**Phase Synchronization** (between channels):
```python
wg.sync_output_phase()  # Align phase of both channels
```

---

## Routing Patterns

### Pattern 1: Generate Signal to Physical Output
**Use Case**: Provide stimulus to external device under test (DUT)

```python
wg = m.set_instrument(1, WaveformGenerator)

connections = [
    dict(source="Slot1OutA", destination="Output1"),  # WaveformGen Ch1 → OUT1 BNC
    dict(source="Slot1OutB", destination="Output2"),  # WaveformGen Ch2 → OUT2 BNC
]
m.set_connections(connections=connections)

# Generate 1kHz sine on OUT1, 2kHz square on OUT2
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)
wg.generate_waveform(2, "Square", amplitude=0.5, frequency=2e3, duty=25)
```

**Conceptual Wiring**:
```
Slot 1 (WaveformGen) OutputA → Physical OUT1 (to external DUT)
Slot 1 (WaveformGen) OutputB → Physical OUT2 (to external DUT)
```

---

### Pattern 2: Drive Custom Module Input (Cross-Slot Routing)
**Use Case**: WaveformGen in Slot 1 provides stimulus to CloudCompile module in Slot 2

```python
wg = m.set_instrument(1, WaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_filter.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → Module InputA
    dict(source="Slot1OutB", destination="Slot2InB"),  # WaveformGen → Module InputB
]
m.set_connections(connections=connections)

# Generate test signals
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)    # Test signal
wg.generate_waveform(2, "Square", amplitude=0.5, frequency=100)  # Clock/trigger signal
```

**Conceptual Wiring**:
```
Slot 1 (WaveformGen) OutputA → Slot 2 (Custom Module) InputA
Slot 1 (WaveformGen) OutputB → Slot 2 (Custom Module) InputB
```

---

### Pattern 3: Stimulus + Monitor (Three-Slot Pipeline)
**Use Case**: WaveformGen → Custom Module → Oscilloscope

```python
wg = m.set_instrument(1, WaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_filter.tar.gz")
osc = m.set_instrument(3, Oscilloscope)  # Requires 4-slot platform (Moku:Pro)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Stimulus → Module
    dict(source="Slot2OutA", destination="Slot3InA"),  # Module output → Oscilloscope Ch1
    dict(source="Slot1OutA", destination="Slot3InB"),  # Original stimulus → Osc Ch2 (compare)
]
m.set_connections(connections=connections)

# Generate stimulus
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)

# Observe input vs output on oscilloscope
osc.set_timebase(-2e-3, 2e-3)
data = osc.get_data()
# data['ch1'] = filtered output
# data['ch2'] = original input
```

**Conceptual Wiring**:
```
Slot 1 (WaveformGen) OutputA → Slot 2 (Filter) InputA
                              → Slot 3 (Oscilloscope) InputB (reference)
Slot 2 (Filter) OutputA       → Slot 3 (Oscilloscope) InputA (result)
```

---

## Multi-Instrument Scenarios

### Scenario 1: WaveformGen + Oscilloscope (Signal Verification)
**Setup**: Generate signal, verify on oscilloscope

```python
wg = m.set_instrument(1, WaveformGenerator)
osc = m.set_instrument(2, Oscilloscope)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → Osc
]
m.set_connections(connections=connections)

# Generate complex waveform
wg.generate_waveform(1, "Sine",
                     amplitude=1.0,
                     frequency=10e3,
                     am_enable=True,
                     am_depth=50,
                     am_frequency=100)

# Capture and verify
osc.set_timebase(-10e-3, 10e-3)
data = osc.get_data()
```

---

### Scenario 2: WaveformGen + CloudCompile (VHDL Module Testing)
**Setup**: Provide controlled stimulus to custom VHDL module

```python
wg = m.set_instrument(1, WaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="dsp_core.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Test signal → Module
    dict(source="Slot2OutA", destination="Output1"),   # Module result → Physical OUT1
]
m.set_connections(connections=connections)

# Test with swept frequency
wg.generate_waveform(1, "Sine",
                     amplitude=1.0,
                     frequency=1e3,
                     sweep_enable=True,
                     sweep_start=100,
                     sweep_stop=10e3,
                     sweep_time=5.0)

# Module processes swept signal, output goes to physical BNC
```

---

### Scenario 3: Dual-Channel Synchronized Outputs
**Use Case**: I/Q signals, differential signals, or phase-shifted test signals

```python
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3, phase=0)
wg.generate_waveform(2, "Sine", amplitude=1.0, frequency=1e3, phase=90)  # 90° shift
wg.sync_output_phase()  # Ensure phase coherence

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # I signal → Module InputA
    dict(source="Slot1OutB", destination="Slot2InB"),  # Q signal → Module InputB
]
m.set_connections(connections=connections)
```

---

## Common Usage Tips

### Virtual Output Mapping
When WaveformGenerator is in **Slot N**:
- `generate_waveform(1, ...)` → **OutputA** (SlotNOutA in routing)
- `generate_waveform(2, ...)` → **OutputB** (SlotNOutB in routing)
- OutputC, OutputD typically not used by built-in WaveformGen

### Amplitude Units
- Amplitude is specified in **Volts peak** (not peak-to-peak)
- Example: `amplitude=1.0` → ±1V signal (2Vpp)

### Frequency Limits
- Check platform datasheet for DAC sample rate limits
- Moku:Go: Up to ~20 MHz output bandwidth
- Moku:Lab: Up to ~300 MHz output bandwidth
- Moku:Pro/Delta: Higher bandwidth (check datasheets)

### Waveform Types
| Type | Description | Key Parameters |
|------|-------------|----------------|
| `"Sine"` | Sinusoidal | frequency, amplitude, phase |
| `"Square"` | Square wave | frequency, amplitude, duty (%) |
| `"Ramp"` | Sawtooth/Ramp | frequency, amplitude, symmetry (0-100%) |
| `"Triangle"` | Triangle wave | frequency, amplitude |
| `"DC"` | Constant voltage | amplitude (DC offset) |
| `"Pulse"` | Pulse train | frequency, amplitude, duty (%), edge time |

---

## Relationship to CustomWrapper (VHDL Development)

When **driving a custom CloudCompile module** with WaveformGen:

**VHDL (Your Module)**:
```vhdl
architecture MyModule of CustomWrapper is
    signal test_signal : signed(15 downto 0);
    signal trigger     : signed(15 downto 0);
begin
    test_signal <= InputA;   -- Driven by WaveformGen Ch1
    trigger     <= InputB;   -- Driven by WaveformGen Ch2

    -- Your processing logic...
end architecture;
```

**Python (Test Setup)**:
```python
wg = m.set_instrument(1, WaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_module.tar.gz")

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Ch1 → InputA (test_signal)
    dict(source="Slot1OutB", destination="Slot2InB"),  # Ch2 → InputB (trigger)
]
m.set_connections(connections=connections)

# Drive test_signal with 1kHz sine
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)

# Drive trigger with 10Hz square wave
wg.generate_waveform(2, "Square", amplitude=0.5, frequency=10, duty=10)
```

**Result**: Your VHDL module receives controlled test signals, just like in a CocotB testbench, but on real hardware!

---

## Comparison: CocotB vs Hardware Testing

### CocotB Testbench (Simulation):
```python
@cocotb.test()
async def test_my_module(dut):
    dut.InputA.value = 0x1234  # Manual signal assignment
    await ClockCycles(dut.Clk, 10)
```

### Hardware Testing (WaveformGen):
```python
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)  # Continuous stimulus
# Module processes signal in real-time on Moku FPGA
```

**Key Difference**: CocotB drives discrete values, WaveformGen provides continuous analog signals (converted to 16-bit signed by ADC before reaching your VHDL CustomWrapper inputs).

---

## References
- **Python API Examples**: `mcc_py_api_examples/waveformgenerator_*.py`
- **Routing Guide**: `docs/MCC_Routing_Guide.md`
- **Modulation Example**: `mcc_py_api_examples/waveformgenerator_modulation.py`
- **Triggered Output Example**: `mcc_py_api_examples/waveformgenerator_triggered.py`
