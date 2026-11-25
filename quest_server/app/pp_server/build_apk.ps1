# Bulletproof APK Build Runner
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& python "build_apk.py"
if ($LASTEXITCODE -ne 0) {
    throw "build_apk.py execution failed with exit code $LASTEXITCODE"
}
