--------------------------------------------------------------------------------
-- File: {{ app_name }}_custom_inst_main.vhd
-- Generated: {{ timestamp }}
-- Generator: tools/generate_custom_inst.py (template only)
--
-- Description:
--   Application logic for {{ app_name }} CustomInstApp.
--   MCC-agnostic interface with friendly signal names.
--
-- Layer 3 of 3-Layer CustomInstApp Architecture:
--   Layer 1: MCC_TOP_custom_inst_loader.vhd (static, shared)
--   Layer 2: {{ app_name }}_custom_inst_shim.vhd (generated, register mapping)
--   Layer 3: {{ app_name }}_custom_inst_main.vhd (THIS FILE - hand-written logic)
--
-- Developer Notes:
--   - This file is YOURS to edit - implement your application logic here
--   - ZERO knowledge of Control Registers (CR numbers)
--   - Work with friendly signal names only
--   - Standard control signals follow project conventions:
--       Priority: Reset > ClkEn > Enable
--   - BRAM interface is always exposed (ignore if unused)
--
-- Application Signals:
{% for port in friendly_ports %}
--   {{ port.name }}: {{ port.description }}
{% endfor %}
--
-- References:
--   - docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md
--   - {{ app_name }}_app.yaml
--   - CLAUDE.md "Standard Control Signals"
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity {{ app_name }}_custom_inst_main is
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
        -- Handshaking Protocol
        -- Signal to shim layer when register updates are safe
        ------------------------------------------------------------------------
        ready_for_updates : out std_logic;  -- To shim layer

        ------------------------------------------------------------------------
        -- Application Signals (Friendly Names)
        -- These are mapped from Control Registers by the shim layer
        ------------------------------------------------------------------------
{% for port in friendly_ports %}
        {{ port.name }} : in  {{ port.vhdl_type }};  -- {{ port.description }}
{% endfor %}

        ------------------------------------------------------------------------
        -- BRAM Interface (Always Exposed)
        -- 4KB buffer loaded via custom_inst_loader.py during deployment
        -- Ignore if your application doesn't need BRAM
        ------------------------------------------------------------------------
        bram_addr : in  std_logic_vector(11 downto 0);  -- Address (word-aligned)
        bram_data : in  std_logic_vector(31 downto 0);  -- Data
        bram_we   : in  std_logic;                      -- Write enable

        ------------------------------------------------------------------------
        -- MCC I/O (Native MCC Types)
        -- Connect to Moku platform inputs/outputs
        -- Native types: signed(15 downto 0) for all ADC/DAC channels
        ------------------------------------------------------------------------
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0){% if num_inputs >= 3 %};
        InputC  : in  signed(15 downto 0){% endif %}{% if num_inputs >= 4 %};
        InputD  : in  signed(15 downto 0){% endif %};
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0){% if num_outputs >= 3 %};
        OutputC : out signed(15 downto 0){% endif %}{% if num_outputs >= 4 %};
        OutputD : out signed(15 downto 0){% endif %}
    );
end entity {{ app_name }}_custom_inst_main;

architecture rtl of {{ app_name }}_custom_inst_main is

    ----------------------------------------------------------------------------
    -- Internal Signals
    -- TODO: Declare your internal signals here
    ----------------------------------------------------------------------------

    -- Example: Counters, FSM states, intermediate results, etc.
    -- signal counter : unsigned(31 downto 0);
    -- signal state   : std_logic_vector(1 downto 0);

    ----------------------------------------------------------------------------
    -- Constants
    -- TODO: Define your application constants here
    ----------------------------------------------------------------------------

    -- Example: FSM state encodings, thresholds, defaults
    -- constant IDLE_STATE : std_logic_vector(1 downto 0) := "00";
    -- constant MAX_COUNT  : natural := 1000;

    ----------------------------------------------------------------------------
    -- Register Update Handshaking Protocol
    --
    -- The ready_for_updates signal controls when configuration register updates
    -- are applied by the shim layer. This prevents mid-operation glitches.
    --
    -- Reference: HandShakeProtocol.md v2.0
    --
    -- PATTERN A: Always Ready (Simple Applications)
    -- Use for applications that can safely accept configuration changes anytime:
    --
    --     ready_for_updates <= '1';  -- Always accept updates
    --
    -- Suitable for:
    --   - Stateless applications (e.g., simple filters, passthrough)
    --   - Applications where config changes have no critical timing
    --   - Development/testing (accept updates freely)
    --
    -- PATTERN B: FSM-Gated (Complex Applications)
    -- Use for applications with critical timing sequences that must not be
    -- interrupted by configuration changes:
    --
    --     process(Clk)
    --     begin
    --         if rising_edge(Clk) then
    --             case fsm_state is
    --                 when IDLE | READY =>
    --                     ready_for_updates <= '1';  -- Safe to reconfigure
    --
    --                 when ARMED | ACTIVE | CLEANUP =>
    --                     ready_for_updates <= '0';  -- Lock configuration
    --             end case;
    --         end if;
    --     end process;
    --
    -- Suitable for:
    --   - EMFI probe drivers (lock config during pulse generation)
    --   - Waveform generators (lock during burst)
    --   - Time-critical state machines
    --
    -- IMPORTANT NOTES:
    --
    -- 1. Shim Behavior (automatic):
    --    - When ready='0': Shim holds previous values (gate closed)
    --    - When ready='1': Shim latches current CR values (atomic update)
    --    - All registers update together in same cycle (no partial updates)
    --
    -- 2. No Double-Latching Required:
    --    - Use friendly signals directly in your logic
    --    - They are stable between updates (held by shim process)
    --    - Example: dac_output <= intensity;  (no extra latch needed)
    --
    -- 3. Reset Behavior:
    --    - Shim loads safe defaults from YAML on reset
    --    - Your logic sees consistent values from startup
    --
    -- 4. Network Write Timing:
    --    - User writes CR6 over network → Shim sees new value immediately
    --    - If ready='0': Shim keeps outputting old value to main
    --    - If ready='1': Shim outputs new value on next clock cycle
    --    - Result: Main app never sees partial/glitched values
    --
    -- 5. Default Implementation:
    --    - Template provides Pattern A (always ready) as default
    --    - Change to Pattern B if you need critical-section protection
    ----------------------------------------------------------------------------

