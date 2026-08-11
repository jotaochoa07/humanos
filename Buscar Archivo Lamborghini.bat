@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Archivo historico
echo  ---------------------------------------------------------------
echo  Paso 1 de 2: probando que fuentes responden desde tu red.
echo.
"%PY%" archivo_historico.py --test
echo.
echo  ---------------------------------------------------------------
echo  Paso 2 de 2: buscando sobre los gaps de Moore del EP0004.
echo.
REM --sin-monetizacion: el canal aun no esta monetizado, asi que las licencias
REM NC bajan de rojo a ambar. Quitar esta bandera el dia que se monetice.
"%PY%" archivo_historico.py --episodio "%EP%" --limite 15 --sin-monetizacion
echo.
echo  ---------------------------------------------------------------

set "HOJA=%~dp0%EP%\01_RESEARCH\archivo\hoja_de_contactos.html"
if exist "%HOJA%" (
  echo  Abriendo la hoja de contactos en el navegador...
  start "" "%HOJA%"
) else (
  echo  No se genero la hoja. Revisa los errores de arriba.
)

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
