--------------------------------------------------------------------------------
-- File: custom_inst_common_pkg.vhd
-- Author: Volo Team
-- Created: 2025-01-25
-- Updated: 2025-10-29 (CustomInstrument migration)
--
-- Description:
--   Common constants and types for CustomInstApp infrastructure.
--   Defines the VOLO_READY control scheme, BRAM interface parameters,
--   and application register ranges.
--
-- Design Pattern:
--   This package is shared across ALL custom_inst apps and provides the foundation
--   for the 3-layer CustomInstApp architecture:
--     Layer 1: MCC_TOP_custom_inst_loader.vhd (uses this package)
--     Layer 2: <AppName>_custom_inst_shim.vhd (uses this package)
--     Layer 3: <AppName>_custom_inst_main.vhd (MCC-agnostic, doesn't use this)
--
-- Register Map:
--   CR0[31:29] - VOLO_READY control scheme (3-bit)
--   CR1-CR5    - BRAM loader protocol (5 registers)
--   CR6-CR15   - Application registers (10 max)
--
-- References:
--   - docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md
--   - CLAUDE.md "MCC 3-Bit Control Scheme"
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package custom_inst_common_pkg is

    ----------------------------------------------------------------------------
    -- VOLO_READY Control Scheme (CR0[31:29])
    --
    -- Safe default: All-zero state keeps module disabled (bit 31=0)
    --
    -- Usage in Top.vhd:
    --   volo_ready  <= Control0(31);  -- Set by loader after deployment
    --   user_enable <= Control0(30);  -- User-controlled enable/disable
    --   clk_enable  <= Control0(29);  -- Clock gating for sequential logic
    --   global_enable <= volo_ready and user_enable and clk_enable and loader_done;
    ----------------------------------------------------------------------------
    constant VOLO_READY_BIT  : natural := 31;
    constant USER_ENABLE_BIT : natural := 30;
    constant CLK_ENABLE_BIT  : natural := 29;

    ----------------------------------------------------------------------------
    -- BRAM Loader Protocol (CR1-CR5)
    --
    -- 4KB buffer = 1024 words × 32 bits
    -- Address width: 12 bits (2^12 = 4096 bytes / 4 bytes per word = 1024 words)
    -- Data width: 32 bits (matches Control Register width)
    --
    -- The custom_inst_bram_loader FSM uses Control1-Control5 to stream data
    -- into the 4KB BRAM buffer during deployment initialization.
    ----------------------------------------------------------------------------
    constant BRAM_ADDR_WIDTH : natural := 12;  -- 4KB addressing
    constant BRAM_DATA_WIDTH : natural := 32;  -- Control Register width

    ----------------------------------------------------------------------------
    -- Application Register Range (CR6-CR15)
    --
    -- Reserved for application-specific control registers.
    -- Maximum 10 registers available (inclusive range).
    --
    -- These are mapped to friendly signal names in the generated shim layer:
    --   Example: "Pulse Width" → pulse_width : std_logic_vector(7 downto 0)
    ----------------------------------------------------------------------------
    constant APP_REG_MIN : natural := 6;
    constant APP_REG_MAX : natural := 15;

    ----------------------------------------------------------------------------
    -- Helper Functions (Optional - for convenience)
    ----------------------------------------------------------------------------

    -- Combine VOLO_READY control bits into global enable signal
    function combine_volo_ready(
        volo_ready  : std_logic;
        user_enable : std_logic;
        clk_enable  : std_logic;
        loader_done : std_logic
    ) return std_logic;

end package custom_inst_common_pkg;

package body custom_inst_common_pkg is

    -- Combine all 4 ready conditions for global enable
    function combine_volo_ready(
        volo_ready  : std_logic;
        user_enable : std_logic;
        clk_enable  : std_logic;
        loader_done : std_logic
    ) return std_logic is
    begin
        return volo_ready and user_enable and clk_enable and loader_done;
    end function;

end package body custom_inst_common_pkg;
