@echo off
:: One-click wrapper for video_pillar_crop.py / EXE
setlocal
set HERE=%~dp0
if exist "%HERE%video_pillar_crop.exe" (
    "%HERE%video_pillar_crop.exe" "%~1" %*
    exit /b
)
:: fallback to python script if exe not present
python "%HERE%video_pillar_crop.py" "%~1" %*
pause
