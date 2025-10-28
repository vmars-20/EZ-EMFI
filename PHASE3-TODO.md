# Phase 3: Shared Module Library & Testing Expansion

Phase 2 ✅ Complete: 3-layer architecture, progressive testing, documentation

---

## Overview

**Goal:** Establish a reusable VHDL module library as a git submodule with comprehensive progressive tests.

**Why:**
- Share modules across projects (DS1120-PD, future VoloApps)
- Centralize testing and maintenance
- Enable version control for shared components
- Clean separation: reusable vs. application-specific code

**Estimated Time:** 6-8 hours (split across multiple sessions)

---

## Strategic Decisions Needed Before Starting

### Decision 1: Submodule Repository Strategy

**Option A: Create New Standalone Repo (RECOMMENDED)**
```
volo-hdl-common/              # New repo on GitHub/GitLab
├── modules/
│   ├── volo_clk_divider.vhd
│   ├── volo_voltage_pkg.vhd
│   └── ...
├── tests/                    # Progressive tests
├── docs/                     # Module documentation
└── README.md
```

**Pros:**
- Full control over versioning
- Can add CI/CD
- Clean separation from volo_vhdl_external_
- Progressive tests integrated from the start

**Cons:**
- Need to create and maintain separate repo
- Initial setup overhead

**Option B: Fork volo_vhdl_external_**
- Fork existing repo
- Add progressive tests
- Use as submodule

**Pros:**
- Keeps connection to upstream
- Can pull updates
- Less initial work

**Cons:**
- Inherits existing structure
- May have unwanted dependencies

**Option C: Use volo_vhdl_external_ Directly**
- Just add as submodule without forking
- Keep as read-only reference

**Pros:**
- Zero maintenance
- Always up-to-date with source

**Cons:**
- Can't add our tests
- No control over structure

**👉 RECOMMENDATION:** Option A (new repo) for maximum flexibility

---

### Decision 2: Directory Structure in EZ-EMFI

**Option 1: Submodule + Local Copies (RECOMMENDED)**
```
EZ-EMFI/
├── VHDL/
│   └── ds1120_pd_*.vhd           # App-specific only
├── volo-hdl/                     # Submodule (shared modules)
│   ├── modules/
│   │   ├── volo_clk_divider.vhd
│   │   └── volo_voltage_pkg.vhd
│   └── tests/                    # Module tests
└── tests/
    ├── test_configs.py           # References ../volo-hdl/modules/
    └── ds1120_pd_tests/          # App-specific tests
```

**Pros:**
- Clear separation
- Easy to update submodule
- Tests reference submodule directly

**Cons:**
- Need to update paths in test_configs.py

**Option 2: Flat Structure with Submodule**
```
EZ-EMFI/
├── VHDL/                         # Snapshot copied from submodule
│   ├── volo_*.vhd               # Local copies
│   └── ds1120_pd_*.vhd
└── volo-hdl/                     # Submodule (source of truth)
    └── modules/
```

**Pros:**
- VHDL/ directory self-contained
- Can work offline

**Cons:**
- Need manual sync process
- Duplication

**👉 RECOMMENDATION:** Option 1 (submodule references) for single source of truth

---

### Decision 3: Module Priority Order

**Criteria for prioritization:**
1. Currently used in EZ-EMFI? (High priority)
2. Well-tested already? (Lower priority)
3. Reusable across projects? (High priority)
4. Complex/critical? (High priority for testing)

**Suggested Priority (Tier 1 - Do First):**
1. ✅ volo_clk_divider (already has progressive tests)
2. ✅ volo_voltage_pkg (already has progressive tests)
3. volo_common_pkg (infrastructure, used everywhere)
4. volo_voltage_threshold_trigger_core (used in DS1120-PD)
5. volo_bram_loader (infrastructure)

**Tier 2 - Do Second:**
6. fsm_observer (useful for debugging)
7. Additional volo_vhdl_external_ modules (TBD based on exploration)

**Tier 3 - Future:**
8. Advanced modules
9. Specialized utilities

---

## Phase 3 Task Breakdown

### Stage 1: Planning & Exploration (30-45 min)

**1.1 Explore volo_vhdl_external_**
```bash
cd volo_vhdl_external_
find . -name "*.vhd" -type f | head -20
# Identify modules worth migrating
```

