@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"
set "LISTA=%EP%\01_RESEARCH\archivo\seleccion_jota.txt"

echo.
echo  HUMANOS - Bajar la seleccion de archivo
echo  ---------------------------------------------------------------
echo  Baja lo que marcaste en la hoja de contactos (imagen o video), lo
echo  nombra con el estandar del episodio y lo inscribe con su licencia.
echo.
echo  Destino: %EP%\04_IMAGES (fotos) o %EP%\05_VIDEO (metraje), segun
echo  el tipo de cada archivo.
echo.
echo  Pega en seleccion_jota.txt tanto lo que marcaste en la hoja de
echo  fotos como en la de video: este mismo script separa cada uno a
echo  su carpeta.
echo.

"%PY%" registrar_assets.py --episodio "%EP%" --lista "%LISTA%" --sin-monetizacion

echo.
echo  ---------------------------------------------------------------
echo  Gate de derechos:
echo.
"%PY%" derechos.py --episodio "%EP%"

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
