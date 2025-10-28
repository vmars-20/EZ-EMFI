--------------------------------------------------------------------------------
-- Package: volo_voltage_pkg
-- Purpose: Platform-independent voltage conversion utilities for ADC/DAC interfaces
-- Author: johnnyc
-- Date: 2025-01-27
-- 
-- DATADEF PACKAGE: This package provides voltage conversion utilities for
-- 16-bit signed ADC/DAC interfaces. Designed for maximum Verilog compatibility
-- and testbench convenience.
--
-- VOLTAGE SPECIFICATION:
-- - Digital range: -32768 to +32767 (0x8000 to 0x7FFF)
-- - Voltage range: -5.0V to +5.0V (full-scale analog input/output)
-- - Resolution: ~305 µV per digital step (10V / 65536)
-- 
-- VERILOG CONVERSION STRATEGY:
-- - All functions use standard types (signed, std_logic_vector, natural)
-- - No records or complex types in function interfaces
-- - Constants can be directly translated to Verilog parameters
-- - Function overloading uses different parameter types for clarity
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package volo_voltage_pkg is

    -- =============================================================================
    -- VOLTAGE SYSTEM CONSTANTS (16-bit signed, ±5V full scale)
    -- =============================================================================

    -- Digital range constants (16-bit signed)
    constant VOLO_DIGITAL_MIN : signed(15 downto 0) := to_signed(-32768, 16);  -- 0x8000
    constant VOLO_DIGITAL_MAX : signed(15 downto 0) := to_signed(32767, 16);   -- 0x7FFF
    constant VOLO_DIGITAL_ZERO : signed(15 downto 0) := to_signed(0, 16);      -- 0x0000

    -- Voltage range constants (real values in volts)
    constant VOLO_VOLTAGE_MIN : real := -5.0;
    constant VOLO_VOLTAGE_MAX : real := 5.0;
    constant VOLO_VOLTAGE_ZERO : real := 0.0;
    
    -- Resolution and scaling constants
    constant VOLO_VOLTAGE_RESOLUTION : real := 10.0 / 65536.0;  -- ~305.18 µV per step
    constant VOLO_DIGITAL_SCALE_FACTOR : real := 32767.0 / 5.0;  -- 6553.4 digital units per volt
    
    -- Common voltage reference points (from Moku-Voltage-LUTS.md)
    constant VOLO_VOLTAGE_1V : real := 1.0;
    constant VOLO_VOLTAGE_2V4 : real := 2.4;
    constant VOLO_VOLTAGE_2V5 : real := 2.5;
    constant VOLO_VOLTAGE_3V : real := 3.0;
    constant VOLO_VOLTAGE_3V3 : real := 3.3;
    constant VOLO_VOLTAGE_5V : real := 5.0;
    
    -- Corresponding digital values for common voltages
    constant VOLO_DIGITAL_1V : signed(15 downto 0) := to_signed(6554, 16);    -- 0x199A
    constant VOLO_DIGITAL_2V4 : signed(15 downto 0) := to_signed(15729, 16);  -- 0x3DCF
    constant VOLO_DIGITAL_2V5 : signed(15 downto 0) := to_signed(16384, 16);  -- 0x4000
    constant VOLO_DIGITAL_3V : signed(15 downto 0) := to_signed(19661, 16);   -- 0x4CCD
    constant VOLO_DIGITAL_3V3 : signed(15 downto 0) := to_signed(21627, 16);  -- 0x54EB
    constant VOLO_DIGITAL_5V : signed(15 downto 0) := to_signed(32767, 16);   -- 0x7FFF
    
    -- Negative voltage digital values
    constant VOLO_DIGITAL_NEG_1V : signed(15 downto 0) := to_signed(-6554, 16);    -- 0xE666
    constant VOLO_DIGITAL_NEG_2V4 : signed(15 downto 0) := to_signed(-15729, 16);  -- 0xC231
    constant VOLO_DIGITAL_NEG_2V5 : signed(15 downto 0) := to_signed(-16384, 16);  -- 0xC000
    constant VOLO_DIGITAL_NEG_3V : signed(15 downto 0) := to_signed(-19661, 16);   -- 0xB333
    constant VOLO_DIGITAL_NEG_3V3 : signed(15 downto 0) := to_signed(-21627, 16);  -- 0xAA85
    constant VOLO_DIGITAL_NEG_5V : signed(15 downto 0) := to_signed(-32768, 16);   -- 0x8000
    
    -- =============================================================================
    -- VOLTAGE CONVERSION FUNCTIONS
    -- =============================================================================
    
    -- Convert voltage (real) to digital value (signed 16-bit)
    function voltage_to_digital(voltage : real) return signed;
    
    -- Convert digital value (signed 16-bit) to voltage (real)
    function digital_to_voltage(digital : signed(15 downto 0)) return real;
    
    -- Convert digital value (std_logic_vector) to voltage (real)
    function digital_to_voltage(digital : std_logic_vector(15 downto 0)) return real;
    
    -- Convert voltage (real) to digital value (std_logic_vector)
    function voltage_to_digital_vector(voltage : real) return std_logic_vector;
    
    -- =============================================================================
    -- TESTBENCH CONVENIENCE FUNCTIONS
    -- =============================================================================
    
    -- Check if digital value represents a specific voltage within tolerance
    function is_voltage_equal(digital : signed(15 downto 0); expected_voltage : real; tolerance_volts : real := 0.001) return boolean;
    function is_voltage_equal(digital : std_logic_vector(15 downto 0); expected_voltage : real; tolerance_volts : real := 0.001) return boolean;
    
    -- Check if digital value is within voltage range
    function is_voltage_in_range(digital : signed(15 downto 0); min_voltage : real; max_voltage : real) return boolean;
    function is_voltage_in_range(digital : std_logic_vector(15 downto 0); min_voltage : real; max_voltage : real) return boolean;
    
    -- Get voltage difference between expected and actual
    function get_voltage_error(digital : signed(15 downto 0); expected_voltage : real) return real;
    function get_voltage_error(digital : std_logic_vector(15 downto 0); expected_voltage : real) return real;
    
    -- =============================================================================
    -- VALIDATION FUNCTIONS
    -- =============================================================================
    
    -- Check if digital value is within valid Moku range
    function is_valid_moku_digital(digital : signed(15 downto 0)) return boolean;
    function is_valid_moku_digital(digital : std_logic_vector(15 downto 0)) return boolean;
    
    -- Check if voltage is within valid Moku range
    function is_valid_moku_voltage(voltage : real) return boolean;
    
    -- Clamp digital value to valid Moku range
    function clamp_moku_digital(digital : signed(15 downto 0)) return signed;
    function clamp_moku_digital(digital : std_logic_vector(15 downto 0)) return std_logic_vector;
    
    -- Clamp voltage to valid Moku range
    function clamp_moku_voltage(voltage : real) return real;
    
    -- =============================================================================
    -- UTILITY FUNCTIONS
    -- =============================================================================
    
    -- Convert digital value to string for debugging
    function digital_to_string(digital : signed(15 downto 0)) return string;
    function digital_to_string(digital : std_logic_vector(15 downto 0)) return string;
    
    -- Convert voltage to string for debugging
    function voltage_to_string(voltage : real; precision : natural := 3) return string;
    
    -- Get the digital step size for a given voltage range
    function get_voltage_step_size(voltage_range : real) return real;
    
    -- Calculate the number of digital steps between two voltages
    function get_digital_steps_between(min_voltage : real; max_voltage : real) return natural;
    
