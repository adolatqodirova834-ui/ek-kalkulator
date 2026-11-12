@echo off
rem EK kalkulyatori - Windows launcher. First run installs the libraries (needs internet).
setlocal
chcp 65001 >nul
title EK kalkulyatori
cd /d "%~dp0"

set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo XATO: Python 3.11 yoki undan yangi versiya topilmadi.
  echo O'rnatish: https://www.python.org/downloads/
  echo O'rnatishda "Add python.exe to PATH" belgisini yoqing.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Birinchi ishga tushirish: virtual muhit yaratilmoqda...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)
if not exist ".venv\.installed" (
  echo Kutubxonalar o'rnatilmoqda - bir necha daqiqa, internet kerak...
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
  if errorlevel 1 goto :fail
  echo ok> ".venv\.installed"
)

".venv\Scripts\python.exe" run_app.py
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo XATO: ishga tushirib bo'lmadi. Yuqoridagi xabarlarni tekshiring.
pause
exit /b 1
