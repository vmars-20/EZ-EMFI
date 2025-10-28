# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EZ-EMFI** is a multi-domain project combining VHDL EMFI probe drivers with Python control tooling for the Moku platform.

**Domains:**
- 🔌 **VHDL/EMFI**: Probe drivers (DS1120-PD, DS1140-PD) running on Moku FPGA
- 🐍 **Python Tooling**: TUI apps, MCC utilities, deployment scripts
- 🧪 **Testing**: CocotB progressive tests, hardware validation

---

## ⚡ Quick Start: Choose Your Context

**This repo contains multiple subsystems.** Use slash commands to load focused context:

### `/vhdl` - VHDL Development Context
Load this when working on:
- EMFI probe drivers (DS1120-PD, DS1140-PD)
- VHDL packages (volo_*, ds1120_pd_*)
- CocotB test development
- FSM design and debugging

**Files in scope:** `VHDL/`, `tests/`, VHDL-related docs

### `/python` - Python Tooling Context
Load this when working on:
- DS1140-PD TUI control app
- MCC package builders
- Deployment scripts
- Moku API integration

**Files in scope:** `tools/`, `models/`, `scripts/`, `shared/`

### `/test` - Testing Context
Load this when working on:
- CocotB progressive tests (P1/P2/P3)
- Test infrastructure
- Hardware validation
- Test debugging

**Files in scope:** `tests/`, test-related docs

---

## Project Structure

```
EZ-EMFI/
├── VHDL/                      # VHDL source (probe drivers, packages)
├── tests/                     # CocotB progressive tests
├── tools/                     # Python TUI apps and utilities
├── models/                    # Python data models (YAML parsing)
├── scripts/                   # Build/deployment scripts
├── docs/                      # Domain-specific documentation
├── .claude/commands/          # Context slash commands
└── .serena/memories/          # AI-optimized knowledge base (Moku APIs, lessons learned)
```

---

## Quick Reference

**VHDL:** 3-layer VoloApp architecture (Loader → Shim → Main)
**Testing:** Progressive CocotB (P1: fast, P2: comprehensive)
**Python:** DS1140-PD YAML-driven TUI (framework TBD)
**Deployment:** MCC CloudCompile → Moku hardware

---

## First Time Setup

```bash
# Python environment (uv)
uv sync

# Run VHDL tests
uv run python tests/run.py volo_clk_divider

# Check what's available
ls .claude/commands/        # Available contexts
uv run python tests/run.py --all  # All test modules
```

---

## Essential Documentation

**Before making changes, consult:**
- `.claude/commands/*.md` - Domain-specific contexts (use slash commands)
- `docs/VHDL_COCOTB_LESSONS_LEARNED.md` - Critical testing pitfalls
- `docs/OSCILLOSCOPE_DEBUGGING_TECHNIQUES.md` - Hardware validation workflows
- `docs/CLAUDE_FULL_BACKUP.md` - Complete VHDL documentation (backup)

**For detailed VHDL reference:** Use `/vhdl` command or read `docs/CLAUDE_FULL_BACKUP.md`

**For Moku API reference:** Use `/moku` command to access `.serena/memories/instrument_*.md`

---

## Serena Integration

**EZ-EMFI uses Serena memories** for AI-optimized knowledge storage:

**Instrument APIs (16 files):**
- `instrument_oscilloscope.md`, `instrument_cloud_compile.md`, `instrument_arbitrary_waveform_generator.md`
- `instrument_data_logger.md`, `instrument_spectrum_analyzer.md`, `instrument_waveform_generator.md`
- Plus 10 more instrument references (see `.serena/memories/instrument_*.md`)

**MCC & Hardware (4 files):**
- `mcc_routing_concepts.md` - Slot routing and cross-slot connections
- `riscure_ds1120a.md` - DS1120A EMFI probe hardware specifications
- `platform_models.md` - Moku platform specs (with Control0-15 caveat)
- `oscilloscope_debugging_techniques.md` - Hardware validation patterns

**Why Serena?**
- LLM-optimized markdown format
- No MCP server dependency (direct file access)
- Version controlled with git
- Portable across projects
- Captures incremental learning during hardware debugging

**Future memories** (to be captured during deployment):
- `ds1140_pd_deployment.md` - DS1140-PD hardware validation lessons
- `emfi_probe_characterization.md` - EMFI probe testing results

**Access via:** `/moku` slash command references all Serena memories

---

## Context Switching Guide

**Working on VHDL?** → Type `/vhdl` to load VHDL-specific context
**Working on Python?** → Type `/python` to load TUI/tooling context
**Debugging tests?** → Type `/test` to load testing infrastructure

**Why?** Keeps context tight, prevents LLM confusion between VHDL and Python domains.

---

## Contributing

When adding new features:
1. Choose the appropriate domain context (`/vhdl`, `/python`, `/test`)
2. Follow domain-specific guidelines (loaded by slash command)
3. Update relevant slash command if you discover new patterns
4. Test in the appropriate environment (GHDL, CocotB, or Python)

---

**Last Updated:** 2025-01-28
**Maintainer:** vmars20
**Full VHDL Docs:** `docs/CLAUDE_FULL_BACKUP.md` (306 lines)
