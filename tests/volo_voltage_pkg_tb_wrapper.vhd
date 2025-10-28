--------------------------------------------------------------------------------
-- Simple Testbench Wrapper for volo_voltage_pkg (CocotB)
-- Purpose: Expose package constants for basic validation testing
-- Author: EZ-EMFI Team (adapted from volo-vhdl)
-- Date: 2025-01-27
--
-- Note: This wrapper exposes voltage conversion constants for testing.
--       Package functions are tested through Python CocotB assertions.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Import volo_voltage_pkg for testing
use work.volo_voltage_pkg.all;

entity volo_voltage_pkg_tb_wrapper is
    port (
        -- Expose common voltage constants as output ports for verification
        const_digital_1v      : out signed(15 downto 0);
        const_digital_2v4     : out signed(15 downto 0);
        const_digital_2v5     : out signed(15 downto 0);
        const_digital_3v      : out signed(15 downto 0);
        const_digital_3v3     : out signed(15 downto 0);
        const_digital_5v      : out signed(15 downto 0);
        const_digital_neg_1v  : out signed(15 downto 0);
        const_digital_neg_2v5 : out signed(15 downto 0);
        const_digital_zero    : out signed(15 downto 0);

        -- Simple passthrough for basic sanity check
        test_digital_passthrough : in signed(15 downto 0) := (others => '0');
        test_digital_result      : out signed(15 downto 0)
    );
end entity volo_voltage_pkg_tb_wrapper;

architecture simple of volo_voltage_pkg_tb_wrapper is
begin
    -- Expose constants from package
    const_digital_1v      <= VOLO_DIGITAL_1V;
    const_digital_2v4     <= VOLO_DIGITAL_2V4;
    const_digital_2v5     <= VOLO_DIGITAL_2V5;
    const_digital_3v      <= VOLO_DIGITAL_3V;
    const_digital_3v3     <= VOLO_DIGITAL_3V3;
    const_digital_5v      <= VOLO_DIGITAL_5V;
    const_digital_neg_1v  <= VOLO_DIGITAL_NEG_1V;
    const_digital_neg_2v5 <= VOLO_DIGITAL_NEG_2V5;
    const_digital_zero    <= VOLO_DIGITAL_ZERO;

    -- Simple passthrough (just verify signals work)
    test_digital_result <= test_digital_passthrough;

end architecture simple;
