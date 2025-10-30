--------------------------------------------------------------------------------
-- File: MCC_TOP_custom_inst_loader.vhd
-- Author: Volo Team
-- Created: 2025-01-25
-- Updated: 2025-10-29 (CustomInstrument migration)
--
-- Description:
--   SimpleCustomInstrument architecture for CustomInstApp infrastructure.
--   This is the static, shared top-level file for ALL custom_inst apps.
--
-- Architecture: Behavioral of SimpleCustomInstrument
--
-- Responsibilities:
--   1. Extract VOLO_READY control bits from CR0[31:29]
--   2. Instantiate custom_inst_bram_loader FSM (CR1-CR5 protocol)
--   3. Pass app registers (CR6-CR15) to shim layer
--   4. Instantiate app-specific shim layer
--   5. Route MCC I/O (InputA/B/C, OutputA/B/C)
--
-- Register Map:
--   CR0[31]    = volo_ready  (set by loader after deployment)
--   CR0[30]    = user_enable (user-controlled enable/disable)
--   CR0[29]    = clk_enable  (clock gating for sequential logic)
--   CR0[28:0]  = Available for app-specific use
--   CR1-CR5    = BRAM loader protocol (managed by custom_inst_bram_loader FSM)
--   CR6-CR15   = Application registers (passed to shim, max 10 registers)
--
-- Design Note:
--   This file is STATIC and shared across all custom_inst apps.
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
--   - docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md
--   - CLAUDE.md "MCC 3-Bit Control Scheme"
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.custom_inst_common_pkg.all;

-- SimpleCustomInstrument entity is provided by MCC - DO NOT REDEFINE
-- See Moku documentation for SimpleCustomInstrument interface specification

architecture Behavioral of SimpleCustomInstrument is

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
    -- Application Register Signals (CR6-CR15)
    -- Only declare the ones your app uses (max 10 registers)
    ----------------------------------------------------------------------------
    signal app_reg_6      : std_logic_vector(31 downto 0);
    signal app_reg_7      : std_logic_vector(31 downto 0);
    signal app_reg_8      : std_logic_vector(31 downto 0);
    signal app_reg_9      : std_logic_vector(31 downto 0);
    signal app_reg_10     : std_logic_vector(31 downto 0);
    signal app_reg_11     : std_logic_vector(31 downto 0);
    signal app_reg_12     : std_logic_vector(31 downto 0);
    signal app_reg_13     : std_logic_vector(31 downto 0);
    signal app_reg_14     : std_logic_vector(31 downto 0);
    signal app_reg_15     : std_logic_vector(31 downto 0);

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
    -- Map Application Registers (CR6-CR15)
    ----------------------------------------------------------------------------
    app_reg_6  <= Control6;
    app_reg_7  <= Control7;
    app_reg_8  <= Control8;
    app_reg_9  <= Control9;
    app_reg_10 <= Control10;
    app_reg_11 <= Control11;
    app_reg_12 <= Control12;
    app_reg_13 <= Control13;
    app_reg_14 <= Control14;
    app_reg_15 <= Control15;

    ----------------------------------------------------------------------------
    -- Instantiate BRAM Loader FSM
    --
    -- Manages CR1-CR5 protocol for loading 4KB buffer
    ----------------------------------------------------------------------------
    BRAM_LOADER_INST: entity WORK.custom_inst_bram_loader
        port map (
            Clk      => Clk,
            Reset    => Reset,
            Control1 => Control1,
            Control2 => Control2,
            Control3 => Control3,
            Control4 => Control4,
            Control5 => Control5,
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
    -- Example for DS1140_PD:
    --
    -- APP_SHIM_INST: entity WORK.DS1140_PD_custom_inst_shim
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
    --         -- Application Registers (only used ones, max 10)
    --         app_reg_6   => app_reg_6,
    --         app_reg_7   => app_reg_7,
    --         app_reg_8   => app_reg_8,
    --
    --         -- BRAM Interface
    --         bram_addr   => bram_addr,
    --         bram_data   => bram_data,
    --         bram_we     => bram_we,
    --
    --         -- MCC I/O
    --         InputA      => InputA,
    --         InputB      => InputB,
    --         InputC      => InputC,
    --         OutputA     => OutputA,
    --         OutputB     => OutputB,
    --         OutputC     => OutputC
    --     );
    --
    ----------------------------------------------------------------------------

    -- Placeholder: Remove these when app shim is instantiated
    OutputA <= InputA;  -- Pass-through for now
    OutputB <= InputB;  -- Pass-through for now
    OutputC <= InputC;  -- Pass-through for now

    ----------------------------------------------------------------------------
    -- Future Enhancement: Dynamic App Loading
    --
    -- Possible approaches:
    -- 1. Build script substitutes app name during package creation
    -- 2. Use VHDL configuration to bind app shim at compile time
    -- 3. Multi-app loader with slot selection logic
    ----------------------------------------------------------------------------

end architecture Behavioral;
