#!/usr/bin/env python3
"""
Test runner script for Meli Challenge
Runs all tests with different options and generates reports
"""

import sys
import os
import argparse
import unittest
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test modules
from tests.test_spiders import *
from tests.test_pipelines import *
from tests.test_integration import *


def create_test_suite():
    """Create a test suite with all test cases"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'tests.test_spiders',
        'tests.test_pipelines', 
        'tests.test_integration'
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name, fromlist=['*'])
            suite.addTests(loader.loadTestsFromModule(module))
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
    
    return suite


def run_tests_with_options(suite, verbosity=2, failfast=False, buffer=False):
    """Run tests with specified options"""
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=failfast,
        buffer=buffer
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result


def run_specific_tests(test_pattern, verbosity=2):
    """Run specific tests based on pattern"""
    loader = unittest.TestLoader()
    
    # Try to load tests by pattern
    try:
        suite = loader.loadTestsFromName(test_pattern)
    except AttributeError:
        print(f"Error: Could not find tests matching pattern '{test_pattern}'")
        return None
    
    return run_tests_with_options(suite, verbosity)


def run_tests_by_category(category, verbosity=2):
    """Run tests by category"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if category == 'spiders':
        import tests.test_spiders
        suite.addTests(loader.loadTestsFromModule(tests.test_spiders))
    elif category == 'pipelines':
        import tests.test_pipelines
        suite.addTests(loader.loadTestsFromModule(tests.test_pipelines))
    elif category == 'integration':
        import tests.test_integration
        suite.addTests(loader.loadTestsFromModule(tests.test_integration))
    elif category == 'unit':
        # Run only unit tests (spiders and pipelines)
        import tests.test_spiders
        import tests.test_pipelines
        suite.addTests(loader.loadTestsFromModule(tests.test_spiders))
        suite.addTests(loader.loadTestsFromModule(tests.test_pipelines))
    else:
        print(f"Error: Unknown category '{category}'. Available categories: spiders, pipelines, integration, unit")
        return None
    
    return run_tests_with_options(suite, verbosity)


def generate_test_report(result, output_file=None):
    """Generate a test report"""
    if output_file is None:
        output_file = f"test_report_{int(time.time())}.txt"
    
    with open(output_file, 'w') as f:
        f.write("MELI CHALLENGE TEST REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tests run: {result.testsRun}\n")
        f.write(f"Failures: {len(result.failures)}\n")
        f.write(f"Errors: {len(result.errors)}\n")
        f.write(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}\n\n")
        
        if result.failures:
            f.write("FAILURES:\n")
            f.write("-" * 20 + "\n")
            for test, traceback in result.failures:
                f.write(f"{test}:\n{traceback}\n\n")
        
        if result.errors:
            f.write("ERRORS:\n")
            f.write("-" * 20 + "\n")
            for test, traceback in result.errors:
                f.write(f"{test}:\n{traceback}\n\n")
        
        if result.failures or result.errors:
            f.write("SUMMARY: FAILED\n")
        else:
            f.write("SUMMARY: PASSED\n")
    
    print(f"Test report generated: {output_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Meli Challenge tests')
    parser.add_argument(
        '--category', '-c',
        choices=['all', 'spiders', 'pipelines', 'integration', 'unit'],
        default='all',
        help='Test category to run (default: all)'
    )
    parser.add_argument(
        '--pattern', '-p',
        help='Run specific tests matching pattern (e.g., TestMeliUySpider)'
    )
    parser.add_argument(
        '--verbosity', '-v',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Test output verbosity (default: 2)'
    )
    parser.add_argument(
        '--failfast', '-f',
        action='store_true',
        help='Stop on first failure or error'
    )
    parser.add_argument(
        '--buffer', '-b',
        action='store_true',
        help='Buffer stdout and stderr during test runs'
    )
    parser.add_argument(
        '--report', '-r',
        help='Generate test report to specified file'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available tests without running them'
    )
    
    args = parser.parse_args()
    
    # List tests if requested
    if args.list:
        suite = create_test_suite()
        print("Available tests:")
        for test in suite:
            print(f"  {test}")
        return
    
    # Run specific tests by pattern
    if args.pattern:
        result = run_specific_tests(args.pattern, args.verbosity)
        if result is None:
            sys.exit(1)
    # Run tests by category
    elif args.category != 'all':
        result = run_tests_by_category(args.category, args.verbosity)
        if result is None:
            sys.exit(1)
    # Run all tests
    else:
        suite = create_test_suite()
        result = run_tests_with_options(
            suite, 
            verbosity=args.verbosity,
            failfast=args.failfast,
            buffer=args.buffer
        )
    
    # Generate report if requested
    if args.report:
        generate_test_report(result, args.report)
    
    # Exit with appropriate code
    if result.failures or result.errors:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
