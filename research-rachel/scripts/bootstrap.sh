#!/usr/bin/env sh
set -eu

REPOSITORY_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPOSITORY_ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e './apps/api[dev]'
npm install

echo 'Setup complete. Activate with: source .venv/bin/activate'
echo 'Then run both apps with: npm run dev'
