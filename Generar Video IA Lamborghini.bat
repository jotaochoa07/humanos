@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Kling (ultimo recurso)
echo  ---------------------------------------------------------------
echo  Esto NO es el plan A. Solo genera los planos que Moore marco como
echo  recreacion: los que no existen en ningun archivo del mundo, como
echo  la conversacion a puerta cerrada con Enzo.
echo.
echo  Antes de correrlo conviene haber buscado archivo real con
echo  "Buscar Video Lamborghini.bat".
echo.
echo  ---------------------------------------------------------------
echo  Paso 1 de 3: comprobando la clave de KIE y que ruta responde.
echo.
"%PY%" kling_client.py --descubrir

echo.
echo  ---------------------------------------------------------------
echo  Paso 2 de 3: que se generaria (sin gastar creditos todavia).
echo.
"%PY%" kling_client.py --episodio "%EP%" --gaps-ia --simular

echo.
echo  ---------------------------------------------------------------
echo  Paso 3 de 3: generar de verdad. Esto SI gasta creditos.
echo.
echo  Cierra esta ventana ahora si no quieres seguir.
pause

"%PY%" kling_client.py --episodio "%EP%" --gaps-ia --segundos 5

echo.
echo  ---------------------------------------------------------------
echo  Lo generado queda en %EP%\05_VIDEO y anotado en el registro de
echo  assets como material propio, asi que el gate de derechos lo pasa.
echo.
echo  Pulsa una tecla para cerrar.
pause >nul
