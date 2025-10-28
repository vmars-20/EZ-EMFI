--------------------------------------------------------------------------------
-- FSM Observer (Fixed 6-bit encoding with optional sign-flip fault indication)
--
-- Purpose: Convert binary-encoded FSM state to oscilloscope-visible voltage.
--          Fixed 6-bit encoding allows single tested entity for all FSMs.
--          Automatic voltage spreading with optional fault sign-flip mode.
--
-- Two modes:
--   1. NO FAULTS: All states use positive voltage stairstep (V_MIN → V_MAX)
--   2. SIGN-FLIP FAULTS: Fault states flip sign of previous voltage
--
-- Sign-flip behavior: When FSM enters fault state (>= FAULT_STATE_THRESHOLD),
-- output voltage becomes NEGATIVE magnitude of the previous normal state.
--   Example: S1(0.5V) → S2(1.0V) → S3(1.5V) → FAULT → output = -1.5V
--   Magnitude preserves "where did it fault from" for debugging.
--
-- Integration:
--   - FSM uses fixed 6-bit state vector (std_logic_vector(5 downto 0))
--   - Observer watches state signal (non-invasive, parallel connection)
--   - Output connects to dedicated debug channel (e.g., OutputB)
--
-- Voltage encoding strategy:
--   - Positive voltages (stairstep up) = Normal state progression
--   - Negative voltages (sign-flip) = Fault states with historical context
--   - Zero voltage (0.0V) = Typical IDLE/ground reference
--
-- Uses: Moku_Voltage_pkg for all voltage conversions
-- Tier: 1 (Strict RTL - Verilog portable)
--
-- Author: AI-assisted design (2025-10-24)
-- Pattern: Inspectable FSM Observer
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.volo_voltage_pkg.all;

entity fsm_observer is
    generic (
        -- Number of total states (normal + fault)
        NUM_STATES : positive := 8;

        -- Voltage range for normal states
        V_MIN : real := 0.0;    -- First state voltage
        V_MAX : real := 2.5;    -- Last normal state voltage

        -- Fault configuration (set to NUM_STATES to disable faults)
        FAULT_STATE_THRESHOLD : natural := 8;  -- States >= this are faults

        -- State names for documentation/debugging (optional)
        -- Used by Python generator for trigger tables and decoders
        STATE_0_NAME : string := "STATE_0";
        STATE_1_NAME : string := "STATE_1";
        STATE_2_NAME : string := "STATE_2";
        STATE_3_NAME : string := "STATE_3";
        STATE_4_NAME : string := "STATE_4";
        STATE_5_NAME : string := "STATE_5";
        STATE_6_NAME : string := "STATE_6";
        STATE_7_NAME : string := "STATE_7"
        -- Can extend up to STATE_63_NAME if needed for larger FSMs
    );
    port (
        -- Clock/reset (only used if FAULT_STATE_THRESHOLD < NUM_STATES)
        clk          : in  std_logic := '0';
        reset        : in  std_logic := '0';  -- Active-low reset

        -- FSM state input (ALWAYS 6 bits, fixed width)
        state_vector : in  std_logic_vector(5 downto 0);

        -- Oscilloscope output (16-bit signed, Moku ±5V scale)
        voltage_out  : out signed(15 downto 0)
    );
end entity fsm_observer;

architecture rtl of fsm_observer is

    -- ========================================================================
    -- Voltage Lookup Table (LUT)
    -- ========================================================================
    -- 64-entry LUT calculated at elaboration time (zero runtime overhead)
    type voltage_lut_t is array (0 to 63) of signed(15 downto 0);

    -- Calculate voltage LUT for normal states
    -- Linear interpolation between V_MIN and V_MAX
    function calculate_voltage_lut return voltage_lut_t is
        variable lut : voltage_lut_t;
        variable v_step : real;
        variable voltage : real;
        variable num_normal : natural;
    begin
        -- Determine number of normal (non-fault) states
        if FAULT_STATE_THRESHOLD < NUM_STATES then
            num_normal := FAULT_STATE_THRESHOLD;
        else
            num_normal := NUM_STATES;  -- No fault states
        end if;

        -- Calculate voltage step between normal states
        if num_normal > 1 then
            v_step := (V_MAX - V_MIN) / real(num_normal - 1);
        else
            v_step := 0.0;
        end if;

        -- Populate LUT for normal states (linear interpolation)
        for i in 0 to num_normal-1 loop
            voltage := V_MIN + (real(i) * v_step);
            lut(i) := voltage_to_digital(voltage);
        end loop;

        -- Unused states → failsafe (0.0V)
        for i in num_normal to 63 loop
            lut(i) := VOLO_DIGITAL_ZERO;
        end loop;

        return lut;
    end function;

    -- Constant LUT (calculated once at elaboration, zero runtime overhead)
    constant VOLTAGE_LUT : voltage_lut_t := calculate_voltage_lut;

    -- ========================================================================
    -- Internal Signals
    -- ========================================================================
    signal state_index     : natural range 0 to 63;
    signal is_fault_state  : boolean;
    signal current_voltage : signed(15 downto 0);
    signal prev_voltage    : signed(15 downto 0);

begin

    -- ========================================================================
    -- State Vector Decoding
    -- ========================================================================
    -- Convert state vector to integer index
    state_index <= to_integer(unsigned(state_vector));

    -- Detect fault state
    is_fault_state <= (state_index >= FAULT_STATE_THRESHOLD);

    -- Lookup current voltage from LUT
    current_voltage <= VOLTAGE_LUT(state_index);

    -- ========================================================================
    -- Sign-Flip Fault Mode (if fault states exist)
    -- ========================================================================
    gen_with_faults: if FAULT_STATE_THRESHOLD < NUM_STATES generate
        -- Track previous non-fault voltage
        process(clk, reset)
        begin
            if reset = '0' then
                prev_voltage <= VOLO_DIGITAL_ZERO;
            elsif rising_edge(clk) then
                -- Update previous voltage only when in normal (non-fault) state
                if not is_fault_state then
                    prev_voltage <= current_voltage;
                end if;
            end if;
        end process;

        -- Output: Sign-flip when in fault state
        -- This preserves the magnitude of the voltage from the last normal state,
        -- but negates it to indicate fault condition.
        voltage_out <= -prev_voltage when is_fault_state
                       else current_voltage;
    end generate;

    -- ========================================================================
    -- No Faults Mode (all states use normal voltage)
    -- ========================================================================
    gen_no_faults: if FAULT_STATE_THRESHOLD >= NUM_STATES generate
        -- Purely combinational (no clock needed)
        voltage_out <= current_voltage;
    end generate;

end architecture rtl;
