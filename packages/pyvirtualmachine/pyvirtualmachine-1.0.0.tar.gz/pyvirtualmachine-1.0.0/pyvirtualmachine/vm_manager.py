import subprocess
import os

def create_vm(name, iso_path, ram_mb=1024, disk_mb=20000):
    subprocess.run(["VBoxManage", "createvm", "--name", name, "--register"])
    subprocess.run(["VBoxManage", "modifyvm", name, "--memory", str(ram_mb), "--acpi", "on", "--boot1", "dvd"])
    vdi_path = os.path.join(os.getcwd(), f"{name}.vdi")
    subprocess.run(["VBoxManage", "createhd", "--filename", vdi_path, "--size", str(disk_mb)])
    subprocess.run(["VBoxManage", "storagectl", name, "--name", "SATA Controller", "--add", "sata", "--controller", "IntelAhci"])
    subprocess.run(["VBoxManage", "storageattach", name, "--storagectl", "SATA Controller", "--port", "0", "--device", "0", "--type", "hdd", "--medium", vdi_path])
    subprocess.run(["VBoxManage", "storageattach", name, "--storagectl", "SATA Controller", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", iso_path])

def start_vm(name):
    subprocess.run(["VBoxManage", "startvm", name])

def stop_vm(name):
    subprocess.run(["VBoxManage", "controlvm", name, "acpipowerbutton"])
