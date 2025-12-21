#!/bin/bash

# analyze-lc-result.sh
# Downloads (if URL provided) and analyzes the structure of a LimaCharlie API result JSON file
# Usage: ./analyze-lc-result.sh <resource-link-url-or-file-path>

set -e

# Check if input is provided
if [ -z "$1" ]; then
    echo "Error: No URL or file path provided" >&2
    echo "" >&2
    echo "Usage: $0 <resource-link-url-or-file-path>" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  $0 https://storage.googleapis.com/lc-tmp-mcp-export/..." >&2
    echo "  $0 /tmp/lc-result-123456.json" >&2
    exit 1
fi

INPUT="$1"
DOWNLOADED=false

# Cleanup function for downloaded files on error
cleanup_on_error() {
    if [ "$DOWNLOADED" = true ] && [ -n "$FILE_PATH" ] && [ -f "$FILE_PATH" ]; then
        rm -f "$FILE_PATH"
    fi
}

# Detect if input is a URL or file path
if [[ "$INPUT" =~ ^https?:// ]]; then
    # It's a URL - download it
    TIMESTAMP=$(date +%s%N)
    FILE_PATH="/tmp/lc-result-${TIMESTAMP}.json"
    DOWNLOADED=true

    # Download with curl (auto-decompresses .gz)
    if ! curl -sL "$INPUT" -o "$FILE_PATH" 2>/dev/null; then
        echo "Error: Failed to download from URL" >&2
        echo "The resource_link may be expired or inaccessible" >&2
        cleanup_on_error
        exit 1
    fi

    # Check if downloaded file is empty
    if [ ! -s "$FILE_PATH" ]; then
        echo "Error: Downloaded file is empty" >&2
        cleanup_on_error
        exit 1
    fi
else
    # It's a file path - use directly
    FILE_PATH="$INPUT"
    DOWNLOADED=false
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH" >&2
    cleanup_on_error
    exit 1
fi

# Check if file is readable
if [ ! -r "$FILE_PATH" ]; then
    echo "Error: File is not readable: $FILE_PATH" >&2
    cleanup_on_error
    exit 1
fi

# Verify it's valid JSON before schema analysis
if ! jq empty "$FILE_PATH" 2>/dev/null; then
    echo "Error: Content is not valid JSON" >&2
    if [ "$DOWNLOADED" = true ]; then
        echo "First 200 bytes of content:" >&2
        head -c 200 "$FILE_PATH" >&2
    fi
    cleanup_on_error
    exit 1
fi

# Generate and output the JSON schema to stdout (compact format for LLM consumption)
if ! jq -c -n '
  def schema:
    if type == "object" then
      with_entries(.value |= schema)
    elif type == "array" then
      if length == 0 then
        []
      else
        # assume elements have same shape, use first
        [ (.[0] | schema) ]
      end
    else
      type
    end;

  reduce inputs as $i ({}; . * ($i | schema))
' "$FILE_PATH" 2>/dev/null; then
    echo "Error: Failed to analyze JSON structure" >&2
    cleanup_on_error
    exit 1
fi

# Output the file path to stderr with delimiter
echo "---FILE_PATH---" >&2
echo "$FILE_PATH" >&2
