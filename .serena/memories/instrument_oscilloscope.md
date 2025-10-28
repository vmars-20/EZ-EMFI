# Moku Instrument: Oscilloscope

## Purpose
Real-time waveform capture and display for time-domain signal analysis. Typically used to **monitor custom module outputs**, debug signal integrity, or observe external inputs.

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, Oscilloscope

m = MultiInstrument('192.168.1.100', platform_id=2)
osc = m.set_instrument(1, Oscilloscope)  # Load into Slot 1
```

### Configuration Methods

**Timebase (X-axis)**:
```python
osc.set_timebase(start, stop)
# Example: osc.set_timebase(-5e-3, 5e-3)  # ±5ms window
```

**Triggering**:
```python
osc.set_trigger(type, source, level, mode, edge)
# Example: osc.set_trigger(type="Edge", source="ChannelA", level=0.5, mode="Normal", edge="Rising")
```

**Waveform Generation** (Oscilloscope can also generate!):
```python
osc.generate_waveform(channel, waveform_type, amplitude, frequency, **kwargs)
# Example: osc.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)
# Example: osc.generate_waveform(2, "Square", amplitude=0.5, frequency=2e3, duty=50)
```

**Phase Sync** (between generated waveforms):
```python
osc.sync_output_phase()
```

### Data Acquisition

**Get Single Frame**:
```python
data = osc.get_data()
# Returns dict: {'time': [...], 'ch1': [...], 'ch2': [...]}
```

**Wait for Trigger Re-acquisition**:
```python
data = osc.get_data(wait_reacquire=True)
```

---

## Routing Patterns

### Pattern 1: Monitor External Signal (Physical Input)
**Use Case**: Observe external signal on BNC IN1

```python
connections = [
    dict(source="Input1", destination="Slot1InA"),   # Physical IN1 → Oscilloscope Ch1
]
m.set_connections(connections=connections)

# Configure and read
osc.set_timebase(-1e-3, 1e-3)
data = osc.get_data()
print("Channel 1 data:", data['ch1'])
```

**Conceptual Wiring**:
```
Physical IN1 → Oscilloscope Slot1 InputA (displayed as Channel 1)
```

---

### Pattern 2: Monitor Custom Module Output (Cross-Slot Routing)
**Use Case**: Oscilloscope in Slot 1 monitors CloudCompile module in Slot 2

```python
# Setup
osc = m.set_instrument(1, Oscilloscope)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_module.tar.gz")

# Route custom module output → Oscilloscope input
connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module OutputA → Osc Ch1
    dict(source="Slot2OutB", destination="Slot1InB"),  # Module OutputB → Osc Ch2
]
m.set_connections(connections=connections)

# Monitor in real-time
osc.set_timebase(-10e-6, 10e-6)  # ±10μs window
osc.set_trigger(type="Edge", source="ChannelA", level=0.1, mode="Normal", edge="Rising")

data = osc.get_data()
print("Module OutputA:", data['ch1'])
print("Module OutputB:", data['ch2'])
```

**Conceptual Wiring**:
```
Slot 2 (Custom Module) OutputA → Slot 1 (Oscilloscope) InputA (Ch1)
Slot 2 (Custom Module) OutputB → Slot 1 (Oscilloscope) InputB (Ch2)
```

---

### Pattern 3: Monitor + Output to Physical (Fan-Out Routing)
**Use Case**: Monitor custom module output AND send to physical BNC simultaneously

```python
connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module → Osc (monitor)
    dict(source="Slot2OutA", destination="Output1"),   # Module → OUT1 (physical device)
]
m.set_connections(connections=connections)
```

**Conceptual Wiring**:
```
Slot 2 OutputA → Slot 1 InputA (monitoring)
                → Physical OUT1 (to target device)
```

---

## Multi-Instrument Scenarios

### Scenario 1: Oscilloscope + Waveform Generator (Stimulus/Response)
**Setup**: WaveformGen in Slot 2 generates signal, Oscilloscope in Slot 1 captures it

```python
wg = m.set_instrument(2, WaveformGenerator)
osc = m.set_instrument(1, Oscilloscope)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # WaveformGen → Osc
]
m.set_connections(connections=connections)

# Generate 1kHz sine wave
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)

