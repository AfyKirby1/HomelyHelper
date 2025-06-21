@echo off
echo ========================================
echo    Building HomelyHelper Desktop App
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

echo Creating portable executable...
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del "*.spec"

REM Build the app with optimizations
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "HomelyHelper" ^
    --distpath "./dist" ^
    --workpath "./build" ^
    --specpath "./build" ^
    --optimize 2 ^
    main.py

echo.
if exist "dist\HomelyHelper.exe" (
    echo ✅ Build successful!
    echo.
    echo Your portable app is ready:
    echo 📁 Location: dist\HomelyHelper.exe
    echo 📏 Size: ~35MB
    echo.
    echo 🚀 You can now distribute this single file!
    echo    Users just double-click to run - no installation needed!
    echo.
    echo 💡 To test: .\dist\HomelyHelper.exe
) else (
    echo ❌ Build failed. Check the output above for errors.
)

echo.
pause 