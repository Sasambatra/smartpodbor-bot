#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
if [[ ! -f .env ]]; then
    (umask 077; cp .env.example .env)
fi
printf '%s\n' 'Готово. Добавьте BOT_TOKEN в .env и выполните ./run.sh. Демо: ./run.sh --demo'
