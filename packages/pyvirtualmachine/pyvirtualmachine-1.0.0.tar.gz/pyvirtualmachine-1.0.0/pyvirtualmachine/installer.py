import subprocess
import platform
import os
import urllib.request

def is_virtualbox_installed():
    try:
        subprocess.run(["VBoxManage", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def install_virtualbox():
    if is_virtualbox_installed():
        print("VirtualBox is already installed.")
        return True

    system = platform.system()
    if system == "Windows":
        url = "https://download.virtualbox.org/virtualbox/7.0.10/VirtualBox-7.0.10-158379-Win.exe"
        installer_path = os.path.join(os.getcwd(), "VBoxInstaller.exe")
        urllib.request.urlretrieve(url, installer_path)
        subprocess.run([installer_path, "/S"], check=True)
        os.remove(installer_path)
    elif system == "Darwin":
        print("Download VirtualBox DMG manually from: https://www.virtualbox.org/wiki/Downloads")
    elif system == "Linux":
        print("Use your package manager to install VirtualBox (e.g., sudo apt install virtualbox)")
    else:
        print(f"Unsupported OS: {system}")
        return False

    return is_virtualbox_installed()
