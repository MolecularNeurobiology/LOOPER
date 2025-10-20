#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify dict-based command system works correctly.
This replaces the old typed command classes with simple dict-based commands.
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ..models.command import (
    LEGACY_COMMAND_MAPPING, SEEDED_COMMANDS,
    map_legacy_command, getCommandFilename, getStep
)

def test_legacy_command_mapping():
    """Test that legacy commands are properly mapped to new seeded commands"""
    print("Testing legacy command mapping...")
    
    # Test legacy mappings
    assert map_legacy_command('start') == 'initialize_rig'
    assert map_legacy_command('load_pups') == 'send_filename'
    assert map_legacy_command('go_to_next') == 'go_to_next'  # No change
    
    # Test legacy detection
    assert is_legacy_command('start') == True
    assert is_legacy_command('load_pups') == True
    assert is_legacy_command('initialize_rig') == False
    
    print("[PASS] Legacy command mapping tests passed")

def test_seeded_command_validation():
    """Test seeded command validation"""
    print("Testing seeded command validation...")
    
    # Test seeded command detection
    assert is_seeded_command('initialize_rig') == True
    assert is_seeded_command('send_filename') == True
    assert is_seeded_command('go_to_next') == True
    assert is_seeded_command('unknown_command') == False
    
    print("[PASS] Seeded command validation tests passed")

def test_command_structure_validation():
    """Test command structure validation"""
    print("Testing command structure validation...")

    # Valid command
    valid_command = {
        'type': 'initialize_rig',
        'macAddress': 'AA:BB:CC:DD:EE:FF',
        'payload': {}
    }
    assert validate_command_structure(valid_command) == True

    # Missing type
    invalid_command1 = {
        'macAddress': 'AA:BB:CC:DD:EE:FF',
        'payload': {}
    }
    assert validate_command_structure(invalid_command1) == False

    # Missing macAddress
    invalid_command2 = {
        'type': 'initialize_rig',
        'payload': {}
    }
    assert validate_command_structure(invalid_command2) == False

    # Invalid payload type
    invalid_command3 = {
        'type': 'initialize_rig',
        'macAddress': 'AA:BB:CC:DD:EE:FF',
        'payload': 'invalid'
    }
    assert validate_command_structure(invalid_command3) == False

    print("[PASS] Command structure validation tests passed")

def test_command_data_extraction():
    """Test extracting data from command dicts"""
    print("Testing command data extraction...")
    
    # Test command with user ID and MAC address
    command = {
        'type': 'send_filename',
        'macAddress': 'AA:BB:CC:DD:EE:FF',
        'userId': 123,
        'payload': {
            'filename': 'test.csv',
            'stages': [{'name': 'stage1'}, {'name': 'stage2'}]
        }
    }
    
    assert get_command_user_id(command) == '123'
    assert get_command_mac_address(command) == 'AA:BB:CC:DD:EE:FF'
    assert len(get_command_stages(command)) == 2
    
    # Test command with user ID in payload
    command2 = {
        'type': 'stream',
        'macAddress': 'BB:CC:DD:EE:FF:AA',
        'payload': {
            'userId': 456
        }
    }
    
    assert get_command_user_id(command2) == '456'
    assert get_command_mac_address(command2) == 'BB:CC:DD:EE:FF:AA'
    
    print("[PASS] Command data extraction tests passed")

def test_command_creation():
    """Test creating properly structured commands"""
    print("Testing command creation...")

    # Create simple command
    cmd1 = create_command('initialize_rig', 'AA:BB:CC:DD:EE:FF')
    assert cmd1['type'] == 'initialize_rig'
    assert cmd1['macAddress'] == 'AA:BB:CC:DD:EE:FF'
    assert cmd1['payload'] == {}
    assert 'userId' not in cmd1

    # Create command with payload and user ID
    payload = {'filename': 'experiment.csv'}
    cmd2 = create_command('send_filename', 'BB:CC:DD:EE:FF:AA', payload, 789)
    assert cmd2['type'] == 'send_filename'
    assert cmd2['macAddress'] == 'BB:CC:DD:EE:FF:AA'
    assert cmd2['payload'] == payload
    assert cmd2['userId'] == 789

    print("[PASS] Command creation tests passed")

def test_real_world_scenarios():
    """Test real-world command scenarios"""
    print("Testing real-world scenarios...")
    
    # Scenario 1: Legacy 'start' command received
    legacy_start = {
        'type': 'start',
        'macAddress': 'AA:BB:CC:DD:EE:FF',
        'payload': {}
    }
    
    # Map to new command
    new_type = map_legacy_command(legacy_start['type'])
    assert new_type == 'initialize_rig'
    
    # Scenario 2: New 'send_filename' command
    send_file_cmd = create_command(
        'send_filename', 
        'BB:CC:DD:EE:FF:AA',
        {'filename': 'data.csv'},
        user_id=123
    )
    
    assert validate_command_structure(send_file_cmd)
    assert get_command_user_id(send_file_cmd) == '123'
    
    # Scenario 3: Stream command with stages
    stream_cmd = {
        'type': 'stream',
        'macAddress': 'CC:DD:EE:FF:AA:BB',
        'userId': 456,
        'payload': {
            'stages': [
                {'name': 'calibration', 'type': 'timed', 'durationInSeconds': 30},
                {'name': 'measurement', 'type': 'wait_for_user'}
            ]
        }
    }
    
    stages = get_command_stages(stream_cmd)
    assert len(stages) == 2
    assert stages[0]['name'] == 'calibration'
    assert stages[1]['name'] == 'measurement'
    
    print("[PASS] Real-world scenario tests passed")

def main():
    """Run all tests"""
    print("Testing Dict-Based Command System")
    print("=" * 50)

    try:
        test_legacy_command_mapping()
        test_seeded_command_validation()
        test_command_structure_validation()
        test_command_data_extraction()
        test_command_creation()
        test_real_world_scenarios()

        print("=" * 50)
        print("All tests passed! Dict-based command system is working correctly.")
        print("\nThe system now supports:")
        print("- Legacy command mapping (start -> initialize_rig, load_pups -> send_filename)")
        print("- Seeded command validation")
        print("- Proper command structure validation")
        print("- Data extraction from command dicts")
        print("- Command creation utilities")
        print("- Real-world usage scenarios")

    except AssertionError as e:
        print("[FAIL] Test failed: {}".format(e))
        sys.exit(1)
    except Exception as e:
        print("[ERROR] Unexpected error: {}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
