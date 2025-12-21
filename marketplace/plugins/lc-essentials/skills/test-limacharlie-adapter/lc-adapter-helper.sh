#!/bin/bash
# LimaCharlie Adapter Test Helper
# Usage: ./lc-adapter-helper.sh <command> [options]
#
# Commands:
#   sample [count]        - Capture sample logs (default 20 lines)
#   setup <oid> <iid> [mapping options] - Download adapter and create launch script
#   start                 - Start the adapter (run in background)
#   stop                  - Stop the adapter and cleanup
#   status                - Check if adapter is running
#   logs                  - Show adapter logs
#   info                  - Show current configuration

set -e

# Configuration file location
CONFIG_DIR="${HOME}/.lc-adapter-test"
CONFIG_FILE="${CONFIG_DIR}/config"
ADAPTER_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

detect_platform() {
    OS_TYPE=$(uname -s)
    ARCH=$(uname -m)

    case "$OS_TYPE" in
        Linux)
            DOWNLOAD_URL="https://downloads.limacharlie.io/adapter/linux/64"
            if command -v journalctl &> /dev/null; then
                LOG_SOURCE="journalctl"
                LOG_CMD="journalctl -f --no-pager"
            else
                LOG_SOURCE="file"
                # Try common log files
                for f in /var/log/syslog /var/log/messages /var/log/auth.log; do
                    if [ -r "$f" ]; then
                        LOG_FILE="$f"
                        LOG_CMD="tail -f $f"
                        break
                    fi
                done
                if [ -z "$LOG_FILE" ]; then
                    log_error "No readable log files found in /var/log"
                    exit 1
                fi
            fi
            ;;
        Darwin)
            if [ "$ARCH" = "arm64" ]; then
                DOWNLOAD_URL="https://downloads.limacharlie.io/adapter/mac/arm64"
            else
                DOWNLOAD_URL="https://downloads.limacharlie.io/adapter/mac/64"
            fi
            LOG_SOURCE="unified"
            LOG_CMD="log stream --style syslog"
            ;;
        *)
            log_error "Unsupported OS: $OS_TYPE"
            exit 1
            ;;
    esac

    HOSTNAME_VAL=$(hostname)
}

save_config() {
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" << EOF
ADAPTER_DIR="$ADAPTER_DIR"
OID="$OID"
IID="$IID"
HOSTNAME_VAL="$HOSTNAME_VAL"
LOG_SOURCE="$LOG_SOURCE"
LOG_CMD="$LOG_CMD"
EOF
    log_info "Configuration saved to $CONFIG_FILE"
}

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        return 0
    else
        log_error "No configuration found. Run 'setup' first."
        return 1
    fi
}

