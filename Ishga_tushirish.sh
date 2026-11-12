#!/usr/bin/env bash
# EK kalkulyatori - Linux / macOS launcher. First run installs the libraries (needs internet).
set -e
cd "$(dirname "$0")"

PY=""
for c in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "XATO: Python 3.11 yoki undan yangi versiya topilmadi."
  echo "O'rnatish: https://www.python.org/downloads/"
  read -r -p "Yopish uchun Enter bosing..." _
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Birinchi ishga tushirish: virtual muhit yaratilmoqda..."
  "$PY" -m venv .venv
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  echo "Kutubxonalar o'rnatilmoqda (bir necha daqiqa, internet kerak)..."
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt
  touch .venv/.installed
fi

exec .venv/bin/python run_app.py "$@"
