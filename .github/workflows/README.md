Video Pillar Crop — Repository-ready package
===========================================

Files included:
- .github/workflows/build-windows-exe.yml  -> GitHub Actions workflow to build video_pillar_crop.exe on Windows runners
- video_pillar_crop.py                     -> Pillar detection script
- pillar_detect.bat                        -> Drag & drop launcher (uses EXE if present, otherwise python)
- build_exe.ps1                            -> Local PowerShell builder using PyInstaller
- README.md                                -> (this file)
- LICENSE                                  -> MIT license

How to use:
1. Place these files in your GitHub repository root.
2. Commit and push to the 'main' branch.
3. On GitHub, go to Actions -> Build Windows EXE -> Run workflow. Optionally provide ffmpeg_url to bundle ffmpeg.exe.
   Recommended URL: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
4. Download the artifact (video_pillar_crop-windows) when the run finishes.

Notes:
- The workflow builds the EXE but does not automatically include ffmpeg unless you supply an ffmpeg_url that points to a ZIP/7z containing ffmpeg.exe.
- If you prefer local builds, use build_exe.ps1 on a Windows machine to create the EXE locally.
