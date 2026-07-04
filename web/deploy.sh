#!/usr/bin/env bash
# Sync local site to 1panel static site on 8.152.204.58
set -euo pipefail

LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)/"
REMOTE="root@8.152.204.58:/opt/1panel/www/sites/8.152.204.58/index/"
SSH_PORT="${SSH_PORT:-22}"

RSYNC_OPTS=(-avz --delete --exclude 'deploy.sh' --exclude '.DS_Store' --exclude '.git')

if [[ "${1:-}" == "--dry-run" ]]; then
  RSYNC_OPTS+=(--dry-run)
  echo "[dry-run] no files will be changed on the server"
fi

rsync "${RSYNC_OPTS[@]}" -e "ssh -p ${SSH_PORT}" "${LOCAL_DIR}" "${REMOTE}"
echo "Deployed to ${REMOTE}"
