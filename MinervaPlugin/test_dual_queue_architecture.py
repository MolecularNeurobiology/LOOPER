#!/usr/bin/env python3
"""
Test script for the new dual queue architecture implementation.

This script tests:
1. New RabbitMQ client initialization
2. Stream control command handling
3. Active user tracking
4. Rig stream data generation
"""

import sys
import time
import threading
from datetime import datetime

# Mock the RabbitMQ client to avoid dependency issues
class MockRabbitMQClient:
    def __init__(self, logger, queue, id=None, use_ttl=False):
        self.logger = logger
        self.queue = queue
        self.id = id
        self.use_ttl = use_ttl
        self.is_consuming = False

    def send_message(self, message):
        pass

    def consume_message(self, callback):
        self.is_consuming = True

    def stop_consuming(self):
        self.is_consuming = False

# Mock the imports to avoid RabbitMQ dependency
import sys
from unittest.mock import Mock

# Mock the modules
sys.modules['pika'] = Mock()
sys.modules['rabbitmq_client'] = Mock()
sys.modules['rabbitmq_client'].RabbitMQClient = MockRabbitMQClient

# Import the plugin and related classes
try:
    from plugin import Plugin, PluginRegistration, MinervaStreamData
    from command import COMMANDS
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the MinervaPlugin directory")
    sys.exit(1)

def setup_logger():
    """Setup a simple logger for testing."""
    import logging
    
    logger = logging.getLogger('test_dual_queue')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def simulate_stream_heartbeat(user_id="test_user", mac_address="test:mac:address"):
    """
    Simulate a stream heartbeat command.
    
    Args:
        user_id (str): The user ID sending the heartbeat.
        mac_address (str): The MAC address for the device.
    
    Returns:
        dict: A stream heartbeat command.
    """
    return {
        'type': 'stream',
        'userId': user_id,
        'macAddress': mac_address,
        'payload': {}
    }

def simulate_control_command(command_type="go_to_next", mac_address="test:mac:address"):
    """
    Simulate a control command.
    
    Args:
        command_type (str): The type of control command.
        mac_address (str): The MAC address for the device.
    
    Returns:
        dict: A control command.
    """
    return {
        'type': command_type,
        'macAddress': mac_address,
        'payload': {}
    }

def test_dual_queue_initialization():
    """Test that the plugin initializes with dual queue architecture."""
    print("\n" + "="*60)
    print("TEST: Dual Queue Initialization")
    print("="*60)

    logger = setup_logger()
    registration = PluginRegistration(mac_address="test:mac:address")

    try:
        # Patch the RabbitMQClient in the plugin module
        import plugin
        original_client = plugin.RabbitMQClient
        plugin.RabbitMQClient = MockRabbitMQClient

        plugin_instance = Plugin(registration, logger)

        # Check that new components are initialized
        assert hasattr(plugin_instance, '_stream_control_consumer'), "Stream control consumer not initialized"
        assert hasattr(plugin_instance, '_rig_stream_producer'), "Rig stream producer not initialized"
        assert hasattr(plugin_instance, '_active_users'), "Active users set not initialized"
        assert hasattr(plugin_instance, '_last_heartbeat'), "Last heartbeat dict not initialized"
        assert hasattr(plugin_instance, '_heartbeat_lock'), "Heartbeat lock not initialized"

        # Check initial state
        assert len(plugin_instance._active_users) == 0, "Active users should start empty"
        assert len(plugin_instance._last_heartbeat) == 0, "Last heartbeat should start empty"

        print("✅ All new components initialized successfully")

        # Restore original client
        plugin.RabbitMQClient = original_client

        return plugin_instance

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_active_user_tracking(plugin):
    """Test the active user tracking functionality."""
    print("\n" + "="*60)
    print("TEST: Active User Tracking")
    print("="*60)
    
    if not plugin:
        print("❌ Plugin not available for testing")
        return False
    
    try:
        # Test initial state
        assert plugin.get_active_users_count() == 0, "Initial active users should be 0"
        assert not plugin.has_active_users(), "Should have no active users initially"
        
        # Simulate stream heartbeats
        heartbeat1 = simulate_stream_heartbeat("user1")
        heartbeat2 = simulate_stream_heartbeat("user2")
        
        # Process heartbeats directly (simulating stream control consumer)
        plugin._handle_stream_control(heartbeat1)
        plugin._handle_stream_control(heartbeat2)
        
        # Check active users
        assert plugin.get_active_users_count() == 2, f"Expected 2 active users, got {plugin.get_active_users_count()}"
        assert plugin.has_active_users(), "Should have active users"
        
        active_users = plugin.get_active_users_list()
        assert "user1" in active_users, "User1 should be active"
        assert "user2" in active_users, "User2 should be active"
        
        print(f"✅ Active user tracking working: {active_users}")
        return True
        
    except Exception as e:
        print(f"❌ Active user tracking failed: {e}")
        return False

