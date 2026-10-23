@echo off
cd /d "%~dp0"
echo Installing... please wait
python -m pip install -r requirements.txt
echo Starting app. Keep this window open.
python -m streamlit run app.py
pause
