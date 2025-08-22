#!/usr/bin/env python3
"""
Test script to verify the reorganized MinervaPlugin structure works correctly.
This script tests the essential functionality without requiring external dependencies.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))  # For direct imports
sys.path.insert(0, str(parent_dir))   # For package imports

def test_command_utilities():
    """Test command utility functions."""
    print("Testing command utilities...")
    
    try:
        from models.command import getCommandFilename, getStep, map_legacy_command
        
        # Test getCommandFilename
        cmd1 = {'type': 'send_filename', 'payload': {'filename': 'experiment.csv'}}
        filename = getCommandFilename(cmd1)
        assert filename == 'experiment.csv', f"Expected 'experiment.csv', got {filename}"
        print("  ✓ getCommandFilename works correctly")
        
        # Test getStep
        cmd2 = {'type': 'go_to_step', 'payload': {'step': 3}}
        step = getStep(cmd2)
        assert step == 3, f"Expected 3, got {step}"
        print("  ✓ getStep works correctly")
        
        # Test legacy mapping
        mapped = map_legacy_command('start')
        assert mapped == 'initialize_rig', f"Expected 'initialize_rig', got {mapped}"
        print("  ✓ Legacy command mapping works correctly")
        
        # Test edge cases
        assert getCommandFilename({}) is None
        assert getStep({}) is None
        assert map_legacy_command('unknown') == 'unknown'
        print("  ✓ Edge cases handled correctly")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Command utilities test failed: {e}")
        return False

def test_signal_types():
    """Test signal type definitions."""
    print("Testing signal types...")
    
    try:
        from models.signals import (
            TimeSeriesSignal, TimestampSignal, SingleValueSignal,
            StatusSignal, DebugSignal, DurationSignal
        )
        
        # Test TimeSeriesSignal creation
        ts_signal = TimeSeriesSignal(
            name="ECG",
            type="time_series",
            xUnit="seconds",
            yUnit="mV",
            data=[{"x": 1.0, "y": 0.5}]
        )
        assert ts_signal.name == "ECG"
        assert ts_signal.type == "time_series"
        print("  ✓ TimeSeriesSignal creation works")
        
        # Test SingleValueSignal creation
        sv_signal = SingleValueSignal(
            name="Heart Rate",
            type="single_value",
            valueUnit="bpm",
            data=72.5
        )
        assert sv_signal.name == "Heart Rate"
        assert sv_signal.data == 72.5
        print("  ✓ SingleValueSignal creation works")
        
        # Test StatusSignal creation
        status_signal = StatusSignal(
            name="Device Connected",
            type="status",
            data=True
        )
        assert status_signal.data is True
        print("  ✓ StatusSignal creation works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Signal types test failed: {e}")
        return False

def test_package_imports():
    """Test package-level imports."""
    print("Testing package-level imports...")
    
    try:
        # Test importing from the main package
        from MinervaPlugin import getCommandFilename, getStep, map_legacy_command
        from MinervaPlugin import TimeSeriesSignal, SingleValueSignal
        
        # Test that they work the same as direct imports
        cmd = {'type': 'send_filename', 'payload': {'filename': 'test.csv'}}
        filename = getCommandFilename(cmd)
        assert filename == 'test.csv'
        print("  ✓ Package-level command utilities work")
        
        # Test signal creation
        signal = SingleValueSignal(name="Test", type="single_value", data=42)
        assert signal.data == 42
        print("  ✓ Package-level signal types work")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Package imports test failed: {e}")
        return False

def test_directory_structure():
    """Test that the directory structure is correct."""
    print("Testing directory structure...")
    
    base_dir = Path(__file__).parent
    expected_dirs = ['core', 'models', 'simulator', 'scripts', 'tests', 'utils', 'docs']
    
    try:
        for dir_name in expected_dirs:
            dir_path = base_dir / dir_name
            assert dir_path.exists(), f"Directory {dir_name} does not exist"
            
            init_file = dir_path / '__init__.py'
            assert init_file.exists(), f"__init__.py missing in {dir_name}"
        
        print("  ✓ All expected directories exist")
        print("  ✓ All directories have __init__.py files")
        
        # Check key files are in the right places
        assert (base_dir / 'models' / 'command.py').exists()
        assert (base_dir / 'models' / 'signals.py').exists()
        assert (base_dir / 'core' / 'plugin.py').exists()
        print("  ✓ Key files are in correct locations")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Directory structure test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Reorganized MinervaPlugin Structure")
    print("=" * 60)
    
    tests = [
        test_directory_structure,
        test_command_utilities,
        test_signal_types,
        test_package_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"  ✗ Test {test_func.__name__} crashed: {e}")
            print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The reorganized structure is working correctly.")
        print("\nThe MinervaPlugin has been successfully reorganized into:")
        print("  📁 core/     - Core plugin functionality")
        print("  📁 models/   - Data models and types")
        print("  📁 simulator/ - Simulation components")
        print("  📁 scripts/  - Utility scripts")
        print("  📁 tests/    - Test files")
        print("  📁 utils/    - Utility tools")
        print("  📁 docs/     - Documentation")
        print("\nYou can now import from:")
        print("  from MinervaPlugin import getCommandFilename, getStep")
        print("  from MinervaPlugin import TimeSeriesSignal, SingleValueSignal")
        print("  from MinervaPlugin.core.plugin import Plugin")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
