# Time & Frequency Analyzer - Instrument API Reference

## Purpose
Precision **interval timing and frequency stability analysis** for digital signals. Measures event intervals, calculates Allan deviation, and characterizes clock jitter for oscillator and timing system validation.

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
            instrument='TimeFrequencyAnalyzer',
            settings={
                'event_detector': {
                    'event_id': 1,
                    'source': 'Input1',
                    'threshold': 0,
                    'edge': 'Rising'
                },
                'interval_analyzer': {
                    'interval_id': 1,
                    'start_event_id': 1,
                    'stop_event_id': 1
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
from moku.instruments import TimeFrequencyAnalyzer
i = TimeFrequencyAnalyzer('192.168.1.100', force_connect=True)
```

### Event Detector Configuration
```python
# Define events to measure (up to 2 event types: A and B)
i.set_event_detector(
    event_id=1,                # Event A (1) or Event B (2)
    source='Input1',           # 'Input1' or 'Input2'
    threshold=0,               # Trigger threshold (V)
    edge='Rising'              # 'Rising' or 'Falling'
)

i.set_event_detector(
    event_id=2,                # Event B
    source='Input2',
    threshold=0,
    edge='Rising'
)
```

### Interpolation Mode
```python
# Set timing interpolation algorithm
i.set_interpolation(mode='Linear')  # 'Linear' or 'Sinc'
# Linear: Faster, less accurate
# Sinc: Slower, higher precision
```

### Acquisition Mode
```python
# Set measurement window
i.set_acquisition_mode(
    mode='Windowed',           # 'Windowed' or 'Continuous'
    window_length=100e-3       # Window duration in seconds (for Windowed mode)
)

# Continuous mode: Stream data indefinitely
i.set_acquisition_mode(mode='Continuous')
```

### Interval Analyzer Configuration
```python
# Define intervals to measure
i.set_interval_analyzer(
    interval_id=1,             # Interval A (1) or Interval B (2)
    start_event_id=1,          # Start at Event A (1) or Event B (2)
    stop_event_id=1            # Stop at Event A (1) or Event B (2)
)

# Example: Interval A = Event A to Event A (period of signal on Input1)
i.set_interval_analyzer(1, start_event_id=1, stop_event_id=1)

# Example: Interval B = Event A to Event B (delay between Input1 and Input2)
i.set_interval_analyzer(2, start_event_id=1, stop_event_id=2)
```

### Data Retrieval with Statistics
```python
# Get interval measurements and statistics
data = i.get_data()

# Interval 1 statistics
print(data['interval1']['statistics'])
# Contains: mean, stddev, min, max, count, allan_deviation, etc.

# Interval 2 statistics
print(data['interval2']['statistics'])

# Access specific statistics
mean_period = data['interval1']['statistics']['mean']
stddev = data['interval1']['statistics']['stddev']
allan_dev = data['interval1']['statistics']['allan_deviation']
```

## Routing Patterns

### Pattern 1: Clock Period Measurement
```python
# Measure period and jitter of a clock signal
tfa = m.set_instrument(1, TimeFrequencyAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),  # Clock signal
]
m.set_connections(connections=connections)

# Configure for period measurement
tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')
tfa.set_interpolation(mode='Sinc')  # High precision
tfa.set_acquisition_mode(mode='Windowed', window_length=100e-3)
tfa.set_interval_analyzer(1, start_event_id=1, stop_event_id=1)  # Event A to Event A = period

data = tfa.get_data()
clock_period = data['interval1']['statistics']['mean']
clock_jitter = data['interval1']['statistics']['stddev']
```

### Pattern 2: Propagation Delay Measurement
```python
# Measure delay between input and output of a system
tfa = m.set_instrument(1, TimeFrequencyAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),  # System input trigger
    dict(source="Input2", destination="Slot1InB"),  # System output trigger
]
m.set_connections(connections=connections)

tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')  # Input trigger
tfa.set_event_detector(2, source='Input2', threshold=0, edge='Rising')  # Output trigger
tfa.set_interval_analyzer(1, start_event_id=1, stop_event_id=2)  # Event A → Event B = delay

data = tfa.get_data()
propagation_delay = data['interval1']['statistics']['mean']
```

### Pattern 3: Custom Module Timing Validation
```python
# Measure timing characteristics of custom VHDL module
mcc = m.set_instrument(1, CloudCompile, bitstream="clock_divider.tar.gz")
tfa = m.set_instrument(2, TimeFrequencyAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Reference clock → Custom module
    dict(source="Slot1OutA", destination="Slot2InA"),  # Divided clock → TFA Event A
    dict(source="Input1", destination="Slot2InB"),     # Reference clock → TFA Event B
]
m.set_connections(connections=connections)

