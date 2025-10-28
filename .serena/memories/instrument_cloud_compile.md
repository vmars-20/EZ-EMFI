# Moku Instrument: Cloud Compile (Custom VHDL/Verilog)

## Purpose
**Deploy custom FPGA designs (VHDL/Verilog) to Moku hardware.** This is THE instrument for running your CustomWrapper modules. Unlike built-in instruments, Cloud Compile lets you implement arbitrary digital logic on the FPGA.

---

## Key Python API

### Initialization (Multi-Instrument Mode)
```python
from moku.instruments import MultiInstrument, CloudCompile

m = MultiInstrument('192.168.1.100', platform_id=2)
mcc = m.set_instrument(1, CloudCompile, bitstream="path/to/bitstream.tar.gz")
```

**Required**: Bitstream file (`.tar.gz`) from Moku Cloud Compile service
- Upload your VHDL project to Moku Cloud Compile
- MCC synthesizes with Vivado
- Download resulting bitstream
- Deploy via Python API

### Configuration Methods

**Set Control Registers**:
```python
mcc.set_control(register_num, value)
# Example: mcc.set_control(0, 0xC0000001)  # Control0 (MCC_READY + Enable)
# Example: mcc.set_control(1, 0x000000FF)  # Control1 (custom parameter)
```

**Get Control Register** (read back):
```python
value = mcc.get_control(register_num)
# Example: val = mcc.get_control(0)  # Read Control0 (check MCC_READY bit)
```

---

## Routing Patterns

### Pattern 1: Custom Module to Physical I/O
```python
mcc = m.set_instrument(1, CloudCompile, bitstream="my_module.tar.gz")

connections = [
    dict(source="Input1", destination="Slot1InA"),   # Physical IN1 → Module InputA
    dict(source="Slot1OutA", destination="Output1"), # Module OutputA → Physical OUT1
]
m.set_connections(connections=connections)

# Configure module via control registers
mcc.set_control(0, 0xC0000001)  # MCC_READY + Enable
mcc.set_control(1, 0x12345678)  # Custom parameter
```

**VHDL (Your Module)**:
```vhdl
architecture MyModule of CustomWrapper is
    signal mcc_ready : std_logic;
    signal enable : std_logic;
    signal param : unsigned(31 downto 0);
begin
    mcc_ready <= Control0(31);
    enable <= Control0(30);
    param <= unsigned(Control1);

    -- Your logic using InputA → OutputA
    process(Clk)
    begin
        if rising_edge(Clk) then
            if mcc_ready = '1' and enable = '1' then
                OutputA <= process_signal(InputA, param);
            end if;
        end if;
    end process;
end architecture;
```

---

### Pattern 2: Dual-Slot with Monitoring (Oscilloscope + Custom Module)
```python
osc = m.set_instrument(1, Oscilloscope)
mcc = m.set_instrument(2, CloudCompile, bitstream="emfi_seq.tar.gz")

connections = [
    dict(source="Slot2OutA", destination="Slot1InA"),  # Module → Osc Ch1 (monitor)
    dict(source="Slot2OutB", destination="Slot1InB"),  # Module status → Osc Ch2
    dict(source="Slot2OutA", destination="Output1"),   # Module → Physical OUT1
]
m.set_connections(connections=connections)

# Configure custom module
mcc.set_control(0, 0xC0000001)  # Enable
mcc.set_control(1, 0x000000FF)  # DelayS1 parameter

# Monitor outputs on oscilloscope
osc.set_timebase(-10e-6, 10e-6)
osc.set_trigger(type="Edge", source="ChannelA", level=0.5)
data = osc.get_data()
```

**This is your EMFI-Seq setup!**

---

### Pattern 3: Cross-Slot Processing Pipeline (Two Custom Modules)
```python
preprocessor = m.set_instrument(1, CloudCompile, bitstream="preprocessor.tar.gz")
postprocessor = m.set_instrument(2, CloudCompile, bitstream="postprocessor.tar.gz")

connections = [
    dict(source="Input1", destination="Slot1InA"),    # Physical input → Preprocessor
    dict(source="Slot1OutA", destination="Slot2InA"), # Preprocessor → Postprocessor
    dict(source="Slot2OutA", destination="Output1"),  # Postprocessor → Physical output
]
m.set_connections(connections=connections)

# Configure both modules
preprocessor.set_control(0, 0xC0000001)
preprocessor.set_control(1, 0x00000010)  # Preprocessor params

postprocessor.set_control(0, 0xC0000001)
postprocessor.set_control(2, 0x00000020)  # Postprocessor params
```

