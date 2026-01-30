"""
Build script for VS Code Manager Windows Installer
Creates an executable and installer package
"""

import os
import subprocess
import sys

def create_icon():
    """Create an ICO file for the application"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Installing Pillow for icon creation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageDraw

    # Create icon at multiple sizes
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle - blue
        margin = size // 10
        draw.ellipse([margin, margin, size - margin, size - margin],
                    fill='#58a6ff')

        # Inner circle - dark
        inner_margin = size // 6
        draw.ellipse([inner_margin, inner_margin, size - inner_margin, size - inner_margin],
                    fill='#0d1117')

        # Center circle - blue
        center_margin = size // 4
        draw.ellipse([center_margin, center_margin, size - center_margin, size - center_margin],
                    fill='#58a6ff')

        # Draw V shape
        v_top = int(size * 0.3)
        v_bottom = int(size * 0.7)
        v_left = int(size * 0.35)
        v_right = int(size * 0.65)
        v_center = size // 2
        v_width = max(2, size // 12)

        # Left line of V
        draw.polygon([
            (v_left, v_top),
            (v_left + v_width, v_top),
            (v_center + v_width//2, v_bottom),
            (v_center - v_width//2, v_bottom),
        ], fill='#0d1117')

        # Right line of V
        draw.polygon([
            (v_right - v_width, v_top),
            (v_right, v_top),
            (v_center + v_width//2, v_bottom),
            (v_center - v_width//2, v_bottom),
        ], fill='#0d1117')

        images.append(img)

    # Save as ICO
    icon_path = os.path.join(os.path.dirname(__file__), 'vscode_manager.ico')
    images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    print(f"Icon created: {icon_path}")
    return icon_path


def build_executable():
    """Build the executable using PyInstaller"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'vscode_manager.py')
    icon_path = os.path.join(script_dir, 'vscode_manager.ico')

    # Create icon if it doesn't exist
    if not os.path.exists(icon_path):
        create_icon()

    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=VSCodeManager',
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--clean',
        f'--icon={icon_path}',
        f'--distpath={os.path.join(script_dir, "dist")}',
        f'--workpath={os.path.join(script_dir, "build")}',
        f'--specpath={script_dir}',
        '--add-data', f'{icon_path};.',
        main_script
    ]

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_path = os.path.join(script_dir, 'dist', 'VSCodeManager.exe')
        print(f"\nBuild successful!")
        print(f"Executable: {exe_path}")
        return exe_path
    else:
        print("Build failed!")
        return None


def create_inno_setup_script():
    """Create Inno Setup script for installer"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    inno_script = f'''; VS Code Manager Installer Script
; Created with Inno Setup

#define MyAppName "VS Code Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "VS Code Manager"
#define MyAppExeName "VSCodeManager.exe"

[Setup]
AppId={{{{8F3E4B2A-1C5D-4E6F-9A8B-7C2D3E4F5A6B}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir={script_dir}\\installer
OutputBaseFilename=VSCodeManager_Setup
SetupIconFile={script_dir}\\vscode_manager.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "{script_dir}\\dist\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
'''

    inno_path = os.path.join(script_dir, 'installer.iss')
    with open(inno_path, 'w') as f:
        f.write(inno_script)

    print(f"Inno Setup script created: {inno_path}")
    return inno_path


def main():
    print("=" * 50)
    print("VS Code Manager - Build Installer")
    print("=" * 50)

    # Step 1: Create icon
    print("\n[1/3] Creating application icon...")
    create_icon()

    # Step 2: Build executable
    print("\n[2/3] Building executable with PyInstaller...")
    exe_path = build_executable()

    if exe_path and os.path.exists(exe_path):
        # Step 3: Create Inno Setup script
        print("\n[3/3] Creating Inno Setup installer script...")
        inno_path = create_inno_setup_script()

        print("\n" + "=" * 50)
        print("BUILD COMPLETE!")
        print("=" * 50)
        print(f"\nExecutable: {exe_path}")
        print(f"\nTo create installer:")
        print(f"1. Install Inno Setup from: https://jrsoftware.org/isdl.php")
        print(f"2. Open: {inno_path}")
        print(f"3. Click Build > Compile")
        print(f"\nOr run directly: {exe_path}")
    else:
        print("\nBuild failed. Please check the errors above.")


if __name__ == '__main__':
    main()