def test_signal_generation(plugin):
    """Test the signal generation functionality."""
    print("\n" + "="*60)
    print("TEST: Signal Generation")
    print("="*60)
    
    if not plugin:
        print("❌ Plugin not available for testing")
        return False
    
    try:
        # Test signal generation
        signals = plugin._generate_mock_signals()
        
        assert isinstance(signals, list), "Signals should be a list"
        assert len(signals) > 0, "Should generate at least one signal"
        
        # Check for expected signal types
        signal_names = [s['name'] for s in signals]
        expected_signals = ['ECG', 'BPM', 'Airflow', 'avgHR', 'Status', 'Debug Info']
        
        for expected in expected_signals:
            assert expected in signal_names, f"Missing expected signal: {expected}"
        
        # Check signal structure
        ecg_signal = next(s for s in signals if s['name'] == 'ECG')
        assert ecg_signal['type'] == 'time_series', "ECG should be time_series type"
        assert 'data' in ecg_signal, "ECG should have data"
        assert len(ecg_signal['data']) > 0, "ECG should have data points"
        
        print(f"✅ Signal generation working: {len(signals)} signals generated")
        print(f"   Signal names: {signal_names}")
        return True
        
    except Exception as e:
        print(f"❌ Signal generation failed: {e}")
        return False

def test_stream_data_generation(plugin):
    """Test the complete stream data generation."""
    print("\n" + "="*60)
    print("TEST: Stream Data Generation")
    print("="*60)
    
    if not plugin:
        print("❌ Plugin not available for testing")
        return False
    
    try:
        # Generate stream data
        stream_data = plugin._generate_current_stream_data()
        
        assert isinstance(stream_data, dict), "Stream data should be a dict"
        assert 'mac_address' in stream_data, "Should have mac_address"
        assert 'signals' in stream_data, "Should have signals"
        
        assert stream_data['mac_address'] == "test:mac:address", "MAC address should match"
        assert len(stream_data['signals']) > 0, "Should have signals"
        
        print(f"✅ Stream data generation working")
        print(f"   MAC: {stream_data['mac_address']}")
        print(f"   Signals: {len(stream_data['signals'])}")
        return True
        
    except Exception as e:
        print(f"❌ Stream data generation failed: {e}")
        return False

