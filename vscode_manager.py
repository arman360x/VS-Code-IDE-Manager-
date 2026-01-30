"""
VS Code Instance Manager
Manage multiple VS Code instances - Open, Close, Minimize, Maximize, Focus
With Remote SSH Connection Management for productivity
Works on Windows OS

Requirements:
    pip install pywin32 psutil

Usage:
    python vscode_manager.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import json
import os
from datetime import datetime
import base64

try:
    import psutil
    import win32gui
    import win32con
    import win32process
except ImportError:
    print("Installing required packages...")
    import subprocess as sp
    sp.run(["pip", "install", "pywin32", "psutil"])
    import psutil
    import win32gui
    import win32con
    import win32process


# Premium Color Scheme
class Colors:
    # Main backgrounds
    BG_DARK = "#0d1117"
    BG_SECONDARY = "#161b22"
    BG_TERTIARY = "#21262d"
    BG_HOVER = "#30363d"

    # Accent colors
    ACCENT_PRIMARY = "#58a6ff"
    ACCENT_GREEN = "#3fb950"
    ACCENT_PURPLE = "#a371f7"
    ACCENT_ORANGE = "#d29922"
    ACCENT_RED = "#f85149"

    # Text colors
    TEXT_PRIMARY = "#e6edf3"
    TEXT_SECONDARY = "#8b949e"
    TEXT_MUTED = "#6e7681"

    # Border
    BORDER = "#30363d"
    BORDER_LIGHT = "#3d444d"

    # Button colors
    BTN_PRIMARY_BG = "#238636"
    BTN_PRIMARY_HOVER = "#2ea043"
    BTN_SECONDARY_BG = "#21262d"
    BTN_SECONDARY_HOVER = "#30363d"


class VSCodeInstance:
    """Represents a single VS Code window instance"""
    def __init__(self, hwnd, pid, title):
        self.hwnd = hwnd
        self.pid = pid
        self.title = title
        self.workspace = self.extract_workspace(title)
        self.is_remote = "[SSH:" in title or "SSH: " in title or "[WSL:" in title

    def extract_workspace(self, title):
        """Extract workspace/folder name from window title"""
        if " - Visual Studio Code" in title:
            parts = title.replace(" - Visual Studio Code", "").split(" - ")
            if len(parts) >= 2:
                return parts[-1]
            elif len(parts) == 1:
                return parts[0]
        return title

    def __str__(self):
        return f"[PID: {self.pid}] {self.workspace}"


class RemoteProfile:
    """Represents a remote SSH connection profile"""
    def __init__(self, name, host, username, password="", ssh_key="", port=22):
        self.name = name
        self.host = host
        self.username = username
        self.password = password
        self.ssh_key = ssh_key
        self.port = port

    def to_dict(self):
        return {
            "name": self.name,
            "host": self.host,
            "username": self.username,
            "password": base64.b64encode(self.password.encode()).decode() if self.password else "",
            "ssh_key": self.ssh_key,
            "port": self.port
        }

    @staticmethod
    def from_dict(data):
        password = ""
        if data.get("password"):
            try:
                password = base64.b64decode(data["password"]).decode()
            except:
                password = data.get("password", "")
        return RemoteProfile(
            name=data.get("name", ""),
            host=data.get("host", ""),
            username=data.get("username", ""),
            password=password,
            ssh_key=data.get("ssh_key", ""),
            port=data.get("port", 22)
        )

    def get_ssh_uri(self):
        """Get VS Code Remote SSH URI"""
        return f"ssh://{self.username}@{self.host}:{self.port}"


class VSCodeManager:
    """Core manager for VS Code instances"""

    def __init__(self):
        self.instances = []
        self.vscode_paths = [
            r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
        ]
        self.config_file = os.path.join(os.path.expanduser("~"), ".vscode_manager_config.json")
        self.config = self.load_config()

    def load_config(self):
        """Load saved config"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"workspaces": [], "vscode_path": None, "remote_profiles": []}

    def save_config(self):
        """Save config"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_remote_profiles(self):
        """Get all remote profiles"""
        profiles = []
        for data in self.config.get("remote_profiles", []):
            profiles.append(RemoteProfile.from_dict(data))
        return profiles

    def add_remote_profile(self, profile):
        """Add a remote profile"""
        if "remote_profiles" not in self.config:
            self.config["remote_profiles"] = []
        self.config["remote_profiles"].append(profile.to_dict())
        self.save_config()
        # Update SSH config for key-based auth
        self.update_ssh_config(profile)

    def update_remote_profile(self, index, profile):
        """Update a remote profile"""
        if 0 <= index < len(self.config.get("remote_profiles", [])):
            # Get old profile name to remove from SSH config
            old_profile = RemoteProfile.from_dict(self.config["remote_profiles"][index])
            self.config["remote_profiles"][index] = profile.to_dict()
            self.save_config()
            # Update SSH config
            self.remove_from_ssh_config(old_profile.name)
            self.update_ssh_config(profile)

    def delete_remote_profile(self, index):
        """Delete a remote profile"""
        if 0 <= index < len(self.config.get("remote_profiles", [])):
            # Get profile name to remove from SSH config
            profile = RemoteProfile.from_dict(self.config["remote_profiles"][index])
            del self.config["remote_profiles"][index]
            self.save_config()
            # Remove from SSH config
            self.remove_from_ssh_config(profile.name)

    def get_ssh_config_path(self):
        """Get the SSH config file path"""
        ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, exist_ok=True)
        return os.path.join(ssh_dir, "config")

    def update_ssh_config(self, profile):
        """Add or update SSH config entry for a profile"""
        ssh_config_path = self.get_ssh_config_path()

        # Create the SSH config entry
        # Use a sanitized name for the Host alias (replace spaces with underscores)
        host_alias = profile.name.replace(" ", "_").replace(".", "-")

        new_entry_lines = [
            f"\n# VS Code Manager - {profile.name}",
            f"Host {host_alias}",
            f"    HostName {profile.host}",
            f"    User {profile.username}",
            f"    Port {profile.port}",
        ]

        if profile.ssh_key and os.path.exists(profile.ssh_key):
            new_entry_lines.append(f"    IdentityFile {profile.ssh_key}")

        new_entry_lines.append("    StrictHostKeyChecking no")
        new_entry_lines.append("")

        new_entry = "\n".join(new_entry_lines)

        # Read existing config
        existing_content = ""
        if os.path.exists(ssh_config_path):
            try:
                with open(ssh_config_path, 'r') as f:
                    existing_content = f.read()
            except:
                pass

        # Remove old entry if exists
        existing_content = self._remove_host_entry(existing_content, host_alias)

        # Append new entry
        with open(ssh_config_path, 'w') as f:
            f.write(existing_content.rstrip() + new_entry)

        return host_alias

    def remove_from_ssh_config(self, profile_name):
        """Remove SSH config entry for a profile"""
        ssh_config_path = self.get_ssh_config_path()
        host_alias = profile_name.replace(" ", "_").replace(".", "-")

        if os.path.exists(ssh_config_path):
            try:
                with open(ssh_config_path, 'r') as f:
                    content = f.read()

                content = self._remove_host_entry(content, host_alias)

                with open(ssh_config_path, 'w') as f:
                    f.write(content)
            except:
                pass

    def _remove_host_entry(self, content, host_alias):
        """Remove a Host entry from SSH config content"""
        lines = content.split('\n')
        new_lines = []
        skip_until_next_host = False
        skip_comment = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for our comment marker
            if stripped.startswith(f"# VS Code Manager -"):
                # Check if next line is the host we want to remove
                if i + 1 < len(lines) and lines[i + 1].strip().lower() == f"host {host_alias}".lower():
                    skip_comment = True
                    skip_until_next_host = True
                    i += 1
                    continue

            if skip_comment:
                skip_comment = False
                i += 1
                continue

            # Check for Host line
            if stripped.lower().startswith("host ") and not stripped.lower().startswith("hostname"):
                if skip_until_next_host:
                    skip_until_next_host = False
                current_host = stripped[5:].strip().split()[0] if stripped[5:].strip() else ""
                if current_host.lower() == host_alias.lower():
                    skip_until_next_host = True
                    i += 1
                    continue

            if skip_until_next_host:
                # Skip lines until we hit another Host directive or end
                if stripped.lower().startswith("host ") and not stripped.lower().startswith("hostname"):
                    skip_until_next_host = False
                    new_lines.append(line)
                i += 1
                continue

            new_lines.append(line)
            i += 1

        # Clean up multiple blank lines
        result = '\n'.join(new_lines)
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')

        return result

    def get_vscode_path(self):
        """Find VS Code executable path"""
        if self.config.get("vscode_path") and os.path.exists(self.config["vscode_path"]):
            return self.config["vscode_path"]

        username = os.environ.get("USERNAME", "")
        for path in self.vscode_paths:
            full_path = path.format(username)
            if os.path.exists(full_path):
                return full_path

        return "code"

    def refresh_instances(self):
        """Scan and refresh list of running VS Code instances"""
        self.instances = []

        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Visual Studio Code" in title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        instance = VSCodeInstance(hwnd, pid, title)
                        results.append(instance)
                    except:
                        pass
            return True

        win32gui.EnumWindows(enum_windows_callback, self.instances)
        return self.instances

    def open_workspace(self, folder_path):
        """Open a new VS Code instance with specified folder"""
        vscode_path = self.get_vscode_path()
        try:
            if vscode_path == "code":
                subprocess.Popen(["code", folder_path], shell=True)
            else:
                subprocess.Popen([vscode_path, folder_path])

            if folder_path not in self.config["workspaces"]:
                self.config["workspaces"].insert(0, folder_path)
                self.config["workspaces"] = self.config["workspaces"][:20]
                self.save_config()
            return True
        except Exception as e:
            return str(e)

    def open_remote(self, profile, remote_path=""):
        """Open VS Code with Remote SSH connection"""
        vscode_path = self.get_vscode_path()
        try:
            # Use the SSH config host alias if SSH key is configured
            # This allows VS Code to use the IdentityFile from SSH config
            if profile.ssh_key and os.path.exists(profile.ssh_key):
                host_alias = profile.name.replace(" ", "_").replace(".", "-")
                ssh_host = host_alias
            else:
                ssh_host = f"{profile.username}@{profile.host}"

            if remote_path:
                uri = f"vscode-remote://ssh-remote+{ssh_host}/{remote_path}"
            else:
                uri = f"vscode-remote://ssh-remote+{ssh_host}/"

            if vscode_path == "code":
                subprocess.Popen(["code", "--folder-uri", uri], shell=True)
            else:
                subprocess.Popen([vscode_path, "--folder-uri", uri])
            return True
        except Exception as e:
            return str(e)

    def open_new_window(self):
        """Open a new empty VS Code window"""
        vscode_path = self.get_vscode_path()
        try:
            if vscode_path == "code":
                subprocess.Popen(["code", "-n"], shell=True)
            else:
                subprocess.Popen([vscode_path, "-n"])
            return True
        except Exception as e:
            return str(e)

    def focus_instance(self, instance):
        """Bring VS Code instance to foreground"""
        try:
            if win32gui.IsIconic(instance.hwnd):
                win32gui.ShowWindow(instance.hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(instance.hwnd)
            return True
        except Exception as e:
            return str(e)

    def minimize_instance(self, instance):
        """Minimize VS Code instance"""
        try:
            win32gui.ShowWindow(instance.hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            return str(e)

    def maximize_instance(self, instance):
        """Maximize VS Code instance"""
        try:
            win32gui.ShowWindow(instance.hwnd, win32con.SW_MAXIMIZE)
            return True
        except Exception as e:
            return str(e)

    def restore_instance(self, instance):
        """Restore VS Code instance to normal size"""
        try:
            win32gui.ShowWindow(instance.hwnd, win32con.SW_RESTORE)
            return True
        except Exception as e:
            return str(e)

    def close_instance(self, instance):
        """Close VS Code instance"""
        try:
            win32gui.PostMessage(instance.hwnd, win32con.WM_CLOSE, 0, 0)
            return True
        except Exception as e:
            return str(e)

    def minimize_all(self):
        """Minimize all VS Code instances"""
        self.refresh_instances()
        for instance in self.instances:
            self.minimize_instance(instance)

    def close_all(self):
        """Close all VS Code instances"""
        self.refresh_instances()
        for instance in self.instances:
            self.close_instance(instance)


class RemoteProfileDialog(tk.Toplevel):
    """Dialog for adding/editing remote profiles"""

    def __init__(self, parent, profile=None, title="Add Remote Profile"):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x620")
        self.resizable(True, True)
        self.minsize(500, 580)
        self.configure(bg=Colors.BG_DARK)

        self.result = None
        self.profile = profile

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

        if profile:
            self.populate_fields(profile)

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self.wait_window(self)

    def create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = tk.Frame(self, bg=Colors.BG_SECONDARY)
        header_frame.pack(fill=tk.X)

        header_label = tk.Label(header_frame, text="SSH Connection Profile",
                               font=("Segoe UI Semibold", 12), fg=Colors.TEXT_PRIMARY,
                               bg=Colors.BG_SECONDARY)
        header_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Buttons frame at bottom - pack first to ensure visibility
        btn_frame = tk.Frame(self, bg=Colors.BG_SECONDARY)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, ipady=12)

        inner_btn_frame = tk.Frame(btn_frame, bg=Colors.BG_SECONDARY)
        inner_btn_frame.pack(side=tk.RIGHT, padx=20)

        cancel_btn = tk.Button(inner_btn_frame, text="Cancel", font=("Segoe UI Semibold", 10),
                              bg=Colors.BTN_SECONDARY_BG, fg=Colors.TEXT_PRIMARY,
                              activebackground=Colors.BTN_SECONDARY_HOVER,
                              activeforeground=Colors.TEXT_PRIMARY,
                              relief="flat", cursor="hand2", width=10,
                              command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, ipady=5)

        save_btn = tk.Button(inner_btn_frame, text="Save", font=("Segoe UI Semibold", 10),
                            bg=Colors.BTN_PRIMARY_BG, fg=Colors.TEXT_PRIMARY,
                            activebackground=Colors.BTN_PRIMARY_HOVER,
                            activeforeground=Colors.TEXT_PRIMARY,
                            relief="flat", cursor="hand2", width=10,
                            command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=(0, 10), ipady=5)

        # Main scrollable content
        main_frame = tk.Frame(self, bg=Colors.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Form fields
        self.entries = {}
        fields_data = [
            ("Profile Name", "name", False),
            ("Host / IP Address", "host", False),
            ("Port", "port", False),
            ("Username", "username", False),
            ("Password", "password", True),
            ("SSH Key Path", "ssh_key", False),
        ]

        for label_text, field_name, is_password in fields_data:
            # Label
            lbl = tk.Label(main_frame, text=label_text, font=("Segoe UI", 9),
                          fg=Colors.TEXT_SECONDARY, bg=Colors.BG_DARK)
            lbl.pack(anchor="w", pady=(5, 2))

            if field_name == "ssh_key":
                # SSH Key with browse button
                ssh_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
                ssh_frame.pack(fill=tk.X, pady=(0, 5))

                entry = tk.Entry(ssh_frame, font=("Segoe UI", 10),
                                bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY,
                                insertbackground=Colors.TEXT_PRIMARY, relief="flat",
                                highlightthickness=1, highlightbackground=Colors.BORDER,
                                highlightcolor=Colors.ACCENT_PRIMARY)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

                browse_btn = tk.Button(ssh_frame, text="Browse", font=("Segoe UI", 9),
                                      bg=Colors.BTN_SECONDARY_BG, fg=Colors.TEXT_PRIMARY,
                                      activebackground=Colors.BTN_SECONDARY_HOVER,
                                      activeforeground=Colors.TEXT_PRIMARY,
                                      relief="flat", cursor="hand2",
                                      command=lambda e=entry: self.browse_ssh_key(e))
                browse_btn.pack(side=tk.LEFT, padx=(8, 0), ipady=3, ipadx=8)
                self.entries[field_name] = entry
            else:
                # Regular entry
                show = "*" if is_password else ""
                entry = tk.Entry(main_frame, font=("Segoe UI", 10), show=show,
                                bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY,
                                insertbackground=Colors.TEXT_PRIMARY, relief="flat",
                                highlightthickness=1, highlightbackground=Colors.BORDER,
                                highlightcolor=Colors.ACCENT_PRIMARY)
                entry.pack(fill=tk.X, ipady=5, pady=(0, 5))

                if field_name == "port":
                    entry.insert(0, "22")

                self.entries[field_name] = entry

        # Note at bottom of form
        note_frame = tk.Frame(main_frame, bg=Colors.BG_TERTIARY)
        note_frame.pack(fill=tk.X, pady=(15, 5))

        note_label = tk.Label(note_frame,
                             text="Tip: For security, prefer SSH key authentication over password.",
                             font=("Segoe UI", 8), fg=Colors.TEXT_MUTED, bg=Colors.BG_TERTIARY)
        note_label.pack(anchor="w", padx=10, pady=6)

    def browse_ssh_key(self, entry):
        """Browse for SSH key file"""
        ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
        if not os.path.exists(ssh_dir):
            ssh_dir = os.path.expanduser("~")

        filepath = filedialog.askopenfilename(
            title="Select SSH Key",
            initialdir=ssh_dir,
            filetypes=[("All files", "*.*"), ("PEM files", "*.pem"), ("PPK files", "*.ppk")]
        )
        if filepath:
            entry.delete(0, tk.END)
            entry.insert(0, filepath)

    def populate_fields(self, profile):
        """Populate fields with existing profile data"""
        self.entries["name"].insert(0, profile.name)
        self.entries["host"].insert(0, profile.host)
        self.entries["port"].delete(0, tk.END)
        self.entries["port"].insert(0, str(profile.port))
        self.entries["username"].insert(0, profile.username)
        self.entries["password"].insert(0, profile.password)
        self.entries["ssh_key"].insert(0, profile.ssh_key)

    def save(self):
        """Save the profile"""
        name = self.entries["name"].get().strip()
        host = self.entries["host"].get().strip()
        username = self.entries["username"].get().strip()

        if not name or not host or not username:
            messagebox.showwarning("Missing Fields", "Please fill in Name, Host, and Username.",
                                  parent=self)
            return

        try:
            port = int(self.entries["port"].get().strip())
        except ValueError:
            port = 22

        self.result = RemoteProfile(
            name=name,
            host=host,
            username=username,
            password=self.entries["password"].get(),
            ssh_key=self.entries["ssh_key"].get().strip(),
            port=port
        )
        self.destroy()

    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.destroy()


class PremiumButton(tk.Canvas):
    """Custom premium styled button"""

    def __init__(self, parent, text, command=None, width=120, height=36,
                 bg_color=None, hover_color=None, text_color=None, icon=None):
        super().__init__(parent, width=width, height=height,
                        bg=parent.cget("bg"), highlightthickness=0)

        self.command = command
        self.text = text
        self.icon = icon
        self.width = width
        self.height = height
        self.bg_color = bg_color or Colors.BTN_SECONDARY_BG
        self.hover_color = hover_color or Colors.BTN_SECONDARY_HOVER
        self.text_color = text_color or Colors.TEXT_PRIMARY
        self.is_hovered = False

        self.draw_button()

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.config(cursor="hand2")

    def draw_button(self):
        self.delete("all")
        color = self.hover_color if self.is_hovered else self.bg_color

        # Draw rounded rectangle
        radius = 6
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius, fill=color, outline="")

        # Draw text
        display_text = f"{self.icon} {self.text}" if self.icon else self.text
        self.create_text(self.width//2, self.height//2, text=display_text,
                        fill=self.text_color, font=("Segoe UI Semibold", 9))

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()

    def on_leave(self, event):
        self.is_hovered = False
        self.draw_button()

    def on_click(self, event):
        if self.command:
            self.command()


class VSCodeManagerGUI:
    """GUI for VS Code Instance Manager"""

    def __init__(self):
        self.manager = VSCodeManager()
        self.root = tk.Tk()
        self.root.title("VS Code Manager Pro")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        self.root.configure(bg=Colors.BG_DARK)

        # Set window icon
        self.set_window_icon()

        self.selected_hwnd = None

        self.setup_styles()
        self.create_widgets()
        self.create_context_menu()
        self.create_remote_context_menu()
        self.refresh_list()
        self.refresh_remote_list()

        self.auto_refresh()

    def set_window_icon(self):
        """Create and set a custom window icon"""
        # Create a simple icon using PhotoImage
        icon_size = 32
        icon = tk.PhotoImage(width=icon_size, height=icon_size)

        # Draw a simple VS Code-like icon
        # Background
        for x in range(icon_size):
            for y in range(icon_size):
                icon.put(Colors.ACCENT_PRIMARY, (x, y))

        # Create a "V" shape pattern
        for i in range(12):
            # Left side of V
            icon.put(Colors.TEXT_PRIMARY, (8 + i//2, 8 + i))
            icon.put(Colors.TEXT_PRIMARY, (9 + i//2, 8 + i))
            # Right side of V
            icon.put(Colors.TEXT_PRIMARY, (23 - i//2, 8 + i))
            icon.put(Colors.TEXT_PRIMARY, (22 - i//2, 8 + i))

        self.root.iconphoto(True, icon)

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Frame styles
        style.configure("TFrame", background=Colors.BG_DARK)
        style.configure("Secondary.TFrame", background=Colors.BG_SECONDARY)

        # Label styles
        style.configure("TLabel", background=Colors.BG_DARK, foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20),
                       foreground=Colors.TEXT_PRIMARY, background=Colors.BG_DARK)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11),
                       foreground=Colors.TEXT_SECONDARY, background=Colors.BG_DARK)
        style.configure("Status.TLabel", font=("Segoe UI", 9),
                       foreground=Colors.TEXT_MUTED, background=Colors.BG_SECONDARY)

        # Notebook (tabs) styles
        style.configure("TNotebook", background=Colors.BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab",
                       background=Colors.BG_SECONDARY,
                       foreground=Colors.TEXT_SECONDARY,
                       padding=[20, 12],
                       font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab",
                 background=[("selected", Colors.BG_DARK)],
                 foreground=[("selected", Colors.ACCENT_PRIMARY)])

        # Treeview styles
        style.configure("Treeview",
                       background=Colors.BG_SECONDARY,
                       foreground=Colors.TEXT_PRIMARY,
                       fieldbackground=Colors.BG_SECONDARY,
                       font=("Segoe UI", 10),
                       rowheight=40,
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=Colors.BG_TERTIARY,
                       foreground=Colors.TEXT_SECONDARY,
                       font=("Segoe UI Semibold", 10),
                       borderwidth=0,
                       relief="flat")
        style.map("Treeview",
                 background=[("selected", Colors.ACCENT_PRIMARY)],
                 foreground=[("selected", Colors.TEXT_PRIMARY)])
        style.map("Treeview.Heading",
                 background=[("active", Colors.BG_HOVER)])

        # Scrollbar styles
        style.configure("Vertical.TScrollbar",
                       background=Colors.BG_TERTIARY,
                       troughcolor=Colors.BG_SECONDARY,
                       borderwidth=0,
                       arrowsize=0)
        style.map("Vertical.TScrollbar",
                 background=[("active", Colors.BG_HOVER)])

    def create_context_menu(self):
        """Create right-click context menu for instances"""
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                   bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY,
                                   activebackground=Colors.ACCENT_PRIMARY,
                                   activeforeground=Colors.TEXT_PRIMARY,
                                   font=("Segoe UI", 10), borderwidth=0,
                                   relief="flat")
        self.context_menu.add_command(label="  Focus Window", command=self.focus_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  Minimize", command=self.minimize_selected)
        self.context_menu.add_command(label="  Maximize", command=self.maximize_selected)
        self.context_menu.add_command(label="  Restore", command=self.restore_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  Close Window", command=self.close_selected)

    def create_remote_context_menu(self):
        """Create right-click context menu for remote profiles"""
        self.remote_context_menu = tk.Menu(self.root, tearoff=0,
                                          bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY,
                                          activebackground=Colors.ACCENT_PRIMARY,
                                          activeforeground=Colors.TEXT_PRIMARY,
                                          font=("Segoe UI", 10), borderwidth=0,
                                          relief="flat")
        self.remote_context_menu.add_command(label="  Connect", command=self.connect_remote)
        self.remote_context_menu.add_command(label="  Connect to Path...", command=self.connect_remote_path)
        self.remote_context_menu.add_separator()
        self.remote_context_menu.add_command(label="  Edit Profile", command=self.edit_remote_profile)
        self.remote_context_menu.add_command(label="  Copy SSH Command", command=self.copy_ssh_command)
        self.remote_context_menu.add_separator()
        self.remote_context_menu.add_command(label="  Delete Profile", command=self.delete_remote_profile)

    def on_tree_click(self, event):
        """Handle single click on treeview"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)

    def on_right_click(self, event):
        """Handle right-click on instances treeview"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            item_data = self.tree.item(item)
            if item_data["tags"]:
                self.selected_hwnd = int(item_data["tags"][0])
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def on_remote_click(self, event):
        """Handle single click on remote treeview"""
        item = self.remote_tree.identify_row(event.y)
        if item:
            self.remote_tree.selection_set(item)
            self.remote_tree.focus(item)

    def on_remote_right_click(self, event):
        """Handle right-click on remote treeview"""
        item = self.remote_tree.identify_row(event.y)
        if item:
            self.remote_tree.selection_set(item)
            self.remote_tree.focus(item)
            try:
                self.remote_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.remote_context_menu.grab_release()

    def on_selection_change(self, event):
        """Track selection changes"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            if item["tags"]:
                self.selected_hwnd = int(item["tags"][0])

    def create_widgets(self):
        """Create all GUI widgets"""
        # Bottom control bar - pack first so it stays at bottom
        control_bar = tk.Frame(self.root, bg=Colors.BG_SECONDARY)
        control_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=10)

        # Left side - Instance controls
        controls_left = tk.Frame(control_bar, bg=Colors.BG_SECONDARY)
        controls_left.pack(side=tk.LEFT, padx=25, pady=8)

        control_label = tk.Label(controls_left, text="Instance Controls:",
                                font=("Segoe UI", 10), fg=Colors.TEXT_SECONDARY,
                                bg=Colors.BG_SECONDARY)
        control_label.pack(side=tk.LEFT, padx=(0, 12))

        for text, cmd in [("Focus", self.focus_selected), ("Minimize", self.minimize_selected),
                          ("Maximize", self.maximize_selected), ("Restore", self.restore_selected),
                          ("Close", self.close_selected)]:
            btn = PremiumButton(controls_left, text=text, command=cmd, width=80, height=30)
            btn.pack(side=tk.LEFT, padx=2)

        # Right side - Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(control_bar, textvariable=self.status_var,
                               font=("Segoe UI", 9), fg=Colors.TEXT_MUTED,
                               bg=Colors.BG_SECONDARY)
        status_label.pack(side=tk.RIGHT, padx=25, pady=8)

        # Main container - pack after bottom bar
        main_frame = tk.Frame(self.root, bg=Colors.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header section
        header_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
        header_frame.pack(fill=tk.X, padx=25, pady=(20, 15))

        # Logo and title
        title_container = tk.Frame(header_frame, bg=Colors.BG_DARK)
        title_container.pack(side=tk.LEFT)

        # Logo canvas
        logo_canvas = tk.Canvas(title_container, width=45, height=45,
                               bg=Colors.BG_DARK, highlightthickness=0)
        logo_canvas.pack(side=tk.LEFT, padx=(0, 12))

        # Draw premium logo
        self.draw_logo(logo_canvas)

        title_text_frame = tk.Frame(title_container, bg=Colors.BG_DARK)
        title_text_frame.pack(side=tk.LEFT)

        title_label = tk.Label(title_text_frame, text="VS Code Manager",
                              font=("Segoe UI Semibold", 18), fg=Colors.TEXT_PRIMARY,
                              bg=Colors.BG_DARK)
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(title_text_frame, text="Manage instances & remote connections",
                                 font=("Segoe UI", 10), fg=Colors.TEXT_SECONDARY,
                                 bg=Colors.BG_DARK)
        subtitle_label.pack(anchor="w")

        # Quick action buttons in header
        btn_frame = tk.Frame(header_frame, bg=Colors.BG_DARK)
        btn_frame.pack(side=tk.RIGHT)

        actions = [
            ("Open Folder", self.open_folder, Colors.BTN_SECONDARY_BG),
            ("New Window", self.new_window, Colors.BTN_SECONDARY_BG),
            ("Refresh", self.refresh_all, Colors.BTN_SECONDARY_BG),
        ]

        for text, cmd, color in actions:
            btn = PremiumButton(btn_frame, text=text, command=cmd, width=100, height=32,
                              bg_color=color, hover_color=Colors.BTN_SECONDARY_HOVER)
            btn.pack(side=tk.LEFT, padx=4)

        # Notebook (tabs)
        notebook_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Running Instances
        instances_tab = tk.Frame(self.notebook, bg=Colors.BG_DARK)
        self.notebook.add(instances_tab, text="  Running Instances  ")

        # Instances container with border effect
        instances_container = tk.Frame(instances_tab, bg=Colors.BORDER)
        instances_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0), padx=2)

        instances_inner = tk.Frame(instances_container, bg=Colors.BG_SECONDARY)
        instances_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Treeview for instances
        columns = ("pid", "workspace", "type", "title")
        self.tree = ttk.Treeview(instances_inner, columns=columns, show="headings")

        self.tree.heading("pid", text="PID", anchor="w")
        self.tree.heading("workspace", text="Workspace", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.heading("title", text="Window Title", anchor="w")

        self.tree.column("pid", width=70, minwidth=60)
        self.tree.column("workspace", width=250, minwidth=150)
        self.tree.column("type", width=80, minwidth=70)
        self.tree.column("title", width=500, minwidth=200)

        scrollbar = ttk.Scrollbar(instances_inner, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", lambda e: self.focus_selected())
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        self.tree.bind("<Return>", lambda e: self.focus_selected())
        self.tree.bind("<Delete>", lambda e: self.close_selected())

        # Tab 2: Remote Profiles
        remote_tab = tk.Frame(self.notebook, bg=Colors.BG_DARK)
        self.notebook.add(remote_tab, text="  Remote Profiles (SSH)  ")

        # Remote toolbar
        remote_toolbar = tk.Frame(remote_tab, bg=Colors.BG_DARK)
        remote_toolbar.pack(fill=tk.X, pady=(10, 8))

        add_btn = PremiumButton(remote_toolbar, text="Add Profile", command=self.add_remote_profile,
                               width=110, height=32, bg_color=Colors.BTN_PRIMARY_BG,
                               hover_color=Colors.BTN_PRIMARY_HOVER, icon="+")
        add_btn.pack(side=tk.LEFT)

        for text, cmd in [("Connect", self.connect_remote), ("Edit", self.edit_remote_profile),
                          ("Delete", self.delete_remote_profile)]:
            btn = PremiumButton(remote_toolbar, text=text, command=cmd, width=90, height=32)
            btn.pack(side=tk.LEFT, padx=(8, 0))

        # Remote profiles container
        remote_container = tk.Frame(remote_tab, bg=Colors.BORDER)
        remote_container.pack(fill=tk.BOTH, expand=True, padx=2)

        remote_inner = tk.Frame(remote_container, bg=Colors.BG_SECONDARY)
        remote_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Remote treeview
        remote_columns = ("name", "host", "port", "username", "password", "ssh_key")
        self.remote_tree = ttk.Treeview(remote_inner, columns=remote_columns, show="headings")

        self.remote_tree.heading("name", text="Profile Name", anchor="w")
        self.remote_tree.heading("host", text="Host / IP", anchor="w")
        self.remote_tree.heading("port", text="Port", anchor="w")
        self.remote_tree.heading("username", text="Username", anchor="w")
        self.remote_tree.heading("password", text="Password", anchor="w")
        self.remote_tree.heading("ssh_key", text="SSH Key", anchor="w")

        self.remote_tree.column("name", width=150, minwidth=100)
        self.remote_tree.column("host", width=180, minwidth=100)
        self.remote_tree.column("port", width=60, minwidth=50)
        self.remote_tree.column("username", width=120, minwidth=80)
        self.remote_tree.column("password", width=100, minwidth=80)
        self.remote_tree.column("ssh_key", width=250, minwidth=150)

        remote_scrollbar = ttk.Scrollbar(remote_inner, orient=tk.VERTICAL, command=self.remote_tree.yview)
        self.remote_tree.configure(yscrollcommand=remote_scrollbar.set)

        self.remote_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        remote_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.remote_tree.bind("<Button-1>", self.on_remote_click)
        self.remote_tree.bind("<Double-1>", lambda e: self.connect_remote())
        self.remote_tree.bind("<Button-3>", self.on_remote_right_click)
        self.remote_tree.bind("<Return>", lambda e: self.connect_remote())
        self.remote_tree.bind("<Delete>", lambda e: self.delete_remote_profile())

        # Keyboard shortcuts
        self.root.bind("<F5>", lambda e: self.refresh_all())
        self.root.bind("<Control-n>", lambda e: self.new_window())
        self.root.bind("<Control-o>", lambda e: self.open_folder())
        self.root.bind("<Control-r>", lambda e: self.add_remote_profile())

    def draw_logo(self, canvas):
        """Draw premium VS Code-style logo"""
        # Background circle with gradient effect
        canvas.create_oval(2, 2, 43, 43, fill=Colors.ACCENT_PRIMARY, outline="")
        canvas.create_oval(5, 5, 40, 40, fill=Colors.BG_DARK, outline="")
        canvas.create_oval(7, 7, 38, 38, fill=Colors.ACCENT_PRIMARY, outline="")

        # Draw "V" shape
        canvas.create_polygon(
            16, 14,  # top left
            22, 30,  # bottom middle
            28, 14,  # top right
            25, 14,  # inner top right
            22, 26,  # inner bottom
            19, 14,  # inner top left
            fill=Colors.BG_DARK, outline=""
        )

    def refresh_all(self):
        """Refresh both lists"""
        self.refresh_list()
        self.refresh_remote_list()

    def refresh_list(self):
        """Refresh the instances list"""
        current_selection = self.tree.selection()
        if current_selection:
            item = self.tree.item(current_selection[0])
            if item["tags"]:
                self.selected_hwnd = int(item["tags"][0])

        for item in self.tree.get_children():
            self.tree.delete(item)

        instances = self.manager.refresh_instances()

        item_to_select = None
        for inst in instances:
            inst_type = "Remote" if inst.is_remote else "Local"
            item_id = self.tree.insert("", tk.END,
                                      values=(inst.pid, inst.workspace, inst_type, inst.title),
                                      tags=(str(inst.hwnd),))
            if self.selected_hwnd and inst.hwnd == self.selected_hwnd:
                item_to_select = item_id

        if item_to_select:
            self.tree.selection_set(item_to_select)
            self.tree.focus(item_to_select)
            self.tree.see(item_to_select)

        self.status_var.set(f"{len(instances)} instance(s) running  |  Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def refresh_remote_list(self):
        """Refresh the remote profiles list"""
        for item in self.remote_tree.get_children():
            self.remote_tree.delete(item)

        profiles = self.manager.get_remote_profiles()
        for i, profile in enumerate(profiles):
            masked_pwd = "*" * min(len(profile.password), 8) if profile.password else "-"
            ssh_key_display = os.path.basename(profile.ssh_key) if profile.ssh_key else "-"

            self.remote_tree.insert("", tk.END,
                                   values=(profile.name, profile.host, profile.port,
                                          profile.username, masked_pwd, ssh_key_display),
                                   tags=(str(i),))

    def get_selected_instance(self, show_warning=True):
        """Get currently selected instance"""
        selection = self.tree.selection()
        if not selection:
            if show_warning:
                messagebox.showwarning("No Selection", "Please select an instance first.")
            return None

        item = self.tree.item(selection[0])
        if not item["tags"]:
            return None
        hwnd = int(item["tags"][0])

        for inst in self.manager.instances:
            if inst.hwnd == hwnd:
                return inst

        self.manager.refresh_instances()
        for inst in self.manager.instances:
            if inst.hwnd == hwnd:
                return inst
        return None

    def get_selected_remote_profile(self, show_warning=True):
        """Get currently selected remote profile"""
        selection = self.remote_tree.selection()
        if not selection:
            if show_warning:
                messagebox.showwarning("No Selection", "Please select a remote profile first.")
            return None, -1

        item = self.remote_tree.item(selection[0])
        if not item["tags"]:
            return None, -1

        index = int(item["tags"][0])
        profiles = self.manager.get_remote_profiles()
        if 0 <= index < len(profiles):
            return profiles[index], index
        return None, -1

    def add_remote_profile(self):
        """Add a new remote profile"""
        dialog = RemoteProfileDialog(self.root, title="Add Remote Profile")
        if dialog.result:
            self.manager.add_remote_profile(dialog.result)
            self.refresh_remote_list()
            self.status_var.set(f"Profile added: {dialog.result.name}")

    def edit_remote_profile(self):
        """Edit selected remote profile"""
        profile, index = self.get_selected_remote_profile()
        if profile:
            dialog = RemoteProfileDialog(self.root, profile=profile, title="Edit Remote Profile")
            if dialog.result:
                self.manager.update_remote_profile(index, dialog.result)
                self.refresh_remote_list()
                self.status_var.set(f"Profile updated: {dialog.result.name}")

    def delete_remote_profile(self):
        """Delete selected remote profile"""
        profile, index = self.get_selected_remote_profile()
        if profile:
            if messagebox.askyesno("Delete Profile", f"Delete '{profile.name}'?\n\nThis action cannot be undone."):
                self.manager.delete_remote_profile(index)
                self.refresh_remote_list()
                self.status_var.set(f"Profile deleted: {profile.name}")

    def connect_remote(self):
        """Connect to selected remote profile"""
        profile, _ = self.get_selected_remote_profile()
        if profile:
            result = self.manager.open_remote(profile)
            if result == True:
                self.status_var.set(f"Connecting to {profile.username}@{profile.host}...")
                self.root.after(2000, self.refresh_list)
            else:
                messagebox.showerror("Connection Error", f"Failed to connect:\n{result}")

    def connect_remote_path(self):
        """Connect to remote profile with specific path"""
        profile, _ = self.get_selected_remote_profile()
        if profile:
            remote_path = simpledialog.askstring("Remote Path",
                                                f"Enter remote path on {profile.host}:",
                                                initialvalue=f"/home/{profile.username}",
                                                parent=self.root)
            if remote_path:
                result = self.manager.open_remote(profile, remote_path)
                if result == True:
                    self.status_var.set(f"Connecting to {profile.host}:{remote_path}...")
                    self.root.after(2000, self.refresh_list)
                else:
                    messagebox.showerror("Connection Error", f"Failed to connect:\n{result}")

    def copy_ssh_command(self):
        """Copy SSH command to clipboard"""
        profile, _ = self.get_selected_remote_profile()
        if profile:
            if profile.ssh_key:
                cmd = f'ssh -i "{profile.ssh_key}" -p {profile.port} {profile.username}@{profile.host}'
            else:
                cmd = f'ssh -p {profile.port} {profile.username}@{profile.host}'

            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            self.status_var.set("SSH command copied to clipboard")

    def open_folder(self):
        """Open a folder in new VS Code instance"""
        folder = filedialog.askdirectory(title="Select Folder to Open in VS Code")
        if folder:
            result = self.manager.open_workspace(folder)
            if result == True:
                self.status_var.set(f"Opening: {os.path.basename(folder)}")
                self.root.after(1500, self.refresh_list)
            else:
                messagebox.showerror("Error", f"Failed to open VS Code:\n{result}")

    def new_window(self):
        """Open new empty VS Code window"""
        result = self.manager.open_new_window()
        if result == True:
            self.status_var.set("Opening new window...")
            self.root.after(1500, self.refresh_list)
        else:
            messagebox.showerror("Error", f"Failed to open VS Code:\n{result}")

    def focus_selected(self):
        """Focus selected instance"""
        instance = self.get_selected_instance()
        if instance:
            self.manager.focus_instance(instance)
            self.status_var.set(f"Focused: {instance.workspace}")

    def minimize_selected(self):
        """Minimize selected instance"""
        instance = self.get_selected_instance()
        if instance:
            self.manager.minimize_instance(instance)
            self.status_var.set(f"Minimized: {instance.workspace}")

    def maximize_selected(self):
        """Maximize selected instance"""
        instance = self.get_selected_instance()
        if instance:
            self.manager.maximize_instance(instance)
            self.status_var.set(f"Maximized: {instance.workspace}")

    def restore_selected(self):
        """Restore selected instance"""
        instance = self.get_selected_instance()
        if instance:
            self.manager.restore_instance(instance)
            self.status_var.set(f"Restored: {instance.workspace}")

    def close_selected(self):
        """Close selected instance"""
        instance = self.get_selected_instance()
        if instance:
            if messagebox.askyesno("Close Instance", f"Close '{instance.workspace}'?"):
                self.manager.close_instance(instance)
                self.status_var.set(f"Closed: {instance.workspace}")
                self.root.after(500, self.refresh_list)

    def minimize_all(self):
        """Minimize all instances"""
        self.manager.minimize_all()
        self.status_var.set("All instances minimized")
        self.refresh_list()

    def close_all(self):
        """Close all instances"""
        count = len(self.manager.instances)
        if count > 0 and messagebox.askyesno("Close All", f"Close all {count} VS Code instance(s)?"):
            self.manager.close_all()
            self.status_var.set("All instances closed")
            self.root.after(500, self.refresh_list)

    def auto_refresh(self):
        """Auto-refresh every 3 seconds"""
        self.refresh_list()
        self.root.after(3000, self.auto_refresh)

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    if os.name != 'nt':
        print("This tool is designed for Windows OS.")
        print("For Linux/Mac, you would need different window management APIs.")
        return

    app = VSCodeManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
