#!/usr/bin/env python3
"""
VHDL Dependency Graph Builder using GHDL native dependency resolution.

No manual dependency tracking needed! GHDL automatically determines
compilation order by analyzing VHDL 'use' statements.

Usage:
    python scripts/build_vhdl_deps.py              # Import all sources (build dependency graph)
    python scripts/build_vhdl_deps.py --clean      # Clean build artifacts
    python scripts/build_vhdl_deps.py --entity foo # Build specific entity (elaborate)
    python scripts/build_vhdl_deps.py --help       # Show help

Note: Default mode (no args) only imports sources to build dependency graph.
      It does NOT compile/elaborate entities. Use --entity to actually build.

Features:
    - Auto-discovers all VHDL files in instruments/, experimental/, and modules/
    - GHDL resolves dependencies automatically
    - Works from any directory (finds project root)
    - Skips testbenches and test wrappers
    - Comprehensive error reporting

Author: Claude Code (GHDL Build Modernization)
Date: 2025-01-25
"""

from pathlib import Path
import subprocess
import sys
import shutil
from typing import List, Optional


# ANSI color codes for output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def find_project_root() -> Path:
    """Find project root by looking for pyproject.toml"""
    current = Path(__file__).resolve().parent

    # Go up until we find pyproject.toml or hit root
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    # Fallback: assume script is in scripts/ subdirectory
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = find_project_root()
MODULES_DIR = PROJECT_ROOT / "modules"
INSTRUMENTS_DIR = PROJECT_ROOT / "instruments"
EXPERIMENTAL_DIR = PROJECT_ROOT / "experimental"
WORK_DIR = MODULES_DIR / "work"


def print_status(icon: str, message: str, color: str = Colors.NC):
    """Print colored status message"""
    print(f"{color}{icon} {message}{Colors.NC}")


def find_vhdl_files() -> List[Path]:
    """
    Find all VHDL source files across the project.

    Searches in:
    - instruments/ (top-level instruments with MCC integration)
    - experimental/ (experimental instruments)
    - modules/shared/ (utility modules: core/, packages/, observer/)
    - modules/oddball/ (special-case modules)
    - modules/examples/ (educational examples)
    - modules/untested/ (modules without CocotB tests)

    Skips:
    - Testbench files (containing 'tb' in path)
    - Test wrapper files (containing 'wrapper' in name)
    - Files in cloudcompile_package/ directories
    - Files in incoming/ directories

    Returns:
        List of Path objects for VHDL source files
    """
    vhdl_files = []

    # Search locations: (directory, base_path)
    search_locations = [
        (INSTRUMENTS_DIR, PROJECT_ROOT),
        (EXPERIMENTAL_DIR, PROJECT_ROOT),
        (MODULES_DIR / "shared", MODULES_DIR),
        (MODULES_DIR / "oddball", MODULES_DIR),
        (MODULES_DIR / "examples", MODULES_DIR),
        (MODULES_DIR / "untested", MODULES_DIR),
    ]

    for location, _ in search_locations:
        if not location.exists():
            continue

        # Find all .vhd files recursively
        for vhd_file in location.rglob("*.vhd"):
            # Skip testbenches
            if "/tb/" in str(vhd_file) or "\\tb\\" in str(vhd_file):
                continue

            # Skip test wrappers
            if "wrapper" in vhd_file.name.lower():
                continue

            # Skip cloudcompile packages
            if "cloudcompile_package" in str(vhd_file):
                continue

            # Skip incoming directories
            if "incoming" in str(vhd_file):
                continue

            vhdl_files.append(vhd_file)

    return sorted(vhdl_files)  # Sort for consistent ordering


