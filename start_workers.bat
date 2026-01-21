@echo off
REM Script para iniciar 14 workers
REM Uso: start_workers.bat          (abre 14 terminales)
REM      start_workers.bat --silent (abre 1 terminal con todos los workers en background)

setlocal enabledelayedexpansion

REM Verificar si se paso el parametro --silent
set SILENT_MODE=0
if "%1"=="--silent" set SILENT_MODE=1
if "%1"=="-s" set SILENT_MODE=1

if %SILENT_MODE%==1 (
    echo Iniciando 14 workers en modo silencioso...
    echo Los workers se ejecutaran en background
    echo.
    
    REM Iniciar 14 workers en background sin mostrar ventanas
    for /L %%i in (1,1,14) do (
        start /B "" python cli/worker.py --continuous
        echo Worker %%i iniciado en background
    )
    
    echo.
    echo Todos los workers estan corriendo en background
    echo Para detenerlos, cierra esta ventana o usa Ctrl+C
    echo.
    pause
) else (
    echo Iniciando 14 workers en modo normal...
    echo Se abriran 14 ventanas de terminal
    echo.
    
    REM Iniciar 14 workers, cada uno en su propia ventana
    for /L %%i in (1,1,14) do (
        start "Worker %%i" cmd /k "python cli/worker.py --continuous"
        echo Ventana %%i abierta

    )
    
    echo.
    echo Las 14 ventanas de workers han sido abiertas
    echo Cada worker esta ejecutandose en modo continuo
)

endlocal