**1.2 Create Migration Spreadsheet**
Create `docs/MODULE_MIGRATION_PLAN.md`:
- Module name
- Current location
- Dependencies
- Test status
- Priority (1-3)
- Estimated test time

**1.3 Make Strategic Decisions**
- Choose submodule strategy (Option A/B/C)
- Choose directory structure (Option 1/2)
- Finalize module priority list

**Deliverable:** `docs/MODULE_MIGRATION_PLAN.md` with clear decisions

---

### Stage 2: Create Submodule Repository (1-2 hours)

**2.1 Create New Repo (if Option A chosen)**
```bash
# On GitHub/GitLab
# Create new repo: volo-hdl-common

# Clone locally
git clone <repo-url> volo-hdl-common
cd volo-hdl-common

# Set up structure
mkdir -p modules tests docs
cp <EZ-EMFI path> ...  # Copy initial modules
```

**2.2 Set Up Infrastructure**
```bash
# Add README
# Add LICENSE
# Add pyproject.toml (for testing)
# Add .gitignore
# Add test runner (tests/run.py)
# Add test_configs.py
```

**2.3 Initial Commit**
```bash
git add .
git commit -m "feat: Initialize volo-hdl-common shared library"
git push
```

**Deliverable:** Standalone repo ready for modules

---

### Stage 3: Migrate Priority Modules (3-4 hours)

**For Each Module (follow this pattern):**

**3.1 Create Staging Area (5 min)**
```bash
# In EZ-EMFI
mkdir -p incoming_modules/<module_name>/
```

**3.2 Copy Module Files (5 min)**
```bash
# Copy from volo_vhdl_external_ or VHDL/
cp volo_vhdl_external_/<module>.vhd incoming_modules/<module_name>/
# Or from current VHDL/ if already there
```

**3.3 Create Progressive Tests (30-45 min per module)**

Follow the established pattern:

```bash
# In volo-hdl-common repo
mkdir -p tests/<module_name>_tests
```

Create `tests/<module_name>_tests/<module_name>_constants.py`:
```python
from pathlib import Path

MODULE_NAME = "<module_name>"
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODULES_DIR = PROJECT_ROOT / "modules"

HDL_SOURCES = [MODULES_DIR / "<module_name>.vhd"]
HDL_TOPLEVEL = "<entity_name>"

class TestValues:
    P1_TEST_CYCLES = 20
    P2_TEST_CYCLES = 100

class ErrorMessages:
    RESET_FAILED = "Reset check failed: expected {}, got {}"
```

Create `tests/test_<module_name>_progressive.py`:
```python
import cocotb
from test_base import TestBase, VerbosityLevel
from <module_name>_tests.<module_name>_constants import *

class <ModuleName>Tests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def run_p1_basic(self):
        # 2-4 essential tests
        pass

    async def run_p2_intermediate(self):
        # Comprehensive tests
        pass

@cocotb.test()
async def test_<module_name>(dut):
    tester = <ModuleName>Tests(dut)
    await tester.run_all_tests()
```

**3.4 Test Module (10 min)**
```bash
# In volo-hdl-common
uv run python tests/run.py <module_name>
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module_name>
```

**3.5 Commit to Submodule (5 min)**
```bash
git add modules/<module_name>.vhd tests/<module_name>*
git commit -m "feat: Add <module_name> with progressive tests (P1/P2)"
git push
```

**Repeat for each priority module**

**Deliverable:** 5+ modules with progressive tests in submodule

---

### Stage 4: Integrate Submodule into EZ-EMFI (30-45 min)

**4.1 Add Submodule**
```bash
# In EZ-EMFI
git submodule add <repo-url> volo-hdl
git submodule update --init --recursive
```

**4.2 Update test_configs.py**
```python
# Update paths to reference submodule
VOLO_HDL = PROJECT_ROOT / "volo-hdl" / "modules"

TESTS_CONFIG = {
    "volo_clk_divider": TestConfig(
        sources=[VOLO_HDL / "volo_clk_divider.vhd"],
        # ...
    ),
}
```

**4.3 Remove Duplicate Files (if using Option 1 structure)**
```bash
# Remove modules now in submodule from VHDL/
git rm VHDL/volo_clk_divider.vhd
git rm VHDL/volo_voltage_pkg.vhd
# Keep ds1120_pd_*.vhd (app-specific)
```

**4.4 Test Integration**
```bash
uv run python tests/run.py --all
# Verify all tests still pass
```

