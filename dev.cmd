@echo off
rem Start DGX tunnel, backend, frontend, then check everything. Run from anywhere.
setlocal
set ROOT=%~dp0

rem --- 1. tunnel (skip if 47001 already listening)
netstat -an | findstr "LISTENING" | findstr ":47001 " >nul
if errorlevel 1 (
  echo Starting DGX tunnel...
  start "tunnel" cmd /k ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=4 -N -L 47001:localhost:47001 -L 47002:localhost:47002 sece2026-student36@aicentre.sece.ac.in
)

rem --- 2. backend (skip if 47000 already listening)
netstat -an | findstr "LISTENING" | findstr ":47000 " >nul
if errorlevel 1 (
  echo Starting backend...
  start "backend" /d "%ROOT%backend" cmd /k "set LLM_BASE_URL=http://localhost:47001/v1&& set LLM_BASE_URL_FAST=http://localhost:47002/v1&& set LLM_ALLOW_MOCK=false&& set ALLOWED_ORIGINS=http://localhost:5173&& python -m uvicorn api.main:app --host 127.0.0.1 --port 47000"
)

rem --- 3. frontend (skip if 5173 already listening)
netstat -an | findstr "LISTENING" | findstr ":5173 " >nul
if errorlevel 1 (
  echo Starting frontend...
  start "frontend" /d "%ROOT%frontend" cmd /k npm run dev
)

rem --- 4. checks (wait for startup, then probe)
echo Waiting 15s for services...
timeout /t 15 /nobreak >nul
echo.
call :check "vLLM heavy  (47001)" http://localhost:47001/health
call :check "vLLM fast   (47002)" http://localhost:47002/health
call :check "backend     (47000)" http://localhost:47000/health
call :check "frontend    (5173) " http://localhost:5173/
echo.
echo Open http://localhost:5173  (not 127.0.0.1)
pause
exit /b

:check
curl -s -o nul -m 5 -w "%%{http_code}" %2 > "%TEMP%\chk.txt"
set /p CODE=<"%TEMP%\chk.txt"
if "%CODE%"=="200" (echo [ OK ] %~1) else (echo [FAIL] %~1 - http %CODE%)
exit /b
