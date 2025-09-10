#!/usr/bin/env python3
"""
Minimal PCC Test Script
This script attempts to run PCC in the simplest possible way to identify issues
"""

import os
import sys
import traceback

def test_basic_imports():
    """Test basic imports that PCC needs"""
    print("🔍 Testing basic imports...")
    
    try:
        import argparse
        print("✅ argparse")
    except Exception as e:
        print(f"❌ argparse: {e}")
        return False
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QFile
        from PySide6.QtUiTools import QUiLoader
        print("✅ PySide6 (Qt)")
    except Exception as e:
        print(f"❌ PySide6: {e}")
        print("   💡 Install with: pip install PySide6")
        return False
    
    try:
        import numpy
        print("✅ numpy")
    except Exception as e:
        print(f"❌ numpy: {e}")
        return False
    
    try:
        import psutil
        print("✅ psutil")
    except Exception as e:
        print(f"❌ psutil: {e}")
        return False
    
    return True

def test_internal_modules():
    """Test internal PCC modules"""
    print("\n🏠 Testing internal modules...")
    
    # Change to PCC directory
    pcc_dir = os.path.dirname(__file__)
    if pcc_dir:
        os.chdir(pcc_dir)
        sys.path.insert(0, pcc_dir)
    
    modules_to_test = [
        "fm_tools",
        "DATA", 
        "DETECTORS",
        "EFFECTORS", 
        "SETTINGS",
        "STREAMS",
        "STAGES"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    return True

def test_minerva_plugin():
    """Test MinervaPlugin import"""
    print("\n🔌 Testing MinervaPlugin...")
    
    try:
        from MinervaPlugin import plugin as mp
        print("✅ MinervaPlugin imported")
        return True
    except Exception as e:
        print(f"❌ MinervaPlugin: {e}")
        print("   💡 Check if MinervaPlugin directory exists")
        print("   💡 Check if config.py has correct network settings")
        traceback.print_exc()
        return False

def test_qt_ui():
    """Test Qt UI loading"""
    print("\n🖥️  Testing Qt UI...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QFile
        from PySide6.QtUiTools import QUiLoader
        
        # Create Qt application in headless mode
        app = QApplication(["--platform", "offscreen"])
        print("✅ Qt application created")
        
        # Test UI file
        ui_file_path = "PCC_client.ui"
        if os.path.exists(ui_file_path):
            ui_file = QFile(ui_file_path)
            loader = QUiLoader()
            ui = loader.load(ui_file)
            print("✅ UI file loaded")
            return True
        else:
            print(f"❌ UI file not found: {ui_file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Qt UI test failed: {e}")
        traceback.print_exc()
        return False

def run_pcc_minimal():
    """Try to run PCC in minimal mode"""
    print("\n🚀 Attempting minimal PCC startup...")
    
    try:
        # Import PCC_client
        print("   Importing PCC_client...")
        import PCC_client
        print("   ✅ PCC_client imported successfully")
        
        # Try to run main function with simulation mode
        print("   Running PCC main with simulation mode...")
        
        # Override sys.argv to simulate command line args
        original_argv = sys.argv.copy()
        sys.argv = ["PCC_client.py", "--simulation", "--interactive"]
        
        try:
            # This will likely fail, but we want to see HOW it fails
            PCC_client.main()
        except SystemExit:
            print("   ✅ PCC exited normally (SystemExit)")
        except KeyboardInterrupt:
            print("   ✅ PCC interrupted by user")
        except Exception as e:
            print(f"   ❌ PCC failed with error: {e}")
            traceback.print_exc()
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"   ❌ Failed to import or run PCC_client: {e}")
        traceback.print_exc()

def main():
    print("🧪 PCC Minimal Test")
    print("=" * 40)
    print("This script tests PCC in the simplest possible way")
    print("")
    
    # Run tests in order
    if not test_basic_imports():
        print("\n❌ Basic imports failed - fix these first")
        return
    
    if not test_internal_modules():
        print("\n❌ Internal modules failed - check PCC installation")
        return
    
    if not test_minerva_plugin():
        print("\n❌ MinervaPlugin failed - check network configuration")
        print("   💡 Try running: python MinervaPlugin/configure_network.py")
        return
    
    if not test_qt_ui():
        print("\n❌ Qt UI failed - check UI file and Qt installation")
        return
    
    print("\n✅ All basic tests passed - attempting PCC startup...")
    run_pcc_minimal()
    
    print("\n" + "=" * 40)
    print("🏁 Test Complete!")
    print("")
    print("💡 If PCC still doesn't work:")
    print("1. Run: python debug_pcc_startup.py")
    print("2. Check the exact error message above")
    print("3. Try: python PCC_client.py --simulation --interactive")

if __name__ == "__main__":
    main()
