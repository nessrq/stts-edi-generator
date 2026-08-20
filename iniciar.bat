@echo off
REM Arranca el backend FastAPI (puerto 8005)
set "BACKEND=C:\Users\Nestor David\Documents\edi_web\backend"
set "PYEXE=C:\Users\Nestor David\AppData\Local\Programs\Python\Python312\python.exe"
echo Iniciando backend API en http://127.0.0.1:8005 ...
start "EDI Backend" cmd /k "cd /d "%BACKEND%" && "%PYEXE%" run_backend.py"

REM Arranca el frontend React (Vite)
set "FRONTEND=C:\Users\Nestor David\Documents\edi_web\frontend"
echo Iniciando frontend React en http://localhost:5173 ...
start "EDI Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"
