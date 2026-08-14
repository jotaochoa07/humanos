@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ================================================================
echo   Programar la revision semanal de canal (Mr. You)
echo  ================================================================
echo.
echo   Crea la tarea "HUMANOS - Direccion semanal" en el Programador
echo   de Windows. Corre los LUNES a las 09:00.
echo.
echo   Lee la serie historica que dejo la captura diaria, compara la
echo   semana contra la anterior y escribe una nota en:
echo      _LAB\direccion_canal\
echo.
echo   AVISO: esta tarea SI usa modelo (OpenRouter). Cuesta unos
echo   centavos por corrida. La captura diaria no cuesta nada.
echo.
pause

REM Ver nota en 'Programar Captura Diaria.bat': /TR no soporta && ni >>.
schtasks /Create ^
  /TN "HUMANOS - Direccion semanal" ^
  /TR "\"%~dp0_run_direccion.bat\"" ^
  /SC WEEKLY ^
  /D MON ^
  /ST 09:00 ^
  /F

echo.
if %ERRORLEVEL%==0 (
  echo   TAREA CREADA.
  echo.
  echo   Probarla ahora:  schtasks /Run /TN "HUMANOS - Direccion semanal"
  echo   Borrarla:        schtasks /Delete /TN "HUMANOS - Direccion semanal" /F
  echo.
  echo   OJO: necesita al menos DOS dias capturados para poder comparar.
  echo   Si corre hoy, te va a decir que todavia no tiene con que comparar.
  echo   Eso es correcto, no es un error.
) else (
  echo   No se pudo crear. Proba abriendo este .bat como Administrador.
)
echo.
pause
