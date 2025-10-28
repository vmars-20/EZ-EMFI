# Riscure DS1120A - EMFI Probe (Unidirectional)

---
vendor: Riscure
model: DS1120A
category: emfi_probe
variant: unidirectional
power_type: high_voltage_external
moku_compatible: true
related_devices:
  - riscure_ds1121a
datasheet: docs/datasheets/DS1120A_DS1121A_datasheet.pdf
---

## Overview

Electromagnetic Fault Injection (EMFI) probe for hardware security testing. High-power unidirectional design optimized for testing hardened targets. All interfacing done through external control hardware (Moku-Go, Riscure Spider, etc.).

**Key Characteristics:**
- **Injection only** (no EM measurement capability)
- **Fixed 50ns pulse width** (not adjustable)
- **High power**: 450V, 64A capability
- **Fast response**: 40-50ns propagation delay
- **Simple 3-signal interface**: trigger, power control, current monitor

## Physical Connectors

### Top Panel (Left to Right)

| Position | Connector Type | Gender | Signal Name | Direction | Description |
|----------|---------------|--------|-------------|-----------|-------------|
| 1 | **Barrel Jack** | 2.1mm/2.5mm center-positive | `power_24vdc` | INPUT | 24VDC power supply (external PSU required) |
| 2 | **SMA** | Female | `coil_current` | OUTPUT | Current monitor output (to scope/Moku input) |
| 3 | **SMA** | Female | `digital_glitch` | INPUT | Trigger signal (from Moku output/pattern generator) |
| 4 | **SMA** | Female | `pulse_amplitude` | INPUT | Analog power control (from Moku DAC output) |

### Bottom

| Position | Connector Type | Description |
|----------|---------------|-------------|
| Bottom mount | **SMA threaded** | Interchangeable probe tip mounting (1.5mm, 4mm, crescent) |

### Connector Electrical Characteristics

| Connector | Impedance | Voltage Range | Notes |
|-----------|-----------|---------------|-------|
| `coil_current` (SMA) | 50Ω | -1.4V to 0V | Transient pulse, use AC coupling |
| `digital_glitch` (SMA) | 50Ω | 0-3.3V TTL | Rising edge triggered |
| `pulse_amplitude` (SMA) | 50Ω | 0-3.3V analog | Linear control 5-100% power |
| `power_24vdc` (Barrel) | N/A | 24V-450V DC | External high-voltage PSU required |

## Signal Interface

### Inputs (Driven by Moku/Controller)

| Signal Name | Connector | Voltage Range | Description | Moku Port Compatibility |
|-------------|-----------|---------------|-------------|-------------------------|
| `digital_glitch` | SMA Female | 0-3.3V TTL | Trigger pulse (rising edge) initiates EM glitch | OutputA, OutputB (TTL mode) |
| `pulse_amplitude` | SMA Female | 0-3.3V analog | Power level control (linear mapping) | DACOut1, DACOut2 |
| `power_24vdc` | Barrel Jack | 24-450V DC | High-voltage power supply | External PSU (not Moku) |

**Trigger Timing:**
- **Pulse width**: 50ns (fixed, hardware-determined)
- **Propagation delay** (trigger → coil current): ~50ns ±10%
- **Propagation delay** (trigger → EM tip): ~40ns ±10%
- **Min trigger pulse**: 10ns (will generate full 50ns EM pulse)

**Power Control:**
- **Range**: 5-100% (lower than 5% unreliable)
- **Scaling**: Linear voltage-to-power mapping (to be characterized)
- **Settling time**: <1µs after amplitude change

### Outputs (Read by Moku/Scope)

| Signal Name | Connector | Voltage Range | Description | Moku Port Compatibility |
|-------------|-----------|---------------|-------------|-------------------------|
| `coil_current` | SMA Female | -1.4V to 0V | Real-time coil current waveform (transient) | InputA, InputB (AC coupled, 50Ω term) |

**Current Monitor:**
- **Peak voltage**: -1.4V ±10% (4mm tip) / -1.2V ±10% (1.5mm tip)
- **Pulse width**: 17-20ns ±10%
- **Bandwidth**: >50 MHz (use scope/Moku with ≥100 MHz BW)
- **Coupling**: AC coupling recommended (transient pulse)
- **Termination**: 50Ω required

### Physical Outputs (Non-Electrical)

| Output | Description |
|--------|-------------|
| **EM probe tip** | Electromagnetic pulse delivered to target chip (physical proximity coupling, not measured electrically) |

## Electrical Specifications

| Parameter | Value | Tolerance | Notes |
|-----------|-------|-----------|-------|
| Max voltage over coil | 450V | ±10% | Internal voltage (not externally visible) |
| Max internal current | 64A | N/A | Internal to probe |
| Max coil current (4mm tip) | 56A | ±10% | Measured via `coil_current` monitor |
| Max coil current (1.5mm tip) | 48A | ±10% | Measured via `coil_current` monitor |
| EM pulse power control | 5-100% | N/A | Linear via `pulse_amplitude` |
| Pulse width (fixed) | 50ns | N/A | Not adjustable |
| Max pulse frequency | 1 MHz | N/A | For constant power operation |
| Working voltage | 24-450V DC | ±10% | External PSU required |
| Operating temperature | 0-70°C | N/A | Ambient temperature range |

