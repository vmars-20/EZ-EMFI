#!/usr/bin/env python3
"""
Verbosity Demonstration Script

Shows the dramatic difference in output between verbosity levels.
Run this to see why the new approach is better for LLMs.

Usage:
    python tests/test_verbosity_demo.py

Author: Volo Engineering
Date: 2025-01-26
"""

import os
import sys


def print_separator():
    print("=" * 70)


def simulate_old_style_output():
    """Simulate the old verbose CocotB output"""
    print("\n")
    print_separator()
    print("OLD STYLE OUTPUT (Current CocotB default)")
    print_separator()
    print()

    # Simulate typical CocotB output
    test_output = """
     0.00ns INFO     cocotb.gpi                         ..mbed/gpi_embed.cpp:76   in set_program_name_in_venv        Did not detect Python virtual environment. Using system-wide Python interpreter
     0.00ns INFO     cocotb.gpi                         ../gpi/GpiCommon.cpp:101   in gpi_print_registered_impl       VPI registered
     0.00ns INFO     cocotb.gpi                         ..mbed/gpi_embed.cpp:122   in _embed_init_python              Python interpreter initialized and cocotb loaded!
     0.00ns INFO     cocotb                              __init__.py:128            in _initialise_testbench           Running on GHDL version 4.0.0-dev (3.0.0.r845.g5578718d1) [Dunoon edition]
     0.00ns INFO     cocotb                              __init__.py:169            in _initialise_testbench           Running tests with cocotb v1.9.0 from /Users/johnycsh/.venv/lib/python3.11/site-packages/cocotb
     0.00ns INFO     cocotb                              __init__.py:191            in _initialise_testbench           Seeding Python random module with 1706285543
     0.00ns INFO     cocotb.regression                   regression.py:127          in __init__                        Found test test_counter_nbit.test_reset_behavior
     0.00ns INFO     cocotb.regression                   regression.py:127          in __init__                        Found test test_counter_nbit.test_count_up_to_max
     0.00ns INFO     cocotb.regression                   regression.py:127          in __init__                        Found test test_counter_nbit.test_count_down_to_zero
     0.00ns INFO     cocotb.regression                   regression.py:479          in _start_test                     Running test 1/10: test_reset_behavior

======================================================================
Test 1: Reset Behavior
======================================================================
     0.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:29    in test_reset_behavior            Starting reset sequence...
     0.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:30    in test_reset_behavior            Setting up clock with period 10ns
    10.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:32    in test_reset_behavior            Clock started
    10.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:33    in test_reset_behavior            Asserting reset (active low)
    10.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:35    in test_reset_behavior            Waiting 5 clock cycles...
    60.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:37    in test_reset_behavior            Deasserting reset
    60.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:39    in test_reset_behavior            Waiting 2 clock cycles for settling...
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:41    in test_reset_behavior            Checking counter value after reset
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:43    in test_reset_behavior              Count after reset: 0
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:44    in test_reset_behavior              Status after reset: 0x04 (at_zero flag set)
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:46    in test_reset_behavior            ✓ Reset test PASSED

======================================================================
Test 2: Count Up to Max
======================================================================
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:52    in test_count_up_to_max           Starting count up test...
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:53    in test_count_up_to_max           Setting max_value = 10
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:54    in test_count_up_to_max           Setting up_down = 1 (count up)
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:55    in test_count_up_to_max           Setting enable = 1
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:65    in test_count_up_to_max           Initial state check:
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:67    in test_count_up_to_max             Initial: count = 0
    80.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:70    in test_count_up_to_max           Starting to count from 1 to 10...
    90.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 1: count = 1
   100.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 2: count = 2
   110.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 3: count = 3
   120.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 4: count = 4
   130.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 5: count = 5
   140.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 6: count = 6
   150.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 7: count = 7
   160.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 8: count = 8
   170.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 9: count = 9
   180.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:74    in test_count_up_to_max             After cycle 10: count = 10
   180.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:77    in test_count_up_to_max           Checking wrap-around behavior...
   190.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:80    in test_count_up_to_max             ✓ Counter wrapped from 10 → 0
   190.00ns INFO     cocotb.counter_nbit                 test_counter_nbit.py:82    in test_count_up_to_max           ✓ Count up test PASSED

... [200+ more lines of similar verbose output] ...

======================================================================
REGRESSION SUMMARY
======================================================================
   2000.00ns INFO     cocotb.regression                   regression.py:365          in _log_test_summary
   2000.00ns INFO     cocotb.regression                   regression.py:366          in _log_test_summary              Test Summary:
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_reset_behavior: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_count_up_to_max: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_count_down_to_zero: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_terminal_count_up: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_terminal_count_down: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_load_value: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_max_value_change: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_enable_control: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_status_register: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:369          in _log_test_summary                test_summary: PASS
   2000.00ns INFO     cocotb.regression                   regression.py:372          in _log_test_summary
   2000.00ns INFO     cocotb.regression                   regression.py:373          in _log_test_summary              ALL TESTS PASSED
    """
    print(test_output)

    # Count lines
    line_count = len(test_output.strip().split('\n'))
    print(f"\nTOTAL OUTPUT: {line_count} lines")
    print("CONTEXT USAGE: ~4000 tokens")
    print()


