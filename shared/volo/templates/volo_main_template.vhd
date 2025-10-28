--------------------------------------------------------------------------------
-- File: {{ app_name }}_volo_main.vhd
-- Generated: {{ timestamp }}
-- Generator: tools/generate_volo_app.py (template only)
--
-- Description:
--   Application logic for {{ app_name }} VoloApp.
--   MCC-agnostic interface with friendly signal names.
--
-- Layer 3 of 3-Layer VoloApp Architecture:
--   Layer 1: MCC_TOP_volo_loader.vhd (static, shared)
--   Layer 2: {{ app_name }}_volo_shim.vhd (generated, register mapping)
--   Layer 3: {{ app_name }}_volo_main.vhd (THIS FILE - hand-written logic)
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
--   - docs/VOLO_APP_DESIGN.md
--   - {{ app_name }}_app.yaml
--   - CLAUDE.md "Standard Control Signals"
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity {{ app_name }}_volo_main is
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
{% for port in friendly_ports %}
        {{ port.name }} : in  {{ port.vhdl_type }};  -- {{ port.description }}
{% endfor %}

        ------------------------------------------------------------------------
        -- BRAM Interface (Always Exposed)
        -- 4KB buffer loaded via volo_loader.py during deployment
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
        InputB  : in  signed(15 downto 0);
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0)
    );
end entity {{ app_name }}_volo_main;

architecture rtl of {{ app_name }}_volo_main is

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
    --         OutputB <= (others => '0');
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
    --                 OutputB <= (others => '0');
    --             end if;
    --         end if;
    --         -- ClkEn='0': Hold state (no updates)
    --     end if;
    -- end process;
    ----------------------------------------------------------------------------

    -- Placeholder: Remove when implementing
    OutputA <= (others => '0');
    OutputB <= (others => '0');

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
    --    - Create CocotB tests in tests/test_{{ app_name | lower }}_volo.py
    --    - Test with friendly signals directly
    --    - Simulate without MCC infrastructure
    --
    -- 4. BRAM Usage:
    --    - Loaded during deployment via volo_loader.py
    --    - Contains application-specific data (LUTs, waveforms, etc.)
    --    - Read-only after loading (typically)
    --
    -- 5. References:
    --    - CLAUDE.md: Standard control signals, coding standards
    --    - tests/README.md: CocotB testing framework
    --    - docs/VOLO_APP_DESIGN.md: Complete architecture
    ----------------------------------------------------------------------------

end architecture rtl;
