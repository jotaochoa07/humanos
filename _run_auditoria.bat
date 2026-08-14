@echo off
REM Runner de la auditoria de alineacion de marca.
REM Lo invoca el Programador de tareas. Solo lectura sobre los agentes.
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" auditar_alineacion.py > "%~dp0_LAB\_arranque_auditoria.log" 2>&1
exit /b %ERRORLEVEL%
