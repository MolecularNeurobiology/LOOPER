#!/usr/bin/env python3
"""
Test script to verify the 30-second timeout functionality.
This script demonstrates that streaming auto-stops after 30 seconds without stream commands.
"""

import time
import logging
from datetime import datetime
from plugin import Plugin, PluginRegistration
from command import COMMANDS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def simulate_stream_command(user_id="test_user", mac_address="test:mac:address"):
    """Simulate a stream command from a user."""
    return {
        'type': COMMANDS.STREAM.value,
        'userId': user_id,
        'macAddress': mac_address,
        'payload': {
            'stages': [{'name': 'test_stage', 'type': 'timed', 'durationInSeconds': 60}],
            'signals': [{'name': 'test_signal', 'type': 'single_value', 'data': 42.0}],
            'currentStage': 'test_stage'
        }
    }

def test_timeout_functionality():
    """Test that streaming stops after 30 seconds without stream commands."""
    print("Testing 30-second timeout functionality")
    print("=" * 50)

    # Create plugin instance
    registration = PluginRegistration("test:timeout:device")
    plugin = Plugin(registration, logging.getLogger())

    try:
        # Start the plugin
        plugin.start()
        time.sleep(1)  # Let it initialize

        # Send initial stream command to start streaming
        user_id = "timeout_test_user"
        stream_command = simulate_stream_command(user_id)
        plugin._handle_command(stream_command)

        print(f"✅ Started streaming for user {user_id}")
        print(f"📊 Active sessions: {plugin.get_user_session_count()}")

        # Verify user is streaming
        assert plugin.is_user_streaming(user_id), "User should be streaming"

        print("\n⏰ Waiting for 35 seconds to test timeout...")
        print("(Timeout should trigger after 30 seconds)")

        # Wait and check status every 5 seconds
        for i in range(7):  # 7 * 5 = 35 seconds
            time.sleep(5)
            session_count = plugin.get_user_session_count()
            is_streaming = plugin.is_user_streaming(user_id)
            elapsed = (i + 1) * 5

            print(f"⏱️  {elapsed}s elapsed - Sessions: {session_count}, User streaming: {is_streaming}")

            # After 30 seconds, the session should be cleaned up
            if elapsed >= 30 and not is_streaming:
                print(f"✅ SUCCESS: Streaming stopped after {elapsed} seconds (timeout worked!)")
                break
        else:
            print("❌ FAILURE: Streaming did not stop after 35 seconds")
            return False

        # Final verification
        final_session_count = plugin.get_user_session_count()
        final_is_streaming = plugin.is_user_streaming(user_id)

        print(f"\n📊 Final status:")
        print(f"   - Active sessions: {final_session_count}")
        print(f"   - User streaming: {final_is_streaming}")

        if final_session_count == 0 and not final_is_streaming:
            print("✅ SUCCESS: Timeout functionality working correctly!")
            return True
        else:
            print("❌ FAILURE: Session was not properly cleaned up")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        plugin.stop()

def test_heartbeat_refresh():
    """Test that sending stream commands refreshes the heartbeat and prevents timeout."""
    print("\n🧪 Testing heartbeat refresh functionality")
    print("=" * 50)

    registration = PluginRegistration("test:heartbeat:device")
    plugin = Plugin(registration, logging.getLogger())

    try:
        plugin.start()
        time.sleep(1)

        user_id = "heartbeat_test_user"
        stream_command = simulate_stream_command(user_id)
        plugin._handle_command(stream_command)

        print(f"✅ Started streaming for user {user_id}")

        # Send stream commands every 10 seconds for 40 seconds
        for i in range(4):  # 4 * 10 = 40 seconds
            time.sleep(10)
            plugin._handle_command(stream_command)  # Refresh heartbeat
            elapsed = (i + 1) * 10
            is_streaming = plugin.is_user_streaming(user_id)
            print(f"⏱️  {elapsed}s elapsed - Sent heartbeat, User streaming: {is_streaming}")

            if not is_streaming:
                print(f"❌ FAILURE: Streaming stopped unexpectedly at {elapsed}s")
                return False

        print("✅ SUCCESS: Heartbeat refresh prevents timeout!")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        plugin.stop()

if __name__ == "__main__":
    print("🔬 Testing Streaming Timeout Functionality")
    print("=" * 60)

    try:
        # Test 1: Verify timeout works
        success1 = test_timeout_functionality()

        # Test 2: Verify heartbeat refresh works
        success2 = test_heartbeat_refresh()

        print("\n" + "=" * 60)
        print("📋 SUMMARY:")
        print(f"   Timeout test: {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"   Heartbeat test: {'✅ PASS' if success2 else '❌ FAIL'}")

        if success1 and success2:
            print("\n🎉 All timeout functionality tests PASSED!")
        else:
            print("\n💥 Some tests FAILED!")

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
