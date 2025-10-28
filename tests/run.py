#!/usr/bin/env python3
"""
CocotB Python Test Runner for Volo VHDL

Replaces Makefile-based test system with native Python runner.
Uses CocotB 2.0+ Python API for build and test orchestration.

Usage:
    python tests/run.py volo_clk_divider              # Run single test
    python tests/run.py --all                        # Run all tests
    python tests/run.py --category=volo_common       # Run category
    python tests/run.py --list                       # List available tests

Author: Claude Code (CocotB Python Runner Migration)
Date: 2025-01-25
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import os
import subprocess
import threading

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_configs import TESTS_CONFIG, get_test_names, get_tests_by_category, get_categories

# Import GHDL output filter
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from ghdl_output_filter import GHDLOutputFilter, FilterLevel

# CocotB imports
try:
    from cocotb_tools.runner import get_runner
except ImportError:
    print("❌ CocotB tools not found! Install with: uv sync")
    sys.exit(1)


class FilteredOutput:
    """
    Context manager that captures and filters stdout/stderr at OS level.

    This is BULLETPROOF - it redirects file descriptors 1 and 2 (stdout/stderr)
    through pipes, so even C code (like GHDL) can't bypass it.
    """
    def __init__(self, filter_level: FilterLevel = FilterLevel.NORMAL):
        self.filter = GHDLOutputFilter(level=filter_level)
        self.original_stdout = None
        self.original_stderr = None
        self.pipe_read = None
        self.pipe_write = None
        self.reader_thread = None
        self.stop_reading = False

    def __enter__(self):
        """Start capturing and filtering output"""
        # Save original file descriptors
        self.original_stdout = os.dup(1)  # Save stdout
        self.original_stderr = os.dup(2)  # Save stderr

        # Create pipe for capturing output
        self.pipe_read, self.pipe_write = os.pipe()

        # Redirect stdout and stderr to pipe write end
        os.dup2(self.pipe_write, 1)  # Redirect stdout to pipe
        os.dup2(self.pipe_write, 2)  # Redirect stderr to pipe

        # Start reader thread to filter and display output
        self.stop_reading = False
        self.reader_thread = threading.Thread(target=self._read_and_filter)
        self.reader_thread.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original output and clean up"""
        try:
            # Flush before restoring
            sys.stdout.flush()
            sys.stderr.flush()

            # Restore original stdout/stderr
            os.dup2(self.original_stdout, 1)
            os.dup2(self.original_stderr, 2)

            # Close pipe write end (signals EOF to reader)
            os.close(self.pipe_write)

            # Wait for reader thread to finish
            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=2.0)

            # Close remaining file descriptors
            if self.original_stdout:
                os.close(self.original_stdout)
            if self.original_stderr:
                os.close(self.original_stderr)
            # Note: pipe_read is closed by fdopen in the thread
        except Exception as e:
            print(f"Warning: cleanup error: {e}", file=sys.stderr)

        return False  # Don't suppress exceptions

    def _read_and_filter(self):
        """Read from pipe and filter output in real-time"""
        pipe_file = None
        try:
            # Wrap pipe_read in a file object
            pipe_file = os.fdopen(self.pipe_read, 'r', buffering=1)
            for line in pipe_file:
                # Filter and print to original stdout
                if not self.filter.should_filter(line.rstrip('\n')):
                    os.write(self.original_stdout, line.encode())
                else:
                    self.filter.stats.filtered_lines += 1
                self.filter.stats.total_lines += 1
        except (OSError, ValueError):
            # Pipe closed or invalid - normal shutdown
            pass
        except Exception as e:
            # Log unexpected errors to original stdout
            try:
                os.write(self.original_stdout, f"\n[Filter error: {e}]\n".encode())
            except:
                pass
        finally:
            if pipe_file:
                try:
                    pipe_file.close()
                except:
                    pass


