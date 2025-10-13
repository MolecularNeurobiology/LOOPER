#!/usr/bin/env python3
"""
Test RabbitMQ Connection with Detailed Logging
This script tests the RabbitMQ connection exactly like PCC does, with detailed logging
"""

import os
import sys
import logging

# Add the MinervaPlugin core directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'MinervaPlugin', 'core'))

def setup_logging():
    """Set up detailed logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_rabbitmq_connection():
    """Test RabbitMQ connection like PCC does"""
    logger = setup_logging()
    
    print("🧪 Testing RabbitMQ Connection (PCC Style)")
    print("=" * 60)
    
    try:
        # Import config
        from config import RABBITMQ_SERVER, RABBITMQ_PORT, RABBITMQ_AMQP_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD
        
        print(f"📋 Configuration:")
        print(f"   Server: {RABBITMQ_SERVER}")
        print(f"   AMQP Port: {RABBITMQ_AMQP_PORT}")
        print(f"   Management Port: {RABBITMQ_PORT}")
        print(f"   User: {RABBITMQ_USER}")
        print(f"   Password: {'*' * len(RABBITMQ_PASSWORD)}")
        print("")
        
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    try:
        # Import RabbitMQ client
        from rabbitmq_client import RabbitMQClient
        print("✅ RabbitMQ client imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import RabbitMQ client: {e}")
        return False
    
    # Test different types of connections like PCC does
    test_cases = [
        ("ping", "ping", None, False),
        ("command_queue", "command_queue", "aa:bb:cc:dd:ee:ff", False),
        ("stream_control", "stream_control", "aa:bb:cc:dd:ee:ff", True),
        ("rig_stream", "rig_stream", "aa:bb:cc:dd:ee:ff", True),
    ]
    
    success_count = 0
    
    for test_name, queue_name, mac_id, use_ttl in test_cases:
        print(f"\n🔄 Testing {test_name} connection...")
        print(f"   Queue: {queue_name}")
        print(f"   MAC ID: {mac_id}")
        print(f"   Use TTL: {use_ttl}")
        
        try:
            # Create RabbitMQ client exactly like PCC does
            client = RabbitMQClient(
                logger=logger,
                queue=queue_name,
                id=mac_id,
                use_ttl=use_ttl,
                ttl_seconds=10 if use_ttl else None
            )
            
            print(f"   ✅ {test_name} client created successfully")
            
            # Test sending a message
            test_message = f"test message from {test_name}"
            if client.send_message(test_message):
                print(f"   ✅ {test_name} message sent successfully")
                success_count += 1
            else:
                print(f"   ❌ {test_name} message send failed")
            
            # Close the client
            client.close()
            print(f"   ✅ {test_name} client closed")
            
        except Exception as e:
            print(f"   ❌ {test_name} connection failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Results: {success_count}/{len(test_cases)} connections successful")
    
    if success_count == len(test_cases):
        print("🎉 ALL RABBITMQ CONNECTIONS SUCCESSFUL!")
        print("✅ PCC should be able to connect to RabbitMQ")
        return True
    else:
        print("❌ SOME RABBITMQ CONNECTIONS FAILED")
        print("💡 PCC will likely crash due to connection issues")
        return False

def test_plugin_initialization():
    """Test MinervaPlugin initialization like PCC does"""
    print(f"\n🔌 Testing MinervaPlugin Initialization")
    print("-" * 40)
    
    try:
        # Import plugin modules
        from plugin import Plugin, PluginRegistration
        
        # Create registration params like PCC does
        registration = PluginRegistration(mac_address="aa:bb:cc:dd:ee:ff")
        
        # Set up logger
        logger = setup_logging()
        
        print("🔄 Creating MinervaPlugin instance...")
        
        # Create plugin instance (this is where PCC usually crashes)
        plugin = Plugin(registration, logger)
        
        print("✅ MinervaPlugin created successfully!")
        print("✅ All RabbitMQ clients initialized")
        
        # Clean up
        plugin.stop()
        print("✅ Plugin stopped cleanly")
        
        return True
        
    except Exception as e:
        print(f"❌ Plugin initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 PCC RabbitMQ Connection Test")
    print("=" * 60)
    print("This script tests RabbitMQ connections exactly like PCC does")
    print("")
    
    # Test basic RabbitMQ connection
    rabbitmq_success = test_rabbitmq_connection()
    
    # Test plugin initialization
    plugin_success = test_plugin_initialization()
    
    print("\n" + "=" * 60)
    print("🏁 Test Summary:")
    print(f"   RabbitMQ Connections: {'✅ PASS' if rabbitmq_success else '❌ FAIL'}")
    print(f"   Plugin Initialization: {'✅ PASS' if plugin_success else '❌ FAIL'}")
    
    if rabbitmq_success and plugin_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ PCC should work with current configuration")
    else:
        print("\n❌ TESTS FAILED!")
        print("💡 Fix the issues above before running PCC")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check RabbitMQ server is running: docker ps")
        print("2. Create RabbitMQ user for remote access:")
        print("   docker exec minerva-rabbit-mq-1 rabbitmqctl add_user minerva_user secure_password")
        print("   docker exec minerva-rabbit-mq-1 rabbitmqctl set_permissions minerva_user '.*' '.*' '.*'")
        print("3. Update config.py with new credentials")
        print("4. Test network connectivity: python MinervaPlugin/test_network_connection.py")

if __name__ == "__main__":
    main()
