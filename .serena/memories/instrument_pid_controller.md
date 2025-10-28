# Moku Instrument: PID Controller

## Purpose
Closed-loop control for stabilization and regulation. Implements proportional-integral-derivative (PID) feedback control. Useful for **locking custom module outputs**, temperature/frequency stabilization, or implementing feedback systems.

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
            instrument='PIDController',
            settings={
                'pid': {
                    'channel': 1,
                    'kp': 1.0,
                    'ki': 0.1,
                    'kd': 0.01,
                    'crossover_freq': 1e3
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
from moku.instruments import MultiInstrument, PIDController

m = MultiInstrument('192.168.1.100', platform_id=2)
pid = m.set_instrument(1, PIDController)
```

### Configuration Methods

**Set PID Gains** (Frequency Response Method):
```python
pid.set_by_frequency(channel, kp, ki, kd, crossover_freq, **kwargs)
# Example: pid.set_by_frequency(1, kp=1.0, ki=0.1, kd=0.01, crossover_freq=1e3)
```

**Set PID Gains** (Direct Gain Method):
```python
pid.set_by_gain(channel, overall_gain, prop_gain, int_gain, diff_gain)
# Example: pid.set_by_gain(1, overall_gain=10, prop_gain=1.0, int_gain=0.5, diff_gain=0.1)
```

**Set Input Matrix** (differential inputs, etc.):
```python
pid.set_input_matrix(channel, input1_gain, input2_gain)
# Example: pid.set_input_matrix(1, input1_gain=1.0, input2_gain=-1.0)  # Differential
```

**Enable/Disable**:
```python
pid.enable_channel(channel, enable=True)
```

### Data Acquisition

**Monitor Output**:
```python
data = pid.get_data()
# Returns dict with control output values
```

---

## Routing Patterns

### Pattern 1: Lock External Signal to Setpoint
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),   # Sensor/measurement → PID input
    dict(source="Slot1OutA", destination="Output1"), # PID output → Actuator
]
m.set_connections(connections=connections)

# Configure PID for stabilization
pid.set_by_frequency(1, kp=1.0, ki=0.1, kd=0.01, crossover_freq=1e3)
pid.enable_channel(1, enable=True)
```

### Pattern 2: Lock Custom Module Output
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="oscillator.tar.gz")
pid = m.set_instrument(1, PIDController)

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module output → PID (error signal)
    dict(source="Slot1OutA", destination="Slot2InB"),  # PID output → Module control input
]
m.set_connections(connections=connections)

# Implement feedback loop
pid.set_by_frequency(1, kp=10.0, ki=1.0, kd=0.0, crossover_freq=100)
```

---

## Multi-Instrument Scenarios

### Scenario: Phase-Locked Loop (PID + Lock-in Amplifier)
```python
lia = m.set_instrument(2, LockInAmp)
pid = m.set_instrument(1, PIDController)

connections = [
    dict(source="Input1", destination="Slot2InA"),    # External signal → Lock-in
    dict(source="Slot2OutA", destination="Slot1InA"), # Phase error → PID
    dict(source="Slot1OutA", destination="Output1"),  # PID control → VCO
]
m.set_connections(connections=connections)

# Lock to phase
lia.set_monitor(1, "theta")  # Output phase error
pid.set_by_frequency(1, kp=5.0, ki=0.5, kd=0.0, crossover_freq=10)
```

---

## References
- **Examples**: `mcc_py_api_examples/pidcontroller_*.py`
