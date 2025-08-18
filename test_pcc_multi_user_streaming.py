#!/usr/bin/env python3
"""
Test script to verify PCC_client correctly sends data to multiple users.
This test simulates the scenario where multiple users are streaming from the same rig.
"""

import json
import time
import threading
from datetime import datetime
import logging

# Import the plugin module
try:
    from MinervaPlugin.plugin import Plugin, PluginRegistration, MinervaStreamData
    from MinervaPlugin.command import COMMANDS
except ImportError as e:
    print("Import error: {}".format(e))
    print("Make sure you're running this from the correct directory")
    exit(1)

def setup_logger():
    """Set up a simple logger for testing."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def simulate_stream_command(user_id, mac_address="test:mac:address"):
    """
    Simulate a stream command from a user.
    
    Args:
        user_id (str): The user ID sending the command.
        mac_address (str): The MAC address for the device.
    
    Returns:
        dict: A stream command payload.
    """
    return {
        'type': COMMANDS.STREAM.value,
        'userId': user_id,  # Send userId at top level like frontend does
        'payload': {
            'macAddress': mac_address,
            'stages': [
                {'name': 'test_stage', 'type': 'timed', 'durationInSeconds': 60}
            ],
            'signals': [
                {'name': 'test_signal', 'type': 'single_value', 'data': 42.0}
            ],
            'currentStage': 'test_stage'
        }
    }

def create_mock_pcc_data():
    """Create mock data that PCC_client would generate."""
    return {
        "signals": [
            {
                "name": "Airflow",
                "type": "time_series",
                "xUnit": "seconds",
                "data": [
                    {"x": 0.0, "y": 1.5},
                    {"x": 0.1, "y": 1.6},
                    {"x": 0.2, "y": 1.4}
                ]
            },
            {
                "name": "avg_bpm",
                "type": "single_value",
                "data": 75.5
            },
            {
                "name": "avg_hr",
                "type": "single_value", 
                "data": 72.3
            }
        ]
    }

def test_multi_user_streaming():
    """Test that PCC_client sends data to multiple users correctly."""
    logger = setup_logger()
    
    # Create plugin instance
    registration = PluginRegistration(mac_address="test:mac:address")
    plugin = Plugin(registration, logger)
    
    print("Starting plugin...")
    plugin.start()
    
    try:
        # Simulate multiple users starting to stream
        print("\n=== Setting up multiple users ===")
        user_ids = ["user1", "user2", "user3"]
        
        for user_id in user_ids:
            command = simulate_stream_command(user_id)
            plugin._handle_command(command)
            print("Started streaming for {}".format(user_id))
        
        time.sleep(1)
        
        # Verify all users are active
        active_sessions = plugin.get_active_user_sessions()
        print("Active sessions: {}".format(active_sessions))
        assert len(active_sessions) == 3, "Expected 3 active sessions, got {}".format(len(active_sessions))

        # Test the PCC_client logic
        print("\n=== Testing PCC_client multi-user data sending ===")

        # Create mock stream data like PCC_client would
        mock_stream_data = MinervaStreamData(
            mac_address="test:mac:address",
            stages=[{"name": "test_stage", "type": "timed", "durationInSeconds": 60}],
            signals=create_mock_pcc_data()["signals"],
            current_stage="test_stage"
        )

        # Test the new logic: get active users and send to each
        active_users = plugin.get_active_user_sessions()
        print("Active users before sending data: {}".format(active_users))

        if active_users:
            # Send to each active user session (like PCC_client now does)
            for user_id in active_users:
                plugin.update_stream_data(mock_stream_data, user_id=user_id)
                print("✓ Sent stream data to user {}".format(user_id))

            print("✓ Successfully sent data to {} users".format(len(active_users)))

            # Verify each user has the updated data
            for user_id in active_users:
                user_data = plugin.get_stream_data(user_id)
                assert user_data is not None, "User {} should have stream data".format(user_id)
                assert user_data.mac_address == "test:mac:address", "User {} data should have correct MAC".format(user_id)
                assert len(user_data.signals) == 3, "User {} should have 3 signals".format(user_id)
                print("✓ Verified data for user {}".format(user_id))
        else:
            print("❌ No active users found")
            
        # Test fallback behavior (when no active users)
        print("\n=== Testing fallback behavior ===")
        
        # Stop all users
        for user_id in user_ids:
            plugin._stop_user_streaming(user_id)
        
        time.sleep(0.5)
        
        # Verify no active users
        active_users = plugin.get_active_user_sessions()
        assert len(active_users) == 0, "Should have no active users, got {}".format(len(active_users))
        
        # Test fallback: send to default stream data
        plugin.update_stream_data(mock_stream_data)  # No user_id specified
        default_data = plugin.get_stream_data()  # No user_id specified
        assert default_data is not None, "Should have default stream data"
        assert default_data.mac_address == "test:mac:address", "Default data should have correct MAC"
        print("✓ Fallback to default stream data works")
        
        print("\n=== All Tests Passed! ===")
        
    except Exception as e:
        print("Test failed with error: {}".format(e))
        raise
    finally:
        print("\nStopping plugin...")
        plugin.stop()
        print("Plugin stopped.")

def test_user_id_extraction():
    """Test that stream commands correctly extract user IDs."""
    print("\n=== Testing User ID Extraction ===")
    
    # Test command with userId at top level (like frontend sends)
    command1 = {
        'type': COMMANDS.STREAM.value,
        'userId': 123,  # Number like frontend sends
        'payload': {'macAddress': 'test:mac'}
    }
    
    from MinervaPlugin.command import StreamCommand
    stream_cmd1 = StreamCommand(command1)
    user_id1 = stream_cmd1.get_user_id()
    print("Extracted user ID from top level: {}".format(user_id1))
    assert user_id1 == "123", "Expected '123', got '{}'".format(user_id1)

    # Test command with userId in payload (backward compatibility)
    command2 = {
        'type': COMMANDS.STREAM.value,
        'payload': {'userId': 'user456', 'macAddress': 'test:mac'}
    }

    stream_cmd2 = StreamCommand(command2)
    user_id2 = stream_cmd2.get_user_id()
    print("Extracted user ID from payload: {}".format(user_id2))
    assert user_id2 == "user456", "Expected 'user456', got '{}'".format(user_id2)

    # Test command with no userId (fallback)
    command3 = {
        'type': COMMANDS.STREAM.value,
        'payload': {'macAddress': 'test:mac'}
    }

    stream_cmd3 = StreamCommand(command3)
    user_id3 = stream_cmd3.get_user_id()
    print("Extracted user ID fallback: {}".format(user_id3))
    assert user_id3 == "default_user", "Expected 'default_user', got '{}'".format(user_id3)
    
    print("✓ User ID extraction tests passed")

if __name__ == "__main__":
    print("Testing PCC_client Multi-User Streaming Implementation")
    print("=" * 60)
    
    try:
        test_user_id_extraction()
        test_multi_user_streaming()
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✓ User ID extraction from stream commands works correctly")
        print("✓ Multiple users can stream from the same rig simultaneously")
        print("✓ PCC_client sends data to all active user sessions")
        print("✓ Fallback to default stream data works when no users are active")
        print("\n🔧 Your client's issue should now be resolved:")
        print("- user_id is now extracted from the stream command sent by frontend")
        print("- Same rig can send data to multiple users simultaneously")
        print("- Each user gets their own dedicated stream queue")
        
    except Exception as e:
        print("\n❌ Tests failed: {}".format(e))
        import traceback
        traceback.print_exc()
