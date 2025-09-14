import PySimpleGUI as sg
from .installer import install_virtualbox
from .vm_manager import create_vm, start_vm

def main():
    if not install_virtualbox():
        print("VirtualBox is required to run VMs.")
        return

    layout = [
        [sg.Text("VM Name"), sg.Input(key="-NAME-")],
        [sg.Text("ISO Path"), sg.Input(key="-ISO-"), sg.FileBrowse(file_types=(("ISO Files", "*.iso"),))],
        [sg.Text("RAM (MB)"), sg.Input("1024", key="-RAM-")],
        [sg.Button("Create and Start VM")]
    ]

    window = sg.Window("PyVirtualMachine", layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == "Create and Start VM":
            create_vm(values["-NAME-"], values["-ISO-"], int(values["-RAM-"]))
            start_vm(values["-NAME-"])

    window.close()
