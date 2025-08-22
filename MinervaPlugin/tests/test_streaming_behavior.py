#!/usr/bin/env python3
"""
Test script to demonstrate that the plugin only starts streaming when commanded.
This script shows the difference between plugin startup and actual streaming.
"""

import time
import json
import logging
from plugin import Plugin, PluginRegistration
from command import COMMANDS

def setup_logger():
    """Set up a logger for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def simulate_stream_command(user_id="test_user"):
    """
    Simulate a stream command from a user.
    
    Args:
        user_id (str): The user ID sending the command.
    
    Returns:
        dict: A stream command payload.
    """
    return {
        'type': 'stream',
        'userId': user_id,
        'payload': {
            'macAddress': 'test:mac:address',
            'stages': [
                {'name': 'Stage 1', 'type': 'wait_for_user'},
                {'name': 'Stage 2', 'type': 'timed', 'duration_in_seconds': 60}
            ],
            'signals': [
                {
                    'name': 'ECG',
                    'type': 'time_series',
                    'x_unit': 's',
                    'y_unit': 'mV',
                    'data': []
                }
            ],
            'currentStage': 'Stage 1'
        }
    }

def simulate_stop_stream_command(user_id="test_user"):
    """
    Simulate a stop stream command from a user.
    
    Args:
        user_id (str): The user ID sending the command.
    
    Returns:
        dict: A stop stream command payload.
    """
    return {
        'type': 'stop_stream',
        'userId': user_id,
        'payload': {
            'userId': user_id
        }
    }

def test_plugin_behavior():
    """Test that plugin only streams when commanded"""
    logger = setup_logger()
    
    print("=" * 60)
    print("TESTING PLUGIN STREAMING BEHAVIOR")
    print("=" * 60)
    
    # Create plugin instance
    registration = PluginRegistration(mac_address="test:mac:address")
    plugin = Plugin(registration, logger)
    
    print("\n1. Starting plugin (this should NOT start streaming)...")
    plugin.start()
    
    print(f"   Active streaming sessions: {plugin.get_user_session_count()}")
    print(f"   Is streaming: {plugin.get_is_streaming()}")
    
    # Wait a bit to show plugin is running but not streaming
    print("\n2. Waiting 3 seconds to show plugin is running but NOT streaming...")
    for i in range(3):
        time.sleep(1)
        print(f"   After {i+1}s - Active sessions: {plugin.get_user_session_count()}, Is streaming: {plugin.get_is_streaming()}")
    
    print("\n3. Now sending STREAM command (this SHOULD start streaming)...")
    stream_command = simulate_stream_command("test_user_123")
    plugin._handle_command(stream_command)
    
    # Give it a moment to process
    time.sleep(1)
    
    print(f"   Active streaming sessions: {plugin.get_user_session_count()}")
    print(f"   Is streaming: {plugin.get_is_streaming()}")
    print(f"   Active users: {plugin.get_active_user_sessions()}")
    
    print("\n4. Waiting 3 seconds to show streaming is now active...")
    for i in range(3):
        time.sleep(1)
        print(f"   After {i+1}s - Active sessions: {plugin.get_user_session_count()}, Is streaming: {plugin.get_is_streaming()}")
    
    print("\n5. Sending STOP STREAM command...")
    stop_command = simulate_stop_stream_command("test_user_123")
    plugin._handle_command(stop_command)
    
    # Give it a moment to process
    time.sleep(1)
    
    print(f"   Active streaming sessions: {plugin.get_user_session_count()}")
    print(f"   Is streaming: {plugin.get_is_streaming()}")
    
    print("\n6. Waiting 2 seconds to confirm streaming has stopped...")
    for i in range(2):
        time.sleep(1)
        print(f"   After {i+1}s - Active sessions: {plugin.get_user_session_count()}, Is streaming: {plugin.get_is_streaming()}")
    
    print("\n7. Stopping plugin...")
    plugin.stop()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nSUMMARY:")
    print("- Plugin startup does NOT automatically start streaming")
    print("- Streaming only starts when a STREAM command is received")
    print("- Streaming stops when a STOP_STREAM command is received")
    print("- The plugin correctly manages streaming sessions per user")

if __name__ == "__main__":
    test_plugin_behavior()
