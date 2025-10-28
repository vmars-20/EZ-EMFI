# EZ-EMFI

**Electromagnetic Fault Injection (EMFI) probe driver for the Riscure DS1120-PD probe on Moku hardware**

EZ-EMFI is a VHDL-based EMFI probe driver designed to run on Liquid Instruments' Moku platform using the Multi-instrument Cloud Compile (MCC) framework. It provides precise control over electromagnetic pulses for hardware security research and fault injection experiments.

## Quick Start

### Prerequisites

- Python 3.9 or later
- `uv` for Python environment management
- GHDL (for VHDL simulation/testing)
- Moku device (for hardware deployment)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd EZ-EMFI

# Install Python dependencies with uv
uv sync

# Install Moku API
pip install moku
```

### Running Tests

The project uses progressive CocotB testing for LLM-friendly output:

```bash
# Quick validation (P1 tests, <20 lines output)
uv run python tests/run.py ds1120_pd_volo

# Full test suite (P2 tests)
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py ds1120_pd_volo

# Run all tests
uv run python tests/run.py --all

# Test specific module
uv run python tests/run.py volo_clk_divider
```

## Project Structure

```
EZ-EMFI/
├── VHDL/                      # All VHDL source files
│   ├── Top.vhd               # Layer 1: CustomWrapper architecture
│   ├── DS1120_PD_volo_shim.vhd   # Layer 2: Register mapping (generated)
│   ├── DS1120_PD_volo_main.vhd   # Layer 3: Application logic
│   ├── ds1120_pd_fsm.vhd     # 7-state FSM core
│   └── volo_*.vhd            # Reusable VoloApp modules
├── tests/                     # Progressive CocotB tests
│   ├── ds1120_pd_tests/      # DS1120-PD test package
│   └── test_*.py             # Progressive test files
├── models/                    # Python models for code generation
├── tools/                     # Code generation and deployment tools
├── docs/                      # Documentation
│   ├── COCOTB_PATTERNS.md    # Testing patterns reference
│   └── PROGRESSIVE_TESTING_GUIDE.md  # Testing guide
├── DS1120_PD_app.yaml        # Application descriptor
├── pyproject.toml            # Python dependencies
└── CLAUDE.md                 # AI assistant guidance
```

## Architecture

EZ-EMFI uses a **3-layer VoloApp architecture** for clean separation of concerns:

### Layer 1: Top.vhd (CustomWrapper)
- Implements MCC CustomWrapper interface
- BRAM loader FSM for configuration data
- VOLO_READY control scheme (3-bit enable control)
- Maps Control Registers (CR0-CR30) to application registers

### Layer 2: DS1120_PD_volo_shim.vhd (Register Mapping)
- **Auto-generated** from YAML descriptor
- Maps raw Control Registers to friendly signal names
- Example: CR20 → `armed`, CR21 → `force_fire`
- MCC-agnostic interface for application logic

### Layer 3: DS1120_PD_volo_main.vhd (Application Logic)
- **Hand-written application code**
- Uses friendly signal names only
- Integrates FSM, clock divider, trigger detection
- Implements safety features (voltage clamping, timeouts)

## Key Features

### Safety Controls
- **Voltage clamping:** Maximum 3.0V intensity output
- **Timing limits:** Max 32 firing cycles, min 8 cooling cycles
- **Timeout protection:** Configurable armed timeout (12-bit, up to 4095 cycles)
- **Spurious trigger detection:** Monitors triggers when not armed
- **Fire count limiting:** Prevents excessive use (max 15 fires)
- **Fault state:** Hard fault state for error conditions

### 7-State FSM
```
READY (000) → ARMED (001) → FIRING (010) → COOLING (011) → DONE (100)
                  ↓                                            ↑
              TIMEDOUT (101) --------------------------------→┘
                  ↓
              HARDFAULT (111)