begin

    ----------------------------------------------------------------------------
    -- TODO: Implement Your Application Logic Here
    --
    -- Standard Control Signal Pattern:
    --
    -- process(Clk, Reset)
    -- begin
    --     if Reset = '1' then
    --         -- Reset: All outputs to safe defaults
    --         OutputA <= (others => '0');
    --         OutputB <= (others => '0');{% if num_outputs >= 3 %}
    --         OutputC <= (others => '0');{% endif %}{% if num_outputs >= 4 %}
    --         OutputD <= (others => '0');{% endif %}
    --         -- Reset internal state
    --
    --     elsif rising_edge(Clk) then
    --         if ClkEn = '1' then
    --             if Enable = '1' then
    --                 -- Normal operation: Implement functionality
    --                 -- Use friendly signals:
{% for port in friendly_ports %}
    --                 --   {{ port.name }}
{% endfor %}
    --
    --             else
    --                 -- Idle: Hold state, outputs parked
    --                 OutputA <= (others => '0');
    --                 OutputB <= (others => '0');{% if num_outputs >= 3 %}
    --                 OutputC <= (others => '0');{% endif %}{% if num_outputs >= 4 %}
    --                 OutputD <= (others => '0');{% endif %}
    --             end if;
    --         end if;
    --         -- ClkEn='0': Hold state (no updates)
    --     end if;
    -- end process;
    ----------------------------------------------------------------------------

    ----------------------------------------------------------------------------
    -- Default Handshaking Implementation
    --
    -- TODO: Customize for your application's needs
    --
    -- Default: Always ready (Pattern A)
    -- Change to FSM-gated (Pattern B) if you need to lock config during
    -- critical operations.
    ----------------------------------------------------------------------------
    ready_for_updates <= '1';  -- Default: Always accept updates

    -- TODO: If using Pattern B (FSM-gated), replace above with FSM logic:
    --
    -- process(Clk)
    -- begin
    --     if rising_edge(Clk) then
    --         case fsm_state is
    --             when IDLE | READY =>
    --                 ready_for_updates <= '1';
    --             when ARMED | ACTIVE | CLEANUP =>
    --                 ready_for_updates <= '0';
    --         end case;
    --     end if;
    -- end process;

    ----------------------------------------------------------------------------
    -- Application Outputs (Placeholder)
    --
    -- TODO: Replace these placeholders with your actual application logic
    ----------------------------------------------------------------------------

    -- Placeholder: Remove when implementing
    OutputA <= (others => '0');
    OutputB <= (others => '0');
{% if num_outputs >= 3 %}    OutputC <= (others => '0');
{% endif %}{% if num_outputs >= 4 %}    OutputD <= (others => '0');
{% endif %}

    ----------------------------------------------------------------------------
    -- Optional: BRAM Instantiation
    --
    -- If your application uses the 4KB buffer:
    --
    -- BRAM_INST: entity WORK.bram_4kb
    --     port map (
    --         clk     => Clk,
    --         we      => bram_we,
    --         addr    => bram_addr,
    --         din     => bram_data,
    --         dout    => bram_read_data
    --     );
    ----------------------------------------------------------------------------

    ----------------------------------------------------------------------------
    -- Development Tips:
    --
    -- 1. MCC-Agnostic Design:
    --    - Never reference CR numbers in this file
    --    - Use friendly signal names only
    --    - Makes code portable and testable
    --
    -- 2. Control Signal Priority:
    --    - Reset: Forces safe state (highest priority)
    --    - ClkEn: Freezes sequential logic when low
    --    - Enable: Gates functional work
    --
    -- 3. Testing:
    --    - Create CocotB tests in tests/test_{{ app_name | lower }}_custom_inst.py
    --    - Test with friendly signals directly
    --    - Simulate without MCC infrastructure
    --
    -- 4. BRAM Usage:
    --    - Loaded during deployment via custom_inst_loader.py
    --    - Contains application-specific data (LUTs, waveforms, etc.)
    --    - Read-only after loading (typically)
    --
    -- 5. References:
    --    - CLAUDE.md: Standard control signals, coding standards
    --    - tests/README.md: CocotB testing framework
    --    - docs/CUSTOM_INSTRUMENT_MIGRATION_PLAN.md: Complete architecture
    ----------------------------------------------------------------------------

end architecture rtl;