def run_ghdl_command(args: List[str], description: str) -> bool:
    """
    Run a GHDL command and handle errors.

    Args:
        args: Command arguments (including 'ghdl')
        description: Human-readable description for error messages

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            args,
            cwd=MODULES_DIR,
            capture_output=True,
            text=True,
            check=True
        )

        # Print any output (GHDL sometimes has warnings)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return True

    except subprocess.CalledProcessError as e:
        print_status("❌", f"{description} failed!", Colors.RED)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print_status("❌", "GHDL not found! Install with your package manager.", Colors.RED)
        print("   brew install ghdl  # macOS")
        print("   apt install ghdl   # Ubuntu/Debian")
        return False


def import_all_sources() -> bool:
    """
    Import all VHDL sources into GHDL work library.

    GHDL analyzes the files and builds an internal dependency graph.
    This is much faster than compilation and lets GHDL figure out
    what depends on what.

    Returns:
        True if successful, False otherwise
    """
    print_status("🔍", "Finding VHDL source files...", Colors.BLUE)
    vhdl_files = find_vhdl_files()

    if not vhdl_files:
        print_status("❌", "No VHDL files found!", Colors.RED)
        return False

    print(f"   Found {len(vhdl_files)} VHDL source files")

    # Show first few files for confirmation
    print("   First few files:")
    for f in vhdl_files[:5]:
        rel_path = f.relative_to(PROJECT_ROOT)
        print(f"     - {rel_path}")
    if len(vhdl_files) > 5:
        print(f"     ... and {len(vhdl_files) - 5} more")

    # Create work directory if it doesn't exist
    WORK_DIR.mkdir(exist_ok=True)

    print_status("📦", "Importing sources into GHDL work library...", Colors.BLUE)

    # Import all files
    cmd = [
        "ghdl",
        "-i",  # Import
        f"--workdir={WORK_DIR}",
        "--std=08",
    ] + [str(f) for f in vhdl_files]

    if not run_ghdl_command(cmd, "Import"):
        return False

    print_status("✅", "Import complete - GHDL has dependency information", Colors.GREEN)
    return True


def build_entity(entity_name: str) -> bool:
    """
    Build (elaborate) a specific entity.

    GHDL uses its internal dependency graph to compile everything
    needed for this entity in the correct order.

    Args:
        entity_name: Name of the top-level entity to build

    Returns:
        True if successful, False otherwise
    """
    print_status("🔨", f"Building entity '{entity_name}'...", Colors.BLUE)

    cmd = [
        "ghdl",
        "-m",  # Make (elaborate)
        f"--workdir={WORK_DIR}",
        "--std=08",
        entity_name
    ]

    if not run_ghdl_command(cmd, f"Build {entity_name}"):
        return False

    print_status("✅", f"Built '{entity_name}' successfully", Colors.GREEN)
    return True


def clean_build_artifacts():
    """
    Clean all build artifacts.

    Removes:
    - GHDL work directory
    - Compiled object files (*.o)
    - GHDL library files (work-*.cf)
    """
    print_status("🧹", "Cleaning build artifacts...", Colors.BLUE)

    cleaned_items = []

    # Remove work directory
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
        cleaned_items.append("work/")

    # Remove object files
    for obj_file in MODULES_DIR.glob("*.o"):
        obj_file.unlink()
        cleaned_items.append(obj_file.name)

    # Remove GHDL library files
    for cf_file in MODULES_DIR.glob("work-*.cf"):
        cf_file.unlink()
        cleaned_items.append(cf_file.name)

    # Remove elaborated executables (entity names)
    # Note: Hard to identify these automatically, so we skip for now

    if cleaned_items:
        print(f"   Removed: {', '.join(cleaned_items[:5])}")
        if len(cleaned_items) > 5:
            print(f"   ... and {len(cleaned_items) - 5} more")
        print_status("✅", "Clean complete", Colors.GREEN)
    else:
        print_status("✅", "Already clean (no artifacts found)", Colors.GREEN)


def build_all() -> int:
    """
    Build all modules by importing all sources.

    This doesn't elaborate any specific entities, but prepares
    GHDL's dependency graph so any entity can be quickly built.

    Returns:
        0 on success, 1 on failure
    """
    if not import_all_sources():
        return 1

    print()
    print_status("✅", "Dependency graph complete!", Colors.GREEN)
    print("   GHDL has imported all sources and resolved dependencies.")
    print("   To build a specific entity:")
    print(f"   {Colors.BLUE}python scripts/build_vhdl_deps.py --entity <entity_name>{Colors.NC}")

    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="VHDL Dependency Graph Builder using GHDL native dependency resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build_vhdl_deps.py                    # Import all sources (dependency graph)
  python scripts/build_vhdl_deps.py --entity foo       # Build entity 'foo'
  python scripts/build_vhdl_deps.py --clean            # Clean artifacts

  # Or with UV:
  uv run python scripts/build_vhdl_deps.py
  uv run python scripts/build_vhdl_deps.py --entity volo_clk_divider

Features:
  - Auto-discovers all VHDL files in instruments/, experimental/, and modules/
  - GHDL resolves dependencies automatically (no manual tracking!)
  - Works from any directory (finds project root)
  - Skips testbenches and test wrappers automatically
        """
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts (work/, *.o, *.cf files)"
    )
    parser.add_argument(
        "--entity",
        type=str,
        metavar="NAME",
        help="Build specific entity (elaborates with dependencies)"
    )

    args = parser.parse_args()

    # Check that modules directory exists
    if not MODULES_DIR.exists():
        print_status("❌", f"Modules directory not found: {MODULES_DIR}", Colors.RED)
        print("   Are you in the right directory?")
        return 1

    # Handle commands
    if args.clean:
        clean_build_artifacts()
        return 0

    elif args.entity:
        # Import sources first, then build entity
        if not import_all_sources():
            return 1
        print()
        if not build_entity(args.entity):
            return 1
        return 0

    else:
        # Default: import all sources
        return build_all()


if __name__ == "__main__":
    sys.exit(main())
