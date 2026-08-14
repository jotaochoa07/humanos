@echo off
REM Runner de la captura diaria. Lo invoca el Programador de tareas de Windows.
REM No lo ejecutes a mano: para eso esta "Actualizar Metricas Canal.bat".
REM
REM Dos correcciones del 2026-08-01:
REM  1) La salida NO se redirige a capturar_canal.log. El script Python ya
REM     escribe ese archivo por su cuenta, y si cmd lo tiene abierto con >>
REM     Windows le niega el permiso al script (PermissionError 13).
REM     Este .bat escribe en un archivo distinto: solo para atrapar errores
REM     que ocurren ANTES de que Python arranque (ej. interprete no encontrado).
REM  2) Se usa la ruta completa del interprete. El Programador de tareas arranca
REM     con un PATH reducido y 'python' a secas no existe ahi.

cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" capturar_canal.py > "%~dp0_LAB\_arranque_captura.log" 2>&1
exit /b %ERRORLEVEL%
