import os
import time
import subprocess
import sys
import platform

def setup_startup():
    if platform.system() != "Windows":
        return
    try:
        script_path = os.path.abspath(__file__)
        task_name = "greenworm"
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", task_name],
            capture_output=True
        )
        if result.returncode == 0:
            print("Startup task already exists")
            return
        cmd = [
            "schtasks", "/Create", "/TN", task_name,
            "/TR", f'"{sys.executable}" "{script_path}"',
            "/SC", "ONLOGON", "/RL", "HIGHEST", "/F"
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"Added {script_path} to startup via Task Scheduler")
    except Exception as e:
        print(f"Failed to setup startup: {e}")

def get_removable_drives():
    drives = []
    system = platform.system()
    
    if system == "Windows":
        try:
            import win32file
            import win32api
            drive_list = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            for drive in drive_list:
                try:
                    drive_type = win32file.GetDriveType(drive)
                    if drive_type == win32file.DRIVE_REMOVABLE:
                        drives.append(drive.rstrip('\\'))
                except:
                    pass
        except ImportError:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    path = f"{letter}:\\"
                    if os.path.exists(path):
                        drive_type = kernel32.GetDriveTypeW(ctypes.c_wchar_p(path))
                        if drive_type == 2:  # DRIVE_REMOVABLE
                            drives.append(path)
            except:
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    path = f"{letter}:\\"
                    if os.path.exists(path):
                        drives.append(path)
    elif system == "Linux":
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) > 1 and ('/media/' in parts[1] or '/mnt/' in parts[1]):
                        path = parts[1]
                        if os.path.ismount(path):
                            drives.append(path)
        except:
            pass
    elif system == "Darwin":
        try:
            result = subprocess.run(['ls', '/Volumes'], capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line and line not in ['Macintosh HD']:
                    drives.append(f'/Volumes/{line}')
        except:
            pass
    
    return drives

def run_autorun(drive_path):
    autorun_py = os.path.join(drive_path, 'autorun.py')
    autorun_exe = os.path.join(drive_path, 'autorun.exe')
    
    if os.path.exists(autorun_py):
        try:
            print(f"Running {autorun_py}")
            subprocess.Popen([sys.executable, autorun_py])
        except Exception as e:
            print(f"Failed to run autorun.py: {e}")
    elif os.path.exists(autorun_exe):
        try:
            print(f"Running {autorun_exe}")
            subprocess.Popen([autorun_exe])
        except Exception as e:
            print(f"Failed to run autorun.exe: {e}")

def main():
    setup_startup()
    known_drives = set(get_removable_drives())
    print(f"Monitoring for USB/SD card insertion... Known drives: {known_drives}")
    
    while True:
        current_drives = set(get_removable_drives())
        new_drives = current_drives - known_drives
        
        for drive in new_drives:
            print(f"New drive detected: {drive}")
            run_autorun(drive)
        
        known_drives = current_drives
        time.sleep(2)

if __name__ == "__main__":
    main()