```

### Control Interface
- **CR20:** Armed - Arm the probe driver
- **CR21:** Force Fire - Manual trigger (bypass threshold)
- **CR22:** Reset FSM - Return to READY state
- **CR23:** Timing Control - Clock divider + delay upper bits
- **CR24:** Delay Lower - Armed timeout lower 8 bits
- **CR25:** Firing Duration - Cycles to stay in FIRING state
- **CR26:** Cooling Duration - Cycles to stay in COOLING state
- **CR27-28:** Trigger Threshold - 16-bit voltage threshold (default 2.4V)
- **CR29-30:** Intensity - 16-bit output intensity (clamped to 3.0V)

## Development

### Testing Workflow

The project uses **progressive testing** to minimize test output while maintaining full coverage:

**P1 Tests (Default):**
- 2-4 essential tests per module
- <20 lines output (LLM-friendly)
- Runs automatically on every test invocation

**P2 Tests (Comprehensive):**
- Full test coverage
- Edge cases and boundaries
- Enable with `TEST_LEVEL=P2_INTERMEDIATE`

**Example:**
```bash
# P1 output (default):
P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Arm and trigger
  ✓ PASS
T3: Intensity clamping
  ✓ PASS
T4: Enable control
  ✓ PASS
ALL 4 TESTS PASSED

# P2 runs all 7 tests when needed
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py ds1120_pd_volo
```

### Code Generation

The shim layer is auto-generated from a YAML descriptor:

```bash
# Generate shim and main template
uv run python tools/generate_volo_app.py \
    --config DS1120_PD_app.yaml \
    --output generated/
```

### Linting and Formatting

```bash
# Run Ruff linter
ruff check .

# Run Ruff formatter
ruff format .
```

## Hardware Deployment

### Build MCC Package

```bash
# Build package for CloudCompile
uv run python scripts/build_mcc_package.py modules/DS1120-PD
```

### Deploy to Moku

```bash
# After CloudCompile, deploy bitstream
python tools/volo_loader.py \
    --config DS1120_PD_app.yaml \
    --device <device_id> \
    --ip <device_ip>
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete project reference for AI assistants
- **[PHASE2_COMPLETE.md](PHASE2_COMPLETE.md)** - Phase 2 implementation summary
- **[docs/COCOTB_PATTERNS.md](docs/COCOTB_PATTERNS.md)** - Testing patterns reference
- **[docs/PROGRESSIVE_TESTING_GUIDE.md](docs/PROGRESSIVE_TESTING_GUIDE.md)** - Testing guide
- **[docs/USING_PATTERNS_REFERENCE.md](docs/USING_PATTERNS_REFERENCE.md)** - How to use patterns

## Technical Details

### Voltage Scale
- 16-bit signed integer
- ±5V full scale
- Resolution: ~305µV per bit
- Conversion utilities in `volo_voltage_pkg.vhd`

### VOLO_READY Control Scheme
Global enable requires ALL conditions:
- `volo_ready` (CR0[31]) - Set by loader after deployment
- `user_enable` (CR0[30]) - User-controlled enable
- `clk_enable` (CR0[29]) - Clock gating control
- `loader_done` - BRAM loader completion signal

### Reset Hierarchy
Priority: `Reset > ClkEn > Enable`
- `Reset = '1'` → Forces safe state unconditionally
- `Enable = '0'` → Disables functional operation
- `ClkEn = '0'` → Freezes sequential logic

## Contributing

When contributing to this project:

1. **Tests are required** - Add progressive tests for new modules
2. **Keep P1 minimal** - Essential tests only, <20 lines output
3. **Use the patterns** - Reference `docs/COCOTB_PATTERNS.md`
4. **VHDL conventions** - Follow signal naming and reset strategies in CLAUDE.md
5. **Safety first** - All intensity outputs must be clamped to 3.0V max

## License

[Add license information]

## Contact

[Add contact information]

## Acknowledgments

Built on the VoloApp framework and Moku Multi-instrument Cloud Compile platform.
