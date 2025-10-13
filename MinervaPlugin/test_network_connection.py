#!/usr/bin/env python3
"""
Network connectivity test script for Minerva RabbitMQ connection
This script helps diagnose network issues when connecting to a remote Minerva server
"""

import socket
import time
import sys
import os
import requests
from urllib.parse import urlparse

# Add the core directory to the path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

try:
    from config import RABBITMQ_SERVER, RABBITMQ_PORT, RABBITMQ_AMQP_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD
except ImportError:
    print("❌ Could not import config. Make sure you're running this from the MinervaPlugin directory.")
    sys.exit(1)

def test_socket_connection(host, port, timeout=10):
    """Test basic socket connectivity to a host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"   Exception: {e}")
        return False

def test_rabbitmq_management_ui(host, port, user, password):
    """Test RabbitMQ Management UI accessibility"""
    try:
        url = f"http://{host}:{port}/api/overview"
        response = requests.get(url, auth=(user, password), timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"   Exception: {e}")
        return False

def test_ping(host):
    """Test basic ping connectivity"""
    try:
        # Use ping command (works on Windows, Linux, macOS)
        import subprocess
        if os.name == 'nt':  # Windows
            result = subprocess.run(['ping', '-n', '1', host], 
                                  capture_output=True, text=True, timeout=10)
        else:  # Linux/macOS
            result = subprocess.run(['ping', '-c', '1', host], 
                                  capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"   Exception: {e}")
        return False

def main():
    print("🔍 Minerva Network Connectivity Test")
    print("=" * 50)
    print(f"Target Server: {RABBITMQ_SERVER}")
    print(f"RabbitMQ AMQP Port: {RABBITMQ_AMQP_PORT}")
    print(f"RabbitMQ Management Port: {RABBITMQ_PORT}")
    print(f"Username: {RABBITMQ_USER}")
    print("")

    # Test 1: Basic ping
    print("1. Testing basic connectivity (ping)...")
    if test_ping(RABBITMQ_SERVER):
        print("   ✅ Ping successful")
    else:
        print("   ❌ Ping failed - host may be unreachable or ping disabled")
    print("")

    # Test 2: RabbitMQ AMQP port
    print(f"2. Testing RabbitMQ AMQP port ({RABBITMQ_AMQP_PORT})...")
    if test_socket_connection(RABBITMQ_SERVER, RABBITMQ_AMQP_PORT, timeout=15):
        print("   ✅ AMQP port is accessible")
    else:
        print("   ❌ AMQP port is not accessible")
        print("   💡 Check if:")
        print("      - RabbitMQ is running on the target machine")
        print("      - Port 5672 is open in firewall")
        print("      - Docker containers are running (docker ps)")
    print("")

    # Test 3: RabbitMQ Management UI port
    print(f"3. Testing RabbitMQ Management port ({RABBITMQ_PORT})...")
    if test_socket_connection(RABBITMQ_SERVER, RABBITMQ_PORT, timeout=15):
        print("   ✅ Management port is accessible")
        
        # Test 4: Management UI authentication
        print("4. Testing RabbitMQ Management UI authentication...")
        if test_rabbitmq_management_ui(RABBITMQ_SERVER, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD):
            print("   ✅ Management UI authentication successful")
        else:
            print("   ❌ Management UI authentication failed")
            print("   💡 Check if:")
            print("      - Username/password are correct")
            print("      - Guest user is allowed for remote connections")
            print("      - RabbitMQ user permissions are set correctly")
    else:
        print("   ❌ Management port is not accessible")
        print("   💡 Check if:")
        print("      - Port 15672 is open in firewall")
        print("      - RabbitMQ management plugin is enabled")
    print("")

    # Test 5: Common network issues
    print("5. Common troubleshooting tips:")
    print("   🔧 If AMQP port fails:")
    print("      - On server: docker ps (check if minerva-rabbit-mq-1 is running)")
    print("      - On server: docker logs minerva-rabbit-mq-1")
    print("      - Check Windows Firewall or iptables rules")
    print("")
    print("   🔧 If guest user fails on remote connection:")
    print("      - RabbitMQ restricts 'guest' user to localhost by default")
    print("      - Create a new user: docker exec minerva-rabbit-mq-1 rabbitmqctl add_user myuser mypass")
    print("      - Set permissions: docker exec minerva-rabbit-mq-1 rabbitmqctl set_permissions myuser '.*' '.*' '.*'")
    print("      - Update config.py with new credentials")
    print("")
    print("   🔧 Network connectivity:")
    print(f"      - Try accessing management UI: http://{RABBITMQ_SERVER}:{RABBITMQ_PORT}")
    print("      - Check if both machines are on same network/subnet")
    print("      - Test from server machine: telnet localhost 5672")
    print("")

    # Test 6: Try actual RabbitMQ connection
    print("6. Testing actual RabbitMQ connection...")
    try:
        import pika
        
        # Use the same connection parameters as the main code
        if RABBITMQ_SERVER == "localhost" or RABBITMQ_SERVER.startswith("127."):
            connection_params = pika.ConnectionParameters(
                host=RABBITMQ_SERVER,
                heartbeat=600,
                blocked_connection_timeout=300,
                socket_timeout=10,
            )
        else:
            connection_params = pika.ConnectionParameters(
                host=RABBITMQ_SERVER,
                heartbeat=300,
                blocked_connection_timeout=180,
                socket_timeout=30,
                connection_attempts=3,
                retry_delay=2,
            )
        
        print("   Attempting RabbitMQ connection...")
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        print("   ✅ RabbitMQ connection successful!")
        connection.close()
        
    except ImportError:
        print("   ⚠️  pika not installed, skipping RabbitMQ connection test")
    except Exception as e:
        print(f"   ❌ RabbitMQ connection failed: {e}")
        print("   💡 This is likely the same error causing PCC to crash")

    print("")
    print("🏁 Test complete!")

if __name__ == "__main__":
    main()