## Probe Tips (Interchangeable)

All tips use SMA threaded mount:

| Tip Type | Diameter | Variants | Max Current | Use Case |
|----------|----------|----------|-------------|----------|
| Small | 1.5mm | Positive/Negative polarity | 48A ±10% | Precision targeting, de-capped chips |
| Large | 4mm | Positive/Negative polarity | 56A ±10% | Higher field strength, packaged chips |
| Crescent | N/A | Single variant | N/A | Specialized targeting |
| High Precision | Various | Multiple sizes | N/A | Ultra-fine positioning |

**Tip Selection Impact:**
- Larger tips → higher current → stronger EM field → less spatial precision
- Smaller tips → lower current → weaker field → better spatial precision
- Tip selection does NOT affect electrical interface (all use same SMA mount)

## Typical Wiring Diagram

```
[Moku OutputA] --SMA--> [digital_glitch] ---> [DS1120A] --probe tip--> [Target DUT]
                                                  ↑
[Moku DACOut1] --SMA--> [pulse_amplitude] -------┘
                                                  ↓
                        [coil_current] --SMA--> [Moku InputA]
                                                  ↑
[24V PSU] --barrel--> [power_24vdc] -------------┘
```

## Signal Flow (for Diagram Generation)

**Inputs:**
- `digital_glitch`: External trigger → DS1120A
- `pulse_amplitude`: External DAC → DS1120A
- `power_24vdc`: External PSU → DS1120A

**Outputs:**
- `coil_current`: DS1120A → External scope/ADC
- `em_field`: DS1120A probe tip → Target DUT (physical proximity, non-electrical)

**Example BenchConfig Routing:**
```python
ExternalHardware(
    device_type='riscure_ds1120a',
    connections=[
        {'probe': 'digital_glitch', 'moku': 'OutputA'},
        {'probe': 'pulse_amplitude', 'moku': 'DACOut1'},
        {'probe': 'coil_current', 'moku': 'InputA'}
    ],
    settings={
        'probe_tip': '4mm_positive',
        'external_psu_voltage': 24  # Document only
    }
)
```

## Comparison to DS1121A

See [[riscure_ds1121a]] for bidirectional variant with:
- **Simultaneous EM measurement** (sense target emissions while injecting)
- **Adjustable pulse width** (4-200ns vs fixed 50ns)
- **Higher pulse frequency** (50 MHz vs 1 MHz)
- **Lower power** (100V vs 450V - less capable for hardened targets)
- **Additional output**: `em_sense` connector

**When to use DS1120A:**
- ✓ Hardened targets requiring high power
- ✓ Simpler setup (fewer connections)
- ✓ Don't need EM sensing during attack
- ✓ Fixed pulse width sufficient

**When to use DS1121A:**
- ✓ Need EM-based triggering
- ✓ Want to measure target emissions
- ✓ Need adjustable pulse width
- ✓ Higher frequency operation
- ✓ Sensitive targets (lower power safer)

## Moku-Go Integration Notes

**Moku Output Ports** (driving probe):
- **OutputA/B** (TTL mode): Connect to `digital_glitch`
  - Configure as digital output, TTL levels (0/3.3V)
  - Generate trigger pulse (≥10ns width, probe extends to 50ns)

- **DACOut1/2**: Connect to `pulse_amplitude`
  - Configure as DC-coupled, 0-3.3V range
  - Value controls power percentage (characterization needed)

**Moku Input Ports** (reading probe):
- **InputA/B**: Connect to `coil_current`
  - Configure as AC-coupled, 50Ω termination, ±5V range
  - Sample rate ≥250 MSa/s recommended (5ns/sample for 50ns pulse)
  - Use oscilloscope or data logger instrument

**Example Moku Configuration:**
```python
# Trigger output (OutputA)
moku.set_digital_output('A', ttl_mode=True)

# Power control (DACOut1)
power_percent = 75  # 75% power
dac_voltage = (power_percent / 100.0) * 3.3  # Linear (to be characterized)
moku.set_dac_output(1, dac_voltage)

# Current monitor (InputA)
moku.configure_input('A', coupling='AC', impedance='50ohm', range='5V')
```

## Safety and Handling

- ⚠️ **High voltage**: External PSU can deliver 24-450V DC
- ⚠️ **Permanent damage risk**: Can destroy unprotected chips
- ⚠️ **ESD sensitive**: Use grounded wrist strap when handling
- ✓ Always verify power level before first trigger
- ✓ Test on sacrificial DUT first
- ✓ Use appropriate probe tip for target (larger = safer for chip)

## External Requirements

**Not Included:**
- **High-voltage PSU**: 24-450V DC, center-positive barrel connector
- **Coaxial cables**: 3× SMA male-to-male, 50Ω (suggest <1m length)
- **XYZ positioning stage**: Optional but highly recommended (Keysight DS1010A compatible)

## References

- **Datasheet**: `docs/datasheets/DS1120A_DS1121A_datasheet.pdf`
- **Related device**: [[riscure_ds1121a]] (bidirectional variant)
- **Usage examples**: TBD (to be added when tests written)
- **Moku integration**: See [[bench_config_framework]] for BenchConfig usage
