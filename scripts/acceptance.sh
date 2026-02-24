#!/usr/bin/env bash
set -euo pipefail

echo "Running backend tests..."
pytest -q

echo "Running frontend tests..."
(
  cd frontend
  bun run test
)

echo "Acceptance checks passed."
