# Network Troubleshooting Guide

This guide helps resolve issues when connecting PCC to a remote Minerva server.

## Quick Fix Steps

### 1. **Use the Configuration Helper**
```bash
cd Autoresuscitation/MinervaPlugin
python configure_network.py
```

### 2. **Test Network Connectivity**
```bash
cd Autoresuscitation/MinervaPlugin
python test_network_connection.py
```

### 3. **Check Server Status**
On the Minerva server machine:
```bash
docker ps
docker logs minerva-rabbit-mq-1
```

## Common Issues and Solutions

### Issue 1: "Connection Refused" or "Timeout"

**Symptoms:**
- PCC crashes immediately when trying to connect
- Error messages about connection timeouts
- Socket connection failures

**Solutions:**

1. **Check if Minerva is running on target machine:**
   ```bash
   # On server machine
   docker ps
   # Should show minerva-rabbit-mq-1, minerva-api-1, minerva-web-1
   ```

2. **Check firewall settings:**
   ```bash
   # Windows (run as administrator)
   netsh advfirewall firewall add rule name="RabbitMQ AMQP" dir=in action=allow protocol=TCP localport=5672
   netsh advfirewall firewall add rule name="RabbitMQ Management" dir=in action=allow protocol=TCP localport=15672
   
   # Linux
   sudo ufw allow 5672
   sudo ufw allow 15672
   ```

3. **Test port accessibility:**
   ```bash
   # From PCC machine, test if ports are open
   telnet 192.168.1.75 5672
   telnet 192.168.1.75 15672
   ```

### Issue 2: "Authentication Failed" or "Access Denied"

**Symptoms:**
- Connection succeeds but authentication fails
- "ACCESS_REFUSED" errors
- Guest user login issues

**Root Cause:**
RabbitMQ restricts the `guest` user to localhost connections only by default.

**Solutions:**

1. **Create a new RabbitMQ user:**
   ```bash
   # On server machine
   docker exec minerva-rabbit-mq-1 rabbitmqctl add_user minerva_user secure_password
   docker exec minerva-rabbit-mq-1 rabbitmqctl set_permissions minerva_user ".*" ".*" ".*"
   docker exec minerva-rabbit-mq-1 rabbitmqctl set_user_tags minerva_user administrator
   ```

2. **Update PCC configuration:**
   ```python
   # In Autoresuscitation/MinervaPlugin/core/config.py
   RABBITMQ_USER = "minerva_user"
   RABBITMQ_PASSWORD = "secure_password"
   ```

3. **Alternative: Enable guest remote access (less secure):**
   ```bash
   # On server machine - create rabbitmq.conf
   docker exec minerva-rabbit-mq-1 sh -c 'echo "loopback_users = none" > /etc/rabbitmq/rabbitmq.conf'
   docker restart minerva-rabbit-mq-1
   ```

### Issue 3: "Connection Drops" or "Intermittent Failures"

**Symptoms:**
- Connection works initially but drops frequently
- Reconnection attempts fail
- Streaming data stops

**Solutions:**

1. **Check network stability:**
   ```bash
   # Continuous ping test
   ping -t 192.168.1.75  # Windows
   ping 192.168.1.75     # Linux/Mac
   ```

2. **Adjust timeout settings:**
   The updated `rabbitmq_client.py` now uses longer timeouts for network connections automatically.

3. **Check for network congestion:**
   - Use WiFi analyzer to check for interference
   - Try wired connection instead of WiFi
   - Check bandwidth usage on network

### Issue 4: "Docker Not Accessible from Network"

**Symptoms:**
- Docker containers run fine locally
- Ports not accessible from other machines
- Connection refused from network

**Solutions:**

1. **Check Docker port binding:**
   ```bash
   docker ps
   # Should show: 0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
   ```

2. **Restart Docker with correct port binding:**
   ```bash
   cd minerva
   docker compose -f docker-compose.prod.yml down
   docker compose -f docker-compose.prod.yml up -d
   ```

3. **Check Docker daemon settings:**
   - Ensure Docker is not bound to localhost only
   - Check Docker Desktop network settings

## Network Configuration Examples

### Example 1: Same Machine (Localhost)
```python
# config.py
RABBITMQ_SERVER = "localhost"
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"
```

### Example 2: Different Machine on Same Network
```python
# config.py
RABBITMQ_SERVER = "192.168.1.75"  # Server's IP
RABBITMQ_USER = "minerva_user"    # Custom user
RABBITMQ_PASSWORD = "secure_password"
```

### Example 3: Remote Server with Custom Port
```python
# config.py
RABBITMQ_SERVER = "10.0.0.100"
RABBITMQ_AMQP_PORT = 5672
RABBITMQ_USER = "remote_user"
RABBITMQ_PASSWORD = "remote_password"
```

## Diagnostic Commands

### On PCC Machine:
```bash
# Test basic connectivity
ping 192.168.1.75

# Test specific ports
telnet 192.168.1.75 5672
telnet 192.168.1.75 15672

# Run network test
python test_network_connection.py
```

### On Server Machine:
```bash
# Check Docker status
docker ps
docker logs minerva-rabbit-mq-1

# Check port listeners
netstat -an | grep 5672
netstat -an | grep 15672

# Test RabbitMQ locally
docker exec minerva-rabbit-mq-1 rabbitmqctl status
```

## Advanced Troubleshooting

### Enable RabbitMQ Debug Logging:
```bash
# On server machine
docker exec minerva-rabbit-mq-1 rabbitmqctl set_log_level debug
docker logs -f minerva-rabbit-mq-1
```

### Check Network Routes:
```bash
# On PCC machine
tracert 192.168.1.75  # Windows
traceroute 192.168.1.75  # Linux/Mac
```

### Monitor Network Traffic:
```bash
# On server machine
sudo tcpdump -i any port 5672
```

## Prevention Tips

1. **Use static IP addresses** for server machines
2. **Create dedicated RabbitMQ users** instead of using guest
3. **Document network configuration** for each lab setup
4. **Test connectivity** before starting experiments
5. **Use wired connections** when possible for stability

## Getting Help

If issues persist:

1. Run `python test_network_connection.py` and share the output
2. Check Docker logs: `docker logs minerva-rabbit-mq-1`
3. Verify network configuration with IT department
4. Consider using VPN if connecting across different networks
