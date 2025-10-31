# Moku Deployment Agent

**Purpose:** Deploy instruments to Moku hardware, configure routing, discover devices

---

## Quick Start

### In Claude Code

```
@moku-deploy Deploy DS1140-PD with oscilloscope monitoring
@moku-deploy Discover Moku devices on network
@moku-deploy Configure routing for cross-slot connections
```

### In Cursor / Other IDEs

1. Copy contents of `agent.md`
2. Paste into chat context
3. Ask: "Deploy DS1140-PD with oscilloscope monitoring"

---

## Common Use Cases

### Deploying Instruments

```
@moku-deploy Deploy DS1140-PD bitstream to 192.168.1.100
@moku-deploy Set up multi-instrument with CloudCompile + Oscilloscope
@moku-deploy Configure oscilloscope for FSM state monitoring
```

### Device Discovery

```
@moku-deploy Find all Moku devices on network
@moku-deploy Look up IP address for device "Lilo"
@moku-deploy Update device cache
```

### Routing Configuration

```
@moku-deploy Set up routing: Input1 → Slot2, Slot2OutA → Output1
@moku-deploy Configure cross-slot connection from Slot1 to Slot2
@moku-deploy Route FSM debug output to oscilloscope
```

### Hardware Validation

```
@moku-deploy Read FSM state from oscilloscope Ch1
@moku-deploy Poll oscilloscope until DONE state reached
@moku-deploy Validate DS1140-PD deployment
```

---

## What This Agent Can Do

✅ **Read:**
- Deployment scripts (`tools/**/*.py`)
- Instrument API docs (`.serena/memories/instrument_*.md`)
- Routing concepts, platform specs

✅ **Execute:**
- Run deployment scripts
- Device discovery commands
- Hardware validation workflows

✅ **Edit:**
- Deployment configuration files (JSON, YAML)
- Generated moku-models configs

---

## What This Agent Cannot Do

❌ **Write new Python deployment scripts** → Use `@python-dev` agent
❌ **Modify tests** → Use `@test-runner` agent
❌ **Modify VHDL** → Use `@vhdl-dev` agent (when available)

---

## Key Features

### Default Reference
- **Always** reads `.serena/memories/instrument_oscilloscope.md` before oscilloscope setup
- Reads other instrument docs on-demand

### moku-models First
- Uses Pydantic models as primary interface
- Type-safe configuration with automatic validation
- Converts to dict only when calling 1st party moku library

### Device Discovery
- Find Moku devices via zeroconf
- Cache device metadata (IP, serial, name)
- Lookup by IP or friendly name

### Hardware Validation
- Oscilloscope polling pattern (handles latency)
- FSM state decoding
- Voltage reading and interpretation

---

## Integration with Slash Commands

Use `/moku` to enter deployment mode, then invoke agent:

```
/moku
@moku-deploy Deploy DS1140-PD
```

---

## Reference Tools

- `tools/moku_go.py` - moku-models pattern, device discovery
- `tools/deploy_ds1140_pd.py` - Comprehensive deployment example
- `tools/fire_now.py` - Quick testing script

---

## Available Instrument API Docs

Read `.serena/memories/instrument_*.md` for:
- Oscilloscope (read by default)
- CloudCompile, Arbitrary Waveform Generator
- Waveform Generator, Spectrum Analyzer
- Lock-In Amplifier, Phasemeter, PID Controller
- Plus 9 more instruments

---

## Files

- `agent.md` - Standalone agent instructions (portable)
- `README.md` - This file (usage guide)

---

**Version:** 1.0
**Last Updated:** 2025-01-28
