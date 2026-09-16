#!/usr/bin/env bash
set -euo pipefail
eval_dir="$(cd "$(dirname "$0")/.." && pwd)"
tool_dir="$eval_dir/.tools"
if [ ! -x "$tool_dir/bin/uv" ]; then
  python3 -m venv "$tool_dir"
  "$tool_dir/bin/python" -m pip install 'uv==0.8.22'
fi
exec "$tool_dir/bin/uv" sync --locked --extra test --project "$eval_dir"