class TestRunner:
    """CocotB test runner using Python API"""

    def __init__(self, verbose: bool = False, filter_output: bool = True):
        self.verbose = verbose
        self.filter_output = filter_output
        self.tests_dir = Path(__file__).parent

    def run_test(self, test_name: str) -> bool:
        """
        Run a single test.
        Returns True if test passed, False otherwise.
        """
        if test_name not in TESTS_CONFIG:
            print(f"❌ Test '{test_name}' not found!")
            print(f"Available tests: {', '.join(get_test_names())}")
            return False

        config = TESTS_CONFIG[test_name]

        print("=" * 70)
        print(f"Running test: {test_name}")
        print(f"Category: {config.category}")
        print(f"Toplevel: {config.toplevel}")
        print(f"Test module: {config.test_module}")
        print("=" * 70)

        # Validate source files exist
        missing_sources = [str(src) for src in config.sources if not src.exists()]
        if missing_sources:
            print(f"❌ Missing source files:")
            for src in missing_sources:
                print(f"  - {src}")
            return False

        # Create GHDL runner
        runner = get_runner("ghdl")

        # Set working directory to tests/
        os.chdir(self.tests_dir)

        # Build configuration
        build_args = config.ghdl_args.copy()

        # Add simulation arguments (empty for now - keeping it simple!)
        # TODO: Add back GHDL optimization flags once basic testing works:
        #   --ieee-asserts=disable-at-0  (suppress initialization warnings)
        #   --assert-level=error         (only stop on errors)
        #   --stop-time=10ms             (timeout for runaway sims)
        sim_args = []

        # Set CocotB environment variables
        os.environ["COCOTB_REDUCED_LOG_FMT"] = "1"
        os.environ["COCOTB_LOG_LEVEL"] = "DEBUG" if self.verbose else "INFO"

        # Determine filter level
        filter_level_str = os.environ.get("GHDL_FILTER_LEVEL", "normal").lower()
        if filter_level_str == "aggressive":
            filter_level = FilterLevel.AGGRESSIVE
        elif filter_level_str == "normal":
            filter_level = FilterLevel.NORMAL
        elif filter_level_str == "minimal":
            filter_level = FilterLevel.MINIMAL
        elif filter_level_str == "none":
            filter_level = FilterLevel.NONE
        else:
            filter_level = FilterLevel.NORMAL

        try:
            # Build HDL (unfiltered - we want to see build errors)
            print("\n📦 Building HDL sources...")
            runner.build(
                sources=[str(src) for src in config.sources],
                hdl_toplevel=config.toplevel,
                always=True,
                build_args=build_args,
            )

            # Run tests with BULLETPROOF output filtering
            print("\n🧪 Running CocotB tests...")

            if self.filter_output and filter_level != FilterLevel.NONE:
                # BULLETPROOF: Capture at OS level - even GHDL can't bypass this!
                with FilteredOutput(filter_level=filter_level) as filtered:
                    runner.test(
                        hdl_toplevel=config.toplevel,
                        test_module=config.test_module,
                        test_args=sim_args,
                    )
                # Print filter summary
                if filtered.filter.stats.filtered_lines > 0:
                    print(f"\n[Filtered {filtered.filter.stats.filtered_lines} lines " +
                          f"({filtered.filter.stats.filtered_lines}/{filtered.filter.stats.total_lines} = " +
                          f"{100*filtered.filter.stats.filtered_lines/filtered.filter.stats.total_lines:.1f}% reduction)]")
            else:
                # No filtering - direct output
                runner.test(
                    hdl_toplevel=config.toplevel,
                    test_module=config.test_module,
                    test_args=sim_args,
                )

            print("\n" + "=" * 70)
            print(f"✅ Test '{test_name}' PASSED")
            print("=" * 70)
            return True

        except Exception as e:
            print("\n" + "=" * 70)
            print(f"❌ Test '{test_name}' FAILED")
            print(f"Error: {e}")
            print("=" * 70)
            return False

    def run_all_tests(self) -> dict:
        """
        Run all configured tests.
        Returns dict of {test_name: passed}
        """
        results = {}
        test_names = get_test_names()

        print(f"\n🚀 Running {len(test_names)} tests...\n")

        for i, test_name in enumerate(test_names, 1):
            print(f"\n[{i}/{len(test_names)}] {test_name}")
            results[test_name] = self.run_test(test_name)

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed

        for test_name, passed_flag in results.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            print(f"{status}: {test_name}")

        print("=" * 70)
        print(f"Results: {passed} passed, {failed} failed, {len(results)} total")
        print("=" * 70)

        return results

    def run_category(self, category: str) -> dict:
        """
        Run all tests in a category.
        Returns dict of {test_name: passed}
        """
        tests = get_tests_by_category(category)

        if not tests:
            print(f"❌ Category '{category}' not found!")
            print(f"Available categories: {', '.join(get_categories())}")
            return {}

        print(f"\n🚀 Running {len(tests)} tests in category '{category}'...\n")

        results = {}
        for i, test_name in enumerate(sorted(tests.keys()), 1):
            print(f"\n[{i}/{len(tests)}] {test_name}")
            results[test_name] = self.run_test(test_name)

        # Summary
        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed

        print("\n" + "=" * 70)
        print(f"Category '{category}': {passed} passed, {failed} failed")
        print("=" * 70)

        return results

    def list_tests(self):
        """List all available tests"""
        print("Available CocotB Tests")
        print("=" * 70)

        for category in get_categories():
            tests = get_tests_by_category(category)
            print(f"\n{category.upper()} ({len(tests)} tests):")
            for test_name in sorted(tests.keys()):
                config = tests[test_name]
                print(f"  - {test_name:30s} ({config.test_module})")

        print("\n" + "=" * 70)
        print(f"Total: {len(TESTS_CONFIG)} tests")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="CocotB Python Test Runner for Volo VHDL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run.py volo_clk_divider              # Run single test
  python tests/run.py --all                        # Run all tests
  python tests/run.py --category=volo_modules      # Run category
  python tests/run.py --list                       # List tests
  python tests/run.py volo_clk_divider --verbose   # Verbose output
        """,
    )

    parser.add_argument(
        "test_name",
        nargs="?",
        help="Name of test to run (e.g., volo_clk_divider)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Run all tests in category (e.g., volo_common, uart, instruments)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tests",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (DEBUG log level)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Disable GHDL output filtering (show all warnings)",
    )
    parser.add_argument(
        "--filter-level",
        type=str,
        choices=["aggressive", "normal", "minimal", "none"],
        default=None,
        help="Set GHDL output filter level (default: normal)",
    )

    args = parser.parse_args()

    # Set filter level if specified
    if args.filter_level:
        os.environ["GHDL_FILTER_LEVEL"] = args.filter_level
    elif args.no_filter:
        os.environ["GHDL_FILTER_LEVEL"] = "none"

    # Create runner
    runner = TestRunner(verbose=args.verbose, filter_output=not args.no_filter)

    # Handle commands
    if args.list:
        runner.list_tests()
        return 0

    elif args.all:
        results = runner.run_all_tests()
        # Exit with non-zero if any tests failed
        return 0 if all(results.values()) else 1

    elif args.category:
        results = runner.run_category(args.category)
        return 0 if all(results.values()) else 1

    elif args.test_name:
        success = runner.run_test(args.test_name)
        return 0 if success else 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
