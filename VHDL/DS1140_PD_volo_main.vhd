--------------------------------------------------------------------------------
-- File: DS1140_PD_volo_main.vhd
-- Description: Main application logic for DS1140-PD EMFI probe driver
--              (Refactored version of DS1120-PD with modern architecture)
--
-- This module integrates:
--   - FSM core (ds1120_pd_fsm) for state control (3-bit state output)
--   - Clock divider for timing control
--   - Threshold trigger for trigger detection
--   - FSM observer for debug visualization (6-bit standard compliance)
--   - Safety features (voltage clamping, timing enforcement)
--   - Three-output design (trigger, intensity, FSM debug)
--
-- Key Improvements over DS1120-PD:
--   ✓ Direct 16-bit register signals (no reconstruction needed)
--   ✓ Three outputs: OutputA (trigger), OutputB (intensity), OutputC (FSM debug)
--   ✓ Cleaner architecture (counter_16bit type eliminates high/low splits)
--   ✓ 6-bit FSM observer standard compliance (pads 3-bit FSM state)
--
-- Layer 3 of 3-Layer VoloApp Architecture:
--   Layer 1: MCC_TOP_volo_loader.vhd (static, shared)
--   Layer 2: DS1140_PD_volo_shim.vhd (generated, register mapping)
--   Layer 3: DS1140_PD_volo_main.vhd (THIS FILE - application logic)
--
-- Author: VOLO Team
-- Date: 2025-10-28
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

-- DS1140-PD package with constants and safety functions
use work.ds1140_pd_pkg.all;

entity DS1140_PD_volo_main is
    port (
        ------------------------------------------------------------------------
        -- Standard Control Signals
        -- Priority Order: Reset > ClkEn > Enable
        ------------------------------------------------------------------------
        Clk     : in  std_logic;
        Reset   : in  std_logic;  -- Active-high reset (forces safe state)
        Enable  : in  std_logic;  -- Functional enable (gates work)
        ClkEn   : in  std_logic;  -- Clock enable (freezes sequential logic)

        ------------------------------------------------------------------------
        -- Application Signals (Friendly Names)
        -- Mapped from Control Registers by shim layer
        -- SIMPLIFIED: Uses counter_16bit type for 16-bit values
        ------------------------------------------------------------------------
        arm_probe           : in  std_logic;                      -- CR20: Arm probe
        force_fire          : in  std_logic;                      -- CR21: Manual trigger
        reset_fsm           : in  std_logic;                      -- CR22: Reset FSM
        clock_divider       : in  std_logic_vector(7 downto 0);   -- CR23: Clock divider
        arm_timeout         : in  std_logic_vector(15 downto 0);  -- CR24: 16-bit timeout (NEW!)
        firing_duration     : in  std_logic_vector(7 downto 0);   -- CR25: Firing cycles
        cooling_duration    : in  std_logic_vector(7 downto 0);   -- CR26: Cooling cycles
        trigger_threshold   : in  std_logic_vector(15 downto 0);  -- CR27: 16-bit threshold (NEW!)
        intensity           : in  std_logic_vector(15 downto 0);  -- CR28: 16-bit intensity (NEW!)

        ------------------------------------------------------------------------
        -- BRAM Interface (Reserved for future use)
        ------------------------------------------------------------------------
        bram_addr : in  std_logic_vector(11 downto 0);
        bram_data : in  std_logic_vector(31 downto 0);
        bram_we   : in  std_logic;

        ------------------------------------------------------------------------
        -- MCC I/O (Native MCC Types - Three Outputs!)
        -- InputA: External trigger signal (16-bit signed ADC, ±5V)
        -- InputB: Probe current monitor (16-bit signed ADC, ±5V)
        -- OutputA: Trigger output to probe (16-bit signed DAC, ±5V)
        -- OutputB: Intensity/amplitude to probe (16-bit signed DAC, ±5V)
        -- OutputC: FSM state debug via fsm_observer (16-bit signed DAC, ±5V)
        ------------------------------------------------------------------------
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0)
    );
