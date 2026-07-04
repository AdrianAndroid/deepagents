#!/usr/bin/env bash
# Serve the site locally and open it in the default browser.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}/"

# If the port is busy, bump until we find a free one (max 10 tries).
for _ in $(seq 1 10); do
  if ! lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  echo "Port ${PORT} busy, trying $((PORT + 1))..."
  PORT=$((PORT + 1))
  URL="http://127.0.0.1:${PORT}/"
done

echo "Serving ${DIR} at ${URL}"
echo "Press Ctrl+C to stop."

# Open the browser shortly after the server starts.
( sleep 1 && (command -v open >/dev/null && open "${URL}" || \
              command -v xdg-open >/dev/null && xdg-open "${URL}" || \
              echo "Open ${URL} in your browser") ) &

cd "${DIR}"
exec python3 -m http.server "${PORT}" --bind 127.0.0.1
