--------------------------------------------------------------------------------
-- File: DS1120_PD_volo_main.vhd
-- Description: Main application logic for DS1120-PD EMFI probe driver
--
-- This module integrates:
--   - FSM core (ds1120_pd_fsm) for state control
--   - Clock divider for timing control
--   - Threshold trigger for trigger detection
--   - FSM observer for debug visualization
--   - Safety features (voltage clamping, timing enforcement)
--
-- Layer 3 of 3-Layer VoloApp Architecture:
--   Layer 1: MCC_TOP_volo_loader.vhd (static, shared)
--   Layer 2: DS1120-PD_volo_shim.vhd (generated, register mapping)
--   Layer 3: DS1120-PD_volo_main.vhd (THIS FILE - application logic)
--
-- Author: VOLO Team
-- Date: 2025-01-27
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

-- DS1120-PD package with constants
use work.ds1120_pd_pkg.all;

entity DS1120_PD_volo_main is
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
        -- These are mapped from Control Registers by the shim layer
        ------------------------------------------------------------------------
        armed               : in  std_logic;  -- Arm the probe driver
        force_fire          : in  std_logic;  -- Manual trigger
        reset_fsm           : in  std_logic;  -- Reset state machine
        timing_control      : in  std_logic_vector(7 downto 0);  -- [7:4]=clk_div, [3:0]=delay_upper
        delay_lower         : in  std_logic_vector(7 downto 0);  -- Delay lower 8 bits
        firing_duration     : in  std_logic_vector(7 downto 0);  -- Firing cycles
        cooling_duration    : in  std_logic_vector(7 downto 0);  -- Cooling cycles
        trigger_thresh_high : in  std_logic_vector(7 downto 0);  -- Threshold [15:8]
        trigger_thresh_low  : in  std_logic_vector(7 downto 0);  -- Threshold [7:0]
        intensity_high      : in  std_logic_vector(7 downto 0);  -- Intensity [15:8]
        intensity_low       : in  std_logic_vector(7 downto 0);  -- Intensity [7:0]

        ------------------------------------------------------------------------
        -- BRAM Interface (Reserved for future use)
        ------------------------------------------------------------------------
        bram_addr : in  std_logic_vector(11 downto 0);
        bram_data : in  std_logic_vector(31 downto 0);
        bram_we   : in  std_logic;

        ------------------------------------------------------------------------
        -- MCC I/O (Native MCC Types)
        -- InputA: External trigger signal (signed 16-bit ADC)
        -- InputB: Probe current monitor (signed 16-bit ADC)
        -- OutputA: Trigger output to probe (signed 16-bit DAC)
        -- OutputB: Intensity/debug output (signed 16-bit DAC)
        ------------------------------------------------------------------------
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0)
    );
end entity DS1120_PD_volo_main;

architecture rtl of DS1120_PD_volo_main is

    ----------------------------------------------------------------------------
    -- Internal Signals
    ----------------------------------------------------------------------------

    -- Clock divider signals
    signal clk_div_sel      : std_logic_vector(7 downto 0);
    signal divided_clk_en   : std_logic;
    signal clk_div_status   : std_logic_vector(7 downto 0);

    -- 16-bit reconstructed values
    signal trigger_threshold : signed(15 downto 0);
    signal intensity_value   : signed(15 downto 0);
    signal intensity_clamped : signed(15 downto 0);
    signal arm_timeout      : unsigned(11 downto 0);

    -- Threshold trigger signals
    signal trigger_detected : std_logic;
    signal above_threshold  : std_logic;
    signal crossing_count   : unsigned(15 downto 0);

    -- FSM core signals
    signal fsm_state        : std_logic_vector(2 downto 0);
    signal firing_active    : std_logic;
    signal was_triggered    : std_logic;
    signal timed_out        : std_logic;
    signal fire_count       : unsigned(3 downto 0);
    signal spurious_count   : unsigned(3 downto 0);

    -- Output signals
    signal trigger_out      : signed(15 downto 0);
    signal intensity_out    : signed(15 downto 0);

    -- FSM observer signals
    signal fsm_state_6bit   : std_logic_vector(5 downto 0);
    signal debug_voltage    : signed(15 downto 0);

    -- Status register
    signal status_reg       : std_logic_vector(15 downto 0);

