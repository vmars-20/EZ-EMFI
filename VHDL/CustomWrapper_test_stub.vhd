-- ###########################################################################
-- # CustomWrapper Entity Stub for CocotB Testing
-- #
-- # This stub replicates the MCC-provided CustomWrapper entity interface
-- # for use in CocotB testbenches where MCC is not available.
-- #
-- # For production builds, MCC provides the actual entity declaration via
-- # mcc_templates/mcc-Top.vhd, and module-specific architectures are in
-- # modules/<module>/top/Top.vhd
-- #
-- # Source: Based on mcc_build_pattern Serena memory
-- # Date: 2025-10-22
-- ###########################################################################

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity CustomWrapper is
    port (
        -- Clock and Reset
        Clk     : in  std_logic;
        Reset   : in  std_logic;

        -- Input signals (ADC data, signed 16-bit)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        InputC  : in  signed(15 downto 0);
        InputD  : in  signed(15 downto 0);

        -- Output signals (DAC data, signed 16-bit)
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0);
        OutputD : out signed(15 downto 0);

        -- Control registers (32-bit each, from Moku platform)
        -- Note: std_logic_vector, NOT signed!
        -- Total: 32 registers (Control0-31)
        Control0  : in  std_logic_vector(31 downto 0);
        Control1  : in  std_logic_vector(31 downto 0);
        Control2  : in  std_logic_vector(31 downto 0);
        Control3  : in  std_logic_vector(31 downto 0);
        Control4  : in  std_logic_vector(31 downto 0);
        Control5  : in  std_logic_vector(31 downto 0);
        Control6  : in  std_logic_vector(31 downto 0);
        Control7  : in  std_logic_vector(31 downto 0);
        Control8  : in  std_logic_vector(31 downto 0);
        Control9  : in  std_logic_vector(31 downto 0);
        Control10 : in  std_logic_vector(31 downto 0);
        Control11 : in  std_logic_vector(31 downto 0);
        Control12 : in  std_logic_vector(31 downto 0);
        Control13 : in  std_logic_vector(31 downto 0);
        Control14 : in  std_logic_vector(31 downto 0);
        Control15 : in  std_logic_vector(31 downto 0);
        Control16 : in  std_logic_vector(31 downto 0);
        Control17 : in  std_logic_vector(31 downto 0);
        Control18 : in  std_logic_vector(31 downto 0);
        Control19 : in  std_logic_vector(31 downto 0);
        Control20 : in  std_logic_vector(31 downto 0);
        Control21 : in  std_logic_vector(31 downto 0);
        Control22 : in  std_logic_vector(31 downto 0);
        Control23 : in  std_logic_vector(31 downto 0);
        Control24 : in  std_logic_vector(31 downto 0);
        Control25 : in  std_logic_vector(31 downto 0);
        Control26 : in  std_logic_vector(31 downto 0);
        Control27 : in  std_logic_vector(31 downto 0);
        Control28 : in  std_logic_vector(31 downto 0);
        Control29 : in  std_logic_vector(31 downto 0);
        Control30 : in  std_logic_vector(31 downto 0);
        Control31 : in  std_logic_vector(31 downto 0)
    );
end entity CustomWrapper;

-- Architecture is provided by module-specific Top.vhd files
-- Example: modules/EMFI-Seq/top/Top.vhd provides "architecture EMFI_Seq of CustomWrapper"
