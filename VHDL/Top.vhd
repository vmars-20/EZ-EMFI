--------------------------------------------------------------------------------
-- File: MCC_TOP_volo_loader.vhd
-- Author: Volo Team
-- Created: 2025-10-28
--
-- Description:
--   CustomWrapper architecture for VoloApp infrastructure (DS1140-PD).
--   This is the static, shared top-level file for ALL volo-apps.
--
-- Architecture: DS1140_PD (refactored EMFI probe driver)
--
-- Responsibilities:
--   1. Extract VOLO_READY control bits from CR0[31:29]
--   2. Instantiate volo_bram_loader FSM (CR10-CR14 protocol)
--   3. Pass app registers (CR20-CR28) to shim layer
--   4. Instantiate app-specific shim layer (DS1140_PD_volo_shim)
--   5. Route MCC I/O (InputA/B, OutputA/B/C - THREE OUTPUTS!)
--
-- Register Map:
--   CR0[31]    = volo_ready  (set by loader after deployment)
--   CR0[30]    = user_enable (user-controlled enable/disable)
--   CR0[29]    = clk_enable  (clock gating for sequential logic)
--   CR0[28:0]  = Available for app-specific use
--   CR10-CR14  = BRAM loader protocol (managed by volo_bram_loader FSM)
--   CR20-CR28  = Application registers (7 registers, passed to shim)
--
-- Key Changes from DS1120-PD:
--   ✓ Architecture name: DS1140_PD (not DS1120_PD)
--   ✓ Component name: DS1140_PD_volo_shim (not DS1120_PD_volo_shim)
--   ✓ Three outputs: OutputA, OutputB, OutputC (DS1120-PD only used A and B)
--   ✓ Fewer registers: CR20-CR28 (7 registers vs 11 in DS1120-PD)
--
-- Design Note:
--   This file is STATIC and shared across all volo-apps.
--   The app-specific shim is instantiated using direct instantiation.
--
-- References:
--   - docs/VOLO_APP_DESIGN.md
--   - DS1140_PD_app.yaml
--   - DS1140_PD_LAYER1_HANDOFF.md
--   - DS1140_PD_THREE_OUTPUT_DESIGN.md
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.volo_common_pkg.all;

-- CustomWrapper entity is provided by MCC - DO NOT REDEFINE
-- See Moku documentation for CustomWrapper interface specification

architecture DS1140_PD of CustomWrapper is

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
    -- Application Register Signals (CR20-CR28)
    -- DS1140-PD uses 7 registers (simplified from DS1120-PD's 11)
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

begin

    ----------------------------------------------------------------------------
    -- Extract VOLO_READY Control Bits (Control15[31:29])
    --
    -- Safe default: All-zero state keeps module disabled (bit 31=0)
    -- The volo_loader.py script sets these bits after bitstream loading
    -- NOTE: Moved to Control15 to avoid conflict with application registers
    ----------------------------------------------------------------------------
    volo_ready  <= Control15(VOLO_READY_BIT);   -- Bit 31
    user_enable <= Control15(USER_ENABLE_BIT);  -- Bit 30
    clk_enable  <= Control15(CLK_ENABLE_BIT);   -- Bit 29

    ----------------------------------------------------------------------------
    -- Map Application Registers (Control0-Control8)
    -- DS1140-PD uses 9 control registers (MCC only provides Control0-Control15)
    ----------------------------------------------------------------------------
    app_reg_20 <= Control0;   -- Arm Probe
    app_reg_21 <= Control1;   -- Force Fire
    app_reg_22 <= Control2;   -- Reset FSM
    app_reg_23 <= Control3;   -- Clock Divider
    app_reg_24 <= Control4;   -- Arm Timeout
    app_reg_25 <= Control5;   -- Firing Duration
    app_reg_26 <= Control6;   -- Cooling Duration
    app_reg_27 <= Control7;   -- Trigger Threshold
    app_reg_28 <= Control8;   -- Intensity

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
    -- Instantiate App-Specific Shim Layer: DS1140_PD
    -- CRITICAL: Three outputs (OutputA, OutputB, OutputC)
    ----------------------------------------------------------------------------
    APP_SHIM_INST: entity WORK.DS1140_PD_volo_shim
        port map (
            -- Clock and Reset
            Clk         => Clk,
            Reset       => Reset,

            -- VOLO Control Signals
            volo_ready  => volo_ready,
            user_enable => user_enable,
            clk_enable  => clk_enable,
            loader_done => loader_done,

            -- Application Registers (CR20-CR28, 7 total)
            app_reg_20  => app_reg_20,
            app_reg_21  => app_reg_21,
            app_reg_22  => app_reg_22,
            app_reg_23  => app_reg_23,
            app_reg_24  => app_reg_24,
            app_reg_25  => app_reg_25,
            app_reg_26  => app_reg_26,
            app_reg_27  => app_reg_27,
            app_reg_28  => app_reg_28,

            -- BRAM Interface
            bram_addr   => bram_addr,
            bram_data   => bram_data,
            bram_we     => bram_we,

            -- MCC I/O (THREE OUTPUTS!)
            InputA      => InputA,
            InputB      => InputB,
            OutputA     => OutputA,  -- Trigger signal to probe
            OutputB     => OutputB,  -- Intensity/amplitude to probe
            OutputC     => OutputC   -- FSM state debug (NEW!)
        );

    ----------------------------------------------------------------------------
    -- OutputD Unused (tie to zero for safety)
    ----------------------------------------------------------------------------
    OutputD <= (others => '0');

    ----------------------------------------------------------------------------
    -- Future Enhancement: Dynamic App Loading
    --
    -- Possible approaches:
    -- 1. Build script substitutes app name during package creation
    -- 2. Use VHDL configuration to bind app shim at compile time
    -- 3. Multi-app loader with slot selection logic
    ----------------------------------------------------------------------------

end architecture DS1140_PD;
