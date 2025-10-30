--------------------------------------------------------------------------------
-- File: custom_inst_bram_loader.vhd
-- Author: Volo Team
-- Created: 2025-01-25
-- Updated: 2025-10-29 (CustomInstrument migration)
--
-- Description:
--   BRAM Loader FSM for CustomInstApp infrastructure.
--   Streams 4KB buffer data via Control Registers CR1-CR5.
--
-- Protocol (CR1-CR5):
--   Control1[0]      : Start signal (write 1 to begin loading)
--   Control1[31:16]  : Word count (number of 32-bit words to load, max 1024)
--   Control2[11:0]   : Address to write (12-bit, 0-4095 bytes / 4 = 0-1023 words)
--   Control3[31:0]   : Data to write (32-bit word)
--   Control4[0]      : Write strobe (pulse high to commit write)
--   Control5         : Reserved for future use
--
-- Usage Pattern (Python/deployment script):
--   1. Set Control1 = (word_count << 16) | 0x0001  # Start + count
--   2. For each word:
--      a. Set Control2 = address
--      b. Set Control3 = data
--      c. Set Control4 = 0x0001  # Write strobe
--      d. Set Control4 = 0x0000  # Clear strobe
--   3. Wait for 'done' signal to assert
--
-- State Machine:
--   IDLE     → Wait for Control1[0] = 1
--   LOADING  → Monitor Control4[0] for write strobes
--   DONE     → Assert done signal, wait for reset
--
-- Design Notes:
--   - Simple edge-detected write protocol (no handshaking)
--   - Assumes deployment script controls timing
--   - BRAM is always-enabled (can be accessed by app after loading)
--   - Done signal is sticky (cleared only on reset)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.custom_inst_common_pkg.all;

entity custom_inst_bram_loader is
    port (
        -- Clock and Reset
        Clk      : in  std_logic;
        Reset    : in  std_logic;  -- Active-high reset

        -- Control Registers (from MCC)
        Control1 : in  std_logic_vector(31 downto 0);  -- Start + word count
        Control2 : in  std_logic_vector(31 downto 0);  -- Address
        Control3 : in  std_logic_vector(31 downto 0);  -- Data
        Control4 : in  std_logic_vector(31 downto 0);  -- Write strobe
        Control5 : in  std_logic_vector(31 downto 0);  -- Reserved

        -- BRAM Interface (to application)
        bram_addr : out std_logic_vector(11 downto 0);  -- 4KB address space
        bram_data : out std_logic_vector(31 downto 0);  -- 32-bit data
        bram_we   : out std_logic;                      -- Write enable

        -- Status
        done      : out std_logic  -- Asserted when loading complete
    );
end entity custom_inst_bram_loader;

architecture rtl of custom_inst_bram_loader is

    -- FSM States (use std_logic_vector for Verilog portability)
    constant IDLE    : std_logic_vector(1 downto 0) := "00";
    constant LOADING : std_logic_vector(1 downto 0) := "01";
    constant DONE_ST : std_logic_vector(1 downto 0) := "10";

    signal state      : std_logic_vector(1 downto 0);
    signal next_state : std_logic_vector(1 downto 0);

    -- Control signals
    signal start_loading : std_logic;
    signal write_strobe  : std_logic;
    signal word_count    : unsigned(15 downto 0);
    signal words_written : unsigned(15 downto 0);

    -- Write strobe edge detection
    signal write_strobe_prev : std_logic;
    signal write_strobe_edge : std_logic;

    -- Done flag (sticky until reset)
    signal done_internal : std_logic;

begin

    ----------------------------------------------------------------------------
    -- Extract control signals from Control Registers
    ----------------------------------------------------------------------------
    start_loading <= Control1(0);
    word_count    <= unsigned(Control1(31 downto 16));
    write_strobe  <= Control4(0);

    ----------------------------------------------------------------------------
    -- Edge detection for write strobe (rising edge)
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            write_strobe_prev <= '0';
        elsif rising_edge(Clk) then
            write_strobe_prev <= write_strobe;
        end if;
    end process;

    write_strobe_edge <= '1' when (write_strobe = '1' and write_strobe_prev = '0') else '0';

    ----------------------------------------------------------------------------
    -- FSM: State Register
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            state <= IDLE;
        elsif rising_edge(Clk) then
            state <= next_state;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- FSM: Next State Logic
    ----------------------------------------------------------------------------
    process(state, start_loading, write_strobe_edge, words_written, word_count)
    begin
        next_state <= state;  -- Default: hold state

        case state is
            when IDLE =>
                if start_loading = '1' then
                    next_state <= LOADING;
                end if;

            when LOADING =>
                -- Check if all words have been written
                if words_written >= word_count then
                    next_state <= DONE_ST;
                end if;

            when DONE_ST =>
                -- Stay in DONE until reset
                next_state <= DONE_ST;

            when others =>
                next_state <= IDLE;
        end case;
    end process;

    ----------------------------------------------------------------------------
    -- FSM: Word Counter
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            words_written <= (others => '0');
        elsif rising_edge(Clk) then
            if state = IDLE then
                words_written <= (others => '0');
            elsif state = LOADING and write_strobe_edge = '1' then
                words_written <= words_written + 1;
            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- FSM: Done Flag (Sticky)
    ----------------------------------------------------------------------------
    process(Clk, Reset)
    begin
        if Reset = '1' then
            done_internal <= '0';
        elsif rising_edge(Clk) then
            if state = DONE_ST then
                done_internal <= '1';
            end if;
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Output Assignments
    ----------------------------------------------------------------------------

    -- BRAM address (from Control2, lower 12 bits)
    bram_addr <= Control2(11 downto 0);

    -- BRAM data (from Control3)
    bram_data <= Control3;

    -- BRAM write enable (pulse on write_strobe rising edge, only in LOADING state)
    bram_we <= '1' when (state = LOADING and write_strobe_edge = '1') else '0';

    -- Done signal (sticky)
    done <= done_internal;

end architecture rtl;