# Measure divided clock period
tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')
tfa.set_interval_analyzer(1, start_event_id=1, stop_event_id=1)

data = tfa.get_data()
divided_period = data['interval1']['statistics']['mean']
```

## Multi-Instrument Scenarios

### Waveform Generator + TFA (Clock Stability Test)
```python
# Generate clock and measure its stability
wg = m.set_instrument(1, WaveformGenerator)
tfa = m.set_instrument(2, TimeFrequencyAnalyzer)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # WaveformGen → TFA
]
m.set_connections(connections=connections)

wg.generate_waveform(1, type='Square', frequency=10e6, amplitude=1.0)
tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')
tfa.set_interval_analyzer(1, start_event_id=1, stop_event_id=1)

data = tfa.get_data()
allan_deviation = data['interval1']['statistics']['allan_deviation']
```

### Custom Module + TFA (Timing Verification)
```python
# Validate custom VHDL timing generator
mcc = m.set_instrument(1, CloudCompile, bitstream="pulse_generator.tar.gz")
tfa = m.set_instrument(2, TimeFrequencyAnalyzer)

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Custom pulse train → TFA
]
m.set_connections(connections=connections)

tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')
tfa.set_interval_analyzer(1, start_event_id=1, stop_event_id=1)

# Verify pulse period matches design spec
data = tfa.get_data()
measured_period = data['interval1']['statistics']['mean']
expected_period = 1e-6  # 1 µs
assert abs(measured_period - expected_period) < 1e-9  # Within 1 ns tolerance
```

## VHDL Integration

### Clock Divider Validation
```python
# Test custom clock divider with Time & Frequency Analyzer
mcc = m.set_instrument(1, CloudCompile, bitstream="configurable_divider.tar.gz")
tfa = m.set_instrument(2, TimeFrequencyAnalyzer)

connections = [
    dict(source="Input1", destination="Slot1InA"),     # Reference clock
    dict(source="Slot1OutA", destination="Slot2InA"),  # Divided clock
    dict(source="Slot1OutA", destination="Output1"),   # Monitor output
]
m.set_connections(connections=connections)
```

**VHDL CustomWrapper Example:**
```vhdl
-- Example: Configurable clock divider
architecture ClockDivider of CustomWrapper is
    signal div_ratio : unsigned(15 downto 0);
begin
    div_ratio <= unsigned(Control0(15 downto 0));
    
    process(Clk)
        variable counter : unsigned(15 downto 0) := (others => '0');
    begin
        if rising_edge(Clk) then
            if counter >= div_ratio - 1 then
                counter := (others => '0');
                OutputA <= not OutputA;  -- Toggle output (→ TFA measures period)
            else
                counter := counter + 1;
            end if;
        end if;
    end process;
end architecture;
```

## CocotB Test Comparison

**Local VHDL Test (CocotB):**
```python
# Test clock divider timing locally
dut.Control0.value = 0x00000008  # Divide by 8
await RisingEdge(dut.Clk)
# Count cycles, verify toggle period
```

**Hardware Validation (TFA):**
```python
# Deploy and measure actual period with ps-level precision
tfa.set_event_detector(1, source='Input1', threshold=0, edge='Rising')
tfa.set_interpolation(mode='Sinc')  # High precision
data = tfa.get_data()
measured_period = data['interval1']['statistics']['mean']
# Verify against expected period with high accuracy
```

## Common Use Cases

1. **Clock Jitter Measurement**: Quantify oscillator stability (stddev of period)
2. **Allan Deviation Analysis**: Long-term frequency stability characterization
3. **Propagation Delay**: Measure signal delay through systems
4. **Phase Noise**: Characterize timing noise in PLLs and oscillators
5. **VHDL Timing Validation**: Verify custom timing generators and dividers

## Key Statistics Provided

- **Mean**: Average interval duration
- **Stddev**: Jitter (period-to-period variation)
- **Min/Max**: Timing bounds
- **Allan Deviation**: Frequency stability metric
- **Count**: Number of intervals measured

## Related Instruments
- **Phasemeter**: Phase measurement (related to timing)
- **WaveformGenerator**: Generate test clocks
- **Oscilloscope**: Time-domain waveform visualization
- **CloudCompile**: Custom timing modules to be characterized
