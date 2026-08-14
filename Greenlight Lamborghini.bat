@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  MR. YOU - Protocolo de Greenlight
echo  Episodio: EP0004 Ferruccio Lamborghini
echo.
python mr_you.py --episodio EP0004_Ferruccio_Lamborghini --expresion STORY --tier A
echo.
echo  ---------------------------------------------------------------
echo  Pulsa una tecla para cerrar.
pause >nul
