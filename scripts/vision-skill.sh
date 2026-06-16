#!/usr/bin/env bash
# Auto-detect a working Python 3 interpreter and run vision.py.
# Handles the Windows Store "python3" stub (exits 49) gracefully.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_python() {
    for cmd in python python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PY="$(detect_python)" || {
    echo "ERROR: No working Python 3.8+ found. Install Python from https://python.org" >&2
    exit 1
}

exec "$PY" "$SCRIPT_DIR/vision.py" "$@"
