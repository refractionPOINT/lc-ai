#!/bin/bash

# LimaCharlie Onboarding Hook
# Runs on SessionStart to display welcome message

PROJECT_ROOT="$CLAUDE_PROJECT_DIR"
MARKER_FILE="$PROJECT_ROOT/.claude/.onboarded"

# Determine if this is first time or returning user
FIRST_TIME=false
if [ ! -f "$MARKER_FILE" ]; then
    FIRST_TIME=true
fi

# Detect configured services (for both authenticated and unauthenticated screens)
STATUS_LINES=""
SETUP_REQUIRED=false

# Check if LimaCharlie plugin is enabled (MCP comes from plugin)
LC_MCP_CONFIGURED=false
if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    if grep -qE '"lc-essentials@lc-marketplace"\s*:\s*true' "$PROJECT_ROOT/.claude/settings.json"; then
        LC_MCP_CONFIGURED=true
    fi
fi

if [ "$LC_MCP_CONFIGURED" = false ]; then
    SETUP_REQUIRED=true
fi

# Check MCP servers from installed plugin
PLUGIN_MCP="$PROJECT_ROOT/plugins/lc-essentials/.mcp.json"
if [ -f "$PLUGIN_MCP" ]; then
    MCP_COUNT=$(grep -o '"mcpServers"' "$PLUGIN_MCP" | wc -l)
    if [ $MCP_COUNT -gt 0 ]; then
        # Extract server names using grep and sed (exclude mcpServers and headers)
        MCP_SERVERS=$(grep -oP '"\K[^"]+(?="\s*:\s*\{)' "$PLUGIN_MCP" | grep -v "mcpServers" | grep -v "^headers$" | head -5)
        if [ -n "$MCP_SERVERS" ]; then
            STATUS_LINES="${STATUS_LINES}\u001b[32m    ✓ MCP Servers:\u001b[0m\n"
            while IFS= read -r server; do
                STATUS_LINES="${STATUS_LINES}\u001b[32m       • $server\u001b[0m\n"
            done <<< "$MCP_SERVERS"
        fi
    fi
fi

# Check enabled plugins/skills
if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    PLUGINS=$(cat "$PROJECT_ROOT/.claude/settings.json" | tr -d '\n' | grep -oP '"enabledPlugins"\s*:\s*\{[^}]+\}' | grep -oP '"\K[^"]+(?="\s*:\s*true)')
    if [ -n "$PLUGINS" ]; then
        STATUS_LINES="${STATUS_LINES}\u001b[32m    ✓ Skills & Plugins:\u001b[0m\n"
        while IFS= read -r plugin; do
            # Strip @marketplace suffix for display and folder lookup
            PLUGIN_BASE=$(echo "$plugin" | sed 's/@.*//')
            # Format plugin name nicely (handle "lc" as "LC")
            PLUGIN_NAME=$(echo "$PLUGIN_BASE" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++){if($i=="lc")$i="LC";else sub(/./,toupper(substr($i,1,1)),$i)}}1')
            STATUS_LINES="${STATUS_LINES}\u001b[32m       • $PLUGIN_NAME\u001b[0m\n"

            # Check if this plugin has skills
            PLUGIN_DIR_NAME="$PLUGIN_BASE"
            PLUGIN_SKILLS_DIR="$PROJECT_ROOT/plugins/$PLUGIN_DIR_NAME/skills"
            if [ -d "$PLUGIN_SKILLS_DIR" ]; then
                SKILL_COUNT=$(ls "$PLUGIN_SKILLS_DIR" 2>/dev/null | wc -l)
                if [ $SKILL_COUNT -gt 0 ]; then
                    STATUS_LINES="${STATUS_LINES}\u001b[36m         └─ $SKILL_COUNT specialized skills available\u001b[0m\n"
                fi
            fi
        done <<< "$PLUGINS"
    fi
fi

# Count total tools and capabilities
TOTAL_MCP_SERVERS=$(echo "$MCP_SERVERS" | grep -v '^$' | wc -l 2>/dev/null || echo 0)
TOTAL_PLUGINS=$(echo "$PLUGINS" | grep -v '^$' | wc -l 2>/dev/null || echo 0)

