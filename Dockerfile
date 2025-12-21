# LimaCharlie Claude Code Container
# Pre-configured environment with lc-essentials plugin for LimaCharlie operations

FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    vim \
    nano \
    openssh-client \
    ca-certificates \
    gnupg \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install LimaCharlie Python SDK and Jinja2 (for render-html.py)
RUN pip3 install --break-system-packages limacharlie jinja2

# Create lc user with sudo access
RUN useradd -m -s /bin/bash lc \
    && echo "lc ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER lc
WORKDIR /home/lc

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

# Pre-configure Claude settings to use GitHub-based marketplace
RUN mkdir -p /home/lc/.claude && \
    echo '{\
  "extraKnownMarketplaces": {\
    "limacharlie-marketplace": {\
      "source": {\
        "source": "github",\
        "repo": "refractionPOINT/lc-ai",\
        "path": "plugins"\
      }\
    }\
  },\
  "enabledPlugins": {\
    "lc-essentials@limacharlie-marketplace": true\
  }\
}' > /home/lc/.claude/settings.json

# Copy entrypoint script
COPY --chown=lc:lc entrypoint.sh /home/lc/entrypoint.sh
RUN chmod +x /home/lc/entrypoint.sh

ENTRYPOINT ["/home/lc/entrypoint.sh"]