def simulate_new_style_minimal():
    """Simulate new P1 + MINIMAL output (LLM-friendly)"""
    print_separator()
    print("NEW STYLE - P1 + MINIMAL (Default for LLMs)")
    print_separator()
    print()

    test_output = """P1 - BASIC TESTS
T1: Reset behavior
  ✓ PASS
T2: Count up to 5
  ✓ PASS
T3: Count down from 5
  ✓ PASS
T4: Enable control
  ✓ PASS
ALL 4 TESTS PASSED"""

    print(test_output)

    line_count = len(test_output.strip().split('\n'))
    print(f"\nTOTAL OUTPUT: {line_count} lines")
    print("CONTEXT USAGE: ~50 tokens")
    print()


def simulate_new_style_normal():
    """Simulate new P1 + NORMAL output (human-friendly)"""
    print_separator()
    print("NEW STYLE - P1 + NORMAL (Human-friendly)")
    print_separator()
    print()

    test_output = """============================================================
PHASE: P1 - BASIC TESTS
============================================================
============================================================
Test 1: Reset behavior
✓ Reset behavior PASSED
============================================================
Test 2: Count up to 5
✓ Count up to 5 PASSED
============================================================
Test 3: Count down from 5
✓ Count down from 5 PASSED
============================================================
Test 4: Enable control
✓ Enable control PASSED
============================================================
MODULE: counter_nbit
TESTS RUN: 4
PASSED: 4
FAILED: 0
RESULT: ALL TESTS PASSED ✓
============================================================"""

    print(test_output)

    line_count = len(test_output.strip().split('\n'))
    print(f"\nTOTAL OUTPUT: {line_count} lines")
    print("CONTEXT USAGE: ~150 tokens")
    print()


def simulate_new_style_silent():
    """Simulate new SILENT output (CI/CD friendly)"""
    print_separator()
    print("NEW STYLE - SILENT (CI/CD, all tests pass)")
    print_separator()
    print()

    test_output = ""  # No output when all pass

    if test_output:
        print(test_output)
    else:
        print("[No output - all tests passed]")

    print(f"\nTOTAL OUTPUT: 0 lines")
    print("CONTEXT USAGE: 0 tokens")
    print()


def main():
    print("\n" + "=" * 70)
    print("COCOTB VERBOSITY COMPARISON DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates why the new progressive testing approach")
    print("with verbosity control is essential for LLM-based workflows.")

    simulate_old_style_output()
    simulate_new_style_minimal()
    simulate_new_style_normal()
    simulate_new_style_silent()

    print_separator()
    print("SUMMARY")
    print_separator()
    print()
    print("Old Style:           ~100 lines, ~4000 tokens")
    print("New P1 + MINIMAL:    9 lines,    ~50 tokens    (98% reduction!)")
    print("New P1 + NORMAL:     20 lines,   ~150 tokens   (96% reduction)")
    print("New SILENT:          0 lines,    0 tokens      (100% reduction)")
    print()
    print("For LLMs: Use P1 + MINIMAL (default)")
    print("For Humans: Use P2 + NORMAL")
    print("For CI/CD: Use P3 + SILENT (with exit codes)")
    print()
    print("Configuration:")
    print("  export TEST_LEVEL=P1_BASIC         # Test progression")
    print("  export COCOTB_VERBOSITY=MINIMAL    # Output verbosity")
    print()


if __name__ == "__main__":
    main()