# Create marker file on first time only
if [ "$FIRST_TIME" = true ]; then
    touch "$MARKER_FILE" 2>/dev/null
fi

# Build appropriate message based on first time vs returning
if [ "$FIRST_TIME" = true ]; then
    # First time setup screen
    if [ "$SETUP_REQUIRED" = true ]; then
        MAIN_MESSAGE="\n\u001b[33m╔════════════════════════════════════════════════════════════════════════════════════════════════════╗\u001b[0m\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[33m║  🔐 FIRST TIME SETUP                                                                                ║\u001b[0m\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[33m╚════════════════════════════════════════════════════════════════════════════════════════════════════╝\u001b[0m\n\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[97m  Welcome! Before we get started, let's connect your LimaCharlie environment.\u001b[0m\n\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[36m  Run: /mcp to configure the LimaCharlie MCP server\u001b[0m\n\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[90m  This will enable full access to your LimaCharlie organizations, sensors, and security data.\u001b[0m\n\n"

        # Show current environment state dynamically
        if [ -n "$STATUS_LINES" ]; then
            MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[34m  Your environment:\u001b[0m\n${STATUS_LINES}\n"
        fi
    else
        MAIN_MESSAGE="\n\u001b[32m╔════════════════════════════════════════════════════════════════════════════════════════════════════╗\u001b[0m\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[32m║  ✓ READY TO GO                                                                                     ║\u001b[0m\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[32m╚════════════════════════════════════════════════════════════════════════════════════════════════════╝\u001b[0m\n\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[97m  Your environment is configured and ready!\u001b[0m\n\n"

        # Show current environment state dynamically
        if [ -n "$STATUS_LINES" ]; then
            MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[34m  Your environment:\u001b[0m\n${STATUS_LINES}\n"
        fi

        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[36m  Run /mcp to authenticate with LimaCharlie.\u001b[0m\n"
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[36m  Try: /help or ask me about your security operations!\u001b[0m\n\n"
    fi
else
    # Returning user welcome screen
    MAIN_MESSAGE="\n\u001b[34m  Your environment:\u001b[0m\n${STATUS_LINES}\n"

    # Add any warnings for returning users
    if [ "$SETUP_REQUIRED" = true ]; then
        MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[33m  ⚠️  Setup incomplete: Run /mcp to configure LimaCharlie MCP server\u001b[0m\n\n"
    fi

    MAIN_MESSAGE="${MAIN_MESSAGE}\u001b[36m  Ready to assist with your security operations.\u001b[0m\n\n"
fi

# Output banner
cat <<EOF
{
  "systemMessage": "\n\u001b[34m╔════════════════════════════════════════════════════════════════════════════════════════════════════╗\u001b[0m\n\n\u001b[34m  ██╗     ██╗███╗   ███╗ █████╗  ██████╗██╗  ██╗ █████╗ ██████╗ ██╗     ██╗███████╗\u001b[0m\n\u001b[34m  ██║     ██║████╗ ████║██╔══██╗██╔════╝██║  ██║██╔══██╗██╔══██╗██║     ██║██╔════╝\u001b[0m\n\u001b[34m  ██║     ██║██╔████╔██║███████║██║     ███████║███████║██████╔╝██║     ██║█████╗  \u001b[0m\n\u001b[34m  ██║     ██║██║╚██╔╝██║██╔══██║██║     ██╔══██║██╔══██║██╔══██╗██║     ██║██╔══╝  \u001b[0m\n\u001b[34m  ███████╗██║██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║  ██║██║  ██║███████╗██║███████╗\u001b[0m\n\u001b[34m  ╚══════╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚══════╝\u001b[0m\n\n\u001b[35m  Welcome to the Agentic SecOps Workspace.\u001b[0m\n\n${MAIN_MESSAGE}\u001b[34m╚════════════════════════════════════════════════════════════════════════════════════════════════════╝\u001b[0m\n"
}
EOF

exit 0
