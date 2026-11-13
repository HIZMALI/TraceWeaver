param([int]$Port = 8000, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Use a port between 1024 and 65535.' }
Push-Location $PSScriptRoot
try {
    # Verify exported bytes before installing or opening the synthetic graph. No native writer.
    $verify = @'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
manifest=json.loads((root/'SHA256.json').read_text(encoding='utf8'))
for name, expected in manifest['files'].items():
    path=(root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
        raise SystemExit('Release artifact unavailable')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise SystemExit('Release checksum mismatch; preserve the bundle and obtain an intact copy')
print('Exported artifact checksums match; this does not authenticate source truth.')
'@
    & python -c $verify $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { throw 'Release verification failed.' }
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Project environment creation failed.' }
    }
    $python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    & $python -m pip --disable-pip-version-check install --no-index --find-links wheels -c requirements-dev.lock traceweaver==0.1.0
    if ($LASTEXITCODE -ne 0) { throw 'Offline package installation failed; inspect the platform prerequisites.' }
    & $python -m traceweaver.judge --bundle judge-demo --check
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic bundle verification failed.' }
    if (-not $CheckOnly) {
        & $python -m traceweaver.judge --bundle judge-demo --port $Port
        if ($LASTEXITCODE -ne 0) { throw 'Judge server exited with an error.' }
    }
} finally { Pop-Location }
