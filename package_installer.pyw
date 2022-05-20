import PySimpleGUI as sg
import subprocess, shlex, re

data = []

config = {
    "theme": "DarkGrey15",
    "pip": "pip",
    "confirm-uninstall": True,
    "xscroll": False,
    "show-handle": True,
    "flat-scrollbars": False
}

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        elif output:
            main_window.write_event_value("-stdout-", output.decode())

def list_packages():
    global data
    data = []
    output_ = subprocess.run([config["pip"], "list"], capture_output=True, shell=True).stdout.decode()
    if re.match(r"Package\s*Version\s*\n\-+\s\-+", output_) is None:
        main_window.hide()
        choice, _ = sg.Window("Error", [
            [sg.Text("Cannot get the list of packages.")],
            [sg.Text("Make sure that the command have been configured properly.")],
            [sg.Text("Current pip command: " + config["pip"])],
            [sg.Button("Configure command"), sg.Button("Retry")]
        ], disable_close=True).read(close=True)
        if choice == "Configure command":
            main_window.write_event_value("Settings", True)
        else:
            main_window.un_hide()
            list_packages()
        return
    installed = output_.splitlines()[2:-1]
    for package in installed:
        name, version = package.split(" ")[0], package.split(" ")[-1]
        data.append([name, version])
        #print(name, version)
    main_window["-installed-"].update(data)

def create_main_window():
    sg.theme(config["theme"])
    layout = [
        [sg.Push(), sg.Text("Python Package Installer", font=(sg.DEFAULT_FONT, 20)), sg.Push()],
        [sg.Frame("Install", [
            [sg.Text("Package name:"), sg.Input(expand_x=True, key="-name-", enable_events=True)],
            [sg.Text("Package version:"), sg.Combo([">=", "==", "<=", "~="], "==", key="-sign-", readonly=True), sg.Input(expand_x=True, key="-version-", enable_events=True)],
            [sg.Text("Additional arguments:"), sg.Input(expand_x=True, key="-args-")],
            [sg.Checkbox("Requirements file:", key="-need-req-file-", enable_events=True), sg.Input(disabled=True, expand_x=True, key="-req-file-", enable_events=True), sg.FileBrowse(target="-req-file-", key="-browse-", disabled=True)],
            [sg.Button("Install package", disabled=True, key="-install-")]
        ], expand_x=True)],
        [sg.Pane([
            sg.Column([[sg.Frame("Manage packages", [
                [sg.Table(data, headings=["Name", "Version"], expand_x=True, expand_y=True, key="-installed-", select_mode=sg.TABLE_SELECT_MODE_EXTENDED)],
                [sg.Button("Update table", key="-update-", tooltip=f"{config['pip']} list\nUpdate the table"), sg.Button("Uninstall", key="-uninstall-"), sg.Button("Package information", key="-get-info-")],
                [sg.Button("Check dependency compatibilities", tooltip=f"{config['pip']} check\nVerify if all installed packages have compatible dependencies", key="-check-dep-"), sg.Button("Manage package wheels")]
            ], expand_x=True, expand_y=True)]]),
            sg.Column([[sg.Frame("Output", [
                [sg.Multiline(expand_x=True, expand_y=True, disabled=True, key="-output-", autoscroll=True, right_click_menu=["", ["&Copy output"]], font=sg.DEFAULT_FONT, horizontal_scroll=config["xscroll"])],
                [sg.Checkbox("Use monospace font", key="-monospace-", enable_events=True), sg.Push(), sg.Button("Clear output")]
            ], expand_x=True, expand_y=True)]]),
        ], expand_x=True, expand_y=True, orientation="horizontal", relief="flat", pad=0, show_handle=config["show-handle"])],
        [sg.Text(key="-status-", expand_x=True), sg.Button("Settings"), sg.Quit()]
    ]
    window = sg.Window("Python Package Installer", layout=layout, finalize=True, resizable=True, sbar_relief="flat" if config["flat-scrollbars"] else None)
    return window

