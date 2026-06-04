#!/bin/bash

if [[ "$1" == "--run-main" ]]; then

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================
    today=$(date +"%y%m%d")

    # ---- V3 (Phase 1) configuration ----
    RIGNAME="ChangeMyName"  # Change this value to set the rig name
    source_dir="/media/pi/${RIGNAME}/"
    destination_dir="/home/pi/data2/Projects"

    output_file="/home/pi/Desktop/Rsync_Results/${today}_${RIGNAME}.txt"
    logfile="/home/pi/Desktop/Rsync_Cron_Debug/${today}_${RIGNAME}.log"
    error_file="/home/pi/Desktop/Rsync_Error/${today}_${RIGNAME}.txt"
    network_test_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_test.log"
    network_monitor_log="/home/pi/Desktop/Rsync_Cron_Debug/${today}_network_monitor.log"

    max_attempts=3
    target_host="10.20.16.88"

    # ---- Bandwidth configuration ----
    # Set to 0 to disable bandwidth limiting, or set a value in KB/s
    # Examples: 10000 = 10MB/s, 50000 = 50MB/s, 0 = unlimited
    BANDWIDTH_LIMIT=0  # Change this value as needed

    # ---- PM468 (Phase 2) configuration ----
    PM468_LOGFILE="/home/pi/PM468_rsync_log.log"
    RIG_CONFIG="/home/pi/rig.config"

    # ==== FIX ENVIRONMENT FOR CRON ====
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"
    export HOME="/home/pi"

    # Ensure log directories exist before any writes
    mkdir -p "$(dirname "$logfile")" "$(dirname "$output_file")" \
             "$(dirname "$error_file")" "$(dirname "$PM468_LOGFILE")"

    # ==== START LOGGING ====
    exec > "$logfile" 2>&1
    set -x
    echo "===== COMBINED RSYNC JOB STARTED at $(date) ====="

    # ==========================================================================
    # PHASE 1 FUNCTIONS
    # ==========================================================================

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

    # ==== INTERNET SPEED CHECK ====
    # Measures download (and upload, when available) throughput and records the
    # result in the network test log. Tries, in order:
    #   1. speedtest-cli  (python Ookla client)
    #   2. speedtest      (official Ookla CLI)
    #   3. curl download fallback (no extra package required)
    run_speed_test() {
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "===== INTERNET SPEED CHECK =====" | tee -a "$network_test_log"
        echo "[$timestamp] Starting internet speed check..." | tee -a "$network_test_log"

        if command -v speedtest-cli >/dev/null 2>&1; then
            echo "[$timestamp] Using speedtest-cli" | tee -a "$network_test_log"
            speedtest-cli --simple 2>&1 | tee -a "$network_test_log"

        elif command -v speedtest >/dev/null 2>&1; then
            echo "[$timestamp] Using Ookla speedtest CLI" | tee -a "$network_test_log"
            speedtest --accept-license --accept-gdpr 2>&1 | tee -a "$network_test_log"

        else
            # Fallback: measure download throughput with curl (no extra package).
            local test_url="http://speedtest.tele2.net/10MB.zip"
            echo "[$timestamp] No speedtest tool found; using curl download fallback" \
                | tee -a "$network_test_log"
            echo "[$timestamp] Test file: $test_url" | tee -a "$network_test_log"

            local speed_bps
            speed_bps=$(curl -o /dev/null -s -w '%{speed_download}' --max-time 120 "$test_url")

            if [ -n "$speed_bps" ] && (( $(echo "$speed_bps > 0" | bc -l 2>/dev/null || echo "0") )); then
                local speed_mbps
                speed_mbps=$(echo "scale=2; $speed_bps * 8 / 1000000" | bc -l 2>/dev/null)
                echo "[$timestamp] Download: ${speed_mbps} Mbps (${speed_bps} bytes/s)" \
                    | tee -a "$network_test_log"
            else
                echo "[$timestamp] WARNING: Speed test fallback failed (no internet or URL unreachable)" \
                    | tee -a "$network_test_log"
            fi
        fi

        echo "[$timestamp] Internet speed check complete" | tee -a "$network_test_log"
        echo "================================" | tee -a "$network_test_log"
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

        # Test 4: Internet speed check (recorded in the network test log)
        run_speed_test

        # Test 5: Bandwidth limiting decision
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

    # ==========================================================================
    # PHASE 1 MAIN
    # ==========================================================================
    run_v3_phase() {
        echo "===== PHASE 1 (V3): STARTING RSYNC OPERATION ====="

        # Step 1: Network stability test (now includes the internet speed check)
        if ! perform_network_test; then
            echo "❌ Network stability test failed. Aborting combined job."
            return 1
        fi

        # Step 2: Mount verification
        if ! verify_mount; then
            echo "❌ Mount verification failed. Aborting combined job."
            return 1
        fi

        # Step 3: Perform rsync with retries
        local attempt=1
        while [ $attempt -le $max_attempts ]; do
            echo "Starting rsync attempt $attempt of $max_attempts..."

            if run_rsync_with_retry $attempt; then
                echo "✅ V3 rsync operation completed successfully!"
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
            echo "❌ V3 rsync failed after $max_attempts attempts at $(date)." | tee -a "$error_file"
            echo "Network monitor log available at: $network_monitor_log" | tee -a "$error_file"
            return 1
        fi

        echo "===== PHASE 1 (V3) COMPLETED SUCCESSFULLY at $(date) ====="
        echo "Network monitoring data available at: $network_monitor_log"
        return 0
    }

    # ==========================================================================
    # PHASE 2 MAIN
    # ==========================================================================
    run_pm468_phase() {
        echo "===== PHASE 2 (PM468): STARTING WEEKLY RIGCHECKS SYNC ====="

        echo "$today" >> "$PM468_LOGFILE"
        echo "===== PM468 RSYNC PHASE STARTED at $(date) =====" >> "$PM468_LOGFILE"

        # ==== VALIDATE JQ AND RIG CONFIG ====
        # Read jq values into separate variables so each can be validated before
        # being composed into source_dir. A missing key returns "null" from
        # jq -r, which would silently produce a bad path.
        local PM468_RIGNAME
        local AUTOSAVE_DIR
        PM468_RIGNAME=$(jq -r ".RIGNAME" "$RIG_CONFIG")
        AUTOSAVE_DIR=$(jq -r ".AUTOSAVE_DIR" "$RIG_CONFIG")

        if [[ "$PM468_RIGNAME" == "null" || -z "$PM468_RIGNAME" ]]; then
            echo "ERROR: RIGNAME missing or null in $RIG_CONFIG" | tee -a "$PM468_LOGFILE"
            return 1
        fi

        if [[ "$AUTOSAVE_DIR" == "null" || -z "$AUTOSAVE_DIR" ]]; then
            echo "ERROR: AUTOSAVE_DIR missing or null in $RIG_CONFIG" | tee -a "$PM468_LOGFILE"
            return 1
        fi

        local pm468_source_dir="${AUTOSAVE_DIR}/${PM468_RIGNAME}/"
        local PM468_destination_dir="/home/pi/data2/Projects/PM468_PJ_Weekly_Quantitative_and_Qualitative_Rig_Checks/PM468_PJ_Weekly_Quantitative_and_Qualitative_Rig_Checks_DATA/rigfiles"

        echo "input:  $pm468_source_dir" | tee -a "$PM468_LOGFILE"
        echo "output: $PM468_destination_dir" | tee -a "$PM468_LOGFILE"

        # ==== SUDO GUARD ====
        # Fail early with a clear message if passwordless sudo for rsync is not
        # configured, rather than failing silently mid-transfer.
        if ! sudo -n rsync --version &>/dev/null; then
            echo "ERROR: passwordless sudo access for rsync is required." | tee -a "$PM468_LOGFILE"
            echo "       Add this line via visudo:" | tee -a "$PM468_LOGFILE"
            echo "       pi ALL=(ALL) NOPASSWD: /usr/bin/rsync" | tee -a "$PM468_LOGFILE"
            return 1
        fi

        # ==== PCC PROCESS GUARD ====
        # Do not run the rsync backup while PCC is actively recording.
        # pgrep -x matches the exact process name to avoid false positives
        # (e.g. a process called "PCC_monitor" would not trigger this).
        if pgrep -x "PCC" > /dev/null 2>&1; then
            echo "INFO: PCC is currently running. PM468 rsync skipped to avoid I/O contention." \
                | tee -a "$PM468_LOGFILE"
            return 0
        fi
        echo "✅ PCC not running, proceeding with PM468 rsync." >> "$PM468_LOGFILE"

        # ==== MAIN SYNC ====
        local fail=0
        local found=0

        while IFS= read -r -d "" dir; do
            found=$(( found + 1 ))
            echo "Syncing $dir" | tee -a "$PM468_LOGFILE"
            sudo rsync -avvhcP --partial --mkpath "$dir/" "$PM468_destination_dir/" \
                >> "$PM468_LOGFILE" 2>&1 || fail=1
        done < <(find "$pm468_source_dir" -type d -name rigfiles -print0)

        if [[ $found -eq 0 ]]; then
            echo "WARNING: No rigfiles directories found under $pm468_source_dir" | tee -a "$PM468_LOGFILE"
            return 1
        fi

        echo "Synced $found rigfiles director$([ $found -eq 1 ] && echo y || echo ies)" \
            | tee -a "$PM468_LOGFILE"

        return $fail
    }

    # ==========================================================================
    # COMBINED EXECUTION: V3 FIRST, THEN PM468
    # ==========================================================================
    overall_exit=0

    if ! run_v3_phase; then
        echo "❌ Phase 1 (V3) reported a failure."
        overall_exit=1
        # A network/mount failure means the shared mount is unavailable, so the
        # PM468 phase cannot succeed either. Abort the combined job.
        echo "===== COMBINED RSYNC JOB ABORTED after V3 failure at $(date) ====="
        exit $overall_exit
    fi

    if ! run_pm468_phase; then
        echo "❌ Phase 2 (PM468) reported a failure."
        overall_exit=1
    else
        echo "✅ Phase 2 (PM468) completed."
    fi

    echo "===== COMBINED RSYNC JOB FINISHED at $(date) (exit $overall_exit) ====="
    exit $overall_exit
fi

# ==============================================================================
# OUTER WRAPPER
# ==============================================================================
# Only reached on the initial invocation (no --run-main flag).
# Recompute the logfile path so the exit-code result can be appended to the
# correct log file after the child process finishes.
PM468_LOGFILE="/home/pi/PM468_rsync_log.log"
mkdir -p "$(dirname "$PM468_LOGFILE")"

# ==== TIMEOUT CALCULATION ====
# Pick the sooner of today's or tomorrow's 06:30 so the timeout is correct
# regardless of when the script starts:
#   - Before 06:30 (e.g. 1am):  uses today's 06:30    (~5.5 hrs)
#   - Just before 06:30 (6am):  uses today's 06:30    (~30 min)
#   - After  06:30 (e.g. 9am):  uses tomorrow's 06:30 (~21.5 hrs)
NOW=$(date +%s)
TODAY_CUTOFF=$(date -d "today 06:30" +%s)

if [[ $TODAY_CUTOFF -gt $NOW ]]; then
    END_TIME=$TODAY_CUTOFF
else
    END_TIME=$(date -d "tomorrow 06:30" +%s)
fi

TIMEOUT=$(( END_TIME - NOW ))

CUTOFF_LABEL=$(date -d "@$END_TIME" '+%Y-%m-%d %H:%M')
echo "Timeout set to ${TIMEOUT}s (until $CUTOFF_LABEL)" >> "$PM468_LOGFILE"

timeout --kill-after=60s "${TIMEOUT}s" "$0" --run-main
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 124 ]]; then
    echo "[$(date)] Job stopped at 06:30 due to timeout" >> "$PM468_LOGFILE"
elif [[ $EXIT_CODE -ne 0 ]]; then
    echo "[$(date)] Job failed with exit code $EXIT_CODE" >> "$PM468_LOGFILE"
else
    echo "[$(date)] Job completed successfully" >> "$PM468_LOGFILE"
fi

echo "========== Finished Rsync Attempt ==========" >> "$PM468_LOGFILE"
