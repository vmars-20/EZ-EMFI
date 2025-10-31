--------------------------------------------------------------------------------
-- File: test_shim_handshake.vhd
-- Purpose: Test harness for shim layer handshaking validation
--
-- Exposes shim internals for direct testing of ready_for_updates protocol.
-- This is a minimal test fixture that implements ONLY the register update
-- process from the shim template.
--
-- Reference: docs/CocoTB-TestingNetworkRegs.md
-- Created: 2025-01-31
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity test_shim_handshake is
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk   : in  std_logic;
        Reset : in  std_logic;

        ------------------------------------------------------------------------
        -- Handshaking control (from main application)
        ------------------------------------------------------------------------
        ready_for_updates : in  std_logic;

        ------------------------------------------------------------------------
        -- Control register inputs (simulating network writes)
        ------------------------------------------------------------------------
        app_reg_6 : in  std_logic_vector(31 downto 0);
        app_reg_7 : in  std_logic_vector(31 downto 0);

        ------------------------------------------------------------------------
        -- Friendly signal outputs (for verification)
        ------------------------------------------------------------------------
        intensity : out signed(15 downto 0);
        threshold : out signed(15 downto 0)
    );
end test_shim_handshake;

architecture rtl of test_shim_handshake is
begin

    ----------------------------------------------------------------------------
    -- Atomic Register Update Process
    --
    -- This is the EXACT process from custom_inst_shim_template.vhd
    -- Implements gated latching controlled by ready_for_updates signal.
    ----------------------------------------------------------------------------
    REGISTER_UPDATE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                -- Load default values (from HandShakeProtocol.md examples)
                -- These match the values in handshake_constants.py
                intensity <= to_signed(9830, 16);   -- 0x2666 (2.0V)
                threshold <= to_signed(11796, 16);  -- 0x2E0E (2.4V)

            elsif ready_for_updates = '1' then
                -- Atomic update: Latch current CR values
                -- Main application has signaled it's safe to apply changes
                intensity <= signed(app_reg_6(31 downto 16));
                threshold <= signed(app_reg_7(31 downto 16));
            end if;
            -- else: Hold previous values (gate closed, main app is busy)
        end if;
    end process REGISTER_UPDATE_PROC;

end architecture rtl;