def create_settings_window(not_cancellable):
    layout = [
        [sg.Text("Theme"), sg.Combo(sg.theme_list(), config["theme"], key="-theme-", enable_events=True, readonly=True)],
        [sg.Text("Configure pip command"), sg.Input(config["pip"], key="-pip-", enable_events=True)],
        [sg.Text("This app will use the command you specified. For example:"), sg.Text(f"{config['pip']} install SomePackage", font=("Courier", sg.DEFAULT_FONT[1]), key="-example-")],
        [sg.Checkbox("Show confirmation before uninstalling packages", config["confirm-uninstall"], key="-confirm-uninstall-")],
        [sg.Checkbox("Enable horizontal scrolling for output", config["xscroll"], key="-xscroll-")],
        [sg.Checkbox("Show resize handle (the little square between the two bottom columns)", config["show-handle"], key="-pane-handle-")],
        [sg.Checkbox("Use flat scrollbars", config["flat-scrollbars"], key="-flat-scroll-")],
        [sg.Button("Save", disabled=not_cancellable), sg.Cancel(disabled=not_cancellable), sg.Quit()]
    ]
    window = sg.Window("Settings", layout=layout, finalize=True, modal=True, disable_minimize=True, disable_close=not_cancellable)
    return window

def create_manage_wheel_window():
    pip = config["pip"]
    caches = []
    data = subprocess.run([pip, "cache", "list"], capture_output=True, shell=True).stdout.decode().splitlines()[2:]
    print(data)
    caches = list(map(lambda d: [" ".join(d.split(" ")[2:-2]), " ".join(d.split(" ")[-2:])], data))
    print(caches)
    layout = [
        [sg.Text("Cache location: " + subprocess.run([pip, "cache", "dir"], capture_output=True, shell=True).stdout.decode().strip())],
        [sg.Table(caches, headings=["Cache name", "Size"], num_rows=10, expand_x=True)],
        [sg.Button("Delete cache")]
    ]
    window = sg.Window("Manage wheel cache", layout=layout, finalize=True, modal=True)
    return window

main_window = create_main_window()
list_packages()