---

## Multi-Instrument Scenarios

### Scenario 1: WaveformGen + CloudCompile + Oscilloscope (Full Test Setup)
```python
wg = m.set_instrument(1, WaveformGenerator)
mcc = m.set_instrument(2, CloudCompile, bitstream="my_filter.tar.gz")
osc = m.set_instrument(3, Oscilloscope)  # Requires 4-slot platform

connections = [
    dict(source="Slot1OutA", destination="Slot2InA"),  # Stimulus → Module
    dict(source="Slot2OutA", destination="Slot3InA"),  # Module output → Osc Ch1
    dict(source="Slot1OutA", destination="Slot3InB"),  # Original stimulus → Osc Ch2
]
m.set_connections(connections=connections)

# Generate test signal
wg.generate_waveform(1, "Sine", amplitude=1.0, frequency=1e3)

# Monitor input vs output
osc.set_timebase(-2e-3, 2e-3)
data = osc.get_data()
# Compare data['ch1'] (filtered) vs data['ch2'] (original)
```

---

### Scenario 2: CloudCompile + Data Logger (Long-Term Recording)
```python
mcc = m.set_instrument(2, CloudCompile, bitstream="sensor_processor.tar.gz")
dl = m.set_instrument(1, Datalogger)

connections = [
    dict(source="Input1", destination="Slot2InA"),    # Sensor → Module
    dict(source="Slot2OutA", destination="Slot1InA"), # Processed data → Logger
]
m.set_connections(connections=connections)

# Configure module
mcc.set_control(0, 0xC0000001)

# Record 1 hour of processed data
dl.start_logging(duration=3600)
```

---

## Control Register Convention

### Standard Mapping (Recommended)
- **Control0[31]**: MCC_READY (auto-set by MCC after bitstream load)
- **Control0[30]**: User global enable
- **Control0[29:0]**: Module-specific configuration
- **Control1-31**: User-defined parameters

**Why Control0[31]?**
During FPGA bitstream load, all control registers start at `0x00000000`. Network delay (10-200ms) occurs before configuration arrives. Using Control0[31] as MCC_READY ensures module stays disabled during all-zero state, preventing glitches.

**Python**:
```python
mcc.set_control(0, 0xC0000001)  # Bit 31=1 (MCC_READY), Bit 30=1 (Enable), Bit 0=1 (custom)
```

**VHDL**:
```vhdl
signal mcc_ready : std_logic;
signal user_enable : std_logic;
signal global_enable : std_logic;
begin
    mcc_ready <= Control0(31);
    user_enable <= Control0(30);
    global_enable <= mcc_ready and user_enable;  -- Safe enable logic
```

---

## Development Workflow

### 1. Local VHDL Development
```bash
# Write VHDL modules
cd modules/my_module/

# Test with CocotB
cd tests/
make TEST_MODULE=my_module  # Run local simulations
```

### 2. Upload to Moku Cloud Compile
- Package VHDL project
- Upload to Moku Cloud Compile web interface
- MCC synthesizes with Vivado (generates bitstream.tar.gz)
- Download bitstream

### 3. Deploy to Hardware
```python
m = MultiInstrument('192.168.1.100', platform_id=2)
mcc = m.set_instrument(1, CloudCompile, bitstream="path/to/bitstream.tar.gz")

# Configure routing
connections = [...]
m.set_connections(connections=connections)

# Set control registers
mcc.set_control(0, 0xC0000001)
```

### 4. Iterate
- Observe behavior (Oscilloscope, Data Logger, etc.)
- Modify VHDL
- Re-test locally with CocotB
- Re-upload to MCC for synthesis
- Re-deploy

---

## Relationship to CustomWrapper

**Cloud Compile IS CustomWrapper deployment.**

Every custom VHDL/Verilog design deployed via Cloud Compile **must** implement the CustomWrapper entity:

```vhdl
architecture MyModule of CustomWrapper is
    -- Your logic here
end architecture;
```

The CustomWrapper interface (4 inputs, 4 outputs, 32 control registers) is the **contract** between your VHDL and the Moku platform.

---

## References
- **Python API Examples**: `mcc_py_api_examples/cloud_compile_*.py`
- **CustomWrapper Template**: `mcc_templates/mcc-Top.vhd`
- **MCC Routing Guide**: `docs/MCC_Routing_Guide.md`
- **EMFI-Seq Example**: `docs/EMFI_Seq_Operational_Diagram.md` (real deployment)
- **Platform Models**: `docs/PLATFORM_MODELS.md`
