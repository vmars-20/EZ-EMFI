--------------------------------------------------------------------------------
-- File: ds1120_pd_fsm.vhd
-- Description: FSM core for DS1120-PD EMFI probe driver
--
-- This module implements the state machine logic for controlling the
-- Riscure DS1120A EMFI probe with safety features and timing control.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

use work.ds1120_pd_pkg.all;

entity ds1120_pd_fsm is
    port (
        -- Clock and control
        clk         : in  std_logic;
        rst_n       : in  std_logic;  -- Active-low reset
        enable      : in  std_logic;
        clk_en      : in  std_logic;

        -- Control inputs
        arm_cmd     : in  std_logic;
        force_fire  : in  std_logic;
        reset_fsm   : in  std_logic;

        -- Configuration
        delay_count     : in  unsigned(11 downto 0);  -- Armed timeout
        firing_duration : in  unsigned(7 downto 0);   -- Firing time
        cooling_duration: in  unsigned(7 downto 0);   -- Cooling time

        -- Trigger detection
        trigger_detected: in  std_logic;

        -- FSM outputs
        current_state   : out std_logic_vector(2 downto 0);
        firing_active   : out std_logic;  -- High during FIRING state

        -- Status flags
        was_triggered   : out std_logic;  -- Sticky: probe triggered
        timed_out       : out std_logic;  -- Sticky: armed timeout
        fire_count      : out unsigned(3 downto 0);
        spurious_count  : out unsigned(3 downto 0)
    );
end entity ds1120_pd_fsm;

architecture rtl of ds1120_pd_fsm is

    -- FSM signals
    signal state_reg     : std_logic_vector(2 downto 0);
    signal state_next    : std_logic_vector(2 downto 0);

    -- Timing counters
    signal arm_timeout_cnt  : unsigned(11 downto 0);
    signal firing_cnt       : unsigned(7 downto 0);
    signal cooling_cnt      : unsigned(7 downto 0);

    -- Status registers
    signal triggered_reg    : std_logic;
    signal timeout_reg      : std_logic;
    signal fire_cnt_reg     : unsigned(3 downto 0);
    signal spurious_cnt_reg : unsigned(3 downto 0);

    -- Internal control
    signal firing_active_int: std_logic;

