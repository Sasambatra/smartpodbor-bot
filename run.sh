#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Сначала выполните ./setup.sh'
    exit 1
fi
exec .venv/bin/python -m smartphone_bot "$@"
