@echo off
REM Runner de la revision semanal de Mr. You. Lo invoca el Programador de tareas.
REM Ver notas en _run_captura.bat sobre por que no se redirige al log del script
REM y por que se usa la ruta completa del interprete.

cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" direccion_semanal.py > "%~dp0_LAB\direccion_semanal.log" 2>&1
exit /b %ERRORLEVEL%
