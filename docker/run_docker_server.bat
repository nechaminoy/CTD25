@echo off
setlocal

REM Build and run KFC Game Server with Docker

REM Default values
if "%KFC_HOST_PORT%"=="" set KFC_HOST_PORT=8765
if "%KFC_PORT%"=="" set KFC_PORT=8765

REM Parse command line arguments
:parse_args
if "%1"=="" goto start_build
if "%1"=="-p" (
    set KFC_HOST_PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--port" (
    set KFC_HOST_PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--container-port" (
    set KFC_PORT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help

echo Unknown option: %1
echo Use -h or --help for usage information
exit /b 1

:show_help
echo Usage: %0 [OPTIONS]
echo Options:
echo   -p, --port PORT          Host port to bind to (default: 8765)
echo   --container-port PORT    Container port (default: 8765)
echo   -h, --help              Show this help message
echo.
echo Environment variables:
echo   KFC_HOST_PORT           Host port to bind to
echo   KFC_PORT               Container port
exit /b 0

:start_build
echo Building KFC Game Server Docker image...
docker build -f docker/Dockerfile -t kfc-game-server .

if %ERRORLEVEL% EQU 0 (
    echo Build successful! Starting server...
    echo Server will be available on ws://localhost:%KFC_HOST_PORT%
    echo Press Ctrl+C to stop the server
    docker run -p %KFC_HOST_PORT%:%KFC_PORT% -e KFC_PORT=%KFC_PORT% --name kfc-server --rm kfc-game-server
) else (
    echo Build failed!
    exit /b 1
)
