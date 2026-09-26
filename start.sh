#!/usr/bin/env bash
# HCS MovieForge - Linux Start Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/runtime"
PID_FILE="${RUNTIME_DIR}/supervisor.pid"

mkdir -p "${RUNTIME_DIR}"

if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID="$(cat "${PID_FILE}")"
    if kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "[MovieForge] Supervisor already running with PID ${EXISTING_PID}"
        exit 0
    fi
fi

echo "========================================"
echo "  HCS MovieForge - Starting Supervisor  "
echo "========================================"

export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

python3 -m engine.supervisor.main "$@"
