--------------------------------------------------------------------------------
-- File: ds1140_pd_pkg.vhd
-- Description: Constants and types for DS1140-PD EMFI probe driver
--              (Refactored version of DS1120-PD with modern architecture)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package ds1140_pd_pkg is

    ----------------------------------------------------------------------------
    -- FSM State Encodings (3-bit)
    -- States 0-7: READY, ARMED, FIRING, COOLING, DONE, TIMEDOUT, (reserved), HARDFAULT
    -- Note: 3-bit state padded to 6-bit for fsm_observer compatibility
    ----------------------------------------------------------------------------
    constant STATE_READY    : std_logic_vector(2 downto 0) := "000";
    constant STATE_ARMED    : std_logic_vector(2 downto 0) := "001";
    constant STATE_FIRING   : std_logic_vector(2 downto 0) := "010";
    constant STATE_COOLING  : std_logic_vector(2 downto 0) := "011";
    constant STATE_DONE     : std_logic_vector(2 downto 0) := "100";
    constant STATE_TIMEDOUT : std_logic_vector(2 downto 0) := "101";
    constant STATE_HARDFAULT: std_logic_vector(2 downto 0) := "111";

    ----------------------------------------------------------------------------
    -- Voltage Constants (16-bit signed, ±5V full scale)
    -- Resolution: ~305µV per bit (10V / 65536)
    ----------------------------------------------------------------------------
    constant VOLTAGE_0V          : signed(15 downto 0) := x"0000";  -- 0.0V
    constant VOLTAGE_0V5         : signed(15 downto 0) := x"0CCD";  -- 0.5V
    constant VOLTAGE_1V0         : signed(15 downto 0) := x"199A";  -- 1.0V
    constant VOLTAGE_1V5         : signed(15 downto 0) := x"2666";  -- 1.5V
    constant VOLTAGE_2V0         : signed(15 downto 0) := x"3333";  -- 2.0V
    constant TRIGGER_THRESH_2V4  : signed(15 downto 0) := x"3DCF";  -- 2.4V (default)
    constant VOLTAGE_2V5         : signed(15 downto 0) := x"4000";  -- 2.5V
    constant MAX_INTENSITY_3V0   : signed(15 downto 0) := x"4CCD";  -- 3.0V (safety limit)
    constant VOLTAGE_3V3         : signed(15 downto 0) := x"54EB";  -- 3.3V
    constant VOLTAGE_5V0         : signed(15 downto 0) := x"7FFF";  -- 5.0V (max positive)

    ----------------------------------------------------------------------------
    -- Timing Constants
    ----------------------------------------------------------------------------
    constant MAX_FIRING_CYCLES   : natural := 32;   -- Hardware limit on firing duration
    constant MIN_COOLING_CYCLES  : natural := 8;    -- Minimum cooldown period
    constant MAX_ARM_TIMEOUT     : natural := 4095; -- 12-bit counter maximum
    constant DEFAULT_FIRING_TIME : natural := 16;   -- Default firing duration
    constant DEFAULT_COOLING_TIME: natural := 16;   -- Default cooling duration

    ----------------------------------------------------------------------------
    -- Safety Limits
    ----------------------------------------------------------------------------
    constant MAX_FIRE_COUNT      : natural := 15;   -- Maximum fires per session (4-bit)
    constant MAX_SPURIOUS_COUNT  : natural := 15;   -- Maximum spurious triggers (4-bit)

    ----------------------------------------------------------------------------
    -- Helper Functions
    ----------------------------------------------------------------------------

    -- Function to clamp voltage to safe range
    function clamp_voltage(
        voltage : signed(15 downto 0);
        max_val : signed(15 downto 0)
    ) return signed;

    -- Function to extract state name (for simulation/debug)
    function state_to_string(state : std_logic_vector(2 downto 0)) return string;

end package ds1140_pd_pkg;

package body ds1140_pd_pkg is

    -- Clamp voltage to maximum safe value
    function clamp_voltage(
        voltage : signed(15 downto 0);
        max_val : signed(15 downto 0)
    ) return signed is
    begin
        if voltage > max_val then
            return max_val;
        elsif voltage < -max_val then
            return -max_val;
        else
            return voltage;
        end if;
    end function;

    -- Convert state vector to readable string (simulation only)
    function state_to_string(state : std_logic_vector(2 downto 0)) return string is
    begin
        case state is
            when STATE_READY    => return "READY";
            when STATE_ARMED    => return "ARMED";
            when STATE_FIRING   => return "FIRING";
            when STATE_COOLING  => return "COOLING";
            when STATE_DONE     => return "DONE";
            when STATE_TIMEDOUT => return "TIMEDOUT";
            when STATE_HARDFAULT=> return "HARDFAULT";
            when others         => return "UNKNOWN";
        end case;
    end function;

end package body ds1140_pd_pkg;
