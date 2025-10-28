# Reference Materials from volo-vhdl

**Status:** Reference only - DO NOT copy verbatim!

These documents are from the larger volo-vhdl project (40+ modules, complex structure).
They contain excellent patterns and wisdom but need **adaptation** for EZ-EMFI.

## What's Here

### Testing Guides
- **VOLO_COCOTB_TESTING_STANDARD.md** - Authoritative progressive testing patterns (P1/P2/P3/P4)
- **HUMAN_TESTING_README.md** - User-facing testing guide (adapt paths and scale)
- **HUMAN_NEW_MODULE_GUIDE.md** - Module creation guide (we use simpler structure)

### Scripts (Already Integrated)
- ✅ **build_vhdl_deps.py** → Copied to `scripts/build_vhdl.py`
- ✅ **ghdl_output_filter.py** → Copied to `scripts/ghdl_output_filter.py`

## How to Use

**DO:**
- Read for concepts and patterns
- Reference P1/P2/P3 test structure examples
- Learn from progressive testing philosophy
- Understand GHDL filtering strategies

**DON'T:**
- Copy directory structures (they have instruments/, experimental/, etc.)
- Copy file paths verbatim (different project structure)
- Assume same complexity (we have 6 modules, they have 40+)

## What Happens to These Files?

**After Phase 2 completes:**
- Move to `docs/reference/volo-vhdl/` for long-term reference
- Keep for future contributors who want to understand patterns
- Delete if all patterns are captured in EZ-EMFI docs

**For now:** Keep here as reference during Phase 2 progressive test creation.

---

See `PHASE2-prompt.md` for detailed guidance on using these references.
