#!/usr/bin/env bash
# Starts all six drivers from D1, proves each D1 routing key, then runs the
# random dispatcher for 2 minutes. Output goes to stream/logs/.
#
# Usage (from repo root):  bash stream/run_demo.sh [seconds]
set -u
DURATION="${1:-120}"
cd "$(dirname "$0")"
mkdir -p logs
rm -f logs/*.log

declare -A PATTERNS=(
  [Ravi]="bangalore.koramangala.*"
  [Priya]="bangalore.indiranagar.*"
  [Arjun]="bangalore.*.ride"
  [Meena]="bangalore.*.food"
  [Karthik]="chennai.tnagar.food"
  [Control]="bangalore.#"
)

PIDS=()
for NAME in "${!PATTERNS[@]}"; do
  python3 -u driver.py "$NAME" "${PATTERNS[$NAME]}" > "logs/${NAME}.log" 2>&1 &
  PIDS+=($!)
done
sleep 3   # let every queue bind before publishing

echo "=== Part 1: one message for each D1 routing key ===" | tee logs/dispatcher.log
for KEY in bangalore.koramangala.food bangalore.indiranagar.ride bangalore.whitefield.ride \
           chennai.tnagar.food chennai.whitefield.ride bangalore.koramangala; do
  python3 -u dispatcher.py --key "$KEY" | tee -a logs/dispatcher.log
  sleep 1
done

echo "=== Part 2: random dispatcher for ${DURATION}s (every 10th message is bad) ===" | tee -a logs/dispatcher.log
python3 -u dispatcher.py --duration "$DURATION" | tee -a logs/dispatcher.log
sleep 2

for P in "${PIDS[@]}"; do kill -TERM "$P" 2>/dev/null; done
sleep 2
echo "Logs written to stream/logs/"
