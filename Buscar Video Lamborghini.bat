@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Archivo en VIDEO
echo  ---------------------------------------------------------------
echo  Busca METRAJE, no fotos, y solo para los planos que Moore marco
echo  como video_archivo.
echo.
echo  Fuentes: Istituto Luce (via Europeana), Internet Archive,
echo  el fondo filmico de la Library of Congress y Wikimedia.
echo.
echo  Los catalogos que no tienen API - el Luce por su cuenta, British
echo  Pathe, AP Archive - salen como enlaces ya compuestos al final de
echo  la hoja, para mirarlos a mano. Ese material casi nunca es gratis:
echo  la hoja lo dice, no lo disimula.
echo.

REM --sin-monetizacion: el canal aun no esta monetizado, asi que las NC bajan
REM de rojo a ambar. Quitar el dia que se monetice.
"%PY%" archivo_historico.py --episodio "%EP%" --video --limite 15 --sin-monetizacion

echo.
echo  ---------------------------------------------------------------

set "HOJA=%~dp0%EP%\01_RESEARCH\archivo\hoja_de_contactos_video.html"
if exist "%HOJA%" (
  echo  Abriendo la hoja de video...
  start "" "%HOJA%"
) else (
  echo  No se genero la hoja. Revisa los errores de arriba.
  echo  Si dice que no encuentra los gaps, corre antes
  echo  "Cerrar Episodio Lamborghini.bat" para que Moore los genere.
)

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
