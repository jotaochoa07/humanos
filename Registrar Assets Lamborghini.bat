@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Registrar procedencia de los assets
echo  ---------------------------------------------------------------
echo  Te va a preguntar el origen de cada imagen sin registrar.
echo.
echo    - Si la generaste vos o con IA  ..... escribi:  propio
echo    - Si la bajaste de algun sitio  ..... pega la URL o la licencia
echo    - Si no te acordas              ..... Enter (queda pendiente)
echo.
echo  ---------------------------------------------------------------
echo.

"%PY%" registrar_assets.py --episodio "%EP%" --revisar

echo.
echo  ---------------------------------------------------------------
echo  Ahora el gate de derechos:
echo.
"%PY%" derechos.py --episodio "%EP%"

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
