@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Trayendo metricas reales del canal desde la YouTube Analytics API
echo  (el panel tiene que estar corriendo)
echo.
python importar_youtube_api.py
echo.
echo  ---------------------------------------------------------------
echo  Pulsa una tecla para cerrar.
pause >nul