# Capture on oscilloscope
osc.set_timebase(-2e-3, 2e-3)
data = osc.get_data()
```

---

### Scenario 2: Oscilloscope + CloudCompile (Development/Debug)
**Setup**: Monitor custom VHDL module outputs in real-time

```python
mcc = m.set_instrument(2, CloudCompile, bitstream="emfi_seq.tar.gz")
osc = m.set_instrument(1, Oscilloscope)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # EMFI pulse → Ch1
    dict(source="Slot2OutB", destination="Slot1InB"),  # Status signals → Ch2
]
m.set_connections(connections=connections)

# Configure module
mcc.set_control(0, 0xC0000001)  # Enable
mcc.set_control(1, 0x000000FF)  # DelayS1

# Observe outputs
osc.set_trigger(type="Edge", source="ChannelA", level=0.5, mode="Normal")
data = osc.get_data(wait_reacquire=True)
```

---

## Common Usage Tips

### Accessing Channel Data
```python
data = osc.get_data()

time = data['time']      # Time axis (seconds)
ch1 = data['ch1']        # Channel 1 voltage values
ch2 = data['ch2']        # Channel 2 voltage values

# Plot with matplotlib
import matplotlib.pyplot as plt
plt.plot(time, ch1, label='Channel 1')
plt.plot(time, ch2, label='Channel 2')
plt.show()
```

### Trigger Modes
- **"Normal"**: Wait for trigger condition, then capture
- **"Auto"**: Capture continuously, trigger when condition met
- **"Single"**: Capture once, then stop

### Virtual Input Mapping
When Oscilloscope is in **Slot N**:
- `SlotNInA` → **Channel 1** (displayed in GUI)
- `SlotNInB` → **Channel 2** (displayed in GUI)
- `SlotNInC` → (May not be accessible in GUI, depends on instrument)
- `SlotNInD` → (May not be accessible in GUI, depends on instrument)

**Note**: Built-in instruments typically expose only 2 channels in GUI, even though CustomWrapper provides 4 inputs. Check instrument docs for full channel access.

---

## Relationship to CustomWrapper (VHDL Development)

When you create a **custom CloudCompile module**, you can route outputs to Oscilloscope for real-time monitoring:

**VHDL (Your Module)**:
```vhdl
architecture MyModule of CustomWrapper is
begin
    OutputA <= my_signal_1;  -- Will be monitored on Osc Ch1
    OutputB <= my_signal_2;  -- Will be monitored on Osc Ch2
end architecture;
```

**Python (Deployment)**:
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="my_module.tar.gz")
osc = m.set_instrument(1, Oscilloscope)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # my_signal_1 → Ch1
    dict(source="Slot2OutB", destination="Slot1InB"),  # my_signal_2 → Ch2
]
m.set_connections(connections=connections)
```

**Result**: Real-time waveform view of your VHDL signals on Moku app (iPad/macOS/Windows).

---

## MokuBench Quick Reference

**Test Script**: `tests/mokubench_deployment_test.py`

**Run Example**:
```bash
uv run python tests/mokubench_deployment_test.py --ip 192.168.13.159
```

**What It Demonstrates**:
- Deploy CloudCompile (simple_counter) + Oscilloscope
- Route counter output to oscilloscope input  
- Capture 1024 samples of waveform data
- Verify data collection from real hardware

**Status**: ✅ Validated on Moku:Go hardware

**MokuBench Support**: Full framework support in `tests/bench_framework/hardware.py`
- Settings: `timebase`, `trigger` configuration
- Data collection: `get_data()` returns time/ch1/ch2 arrays
- Works with BenchConfig SlotConfig pattern

**Quick BenchConfig Example**:
```python
from bench_framework import BenchConfig, SlotConfig, Connection

config = MokuPlatformConfig(
    platform=MOKU_GO,
    slots={
        1: SlotConfig(instrument='Oscilloscope', settings={'timebase': (-5e-3, 5e-3)}),
        2: SlotConfig(instrument='CloudCompile', bitstream='my_module.tar.gz')
    },
    connections=[
        Connection(source='Slot2OutA', destination='Slot1InA')
    ]
)

backend = HardwareBackend.from_config(config, ip_address='192.168.13.159')
await backend.setup()
data = await backend.run(duration_ms=100)
```

---

## References
- **Python API Examples**: `mcc_py_api_examples/oscilloscope_*.py`
- **Routing Guide**: `docs/MCC_Routing_Guide.md`
- **EMFI-Seq Example**: `docs/EMFI_Seq_Operational_Diagram.md` (Slot 1 Oscilloscope setup)
