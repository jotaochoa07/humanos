@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  HUMANOS - Prueba de vida de los agentes
echo.
python verificar_agentes.py
echo.
echo  ---------------------------------------------------------------
echo  Pulsa una tecla para cerrar.
pause >nul