**4.5 Update Documentation**
Update README.md:
```markdown
## Submodules

This project uses git submodules for shared VHDL modules:

### volo-hdl (Shared Module Library)
```bash
# Initialize after clone
git submodule update --init --recursive

# Update to latest
git submodule update --remote volo-hdl
```
```

**4.6 Commit Integration**
```bash
git add .gitmodules volo-hdl tests/test_configs.py README.md
git commit -m "feat: Integrate volo-hdl submodule for shared modules"
git push
```

**Deliverable:** EZ-EMFI using submodule, all tests passing

---

### Stage 5: Documentation & Polish (30-45 min)

**5.1 Create Module Documentation**

In `volo-hdl/docs/`:
- `MODULES.md` - List of all modules with descriptions
- `TESTING.md` - How to add new modules
- `USAGE.md` - How to use in projects

**5.2 Create Migration Guide**

In `EZ-EMFI/docs/`:
- `SUBMODULE_WORKFLOW.md` - How to work with submodules
  - Updating submodule
  - Adding new modules
  - Testing workflow

**5.3 Update EZ-EMFI Documentation**
- README.md - Reference submodule
- CLAUDE.md - Explain submodule structure

**Deliverable:** Complete documentation

---

## Iteration Prompt Template

**Use this prompt for each module migration:**

```
I'm migrating the [MODULE_NAME] module to the volo-hdl-common submodule with progressive tests.

Context:
- Module location: volo_vhdl_external_/[path] or VHDL/[file]
- Entity name: [entity_name]
- Dependencies: [list dependencies]
- Current test status: [untested / partial / needs progressive]

Tasks:
1. Review module code and identify test requirements
2. Create progressive test structure:
   - P1 (2-4 essential tests, <20 lines output)
   - P2 (comprehensive coverage)
3. Create constants file with test values
4. Implement tests following volo_clk_divider pattern
5. Test and verify both P1 and P2 pass
6. Commit to volo-hdl-common repo

Reference patterns:
- tests/volo_clk_divider_tests/ (working example)
- docs/COCOTB_PATTERNS.md (patterns reference)

Please create the progressive test structure for [MODULE_NAME].
```

---

## Success Criteria

Phase 3 complete when:

- [ ] Strategic decisions documented (submodule strategy, structure)
- [ ] volo-hdl-common repo created and initialized
- [ ] 5+ priority modules migrated with progressive tests
- [ ] All modules have P1 (<20 lines) and P2 tests
- [ ] Submodule integrated into EZ-EMFI
- [ ] All EZ-EMFI tests still pass
- [ ] Documentation complete (module docs, usage guides)
- [ ] Clean git history in both repos

---

## Time Estimates

| Stage | Task | Time |
|-------|------|------|
| 1 | Planning & Exploration | 30-45 min |
| 2 | Create Submodule Repo | 1-2 hours |
| 3 | Migrate 5 Modules | 3-4 hours |
| 4 | Integration | 30-45 min |
| 5 | Documentation | 30-45 min |
| **Total** | | **6-8 hours** |

**Recommendation:** Split across 2-3 sessions:
- Session 1: Stages 1-2 (planning + repo setup)
- Session 2: Stage 3 (module migration)
- Session 3: Stages 4-5 (integration + docs)

---

## Context Preservation Notes

- Each module migration is ~30-45 min (fits in single context window)
- Can pause between modules (each is independent)
- Documentation tasks are low-context
- Testing provides natural checkpoints

---

## Future Enhancements (Phase 4+)

After Phase 3, consider:
- CI/CD for volo-hdl-common (GitHub Actions)
- P3 comprehensive tests (stress testing, random)
- P4 exhaustive tests (formal verification)
- Additional modules from volo_vhdl_external_
- Module versioning strategy
- Release process

---

## Quick Reference

**Key Documents:**
- `docs/COCOTB_PATTERNS.md` - Testing patterns
- `docs/PROGRESSIVE_TESTING_GUIDE.md` - Conversion guide
- `examples/` - Working examples

**Key Commands:**
```bash
# Test a module (P1)
uv run python tests/run.py <module>

# Test a module (P2)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py <module>

# Update submodule
git submodule update --remote volo-hdl

# Run all tests
uv run python tests/run.py --all
```

---

**Ready to Start Phase 3!**

Begin with Stage 1 (Planning & Exploration) to make strategic decisions, then proceed through stages systematically.
