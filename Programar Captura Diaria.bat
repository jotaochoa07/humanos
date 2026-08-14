@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ================================================================
echo   Programar la captura diaria de metricas del canal
echo  ================================================================
echo.
echo   Va a crear una tarea en el Programador de Windows llamada
echo   "HUMANOS - Captura canal", que corre TODOS LOS DIAS a las 08:00.
echo.
echo   No necesita el panel abierto ni una sesion de Claude.
echo   Habla directo con Google usando el token ya guardado.
echo.
pause

REM schtasks NO acepta && ni redirecciones dentro de /TR: rompe el parseo con
REM 'Argumento u opcion no valido - "&&"'. Por eso /TR apunta a un runner .bat
REM que hace el cd, la ejecucion y el log por su cuenta.
schtasks /Create ^
  /TN "HUMANOS - Captura canal" ^
  /TR "\"%~dp0_run_captura.bat\"" ^
  /SC DAILY ^
  /ST 08:00 ^
  /F

echo.
if %ERRORLEVEL%==0 (
  echo   TAREA CREADA.
  echo.
  echo   Para verla:      schtasks /Query /TN "HUMANOS - Captura canal"
  echo   Para probarla:   schtasks /Run   /TN "HUMANOS - Captura canal"
  echo   Para borrarla:   schtasks /Delete /TN "HUMANOS - Captura canal" /F
  echo.
  echo   El registro queda en:  _LAB\capturar_canal.log
) else (
  echo   No se pudo crear. Proba abriendo este .bat como Administrador.
)
echo.
pause
