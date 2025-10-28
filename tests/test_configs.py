"""
Test configurations for EZ-EMFI CocotB tests.
Auto-discovered by run.py - no Makefile needed!

Module categories:
- volo_modules: Reusable VHDL building blocks
- ds1120_pd: DS1120-PD EMFI probe driver application
- examples: Educational examples and demos

Author: EZ-EMFI Team (adapted from volo-vhdl)
Date: 2025-01-27
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
VHDL = PROJECT_ROOT / "VHDL"
TESTS = PROJECT_ROOT / "tests"


@dataclass
class TestConfig:
    """Configuration for a single CocotB test"""
    name: str
    sources: List[Path]
    toplevel: str
    test_module: str
    category: str = "misc"
    ghdl_args: List[str] = field(default_factory=lambda: ["--std=08"])


# ==================================================================================
# Test Configurations
# ==================================================================================

TESTS_CONFIG = {
    # === Volo Modules (Reusable Building Blocks) ===

    "volo_clk_divider": TestConfig(
        name="volo_clk_divider",
        sources=[
            VHDL / "volo_clk_divider.vhd",
        ],
        toplevel="volo_clk_divider",
        test_module="test_volo_clk_divider_progressive",  # Progressive P1/P2 tests
        category="volo_modules",
    ),

    "volo_voltage_pkg": TestConfig(
        name="volo_voltage_pkg",
        sources=[
            VHDL / "volo_voltage_pkg.vhd",
            TESTS / "volo_voltage_pkg_tb_wrapper.vhd",  # Testbench wrapper for package
        ],
        toplevel="volo_voltage_pkg_tb_wrapper",
        test_module="test_volo_voltage_pkg",
        category="volo_modules",
    ),

    # Note: These modules are tested as part of ds1120_pd_volo for now
    # Can create standalone tests later if needed:
    # - volo_voltage_threshold_trigger_core
    # - fsm_observer
    # - volo_bram_loader
    # - volo_common_pkg

    # === DS1120-PD Application ===

    "ds1120_pd_volo": TestConfig(
        name="ds1120_pd_volo",
        sources=[
            # Shared volo modules
            VHDL / "volo_voltage_pkg.vhd",
            VHDL / "volo_clk_divider.vhd",
            VHDL / "volo_voltage_threshold_trigger_core.vhd",
            VHDL / "fsm_observer.vhd",
            VHDL / "volo_common_pkg.vhd",
            VHDL / "volo_bram_loader.vhd",

            # DS1120-PD specific
            VHDL / "ds1120_pd_pkg.vhd",
            VHDL / "ds1120_pd_fsm.vhd",
            VHDL / "DS1120_PD_volo_main.vhd",
            VHDL / "DS1120_PD_volo_shim.vhd",
        ],
        toplevel="DS1120_PD_volo_main",
        test_module="test_ds1120_pd_volo",
        category="ds1120_pd",
    ),

    # === Examples & Demos ===

    "fsm_example": TestConfig(
        name="fsm_example",
        sources=[
            VHDL / "volo_voltage_pkg.vhd",
            VHDL / "fsm_observer.vhd",
            # Note: fsm_example files would go here if we had them
            # For now this is a placeholder
        ],
        toplevel="fsm_observer",  # Using fsm_observer as surrogate
        test_module="test_fsm_example",
        category="examples",
    ),

    "verbosity_demo": TestConfig(
        name="verbosity_demo",
        sources=[
            VHDL / "volo_voltage_pkg.vhd",
            VHDL / "fsm_observer.vhd",
        ],
        toplevel="fsm_observer",
        test_module="test_verbosity_demo",
        category="examples",
    ),
}


# ==================================================================================
# Helper Functions
# ==================================================================================

def get_test_names() -> List[str]:
    """Get sorted list of all test names"""
    return sorted(TESTS_CONFIG.keys())


def get_tests_by_category(category: str) -> dict:
    """Get tests filtered by category"""
    return {
        name: config
        for name, config in TESTS_CONFIG.items()
        if config.category == category
    }


def get_categories() -> List[str]:
    """Get sorted list of all unique categories"""
    return sorted(set(config.category for config in TESTS_CONFIG.values()))


def validate_test_files() -> dict:
    """
    Validate that all configured test files exist.
    Returns dict of {test_name: missing_files}
    """
    issues = {}

    for test_name, config in TESTS_CONFIG.items():
        missing = []

        # Check VHDL sources
        for source in config.sources:
            if not source.exists():
                missing.append(str(source))

        # Check Python test module
        test_file = TESTS / f"{config.test_module}.py"
        if not test_file.exists():
            missing.append(str(test_file))

        if missing:
            issues[test_name] = missing

    return issues


if __name__ == "__main__":
    # CLI for validating configuration
    print("EZ-EMFI CocotB Test Configuration")
    print("=" * 70)
    print(f"Total tests: {len(TESTS_CONFIG)}")
    print(f"\nCategories: {', '.join(get_categories())}")
    print(f"\nTests by category:")
    for category in get_categories():
        tests = get_tests_by_category(category)
        print(f"  {category}: {len(tests)} tests")
        for test_name in sorted(tests.keys()):
            print(f"    - {test_name}")

    # Validate files
    print("\nValidating test files...")
    issues = validate_test_files()
    if issues:
        print(f"\n⚠️  Found {len(issues)} tests with missing files:")
        for test_name, missing_files in issues.items():
            print(f"\n  {test_name}:")
            for file in missing_files:
                print(f"    - {file}")
    else:
        print("✅ All test files validated successfully!")
