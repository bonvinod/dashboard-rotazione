@echo off
echo ============================================
echo   AGGIORNAMENTO DASHBOARD ROTAZIONE AAs
echo ============================================
echo.
echo 1. Refresh Power Query in Excel...
echo 2. Salvataggio snapshot giornaliero...
echo.
python "%~dp0refresh_excel.py"
echo.
echo ============================================
echo   COMPLETATO!
echo ============================================
pause
