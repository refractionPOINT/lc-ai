#!/bin/bash
#
# False Positive Pattern Detector for LimaCharlie Detections
#
# Analyzes a JSONL file of detections and identifies common FP patterns.
# Outputs structured results for LLM analysis.
#
# Usage: ./fp-pattern-detector.sh <detections.jsonl> [--threshold N]
#
# Requirements: jq, bash 4+, standard Unix tools (sort, uniq, awk, etc.)
#

set -uo pipefail
# Note: -e removed to allow jq commands to fail gracefully when no matches found

# ============================================================================
# Configuration & Thresholds
# ============================================================================

# Minimum occurrences to flag as pattern
FREQ_THRESHOLD=${FREQ_THRESHOLD:-50}
# Percentage threshold for single-host concentration
HOST_CONCENTRATION_PCT=${HOST_CONCENTRATION_PCT:-70}
# Minimum count for periodicity detection
PERIODIC_MIN_COUNT=${PERIODIC_MIN_COUNT:-10}
# Mass deployment: min hosts in time window
MASS_DEPLOY_MIN_HOSTS=${MASS_DEPLOY_MIN_HOSTS:-10}
# Mass deployment: time window in seconds
MASS_DEPLOY_WINDOW=${MASS_DEPLOY_WINDOW:-1800}
# Sample size for detection IDs
SAMPLE_SIZE=${SAMPLE_SIZE:-5}

# ============================================================================
# Helper Functions
# ============================================================================

