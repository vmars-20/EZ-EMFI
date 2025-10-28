# How to Use CocotB Patterns in Future Sessions

This document explains how to make Claude Code agents aware of the CocotB patterns reference.

---

## Option 1: Quick Reference in Prompt ⭐ **RECOMMENDED**

When starting a new test-related task, include this in your prompt:

```
I'm working on CocotB tests. Please refer to the patterns in:
- docs/COCOTB_PATTERNS.md - Common CocotB patterns reference
- docs/PROGRESSIVE_TESTING_GUIDE.md - Comprehensive conversion guide

These contain established patterns we use for progressive testing.
```

**This makes the agent:**
1. Read the patterns file first
2. Apply established patterns
3. Follow conventions we've already proven

---

## Option 2: Add to CLAUDE.md (Project Memory)

Update `/Users/vmars20/EZ-EMFI/CLAUDE.md` to include:

```markdown
## Testing Patterns

When working with CocotB tests, refer to these resources:

**Pattern References:**
- `docs/COCOTB_PATTERNS.md` - Quick reference for common patterns (10 patterns)
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Comprehensive conversion guide (575 lines)

**Key Patterns:**
- Progressive test structure (P1/P2/P3 levels via TestBase)
- Constants organization (TestValues, ErrorMessages classes)
- Common utilities (conftest.py helpers)
- Environment control (TEST_LEVEL, COCOTB_VERBOSITY)

**Working Examples:**
- Simple: `tests/volo_voltage_pkg_tests/`
- Complex: `tests/volo_clk_divider_tests/`
```

**Benefit:** Auto-loaded in every session, agent always knows about patterns.

---

## Option 3: Task-Specific Prompts

### For Test Conversion

```
Convert test_my_module.py to progressive format.

References:
- docs/PROGRESSIVE_TESTING_GUIDE.md - Step-by-step instructions
- docs/COCOTB_PATTERNS.md - Pattern reference
- tests/volo_clk_divider_tests/ - Working example

Follow the established pattern: P1 (2-4 tests, <20 lines output), P2 (comprehensive).
```

### For New Test Creation

```
Create a new progressive test for my_module.

Use patterns from docs/COCOTB_PATTERNS.md:
- Inherit from TestBase
- Create constants file with TestValues/ErrorMessages
- Implement run_p1_basic() with 2-4 essential tests
- Keep P1 output under 20 lines

Example: tests/volo_clk_divider_tests/
```

### For Debugging Tests

```
Debug failing test in test_my_module.py.

Refer to docs/COCOTB_PATTERNS.md section 9 (Common Gotchas):
- Entity name casing
- Signal access patterns
- Import path issues
```

---

## What's in Each File?

### docs/COCOTB_PATTERNS.md (Quick Reference)

**10 patterns, ~400 lines:**
1. Progressive test class structure (with TestBase)
2. Constants file organization
3. Common test utilities (conftest.py)
4. Conditional logging (verbosity levels)
5. Environment variables (TEST_LEVEL, COCOTB_VERBOSITY)
6. Assertion patterns
7. Directory structure
8. Test execution commands
9. Common gotchas
10. P1 test design guidelines

**Use when:** Writing/debugging tests, need quick pattern lookup

### docs/PROGRESSIVE_TESTING_GUIDE.md (Comprehensive Guide)

**8-step conversion process, 575 lines:**
- Why progressive testing? (context savings)
- Step-by-step conversion instructions
- Full code templates
- Working examples with explanations
- Troubleshooting section
- Best practices

**Use when:** Converting existing tests, learning the system

---

## Example Session Workflow

### Starting a Test Task

**User:** "Convert test_fsm_example.py to progressive format"

**Claude's optimal workflow:**
1. Reads `docs/PROGRESSIVE_TESTING_GUIDE.md` (comprehensive steps)
2. References `docs/COCOTB_PATTERNS.md` (pattern details)
3. Looks at `tests/volo_clk_divider_tests/` (working example)
4. Follows established patterns
5. Creates progressive test matching our conventions

**Result:** Consistent, well-structured test following proven patterns

---

## Prompt Template for Test Work

Copy/paste this when starting test-related work:

```
Task: [Your task description]

Context:
- This project uses progressive CocotB testing
- Patterns documented in docs/COCOTB_PATTERNS.md
- Full guide in docs/PROGRESSIVE_TESTING_GUIDE.md
- Working examples: tests/volo_clk_divider_tests/, tests/volo_voltage_pkg_tests/

Please:
1. Read the patterns reference first
2. Follow established conventions
3. Keep P1 tests minimal (<20 lines output)
4. Test after each step

[Additional task-specific instructions]
```

---

## Benefits of Using These References

### For You:
- ✅ Agents apply consistent patterns
- ✅ Less explanation needed in prompts
- ✅ Faster task completion
- ✅ Fewer mistakes/rework

### For Agents:
- ✅ Clear examples to follow
- ✅ Proven patterns (already working)
- ✅ Quick lookup vs. inferring patterns
- ✅ Gotchas documented (avoid common issues)

### For Project:
- ✅ Consistent code style
- ✅ Maintainable test structure
- ✅ Knowledge captured and reusable
- ✅ Easy onboarding for new contributors

---

## When to Update These Files?

**Update docs/COCOTB_PATTERNS.md when:**
- You discover a new useful pattern
- Common issue found (add to Gotchas section)
- New conftest.py utility added
- Pattern refinement needed

**Update docs/PROGRESSIVE_TESTING_GUIDE.md when:**
- Conversion process changes
- New step discovered
- Better template created
- Troubleshooting solution found

**Keep files synced** - If a pattern changes, update both:
- COCOTB_PATTERNS.md (quick reference)
- PROGRESSIVE_TESTING_GUIDE.md (detailed explanation)

---

## Summary

**Recommended approach:**

1. **Add to CLAUDE.md** (one-time setup, auto-loaded every session)
2. **Reference in prompts** (when starting test work)
3. **Point to specific sections** (when debugging specific issues)

**Result:** Agents consistently apply established patterns, saving time and ensuring quality.

---

**Created:** 2025-01-27 (Phase 2 completion)
**Purpose:** Help future Claude agents utilize learned CocotB patterns
