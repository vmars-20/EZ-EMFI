# Python Development Agent

**Purpose:** Build TUI apps, parse YAML, write Python utilities for EZ-EMFI

---

## Quick Start

### In Claude Code

```
@python-dev Build a Textual TUI for DS1140-PD control
@python-dev Parse DS1140_PD_app.yaml and extract register definitions
@python-dev Create voltage conversion utility module
```

### In Cursor / Other IDEs

1. Copy contents of `agent.md`
2. Paste into chat context
3. Ask: "Build a Textual TUI for DS1140-PD control"

---

## Common Use Cases

### Building TUI Apps

```
@python-dev Build Textual TUI for DS1140-PD with buttons and voltage inputs
@python-dev Add FSM state display to existing TUI
@python-dev Create mock Moku client for TUI testing
```

### YAML Parsing

```
@python-dev Parse DS1140_PD_app.yaml and generate register constants
@python-dev Validate register definitions in YAML file
@python-dev Extract control register mappings
```

### Writing Utilities

```
@python-dev Create voltage conversion module with type hints
@python-dev Build register packing/unpacking helpers
@python-dev Write FSM state decoder utility
```

### moku-models Integration

```
@python-dev Create MokuConfig for DS1140-PD deployment
@python-dev Build device discovery script using moku-models
@python-dev Validate routing configuration with Pydantic
```

---

## What This Agent Can Do

✅ **Read & Write:**
- `tools/**/*.py` - TUI apps, deployment scripts, utilities
- `models/**/*.py` - Data models, YAML parsers
- `scripts/**/*.py` - Build/deployment automation
- `shared/**/*.py` - Shared utilities
- `*.yaml` - Application descriptors

✅ **Read-Only (for context):**
- `moku-models/` - Type-safe configuration models
- `tests/**/*.py` - Test patterns
- `docs/**/*.md` - Documentation

---

## What This Agent Cannot Do

❌ **Modify tests** → Use `@test-runner` agent
❌ **Modify VHDL** → Use `@vhdl-dev` agent (when available)
❌ **Deploy to hardware** → Use `@moku-deploy` agent (for deployment scripts)

---

## Key Features

### Textual TUI Framework
- Modern terminal UI with buttons, inputs, tables
- Async/await support for Moku API
- CSS-like styling
- Hot reload for development

### moku-models First
- **Always** uses Pydantic models as primary interface
- Type-safe configuration
- Automatic validation
- Converts to dict only when calling 1st party moku library

### Code Quality
- Type hints for all functions
- Ruff-compliant formatting
- Google-style docstrings
- Input validation

---

## Integration with Slash Commands

Use `/python` to enter Python development mode, then invoke agent:

```
/python
@python-dev Build TUI for DS1140-PD
```

---

## Reference Tools

- `tools/moku_go.py` - moku-models pattern, device discovery
- `tools/deploy_ds1140_pd.py` - Deployment workflow example
- `tools/ds1140_tui_prototype.py` - Textual TUI prototype
- `tools/fire_now.py` - Quick testing script

---

## Files

- `agent.md` - Standalone agent instructions (portable)
- `README.md` - This file (usage guide)

---

**Version:** 1.0
**Last Updated:** 2025-01-28
