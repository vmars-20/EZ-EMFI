# Phase 2 Continuation Prompt

Hi Claude! I'm continuing the EZ-EMFI CocotB migration project.

## What We've Accomplished (Phase 1)

✅ **Bulletproof CocotB test infrastructure**
- Pure Python test runner (no Makefiles!)
- OS-level GHDL output filtering (cannot be bypassed)
- Successfully runs tests with 98% cleaner output
- All infrastructure files committed

**Key Achievement:**
```bash
uv run python tests/run.py volo_clk_divider
# Output: [Filtered 2 lines (2/113 = 1.8% reduction)]
# Result: ✅ Test 'volo_clk_divider' PASSED (all 7 tests)
```

## What's Next (Phase 2)

Please read `PHASE2-TODO.md` for the full plan. High-level goals:

1. **Reorganize VHDL files** into logical structure:
   - `VHDL/volo_modules/` - reusable components
   - `VHDL/ds1120_pd/` - application code

2. **Create progressive test structure** (P1/P2/P3 levels):
   - P1 = 3-5 essential tests, <20 lines output (LLM-friendly!)
   - P2 = Full test suite
   - P3 = Comprehensive with edge cases

3. **Update documentation** with new testing workflow

4. **Clean up** temporary files and old structure

## Key References

You have access to:
- `volo_vhdl_external_/` - The full original project with examples
- `outside_docs_helpme/VOLO_COCOTB_TESTING_STANDARD.md` - Testing patterns
- `README-COCOTB.md` - What we just built in Phase 1

## Starting Point

**Option A: Start with VHDL reorganization**
```bash
# Create directories and move files
mkdir -p VHDL/volo_modules VHDL/ds1120_pd
git mv VHDL/volo_*.vhd VHDL/volo_modules/
# ... etc
```

**Option B: Start with progressive test example**
Create `tests/volo_clk_divider_tests/` with P1/P2 split to demonstrate the pattern.

**Option C: Ask me which to prioritize**

## Important Guidelines

1. **Keep it simple** - We're creating a beginner-friendly repository
2. **Progressive approach** - P1 tests should be MINIMAL (truly <20 lines)
3. **Use git mv** - Preserve file history when reorganizing
4. **Test frequently** - After each change, verify tests still run
5. **Commit incrementally** - Don't batch everything into one giant commit

## Success Metrics

- [ ] All tests pass after reorganization
- [ ] P1 tests produce <20 lines of output
- [ ] Structure is clear and logical
- [ ] Documentation is concise and helpful

## My Preference

I'd like to start with **Option B** (progressive test example) because:
- It demonstrates the pattern clearly
- Lower risk than moving files
- Can be tested immediately
- Shows immediate value

But I'm open to your recommendation based on what makes most sense!

---

**Ready when you are!** Feel free to ask clarifying questions before diving in.
