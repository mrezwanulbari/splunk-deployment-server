#!/bin/bash
# =============================================================================
# Splunk Deployment Server Health Check Script
# =============================================================================
# Description: Monitors DS health, client connectivity, and app deployment
# Usage:       bash health_check.sh [--verbose]
# Schedule:    Run via cron every 15 minutes
# =============================================================================

set -euo pipefail

SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"
LOG_FILE="/var/log/splunk/ds_health_check.log"
ALERT_THRESHOLD=100  # Alert if more than this many clients are missing

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- Check Splunk Service Status ---
check_splunk_status() {
    log "=== Checking Splunk Service Status ==="
    if $SPLUNK_HOME/bin/splunk status | grep -q "splunkd is running"; then
        log "[OK] Splunk daemon is running"
    else
        log "[CRITICAL] Splunk daemon is NOT running!"
        return 1
    fi
}

# --- Check Deployment Server Clients ---
check_client_count() {
    log "=== Checking Connected Clients ==="
    local client_count
    client_count=$($SPLUNK_HOME/bin/splunk list deploy-clients -auth admin:changeme 2>/dev/null | grep -c "ip=" || echo 0)
    log "[INFO] Connected clients: $client_count"

    # Compare with expected count
    local expected_count=${EXPECTED_CLIENTS:-500}
    local missing=$((expected_count - client_count))
    if [ "$missing" -gt "$ALERT_THRESHOLD" ]; then
        log "[WARNING] $missing clients are not checking in (expected: $expected_count, actual: $client_count)"
    fi
}

# --- Check Disk Space ---
check_disk_space() {
    log "=== Checking Disk Space ==="
    local usage
    usage=$(df -h "$SPLUNK_HOME" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt 85 ]; then
        log "[WARNING] Disk usage at ${usage}% — consider cleanup"
    else
        log "[OK] Disk usage: ${usage}%"
    fi
}

# --- Check Deployment Apps Directory ---
check_deployment_apps() {
    log "=== Checking Deployment Apps ==="
    local app_count
    app_count=$(ls -d "$SPLUNK_HOME/etc/deployment-apps"/*/ 2>/dev/null | wc -l)
    log "[INFO] Deployment apps available: $app_count"

    # List apps
    for app_dir in "$SPLUNK_HOME/etc/deployment-apps"/*/; do
        local app_name
        app_name=$(basename "$app_dir")
        log "  - $app_name"
    done
}

# --- Check for Configuration Errors ---
check_config() {
    log "=== Validating Configuration ==="
    if $SPLUNK_HOME/bin/splunk btool check --debug 2>&1 | grep -i "error"; then
        log "[WARNING] Configuration errors detected — run 'splunk btool check' for details"
    else
        log "[OK] No configuration errors found"
    fi
}

# --- Main Execution ---
main() {
    log "=========================================="
    log "  Deployment Server Health Check"
    log "=========================================="

    check_splunk_status
    check_disk_space
    check_deployment_apps
    check_client_count
    check_config

    log "=========================================="
    log "  Health check complete"
    log "=========================================="
}

main "$@"
