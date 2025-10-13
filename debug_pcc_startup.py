#!/usr/bin/env python3
"""
PCC Startup Diagnostic Script
This script helps identify why PCC_client.py is not running properly
"""

import os
import sys
import traceback
import importlib.util

def test_import(module_name, description=""):
    """Test if a module can be imported"""
    try:
        if module_name in sys.modules:
            print(f"✅ {module_name} - already imported")
            return True
        
        # Try to import the module
        if '.' in module_name:
            # Handle relative imports
            parts = module_name.split('.')
            parent = parts[0]
            child = parts[1]
            parent_module = __import__(parent)
            getattr(parent_module, child)
        else:
            __import__(module_name)
        
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - ERROR: {e}")
        return False

def test_file_exists(filepath, description=""):
    """Test if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} - {description}")
        return True
    else:
        print(f"❌ {filepath} - NOT FOUND")
        return False

def test_pcc_dependencies():
    """Test all PCC dependencies"""
    print("🔍 Testing PCC Dependencies")
    print("=" * 50)
    
    # Test Python standard library imports
    print("\n📚 Standard Library Modules:")
    test_import("argparse", "Command line argument parsing")
    test_import("logging", "Logging system")
    test_import("os", "Operating system interface")
    test_import("sys", "System-specific parameters")
    test_import("threading", "Threading support")
    test_import("datetime", "Date and time handling")
    test_import("json", "JSON handling")
    
    # Test external library imports
    print("\n📦 External Library Modules:")
    test_import("numpy", "Numerical computing")
    test_import("psutil", "System and process utilities")
    test_import("PySide6.QtCore", "Qt Core")
    test_import("PySide6.QtGui", "Qt GUI")
    test_import("PySide6.QtWidgets", "Qt Widgets")
    test_import("PySide6.QtUiTools", "Qt UI Tools")
    test_import("pyqtgraph", "Scientific graphics")
    test_import("serial", "Serial communication")
    test_import("pika", "RabbitMQ client")
    
    # Test internal modules
    print("\n🏠 Internal Modules:")
    test_import("fm_tools", "FileMaker tools")
    test_import("DATA", "Data handling")
    test_import("DETECTORS", "Signal detectors")
    test_import("EFFECTORS", "Output effectors")
    test_import("SETTINGS", "Settings management")
    test_import("STREAMS", "Data streaming")
    test_import("STAGES", "Experiment stages")
    
    # Test MinervaPlugin
    print("\n🔌 MinervaPlugin:")
    test_import("MinervaPlugin.plugin", "Minerva plugin core")

def test_pcc_files():
    """Test if required PCC files exist"""
    print("\n📁 Required Files:")
    
    base_dir = os.path.dirname(__file__)
    
    files_to_check = [
        ("PCC_client.py", "Main PCC client"),
        ("PCC.py", "PCC core logic"),
        ("PCC_client.ui", "UI definition file"),
        ("fm_tools.py", "FileMaker tools"),
        ("DATA.py", "Data module"),
        ("DETECTORS.py", "Detectors module"),
        ("EFFECTORS.py", "Effectors module"),
        ("SETTINGS.py", "Settings module"),
        ("STREAMS.py", "Streams module"),
        ("STAGES.py", "Stages module"),
        ("MinervaPlugin/core/config.py", "Minerva config"),
        ("MinervaPlugin/core/plugin.py", "Minerva plugin"),
        ("MinervaPlugin/core/rabbitmq_client.py", "RabbitMQ client"),
    ]
    
    for filename, description in files_to_check:
        filepath = os.path.join(base_dir, filename)
        test_file_exists(filepath, description)

def test_minerva_config():
    """Test Minerva configuration"""
    print("\n⚙️  Minerva Configuration:")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'MinervaPlugin', 'core'))
        from config import RABBITMQ_SERVER, RABBITMQ_PORT, RABBITMQ_AMQP_PORT, RABBITMQ_USER
        
        print(f"✅ Config loaded successfully")
        print(f"   Server: {RABBITMQ_SERVER}")
        print(f"   AMQP Port: {RABBITMQ_AMQP_PORT}")
        print(f"   Management Port: {RABBITMQ_PORT}")
        print(f"   User: {RABBITMQ_USER}")
        
        # Test network connectivity
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((RABBITMQ_SERVER, RABBITMQ_AMQP_PORT))
            sock.close()
            
            if result == 0:
                print(f"✅ Network connectivity to {RABBITMQ_SERVER}:{RABBITMQ_AMQP_PORT}")
            else:
                print(f"❌ Cannot connect to {RABBITMQ_SERVER}:{RABBITMQ_AMQP_PORT}")
                print("   💡 Run test_network_connection.py for detailed diagnostics")
        except Exception as e:
            print(f"❌ Network test failed: {e}")
            
    except Exception as e:
        print(f"❌ Config loading failed: {e}")

def test_pcc_startup():
    """Test PCC startup sequence"""
    print("\n🚀 PCC Startup Test:")
    
    try:
        # Change to PCC directory
        pcc_dir = os.path.dirname(__file__)
        os.chdir(pcc_dir)
        
        # Test argument parsing
        print("   Testing argument parsing...")
        import argparse
        parser = argparse.ArgumentParser("PCC_client")
        parser.add_argument("-i", "--interactive", action="store_true")
        parser.add_argument("-s", "--simulation", action="store_true")
        test_args = parser.parse_args([])  # Empty args
        print("   ✅ Argument parsing works")
        
        # Test Qt application creation
        print("   Testing Qt application...")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QFile
        from PySide6.QtUiTools import QUiLoader
        
        # Create minimal Qt app
        app = QApplication(["--platform", "offscreen"])  # Headless mode
        print("   ✅ Qt application created")
        
        # Test UI file loading
        print("   Testing UI file loading...")
        ui_file = QFile(os.path.join(pcc_dir, "PCC_client.ui"))
        if ui_file.exists():
            loader = QUiLoader()
            ui = loader.load(ui_file)
            print("   ✅ UI file loaded successfully")
        else:
            print("   ❌ UI file not found")
            
    except Exception as e:
        print(f"   ❌ Startup test failed: {e}")
        traceback.print_exc()

def main():
    print("🔧 PCC Startup Diagnostic Tool")
    print("=" * 60)
    print("This tool helps identify why PCC_client.py is not running")
    print("")
    
    # Run all tests
    test_pcc_dependencies()
    test_pcc_files()
    test_minerva_config()
    test_pcc_startup()
    
    print("\n" + "=" * 60)
    print("🏁 Diagnostic Complete!")
    print("")
    print("💡 Next Steps:")
    print("1. Fix any ❌ FAILED items above")
    print("2. If network connectivity fails, run: python MinervaPlugin/test_network_connection.py")
    print("3. If imports fail, install missing packages: pip install <package_name>")
    print("4. If files are missing, check your PCC installation")
    print("5. Try running PCC with: python PCC_client.py --simulation --interactive")

if __name__ == "__main__":
    main()