cmd_setup() {
    if [ $# -lt 2 ]; then
        echo "Usage: $0 setup <oid> <iid> [mapping options]"
        echo "  oid - LimaCharlie Organization ID"
        echo "  iid - Installation Key ID (UUID format)"
        echo ""
        echo "Mapping options:"
        echo "  --grok <pattern>        - Grok parsing pattern"
        echo "  --event-type <path>     - Field path for event type"
        echo "  --event-time <path>     - Field path for event timestamp"
        echo "  --event-time-tz <tz>    - Timezone for timestamps (e.g., America/Los_Angeles)"
        echo "  --hostname-path <path>  - Field path for hostname"
        exit 1
    fi

    OID="$1"
    IID="$2"
    shift 2

    # Parse optional mapping arguments
    GROK_PATTERN=""
    EVENT_TYPE_PATH=""
    EVENT_TIME_PATH=""
    EVENT_TIME_TZ=""
    HOSTNAME_PATH=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --grok)
                GROK_PATTERN="$2"
                shift 2
                ;;
            --event-type)
                EVENT_TYPE_PATH="$2"
                shift 2
                ;;
            --event-time)
                EVENT_TIME_PATH="$2"
                shift 2
                ;;
            --event-time-tz)
                EVENT_TIME_TZ="$2"
                shift 2
                ;;
            --hostname-path)
                HOSTNAME_PATH="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log_info "Detecting platform..."
    detect_platform

    log_info "Platform: $OS_TYPE ($ARCH)"
    log_info "Log source: $LOG_SOURCE"
    log_info "Hostname: $HOSTNAME_VAL"

    # Create temp directory
    ADAPTER_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lc-adapter-test-XXXXXX")
    log_info "Created temp directory: $ADAPTER_DIR"

    # Download adapter
    log_info "Downloading adapter from $DOWNLOAD_URL..."
    curl -sSL "$DOWNLOAD_URL" -o "$ADAPTER_DIR/lc_adapter"
    chmod +x "$ADAPTER_DIR/lc_adapter"
    log_info "Adapter downloaded and made executable"

    # Build mapping arguments if provided
    MAPPING_ARGS=""
    if [ -n "$GROK_PATTERN" ]; then
        MAPPING_ARGS="\"client_options.mapping.parsing_grok.message=$GROK_PATTERN\""
        if [ -n "$EVENT_TYPE_PATH" ]; then
            MAPPING_ARGS="$MAPPING_ARGS client_options.mapping.event_type_path=$EVENT_TYPE_PATH"
        fi
        if [ -n "$EVENT_TIME_PATH" ]; then
            MAPPING_ARGS="$MAPPING_ARGS client_options.mapping.event_time_path=$EVENT_TIME_PATH"
        fi
        if [ -n "$EVENT_TIME_TZ" ]; then
            MAPPING_ARGS="$MAPPING_ARGS client_options.mapping.event_time_timezone=$EVENT_TIME_TZ"
        fi
        if [ -n "$HOSTNAME_PATH" ]; then
            MAPPING_ARGS="$MAPPING_ARGS client_options.mapping.sensor_hostname_path=$HOSTNAME_PATH"
        fi
        log_info "Mapping configuration: grok pattern provided"
    fi

    # Create launch script
    cat > "$ADAPTER_DIR/run_adapter.sh" << SCRIPT
#!/bin/bash
$LOG_CMD | $ADAPTER_DIR/lc_adapter stdin \\
  client_options.identity.installation_key=$IID \\
  client_options.identity.oid=$OID \\
  client_options.platform=text \\
  client_options.sensor_seed_key=test-adapter \\
  client_options.hostname=$HOSTNAME_VAL \\
  $MAPPING_ARGS \\
  > $ADAPTER_DIR/adapter.log 2>&1
SCRIPT
    chmod +x "$ADAPTER_DIR/run_adapter.sh"
    log_info "Launch script created at $ADAPTER_DIR/run_adapter.sh"

    # Save configuration
    save_config

    echo ""
    echo "============================================"
    echo "Setup complete!"
    echo "============================================"
    echo "ADAPTER_DIR=$ADAPTER_DIR"
    echo "OID=$OID"
    echo "IID=$IID"
    echo ""
    echo "Next steps:"
    echo "  Start adapter:  $0 start"
    echo "  Check status:   $0 status"
    echo "  View logs:      $0 logs"
    echo "  Stop adapter:   $0 stop"
    echo "============================================"
}

cmd_start() {
    load_config || exit 1

    if pgrep -f "lc_adapter" > /dev/null; then
        log_warn "Adapter is already running"
        cmd_status
        return 0
    fi

    log_info "Starting adapter..."
    # Properly daemonize: redirect all I/O and disown to fully detach
    nohup "$ADAPTER_DIR/run_adapter.sh" </dev/null >/dev/null 2>&1 &
    disown
    sleep 2

    if pgrep -f "lc_adapter" > /dev/null; then
        log_info "Adapter started successfully"
        cmd_status
    else
        log_error "Failed to start adapter. Check logs:"
        echo "  $0 logs"
    fi
}

cmd_stop() {
    log_info "Stopping adapter..."

    # Kill adapter and log source processes
    pkill -9 -f "lc_adapter" 2>/dev/null || true
    pkill -9 -f "journalctl -f" 2>/dev/null || true
    pkill -9 -f "tail -f.*log" 2>/dev/null || true
    pkill -9 -f "log stream" 2>/dev/null || true

    # Load config to get ADAPTER_DIR
    if load_config 2>/dev/null; then
        if [ -n "$ADAPTER_DIR" ] && [ -d "$ADAPTER_DIR" ]; then
            log_info "Cleaning up $ADAPTER_DIR..."
            rm -rf "$ADAPTER_DIR"
        fi
        rm -f "$CONFIG_FILE"
        rmdir "$CONFIG_DIR" 2>/dev/null || true
    fi

    # Clean up the helper script itself if running from /tmp
    if [[ "$0" == /tmp/lc-adapter-helper.sh ]]; then
        log_info "Removing helper script from /tmp..."
        rm -f /tmp/lc-adapter-helper.sh
    fi

    log_info "Adapter stopped and cleaned up"
}

