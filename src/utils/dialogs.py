import platform
import subprocess
import os

def select_folder():
    """
    Opens a native folder selection dialog based on the OS.
    Returns the selected folder path or None if cancelled/failed.
    """
    system_os = platform.system()
    
    if system_os == "Windows":
        return _select_folder_windows()
    elif system_os == "Darwin":
        return _select_folder_mac()
    else:
        # Linux or other: Not fully implemented, return None or use a fallback if needed
        return None

def _select_folder_windows():
    cmd = [
        "powershell",
        "-Command",
        "Add-Type -AssemblyName System.Windows.Forms; $dialog = New-Object System.Windows.Forms.FolderBrowserDialog; $result = $dialog.ShowDialog(); if ($result -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dialog.SelectedPath }"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        path = result.stdout.strip()
        return path if path else None
    except subprocess.CalledProcessError:
        return None

def _select_folder_mac():
    script = 'choose folder with prompt "설교 데이터 폴더를 선택하세요"'
    cmd = ['osascript', '-e', f'POSIX path of ({script})']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        path = result.stdout.strip()
        return path if path else None
    except subprocess.CalledProcessError:
        return None