end entity DS1140_PD_volo_main;

architecture rtl of DS1140_PD_volo_main is

    ----------------------------------------------------------------------------
    -- Internal Signals
    ----------------------------------------------------------------------------

    -- Clock divider signals
    signal clk_div_sel      : std_logic_vector(7 downto 0);
    signal divided_clk_en   : std_logic;
    signal clk_div_status   : std_logic_vector(7 downto 0);

    -- Truncated values (FSM needs 12-bit timeout, we have 16-bit from CR24)
    signal arm_timeout_12bit : unsigned(11 downto 0);

    -- Voltage signals (direct 16-bit, no reconstruction needed!)
    signal trigger_threshold_signed : signed(15 downto 0);
    signal intensity_signed         : signed(15 downto 0);
    signal intensity_clamped        : signed(15 downto 0);

    -- Threshold trigger signals
    signal trigger_detected : std_logic;
    signal above_threshold  : std_logic;
    signal crossing_count   : unsigned(15 downto 0);

    -- FSM core signals (3-bit state from ds1120_pd_fsm)
    signal fsm_state_3bit   : std_logic_vector(2 downto 0);
    signal firing_active    : std_logic;
    signal was_triggered    : std_logic;
    signal timed_out        : std_logic;
    signal fire_count       : unsigned(3 downto 0);
    signal spurious_count   : unsigned(3 downto 0);

    -- FSM observer signals (6-bit standard compliance - CRITICAL!)
    signal fsm_state_6bit   : std_logic_vector(5 downto 0);
    signal fsm_debug_voltage: signed(15 downto 0);

    -- Output signals
    signal trigger_out      : signed(15 downto 0);
    signal intensity_out    : signed(15 downto 0);

