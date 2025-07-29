#!/usr/bin/env python3
"""
Simple test to verify RabbitMQ shutdown fix
"""

import logging
import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugin import Plugin, PluginRegistration
from command import StreamCommand

def test_plugin_shutdown():
    """Test that plugin shuts down cleanly without crashes."""
    print("Testing plugin shutdown functionality")
    print("=" * 50)
    
    # Create plugin instance
    registration = PluginRegistration("test:shutdown:device")
    plugin = Plugin(registration, logging.getLogger())
    
    try:
        # Start the plugin
        plugin.start()
        print("Plugin started successfully")
        
        # Simulate some activity
        user_id = "test_user"
        stream_command_dict = {
            "type": "stream",
            "user_id": user_id,
            "payload": {
                "signals": [
                    {"name": "ECG", "value": 75, "timestamp": time.time()},
                    {"name": "BPM", "value": 72, "timestamp": time.time()}
                ]
            }
        }

        # Send a stream command to create a user session
        plugin._handle_command(stream_command_dict)
        print(f"Started streaming for user {user_id}")
        
        # Wait a moment to let things settle
        time.sleep(2)
        
        # Verify user is streaming
        if plugin.is_user_streaming(user_id):
            print("User streaming confirmed")
        else:
            print("WARNING: User not streaming as expected")
        
        print("Attempting to stop plugin...")
        
        # This is where the crash was happening
        plugin.stop()
        
        print("SUCCESS: Plugin stopped cleanly without crashes!")
        return True
        
    except Exception as e:
        print(f"ERROR: Plugin shutdown failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("RabbitMQ Shutdown Fix Test")
    print("=" * 40)
    
    try:
        success = test_plugin_shutdown()
        
        if success:
            print("\nTEST PASSED: No crashes during shutdown!")
        else:
            print("\nTEST FAILED: Crashes still occurring")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
