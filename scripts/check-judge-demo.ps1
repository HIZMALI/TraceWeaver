Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Project .venv is missing. Follow README setup first.' }
& $projectPython -m traceweaver.judge --bundle (Join-Path $repoRoot 'examples/judge-demo') --check
exit $LASTEXITCODE
