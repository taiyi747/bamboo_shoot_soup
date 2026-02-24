#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

Write-Host "Running backend tests..."
pytest -q

Write-Host "Running frontend tests..."
Push-Location frontend
try {
  bun run test
}
finally {
  Pop-Location
}

Write-Host "Acceptance checks passed."
