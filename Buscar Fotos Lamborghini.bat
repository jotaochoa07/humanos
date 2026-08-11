@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Archivo en FOTO (guion locutado)
echo  ---------------------------------------------------------------
echo  Busca solo los 8 planos que el storyboard nuevo (sobre tu guion
echo  grabado) marco como foto_archivo. No busca los de motion graphic
echo  ni los de recreacion IA - esos no se buscan en un archivo.
echo.

REM --sin-monetizacion: el canal aun no esta monetizado, asi que las NC bajan
REM de rojo a ambar. Quitar el dia que se monetice.
"%PY%" archivo_historico.py --episodio "%EP%" --imagen --limite 15 --sin-monetizacion

echo.
echo  ---------------------------------------------------------------

set "HOJA=%~dp0%EP%\01_RESEARCH\archivo\hoja_de_contactos_imagen.html"
if exist "%HOJA%" (
  echo  Abriendo la hoja de fotos...
  start "" "%HOJA%"
) else (
  echo  No se genero la hoja. Revisa los errores de arriba.
)

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
