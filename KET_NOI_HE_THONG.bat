@echo off
chcp 65001 >nul
title MatrixFlow OS x TikTok Farm Studio — Autonomous Video Pipeline
color 0B

echo ==============================================================================
echo       MATRIXFLOW OS x TIKTOK FARM STUDIO - HỆ THỐNG VẬN HÀNH TỰ ĐỘNG KHÉP KÍN
echo ==============================================================================
echo.

:: 1. KIỂM TRA MÔI TRƯỜNG PYTHON
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [LỖI] Không tìm thấy Python trong hệ thống!
    echo Vui lòng cài đặt Python 3.10+ và tích chọn "Add Python to PATH".
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [+] %PYTHON_VER%: Sẵn sàng.

:: 2. KIỂM TRA MÔI TRƯỜNG NODE.JS
node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [LỖI] Không tìm thấy Node.js trong hệ thống!
    echo Vui lòng cài đặt Node.js từ https://nodejs.org và thử lại.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
echo [+] Node.js %NODE_VER%: Sẵn sàng.

echo.
echo ==============================================================================
echo [1/3] Khởi động Web Dashboard MatrixFlow OS (Next.js - Port 3000)...
echo ==============================================================================
set MATRIX_WEB_DIR=C:\Users\DELL\Downloads\matrixflow-main\matrixflow-main
if not exist "%MATRIX_WEB_DIR%" (
    set MATRIX_WEB_DIR=%~dp0matrixflow-main
)
start "MatrixFlow Dashboard (Next.js)" cmd /k "cd /d "%MATRIX_WEB_DIR%" && echo 🚀 Đang khởi chạy MatrixFlow OS Web Server... && npm run dev"

echo.
echo ==============================================================================
echo [2/3] Khởi động Cầu Nối Bridge Worker (Watchdog & ADB Phone Executor)...
echo ==============================================================================
set BRIDGE_SCRIPT=C:\Users\DELL\Downloads\matrixflow-main\bridge_worker.py
set WATCH_DIR=C:\Users\DELL\Downloads\tool-tiktok-farm\videos\ready_to_post
if not exist "%BRIDGE_SCRIPT%" (
    set BRIDGE_SCRIPT=%~dp0bridge_worker.py
)
if not exist "%WATCH_DIR%" (
    set WATCH_DIR=%~dp0videos\ready_to_post
)

start "MatrixFlow Bridge Worker" cmd /k "python "%BRIDGE_SCRIPT%" --watch-dir "%WATCH_DIR%" --api-url "http://localhost:3000""

echo.
echo ==============================================================================
echo [3/3] Đang kết nối hệ thống và chuẩn bị mở trình duyệt...
echo ==============================================================================
timeout /t 4 /nobreak >nul

echo [+] Đang mở MatrixFlow OS Dashboard tại: http://localhost:3000
start http://localhost:3000

echo.
echo ==============================================================================
echo 🎉 HỆ THỐNG ĐÃ KÍCH HOẠT THÀNH CÔNG!
echo - Web Dashboard:       http://localhost:3000
echo - Thư mục cào & dựng:  tool-tiktok-farm/videos/ready_to_post/
echo - Hàng đợi điều phối:  Tự động đẩy vào Box Phone khi Reviewer bấm [DUYỆT ĐĂNG]
echo ==============================================================================
echo (Bạn có thể thu nhỏ cửa sổ này lại. Không tắt các cửa sổ phụ đang chạy ngầm)
pause
