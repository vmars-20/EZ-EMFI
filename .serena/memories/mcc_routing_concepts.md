# MCC Routing Concepts for VHDL Developers

## Core Principle
**MCC routing** is the external configuration layer that connects:
- Physical I/O (BNC connectors) ↔ Slot virtual I/O (CustomWrapper ports)
- Slot outputs ↔ Slot inputs (cross-slot routing)

**VHDL modules** always see the same CustomWrapper interface regardless of routing.

## CustomWrapper Virtual I/O

Every slot has **identical virtual I/O**:
- 4 inputs: InputA, InputB, InputC, InputD (signed 16-bit)
- 4 outputs: OutputA, OutputB, OutputC, OutputD (signed 16-bit)
- 32 control registers: Control0-31 (std_logic_vector 32-bit)

## Python Routing API Syntax

```python
from moku.instruments import MultiInstrument, CloudCompile

m = MultiInstrument('192.168.1.100', platform_id=2)
mcc = m.set_instrument(1, CloudCompile, bitstream="path/to/bitstream.tar.gz")

connections = [
    dict(source="Input1", destination="Slot1InA"),       # Physical IN1 → InputA
    dict(source="Slot1OutA", destination="Output1"),     # OutputA → Physical OUT1
    dict(source="Slot1OutB", destination="Slot2InA"),    # Cross-slot routing
]

m.set_connections(connections=connections)

# Set control registers
mcc.set_control(0, 0x40000001)  # Control0 (includes MCC_READY bit)
mcc.set_control(1, 0x0000007F)  # Control1
```

## Connection Naming Convention

| Python API Name | Maps to VHDL Port | Description |
|-----------------|-------------------|-------------|
| `"Input1"`, `"Input2"` | N/A (physical ADC) | BNC input connectors |
| `"Output1"`, `"Output2"` | N/A (physical DAC) | BNC output connectors |
| `"Slot1InA"` | `InputA` (Slot 1) | CustomWrapper input port |
| `"Slot1InB"` | `InputB` (Slot 1) | CustomWrapper input port |
| `"Slot1InC"` | `InputC` (Slot 1) | CustomWrapper input port |
| `"Slot1InD"` | `InputD` (Slot 1) | CustomWrapper input port |
| `"Slot1OutA"` | `OutputA` (Slot 1) | CustomWrapper output port |
| `"Slot1OutB"` | `OutputB` (Slot 1) | CustomWrapper output port |
| `"Slot1OutC"` | `OutputC` (Slot 1) | CustomWrapper output port |
| `"Slot1OutD"` | `OutputD` (Slot 1) | CustomWrapper output port |
| `"Slot2InA"` | `InputA` (Slot 2) | CustomWrapper input (different slot) |
| (etc.) | | |

## Routing Rules

### Allowed:
- ✅ Physical Input → Slot Input(s) (fan-out allowed)
- ✅ Slot Output → Physical Output(s) (fan-out allowed)
- ✅ Slot Output → Other Slot Input(s) (cross-slot routing)
- ✅ One source → multiple destinations (fan-out)

### Forbidden:
- ❌ Slot Input → Anything (inputs are destinations only)
- ❌ Physical Output → Anything (outputs are destinations only)
- ❌ Slot Output → Same Slot Input (no internal loopback)

## Common Routing Patterns

### Pattern 1: Simple Physical I/O
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),
    dict(source="Slot1OutA", destination="Output1"),
]
```
**Use**: Basic external signal processing

### Pattern 2: Dual-Slot Monitoring
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),       # Oscilloscope monitors external
    dict(source="Slot2OutA", destination="Slot1InB"),    # Oscilloscope monitors your output
    dict(source="Slot2OutA", destination="Output1"),     # Your output to physical
]
```
**Use**: Slot 1 = Oscilloscope, Slot 2 = Your module (typical development setup)

### Pattern 3: Cross-Slot Pipeline
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),
    dict(source="Slot1OutA", destination="Slot2InA"),    # Chain slots together
    dict(source="Slot2OutA", destination="Output1"),
]
```
**Use**: Multi-stage processing (Slot 1 → Slot 2 → Output)

### Pattern 4: Fan-Out (One ADC → Multiple Slots)
```python
connections = [
    dict(source="Input1", destination="Slot1InA"),       # Same ADC to both slots
    dict(source="Input1", destination="Slot2InA"),
]
```
**Use**: Parallel processing of same input signal

## VHDL Design Implications

### 1. Always Drive All Outputs
```vhdl
-- ✅ GOOD
OutputA <= my_signal;
OutputB <= (others => '0');  -- Explicit safe value
OutputC <= (others => '0');
OutputD <= (others => '0');

-- ❌ BAD (unused outputs left floating)
OutputA <= my_signal;
-- (OutputB/C/D not driven)
```

### 2. Don't Assume Physical I/O Mapping
```vhdl
-- ✅ GOOD: Generic logic, routing-agnostic
if InputA /= 0 then
    trigger <= '1';
end if;

