@echo off
python "%~dp0do_refresh.py"
python "%~dp0salva_snapshot.py"
cd /d "%~dp0"
git add data\
git commit -m "Snapshot %date:~6,4%-%date:~3,2%-%date:~0,2%"
git push
