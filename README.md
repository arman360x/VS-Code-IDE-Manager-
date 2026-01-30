# VS Code Manager Pro

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?style=for-the-badge&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.7+-green?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-purple?style=for-the-badge" alt="Version">
</p>

<p align="center">
  <b>A powerful Windows application to manage multiple VS Code instances and SSH remote connections</b>
</p>

---

## Features

### Instance Management
- **List** all running VS Code instances with PID, workspace, and window title
- **Focus** any instance (bring to foreground)
- **Minimize / Maximize / Restore** windows
- **Close** individual or all instances at once
- **Auto-refresh** every 3 seconds
- Detect **Local vs Remote** instances

### Remote SSH Profile Management
- **Save SSH profiles** with host, username, password, and SSH key
- **One-click connect** to remote servers via VS Code Remote SSH
- **Auto-configure SSH config** (`~/.ssh/config`) for key-based authentication
- **Connect to specific paths** on remote servers
- **Copy SSH command** to clipboard
- **Edit and delete** profiles easily

### Premium UI
- Modern dark theme inspired by GitHub's design
- Custom application icon
- Smooth selection and right-click context menus
- Keyboard shortcuts for power users
- Resizable windows

---

## Screenshots

### Main Window - Running Instances
```
+------------------------------------------------------------------+
|  VS Code Manager                                                  |
|  Manage instances & remote connections                           |
|                                    [Open Folder] [New Window] [Refresh]
+------------------------------------------------------------------+
|  [ Running Instances ]  [ Remote Profiles (SSH) ]                |
+------------------------------------------------------------------+
|  PID    | Workspace        | Type   | Window Title               |
|---------|------------------|--------|----------------------------|
|  12345  | MyProject        | Local  | index.ts - MyProject - ... |
|  67890  | WebApp           | Remote | app.py - WebApp [SSH] - ...|
+------------------------------------------------------------------+
|  Instance Controls: [Focus] [Minimize] [Maximize] [Restore] [Close]
+------------------------------------------------------------------+
```

### Remote Profiles Tab
```
+------------------------------------------------------------------+
|  [+ Add Profile] [Connect] [Edit] [Delete]                       |
+------------------------------------------------------------------+
|  Profile    | Host          | Port | Username | Password | SSH Key|
|-------------|---------------|------|----------|----------|--------|
|  Production | 192.168.1.10  | 22   | ubuntu   | ******** | key.pem|
|  Staging    | staging.io    | 2222 | deploy   | -        | -      |
+------------------------------------------------------------------+
```

---

## Installation