-- ❌ BAD: Hardcoded assumption about physical I/O
-- comment: "InputA is connected to external trigger on BNC IN1"
```

Routing is **configured externally** via Python. Your VHDL should work regardless of routing.

### 3. Use All 4 Inputs/Outputs When Appropriate
Even if target platform has only 2 physical ADCs, use all 4 virtual inputs if your design benefits:

```vhdl
-- Cross-slot routing might send signals to InputC/D
signal_sum <= InputA + InputB + InputC + InputD;
```

MCC routing determines which inputs get real signals (others will be 0).

### 4. No Routing Simulation Needed in Testbenches
CocotB tests drive CustomWrapper ports **directly**:

```python
@cocotb.test()
async def test_my_module(dut):
    dut.InputA.value = 0x1234  # Drive virtual input directly
    await ClockCycles(dut.Clk, 10)
    assert dut.OutputA.value == expected_value  # Monitor virtual output
```

**MCC routing is NOT simulated in tests.** Tests verify VHDL logic correctness only.

## Control Registers

### Python API
```python
mcc.set_control(register_num, value)  # Sets ControlN in VHDL
```

### VHDL Access
```vhdl
architecture MyModule of CustomWrapper is
    signal mcc_ready : std_logic;
    signal user_enable : std_logic;
    signal param1 : unsigned(31 downto 0);
begin
    -- Extract fields from Control0
    mcc_ready <= Control0(31);      -- MCC_READY (auto-set by MCC)
    user_enable <= Control0(30);    -- User enable flag
    
    -- Use other control registers
    param1 <= unsigned(Control1);   -- User-defined parameter
end architecture;
```

### Reserved Bits
- **Control0[31]**: MCC_READY (set automatically by MCC after bitstream load and config)
- **Control0[30]**: Typically used for user global enable
- **Control1-31**: Fully user-defined

## Platform-Specific Constraints

| Platform | Slots | Physical ADC/DAC | Virtual I/O per Slot | Notes |
|----------|-------|------------------|----------------------|-------|
| **Moku:Go** | 2 | 2 ADC / 2 DAC | 4 in / 4 out | Cross-slot routing essential |
| **Moku:Lab** | 2 | 2 ADC / 2 DAC | 4 in / 4 out | Same as Go, higher perf |
| **Moku:Pro** | 4 | 4 ADC / 4 DAC | 4 in / 4 out | Perfect 1:1 mapping possible |
| **Moku:Delta** | 8 | 8 ADC / 8 DAC | 4 in / 4 out | 32 virtual I/O total |

**Key**: Platforms with fewer physical I/O than virtual I/O rely heavily on **cross-slot routing** for multi-instrument setups.

## Debugging Routing Issues

### If module works in CocotB but fails on hardware:

1. **Check Python routing configuration**:
   ```python
   print("Current connections:", m.get_connections())
   ```

2. **Common mistakes**:
   - Forgot to route physical input to slot input
   - Typo in connection name (`"Slot1InA"` vs `"Slot1lnA"`)
   - Routed output to wrong physical port
   - Missing fan-out connection (wanted signal on DAC + other slot)

3. **Verify control registers**:
   ```python
   print("Control0:", mcc.get_control(0))  # Check MCC_READY bit
   ```

## Example: EMFI-Seq Deployment

**Setup**: Oscilloscope (Slot 1) monitors EMFI-Seq (Slot 2)

```python
m = MultiInstrument('192.168.1.100', platform_id=2)
osc = m.set_instrument(1, Oscilloscope)
mcc = m.set_instrument(2, CloudCompile, bitstream="emfi_seq.tar.gz")

connections = [
    # EMFI output → Oscilloscope Ch1 (monitoring)
    dict(source="Slot2OutA", destination="Slot1InA"),
    
    # EMFI status → Oscilloscope Ch2 (monitoring)
    dict(source="Slot2OutB", destination="Slot1InB"),
    
    # EMFI pulse → Physical output (to target device)
    dict(source="Slot2OutA", destination="Output1"),
]

m.set_connections(connections=connections)

# Configure EMFI-Seq
mcc.set_control(0, 0xC0000001)  # MCC_READY + Enable
mcc.set_control(1, 0x000000FF)  # DelayS1 parameter
```

**Result**:
- EMFI-Seq OutputA goes to **both** Oscilloscope (real-time monitoring) **and** Physical OUT1 (target)
- Fan-out routing allows simultaneous observation and deployment

## Summary for VHDL Developers

### You Control:
- VHDL logic inside CustomWrapper architecture
- Control register definitions (Control0-31)
- Virtual I/O behavior (InputA/B/C/D → OutputA/B/C/D logic)

### MCC Controls:
- Physical I/O → Virtual I/O mapping
- Cross-slot signal routing
- Control register values (set via Python)

### Golden Rule:
**Design your VHDL to the CustomWrapper standard (4 in, 4 out, 32 regs). Let MCC routing handle all external connections.**

## References
- **Full Guide**: `docs/MCC_Routing_Guide.md`
- **Platform Models**: `docs/PLATFORM_MODELS.md`
- **Python Examples**: `mcc_py_api_examples/`
- **EMFI-Seq Operational Diagram**: `docs/EMFI_Seq_Operational_Diagram.md`
