@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=C:\JotaOS\data\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\Jota Ochoa\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

set "EP=personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini"

echo.
echo  HUMANOS - Cierre del EP0004 Lamborghini
echo  ---------------------------------------------------------------
echo  Pasa el guion que GRABASTE por todo el pipeline, en orden:
echo.
echo    1. Borges    investiga el Acto 4 (Turin 1963), que nunca paso
echo                 por investigacion.
echo    2. Claims    saca del guion lo que aun no esta auditado.
echo    3. Veritas   audita esas afirmaciones nuevas.
echo    4. Veritas   audita el guion entero.
echo    5. Moore     rehace el storyboard sobre la locucion real y los
echo                 468 segundos reales del wav.
echo    6. Talese    compara tu version con la de Claude.
echo    7. Informe   una sola pagina HTML con todo.
echo.
echo  Tarda unos minutos y gasta creditos de OpenRouter.
echo  Si algo falla, retoma con --desde N sin repetir lo hecho.
echo.
pause

"%PY%" "claude_improvement\_run_pipeline_ep0004.py" %*

echo.
echo  ---------------------------------------------------------------

set "INF=%~dp0%EP%\INFORME_CIERRE_EP0004.html"
if exist "%INF%" (
  echo  Abriendo el informe...
  start "" "%INF%"
) else (
  echo  No se genero el informe. Mira los errores de arriba.
)

echo.
echo  Pulsa una tecla para cerrar.
pause >nul
