@echo off
echo === Tetra-cube D&D Chinese Localization ===
echo Starting local server at http://localhost:8080
echo Press Ctrl+C to stop
echo.
start http://localhost:8080
python -m http.server 8080
