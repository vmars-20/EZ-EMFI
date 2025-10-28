--------------------------------------------------------------------------------
-- Package: volo_lut_pkg
-- Purpose: Generic 0-100 indexed lookup table infrastructure for Moku platform
-- Author: Claude Code (based on archived PercentLut_pkg concepts)
-- Date: 2025-01-28
--
-- DESIGN PHILOSOPHY:
-- Provides LUT infrastructure for COMPLEX/NON-LINEAR mappings only:
--   • Gamma correction curves
--   • Temperature compensation tables
--   • Pre-computed waveforms
--   • Calibration curves
--
-- For SIMPLE LINEAR conversions, use Moku_Pct_pkg instead (zero memory overhead).
--
-- KEY FEATURES:
-- ✓ Human-friendly 0-100 indexing (percentage-based)
-- ✓ 7-bit index type (perfect hardware fit)
-- ✓ Runtime bounds checking with saturation
-- ✓ Verilog-portable design (no records in ports)
-- ✓ Integration with volo_voltage_pkg
--
-- TYPE SAFETY MODEL:
-- • Subtypes provide naming clarity and documentation
-- • Functions provide runtime bounds enforcement
-- • Pragmatic balance between safety and usability
--
-- VERILOG CONVERSION STRATEGY:
-- • LUT types → parameter arrays or .mem files
-- • Functions → Verilog functions with same signature
-- • Subtypes → integer ranges (type checking lost, rely on naming)
-- • No records in port declarations
--
-- USAGE EXAMPLE:
--   constant LED_GAMMA : lut_101x16_t := (...);  -- Pre-computed gamma curve
--   signal brightness_pct : pct_index_t := 50;   -- 50% perceived brightness
--   signal pwm_value : std_logic_vector(15 downto 0);
--
--   pwm_value <= lut_lookup(LED_GAMMA, brightness_pct);
--
-- WHEN TO USE THIS PACKAGE:
--   1. Is mapping linear? → Use Moku_Pct_pkg (zero overhead)
--   2. Is mapping simple formula (e.g., x^2)? → Use custom function
--   3. Is mapping complex/empirical? → Use volo_lut_pkg ✓
--
-- MEMORY OVERHEAD:
--   Each LUT: 101 entries × 16-bit = 202 bytes block RAM
--   Optimization: Use constants (synthesize to ROM)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Import voltage conversion utilities
use work.volo_voltage_pkg.all;