while 1:
    window, event, values = sg.read_all_windows()
    if window is None: break
    if event in (sg.WIN_CLOSED, "Cancel"):
        window.close()
    if event == "Quit":
        window.close()
        if window != main_window: main_window.close()
        break
    elif event == "Settings":
        settings_window = create_settings_window(not_cancellable=values.get(event))
    elif event == "-stdout-":
        main_window["-output-"].print(values["-stdout-"], end="")
    elif event == "Save":
        old_command = config["pip"]
        if values["-pip-"].strip() == "":
            sg.popup("Command cannot be blank", title="Error")
            continue
        settings_window.close()
        config = {
            "theme": values["-theme-"],
            "pip": values["-pip-"].strip(),
            "confirm-uninstall": values["-confirm-uninstall-"],
            "xscroll": values["-xscroll-"],
            "show-handle": values["-pane-handle-"],
            "flat-scrollbars": values["-flat-scroll-"]
        }
        output = main_window["-output-"].get()
        main_window.close()
        del main_window
        main_window = create_main_window()
        main_window["-output-"].update(value=output)
        if old_command != config["pip"]:
            list_packages()
        main_window.force_focus()
    elif event == "-pip-":
        window["-example-"].update(values[event].strip() + " install SomePackage")
        if window["Quit"].visible:
            window["Save"].update(disabled=config["pip"] == values[event])
    elif event == "-update-":
        main_window["-update-"].update(disabled=True)
        main_window["-status-"].update(value="Updating table...")
        main_window.start_thread(list_packages, "-pkg-list-")
    elif event == "-pkg-list-":
        main_window["-status-"].update(value="")
        main_window["-update-"].update(text="Update table", disabled=False)
    elif event in ("-need-req-file-", "-name-", "-req-file-"):
        main_window["-name-"].update(disabled=values["-need-req-file-"])
        main_window["-version-"].update(disabled=values["-need-req-file-"])
        main_window["-req-file-"].update(disabled=not values["-need-req-file-"])
        main_window["-browse-"].update(disabled=not values["-need-req-file-"])
        if not values["-need-req-file-"]:
            if values["-name-"].strip():
                main_window["-install-"].update(disabled=False)
            else: main_window["-install-"].update(disabled=True)
        else:
            if values["-req-file-"].strip():
                main_window["-install-"].update(disabled=False)
            else: main_window["-install-"].update(disabled=True)
    elif event == "-install-":
        main_window["-install-"].update(disabled=True)
        main_window["-status-"].update(value="Installing...")
        args = filter(lambda s: s, [
            values["-name-"] + (values["-sign-"] + values["-version-"] if values["-version-"].strip() else "") if not values["-need-req-file-"] else "",
            "-r" if values["-need-req-file-"] else "", values["-req-file-"] if values["-need-req-file-"] else "",
            *(shlex.split(values["-args-"]) if values["-args-"].strip() else "")
        ])
        main_window["-output-"].update(disabled=False)
        main_window["-output-"].update(value="")
        main_window.start_thread(lambda: run_command([config["pip"], "install", *args]), "-install-done-")
    elif event == "-install-done-":
        main_window["-output-"].update(disabled=True)
        main_window["-status-"].update(value="")
        if not values["-need-req-file-"]:
            main_window["-install-"].update(disabled=not values["-name-"].strip())
        else:
            main_window["-install-"].update(disabled=not values["-req-file-"].strip())
        main_window.write_event_value("-update-", None)
    elif event == "-uninstall-":
        main_window["-output-"].update(disabled=False)
        main_window["-output-"].update(value="")
        if values["-installed-"] == []:
            main_window["-output-"].print("You haven't selected a package.")
            main_window["-output-"].update(disabled=True)
        else:
            if config["confirm-uninstall"]:
                if sg.popup_ok_cancel("Are you sure you want to uninstall these packages?", title="Uninstall?") != "OK":
                    continue
            main_window["-uninstall-"].update(disabled=True)
            main_window["-status-"].update(value="Uninstalling...")
            packages = map(lambda idx: data[idx][0], values["-installed-"])
            main_window.start_thread(lambda: run_command([config["pip"], "uninstall", "-y", *packages]), "-uninstall-done-")
    elif event == "-uninstall-done-":
        main_window["-output-"].update(disabled=True)
        main_window["-status-"].update(value="")
        main_window["-uninstall-"].update(text="Uninstall", disabled=False)
        main_window.write_event_value("-update-", None)
    elif event == "-get-info-":
        main_window["-output-"].update(disabled=True)
        main_window["-output-"].update("")
        if values["-installed-"] == []:
            main_window["-output-"].update("You haven't selected a package.")
        else:
            main_window["-get-info-"].update(disabled=True)
            main_window["-status-"].update(value="Loading...")
            for package in values["-installed-"]:
                name = data[package][0]
                main_window.start_thread(lambda: (name, subprocess.run([config["pip"], "show", name], capture_output=True, shell=True).stdout.decode().strip()), "-pkg-info-")
        main_window["-output-"].update(disabled=True)
    elif event == "-pkg-info-":
        main_window["-output-"].print(f"Information of package {values[event][0]}", font=(sg.DEFAULT_FONT, 15, "bold"))
        main_window["-output-"].print(values["-pkg-info-"][1])
        main_window["-status-"].update(value="")
        main_window["-get-info-"].update(text="Package information", disabled=False)
    elif event == "-check-dep-":
        main_window["-check-dep-"].update(disabled=True)
        main_window["-status-"].update(value="Loading...")
        main_window["-output-"].update(disabled=False)
        main_window["-output-"].update(value="")
        main_window.start_thread(lambda: subprocess.run([config["pip"], "check"], capture_output=True, shell=True).stdout.decode().strip(), "-ver-dep-")
    elif event == "-ver-dep-":
        main_window["-output-"].print(values[event])
        main_window["-output-"].update(disabled=True)
        main_window["-status-"].update(value="")
        main_window["-check-dep-"].update(text="Check dependency compatibilities", disabled=False)
    elif event == "-monospace-":
        main_window["-output-"].update(font=("Courier" if values["-monospace-"] else sg.DEFAULT_FONT[0], sg.DEFAULT_FONT[1]))
    elif event == "Copy":
        sg.clipboard_set(values["-output-"])
    elif event == "Clear output":
        main_window["-output-"].update(value="")
    elif event == "Manage package wheels":
        cache_window = create_manage_wheel_window()
