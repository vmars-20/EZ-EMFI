-- volo_clk_divider.vhd
-- Simple reusable clock divider module with generic division range
-- Provides configurable clock division with runtime enable control
--
-- Features:
-- - Generic MAX_DIV: Configurable maximum division ratio (default 256)
-- - Enable input: Freeze/unfreeze counting
-- - div_sel encoding: 0=÷1, 1=÷2, 2=÷3, ... (simple linear mapping)
-- - Clock enable output (not divided clock - safer for timing)
-- - Status register shows current div_sel and counter state
--
-- Students: Notice how generics make this module flexible without
-- adding complexity to the logic!

library IEEE;
use IEEE.Std_Logic_1164.all;
use IEEE.Numeric_Std.all;

entity volo_clk_divider is
    generic (
        MAX_DIV : natural := 256  -- Maximum division ratio (must be power of 2)
    );
    port (
        clk         : in  std_logic;                    -- Input clock
        rst_n       : in  std_logic;                    -- Active low reset
        enable      : in  std_logic;                    -- Enable (freezes counter when low)
        div_sel     : in  std_logic_vector(7 downto 0); -- Division select (0=div1, 1=div2, ..., 255=div256)
        clk_en      : out std_logic;                    -- Clock enable output
        stat_reg    : out std_logic_vector(7 downto 0)  -- Status register
    );
end entity volo_clk_divider;

architecture rtl of volo_clk_divider is
    -- Calculate counter width based on MAX_DIV generic
    -- Students: This constant is computed at synthesis time!
    constant COUNTER_WIDTH : natural := 8;  -- Support up to 256 division

    signal counter       : unsigned(COUNTER_WIDTH-1 downto 0);
    signal div_value     : unsigned(COUNTER_WIDTH-1 downto 0);
    signal clk_en_int    : std_logic;

begin
    -- Convert div_sel to actual division value
    -- Simple linear mapping: 0→1, 1→2, 2→3, etc.
    -- Clamp to MAX_DIV to prevent overflow
    div_value <= to_unsigned(1, COUNTER_WIDTH) when unsigned(div_sel) = 0 else
                 to_unsigned(MAX_DIV, COUNTER_WIDTH) when unsigned(div_sel) > MAX_DIV else
                 unsigned(div_sel);

    -- Main clock divider process
    -- Students: Notice the control signal priority: reset > enable > functional logic
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            -- Priority 1: Reset dominates
            counter <= (others => '0');
            clk_en_int <= '0';
        elsif rising_edge(clk) then
            if enable = '1' then
                -- Priority 2: Enable gates operation

                -- Special case for divide by 1 (always enable)
                if div_sel = x"00" then
                    clk_en_int <= '1';
                    counter <= (others => '0');
                else
                    -- Normal division logic
                    if counter >= div_value - 1 then
                        counter <= (others => '0');
                        clk_en_int <= '1'; -- Pulse when counter reaches div_value
                    else
                        counter <= counter + 1;
                        clk_en_int <= '0'; -- Low rest of the time
                    end if;
                end if;
            else
                -- Enable = '0': Freeze counter, hold clk_en low
                clk_en_int <= '0';
                -- Counter holds its value (no assignment)
            end if;
        end if;
    end process;

    -- Output assignments
    clk_en <= clk_en_int;

    -- Status register: lower bits show counter state
    stat_reg <= std_logic_vector(counter(7 downto 0));

end architecture rtl;

