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

### Reference Materials (Adapt, Don't Copy!)

**IMPORTANT:** Files in `outside_docs_helpme/` are from the large volo-vhdl project.
They contain excellent patterns but are **structured for a 40+ module project**.
You must **adapt** them for EZ-EMFI's simpler 6-module structure.

**What's in `outside_docs_helpme/`:**
1. ✅ **VOLO_COCOTB_TESTING_STANDARD.md** - Authoritative testing patterns
   - Progressive test levels (P1/P2/P3/P4) ← USE THIS!
   - Test organization structure ← SIMPLIFY for EZ-EMFI
   - Example outputs ← Great reference

2. ✅ **HUMAN_TESTING_README.md** - User-facing testing guide
   - Test execution examples ← Adapt for EZ-EMFI paths
   - Environment variables ← Keep these!
   - Quick start ← Simplify (we only have 5 tests, not 40!)

3. ✅ **HUMAN_NEW_MODULE_GUIDE.md** - Module creation patterns
   - 4-layer architecture (common/datadef/core/top) ← We don't use this
   - MCC integration patterns ← Useful for DS1120-PD
   - Safety patterns ← Good reference

4. ⚠️ **build_vhdl_deps.py** - Already copied to `scripts/build_vhdl.py`
5. ⚠️ **ghdl_output_filter.py** - Already copied to `scripts/ghdl_output_filter.py`

**How to use them:**
- Read for **patterns and concepts**
- Don't copy directory structures (volo-vhdl has instruments/, experimental/, etc.)
- Adapt examples to EZ-EMFI's simpler structure
- Reference progressive test examples (P1/P2/P3 split patterns)

**Also available:**
- `volo_vhdl_external_/` - Full project with working examples
  - Look at `tests/ds1120_pd_volo_tests/` for progressive structure
  - Look at `tests/counter_nbit_tests/` for simple module example
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
