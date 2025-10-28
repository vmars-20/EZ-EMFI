--------------------------------------------------------------------------------
-- Test Wrapper for volo_lut_pkg
-- Purpose: Provides entity for CocotB testing of volo_lut_pkg functions
-- Author: Claude Code
-- Date: 2025-01-28
--
-- This wrapper exposes volo_lut_pkg functions through entity ports so CocotB
-- can test the LUT infrastructure. Since packages contain only functions,
-- this wrapper provides combinational logic to exercise all package features.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.volo_voltage_pkg.all;
use work.volo_lut_pkg.all;

entity volo_lut_pkg_tb_wrapper is
    port (
        -- Control signals
        clk           : in  std_logic;
        reset         : in  std_logic;

        -- Test inputs
        test_index    : in  std_logic_vector(7 downto 0);  -- 0-255 (tests bounds)
        test_voltage  : in  signed(15 downto 0);            -- Voltage for reverse lookup

        -- Function select (one-hot encoding)
        sel_lut_lookup         : in  std_logic;  -- Test lut_lookup (unsigned)
        sel_lut_lookup_signed  : in  std_logic;  -- Test lut_lookup_signed
        sel_to_pct_index       : in  std_logic;  -- Test to_pct_index
        sel_voltage_to_pct     : in  std_logic;  -- Test voltage_to_pct_index

        -- Test outputs (registered for timing)
        lut_output_unsigned    : out std_logic_vector(15 downto 0);
        lut_output_signed      : out signed(15 downto 0);
        pct_index_output       : out std_logic_vector(7 downto 0);  -- 0-100 range
        voltage_output         : out signed(15 downto 0);

        -- Predefined LUT access
        linear_5v_lut_out      : out signed(15 downto 0);
        linear_3v3_lut_out     : out signed(15 downto 0)
    );
end entity volo_lut_pkg_tb_wrapper;

architecture rtl of volo_lut_pkg_tb_wrapper is

    -- Test LUT: Linear 0-5V for validation (0x0000 to 0xFFFF)
    constant TEST_LUT_UNSIGNED : lut_101x16_t := (
        x"0000", x"028F", x"051E", x"07AE", x"0A3D", x"0CCC", x"0F5C", x"11EB", x"147A", x"170A",
        x"1999", x"1C28", x"1EB8", x"2147", x"23D6", x"2666", x"28F5", x"2B84", x"2E14", x"30A3",
        x"3333", x"35C2", x"3851", x"3AE1", x"3D70", x"3FFF", x"428F", x"451E", x"47AD", x"4A3D",
        x"4CCC", x"4F5B", x"51EB", x"547A", x"5709", x"5999", x"5C28", x"5EB7", x"6147", x"63D6",
        x"6666", x"68F5", x"6B84", x"6E14", x"70A3", x"7332", x"75C2", x"7851", x"7AE0", x"7D70",
        x"7FFF", x"828E", x"851E", x"87AD", x"8A3C", x"8CCC", x"8F5B", x"91EA", x"947A", x"9709",
        x"9999", x"9C28", x"9EB7", x"A147", x"A3D6", x"A665", x"A8F5", x"AB84", x"AE13", x"B0A3",
        x"B332", x"B5C1", x"B851", x"BAE0", x"BD6F", x"BFFF", x"C28E", x"C51D", x"C7AD", x"CA3C",
        x"CCCC", x"CF5B", x"D1EA", x"D47A", x"D709", x"D998", x"DC28", x"DEB7", x"E146", x"E3D6",
        x"E665", x"E8F4", x"EB84", x"EE13", x"F0A2", x"F332", x"F5C1", x"F850", x"FAE0", x"FD6F",
        x"FFFF"
    );

    -- Test LUT: Signed version (bipolar -32768 to +32767)
    constant TEST_LUT_SIGNED : lut_101x16_signed_t := (
        to_signed(-32768, 16), to_signed(-32112, 16), to_signed(-31457, 16), to_signed(-30801, 16), to_signed(-30146, 16),
        to_signed(-29491, 16), to_signed(-28835, 16), to_signed(-28180, 16), to_signed(-27525, 16), to_signed(-26869, 16),
        to_signed(-26214, 16), to_signed(-25559, 16), to_signed(-24903, 16), to_signed(-24248, 16), to_signed(-23593, 16),
        to_signed(-22937, 16), to_signed(-22282, 16), to_signed(-21627, 16), to_signed(-20971, 16), to_signed(-20316, 16),
        to_signed(-19661, 16), to_signed(-19005, 16), to_signed(-18350, 16), to_signed(-17694, 16), to_signed(-17039, 16),
        to_signed(-16384, 16), to_signed(-15728, 16), to_signed(-15073, 16), to_signed(-14418, 16), to_signed(-13762, 16),
        to_signed(-13107, 16), to_signed(-12452, 16), to_signed(-11796, 16), to_signed(-11141, 16), to_signed(-10486, 16),
        to_signed(-9830, 16), to_signed(-9175, 16), to_signed(-8520, 16), to_signed(-7864, 16), to_signed(-7209, 16),
        to_signed(-6554, 16), to_signed(-5898, 16), to_signed(-5243, 16), to_signed(-4587, 16), to_signed(-3932, 16),
        to_signed(-3277, 16), to_signed(-2621, 16), to_signed(-1966, 16), to_signed(-1311, 16), to_signed(-655, 16),
        to_signed(0, 16), to_signed(654, 16), to_signed(1310, 16), to_signed(1965, 16), to_signed(2620, 16),
        to_signed(3276, 16), to_signed(3931, 16), to_signed(4586, 16), to_signed(5242, 16), to_signed(5897, 16),
        to_signed(6553, 16), to_signed(7208, 16), to_signed(7863, 16), to_signed(8519, 16), to_signed(9174, 16),
        to_signed(9829, 16), to_signed(10485, 16), to_signed(11140, 16), to_signed(11795, 16), to_signed(12451, 16),
        to_signed(13106, 16), to_signed(13761, 16), to_signed(14417, 16), to_signed(15072, 16), to_signed(15727, 16),
        to_signed(16383, 16), to_signed(17038, 16), to_signed(17693, 16), to_signed(18349, 16), to_signed(19004, 16),
        to_signed(19660, 16), to_signed(20315, 16), to_signed(20970, 16), to_signed(21626, 16), to_signed(22281, 16),
        to_signed(22936, 16), to_signed(23592, 16), to_signed(24247, 16), to_signed(24902, 16), to_signed(25558, 16),
        to_signed(26213, 16), to_signed(26868, 16), to_signed(27524, 16), to_signed(28179, 16), to_signed(28834, 16),
        to_signed(29490, 16), to_signed(30145, 16), to_signed(30800, 16), to_signed(31456, 16), to_signed(32111, 16),
        to_signed(32767, 16)
    );

    -- Internal signals
    signal index_natural : natural;

