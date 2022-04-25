import PySimpleGUI as sg
import subprocess, shlex

theme = "LightGreen1"

data = []

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        elif output:
            window.write_event_value("-stdout-", output.decode())

def list_packages():
    global data
    data = []
    output_ = subprocess.run(["pip", "list"], capture_output=True, shell=True).stdout.decode()
    installed = output_.split("\n")[2:-1]
    for package in installed:
        name, version = package.split(" ")[0], package.split(" ")[-1]
        data.append([name, version])
        #print(name, version)
    window["-installed-"].update(data)

def create_window(theme):
    sg.theme(theme)
    layout = [
        [sg.Push(), sg.Text("Python Package Installer", font=(sg.DEFAULT_FONT, 20)), sg.Push()],
        [sg.Text("Theme: "), sg.Combo(sg.theme_list(), theme, readonly=True, key="-theme-", enable_events=True)],
        [sg.Column([
            [sg.Frame("Install", [
                [sg.Text("Package name:"), sg.Input(expand_x=True, key="-name-", enable_events=True)],
                [sg.Text("Package version:"), sg.Combo([">=", "==", "<=", "~="], "==", key="-sign-", disabled=True, readonly=True), sg.Input(expand_x=True, key="-version-", enable_events=True)],
                [sg.Text("Additional arguments:"), sg.Input(expand_x=True, key="-args-")],
                [sg.Checkbox("Requirements file:", key="-need-req-file-", enable_events=True), sg.Input(disabled=True, expand_x=True, key="-req-file-", enable_events=True), sg.FileBrowse(target="-req-file-", key="-browse-", disabled=True)],
                [sg.Button("Install package", disabled=True, key="-install-")]
            ], expand_x=True)],
            [
                sg.Frame("Manage packages", [
                    [sg.Table(data, headings=["Name", "Version"], expand_x=True, expand_y=True, key="-installed-", select_mode=sg.TABLE_SELECT_MODE_EXTENDED)],
                    [sg.Button("Update table", key="-update-", tooltip="pip list\nUpdate the table"), sg.Button("Uninstall", key="-uninstall-"), sg.Button("Package information", key="-get-info-")],
                    [sg.Button("Check dependency compatibilities", tooltip="pip check\nVerify if all installed packages have compatible dependencies", key="-check-dep-")]
                ], expand_x=True, expand_y=True),
                sg.Frame("Output", [
                    [sg.Multiline(expand_x=True, expand_y=True, disabled=True, key="-output-", autoscroll=True, right_click_menu=["", ["&Copy"]], font=sg.DEFAULT_FONT, horizontal_scroll=True)],
                    [sg.Checkbox("Use monospace font", key="-monospace-", enable_events=True), sg.Push(), sg.Button("Clear output")]
                ], expand_x=True, expand_y=True),
            ],
        ], expand_x=True, expand_y=True)],
        [sg.Text(key="-status-")]
    ]
    return sg.Window("Python Package Installer", layout=layout, finalize=True, resizable=True)

window = create_window(theme)
list_packages()

