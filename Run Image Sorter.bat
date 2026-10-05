@echo off
setlocal
set "PROJECT_DIR=%~dp0"
set "VENV_PYTHON=%PROJECT_DIR%venv_imagesorter\Scripts\python.exe"

if exist "%VENV_PYTHON%" goto run_venv
set "VENV_PYTHON=%PROJECT_DIR%..\venv_imagesorter\Scripts\python.exe"
if exist "%VENV_PYTHON%" goto run_venv
where py >nul 2>nul
if not errorlevel 1 goto run_py
where python >nul 2>nul
if not errorlevel 1 goto run_python

echo Python 3.10 or later was not found. Install Python and try again.
pause
exit /b 1

:run_venv
"%VENV_PYTHON%" "%PROJECT_DIR%run_image_sorter.py"
goto finished

:run_py
py -3 "%PROJECT_DIR%run_image_sorter.py"
goto finished

:run_python
python "%PROJECT_DIR%run_image_sorter.py"

:finished
if errorlevel 1 pause
endlocal