begin

    -- Convert test_index to natural
    index_natural <= to_integer(unsigned(test_index));

    -- Combinational logic for function testing
    process(clk, reset)
    begin
        if reset = '1' then
            lut_output_unsigned <= (others => '0');
            lut_output_signed   <= (others => '0');
            pct_index_output    <= (others => '0');
            voltage_output      <= (others => '0');
            linear_5v_lut_out   <= (others => '0');
            linear_3v3_lut_out  <= (others => '0');

        elsif rising_edge(clk) then
            -- Test lut_lookup (unsigned) with bounds checking
            if sel_lut_lookup = '1' then
                lut_output_unsigned <= lut_lookup(TEST_LUT_UNSIGNED, index_natural);
            end if;

            -- Test lut_lookup_signed with bounds checking
            if sel_lut_lookup_signed = '1' then
                lut_output_signed <= lut_lookup_signed(TEST_LUT_SIGNED, index_natural);
            end if;

            -- Test to_pct_index (clamping function)
            if sel_to_pct_index = '1' then
                -- Direct assignment (avoid signal delay)
                pct_index_output <= std_logic_vector(to_unsigned(to_pct_index(index_natural), 8));
            end if;

            -- Test voltage_to_pct_index (0-3.3V range)
            if sel_voltage_to_pct = '1' then
                -- Direct assignment (avoid signal delay)
                pct_index_output <= std_logic_vector(to_unsigned(
                    voltage_to_pct_index(
                        digital_to_voltage(test_voltage),  -- Convert to real
                        0.0,   -- Min voltage
                        3.3    -- Max voltage
                    ), 8));
            end if;

            -- Predefined LUT access (always available)
            linear_5v_lut_out  <= lut_lookup_signed(LINEAR_5V_LUT, index_natural);
            linear_3v3_lut_out <= lut_lookup_signed(LINEAR_3V3_LUT, index_natural);
        end if;
    end process;

end architecture rtl;