begin

    ----------------------------------------------------------------------------
    -- State Register Process
    ----------------------------------------------------------------------------
    STATE_REG_PROC: process(clk, rst_n)
    begin
        if rst_n = '0' then
            state_reg <= STATE_READY;
        elsif rising_edge(clk) then
            if clk_en = '1' and enable = '1' then
                state_reg <= state_next;
            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Next State Logic
    ----------------------------------------------------------------------------
    NEXT_STATE_PROC: process(state_reg, arm_cmd, force_fire, reset_fsm,
                              trigger_detected, arm_timeout_cnt, firing_cnt,
                              cooling_cnt)
    begin
        -- Default: stay in current state
        state_next <= state_reg;

        case state_reg is

            when STATE_READY =>
                if arm_cmd = '1' then
                    state_next <= STATE_ARMED;
                end if;

            when STATE_ARMED =>
                if force_fire = '1' or trigger_detected = '1' then
                    state_next <= STATE_FIRING;
                elsif arm_timeout_cnt = 0 then
                    state_next <= STATE_TIMEDOUT;
                end if;

            when STATE_FIRING =>
                if firing_cnt = 0 then
                    state_next <= STATE_COOLING;
                end if;

            when STATE_COOLING =>
                if cooling_cnt = 0 then
                    state_next <= STATE_DONE;
                end if;

            when STATE_DONE =>
                if reset_fsm = '1' then
                    state_next <= STATE_READY;
                end if;

            when STATE_TIMEDOUT =>
                if reset_fsm = '1' then
                    state_next <= STATE_READY;
                end if;

            when STATE_HARDFAULT =>
                if reset_fsm = '1' then
                    state_next <= STATE_READY;
                end if;

            when others =>
                state_next <= STATE_READY;

        end case;
    end process;

    ----------------------------------------------------------------------------
    -- Counter Management Process
    ----------------------------------------------------------------------------
    COUNTER_PROC: process(clk, rst_n)
    begin
        if rst_n = '0' then
            arm_timeout_cnt <= (others => '0');
            firing_cnt <= (others => '0');
            cooling_cnt <= (others => '0');
        elsif rising_edge(clk) then
            if clk_en = '1' and enable = '1' then

                -- Armed timeout counter
                if state_reg = STATE_READY and state_next = STATE_ARMED then
                    arm_timeout_cnt <= delay_count;
                elsif state_reg = STATE_ARMED and arm_timeout_cnt > 0 then
                    arm_timeout_cnt <= arm_timeout_cnt - 1;
                end if;

                -- Firing duration counter
                if state_reg = STATE_ARMED and state_next = STATE_FIRING then
                    -- Clamp to maximum firing cycles
                    if firing_duration > MAX_FIRING_CYCLES then
                        firing_cnt <= to_unsigned(MAX_FIRING_CYCLES, 8);
                    else
                        firing_cnt <= firing_duration;
                    end if;
                elsif state_reg = STATE_FIRING and firing_cnt > 0 then
                    firing_cnt <= firing_cnt - 1;
                end if;

                -- Cooling duration counter
                if state_reg = STATE_FIRING and state_next = STATE_COOLING then
                    -- Enforce minimum cooling cycles
                    if cooling_duration < MIN_COOLING_CYCLES then
                        cooling_cnt <= to_unsigned(MIN_COOLING_CYCLES, 8);
                    else
                        cooling_cnt <= cooling_duration;
                    end if;
                elsif state_reg = STATE_COOLING and cooling_cnt > 0 then
                    cooling_cnt <= cooling_cnt - 1;
                end if;

            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Status Flags Process
    ----------------------------------------------------------------------------
    STATUS_PROC: process(clk, rst_n)
    begin
        if rst_n = '0' then
            triggered_reg <= '0';
            timeout_reg <= '0';
            fire_cnt_reg <= (others => '0');
            spurious_cnt_reg <= (others => '0');
        elsif rising_edge(clk) then
            if clk_en = '1' and enable = '1' then

                -- Set triggered flag when entering FIRING state
                if state_reg = STATE_ARMED and state_next = STATE_FIRING then
                    triggered_reg <= '1';
                end if;

                -- Set timeout flag when entering TIMEDOUT state
                if state_reg = STATE_ARMED and state_next = STATE_TIMEDOUT then
                    timeout_reg <= '1';
                end if;

                -- Increment fire count when completing a firing cycle
                if state_reg = STATE_FIRING and state_next = STATE_COOLING then
                    if fire_cnt_reg < "1111" then
                        fire_cnt_reg <= fire_cnt_reg + 1;
                    end if;
                end if;

                -- Clear sticky flags on FSM reset
                if reset_fsm = '1' and state_reg = STATE_READY then
                    triggered_reg <= '0';
                    timeout_reg <= '0';
                    -- Note: fire_cnt_reg is NOT cleared (session counter)
                end if;

                -- Count spurious triggers (trigger detected when not armed)
                if trigger_detected = '1' and state_reg /= STATE_ARMED then
                    if spurious_cnt_reg < "1111" then
                        spurious_cnt_reg <= spurious_cnt_reg + 1;
                    end if;
                end if;

            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Output Assignments
    ----------------------------------------------------------------------------
    current_state <= state_reg;
    firing_active_int <= '1' when state_reg = STATE_FIRING else '0';
    firing_active <= firing_active_int;
    was_triggered <= triggered_reg;
    timed_out <= timeout_reg;
    fire_count <= fire_cnt_reg;
    spurious_count <= spurious_cnt_reg;

end architecture rtl;