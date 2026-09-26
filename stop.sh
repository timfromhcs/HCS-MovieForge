#!/usr/bin/env bash
# HCS MovieForge - Linux Stop Script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/runtime"
PID_FILE="${RUNTIME_DIR}/supervisor.pid"
STATE_FILE="${RUNTIME_DIR}/service-state.json"

echo "========================================"
echo "  HCS MovieForge - Stopping Services    "
echo "========================================"

TRACKED_PIDS=()

if [[ -f "${STATE_FILE}" ]]; then
    PIDS_FROM_STATE=$(python3 -c "import json, sys; d=json.load(open('${STATE_FILE}')); print(' '.join(map(str, d.get('pids', []))))" 2>/dev/null || true)
    for p in ${PIDS_FROM_STATE}; do
        TRACKED_PIDS+=("${p}")
    done
fi

if [[ -f "${PID_FILE}" ]]; then
    SUP_PID=$(cat "${PID_FILE}")
    TRACKED_PIDS+=("${SUP_PID}")
fi

if [ ${#TRACKED_PIDS[@]} -eq 0 ]; then
    echo "[MovieForge] No running supervisor or worker instances found."
    exit 0
fi

echo "[MovieForge] Stopping tracked processes: ${TRACKED_PIDS[*]}"

# Send SIGTERM
for p in "${TRACKED_PIDS[@]}"; do
    if kill -0 "${p}" 2>/dev/null; then
        echo "[MovieForge] Requesting graceful termination for PID ${p}..."
        kill -TERM "${p}" 2>/dev/null || true
    fi
done

# Wait up to 5 seconds
for i in {1..5}; do
    ANY_ALIVE=0
    for p in "${TRACKED_PIDS[@]}"; do
        if kill -0 "${p}" 2>/dev/null; then
            ANY_ALIVE=1
            break
        fi
    done
    if [ ${ANY_ALIVE} -eq 0 ]; then
        break
    fi
    sleep 1
done

# Force kill remaining
for p in "${TRACKED_PIDS[@]}"; do
    if kill -0 "${p}" 2>/dev/null; then
        echo "[MovieForge] Force killing PID ${p}..."
        kill -KILL "${p}" 2>/dev/null || true
    fi
done

rm -f "${PID_FILE}" "${STATE_FILE}"
echo "[MovieForge] All MovieForge processes stopped cleanly."
