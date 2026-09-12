# Capability harness moved to the CLI

The canonical first-level LimaCharlie capability catalog, procedures, references
and workflow policy now live in
[python-limacharlie](https://github.com/refractionPOINT/python-limacharlie/tree/master/limacharlie/capability_data).
Use `limacharlie help capability` to discover them.

AI Sessions pins and installs that CLI directly. Add new platform capabilities
there; no separate lc-ai harness package or domain MCP registration is required.
The previous MCP capability package remains available at the `v1.0.0` tag for
older runner images. Other skills and agent/team definitions in this repository
remain available to their existing consumers.
