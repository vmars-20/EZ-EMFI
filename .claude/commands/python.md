# Python Development Mode

You are now in **Python tooling and TUI development mode**.

---

## Autonomous Development

For TUI apps, YAML parsing, and Python utilities, use the specialized agent:

```
@python-dev Build Textual TUI for DS1140-PD control
@python-dev Parse DS1140_PD_app.yaml and extract register definitions
@python-dev Create voltage conversion utility module
```

The python-dev agent has:
- Full access to `tools/`, `models/`, `scripts/`, `shared/` (read/write)
- Knowledge of Textual TUI framework
- **moku-models as primary interface** (Pydantic validation)
- Voltage conversion patterns, register packing helpers

---

## Key Files in Scope

**Python Source:**
- `tools/**/*.py` - TUI apps, deployment scripts, utilities
- `models/**/*.py` - Data models, YAML parsers
- `moku-models/` - Type-safe Moku configuration (submodule, read-only)
- `scripts/**/*.py` - Build/deployment automation
- `shared/**/*.py` - Shared utilities

**Configuration:**
- `*.yaml` - Application descriptors (DS1140_PD_app.yaml, etc.)
- `pyproject.toml` - Dependencies and project config

---

## Quick Reference

**Environment:**
```bash
uv sync                              # Install dependencies
uv run python tools/<script>.py      # Run scripts
ruff check . && ruff format .        # Lint + format
```

**DS1140-PD Registers (7 total: CR20-CR28):**
- Control: Arm (CR20), Fire (CR21), Reset (CR22)
- Timing: Clock Div (CR23), Timeout (CR24), Fire/Cool Duration (CR25-26)
- Voltage: Threshold (CR27), Intensity (CR28)

**Voltage scale:** ±5V = 16-bit signed (`voltage = raw / 32767.0 * 5.0`)

**Reference tools:**
- `tools/moku_go.py` - moku-models pattern
- `tools/deploy_ds1140_pd.py` - Deployment example
- `tools/ds1140_tui_prototype.py` - Textual TUI

---

## Context Switching

**Working on tests?** → `/test`
**Deploying to hardware?** → `/moku`
**Working on VHDL?** → `/vhdl` (when available)

---

Now in Python development mode. Use `@python-dev` for autonomous development work.
