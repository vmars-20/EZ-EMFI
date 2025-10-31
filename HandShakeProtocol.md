# CustomInstrument Register Architecture and Handshaking Protocol

  Version: 2.0Status: Design SpecificationLast Updated: 2025-01-29

  Overview

  This document describes the register architecture and handshaking protocol for CustomInstrument applications running on the Moku
  platform. The system provides a clean abstraction between network-accessible control registers (CRs) and application logic, with
  atomic update semantics and three-layer separation of concerns.

  Core Principles

  1. Network registers are precious - Only 16 control registers (CR0-CR15) can be written over the network
  2. Atomic updates - Application logic controls when configuration changes are applied
  3. Clean separation - Three distinct layers with clear responsibilities
  4. No buffering in hardware - Shim layer gates updates, doesn't buffer them
  5. Complete state transfers - Python always sends full register set, never partial updates

  ---
  Register Map and Lifecycle

  Physical Register Allocation

  CR0:      Handoff protocol (3-bit, permanent reservation)
  CR1-CR5:  Shim layer internal use
  CR6-CR15: Application-visible registers (10 registers)

  Register Lifecycle Phases

  Phase 1: Boot (BRAM Loading)
  - BRAM loader uses CR1-CR15 for 4KB buffer transfer protocol
  - Loader is non-reentrant (one-time operation)
  - Duration: Boot sequence only

  Phase 2: Runtime (Application Control)
  - BRAM loader completes and releases CR1-CR15
  - All registers (CR1-CR15) now available for application use
  - BRAM buffer persists in memory (read-only from app perspective)
  - No residual state from loader

  Key Insight: After boot, CR1-CR15 are completely free. The BRAM loader leaves only the initialized buffer, no register state.

  ---
  Three-Layer Architecture

  ┌─────────────────────────────────────────────────────┐
  │  Python Network Layer                               │
  │  - Connects via Moku API                            │
  │  - Writes CR0-CR15 over network                     │
  │  - Always sends complete register set               │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼ (Network writes to CR0-CR15)
  ┌─────────────────────────────────────────────────────┐
  │  Shim Layer (Generated VHDL)                        │
  │  - Marshalls data from CRs                          │
  │  - Performs type conversions                        │
  │  - Gates updates based on ready signal              │
  │  - Latches converted values when main is ready      │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼ (Stable, typed signals)
  ┌─────────────────────────────────────────────────────┐
  │  Main Application (Hand-Written VHDL)               │
  │  - Application logic (FSMs, datapaths, etc.)        │
  │  - Controls when updates are safe (ready signal)    │
  │  - Uses converted signals directly                  │
  └─────────────────────────────────────────────────────┘

  Layer Responsibilities

  Python Layer:
  - Construct complete application state
  - Pack values into CR format
  - Execute single atomic network transaction
  - No awareness of handshaking timing

  Shim Layer (Auto-Generated):
  - Extract bit fields from CR registers
  - Convert std_logic_vector → typed signals (signed/unsigned)
  - Latch converted values only when ready_for_updates='1'
  - Provide stable outputs to main app
  - Manage default values on reset

  Main Application Layer (Developer-Written):
  - Implement application logic
  - Assert ready_for_updates when safe to accept new configuration
  - Use shim outputs directly (they're stable)
  - No knowledge of CR bit packing or network protocol

  ---
  Handshaking Protocol

  Signal Interface

  Shim → Main:
  -- All application registers (types vary by field)
  signal_name : out <type>;  -- Stable, latched values

  Main → Shim:
  ready_for_updates : in std_logic;  -- '1' = safe to update

  Protocol Behavior

  Shim Operation:
  process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        -- Load defaults from YAML
        intensity <= to_signed(9830, 16);  -- 2.0V default
        -- ... other defaults
      elsif ready_for_updates = '1' then
        -- Update all latched outputs from current CR values
        intensity <= signed(app_reg_9(31 downto 16));
        threshold <= signed(app_reg_8(31 downto 16));
        -- ... all other registers
      end if;
      -- else: hold previous values (gate closed)
    end if;
  end process;

  Main Application Pattern:
  process(clk)
  begin
    if rising_edge(clk) then
      case fsm_state is
        when IDLE | READY =>
          ready_for_updates <= '1';  -- Safe to reconfigure

        when ARMED | ACTIVE | CLEANUP =>
          ready_for_updates <= '0';  -- Lock configuration

      end case;
    end if;
  end process;

  -- Use signals directly (they're stable)
  dac_output <= intensity;  -- No double-latching needed

  Timing Diagram

  Cycle:     0    1    2    3    4    5    6    7
           ┌────┬────┬────┬────┬────┬────┬────┬────
  CR9      │ 0x2666 (2.0V)    │ 0x3DCF (2.4V)
           └────┴────┴────┴────┴────┴────┴────┴────
           ┌────┬────┬────┬────┬────┬────┬────┬────
  ready    │  0 │  0 │  0 │  1 │  1 │  0 │  0 │  1
           └────┴────┴────┴────┴────┴────┴────┴────
           ┌────┬────┬────┬────┬────┬────┬────┬────
  intensity│ 2.0V (latched)    │2.4V│ 2.4V (held)│2.4V
  (to main)└────┴────┴────┴────┴────┴────┴────┴────

  Cycle 0-2: Main busy (ready='0'), network writes CR9
  Cycle 3:   Main ready, shim latches 2.4V
  Cycle 4:   Network writes again (same value)
  Cycle 5-6: Main busy again, shim holds 2.4V
  Cycle 7:   Main ready, shim updates (no change this time)

  Key Properties:
  - No buffering: Shim always converts latest CR value
  - Gated latching: Updates only apply when ready='1'
  - Atomic updates: All registers update together in same cycle
  - Stable outputs: Main sees constant values between updates

  ---
  Network Interface Contract

  Python Responsibilities

  Complete State Transfer:
  # GOOD: Always send complete state
  controller.update_app_regs(
      arm_probe=1,
      force_fire=0,
      intensity=2.4,
      threshold=2.4,
      firing_duration=16,
      cooling_duration=16,
      clock_divider=0
      # ... all registers
  )

  # BAD: Partial updates (not supported)
  controller.update_app_regs(intensity=2.5)  # Missing other regs!

  Atomic Network Transaction:
  - Python constructs complete register map
  - Single network call updates all CRs
  - No assumptions about hardware timing
  - No read-back required (write-only model)

  Shim Expectations

  No Buffering:
  - Shim does NOT hold "pending" updates
  - CR changes are visible immediately (combinatorially)
  - Latching happens only when main asserts ready

  No Partial Updates:
  - Python guarantees complete state on every write
  - Shim can safely update all registers atomically
  - No need to track "which registers changed"

  ---
  Data Flow Summary

  User Input (TUI/CLI)
      ↓
  Python State Model (untyped dict/dataclass)
      ↓
  Python Packing (value → CR bit fields)
      ↓
  Network API (moku.set_frontend_register())
      ↓
  CR Registers (std_logic_vector(31 downto 0))
      ↓
  Shim Extraction (bit slicing, combinatorial)
      ↓
  Shim Conversion (std_logic_vector → typed, combinatorial)
      ↓
  Shim Latching (gated by ready_for_updates)
      ↓
  Main Application (stable typed signals)

  Latency: Network write → Main sees update = 0 to N cycles (depends on ready signal)

  ---
  Benefits of This Architecture

  Safety

  - Atomic updates: Main controls when config changes apply
  - No mid-operation glitches: ready='0' prevents updates during critical sections
  - Type safety: Shim provides correctly-typed signals (signed/unsigned)

  Simplicity

  - No double-latching: Main uses signals directly
  - No change detection: Python sends complete state every time
  - No buffering complexity: Shim just gates, doesn't queue

  Separation of Concerns

  - Python: High-level state management
  - Shim: Bit packing and type marshalling (generated)
  - Main: Application logic only (developer focus)

  Scalability

  - 10 multi-bit registers: CR6-CR15 for application values
  - 32 1-bit signals: Can pack into CR1 (shim internal)
  - Extensible: CR2-CR5 reserved for future shim features

  ---
  Design Constraints

  Hard Limits

  - 16 total CRs (CR0-CR15) - hardware limit
  - 1 CR reserved (CR0 for handoff) - protocol requirement
  - 10 CRs exposed (CR6-CR15) - architectural choice
  - No re-entrant BRAM loading - one-time boot operation

  Soft Conventions

  - Complete state transfers (Python) - simplifies shim
  - MSB-aligned packing (multi-bit fields) - clean extraction
  - Sequential CR allocation - deterministic generation

  ---
  Future Extensions (Out of Scope for v2.0)

  - Read-back support (main → shim → Python)
  - Change notification strobes (per-register update flags)
  - Multi-field register packing (>10 values via CR2-CR5)
  - Bidirectional handshaking (ready/valid/ack)
  - Message queue in shim (buffer pending updates)

  ---
  End of Architecture Specification
