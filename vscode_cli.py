"""
VS Code Instance Manager - CLI Version
Quick command-line tool to manage VS Code instances

Requirements:
    pip install pywin32 psutil

Usage:
    python vscode_cli.py list              # List all running instances
    python vscode_cli.py open <folder>     # Open folder in new VS Code
    python vscode_cli.py focus <index>     # Focus instance by index
    python vscode_cli.py minimize <index>  # Minimize instance
    python vscode_cli.py maximize <index>  # Maximize instance
    python vscode_cli.py close <index>     # Close instance
    python vscode_cli.py minimize-all      # Minimize all instances
    python vscode_cli.py close-all         # Close all instances
"""

import sys
import subprocess
import os

try:
    import psutil
    import win32gui
    import win32con
    import win32process
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pywin32", "psutil"])
    import psutil
    import win32gui
    import win32con
    import win32process


class VSCodeCLI:
    def __init__(self):
        self.instances = []
    
    def refresh(self):
        """Refresh VS Code instances list"""
        self.instances = []
        
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Visual Studio Code" in title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        workspace = self._extract_workspace(title)
                        results.append({
                            'hwnd': hwnd,
                            'pid': pid,
                            'title': title,
                            'workspace': workspace
                        })
                    except:
                        pass
            return True
        
        win32gui.EnumWindows(callback, self.instances)
        return self.instances
    
    def _extract_workspace(self, title):
        if " - Visual Studio Code" in title:
            parts = title.replace(" - Visual Studio Code", "").split(" - ")
            return parts[-1] if parts else title
        return title
    
    def list_instances(self):
        """List all running VS Code instances"""
        self.refresh()
        
        if not self.instances:
            print("\n  No VS Code instances running.\n")
            return
        
        print("\n" + "=" * 70)
        print("  VS Code Running Instances")
        print("=" * 70)
        print(f"  {'#':<4} {'PID':<8} {'Workspace':<50}")
        print("-" * 70)
        
        for i, inst in enumerate(self.instances):
            workspace = inst['workspace'][:48] + '..' if len(inst['workspace']) > 50 else inst['workspace']
            print(f"  {i:<4} {inst['pid']:<8} {workspace:<50}")
        
        print("=" * 70)
        print(f"  Total: {len(self.instances)} instance(s)\n")
    
    def open_folder(self, folder):
        """Open folder in new VS Code instance"""
        if not os.path.exists(folder):
            print(f"  Error: Folder not found: {folder}")
            return False
        
        try:
            subprocess.Popen(["code", folder], shell=True)
            print(f"  ✓ Opening: {folder}")
            return True
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def open_new(self):
        """Open new empty VS Code window"""
        try:
            subprocess.Popen(["code", "-n"], shell=True)
            print("  ✓ Opening new VS Code window")
            return True
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def _get_instance(self, index):
        """Get instance by index"""
        self.refresh()
        try:
            idx = int(index)
            if 0 <= idx < len(self.instances):
                return self.instances[idx]
            print(f"  Error: Invalid index {idx}. Use 'list' to see available instances.")
        except ValueError:
            print(f"  Error: Invalid index '{index}'")
        return None
    
    def focus(self, index):
        """Focus instance by index"""
        inst = self._get_instance(index)
        if inst:
            try:
                hwnd = inst['hwnd']
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                print(f"  ✓ Focused: {inst['workspace']}")
            except Exception as e:
                print(f"  Error: {e}")
    
    def minimize(self, index):
        """Minimize instance by index"""
        inst = self._get_instance(index)
        if inst:
            win32gui.ShowWindow(inst['hwnd'], win32con.SW_MINIMIZE)
            print(f"  ✓ Minimized: {inst['workspace']}")
    
    def maximize(self, index):
        """Maximize instance by index"""
        inst = self._get_instance(index)
        if inst:
            win32gui.ShowWindow(inst['hwnd'], win32con.SW_MAXIMIZE)
            print(f"  ✓ Maximized: {inst['workspace']}")
    
    def restore(self, index):
        """Restore instance by index"""
        inst = self._get_instance(index)
        if inst:
            win32gui.ShowWindow(inst['hwnd'], win32con.SW_RESTORE)
            print(f"  ✓ Restored: {inst['workspace']}")
    
    def close(self, index):
        """Close instance by index"""
        inst = self._get_instance(index)
        if inst:
            win32gui.PostMessage(inst['hwnd'], win32con.WM_CLOSE, 0, 0)
            print(f"  ✓ Closed: {inst['workspace']}")
    
    def minimize_all(self):
        """Minimize all instances"""
        self.refresh()
        for inst in self.instances:
            win32gui.ShowWindow(inst['hwnd'], win32con.SW_MINIMIZE)
        print(f"  ✓ Minimized {len(self.instances)} instance(s)")
    
    def close_all(self):
        """Close all instances"""
        self.refresh()
        count = len(self.instances)
        for inst in self.instances:
            win32gui.PostMessage(inst['hwnd'], win32con.WM_CLOSE, 0, 0)
        print(f"  ✓ Closed {count} instance(s)")


def print_help():
    """Print usage help"""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                   VS Code Instance Manager - CLI                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Commands:                                                           ║
║    list                    List all running VS Code instances        ║
║    open <folder>           Open folder in new VS Code                ║
║    new                     Open new empty VS Code window             ║
║    focus <index>           Focus/bring to front by index             ║
║    minimize <index>        Minimize instance by index                ║
║    maximize <index>        Maximize instance by index                ║
║    restore <index>         Restore instance to normal size           ║
║    close <index>           Close instance by index                   ║
║    minimize-all            Minimize all VS Code instances            ║
║    close-all               Close all VS Code instances               ║
║                                                                      ║
║  Examples:                                                           ║
║    python vscode_cli.py list                                         ║
║    python vscode_cli.py open C:\\Projects\\MyApp                      ║
║    python vscode_cli.py focus 0                                      ║
║    python vscode_cli.py minimize-all                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def main():
    if os.name != 'nt':
        print("  This tool is designed for Windows OS.")
        return
    
    cli = VSCodeCLI()
    
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'list': cli.list_instances,
        'ls': cli.list_instances,
        'new': cli.open_new,
        'minimize-all': cli.minimize_all,
        'close-all': cli.close_all,
        'help': print_help,
        '-h': print_help,
        '--help': print_help,
    }
    
    commands_with_arg = {
        'open': cli.open_folder,
        'focus': cli.focus,
        'minimize': cli.minimize,
        'min': cli.minimize,
        'maximize': cli.maximize,
        'max': cli.maximize,
        'restore': cli.restore,
        'close': cli.close,
    }
    
    if command in commands:
        commands[command]()
    elif command in commands_with_arg:
        if len(sys.argv) < 3:
            print(f"  Error: '{command}' requires an argument")
            print(f"  Usage: python vscode_cli.py {command} <argument>")
        else:
            arg = sys.argv[2] if command == 'open' else sys.argv[2]
            commands_with_arg[command](arg)
    else:
        print(f"  Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
