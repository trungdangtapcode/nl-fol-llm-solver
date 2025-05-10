@echo off
for %%i in (81 82 83 84 85 86 87 88 89 90 91 92) do (
	for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%i') do (
    	taskkill /PID %%a /F
	)
)
echo All Uvicorn processes on ports 81-88 have been terminated.
pause