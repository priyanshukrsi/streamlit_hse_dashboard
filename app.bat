@echo off
call "C:\Users\priya\miniconda3\Scripts\activate.bat"
call conda activate base
cd /d "C:\Users\priya\Desktop\github_projects\Streamlit HSE Dashboard\app.py"
streamlit run app.py
pause