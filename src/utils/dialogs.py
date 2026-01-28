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
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Tkinter 루트 윈도우 생성 (숨김 상태)
        root = tk.Tk()
        root.withdraw()
        
        # 항상 위로 설정 (브라우저 뒤에 숨는 문제 해결)
        root.wm_attributes('-topmost', 1)
        
        # 폴더 선택 대화상자 호출
        folder_path = filedialog.askdirectory(master=root)
        
        # 정리
        root.destroy()
        return folder_path
    except Exception:
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
