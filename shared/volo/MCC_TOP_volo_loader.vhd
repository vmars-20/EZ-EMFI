--------------------------------------------------------------------------------
-- File: MCC_TOP_volo_loader.vhd
-- Author: Volo Team
-- Created: 2025-01-25
--
-- Description:
--   CustomWrapper architecture for VoloApp infrastructure.
--   This is the static, shared top-level file for ALL volo-apps.
--
-- Architecture: volo_loader of CustomWrapper
--
-- Responsibilities:
--   1. Extract VOLO_READY control bits from CR0[31:29]
--   2. Instantiate volo_bram_loader FSM (CR10-CR14 protocol)
--   3. Pass app registers (CR20-CR30) to shim layer
--   4. Instantiate app-specific shim layer
--   5. Route MCC I/O (InputA/B, OutputA/B)
--
-- Register Map:
--   CR0[31]    = volo_ready  (set by loader after deployment)
--   CR0[30]    = user_enable (user-controlled enable/disable)
--   CR0[29]    = clk_enable  (clock gating for sequential logic)
--   CR0[28:0]  = Available for app-specific use
--   CR10-CR14  = BRAM loader protocol (managed by volo_bram_loader FSM)
--   CR20-CR30  = Application registers (passed to shim)
--
-- Design Note:
--   This file is STATIC and shared across all volo-apps.
--   The app-specific shim is instantiated using direct instantiation.
--   For initial implementation, the app name is provided via comments/TODOs.
--   Future enhancement: Use build script to substitute app name.
--
-- Usage Pattern:
--   1. Copy this file to each app's build directory
--   2. Uncomment and customize the shim instantiation for your app
--   3. Build with MCC CloudCompile
--
-- References:
--   - docs/VOLO_APP_DESIGN.md
--   - CLAUDE.md "MCC 3-Bit Control Scheme"
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.volo_common_pkg.all;

-- CustomWrapper entity is provided by MCC - DO NOT REDEFINE
-- See Moku documentation for CustomWrapper interface specification

architecture volo_loader of CustomWrapper is

    ----------------------------------------------------------------------------
    -- VOLO_READY Control Signals (from CR0[31:29])
    ----------------------------------------------------------------------------
    signal volo_ready  : std_logic;
    signal user_enable : std_logic;
    signal clk_enable  : std_logic;

    ----------------------------------------------------------------------------
    -- BRAM Loader Signals
    ----------------------------------------------------------------------------
    signal bram_addr      : std_logic_vector(11 downto 0);
    signal bram_data      : std_logic_vector(31 downto 0);
    signal bram_we        : std_logic;
    signal loader_done    : std_logic;

    ----------------------------------------------------------------------------
    -- Application Register Signals (CR20-CR30)
    -- Only declare the ones your app uses
    ----------------------------------------------------------------------------
    signal app_reg_20     : std_logic_vector(31 downto 0);
    signal app_reg_21     : std_logic_vector(31 downto 0);
    signal app_reg_22     : std_logic_vector(31 downto 0);
    signal app_reg_23     : std_logic_vector(31 downto 0);
    signal app_reg_24     : std_logic_vector(31 downto 0);
    signal app_reg_25     : std_logic_vector(31 downto 0);
    signal app_reg_26     : std_logic_vector(31 downto 0);
    signal app_reg_27     : std_logic_vector(31 downto 0);
    signal app_reg_28     : std_logic_vector(31 downto 0);
    signal app_reg_29     : std_logic_vector(31 downto 0);
    signal app_reg_30     : std_logic_vector(31 downto 0);

begin

    ----------------------------------------------------------------------------
    -- Extract VOLO_READY Control Bits (CR0[31:29])
    --
    -- Safe default: All-zero state keeps module disabled (bit 31=0)
    -- The volo_loader.py script sets these bits after bitstream loading
    ----------------------------------------------------------------------------
    volo_ready  <= Control0(VOLO_READY_BIT);   -- Bit 31
    user_enable <= Control0(USER_ENABLE_BIT);  -- Bit 30
    clk_enable  <= Control0(CLK_ENABLE_BIT);   -- Bit 29

    ----------------------------------------------------------------------------
    -- Map Application Registers (CR20-CR30)
    ----------------------------------------------------------------------------
    app_reg_20 <= Control20;
    app_reg_21 <= Control21;
    app_reg_22 <= Control22;
    app_reg_23 <= Control23;
    app_reg_24 <= Control24;
    app_reg_25 <= Control25;
    app_reg_26 <= Control26;
    app_reg_27 <= Control27;
    app_reg_28 <= Control28;
    app_reg_29 <= Control29;
    app_reg_30 <= Control30;

    ----------------------------------------------------------------------------
    -- Instantiate BRAM Loader FSM
    --
    -- Manages CR10-CR14 protocol for loading 4KB buffer
    ----------------------------------------------------------------------------
    BRAM_LOADER_INST: entity WORK.volo_bram_loader
        port map (
            Clk       => Clk,
            Reset     => Reset,
            Control10 => Control10,
            Control11 => Control11,
            Control12 => Control12,
            Control13 => Control13,
            Control14 => Control14,
            bram_addr => bram_addr,
            bram_data => bram_data,
            bram_we   => bram_we,
            done      => loader_done
        );

    ----------------------------------------------------------------------------
    -- Instantiate App-Specific Shim Layer
    --
    -- TODO: Customize this section for your specific app
    --
    -- Example for PulseStar:
    --
    -- APP_SHIM_INST: entity WORK.PulseStar_volo_shim
    --     port map (
    --         -- Clock and Reset
    --         Clk         => Clk,
    --         Reset       => Reset,
    --
    --         -- VOLO Control Signals
    --         volo_ready  => volo_ready,
    --         user_enable => user_enable,
    --         clk_enable  => clk_enable,
    --         loader_done => loader_done,
    --
    --         -- Application Registers (only used ones)
    --         app_reg_20  => app_reg_20,
    --         app_reg_21  => app_reg_21,
    --         app_reg_22  => app_reg_22,
    --
    --         -- BRAM Interface
    --         bram_addr   => bram_addr,
    --         bram_data   => bram_data,
    --         bram_we     => bram_we,
    --
    --         -- MCC I/O
    --         InputA      => InputA,
    --         InputB      => InputB,
    --         OutputA     => OutputA,
    --         OutputB     => OutputB
    --     );
    --
    ----------------------------------------------------------------------------

    -- Placeholder: Remove these when app shim is instantiated
    OutputA <= InputA;  -- Pass-through for now
    OutputB <= InputB;  -- Pass-through for now

    ----------------------------------------------------------------------------
    -- Future Enhancement: Dynamic App Loading
    --
    -- Possible approaches:
    -- 1. Build script substitutes app name during package creation
    -- 2. Use VHDL configuration to bind app shim at compile time
    -- 3. Multi-app loader with slot selection logic
    ----------------------------------------------------------------------------

end architecture volo_loader;