end package volo_voltage_pkg;

package body volo_voltage_pkg is
    
    -- =============================================================================
    -- VOLTAGE CONVERSION FUNCTIONS
    -- =============================================================================
    
    function voltage_to_digital(voltage : real) return signed is
        variable digital_real : real;
        variable digital_int : integer;
    begin
        -- Clamp voltage to valid range
        if voltage > VOLO_VOLTAGE_MAX then
            digital_real := VOLO_VOLTAGE_MAX * VOLO_DIGITAL_SCALE_FACTOR;
        elsif voltage < VOLO_VOLTAGE_MIN then
            digital_real := VOLO_VOLTAGE_MIN * VOLO_DIGITAL_SCALE_FACTOR;
        else
            digital_real := voltage * VOLO_DIGITAL_SCALE_FACTOR;
        end if;
        
        -- Convert to integer with proper rounding (round towards zero for negative values)
        if digital_real >= 0.0 then
            digital_int := integer(digital_real + 0.5);
        else
            digital_int := integer(digital_real - 0.5);
        end if;
        
        if digital_int > 32767 then
            digital_int := 32767;
        elsif digital_int < -32768 then
            digital_int := -32768;
        end if;
        
        return to_signed(digital_int, 16);
    end function;
    
    function digital_to_voltage(digital : signed(15 downto 0)) return real is
    begin
        return real(to_integer(digital)) / VOLO_DIGITAL_SCALE_FACTOR;
    end function;
    
    function digital_to_voltage(digital : std_logic_vector(15 downto 0)) return real is
    begin
        return digital_to_voltage(signed(digital));
    end function;
    
    function voltage_to_digital_vector(voltage : real) return std_logic_vector is
    begin
        return std_logic_vector(voltage_to_digital(voltage));
    end function;
    
    -- =============================================================================
    -- TESTBENCH CONVENIENCE FUNCTIONS
    -- =============================================================================
    
    function is_voltage_equal(digital : signed(15 downto 0); expected_voltage : real; tolerance_volts : real := 0.001) return boolean is
        variable actual_voltage : real;
        variable voltage_diff : real;
    begin
        actual_voltage := digital_to_voltage(digital);
        voltage_diff := abs(actual_voltage - expected_voltage);
        return (voltage_diff <= tolerance_volts);
    end function;
    
    function is_voltage_equal(digital : std_logic_vector(15 downto 0); expected_voltage : real; tolerance_volts : real := 0.001) return boolean is
    begin
        return is_voltage_equal(signed(digital), expected_voltage, tolerance_volts);
    end function;
    
    function is_voltage_in_range(digital : signed(15 downto 0); min_voltage : real; max_voltage : real) return boolean is
        variable actual_voltage : real;
    begin
        actual_voltage := digital_to_voltage(digital);
        return (actual_voltage >= min_voltage) and (actual_voltage <= max_voltage);
    end function;
    
    function is_voltage_in_range(digital : std_logic_vector(15 downto 0); min_voltage : real; max_voltage : real) return boolean is
    begin
        return is_voltage_in_range(signed(digital), min_voltage, max_voltage);
    end function;
    
    function get_voltage_error(digital : signed(15 downto 0); expected_voltage : real) return real is
        variable actual_voltage : real;
    begin
        actual_voltage := digital_to_voltage(digital);
        return actual_voltage - expected_voltage;
    end function;
    
    function get_voltage_error(digital : std_logic_vector(15 downto 0); expected_voltage : real) return real is
    begin
        return get_voltage_error(signed(digital), expected_voltage);
    end function;
    
    -- =============================================================================
    -- VALIDATION FUNCTIONS
    -- =============================================================================
    
    function is_valid_moku_digital(digital : signed(15 downto 0)) return boolean is
    begin
        return (digital >= VOLO_DIGITAL_MIN) and (digital <= VOLO_DIGITAL_MAX);
    end function;
    
    function is_valid_moku_digital(digital : std_logic_vector(15 downto 0)) return boolean is
    begin
        return is_valid_moku_digital(signed(digital));
    end function;
    
    function is_valid_moku_voltage(voltage : real) return boolean is
    begin
        return (voltage >= VOLO_VOLTAGE_MIN) and (voltage <= VOLO_VOLTAGE_MAX);
    end function;
    
    function clamp_moku_digital(digital : signed(15 downto 0)) return signed is
    begin
        if digital > VOLO_DIGITAL_MAX then
            return VOLO_DIGITAL_MAX;
        elsif digital < VOLO_DIGITAL_MIN then
            return VOLO_DIGITAL_MIN;
        else
            return digital;
        end if;
    end function;
    
    function clamp_moku_digital(digital : std_logic_vector(15 downto 0)) return std_logic_vector is
    begin
        return std_logic_vector(clamp_moku_digital(signed(digital)));
    end function;
    
    function clamp_moku_voltage(voltage : real) return real is
    begin
        if voltage > VOLO_VOLTAGE_MAX then
            return VOLO_VOLTAGE_MAX;
        elsif voltage < VOLO_VOLTAGE_MIN then
            return VOLO_VOLTAGE_MIN;
        else
            return voltage;
        end if;
    end function;
    
    -- =============================================================================
    -- UTILITY FUNCTIONS
    -- =============================================================================
    
    function digital_to_string(digital : signed(15 downto 0)) return string is
        variable temp : integer;
    begin
        temp := to_integer(digital);
        if temp < 0 then
            return "0x" & to_hstring(std_logic_vector(digital)) & " (" & integer'image(temp) & ")";
        else
            return "0x" & to_hstring(std_logic_vector(digital)) & " (+" & integer'image(temp) & ")";
        end if;
    end function;
    
    function digital_to_string(digital : std_logic_vector(15 downto 0)) return string is
    begin
        return digital_to_string(signed(digital));
    end function;
    
    function voltage_to_string(voltage : real; precision : natural := 3) return string is
        variable temp : real;
        variable int_part : integer;
        variable frac_part : integer;
    begin
        temp := abs(voltage);
        int_part := integer(temp);
        frac_part := integer((temp - real(int_part)) * (10.0 ** precision));
        
        if voltage < 0.0 then
            return "-" & integer'image(int_part) & "." & integer'image(frac_part) & "V";
        else
            return "+" & integer'image(int_part) & "." & integer'image(frac_part) & "V";
        end if;
    end function;
    
    function get_voltage_step_size(voltage_range : real) return real is
    begin
        return voltage_range / 65536.0;
    end function;
    
    function get_digital_steps_between(min_voltage : real; max_voltage : real) return natural is
        variable min_digital : signed(15 downto 0);
        variable max_digital : signed(15 downto 0);
    begin
        min_digital := voltage_to_digital(min_voltage);
        max_digital := voltage_to_digital(max_voltage);
        return natural(to_integer(max_digital - min_digital));
    end function;
    
end package body volo_voltage_pkg;