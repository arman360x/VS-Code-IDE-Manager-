@echo off
title VS Code Manager - Installer
color 0B

echo.
echo  ========================================
echo   VS Code Manager - Installation
echo  ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\VSCodeManager"
set "EXE_NAME=VSCodeManager.exe"
set "SHORTCUT_NAME=VS Code Manager"

echo  Installing to: %INSTALL_DIR%
echo.

:: Create installation directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo  [OK] Created installation directory
) else (
    echo  [OK] Installation directory exists
)

:: Copy executable
copy /Y "%~dp0%EXE_NAME%" "%INSTALL_DIR%\%EXE_NAME%" >nul
if %errorlevel% equ 0 (
    echo  [OK] Copied application files
) else (
    echo  [ERROR] Failed to copy files
    pause
    exit /b 1
)

:: Create Start Menu shortcut
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\%SHORTCUT_NAME%.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\%EXE_NAME%'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'VS Code Instance Manager'; $Shortcut.Save()"
if %errorlevel% equ 0 (
    echo  [OK] Created Start Menu shortcut
) else (
    echo  [WARN] Could not create Start Menu shortcut
)

:: Create Desktop shortcut
set "DESKTOP=%USERPROFILE%\Desktop"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\%EXE_NAME%'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'VS Code Instance Manager'; $Shortcut.Save()"
if %errorlevel% equ 0 (
    echo  [OK] Created Desktop shortcut
) else (
    echo  [WARN] Could not create Desktop shortcut
)

:: Create uninstaller
(
echo @echo off
echo title VS Code Manager - Uninstaller
echo color 0C
echo.
echo  Uninstalling VS Code Manager...
echo.
echo  Removing files...
echo.
echo del /Q "%INSTALL_DIR%\%EXE_NAME%" 2^>nul
echo rmdir "%INSTALL_DIR%" 2^>nul
echo del "%START_MENU%\%SHORTCUT_NAME%.lnk" 2^>nul
echo del "%DESKTOP%\%SHORTCUT_NAME%.lnk" 2^>nul
echo.
echo  [OK] VS Code Manager has been uninstalled.
echo.
echo del "%%~f0"
echo pause
) > "%INSTALL_DIR%\Uninstall.bat"
echo  [OK] Created uninstaller

echo.
echo  ========================================
echo   Installation Complete!
echo  ========================================
echo.
echo  You can now:
echo   - Find "VS Code Manager" in Start Menu
echo   - Use the Desktop shortcut
echo   - Run from: %INSTALL_DIR%\%EXE_NAME%
echo.
echo  To uninstall, run: %INSTALL_DIR%\Uninstall.bat
echo.

set /p "LAUNCH=Launch VS Code Manager now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\%EXE_NAME%"
)

echo.
pause
