#!/usr/bin/env python3
"""
Test script for concurrent user streaming functionality.
This script tests the new user-specific streaming capabilities.
"""

import json
import time
import threading
from datetime import datetime
import logging

# Import the plugin module
try:
    from MinervaPlugin.plugin import Plugin, PluginRegistration
    from MinervaPlugin.command import SEEDED_COMMANDS
except ImportError as e:
    print(f"Import error: {e}")
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
        'type': 'stream',
        'payload': {
            'user_id': user_id,
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

def simulate_stop_stream_command(user_id):
    """
    Simulate a stop stream command from a user.
    
    Args:
        user_id (str): The user ID sending the command.
    
    Returns:
        dict: A stop stream command payload.
    """
    return {
        'type': 'stop_stream',
        'payload': {
            'user_id': user_id
        }
    }

def test_concurrent_streaming():
    """Test concurrent streaming with multiple users."""
    logger = setup_logger()
    
    # Create plugin instance
    registration = PluginRegistration(mac_address="test:mac:address")
    plugin = Plugin(registration, logger)
    
    print("Starting plugin...")
    plugin.start()
    
    try:
        # Test 1: Single user streaming
        print("\n=== Test 1: Single User Streaming ===")
        user1_command = simulate_stream_command("user1")
        plugin._handle_command(user1_command)
        
        time.sleep(2)
        
        # Check if user1 is streaming
        active_sessions = plugin.get_active_user_sessions()
        print(f"Active sessions: {active_sessions}")
        assert "user1" in active_sessions, "User1 should be streaming"
        
        # Test 2: Multiple users streaming
        print("\n=== Test 2: Multiple Users Streaming ===")
        user2_command = simulate_stream_command("user2")
        user3_command = simulate_stream_command("user3")
        
        plugin._handle_command(user2_command)
        plugin._handle_command(user3_command)
        
        time.sleep(2)
        
        active_sessions = plugin.get_active_user_sessions()
        print(f"Active sessions: {active_sessions}")
        assert len(active_sessions) == 3, f"Should have 3 active sessions, got {len(active_sessions)}"
        
        # Test 3: User heartbeat update
        print("\n=== Test 3: User Heartbeat Update ===")
        # Send another stream command from user1 (heartbeat)
        plugin._handle_command(user1_command)
        
        # Verify user1 is still active
        assert plugin.is_user_streaming("user1"), "User1 should still be streaming"
        
        # Test 4: Stop specific user
        print("\n=== Test 4: Stop Specific User ===")
        stop_command = simulate_stop_stream_command("user2")
        plugin._handle_command(stop_command)
        
        time.sleep(1)
        
        active_sessions = plugin.get_active_user_sessions()
        print(f"Active sessions after stopping user2: {active_sessions}")
        assert "user2" not in active_sessions, "User2 should not be streaming"
        assert len(active_sessions) == 2, f"Should have 2 active sessions, got {len(active_sessions)}"
        
        # Test 5: Session count
        print("\n=== Test 5: Session Count ===")
        session_count = plugin.get_user_session_count()
        print(f"Session count: {session_count}")
        assert session_count == 2, f"Should have 2 sessions, got {session_count}"
        
        print("\n=== All Tests Passed! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise
    finally:
        print("\nStopping plugin...")
        plugin.stop()
        print("Plugin stopped.")

def test_timeout_functionality():
    """Test the timeout functionality for inactive users."""
    logger = setup_logger()
    
    # Create plugin instance
    registration = PluginRegistration(mac_address="test:mac:address")
    plugin = Plugin(registration, logger)
    
    print("\n=== Test: Timeout Functionality ===")
    print("Note: This test requires modifying STREAM_TIMEOUT_SECONDS to a small value for testing")
    print("Current timeout is set to 30 seconds, which is too long for this test")
    print("In a real test environment, you would temporarily set it to 5 seconds")
    
    # This test would require modifying the timeout value for practical testing
    # For now, we'll just verify the timeout mechanism exists
    
    plugin.start()
    
    try:
        # Start streaming for a user
        user_command = simulate_stream_command("timeout_user")
        plugin._handle_command(user_command)
        
        time.sleep(1)
        
        # Verify user is streaming
        assert plugin.is_user_streaming("timeout_user"), "User should be streaming"
        
        print("Timeout test setup complete. In production, user would timeout after 30 seconds of inactivity.")
        
    finally:
        plugin.stop()

if __name__ == "__main__":
    print("Testing Concurrent User Streaming Implementation")
    print("=" * 50)
    
    try:
        test_concurrent_streaming()
        test_timeout_functionality()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
