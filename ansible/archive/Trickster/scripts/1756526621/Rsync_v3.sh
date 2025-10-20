#!/bin/bash

# ==== IMPROVED RSYNC SCRIPT WITH NETWORK STABILITY CHECKS ====
today=$(date +"%y%m%d")
RIGNAME="Trickster"  # Change this value to set the rig name
source_dir="/media/pi/${RIGNAME}/"                
destination_dir="/home/pi/data2/Projects" 

output_file="/home/pi/Desktop/Rsync_Results/${today}_${RIGNAME}.txt"
logfile="/home/pi/Desktop/Rsync_Cron_Debug/${today}_${RIGNAME}.log"
error_file="/home/pi/Desktop/Rsync_Error/${today}_${RIGNAME}.txt"
network_test_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_test.log"
network_monitor_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_monitor.log"

max_attempts=3
target_host="10.20.16.88"

# ==== BANDWIDTH CONFIGURATION ====
# Set to 0 to disable bandwidth limiting, or set a value in KB/s
# Examples: 10000 = 10MB/s, 50000 = 50MB/s, 0 = unlimited
BANDWIDTH_LIMIT=0  # Change this value as needed

# ==== FIX ENVIRONMENT FOR CRON ====
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"
export HOME="/home/pi"

# ==== START LOGGING ====
exec > "$logfile" 2>&1
set -x
echo "===== RSYNC JOB STARTED at $(date) ====="

# ==== NETWORK STABILITY FUNCTIONS ====

# Function to test basic connectivity
test_connectivity() {
    echo "Testing network connectivity to $target_host..."
    ping -c 5 "$target_host" > /dev/null 2>&1
    return $?
}

# Function to get current network metrics
get_network_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get ping statistics
    local ping_result=$(ping -c 3 "$target_host" 2>/dev/null | tail -2)
    local latency=$(echo "$ping_result" | grep "rtt min/avg/max" | awk -F'/' '{print $5}')
    local packet_loss=$(echo "$ping_result" | grep "packets transmitted" | awk '{print $6}' | sed 's/%//')
    
    echo "[$timestamp] Latency: ${latency}ms, Packet Loss: ${packet_loss}%" >> "$network_monitor_log"
    
    # Return 1 if network is clearly problematic
    if [ ! -z "$packet_loss" ] && (( $(echo "$packet_loss > 10" | bc -l 2>/dev/null || echo "0") )); then
        echo "[$timestamp] WARNING: High packet loss detected: ${packet_loss}%" >> "$network_monitor_log"
        return 1
    fi
    
    return 0
}

# Function to determine if bandwidth limiting is needed
should_limit_bandwidth() {
    # If explicitly set to 0, don't limit
    if [ "$BANDWIDTH_LIMIT" -eq 0 ]; then
        echo "Bandwidth limiting disabled (BANDWIDTH_LIMIT=0)"
        return 1
    fi
    
    # If explicitly set to a value, use it
    if [ "$BANDWIDTH_LIMIT" -gt 0 ]; then
        echo "Using configured bandwidth limit: ${BANDWIDTH_LIMIT}KB/s"
        return 0
    fi
    
    # Auto-detect: if high latency or packet loss, suggest limiting
    local avg_latency=$(ping -c 5 "$target_host" 2>/dev/null | grep "rtt min/avg/max" | awk -F'/' '{print $5}')
    local packet_loss=$(ping -c 10 "$target_host" 2>/dev/null | grep "packets transmitted" | awk '{print $6}' | sed 's/%//')
    
    if [ ! -z "$avg_latency" ] && (( $(echo "$avg_latency > 100" | bc -l 2>/dev/null || echo "0") )); then
        echo "High latency detected (${avg_latency}ms), suggesting bandwidth limiting"
        return 0
    fi
    
    if [ ! -z "$packet_loss" ] && (( $(echo "$packet_loss > 5" | bc -l 2>/dev/null || echo "0") )); then
        echo "Packet loss detected (${packet_loss}%), suggesting bandwidth limiting"
        return 0
    fi
    
    echo "Network conditions appear stable, bandwidth limiting not needed"
    return 1
}

# Function to perform comprehensive network test
perform_network_test() {
    echo "===== PERFORMING NETWORK STABILITY TEST =====" | tee -a "$network_test_log"
    
    # Test 1: Basic connectivity
    if ! test_connectivity; then
        echo "❌ Network connectivity failed!" | tee -a "$network_test_log"
        echo "Server $target_host unreachable at $(date)" >> "$error_file"
        return 1
    fi
    echo "✅ Basic connectivity: PASSED" | tee -a "$network_test_log"
    
    # Test 2: Get initial network metrics
    echo "Initial network metrics:" | tee -a "$network_test_log"
    get_network_metrics | tee -a "$network_test_log"
    
    # Test 3: Extended ping test for baseline
    echo "Extended ping test (20 packets):" | tee -a "$network_test_log"
    ping -c 20 -i 0.5 "$target_host" | grep -E "(packets transmitted|rtt min/avg/max)" | tee -a "$network_test_log"
    
    # Test 4: Bandwidth limiting decision
    echo "Bandwidth limiting assessment:" | tee -a "$network_test_log"
    if should_limit_bandwidth; then
        echo "⚠️  Bandwidth limiting recommended" | tee -a "$network_test_log"
    else
        echo "✅ No bandwidth limiting needed" | tee -a "$network_test_log"
    fi
    
    return 0
}