def test_heartbeat_cleanup(plugin):
    """Test the heartbeat cleanup functionality."""
    print("\n" + "="*60)
    print("TEST: Heartbeat Cleanup")
    print("="*60)

    if not plugin:
        print("❌ Plugin not available for testing")
        return False

    try:
        # Clear any existing users first
        with plugin._heartbeat_lock:
            plugin._active_users.clear()
            plugin._last_heartbeat.clear()

        # Add a user and then test cleanup
        heartbeat = simulate_stream_heartbeat("cleanup_user")
        plugin._handle_stream_control(heartbeat)

        assert plugin.get_active_users_count() == 1, f"Should have 1 active user, got {plugin.get_active_users_count()}"

        # Manually set an old heartbeat time to simulate timeout
        from datetime import timedelta
        with plugin._heartbeat_lock:
            plugin._last_heartbeat["cleanup_user"] = datetime.now() - timedelta(seconds=35)

        # Run cleanup
        plugin._cleanup_inactive_users()

        assert plugin.get_active_users_count() == 0, f"User should be cleaned up after timeout, got {plugin.get_active_users_count()}"

        print("✅ Heartbeat cleanup working")
        return True

    except Exception as e:
        print(f"❌ Heartbeat cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dual_command_processing(plugin):
    """Test that critical commands and stream commands are processed separately."""
    print("\n" + "="*60)
    print("TEST: Dual Command Processing")
    print("="*60)

    if not plugin:
        print("❌ Plugin not available for testing")
        return False

    try:
        # Clear any existing state
        with plugin._heartbeat_lock:
            plugin._active_users.clear()
            plugin._last_heartbeat.clear()
        with plugin._commands_lock:
            plugin._commands.clear()

        # Test 1: Critical commands should be processed by _handle_command
        start_command = simulate_control_command("start")
        go_next_command = simulate_control_command("go_to_next")
        stop_command = simulate_control_command("stop_stream")

        # Process critical commands
        plugin._handle_command(start_command)
        plugin._handle_command(go_next_command)
        plugin._handle_command(stop_command)

        # Check that critical commands were queued
        with plugin._commands_lock:
            command_count = len(plugin._commands)

        assert command_count == 3, f"Expected 3 critical commands queued, got {command_count}"

        # Test 2: Stream commands should NOT be processed by _handle_command
        stream_command = simulate_stream_heartbeat("test_user")

        # This should NOT add to the command queue
        initial_count = command_count
        plugin._handle_command(stream_command)  # This should reject the stream command

        with plugin._commands_lock:
            final_count = len(plugin._commands)

        assert final_count == initial_count, f"Stream command should not be added to critical command queue"

        # Test 3: Stream commands should be processed by _handle_stream_control
        plugin._handle_stream_control(stream_command)

        assert plugin.get_active_users_count() == 1, "Stream command should add user to active set"
        assert "test_user" in plugin.get_active_users_list(), "User should be in active list"

        # Test 4: Check dual queue mode
        assert plugin.is_dual_queue_mode(), "Plugin should be in dual queue mode"

        stats = plugin.get_command_processing_stats()
        assert stats['active_users'] == 1, "Should have 1 active user in new architecture"
        assert stats['pending_critical_commands'] == 3, "Should have 3 pending critical commands"
        assert stats['architecture_mode'] == 'dual_queue_pure', "Should be in pure dual queue mode"

        print("✅ Dual command processing working correctly")
        print(f"   Critical commands queued: {stats['pending_critical_commands']}")
        print(f"   Active streaming users: {stats['active_users']}")
        print(f"   Architecture mode: {stats['architecture_mode']}")
        return True

    except Exception as e:
        print(f"❌ Dual command processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streaming_logic_integration(plugin):
    """Test that the streaming logic is properly integrated with the new architecture."""
    print("\n" + "="*60)
    print("TEST: Streaming Logic Integration")
    print("="*60)

    if not plugin:
        print("❌ Plugin not available for testing")
        return False

    try:
        # Clear any existing state
        with plugin._heartbeat_lock:
            plugin._active_users.clear()
            plugin._last_heartbeat.clear()

        # Test 1: No streaming when no active users
        assert not plugin.get_is_streaming(), "Should not be streaming with no active users"
        assert not plugin.has_active_users(), "Should have no active users"
        assert plugin.get_user_session_count() == 0, "Should have 0 user sessions"

        # Test 2: Add users and verify streaming state
        user1_heartbeat = simulate_stream_heartbeat("user1")
        user2_heartbeat = simulate_stream_heartbeat("user2")

        plugin._handle_stream_control(user1_heartbeat)
        plugin._handle_stream_control(user2_heartbeat)

        assert plugin.get_is_streaming(), "Should be streaming with active users"
        assert plugin.has_active_users(), "Should have active users"
        assert plugin.get_user_session_count() == 2, "Should have 2 user sessions"

        # Test 3: Check individual user streaming status
        assert plugin.is_user_streaming("user1"), "User1 should be streaming"
        assert plugin.is_user_streaming("user2"), "User2 should be streaming"
        assert not plugin.is_user_streaming("user3"), "User3 should not be streaming"

        # Test 4: Get active user sessions
        active_sessions = plugin.get_active_user_sessions()
        assert "user1" in active_sessions, "User1 should be in active sessions"
        assert "user2" in active_sessions, "User2 should be in active sessions"
        assert len(active_sessions) == 2, "Should have 2 active sessions"

        # Test 5: Stop streaming for one user
        plugin._stop_user_streaming("user1")

        assert plugin.get_user_session_count() == 1, "Should have 1 user session after stopping user1"
        assert not plugin.is_user_streaming("user1"), "User1 should not be streaming after stop"
        assert plugin.is_user_streaming("user2"), "User2 should still be streaming"

        # Test 6: Stop all streaming
        plugin._stop_user_streaming("user2")

        assert not plugin.get_is_streaming(), "Should not be streaming after stopping all users"
        assert plugin.get_user_session_count() == 0, "Should have 0 user sessions"

        print("✅ Streaming logic integration working correctly")
        print(f"   Final active users: {plugin.get_user_session_count()}")
        print(f"   Is streaming: {plugin.get_is_streaming()}")
        return True

    except Exception as e:
        print(f"❌ Streaming logic integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests for the dual queue architecture."""
    print("🧪 Testing Dual Queue Architecture Implementation")
    print("=" * 80)
    
    # Test 1: Initialization
    plugin = test_dual_queue_initialization()
    
    if not plugin:
        print("\n❌ Cannot continue testing without successful initialization")
        return False
    
    # Test 2: Active user tracking
    user_tracking_success = test_active_user_tracking(plugin)
    
    # Test 3: Signal generation
    signal_generation_success = test_signal_generation(plugin)
    
    # Test 4: Stream data generation
    stream_data_success = test_stream_data_generation(plugin)
    
    # Test 5: Dual command processing
    dual_command_success = test_dual_command_processing(plugin)

    # Test 6: Streaming logic integration
    streaming_integration_success = test_streaming_logic_integration(plugin)

    # Test 7: Heartbeat cleanup
    cleanup_success = test_heartbeat_cleanup(plugin)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    tests = [
        ("Dual Queue Initialization", plugin is not None),
        ("Active User Tracking", user_tracking_success),
        ("Signal Generation", signal_generation_success),
        ("Stream Data Generation", stream_data_success),
        ("Dual Command Processing", dual_command_success),
        ("Streaming Logic Integration", streaming_integration_success),
        ("Heartbeat Cleanup", cleanup_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dual queue architecture is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