begin

    ----------------------------------------------------------------------------
    -- Signal Conversion (MUCH simpler with counter_16bit!)
    ----------------------------------------------------------------------------

    -- Clock divider: Pad 4-bit selection to 8-bit
    clk_div_sel <= "0000" & clock_divider(3 downto 0);

    -- Arm timeout: Truncate 16-bit to 12-bit for FSM compatibility
    arm_timeout_12bit <= unsigned(arm_timeout(11 downto 0));

    -- Direct 16-bit signal assignment (no reconstruction needed!)
    trigger_threshold_signed <= signed(trigger_threshold);
    intensity_signed         <= signed(intensity);

    ----------------------------------------------------------------------------
    -- Clock Divider Instance
    -- Provides divided clock enable for FSM timing control
    ----------------------------------------------------------------------------
    U_CLK_DIV: entity work.volo_clk_divider
        generic map (
            MAX_DIV => 16  -- Max division ratio
        )
        port map (
            clk      => Clk,
            rst_n    => not Reset,
            enable   => Enable,
            div_sel  => clk_div_sel,
            clk_en   => divided_clk_en,
            stat_reg => clk_div_status
        );

    ----------------------------------------------------------------------------
    -- Threshold Trigger Instance
    -- Detects when trigger input crosses threshold
    ----------------------------------------------------------------------------
    U_TRIGGER: entity work.volo_voltage_threshold_trigger_core
        port map (
            clk            => Clk,
            reset          => Reset,
            voltage_in     => InputA,  -- MCC ADC input directly
            threshold_high => trigger_threshold_signed,
            threshold_low  => trigger_threshold_signed - x"0100",  -- Small hysteresis
            enable         => Enable,
            mode           => '0',  -- Rising edge trigger
            trigger_out    => trigger_detected,
            above_threshold => above_threshold,
            crossing_count => crossing_count
        );

    ----------------------------------------------------------------------------
    -- FSM Core Instance
    -- Reuses ds1120_pd_fsm (proven design, 3-bit state output)
    ----------------------------------------------------------------------------
    U_FSM: entity work.ds1120_pd_fsm
        port map (
            clk             => Clk,
            rst_n           => not Reset,
            enable          => Enable,
            clk_en          => divided_clk_en,
            arm_cmd         => arm_probe,
            force_fire      => force_fire,
            reset_fsm       => reset_fsm,
            delay_count     => arm_timeout_12bit,
            firing_duration => unsigned(firing_duration),
            cooling_duration => unsigned(cooling_duration),
            trigger_detected => trigger_detected,
            current_state   => fsm_state_3bit,  -- 3-bit output
            firing_active   => firing_active,
            was_triggered   => was_triggered,
            timed_out       => timed_out,
            fire_count      => fire_count,
            spurious_count  => spurious_count
        );

    ----------------------------------------------------------------------------
    -- Output Control with Safety Clamping
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            trigger_out <= (others => '0');
            intensity_out <= (others => '0');
            intensity_clamped <= (others => '0');
        elsif rising_edge(Clk) then
            if Enable = '1' then
                -- Apply safety clamping to intensity (direct 16-bit signal!)
                intensity_clamped <= clamp_voltage(intensity_signed, MAX_INTENSITY_3V0);

                -- Control outputs based on FSM state
                if firing_active = '1' then
                    -- During FIRING: output signals to probe
                    trigger_out <= trigger_threshold_signed;
                    intensity_out <= intensity_clamped;
                else
                    -- Safe state: zero outputs
                    trigger_out <= (others => '0');
                    intensity_out <= (others => '0');
                end if;
            else
                -- When disabled, force safe state
                trigger_out <= (others => '0');
                intensity_out <= (others => '0');
            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- FSM Observer for OutputC Debug
    -- CRITICAL: 6-bit FSM observer standard compliance!
    --
    -- ds1120_pd_fsm outputs 3-bit state (states 0-7)
    -- fsm_observer requires 6-bit state vector (standard interface)
    -- Solution: Zero-extend "000" & fsm_state_3bit preserves all encodings
    --
    -- State mapping:
    --   3-bit "000" → 6-bit "000000" (READY)
    --   3-bit "001" → 6-bit "000001" (ARMED)
    --   3-bit "010" → 6-bit "000010" (FIRING)
    --   3-bit "011" → 6-bit "000011" (COOLING)
    --   3-bit "100" → 6-bit "000100" (DONE)
    --   3-bit "101" → 6-bit "000101" (TIMEDOUT)
    --   3-bit "111" → 6-bit "000111" (HARDFAULT)
    ----------------------------------------------------------------------------

    -- Pad 3-bit FSM state to 6-bit for observer (CRITICAL!)
    fsm_state_6bit <= "000" & fsm_state_3bit;

    U_FSM_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,              -- 8 states (0-7)
            V_MIN => 0.0,                 -- READY = 0.0V
            V_MAX => 2.5,                 -- Last normal state
            FAULT_STATE_THRESHOLD => 7,   -- State "000111" (7) = HARDFAULT
            STATE_0_NAME => "READY",
            STATE_1_NAME => "ARMED",
            STATE_2_NAME => "FIRING",
            STATE_3_NAME => "COOLING",
            STATE_4_NAME => "DONE",
            STATE_5_NAME => "TIMEDOUT",
            STATE_6_NAME => "RESERVED",
            STATE_7_NAME => "HARDFAULT"
        )
        port map (
            clk          => Clk,
            reset        => not Reset,  -- fsm_observer expects active-low reset
            state_vector => fsm_state_6bit,  -- 6-bit input (CRITICAL!)
            voltage_out  => fsm_debug_voltage
        );

    ----------------------------------------------------------------------------
    -- Pack outputs to MCC (Three outputs)
    ----------------------------------------------------------------------------
    OutputA <= trigger_out;        -- Trigger signal to probe
    OutputB <= intensity_out;      -- Intensity/amplitude to probe
    OutputC <= fsm_debug_voltage;  -- FSM state debug (fsm_observer)

    ----------------------------------------------------------------------------
    -- BRAM Reserved for Future Use
    -- Could store:
    --   - Waveform patterns for shaped pulses
    --   - Calibration data
    --   - Timing sequence tables
    --   - Multi-shot patterns
    ----------------------------------------------------------------------------

end architecture rtl;