### Option 1: Download Executable (Recommended)
1. Go to [Releases](https://github.com/arman360x/VS-Code-IDE-Manager-/releases)
2. Download `VSCodeManager_Setup.zip`
3. Extract and run `Install.bat`
4. Launch from Desktop shortcut or Start Menu

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/arman360x/VS-Code-IDE-Manager-.git
cd VS-Code-IDE-Manager-

# Install dependencies
pip install pywin32 psutil

# Run the application
python vscode_manager.py
```

### Option 3: Build Executable Yourself
```bash
# Install build dependencies
pip install pyinstaller pillow

# Run the build script
python build_installer.py
```

---

## Usage

### Managing VS Code Instances

1. **Launch** the application
2. All running VS Code windows appear in the **Running Instances** tab
3. **Select** an instance and use the control buttons:
   - **Focus**: Bring window to front
   - **Minimize/Maximize/Restore**: Window state controls
   - **Close**: Close the VS Code window

4. **Right-click** any instance for quick actions
5. **Double-click** to focus an instance

### Managing Remote SSH Profiles

1. Go to **Remote Profiles (SSH)** tab
2. Click **+ Add Profile**
3. Fill in connection details:
   - **Profile Name**: Friendly name (e.g., "Production Server")
   - **Host/IP**: Server address
   - **Port**: SSH port (default: 22)
   - **Username**: SSH username
   - **Password**: (Optional) SSH password
   - **SSH Key Path**: (Recommended) Path to your `.pem` or private key file

4. Click **Save** - the app automatically configures `~/.ssh/config`
5. **Double-click** a profile to connect via VS Code Remote SSH

### SSH Key Authentication

When you save a profile with an SSH key, the app automatically adds an entry to your SSH config:

```
# VS Code Manager - Production
Host Production
    HostName 192.168.1.10
    User ubuntu
    Port 22
    IdentityFile C:\Users\you\.ssh\production.pem
    StrictHostKeyChecking no
```

This allows VS Code Remote SSH to automatically use your key for authentication.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Refresh all |
| `Ctrl+N` | New VS Code window |
| `Ctrl+O` | Open folder in VS Code |
| `Ctrl+R` | Add remote profile |
| `Enter` | Focus selected / Connect to remote |
| `Delete` | Close instance / Delete profile |
| `Double-click` | Focus instance / Connect to remote |
| `Right-click` | Context menu |

---

## Requirements

- **Windows 10/11**
- **Python 3.7+** (if running from source)
- **VS Code** installed
- **VS Code Remote - SSH extension** (for remote connections)

### Python Dependencies
```
pywin32>=305
psutil>=5.9.0
```

---

## How It Works

### Window Management
The app uses Windows API (via `pywin32`) to:
1. Enumerate all windows using `EnumWindows`
2. Filter windows with "Visual Studio Code" in title
3. Manipulate windows using Win32 functions:
   - `SetForegroundWindow` - Focus
   - `ShowWindow` - Minimize/Maximize/Restore
   - `PostMessage(WM_CLOSE)` - Close

### SSH Integration
1. Profiles are saved to `~/.vscode_manager_config.json`
2. SSH keys are configured in `~/.ssh/config`
3. VS Code is launched with `--folder-uri vscode-remote://ssh-remote+host/path`

---

## File Structure

```
VS-Code-IDE-Manager-/
├── vscode_manager.py      # Main application
├── vscode_cli.py          # Command-line interface
├── build_installer.py     # Build script for Windows installer
├── requirements.txt       # Python dependencies
├── run_manager.bat        # Quick launch script
├── README.md              # This file
├── dist/                  # Built executables
│   ├── VSCodeManager.exe
│   ├── Install.bat
│   └── SilentInstall.bat
└── installer.iss          # Inno Setup script
```

---

## Configuration

Config file location: `~/.vscode_manager_config.json`

```json
{
  "workspaces": [
    "C:\\Projects\\MyApp",
    "C:\\Projects\\WebApp"
  ],
  "vscode_path": null,
  "remote_profiles": [
    {
      "name": "Production",
      "host": "192.168.1.10",
      "username": "ubuntu",
      "password": "",
      "ssh_key": "C:\\Users\\you\\.ssh\\key.pem",
      "port": 22
    }
  ]
}
```

---

## Troubleshooting

### "pywin32 not found"
```bash
pip install pywin32
# If that fails:
pip install pypiwin32
```

### VS Code not detected
- Ensure VS Code is installed
- The app checks these paths:
  - `%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe`
  - `C:\Program Files\Microsoft VS Code\Code.exe`
  - Falls back to `code` command

### SSH connection fails
1. Ensure VS Code **Remote - SSH** extension is installed
2. Check if the SSH key path is correct
3. Verify the key has correct permissions
4. Test SSH manually: `ssh -i "keypath" user@host`

### Instance not appearing
- Ensure VS Code window is fully loaded
- Click Refresh or wait for auto-refresh
- Window must have "Visual Studio Code" in title

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Arman**

- GitHub: [@arman360x](https://github.com/arman360x)

---

## Acknowledgments

- Built with Python and Tkinter
- Uses `pywin32` for Windows API access
- Inspired by the need for better VS Code instance management
- Premium dark theme inspired by GitHub's design

---

<p align="center">
  Made with ❤️ for developers who love VS Code
</p>
