param(
    [ValidateRange(1024,65535)][int]$Port = 8000,
    [switch]$Build
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create .venv with Python 3.11+ and install requirements-dev.lock and the editable project as documented in README.'
}
if ($Build) {
    if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        throw 'Node 24+ and npm are needed only for --Build. Install prerequisites yourself; this script never installs system tools.'
    }
    $nodeVersion = & node --version
    if ([int]($nodeVersion.TrimStart('v').Split('.')[0]) -lt 24) { throw 'Build requires Node 24+.' }
    & npm.cmd --prefix (Join-Path $repoRoot 'web') ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
    & npm.cmd --prefix (Join-Path $repoRoot 'web') run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
}
& $projectPython -m traceweaver.judge --bundle (Join-Path $repoRoot 'examples/judge-demo') --port $Port
exit $LASTEXITCODE
