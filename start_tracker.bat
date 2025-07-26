@echo off
REM Этот файл запускает трекер в фоновом режиме, используя правильный Python из виртуального окружения.
REM Все сообщения и ошибки будут записаны в файлы tracker_stdout.log и tracker_stderr.log

REM Определяем путь к папке, где находится этот .bat файл
set SCRIPT_DIR=%~dp0

REM Путь к pythonw.exe внутри вашего виртуального окружения
set PYTHON_EXE="%SCRIPT_DIR%.venv\Scripts\pythonw.exe"

REM Путь к основному скрипту
set SCRIPT_PATH="%SCRIPT_DIR%daw_tracker.py"

REM Пути к лог-файлам для отладки
set STDOUT_LOG="%SCRIPT_DIR%tracker_stdout.log"
set STDERR_LOG="%SCRIPT_DIR%tracker_stderr.log"

REM Запускаем скрипт в фоновом режиме и перенаправляем весь вывод в лог-файлы
echo Starting tracker at %date% %time%... >> %STDOUT_LOG%
start "DAW_Tracker_Background" /B %PYTHON_EXE% %SCRIPT_PATH% 1>>%STDOUT_LOG% 2>>%STDERR_LOG%