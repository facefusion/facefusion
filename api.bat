@echo off

REM dev
start "" /B .\venv\Scripts\python.exe .\api.py --host 0.0.0.0 --port 9777 headless-run --log-level=info --execution-device-id 0 --execution-providers cuda --video-memory-strategy tolerant

REM device 0
REM start "" /B .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18001 headless-run --log-level=info --execution-device-id 0 --execution-providers cuda --video-memory-strategy tolerant
REM start "" /B .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18003 headless-run --log-level=info --execution-device-id 0 --execution-providers cuda --video-memory-strategy tolerant

REM device 1
REM start "" /B .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18002 headless-run --log-level=info --execution-device-id 1 --execution-providers cuda --video-memory-strategy tolerant
REM start "" /B .\venv\Scripts\python.exe .\api.py --host 127.0.0.1 --port 18004 headless-run --log-level=info --execution-device-id 1 --execution-providers cuda --video-memory-strategy tolerant

REM cd ..\alpha_pilot\mediator
REM mediator.exe