while 1:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == "-stdout-":
        window["-output-"].print(values["-stdout-"], end="")
    elif event == "-theme-":
        theme = values["-theme-"]
        window.close()
        del window
        window = create_window(theme)
    elif event == "-update-":
        window["-update-"].update(disabled=True)
        window["-status-"].update(value="Updating table...")
        window.start_thread(list_packages, "-pkg-list-")
    elif event == "-pkg-list-":
        window["-status-"].update(value="")
        window["-update-"].update(text="Update table", disabled=False)
    elif event in ("-need-req-file-", "-name-", "-req-file-"):
        window["-name-"].update(disabled=values["-need-req-file-"])
        window["-version-"].update(disabled=values["-need-req-file-"])
        window["-req-file-"].update(disabled=not values["-need-req-file-"])
        window["-browse-"].update(disabled=not values["-need-req-file-"])
        if not values["-need-req-file-"]:
            if values["-name-"].strip():
                window["-install-"].update(disabled=False)
            else: window["-install-"].update(disabled=True)
        else:
            if values["-req-file-"].strip():
                window["-install-"].update(disabled=False)
            else: window["-install-"].update(disabled=True)
    elif event == "-version-":
        if values["-version-"].strip():
            window["-sign-"].update(disabled=False)
        else:
            window["-sign-"].update(disabled=True)
    elif event == "-install-":
        window["-install-"].update(disabled=True)
        window["-status-"].update(value="Installing...")
        args = filter(lambda s: s, [
            values["-name-"] + (values["-sign-"] + values["-version-"] if values["-version-"].strip() else "") if not values["-need-req-file-"] else "",
            "-r" if values["-need-req-file-"] else "", values["-req-file-"] if values["-need-req-file-"] else "",
            *(shlex.split(values["-args-"]) if values["-args-"].strip() else "")
        ])
        window["-output-"].update(disabled=False)
        window["-output-"].update(value="")
        window.start_thread(lambda: run_command(["pip", "install", *args]), "-install-done-")
    elif event == "-install-done-":
        window["-output-"].update(disabled=True)
        window["-status-"].update(value="")
        if not values["-need-req-file-"]:
            window["-install-"].update(disabled=not values["-name-"].strip())
        else:
            window["-install-"].update(disabled=not values["-req-file-"].strip())
        window.write_event_value("-update-", None)
    elif event == "-uninstall-":
        window["-output-"].update(disabled=False)
        window["-output-"].update(value="")
        if values["-installed-"] == []:
            window["-output-"].print("You haven't selected a package.")
            window["-output-"].update(disabled=True)
        else:
            window["-uninstall-"].update(disabled=True)
            window["-status-"].update(value="Uninstalling...")
            packages = map(lambda idx: data[idx][0], values["-installed-"])
            window.start_thread(lambda: run_command(["pip", "uninstall", "-y", *packages]), "-uninstall-done-")
    elif event == "-uninstall-done-":
        window["-output-"].update(disabled=True)
        window["-status-"].update(value="")
        window["-uninstall-"].update(text="Uninstall", disabled=False)
        window.write_event_value("-update-", None)
    elif event == "-get-info-":
        window["-output-"].update(disabled=True)
        window["-output-"].update("")
        if values["-installed-"] == []:
            window["-output-"].update("You haven't selected a package.")
        else:
            window["-get-info-"].update(disabled=True)
            window["-status-"].update(value="Loading...")
            for package in values["-installed-"]:
                name = data[package][0]
                window.start_thread(lambda: (name, subprocess.run(["pip", "show", name], capture_output=True, shell=True).stdout.decode().strip()), "-pkg-info-")
        window["-output-"].update(disabled=True)
    elif event == "-pkg-info-":
        window["-output-"].print(f"Information of package {values[event][0]}", font=(sg.DEFAULT_FONT, 15, "bold"))
        window["-output-"].print(values["-pkg-info-"][1])
        window["-status-"].update(value="")
        window["-get-info-"].update(text="Package information", disabled=False)
    elif event == "-check-dep-":
        window["-check-dep-"].update(disabled=True)
        window["-status-"].update(value="Loading...")
        window["-output-"].update(disabled=False)
        window["-output-"].update(value="")
        window.start_thread(lambda: subprocess.run(["pip", "check"], capture_output=True, shell=True).stdout.decode().strip(), "-ver-dep-")
    elif event == "-ver-dep-":
        window["-output-"].print(values[event])
        window["-output-"].update(disabled=True)
        window["-status-"].update(value="")
        window["-check-dep-"].update(text="Check dependency compatibilities", disabled=False)
    elif event == "-monospace-":
        window["-output-"].update(font=("Courier" if values["-monospace-"] else sg.DEFAULT_FONT[0], sg.DEFAULT_FONT[1]))
    elif event == "Copy":
        sg.clipboard_set(values["-output-"])
    elif event == "Clear output":
        window["-output-"].update(value="")
