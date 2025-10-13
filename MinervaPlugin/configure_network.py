#!/usr/bin/env python3
"""
Network configuration helper for Minerva Plugin
This script helps configure the connection to a remote Minerva server
"""

import os
import sys
import re
import socket

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def update_config_file(server_ip, user="guest", password="guest"):
    """Update the config.py file with new server settings"""
    config_path = os.path.join(os.path.dirname(__file__), 'core', 'config.py')
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Update RABBITMQ_SERVER
        content = re.sub(
            r'RABBITMQ_SERVER = \(\s*"[^"]*"\s*\)',
            f'RABBITMQ_SERVER = (\n    "{server_ip}"  # Connect to remote Docker instance\n)',
            content
        )
        
        # Update user and password if not guest
        if user != "guest":
            content = re.sub(
                r'RABBITMQ_USER = "[^"]*"',
                f'RABBITMQ_USER = "{user}"',
                content
            )
        
        if password != "guest":
            content = re.sub(
                r'RABBITMQ_PASSWORD = "[^"]*"',
                f'RABBITMQ_PASSWORD = "{password}"',
                content
            )
        
        # Write updated config
        with open(config_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated config.py:")
        print(f"   Server: {server_ip}")
        print(f"   User: {user}")
        print(f"   Password: {'*' * len(password)}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config file: {e}")
        return False

def test_connection(server_ip):
    """Test if the server is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server_ip, 5672))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("🔧 Minerva Plugin Network Configuration")
    print("=" * 50)
    print("")
    
    # Show current configuration
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
        from config import RABBITMQ_SERVER, RABBITMQ_USER, RABBITMQ_PASSWORD
        print(f"Current configuration:")
        print(f"  Server: {RABBITMQ_SERVER}")
        print(f"  User: {RABBITMQ_USER}")
        print(f"  Password: {'*' * len(RABBITMQ_PASSWORD)}")
        print("")
    except ImportError:
        print("❌ Could not read current configuration")
        print("")
    
    # Show local IP for reference
    local_ip = get_local_ip()
    print(f"This machine's IP address: {local_ip}")
    print("")
    
    # Configuration options
    print("Configuration options:")
    print("1. Use localhost (for local Docker)")
    print("2. Use this machine's IP (for network access)")
    print("3. Enter custom IP address")
    print("4. Test current configuration")
    print("5. Exit")
    print("")
    
    while True:
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            # Localhost configuration
            if update_config_file("localhost"):
                print("✅ Configured for localhost")
                if test_connection("localhost"):
                    print("✅ Connection test successful")
                else:
                    print("⚠️  Connection test failed - make sure Docker is running")
            break
            
        elif choice == "2":
            # This machine's IP
            if update_config_file(local_ip):
                print(f"✅ Configured for this machine's IP ({local_ip})")
                if test_connection(local_ip):
                    print("✅ Connection test successful")
                else:
                    print("⚠️  Connection test failed")
                    print("💡 Make sure Docker ports are accessible from network")
            break
            
        elif choice == "3":
            # Custom IP
            server_ip = input("Enter server IP address: ").strip()
            if not server_ip:
                print("❌ Invalid IP address")
                continue
                
            # Ask for custom credentials
            print("")
            print("RabbitMQ credentials (press Enter for default 'guest'):")
            user = input("Username [guest]: ").strip() or "guest"
            password = input("Password [guest]: ").strip() or "guest"
            
            if update_config_file(server_ip, user, password):
                print(f"✅ Configured for custom server ({server_ip})")
                if test_connection(server_ip):
                    print("✅ Connection test successful")
                else:
                    print("⚠️  Connection test failed")
                    print("💡 Run test_network_connection.py for detailed diagnostics")
            break
            
        elif choice == "4":
            # Test current configuration
            try:
                from config import RABBITMQ_SERVER
                print(f"Testing connection to {RABBITMQ_SERVER}...")
                if test_connection(RABBITMQ_SERVER):
                    print("✅ Connection test successful")
                else:
                    print("❌ Connection test failed")
                    print("💡 Run test_network_connection.py for detailed diagnostics")
            except ImportError:
                print("❌ Could not read current configuration")
            
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice, please select 1-5")
    
    print("")
    print("📝 Next steps:")
    print("1. Run test_network_connection.py to verify connectivity")
    print("2. Restart PCC_client.py to use new configuration")
    print("3. Check that Minerva Docker containers are running on target machine")

if __name__ == "__main__":
    main()
