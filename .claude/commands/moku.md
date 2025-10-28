# Moku Instrument API Context

You are now working in the **Moku Python API/Hardware Deployment domain**.

---

## Files In Scope

**Python Tooling:**
- `tools/` - TUI apps, deployment scripts
- `models/` - YAML parsers, data models
- `scripts/` - Build and deployment automation

**Documentation:**
- `.serena/memories/instrument_*.md` - Moku instrument API references (AI-optimized)
- `docs/OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md` - Hardware validation workflows
- `DS1140_PD_app.yaml` - Application descriptor

**Examples:**
- `mcc_py_api_examples/` - Reference implementations (if available)

**Note:** Instrument docs in `.serena/memories/` are LLM-optimized markdown from volo_vhdl project.

---

## Files Out of Scope

**VHDL Development** (use `/vhdl` instead):
- `VHDL/` - Source files
- `tests/test_*_progressive.py` - CocotB tests

---

## Quick Reference

### Multi-Instrument Setup Pattern
```python
from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope

m = MultiInstrument('192.168.1.100', platform_id=2)
mcc = m.set_instrument(2, CloudCompile, bitstream="DS1140-PD.tar.gz")
osc = m.set_instrument(1, Oscilloscope)
```

### Routing Pattern (Monitor + Output)
```python
connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Trigger → Osc Ch1
    dict(source="Slot2OutB", destination="Slot1InB"),  # Intensity → Osc Ch2
    dict(source="Slot2OutC", destination="Output1"),   # FSM debug → Physical
]
m.set_connections(connections=connections)
```

### Control Register Protocol
```python
# DS1140-PD register map (Control0-Control15)
mcc.set_control(15, 0xE0000000)  # VOLO_READY bits [31:29]
mcc.set_control(0, 0x80000000)   # Arm probe (button)
mcc.set_control(4, 0x00FF0000)   # Arm timeout (16-bit)
mcc.set_control(8, 0x26660000)   # Intensity (16-bit, 2.0V)
```

---

## Key Instruments

### CloudCompile (Custom VHDL)
- Deploy DS1140-PD bitstream
- 16 control registers (Control0-Control15)
- 4 inputs, 4 outputs
- **Reference:** `.serena/memories/instrument_cloud_compile.md`

### Oscilloscope
- Monitor DS1140-PD outputs (OutputA/B/C)
- 2 channels displayed in GUI
- Trigger on FSM state transitions
- **Reference:** `.serena/memories/instrument_oscilloscope.md`

### Arbitrary Waveform Generator
- Generate custom trigger signals
- Test DS1140-PD threshold detection
- **Reference:** `.serena/memories/instrument_arbitrary_waveform_generator.md`

---

## DS1140-PD Deployment

### Standard Setup
```python
# Deploy DS1140-PD with oscilloscope monitoring
m = MultiInstrument('192.168.13.159', platform_id=2)
mcc = m.set_instrument(2, CloudCompile, bitstream="modules/DS1140-PD/latest/bitstream.tar.gz")
osc = m.set_instrument(1, Oscilloscope)

connections = [
    dict(source="Input1", destination="Slot2InA"),     # External trigger
    dict(source="Slot2OutA", destination="Output1"),   # Trigger output
    dict(source="Slot2OutB", destination="Output2"),   # Intensity output
    dict(source="Slot2OutC", destination="Slot1InA"),  # FSM debug → Osc
]
m.set_connections(connections=connections)

# Initialize VOLO_READY
mcc.set_control(15, 0xE0000000)  # volo_ready, user_enable, clk_enable
```

### Hardware Validation Workflow
1. Deploy bitstream with oscilloscope monitoring
2. Configure control registers (Control0-Control8)
3. Monitor OutputC (FSM state) on oscilloscope Ch1
4. Use voltage decoding from `OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md`
5. Poll for state transitions (10× 0.1s delays)

---

## Common Patterns

### Voltage Scaling (Critical!)
```python
# Moku platform: ±5V full scale (NOT ±1V!)
digital_value = int((voltage / 5.0) * 32768)
voltage = (digital_value / 32768.0) * 5.0
```

### FSM State Decoding
```python
# DS1140-PD FSM states (OutputC via fsm_observer)
STATE_MAP = {
    0.0: "READY",
    0.36: "ARMED",
    0.71: "FIRING",
    1.07: "COOLING",
    1.43: "DONE",
    1.79: "TIMEDOUT",
    -2.5: "HARDFAULT"  # Negative = fault (preserves context)
}
```

### Polling Pattern
```python
# Wait for state transition (handle oscilloscope latency)
for i in range(10):
    time.sleep(0.1)
    data = osc.get_data()
    voltage = data['ch1'][len(data['ch1']) // 2]
    state = decode_fsm_state(voltage)
    if state == expected_state:
        break
```

---

## Available Instrument References

Check `.serena/memories/instrument_*.md` for detailed API references:
- Oscilloscope
- Arbitrary Waveform Generator
- Cloud Compile
- Data Logger
- Digital Filter Box
- FIR Filter Builder
- Frequency Response Analyzer
- Laser Lock Box
- Lock-In Amplifier
- Logic Analyzer
- Neural Network
- Phasemeter
- PID Controller
- Spectrum Analyzer
- Time-Frequency Analyzer
- Waveform Generator

---

## Context Switching

**Working on VHDL?** → Type `/vhdl` to load VHDL development context
**Working on tests?** → Type `/test` to load testing infrastructure
**Working on Python?** → You're already here! (`/moku`)

---

Now working in Moku API context. Ready to deploy DS1140-PD to hardware!
