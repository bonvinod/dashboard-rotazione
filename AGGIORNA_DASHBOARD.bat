@echo off
echo ============================================
echo   AGGIORNAMENTO DASHBOARD ROTAZIONE AAs
echo ============================================
echo.
echo Salvataggio snapshot di oggi...
python "%~dp0salva_snapshot.py"
echo.
echo Push su GitHub...
cd /d "%~dp0"
git add data\
git commit -m "Snapshot %date:~6,4%-%date:~3,2%-%date:~0,2%"
git push
echo.
echo ============================================
echo   DASHBOARD AGGIORNATA!
echo ============================================
echo I tuoi colleghi vedranno i dati aggiornati.
pause
