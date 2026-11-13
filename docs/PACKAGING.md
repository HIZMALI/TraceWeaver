# Packaging and offline distribution

The source checkout builds its own console. A built TraceWeaver wheel includes static assets,
packaged synthetic fixtures, canonical LICENSE/NOTICE and frontend third-party notices. It contains
no user database, model weights or recording. Supply the published judge bundle separately.

## Build and independently check

After installing the pinned development dependencies and running the frontend build, select new
output directories. These tools refuse implicit overwrite. From Windows/PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/build_judge_wheel.py --output .verification/package/wheel
.\.venv\Scripts\python.exe scripts/verify_release.py --wheel .verification/package/wheel/traceweaver-0.1.0-py3-none-any.whl --output .verification/package/check --source-check
```

On Linux replace the Python path with `.venv/bin/python`. The verifier requires the project's
Playwright Chromium test client; install it as described in the root README's test commands.
It installs the wheel non-editably outside the checkout, copies the intact synthetic judge bundle,
launches a Node-free server and checks actual browser proof. Missing/corrupt/locked owned copies
must return errors without fallback. `--source-check` additionally builds a fresh source setup.

An ordinary installed-wheel launch is:

```text
python -m traceweaver.judge --bundle /path/to/intact/judge-demo --port 8000
```

The server is local at 127.0.0.1. Node is a build/test dependency, not a wheel runtime dependency.
Native runtime dependency wheels must match the actual interpreter/OS/architecture.

## Create a Windows offline export

The exporter downloads compatible binary runtime wheels during preparation. It then copies only
allowlisted judge data, guides, licenses/notices, constraints and the existing offline launcher:

```powershell
.\.venv\Scripts\python.exe scripts/stage_release.py --wheel .verification/package/wheel/traceweaver-0.1.0-py3-none-any.whl --output .verification/package/export
```

The new export's SHA256.json records platform, Python version and exact file digests. It is local
output, not automatically published or attached to GitHub. No existing export or store is replaced.
The packaging guide is exported under the compatibility filename PUBLIC_READINESS.md.
The source-oriented QUICK_START.md refers back to the repository; for a standalone export use:

```powershell
.\RUN_JUDGE.ps1 -CheckOnly
.\RUN_JUDGE.ps1 -Port 8000
```

The launcher verifies exported bytes before creating a folder-local environment and installing
included wheels with `--no-index`. Existing compatible Python must already be installed. It never
seeds or repairs a store. A checksum/platform/storage error is a real error; preserve the export.
Ctrl+C stops the foreground server. Export creation is portable; RUN_JUDGE.ps1 targets Windows.

## License and safety boundaries

Apache-2.0 applies to eligible original project material. Root LICENSE/NOTICE and required upstream
notices accompany new exports; installed dependencies retain their own notices. Review dependency,
model and media rights before separately redistributing them. No model, encoder binary, private
audit logs, environment, source recording or user store is exported. Digests establish byte equality,
not source authenticity. The citation firewall does not prove external truth or causality.

Source tests run in CI on Windows/Ubuntu Python 3.11; the installed-wheel browser flow runs on
Ubuntu, and local Windows/Python 3.14 installation was exercised. This does not verify every Python
version or make platform-specific offline wheels portable. See the repository's Actions for the
exact tested commit. No reliable live-browser AI, production accuracy or hosted service is promised.