cmd_status() {
    echo ""
    echo "=== Adapter Status ==="
    if pgrep -f "lc_adapter" > /dev/null; then
        echo -e "Adapter: ${GREEN}RUNNING${NC}"
        pgrep -fa "lc_adapter" | head -1
    else
        echo -e "Adapter: ${RED}STOPPED${NC}"
    fi

    if load_config 2>/dev/null; then
        echo ""
        echo "=== Configuration ==="
        echo "ADAPTER_DIR: $ADAPTER_DIR"
        echo "OID: $OID"
        echo "IID: $IID"
        echo "LOG_SOURCE: $LOG_SOURCE"
    fi
    echo ""
}

cmd_logs() {
    load_config || exit 1

    if [ -f "$ADAPTER_DIR/adapter.log" ]; then
        echo "=== Adapter Logs (last 50 lines) ==="
        tail -50 "$ADAPTER_DIR/adapter.log"
    else
        log_warn "No log file found at $ADAPTER_DIR/adapter.log"
    fi
}

cmd_info() {
    load_config || exit 1

    echo "=== Adapter Configuration ==="
    echo "ADAPTER_DIR: $ADAPTER_DIR"
    echo "OID: $OID"
    echo "IID: $IID"
    echo "HOSTNAME: $HOSTNAME_VAL"
    echo "LOG_SOURCE: $LOG_SOURCE"
    echo "LOG_CMD: $LOG_CMD"

    if [ -f "$ADAPTER_DIR/lc_adapter" ]; then
        echo ""
        echo "Adapter binary: $ADAPTER_DIR/lc_adapter"
        ls -la "$ADAPTER_DIR/lc_adapter"
    fi
}

cmd_sample() {
    local count="${1:-20}"
    detect_platform

    log_info "Capturing $count sample log lines from $LOG_SOURCE..." >&2

    case "$LOG_SOURCE" in
        journalctl)
            journalctl -n "$count" --no-pager
            ;;
        file)
            tail -n "$count" "$LOG_FILE"
            ;;
        unified)
            log show --last 1m --style syslog | tail -"$count"
            ;;
    esac
}

# Main command dispatcher
case "${1:-help}" in
    setup)
        shift
        cmd_setup "$@"
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    info)
        cmd_info
        ;;
    sample)
        shift
        cmd_sample "$@"
        ;;
    help|--help|-h)
        echo "LimaCharlie Adapter Test Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  sample [count]     - Capture sample logs (default 20 lines)"
        echo "  setup <oid> <iid> [mapping options] - Download adapter and create launch script"
        echo "  start              - Start the adapter in background"
        echo "  stop               - Stop the adapter and cleanup"
        echo "  status             - Check if adapter is running"
        echo "  logs               - Show adapter logs"
        echo "  info               - Show current configuration"
        echo ""
        echo "Mapping options for setup:"
        echo "  --grok <pattern>        - Grok parsing pattern"
        echo "  --event-type <path>     - Field path for event type"
        echo "  --event-time <path>     - Field path for event timestamp"
        echo "  --event-time-tz <tz>    - Timezone for timestamps (e.g., America/Los_Angeles)"
        echo "  --hostname-path <path>  - Field path for hostname"
        echo ""
        echo "Example (basic):"
        echo "  $0 sample 20"
        echo "  $0 setup 8cbe27f4-bfa1-4afb-ba19-138cd51389cd 7a0ca138-693a-481f-abde-8bd0871dd115"
        echo "  $0 start"
        echo ""
        echo "Example (with parsing):"
        echo "  $0 setup <oid> <iid> --grok '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{GREEDYDATA:msg}' \\"
        echo "      --event-type host --event-time date --event-time-tz America/Los_Angeles --hostname-path host"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