usage() {
    cat <<EOF
Usage: $0 <detections.jsonl> [options]

Analyzes LimaCharlie detection data for common false positive patterns.

Options:
  --threshold N         Minimum occurrences to flag (default: $FREQ_THRESHOLD)
  --host-pct N          Host concentration percentage (default: $HOST_CONCENTRATION_PCT)
  --sample-size N       Number of sample IDs per pattern (default: $SAMPLE_SIZE)
  --help                Show this help

Environment variables:
  FREQ_THRESHOLD, HOST_CONCENTRATION_PCT, PERIODIC_MIN_COUNT,
  MASS_DEPLOY_MIN_HOSTS, MASS_DEPLOY_WINDOW, SAMPLE_SIZE

Output: JSON structured results to stdout
EOF
    exit 1
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

check_dependencies() {
    local missing=()
    for cmd in jq sort uniq awk head tail wc; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "ERROR: Missing required commands: ${missing[*]}" >&2
        exit 1
    fi
}

# Get samples of detection IDs for a given filter
get_samples() {
    local filter="$1"
    local file="$2"
    jq -r "select($filter) | .detect_id // .id // .routing.event_id // \"unknown\"" "$file" 2>/dev/null | head -n "$SAMPLE_SIZE" | jq -R -s 'split("\n") | map(select(length > 0))'
}

# ============================================================================
# Pattern Detection Functions
# ============================================================================

# Pattern 1: High-Frequency Single-Host
# >70% of a detection category from ONE hostname
detect_single_host_concentration() {
    local file="$1"
    log "Analyzing: High-Frequency Single-Host Pattern"

    # Group by category, find host distribution
    jq -r '[.cat // "unknown", .detect.routing.hostname // .routing.hostname // "unknown", .detect_id // .id // "unknown"] | @tsv' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        cat=$1; host=$2; id=$3
        cat_total[cat]++
        cat_host[cat":"host]++
        if (!cat_sample[cat]) cat_sample[cat] = id
        else if (split(cat_sample[cat], arr, ",") < 5) cat_sample[cat] = cat_sample[cat] "," id
    }
    END {
        for (cat in cat_total) {
            total = cat_total[cat]
            max_host = ""; max_count = 0
            for (key in cat_host) {
                split(key, parts, ":")
                if (parts[1] == cat && cat_host[key] > max_count) {
                    max_count = cat_host[key]
                    max_host = parts[2]
                }
            }
            pct = (max_count / total) * 100
            if (pct >= '"$HOST_CONCENTRATION_PCT"' && total >= '"$FREQ_THRESHOLD"') {
                printf "%s\t%s\t%d\t%d\t%.1f\t%s\n", cat, max_host, max_count, total, pct, cat_sample[cat]
            }
        }
    }' | sort -t$'\t' -k3 -rn | while IFS=$'\t' read -r cat host count total pct samples; do
        jq -cn --arg cat "$cat" --arg host "$host" --argjson count "$count" \
              --argjson total "$total" --arg pct "$pct" --arg samples "$samples" \
            '{
                pattern: "single_host_concentration",
                category: $cat,
                dominant_host: $host,
                host_count: $count,
                total_count: $total,
                concentration_pct: ($pct | tonumber),
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 2: Temporal Periodicity (hourly/daily)
detect_temporal_periodicity() {
    local file="$1"
    log "Analyzing: Temporal Periodicity Pattern"

    # Extract category + hour-of-day
    jq -r '
        def ts_to_hour: (. / 1000 | floor) % 86400 / 3600 | floor;
        [
            (.cat // "unknown"),
            ((.ts // .detect.routing.event_time // 0) | ts_to_hour),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        cat=$1; hour=$2; id=$3
        key = cat ":" hour
        count[key]++
        cat_total[cat]++
        if (!sample[cat]) sample[cat] = id
    }
    END {
        for (cat in cat_total) {
            # Find if detections cluster in specific hours
            max_hour = -1; max_count = 0
            for (h = 0; h < 24; h++) {
                key = cat ":" h
                if (count[key] > max_count) {
                    max_count = count[key]
                    max_hour = h
                }
            }
            total = cat_total[cat]
            pct = (max_count / total) * 100
            # Flag if >50% in single hour and enough detections
            if (pct >= 50 && total >= '"$PERIODIC_MIN_COUNT"') {
                printf "%s\t%d\t%d\t%d\t%.1f\t%s\n", cat, max_hour, max_count, total, pct, sample[cat]
            }
        }
    }' | while IFS=$'\t' read -r cat hour count total pct sample; do
        jq -cn --arg cat "$cat" --argjson hour "$hour" --argjson count "$count" \
              --argjson total "$total" --arg pct "$pct" --arg sample "$sample" \
            '{
                pattern: "temporal_periodicity",
                category: $cat,
                peak_hour_utc: $hour,
                peak_count: $count,
                total_count: $total,
                concentration_pct: ($pct | tonumber),
                signal: "Detections cluster at specific hour - likely scheduled task",
                sample_ids: [$sample]
            }'
    done
}

# Pattern 3: Identical Command-Line
detect_identical_cmdline() {
    local file="$1"
    log "Analyzing: Identical Command-Line Pattern"

    jq -r '
        [
            (.detect.event.COMMAND_LINE // .event.COMMAND_LINE // ""),
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    $1 != "" {
        cmdline=$1; cat=$2; id=$3
        count[cmdline]++
        cmdline_cat[cmdline] = cat
        if (!sample[cmdline]) sample[cmdline] = id
        else if (split(sample[cmdline], arr, ",") < 5) sample[cmdline] = sample[cmdline] "," id
    }
    END {
        for (cmd in count) {
            if (count[cmd] >= '"$FREQ_THRESHOLD"') {
                # Truncate long command lines for display
                display = substr(cmd, 1, 200)
                if (length(cmd) > 200) display = display "..."
                gsub(/\t/, " ", display)
                printf "%d\t%s\t%s\t%s\n", count[cmd], cmdline_cat[cmd], display, sample[cmd]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count cat cmdline samples; do
        jq -cn --argjson count "$count" --arg cat "$cat" --arg cmdline "$cmdline" --arg samples "$samples" \
            '{
                pattern: "identical_cmdline",
                category: $cat,
                count: $count,
                command_line_preview: $cmdline,
                signal: "Same command repeated - likely automation or deployment",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 4: Known Admin Tool Paths
detect_admin_tool_paths() {
    local file="$1"
    log "Analyzing: Known Admin Tool Path Pattern"

    # Define known admin/IT tool path patterns
    jq -r '
        def is_admin_path:
            . as $p |
            ($p | test("(?i)\\\\CCM\\\\"; "i")) or
            ($p | test("(?i)\\\\SCCM\\\\"; "i")) or
            ($p | test("(?i)\\\\Ansible"; "i")) or
            ($p | test("(?i)\\\\SysInternals\\\\"; "i")) or
            ($p | test("(?i)\\\\AdminTools\\\\"; "i")) or
            ($p | test("(?i)\\\\WSUS\\\\"; "i")) or
            ($p | test("(?i)\\\\PDQ"; "i")) or
            ($p | test("(?i)\\\\BigFix\\\\"; "i")) or
            ($p | test("(?i)\\\\Tanium\\\\"; "i")) or
            ($p | test("(?i)\\\\CrowdStrike\\\\"; "i")) or
            ($p | test("(?i)\\\\SentinelOne\\\\"; "i")) or
            ($p | test("(?i)/usr/local/bin/"; "i")) or
            ($p | test("(?i)/opt/ansible"; "i")) or
            ($p | test("(?i)/opt/chef"; "i")) or
            ($p | test("(?i)/opt/puppet"; "i"));

        (.detect.event.FILE_PATH // .event.FILE_PATH // "") as $path |
        select($path != "" and ($path | is_admin_path)) |
        [
            $path,
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        # Extract tool name from path
        path=$1; cat=$2; id=$3
        tool = path
        if (match(path, /\\CCM\\/)) tool = "SCCM/CCM"
        else if (match(path, /\\SCCM\\/)) tool = "SCCM"
        else if (match(path, /Ansible/)) tool = "Ansible"
        else if (match(path, /SysInternals/)) tool = "SysInternals"
        else if (match(path, /\\WSUS\\/)) tool = "WSUS"
        else if (match(path, /\\PDQ/)) tool = "PDQ Deploy"
        else if (match(path, /\\BigFix\\/)) tool = "BigFix"
        else if (match(path, /\\Tanium\\/)) tool = "Tanium"
        else if (match(path, /CrowdStrike/)) tool = "CrowdStrike"
        else if (match(path, /SentinelOne/)) tool = "SentinelOne"
        else if (match(path, /\/opt\/chef/)) tool = "Chef"
        else if (match(path, /\/opt\/puppet/)) tool = "Puppet"
        else tool = "Other Admin Tool"

        count[tool]++
        tool_cat[tool] = cat
        if (!sample[tool]) sample[tool] = id
        else if (split(sample[tool], arr, ",") < 5) sample[tool] = sample[tool] "," id
        if (!sample_path[tool]) sample_path[tool] = path
    }
    END {
        for (tool in count) {
            if (count[tool] >= 5) {
                printf "%d\t%s\t%s\t%s\t%s\n", count[tool], tool, tool_cat[tool], sample_path[tool], sample[tool]
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r count tool cat path samples; do
        jq -cn --argjson count "$count" --arg tool "$tool" --arg cat "$cat" \
              --arg path "$path" --arg samples "$samples" \
            '{
                pattern: "admin_tool_path",
                tool_identified: $tool,
                category: $cat,
                count: $count,
                sample_path: $path,
                signal: "Known IT/admin tool - likely legitimate",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 5: Service Account Pattern
detect_service_accounts() {
    local file="$1"
    log "Analyzing: Service Account Pattern"

    jq -r '
        def is_service_account:
            . as $u |
            ($u | test("^svc[_-]"; "i")) or
            ($u | test("[_-]service$"; "i")) or
            ($u | test("^SYSTEM$"; "i")) or
            ($u | test("^LOCAL SERVICE$"; "i")) or
            ($u | test("^NETWORK SERVICE$"; "i")) or
            ($u | test("^NT AUTHORITY\\\\"; "i")) or
            ($u | test("^NT SERVICE\\\\"; "i")) or
            ($u | test("^IIS APPPOOL\\\\"; "i")) or
            ($u | test("^\\$"; "")) or  # Computer accounts ending in $
            ($u | test("\\$$"; ""));

        (.detect.event.USER_NAME // .event.USER_NAME // "") as $user |
        select($user != "" and ($user | is_service_account)) |
        [
            $user,
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        user=$1; cat=$2; id=$3
        count[user]++
        user_cat[user] = cat
        if (!sample[user]) sample[user] = id
        else if (split(sample[user], arr, ",") < 5) sample[user] = sample[user] "," id
    }
    END {
        for (user in count) {
            if (count[user] >= '"$FREQ_THRESHOLD"') {
                printf "%d\t%s\t%s\t%s\n", count[user], user, user_cat[user], sample[user]
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r count user cat samples; do
        jq -cn --argjson count "$count" --arg user "$user" --arg cat "$cat" --arg samples "$samples" \
            '{
                pattern: "service_account",
                user_name: $user,
                category: $cat,
                count: $count,
                signal: "Service account activity - typically automated/legitimate",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 6: Same Detection + Same Sensor (noisy sensor)
detect_noisy_sensor() {
    local file="$1"
    log "Analyzing: Noisy Sensor Pattern (Same Detection + Same Sensor)"

    jq -r '
        [
            (.cat // "unknown"),
            (.detect.routing.sid // .routing.sid // "unknown"),
            (.detect.routing.hostname // .routing.hostname // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        cat=$1; sid=$2; host=$3; id=$4
        key = cat "\t" sid "\t" host
        count[key]++
        if (!sample[key]) sample[key] = id
        else if (split(sample[key], arr, ",") < 5) sample[key] = sample[key] "," id
    }
    END {
        for (key in count) {
            if (count[key] >= '"$FREQ_THRESHOLD"') {
                printf "%d\t%s\t%s\n", count[key], key, sample[key]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count cat sid host samples; do
        jq -cn --argjson count "$count" --arg cat "$cat" --arg sid "$sid" \
              --arg host "$host" --arg samples "$samples" \
            '{
                pattern: "noisy_sensor",
                category: $cat,
                sensor_id: $sid,
                hostname: $host,
                count: $count,
                signal: "Single sensor generating excessive alerts - misconfigured app or stuck process",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 7: Same File Hash Pattern
detect_same_hash() {
    local file="$1"
    log "Analyzing: Same File Hash Pattern"

    jq -r '
        (.detect.event.HASH // .event.HASH // "") as $hash |
        select($hash != "" and $hash != null) |
        [
            $hash,
            (.cat // "unknown"),
            (.detect.event.FILE_PATH // .event.FILE_PATH // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        hash=$1; cat=$2; path=$3; id=$4
        count[hash]++
        hash_cat[hash] = cat
        hash_path[hash] = path
        if (!sample[hash]) sample[hash] = id
        else if (split(sample[hash], arr, ",") < 5) sample[hash] = sample[hash] "," id
    }
    END {
        for (hash in count) {
            if (count[hash] >= '"$FREQ_THRESHOLD"') {
                printf "%d\t%s\t%s\t%s\t%s\n", count[hash], hash, hash_cat[hash], hash_path[hash], sample[hash]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count hash cat path samples; do
        jq -cn --argjson count "$count" --arg hash "$hash" --arg cat "$cat" \
              --arg path "$path" --arg samples "$samples" \
            '{
                pattern: "same_hash",
                hash: $hash,
                category: $cat,
                count: $count,
                sample_path: $path,
                signal: "Same binary hash across many detections - likely org-wide legitimate tool",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 8: Tagged Infrastructure (dev/test/staging)
detect_tagged_infrastructure() {
    local file="$1"
    log "Analyzing: Tagged Infrastructure Pattern"

    jq -r '
        def has_infra_tag:
            . as $tags |
            if type == "array" then
                ($tags | map(test("(?i)^(dev|test|staging|qa|lab|sandbox|build|automation|ci|cd)"; "i")) | any)
            else false end;

        (.detect.routing.tags // .routing.tags // []) as $tags |
        select($tags | has_infra_tag) |
        [
            ($tags | map(select(test("(?i)^(dev|test|staging|qa|lab|sandbox|build|automation|ci|cd)"; "i"))) | first // "unknown"),
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        tag=$1; cat=$2; id=$3
        count[tag]++
        tag_cat[tag] = cat
        if (!sample[tag]) sample[tag] = id
        else if (split(sample[tag], arr, ",") < 5) sample[tag] = sample[tag] "," id
    }
    END {
        for (tag in count) {
            if (count[tag] >= 10) {
                printf "%d\t%s\t%s\t%s\n", count[tag], tag, tag_cat[tag], sample[tag]
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r count tag cat samples; do
        jq -cn --argjson count "$count" --arg tag "$tag" --arg cat "$cat" --arg samples "$samples" \
            '{
                pattern: "tagged_infrastructure",
                tag: $tag,
                category: $cat,
                count: $count,
                signal: "Non-production infrastructure tag - expected noisy behavior",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 9: Development Environment Paths
detect_dev_environment() {
    local file="$1"
    log "Analyzing: Development Environment Pattern"

    jq -r '
        def is_dev_path:
            . as $p |
            ($p | test("(?i)node_modules"; "i")) or
            ($p | test("(?i)\\.vscode"; "i")) or
            ($p | test("(?i)\\.idea"; "i")) or
            ($p | test("(?i)\\\\venv\\\\"; "i")) or
            ($p | test("(?i)/venv/"; "i")) or
            ($p | test("(?i)\\.git/"; "i")) or
            ($p | test("(?i)\\\\AppData\\\\Local\\\\Temp"; "i")) or
            ($p | test("(?i)/tmp/"; "i")) or
            ($p | test("(?i)\\\\npm-cache"; "i")) or
            ($p | test("(?i)\\.cargo"; "i")) or
            ($p | test("(?i)\\.rustup"; "i")) or
            ($p | test("(?i)\\\\go\\\\pkg"; "i")) or
            ($p | test("(?i)/go/pkg/"; "i")) or
            ($p | test("(?i)__pycache__"; "i")) or
            ($p | test("(?i)\\.nuget"; "i"));

        (.detect.event.FILE_PATH // .event.FILE_PATH // "") as $path |
        select($path != "" and ($path | is_dev_path)) |
        [
            (if ($path | test("node_modules")) then "node_modules"
             elif ($path | test("\\.vscode")) then "vscode"
             elif ($path | test("\\.idea")) then "idea"
             elif ($path | test("venv")) then "python-venv"
             elif ($path | test("\\.git")) then "git"
             elif ($path | test("Temp|tmp"; "i")) then "temp-directory"
             elif ($path | test("npm-cache")) then "npm-cache"
             elif ($path | test("\\.cargo")) then "rust-cargo"
             elif ($path | test("go.pkg|/go/pkg"; "i")) then "go-modules"
             elif ($path | test("__pycache__")) then "python-cache"
             elif ($path | test("\\.nuget")) then "nuget"
             else "other-dev" end),
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        devtype=$1; cat=$2; id=$3
        count[devtype]++
        type_cat[devtype] = cat
        if (!sample[devtype]) sample[devtype] = id
        else if (split(sample[devtype], arr, ",") < 5) sample[devtype] = sample[devtype] "," id
    }
    END {
        for (dtype in count) {
            if (count[dtype] >= 10) {
                printf "%d\t%s\t%s\t%s\n", count[dtype], dtype, type_cat[dtype], sample[dtype]
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r count devtype cat samples; do
        jq -cn --argjson count "$count" --arg devtype "$devtype" --arg cat "$cat" --arg samples "$samples" \
            '{
                pattern: "dev_environment",
                dev_type: $devtype,
                category: $cat,
                count: $count,
                signal: "Development environment artifact - typically build/compile noise",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 10: Hostname Naming Convention
detect_hostname_patterns() {
    local file="$1"
    log "Analyzing: Hostname Naming Convention Pattern"

    jq -r '
        def hostname_type:
            . as $h |
            if ($h | test("(?i)^(dev|DEV)-"; "i")) then "dev-prefix"
            elif ($h | test("(?i)^(test|TEST)-"; "i")) then "test-prefix"
            elif ($h | test("(?i)^(stg|staging|STG)-"; "i")) then "staging-prefix"
            elif ($h | test("(?i)^(build|BUILD)-"; "i")) then "build-prefix"
            elif ($h | test("(?i)^(ci|CI)-"; "i")) then "ci-prefix"
            elif ($h | test("(?i)-(dev|DEV)$"; "i")) then "dev-suffix"
            elif ($h | test("(?i)-(test|TEST)$"; "i")) then "test-suffix"
            elif ($h | test("(?i)^(dc|DC)[0-9]"; "i")) then "domain-controller"
            elif ($h | test("(?i)^(sccm|SCCM)"; "i")) then "sccm-server"
            elif ($h | test("(?i)^(wsus|WSUS)"; "i")) then "wsus-server"
            elif ($h | test("(?i)^(mgmt|MGMT)"; "i")) then "mgmt-server"
            elif ($h | test("(?i)(kiosk|KIOSK)"; "i")) then "kiosk"
            elif ($h | test("(?i)(sandbox|SANDBOX)"; "i")) then "sandbox"
            elif ($h | test("(?i)(lab|LAB)"; "i")) then "lab"
            else null end;

        (.detect.routing.hostname // .routing.hostname // "") as $host |
        ($host | hostname_type) as $htype |
        select($htype != null) |
        [
            $htype,
            $host,
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        htype=$1; host=$2; cat=$3; id=$4
        count[htype]++
        type_cat[htype] = cat
        if (!sample_host[htype]) sample_host[htype] = host
        if (!sample[htype]) sample[htype] = id
        else if (split(sample[htype], arr, ",") < 5) sample[htype] = sample[htype] "," id
    }
    END {
        for (htype in count) {
            if (count[htype] >= 10) {
                printf "%d\t%s\t%s\t%s\t%s\n", count[htype], htype, type_cat[htype], sample_host[htype], sample[htype]
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r count htype cat samplehost samples; do
        jq -cn --argjson count "$count" --arg htype "$htype" --arg cat "$cat" \
              --arg samplehost "$samplehost" --arg samples "$samples" \
            '{
                pattern: "hostname_convention",
                hostname_type: $htype,
                category: $cat,
                count: $count,
                sample_hostname: $samplehost,
                signal: "Hostname matches infrastructure naming convention",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 11: Low-Entropy Detection Name (same rule fires excessively)
detect_noisy_rules() {
    local file="$1"
    log "Analyzing: Noisy Detection Rule Pattern"

    jq -r '
        [
            (.detect.name // .name // .cat // "unknown"),
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        name=$1; cat=$2; id=$3
        count[name]++
        name_cat[name] = cat
        if (!sample[name]) sample[name] = id
        else if (split(sample[name], arr, ",") < 5) sample[name] = sample[name] "," id
    }
    END {
        for (name in count) {
            if (count[name] >= 100) {
                printf "%d\t%s\t%s\t%s\n", count[name], name, name_cat[name], sample[name]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count name cat samples; do
        jq -cn --argjson count "$count" --arg name "$name" --arg cat "$cat" --arg samples "$samples" \
            '{
                pattern: "noisy_rule",
                rule_name: $name,
                category: $cat,
                count: $count,
                signal: "Detection rule fires excessively - rule may be too broad",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 12: Parent-Child Process Repetition
detect_process_tree_repetition() {
    local file="$1"
    log "Analyzing: Process Tree Repetition Pattern"

    jq -r '
        (.detect.event.PARENT.FILE_PATH // .event.PARENT.FILE_PATH // "") as $parent |
        (.detect.event.FILE_PATH // .event.FILE_PATH // "") as $child |
        select($parent != "" and $child != "") |
        [
            $parent,
            $child,
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        parent=$1; child=$2; cat=$3; id=$4
        # Extract just filenames for grouping
        split(parent, pa, /[\\\/]/)
        split(child, ca, /[\\\/]/)
        pname = pa[length(pa)]
        cname = ca[length(ca)]
        key = pname " -> " cname
        count[key]++
        key_cat[key] = cat
        key_parent[key] = parent
        key_child[key] = child
        if (!sample[key]) sample[key] = id
        else if (split(sample[key], arr, ",") < 5) sample[key] = sample[key] "," id
    }
    END {
        for (key in count) {
            if (count[key] >= '"$FREQ_THRESHOLD"') {
                printf "%d\t%s\t%s\t%s\t%s\t%s\n", count[key], key, key_cat[key], key_parent[key], key_child[key], sample[key]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count chain cat parent child samples; do
        jq -cn --argjson count "$count" --arg chain "$chain" --arg cat "$cat" \
              --arg parent "$parent" --arg child "$child" --arg samples "$samples" \
            '{
                pattern: "process_tree_repetition",
                process_chain: $chain,
                category: $cat,
                count: $count,
                parent_path: $parent,
                child_path: $child,
                signal: "Same parent->child process chain repeated - likely legitimate app behavior",
                sample_ids: ($samples | split(","))
            }'
    done
}

# Pattern 13: Business Hours Concentration
detect_business_hours() {
    local file="$1"
    log "Analyzing: Business Hours Concentration Pattern"

    jq -r '
        def is_business_hour:
            . as $h | $h >= 9 and $h < 17;
        def is_weekday:
            . as $d | $d >= 1 and $d <= 5;

        ((.ts // .detect.routing.event_time // 0) / 1000 | floor) as $epoch |
        (($epoch % 86400) / 3600 | floor) as $hour |
        (($epoch / 86400 | floor) + 4) % 7 as $dow |  # 0=Sun, 1=Mon, etc
        [
            (.cat // "unknown"),
            (if ($hour | is_business_hour) and ($dow | is_weekday) then "business" else "non-business" end),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        cat=$1; period=$2; id=$3
        if (period == "business") biz[cat]++
        else nonbiz[cat]++
        total[cat]++
        if (!sample[cat]) sample[cat] = id
    }
    END {
        for (cat in total) {
            if (total[cat] >= '"$FREQ_THRESHOLD"') {
                biz_count = biz[cat] + 0
                pct = (biz_count / total[cat]) * 100
                if (pct >= 90) {
                    printf "%.1f\t%s\t%d\t%d\t%s\n", pct, cat, biz_count, total[cat], sample[cat]
                }
            }
        }
    }' | sort -t$'\t' -k1 -rn | while IFS=$'\t' read -r pct cat biz_count total sample; do
        jq -cn --arg pct "$pct" --arg cat "$cat" --argjson biz_count "$biz_count" \
              --argjson total "$total" --arg sample "$sample" \
            '{
                pattern: "business_hours_concentration",
                category: $cat,
                business_hours_pct: ($pct | tonumber),
                business_hours_count: $biz_count,
                total_count: $total,
                signal: "90%+ detections during business hours - likely user-driven legitimate activity",
                sample_ids: [$sample]
            }'
    done
}

# Pattern 14: Network Destination Repetition
detect_network_destination_repetition() {
    local file="$1"
    log "Analyzing: Network Destination Repetition Pattern"

    jq -r '
        # Handle various network event structures
        (
            .detect.event.NETWORK_ACTIVITY[0].IP_ADDRESS //
            .event.NETWORK_ACTIVITY[0].IP_ADDRESS //
            .detect.event.DOMAIN_NAME //
            .event.DOMAIN_NAME //
            .detect.event.IP_ADDRESS //
            .event.IP_ADDRESS //
            ""
        ) as $dest |
        select($dest != "" and $dest != null) |
        [
            $dest,
            (.cat // "unknown"),
            (.detect_id // .id // "unknown")
        ] | @tsv
    ' "$file" 2>/dev/null | \
    awk -F'\t' '
    {
        dest=$1; cat=$2; id=$3
        count[dest]++
        dest_cat[dest] = cat
        if (!sample[dest]) sample[dest] = id
        else if (split(sample[dest], arr, ",") < 5) sample[dest] = sample[dest] "," id
    }
    END {
        for (dest in count) {
            if (count[dest] >= '"$FREQ_THRESHOLD"') {
                printf "%d\t%s\t%s\t%s\n", count[dest], dest, dest_cat[dest], sample[dest]
            }
        }
    }' | sort -t$'\t' -k1 -rn | head -20 | while IFS=$'\t' read -r count dest cat samples; do
        # Check if it looks like internal IP
        is_internal="false"
        if [[ "$dest" =~ ^10\. ]] || [[ "$dest" =~ ^192\.168\. ]] || [[ "$dest" =~ ^172\.(1[6-9]|2[0-9]|3[01])\. ]]; then
            is_internal="true"
        fi
        jq -cn --argjson count "$count" --arg dest "$dest" --arg cat "$cat" \
              --arg samples "$samples" --argjson is_internal "$is_internal" \
            '{
                pattern: "network_destination_repetition",
                destination: $dest,
                category: $cat,
                count: $count,
                is_internal_ip: $is_internal,
                signal: "Same network destination in many detections - possibly internal service or CDN",
                sample_ids: ($samples | split(","))
            }'
    done
}

# ============================================================================
# Summary Statistics
# ============================================================================

generate_summary() {
    local file="$1"
    log "Generating summary statistics"

    jq -sc '
        {
            pattern: "summary",
            total_detections: length,
            unique_categories: ([.[].cat] | unique | length),
            unique_hostnames: ([.[] | .detect.routing.hostname // .routing.hostname] | unique | length),
            unique_sensors: ([.[] | .detect.routing.sid // .routing.sid] | unique | length),
            categories: ([.[].cat] | group_by(.) | map({category: .[0], count: length}) | sort_by(-.count) | .[0:10]),
            time_range: {
                earliest: ([.[].ts // .detect.routing.event_time] | min),
                latest: ([.[].ts // .detect.routing.event_time] | max)
            }
        }
    ' "$file" 2>/dev/null
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local input_file=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --threshold)
                FREQ_THRESHOLD="$2"
                shift 2
                ;;
            --host-pct)
                HOST_CONCENTRATION_PCT="$2"
                shift 2
                ;;
            --sample-size)
                SAMPLE_SIZE="$2"
                shift 2
                ;;
            --help|-h)
                usage
                ;;
            -*)
                echo "Unknown option: $1" >&2
                usage
                ;;
            *)
                input_file="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$input_file" ]]; then
        echo "ERROR: No input file specified" >&2
        usage
    fi

    if [[ ! -f "$input_file" ]]; then
        echo "ERROR: File not found: $input_file" >&2
        exit 1
    fi

    check_dependencies

    log "Starting FP pattern analysis on: $input_file"
    log "Thresholds: freq=$FREQ_THRESHOLD, host_pct=$HOST_CONCENTRATION_PCT%, sample_size=$SAMPLE_SIZE"

    # Create temp file to collect all JSON objects
    local tmpfile
    tmpfile=$(mktemp)
    trap "rm -f '$tmpfile'" EXIT

    # Run all pattern detectors and collect output
    # Logs go to stderr (visible), JSON output goes to tmpfile
    for pattern_func in \
        generate_summary \
        detect_single_host_concentration \
        detect_temporal_periodicity \
        detect_identical_cmdline \
        detect_admin_tool_paths \
        detect_service_accounts \
        detect_noisy_sensor \
        detect_same_hash \
        detect_tagged_infrastructure \
        detect_dev_environment \
        detect_hostname_patterns \
        detect_noisy_rules \
        detect_process_tree_repetition \
        detect_business_hours \
        detect_network_destination_repetition
    do
        $pattern_func "$input_file" >> "$tmpfile"
    done

    log "Collected patterns in temp file"

    # Output as JSON array
    # The temp file contains multiple JSON objects (one per line, compact format)
    if [[ -s "$tmpfile" ]]; then
        # Use jq slurp to combine all objects into an array
        # Filter out empty lines and invalid JSON
        jq -s '.' "$tmpfile" 2>/dev/null || {
            log "Warning: Some JSON output was malformed, attempting recovery..."
            # Fallback: try to extract valid JSON lines
            grep -v '^$' "$tmpfile" | jq -c '.' 2>/dev/null | jq -s '.' 2>/dev/null || echo "[]"
        }
    else
        log "No patterns detected above thresholds"
        echo "[]"
    fi

    log "Analysis complete"
}

main "$@"
