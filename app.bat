@echo off
call "path to activate.bat"
call conda activate base
cd /d "path to app.py"
streamlit run app.py
pause