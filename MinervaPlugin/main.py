#!/usr/bin/env python3
"""
Main entry point for the MinervaPlugin system.
This script provides a unified interface to run different components of the plugin system.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

def run_simulator():
    """Run the simulator with multiple rigs."""
    try:
        from .simulator.simulator import main as simulator_main
        simulator_main()
    except ImportError:
        print("Error: Could not import simulator. Make sure all dependencies are installed.")
        print("Try: pip install pika faker")

def run_plugin_test():
    """Run plugin tests."""
    try:
        from .tests.test_dict_commands import main as test_main
        test_main()
    except ImportError as e:
        print(f"Error: Could not import test module: {e}")

def run_streaming_test():
    """Run streaming behavior tests."""
    try:
        from .tests.test_streaming_behavior import main as streaming_test_main
        streaming_test_main()
    except ImportError as e:
        print(f"Error: Could not import streaming test module: {e}")

def cleanup_queues():
    """Clean up RabbitMQ queues."""
    try:
        from .scripts.cleanup_queues import main as cleanup_main
        cleanup_main()
    except ImportError as e:
        print(f"Error: Could not import cleanup script: {e}")
        print("Try: pip install pika")

def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="MinervaPlugin System - Unified entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py simulator              # Run the simulator
  python main.py test                   # Run command tests
  python main.py streaming-test         # Run streaming tests
  python main.py cleanup                # Clean up queues
        """
    )
    
    parser.add_argument(
        'command',
        choices=['simulator', 'test', 'streaming-test', 'cleanup'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Execute the requested command
    try:
        if args.command == 'simulator':
            print("Starting MinervaPlugin Simulator...")
            run_simulator()
        elif args.command == 'test':
            print("Running command system tests...")
            run_plugin_test()
        elif args.command == 'streaming-test':
            print("Running streaming behavior tests...")
            run_streaming_test()
        elif args.command == 'cleanup':
            print("Cleaning up RabbitMQ queues...")
            cleanup_queues()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