begin

    ----------------------------------------------------------------------------
    -- Signal Reconstruction
    ----------------------------------------------------------------------------

    -- Extract clock divider selection from timing control
    clk_div_sel <= "0000" & timing_control(7 downto 4);  -- 4-bit selection

    -- Reconstruct 12-bit arm timeout value
    arm_timeout <= unsigned(timing_control(3 downto 0) & delay_lower);

    -- Reconstruct 16-bit threshold and intensity values
    trigger_threshold <= signed(trigger_thresh_high & trigger_thresh_low);
    intensity_value   <= signed(intensity_high & intensity_low);

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
            threshold_high => trigger_threshold,
            threshold_low  => trigger_threshold - x"0100",  -- Small hysteresis
            enable         => Enable,
            mode           => '0',  -- Rising edge trigger
            trigger_out    => trigger_detected,
            above_threshold => above_threshold,
            crossing_count => crossing_count
        );

    ----------------------------------------------------------------------------
    -- FSM Core Instance
    -- Main state machine for probe control
    ----------------------------------------------------------------------------
    U_FSM: entity work.ds1120_pd_fsm
        port map (
            clk             => Clk,
            rst_n           => not Reset,
            enable          => Enable,
            clk_en          => divided_clk_en,
            arm_cmd         => armed,
            force_fire      => force_fire,
            reset_fsm       => reset_fsm,
            delay_count     => arm_timeout,
            firing_duration => unsigned(firing_duration),
            cooling_duration => unsigned(cooling_duration),
            trigger_detected => trigger_detected,
            current_state   => fsm_state,
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
                -- Apply safety clamping to intensity
                intensity_clamped <= clamp_voltage(intensity_value, MAX_INTENSITY_3V0);

                -- Control outputs based on FSM state
                if firing_active = '1' then
                    -- During firing: output trigger threshold and clamped intensity
                    trigger_out <= trigger_threshold;
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
    -- FSM Observer for Debug Visualization
    -- Maps 3-bit FSM state to oscilloscope-visible voltage
    ----------------------------------------------------------------------------

    -- Pad 3-bit state to 6-bit for observer
    fsm_state_6bit <= "000" & fsm_state;

    U_OBSERVER: entity work.fsm_observer
        generic map (
            NUM_STATES => 8,
            V_MIN => 0.0,
            V_MAX => 2.5,
            FAULT_STATE_THRESHOLD => 7,  -- State 111 is fault
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
            reset        => not Reset,
            state_vector => fsm_state_6bit,
            voltage_out  => debug_voltage
        );

    ----------------------------------------------------------------------------
    -- Status Register Assembly
    ----------------------------------------------------------------------------
    status_reg(15 downto 13) <= fsm_state;              -- Current FSM state
    status_reg(12)           <= was_triggered;          -- Probe was triggered
    status_reg(11)           <= timed_out;              -- Armed timeout occurred
    status_reg(10)           <= '1' when fire_count = "1111" else '0';  -- Max fires reached
    status_reg(9 downto 8)   <= "00";                   -- Reserved
    status_reg(7 downto 4)   <= std_logic_vector(spurious_count);  -- Spurious triggers
    status_reg(3 downto 0)   <= std_logic_vector(fire_count);       -- Fire count

    ----------------------------------------------------------------------------
    -- Pack outputs to MCC format
    ----------------------------------------------------------------------------

    -- OutputA: Trigger output to probe (native MCC DAC type)
    OutputA <= trigger_out;

    -- OutputB: Intensity output OR debug voltage (selectable)
    -- For normal operation: intensity_out
    -- For debug: debug_voltage from FSM observer
    OutputB <= debug_voltage;  -- Use debug output

    ----------------------------------------------------------------------------
    -- BRAM Reserved for Future Use
    -- Could store:
    --   - Waveform patterns for shaped pulses
    --   - Calibration data
    --   - Timing sequence tables
    --   - Multi-shot patterns
    ----------------------------------------------------------------------------

end architecture rtl;