# Function to start background network monitoring
start_network_monitor() {
    echo "Starting background network monitoring..." | tee -a "$network_monitor_log"
    
    # Start background process to monitor network every 30 seconds
    (
        while true; do
            get_network_metrics
            sleep 30
        done
    ) &
    
    NETWORK_MONITOR_PID=$!
    echo "Network monitor PID: $NETWORK_MONITOR_PID" | tee -a "$network_monitor_log"
}

# Function to stop background network monitoring
stop_network_monitor() {
    if [ ! -z "$NETWORK_MONITOR_PID" ]; then
        echo "Stopping network monitor (PID: $NETWORK_MONITOR_PID)" | tee -a "$network_monitor_log"
        kill $NETWORK_MONITOR_PID 2>/dev/null
        wait $NETWORK_MONITOR_PID 2>/dev/null
    fi
}

# ==== MOUNT VERIFICATION ====
verify_mount() {
    echo "===== VERIFYING MOUNT POINTS ====="
    
    # Check if source directory exists and is accessible
    if [ ! -d "$source_dir" ]; then
        echo "❌ Source directory $source_dir does not exist!" | tee -a "$error_file"
        return 1
    fi
    
    # Check mount status
    sudo mount -a
    sudo systemctl daemon-reload
    
    if ! mount | grep -q '/home/pi/data2' ; then
        echo "❌ Mount /home/pi/data2 not found at $(date)" | tee -a "$error_file"
        return 1
    fi
    
    echo "✅ Mount verification: PASSED"
    return 0
}

# ==== IMPROVED RSYNC FUNCTION ====
run_rsync_with_retry() {
    local attempt=$1
    
    echo "===== RSYNC ATTEMPT $attempt ====="
    
    # Use fixed, conservative timeout values
    local timeout_value=600  # 10 minutes - conservative for large files
    
    echo "Using fixed timeout: ${timeout_value}s"
    echo "Starting rsync at $(date)" | tee -a "$network_monitor_log"
    
    # Start network monitoring before rsync
    start_network_monitor
    
    # Build rsync command with conditional bandwidth limiting
    local rsync_cmd="sudo rsync -avz --partial --inplace --timeout=$timeout_value --progress --stats --human-readable --itemize-changes --log-file=\"$output_file\""
    
    # Add bandwidth limiting if configured or recommended
    if [ "$BANDWIDTH_LIMIT" -gt 0 ]; then
        rsync_cmd="$rsync_cmd --bwlimit=$BANDWIDTH_LIMIT"
        echo "Using bandwidth limit: ${BANDWIDTH_LIMIT}KB/s"
    elif should_limit_bandwidth; then
        # Auto-suggest a reasonable limit
        local suggested_limit=10000  # 10MB/s
        rsync_cmd="$rsync_cmd --bwlimit=$suggested_limit"
        echo "Auto-applying bandwidth limit: ${suggested_limit}KB/s due to network conditions"
    else
        echo "No bandwidth limiting applied"
    fi
    
    # Add source and destination
    rsync_cmd="$rsync_cmd \"$source_dir\" \"$destination_dir\""
    
    echo "Executing: $rsync_cmd"
    eval $rsync_cmd 2>&1
    
    local rsync_exit=$?
    
    # Stop network monitoring
    stop_network_monitor
    
    echo "Rsync completed at $(date) with exit code: $rsync_exit" | tee -a "$network_monitor_log"
    
    if [ $rsync_exit -eq 0 ]; then
        echo "✅ Rsync completed successfully on attempt $attempt"
        return 0
    else
        echo "❌ Rsync failed with exit code $rsync_exit on attempt $attempt"
        
        # Log specific error information with network context
        case $rsync_exit in
            30) 
                echo "Timeout error - network may be unstable" | tee -a "$error_file"
                echo "Check network monitor log: $network_monitor_log" | tee -a "$error_file"
                ;;
            23) 
                echo "Partial transfer error - some files may be incomplete" | tee -a "$error_file"
                ;;
            24) 
                echo "Vanished source files error" | tee -a "$error_file"
                ;;
            *) 
                echo "Unknown rsync error code: $rsync_exit" | tee -a "$error_file"
                ;;
        esac
        
        return $rsync_exit
    fi
}

# ==== MAIN EXECUTION ====
main() {
    echo "===== STARTING RSYNC OPERATION ====="
    
    # Step 1: Network stability test
    if ! perform_network_test; then
        echo "❌ Network stability test failed. Aborting rsync operation."
        exit 1
    fi
    
    # Step 2: Mount verification
    if ! verify_mount; then
        echo "❌ Mount verification failed. Aborting rsync operation."
        exit 1
    fi
    
    # Step 3: Perform rsync with retries
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        echo "Starting rsync attempt $attempt of $max_attempts..."
        
        if run_rsync_with_retry $attempt; then
            echo "✅ Rsync operation completed successfully!"
            break
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            echo "Waiting 120 seconds before retry..."
            sleep 120
            
            # Re-test network before retry
            echo "Re-testing network before retry..."
            if ! perform_network_test; then
                echo "❌ Network test failed before retry. Waiting longer..."
                sleep 300  # Wait 5 more minutes
            fi
        fi
        
        ((attempt++))
    done
    
    # Final check
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ Rsync failed after $max_attempts attempts at $(date)." | tee -a "$error_file"
        echo "Network monitor log available at: $network_monitor_log" | tee -a "$error_file"
        exit 1
    fi
    
    echo "===== RSYNC JOB COMPLETED SUCCESSFULLY at $(date) ====="
    echo "Network monitoring data available at: $network_monitor_log"
}

# Run the main function
main "$@" 