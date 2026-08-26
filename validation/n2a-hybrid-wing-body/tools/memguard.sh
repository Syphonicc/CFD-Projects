#!/bin/bash
# memguard.sh - run a command, kill it if available memory drops too low
# Usage: ./memguard.sh 1500 snappyHexMesh -overwrite
set -u
THRESHOLD_MB=${1:?usage: memguard.sh <threshold_MB> <command> [args...]}
shift
POLL=10
avail_mb() { awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo; }

echo "memguard: threshold ${THRESHOLD_MB} MB | available now $(avail_mb) MB"
echo "memguard: launching: $*"
"$@" &
CHILD=$!
MIN_SEEN=$(avail_mb); PEAK=0
while kill -0 "$CHILD" 2>/dev/null; do
    A=$(avail_mb)
    R=$(ps -o rss= -p "$CHILD" 2>/dev/null | tr -d ' '); R=${R:-0}; R=$((R/1024))
    (( A < MIN_SEEN )) && MIN_SEEN=$A
    (( R > PEAK )) && PEAK=$R
    if (( A < THRESHOLD_MB )); then
        echo ""; echo "memguard: available ${A} MB < ${THRESHOLD_MB} MB - TERMINATING"
        kill -TERM "$CHILD" 2>/dev/null
        for i in $(seq 15); do kill -0 "$CHILD" 2>/dev/null || break; sleep 1; done
        kill -0 "$CHILD" 2>/dev/null && kill -KILL "$CHILD" 2>/dev/null
        wait "$CHILD" 2>/dev/null
        echo "memguard: killed. peak RSS ${PEAK} MB"
        exit 137
    fi
    printf '\rmemguard: RSS %6d MB | avail %6d MB | min seen %6d MB   ' "$R" "$A" "$MIN_SEEN"
    sleep "$POLL"
done
wait "$CHILD" 2>/dev/null; RC=$?
echo ""; echo "memguard: finished, exit ${RC} | peak RSS ${PEAK} MB | min available ${MIN_SEEN} MB"
exit "$RC"
