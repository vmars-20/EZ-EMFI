# Moku Deployment Mode

You are now in **Moku hardware deployment mode**.

---

## Autonomous Deployment

For hardware deployment, device discovery, and multi-instrument setup, use the specialized agent:

```
@moku-deploy Deploy DS1140-PD with oscilloscope monitoring
@moku-deploy Discover Moku devices on network
@moku-deploy Configure routing for cross-slot connections
```

The moku-deploy agent has:
- Access to deployment scripts (`tools/**/*.py`)
- Instrument API docs (`.serena/memories/instrument_*.md`)
- **moku-models as primary interface** (Pydantic validation)
- Device discovery and caching patterns
- Hardware validation workflows

---

## Key Files in Scope

**Deployment Scripts:**
- `tools/deploy_ds1140_pd.py` - DS1140-PD deployment workflow
- `tools/moku_go.py` - Device discovery, moku-models pattern
- `tools/fire_now.py` - Quick testing

**API References:**
- `.serena/memories/instrument_oscilloscope.md` - **Read by default**
- `.serena/memories/instrument_cloud_compile.md` - Custom VHDL
- `.serena/memories/instrument_*.md` - 14 more instruments
- `.serena/memories/mcc_routing_concepts.md` - Routing patterns
- `.serena/memories/platform_models.md` - Platform specs

---

## Quick Reference

**Deploy:**
```bash
uv run python tools/deploy_ds1140_pd.py --ip 192.168.1.100
uv run python tools/moku_go.py deploy --device 192.168.1.100 --bitstream bits.tar
```

**Discover:**
```bash
uv run python tools/moku_go.py discover
uv run python tools/moku_go.py list
```

**Multi-Instrument Pattern:**
```python
from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
from moku_models import MokuConfig, SlotConfig, MokuConnection  # Primary interface

m = MultiInstrument('192.168.1.100', platform_id=2)
mcc = m.set_instrument(2, CloudCompile, bitstream="bits.tar.gz")
osc = m.set_instrument(1, Oscilloscope)
```

**Critical:** Moku uses **±5V full scale** (NOT ±1V)

---

## Context Switching

**Working on Python scripts?** → `/python`
**Working on tests?** → `/test`
**Working on VHDL?** → `/vhdl` (when available)

---

Now in Moku deployment mode. Use `@moku-deploy` for autonomous deployment work.
