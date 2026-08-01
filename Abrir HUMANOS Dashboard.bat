@echo off
setlocal
title HUMANOS - Editorial Dashboard
cd /d "C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos"
set PORT=3100

echo.
echo   HUMANOS - Panel Editorial
echo   ---------------------------------------
echo   Iniciando servidor en el puerto %PORT%...
echo.

REM El servidor arranca en su propia ventana para que sus logs queden visibles.
start "HUMANOS Server" cmd /k "npm run editorial"

REM Esperar a que el puerto responda ANTES de abrir el navegador.
REM Sin esta espera el navegador llegaba primero y fallaba al cargar los datos.
set /a INTENTOS=0
:esperar
set /a INTENTOS+=1
if %INTENTOS% GTR 40 goto sinservidor
powershell -NoProfile -Command "try { $c = New-Object Net.Sockets.TcpClient('127.0.0.1', %PORT%); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto esperar
)

echo   Servidor listo. Abriendo el panel...
start "" "http://127.0.0.1:%PORT%/"
echo.
echo   Panel abierto en http://127.0.0.1:%PORT%/
echo   Para apagarlo, cerra la ventana "HUMANOS Server".
echo.
timeout /t 3 /nobreak >nul
exit /b 0

:sinservidor
echo.
echo   [ERROR] El servidor no respondio en 40 segundos.
echo.
echo   Revisa la ventana "HUMANOS Server" para ver el error.
echo   Causas habituales:
echo     - Falta ejecutar: npm install
echo     - El puerto %PORT% ya esta ocupado por otro proceso
echo     - Node.js no esta instalado o no esta en el PATH
echo.
pause
exit /b 1
