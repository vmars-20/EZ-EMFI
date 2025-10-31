# Agents vs. Slash Commands - Migration Summary

**Date:** 2025-01-28
**Status:** Complete for test, python, moku agents

---

## Decision: Hybrid Approach (Option B)

We chose **lightweight slash commands + specialized agents** because:

1. ✅ Manual mode selection (user preference)
2. ✅ Tight context per domain (goal: reduce token bloat)
3. ✅ Autonomous exploration (primary need)
4. ✅ Clear separation: slash cmd = mode, agent = work

---

## Created Agents

### 1. test-runner
- **Location:** `.claude/agents/test-runner/`
- **Purpose:** Run/write/debug CocotB progressive tests
- **Scope:** Read/write `tests/**`, read-only `tools/**` (for context)
- **Slash command:** `/test` (39 lines, down from 506)

### 2. python-dev
- **Location:** `.claude/agents/python-dev/`
- **Purpose:** Build TUI apps, parse YAML, write Python utilities
- **Scope:** Read/write `tools/`, `models/`, `scripts/`, `shared/`, `*.yaml`
- **Slash command:** `/python` (71 lines, down from 429)

### 3. moku-deploy
- **Location:** `.claude/agents/moku-deploy/`
- **Purpose:** Deploy to hardware, device discovery, multi-instrument setup
- **Scope:** Read deployment scripts, execute deployments, edit configs
- **Slash command:** `/moku` (78 lines, down from 213)

---

## Agent Files Structure

Each agent has **dual-format** for portability:

```
.claude/agents/<agent-name>/
├── agent.md       # Standalone instructions (portable to Cursor, Codex, etc.)
└── README.md      # Human usage guide
```

**Slash commands** updated to be lightweight "mode indicators" that reference agents.

---

## Usage Patterns

### In Claude Code

```
/test                    # Enter testing mode
@test-runner Run P1 tests for volo_clk_divider

/python                  # Enter Python development mode
@python-dev Build Textual TUI for DS1140-PD

/moku                    # Enter deployment mode
@moku-deploy Deploy DS1140-PD with oscilloscope monitoring
```

### In Cursor / Other IDEs

1. Copy contents of `.claude/agents/<agent-name>/agent.md`
2. Paste into chat context
3. Ask your question

---

## Context Reduction Results

### Before (Slash Commands Only)

| Command | Lines | Tokens (est) |
|---------|-------|--------------|
| `/test` | 506   | ~3,500       |
| `/python` | 429 | ~3,000       |
| `/moku` | 213   | ~1,500       |
| **Total** | **1,148** | **~8,000** |

### After (Lightweight Slash Commands + Agents)

| Command | Lines | Tokens (est) |
|---------|-------|--------------|
| `/test` | 39    | ~300         |
| `/python` | 71  | ~500         |
| `/moku` | 78    | ~550         |
| **Total** | **188** | **~1,350** |

**Context savings:** ~83% reduction in slash command bloat

**Agent instructions:** Loaded only when invoked, kept separate from main conversation

---

## Key Features

### Scope Boundaries

Each agent has clear read/write permissions:

- **test-runner:** Can write to `tests/**`, read-only `tools/**`
- **python-dev:** Can write to `tools/`, `models/`, cannot touch `tests/**`
- **moku-deploy:** Read-only on scripts, executes deployments, edits configs

### moku-models First

All agents enforce **moku-models as primary interface**:
- Type-safe Pydantic configuration
- Automatic validation
- Convert to dict only when calling 1st party library

### Reference Documents

Agents know where to find detailed docs:
- test-runner → `docs/VHDL_COCOTB_LESSONS_LEARNED.md`
- python-dev → `tools/moku_go.py`, `tools/ds1140_tui_prototype.py`
- moku-deploy → `.serena/memories/instrument_*.md` (reads oscilloscope by default)

---

## What's Left

### /vhdl Slash Command

**Status:** Deferred for manual review

**Reason:** Contains outdated `volo_` references, project is migrating to `CustomInstrument` / `custom_inst`

**Next steps:**
1. User will update `/vhdl` slash command with current terminology
2. Create `vhdl-dev` agent after cleanup

---

## Agent Portability

### Claude Code
- Use `@agent-name` syntax
- Agents have full tool access (Glob, Grep, Read, Write, Edit, Bash, etc.)

### Cursor / Codex / Other Tools
- Copy `agent.md` contents into chat
- Standalone markdown instructions work anywhere
- No Claude Code-specific dependencies

---

## Migration Benefits

1. **Tight context:** Slash commands are now 10-80 lines instead of 200-500
2. **Autonomous exploration:** Agents search/read without cluttering main conversation
3. **Domain isolation:** Clear boundaries prevent VHDL/Python mixing
4. **Portable:** `agent.md` files work in any LLM tool
5. **Scalable:** Easy to add more specialized agents

---

## Future Agents (Ideas)

- `vhdl-dev` - VHDL development (after terminology update)
- `hardware-validation` - Oscilloscope debugging, FSM verification
- `ci-cd` - Test automation, deployment pipelines
- `docs` - Documentation generation and updates

---

## File Locations

**Agents:**
- `.claude/agents/test-runner/`
- `.claude/agents/python-dev/`
- `.claude/agents/moku-deploy/`

**Slash Commands:**
- `.claude/commands/test.md`
- `.claude/commands/python.md`
- `.claude/commands/moku.md`
- `.claude/commands/vhdl.md` (pending update)

**This Document:**
- `Agents-vs-slash-cmds.md` (root directory)

---

**Last Updated:** 2025-01-28
**Migration Status:** ✅ Complete (3/3 agents created)