package volo_lut_pkg is

    -- =========================================================================
    -- TYPE DEFINITIONS
    -- =========================================================================

    -- Percentage index (0-100) - 7-bit natural
    -- Provides naming clarity and runtime range validation
    subtype pct_index_t is natural range 0 to 100;

    -- Standard unsigned LUT (101 entries × 16-bit)
    -- Use for: unsigned values, PWM duty cycles, unipolar voltages (0-5V)
    type lut_101x16_t is array (0 to 100) of std_logic_vector(15 downto 0);

    -- Signed LUT variant (101 entries × 16-bit signed)
    -- Use for: bipolar voltages, offsets, corrections, signed waveforms
    type lut_101x16_signed_t is array (0 to 100) of signed(15 downto 0);

    -- =========================================================================
    -- CORE LOOKUP FUNCTIONS (with bounds checking)
    -- =========================================================================

    -- Unsigned LUT lookup with saturation
    -- Out-of-range indices clamp to nearest valid entry (0 or 100)
    -- Note: pct_index_t is a subtype of natural, so this accepts any natural value
    function lut_lookup(
        lut : lut_101x16_t;
        idx : natural  -- Using natural (pct_index_t is subtype, can't overload)
    ) return std_logic_vector;

    -- Signed LUT lookup with saturation
    function lut_lookup_signed(
        lut : lut_101x16_signed_t;
        idx : natural  -- Using natural (pct_index_t is subtype, can't overload)
    ) return signed;

    -- =========================================================================
    -- INDEX CONVERSION AND VALIDATION
    -- =========================================================================

    -- Convert std_logic_vector to pct_index_t (with clamping)
    -- Useful for mapping hardware counters to LUT indices
    function to_pct_index(slv : std_logic_vector) return pct_index_t;

    -- Convert natural to pct_index_t (with clamping)
    function to_pct_index(n : natural) return pct_index_t;

    -- Validate index is in range 0-100
    function is_valid_pct_index(idx : natural) return boolean;

    -- =========================================================================
    -- VOLTAGE INTEGRATION FUNCTIONS
    -- =========================================================================

    -- Create linear voltage LUT (uses volo_voltage_pkg conversion)
    -- Example: create_linear_voltage_lut(0.0, 3.3) → 0-100% maps to 0V-3.3V
    function create_linear_voltage_lut(
        min_voltage : real;
        max_voltage : real
    ) return lut_101x16_signed_t;

    -- Map voltage to LUT index (0-100)
    -- Example: voltage_to_pct_index(1.65, 0.0, 3.3) → 50 (50% of 3.3V range)
    function voltage_to_pct_index(
        voltage : real;
        min_voltage : real;
        max_voltage : real
    ) return pct_index_t;

    -- Map LUT index to voltage
    -- Example: pct_index_to_voltage(50, 0.0, 3.3) → 1.65
    function pct_index_to_voltage(
        idx : pct_index_t;
        min_voltage : real;
        max_voltage : real
    ) return real;

    -- =========================================================================
    -- PREDEFINED LUTS (Examples)
    -- =========================================================================

    -- Linear 0-5V LUT (for reference/testing)
    constant LINEAR_5V_LUT : lut_101x16_signed_t;

    -- Linear 0-3.3V LUT (common logic level)
    constant LINEAR_3V3_LUT : lut_101x16_signed_t;

end package volo_lut_pkg;

package body volo_lut_pkg is

    -- =========================================================================
    -- CORE LOOKUP FUNCTIONS IMPLEMENTATION
    -- =========================================================================

    function lut_lookup(
        lut : lut_101x16_t;
        idx : natural
    ) return std_logic_vector is
    begin
        -- Bounds checking with saturation
        -- Note: Accepts any natural value (including pct_index_t subtype)
        if idx > 100 then
            return lut(100);
        else
            return lut(idx);
        end if;
    end function;

    function lut_lookup_signed(
        lut : lut_101x16_signed_t;
        idx : natural
    ) return signed is
    begin
        -- Bounds checking with saturation
        -- Note: Accepts any natural value (including pct_index_t subtype)
        if idx > 100 then
            return lut(100);
        else
            return lut(idx);
        end if;
    end function;

    -- =========================================================================
    -- INDEX CONVERSION AND VALIDATION IMPLEMENTATION
    -- =========================================================================

    function to_pct_index(slv : std_logic_vector) return pct_index_t is
        variable idx : natural;
    begin
        idx := to_integer(unsigned(slv));
        if idx > 100 then
            return 100;
        else
            return idx;
        end if;
    end function;

    function to_pct_index(n : natural) return pct_index_t is
    begin
        if n > 100 then
            return 100;
        else
            return n;
        end if;
    end function;

    function is_valid_pct_index(idx : natural) return boolean is
    begin
        return (idx >= 0) and (idx <= 100);
    end function;

    -- =========================================================================
    -- VOLTAGE INTEGRATION FUNCTIONS IMPLEMENTATION
    -- =========================================================================

    function create_linear_voltage_lut(
        min_voltage : real;
        max_voltage : real
    ) return lut_101x16_signed_t is
        variable result : lut_101x16_signed_t;
        variable voltage : real;
        variable voltage_step : real;
    begin
        -- Calculate voltage step
        voltage_step := (max_voltage - min_voltage) / 100.0;

        -- Generate LUT entries
        for i in 0 to 100 loop
            voltage := min_voltage + (real(i) * voltage_step);
            result(i) := voltage_to_digital(voltage);  -- From volo_voltage_pkg
        end loop;

        return result;
    end function;

    function voltage_to_pct_index(
        voltage : real;
        min_voltage : real;
        max_voltage : real
    ) return pct_index_t is
        variable voltage_range : real;
        variable normalized : real;
        variable index : natural;
    begin
        -- Handle edge cases
        if voltage <= min_voltage then
            return 0;
        elsif voltage >= max_voltage then
            return 100;
        end if;

        -- Calculate normalized position (0.0 to 1.0)
        voltage_range := max_voltage - min_voltage;
        if voltage_range <= 0.0 then
            return 0;  -- Invalid range
        end if;

        normalized := (voltage - min_voltage) / voltage_range;

        -- Convert to index with rounding
        index := natural(normalized * 100.0 + 0.5);

        -- Clamp to valid range (safety)
        if index > 100 then
            return 100;
        else
            return index;
        end if;
    end function;

    function pct_index_to_voltage(
        idx : pct_index_t;
        min_voltage : real;
        max_voltage : real
    ) return real is
        variable voltage_range : real;
        variable normalized : real;
    begin
        -- Calculate voltage range
        voltage_range := max_voltage - min_voltage;

        -- Convert index to normalized value (0.0 to 1.0)
        normalized := real(idx) / 100.0;

        -- Calculate voltage
        return min_voltage + (normalized * voltage_range);
    end function;

    -- =========================================================================
    -- PREDEFINED LUTS IMPLEMENTATION
    -- =========================================================================

    -- Linear 0-5V LUT (Moku full range)
    constant LINEAR_5V_LUT : lut_101x16_signed_t :=
        create_linear_voltage_lut(0.0, 5.0);

    -- Linear 0-3.3V LUT (common logic level)
    constant LINEAR_3V3_LUT : lut_101x16_signed_t :=
        create_linear_voltage_lut(0.0, 3.3);

end package body volo_lut_pkg;
