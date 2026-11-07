import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME_FILES = ("wc.py", "wcsg.py", "wc_config.json")

LAUNCHER = r'''
import os
import shutil
import subprocess
import sys

TITLE = __TITLE__
WINDOWED = __WINDOWED__
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def message(text):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, TITLE, 0x10)
    except Exception:
        print(text)


def works(command):
    try:
        result = subprocess.run(command + ["-c", "import sys"], capture_output=True,
                                timeout=20, creationflags=NO_WINDOW)
        return result.returncode == 0
    except Exception:
        return False


def find_python(base):
    candidates = []
    launcher = shutil.which("py")
    if launcher:
        candidates.append([launcher, "-3"])
    for name in ("python", "python3"):
        path = shutil.which(name)
        if path and "WindowsApps" not in path:
            candidates.append([path])
    bundled = os.path.join(base, "python_windows.exe")
    if os.path.exists(bundled):
        candidates.append([bundled])
    for command in candidates:
        if works(command):
            return command
    return None


def main():
    here = sys.executable if getattr(sys, "frozen", False) else __file__
    base = os.path.dirname(os.path.abspath(here))
    wc = os.path.join(base, "wc.py")
    start = os.path.join(base, "start.wc")
    if not (os.path.exists(wc) and os.path.exists(start)):
        message("Program files are missing: wc.py and start.wc must be next to this program.")
        return
    command = find_python(base)
    if command is None:
        message("Python is required, but not installed")
        return
    arguments = command + [wc, start] + ([] if WINDOWED else ["--pause"])
    subprocess.run(arguments, cwd=base, creationflags=NO_WINDOW if WINDOWED else 0)


main()
'''


def pause():
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


def choose_folder():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Choose the folder with your WC program")
    root.destroy()
    return folder


def uses_force_noecho(start_path):
    try:
        from wc import load_config
        word = load_config(os.path.dirname(start_path))["force_noecho"]
        with open(start_path, encoding="utf-8-sig") as f:
            return any(line.strip().startswith(word) for line in f)
    except Exception:
        return False


def prepare_release(folder):
    parent, name = os.path.split(os.path.abspath(folder).rstrip("\\/"))
    release = os.path.join(parent, name + "_release")
    shutil.copytree(folder, release, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for filename in RUNTIME_FILES:
        target = os.path.join(release, filename)
        source = os.path.join(HERE, filename)
        if not os.path.exists(target) and os.path.exists(source):
            shutil.copy2(source, target)
    return name, release


def build_exe(release, name, windowed, icon):
    if importlib.util.find_spec("PyInstaller") is None:
        print("Installing PyInstaller (one time only)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    work = tempfile.mkdtemp()
    try:
        launcher = os.path.join(work, "launcher.py")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write(LAUNCHER.replace("__TITLE__", repr(name)).replace("__WINDOWED__", repr(windowed)))
        command = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconfirm", "--clean",
                   "--name", name, "--distpath", release,
                   "--workpath", os.path.join(work, "build"), "--specpath", work]
        if windowed:
            command.append("--noconsole")
        if os.path.exists(icon):
            command += ["--icon", icon]
        subprocess.check_call(command + [launcher])
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = paths[0] if paths else choose_folder()
    if not folder or not os.path.isdir(folder):
        print("Drop a folder with your WC program onto this file.")
        return

    start = os.path.join(folder, "start.wc")
    if not os.path.exists(start):
        print("start.wc was not found in that folder. The .exe runs start.wc, so create it first.")
        return

    if "--noconsole" in flags:
        windowed = True
    elif "--console" in flags:
        windowed = False
    else:
        suggested = uses_force_noecho(start)
        hint = "Y/n" if suggested else "y/N"
        answer = input(f"Hide the console window in the .exe? Choose yes only if the program talks "
                       f"to the user through WCSG windows [{hint}]: ").strip().lower()
        windowed = suggested if not answer else answer.startswith("y")

    name, release = prepare_release(folder)
    if "--no-build" not in flags:
        print("Building the .exe, this takes a minute...")
        build_exe(release, name, windowed, os.path.join(folder, "icon.ico"))

    print(f"\nDone! Release folder: {release}")
    if not os.path.exists(os.path.join(release, "python_windows.exe")):
        print("There is no python_windows.exe inside, so the other PC needs Python installed.")
    else:
        print("python_windows.exe is inside, it will be used if the other PC has no Python.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"\nBuild failed: {error}")
    except Exception as error:
        print(f"\nError: {error}")
    pause()
