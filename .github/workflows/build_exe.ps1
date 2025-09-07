# build_exe.ps1
<#
Automated builder for video_pillar_crop.exe using PyInstaller.
Run this script in Windows PowerShell.
#>
Set-StrictMode -Version Latest
Write-Host "Starting build for video_pillar_crop.exe"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $here "build_venv"
$python = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"
if (-Not (Test-Path $python)) {
    Write-Host "Creating virtualenv..."
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtualenv. Ensure Python is installed and on PATH."
        exit 1
    }
}
Write-Host "Installing wheel, pyinstaller, pillow..."
& $pip install --upgrade pip wheel pyinstaller pillow
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed."
    exit 2
}
Write-Host "Running PyInstaller..."
$spec_args = @("--onefile","--console","--name","video_pillar_crop","video_pillar_crop.py")
& $python -m PyInstaller $spec_args
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed."
    exit 3
}
$distExe = Join-Path $here "dist\video_pillar_crop.exe"
$outdir = Join-Path $here "dist_windows"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
Copy-Item $distExe $outdir
Write-Host "Build complete. EXE located at: $outdir\video_pillar_crop.exe"
Write-Host "IMPORTANT: Ensure ffmpeg.exe is available on PATH or place ffmpeg.exe next to the EXE."
