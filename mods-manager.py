import PySimpleGUI as sg
from PySimpleGUI import TABLE_SELECT_MODE_BROWSE
import urllib.request
import urllib.error
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
from datetime import date
import os
import sys
import webbrowser
import shutil
import json
import textwrap
import requests
import vdf
import winreg

print('============SETUP...============')
global setup

# Get settings
meb_folder = os.getenv('APPDATA').replace('Roaming', r'LocalLow\Minskworks\Meb')
ms_lls_path = os.getenv('APPDATA').replace('Roaming', r'LocalLow\Minskworks\LandlordsSuper')
if not os.path.isdir(meb_folder):
    try:
        print('Settings not founded, creating settings')
        os.mkdir(meb_folder)
        meb_folder = meb_folder + r'\LandlordsSuper'
        os.mkdir(meb_folder)
    except FileNotFoundError:
        sg.Window("There is no Minskworks folder", [[sg.Text(f"{ms_lls_path} not found :/")]]).read()
        sys.exit()

    try:
        urllib.request.urlretrieve('https://raw.githubusercontent.com/MeblIkea/Water-Launcher/main/logo.ico',
                                   rf'{meb_folder}\icon.ico')
    except urllib.error.URLError:
        os.rmdir(meb_folder)
        urlerror = sg.Window('Error', [[sg.Text('urllib error: Maybe certificate error')]])
        urlerror.read()

    with open(rf'{meb_folder}\settings.json', 'w') as file:
        settings = {'lls_dir': None, 'theme': 'DarkBlue'}
        json.dump(settings, file)
else:
    meb_folder = meb_folder + r'\LandlordsSuper'
    with open(rf'{meb_folder}\settings.json', 'r') as file:
        settings = json.load(file)
    # Check if everything is in order
    if not os.path.isfile(meb_folder + r'\icon.ico'):
        try:
            urllib.request.urlretrieve('https://raw.githubusercontent.com/MeblIkea/Water-Launcher/main/logo.ico',
                                       rf'{meb_folder}\icon.ico')
        except urllib.error.URLError:
            os.rmdir(meb_folder)
            urlerror = sg.Window('Error', [[sg.Text('urllib error: Maybe certificate error')]])
            urlerror.read()

# Set some settings
sg.theme(settings.get('theme'))
sg.SetGlobalIcon(rf'{meb_folder}\icon.ico')
print('Settings loaded\nTheme set\nGetting Latest infos')
info = requests.get('https://pastebin.com/raw/YyDne6X9').json()
version = "1.0.2"
today = date.today()
win_y = 209
print(f'Latest: {info.get("version")}, Current: {version}')

# Setup Layout & Setup
setup_layout = [[sg.Text("Put bellow your Landlord's Super directory (press default if not changed)")],
                [sg.Input('', enable_events=True, size=55, key='Directory'), sg.FolderBrowse()],
                [sg.Button('Default'), sg.Text("This directory don't exist", key='Dir_adv', text_color='red')],
                [sg.Button('Set', disabled=True, key='Set'), sg.Button('Close')]]


def find_steam_lls():
    lls_dir = None
    _hkcu_steam = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
    _steampath, _steampathtype = winreg.QueryValueEx(_hkcu_steam, "SteamPath")
    winreg.CloseKey(_hkcu_steam)
    if _steampathtype == winreg.REG_SZ:
        _lfvdf = open(os.path.join(_steampath, 'config', 'libraryfolders.vdf'))
        _libraryfolders = vdf.parse(_lfvdf)
        for key in _libraryfolders['libraryfolders']:
            if '1127840' in _libraryfolders['libraryfolders'][key]['apps']:
                lls_dir = os.path.join(_libraryfolders['libraryfolders'][key]['path'], 'steamapps', 'common',
                                       "Landlord's Super")
    return lls_dir


# Don't prompt for the directory if the Steam Library scan works, cleaner startup
if settings.get('lls_dir') is None:
    print('Checking Steam location')

    _lls_dir = find_steam_lls()
    if _lls_dir is not None:
        if os.path.isfile(rf"{_lls_dir}\LandlordsSuper.exe"):
            with open(rf'{meb_folder}\settings.json', 'w') as file:
                settings = {'lls_dir': _lls_dir, 'theme': settings.get('theme')}
                json.dump(settings, file)

if settings.get('lls_dir') is None:
    print('Launching Setup')
    setup = sg.Window('Setup', setup_layout, size=(480, 160))
    while setup:
        event, values = setup.read()
        if event == 'Default':
            values['Directory'] = find_steam_lls() or ""
            setup['Directory'].update(values['Directory'])
        try:
            if os.path.isfile(rf"{values.get('Directory')}\LandlordsSuper.exe"):
                setup['Dir_adv'].update("This directory exist, and is Landlord's Super", text_color='lime')
                setup['Set'].update(disabled=False)
            elif os.path.isdir(values.get('Directory')):
                setup['Dir_adv'].update("This directory exist, but isn't Landlord's Super", text_color='yellow green')
                setup['Set'].update(disabled=False)
            else:
                setup['Dir_adv'].update("This directory don't exist", text_color='red')
                setup['Set'].update(disabled=True)
        except TypeError:
            pass
        if event == 'Set':
            if os.path.isdir(values.get('Directory')):
                with open(rf'{meb_folder}\settings.json', 'w') as file:
                    settings = {'lls_dir': values.get('Directory'), 'theme': settings.get('theme')}
                    json.dump(settings, file)
                setup.close()
                break
        if event == sg.WIN_CLOSED or event == 'Close':
            sys.exit()

# Get mods names & download links
print('-Getting Mods')
mods = {}
mods_requests = requests.get('https://api.github.com/users/Moojuiceman-LSMods/repos').json()
for x in mods_requests:
    description = requests.get(f'https://raw.githubusercontent.com/Moojuiceman-LSMods/{x.get("name")}/master/README.md')
    description = description.text.split('#### ')[1].replace('What it does\n\n', '')
    description = textwrap.fill(description, 54)
    if x == mods_requests[len(mods_requests) - 1]:
        print(f'  └--→ {x.get("name")}')
    else:
        print(f'  ├--→ {x.get("name")}')
    mods[x.get('name')] = {'dl_url': f'https://github.com/Moojuiceman-LSMods/{x.get("name")}/releases/latest/download'
                                     f'/{x.get("name")}.dll', 'description': description}

# Check if main mod is already install
if os.path.isdir(rf'{settings.get("lls_dir")}\BepInEx'):
    install_mod = [[sg.Text("Main mod is installed", text_color='lime', key='Is_Mod_installed')],
                   [sg.Button('Install', key='Install_main_mod', disabled=True), sg.Text('State: '),
                    sg.Text('Nothing to do.', key='state')],
                   [sg.Button('Uninstall', key='Uninstall_main_mod')]]
    main_mod_install = True
else:
    install_mod = [
        [sg.Text("Main mod is not installed", text_color='red', key='Is_Mod_installed')],
        [sg.Button('Install', key='Install_main_mod'), sg.Text('State:'),
         sg.Text('Waiting...', key='state')],
        [sg.Button('Uninstall', key='Uninstall_main_mod', disabled=True)]]
    main_mod_install = False
print(f'Main mod install: {main_mod_install}')

# Check if some mods are already install
mods_installed = []
for x in mods:
    if os.path.isfile(rf"{settings.get('lls_dir')}\BepInEx\plugins\{x}.dll"):
        mods_installed.append([x, 'Yes'])
    else:
        mods_installed.append([x, 'No'])

# Menus

if version == info.get('version'):
    stbar = sg.Text('')
    print('Menu is updated')
else:
    stbar = sg.StatusBar(f'*OUTDATED* Current version: {version}, Latest version: {info.get("version")}',
                         text_color='red', enable_events=True, key='outdated_clicked')
    win_y += 18
    print('Menu is outdated')

mod_browser = [
    [sg.Col([[sg.Table(mods_installed, ['Mod name', 'Is Installed'], auto_size_columns=True, enable_events=True,
                       key='Mods_list', select_mode=TABLE_SELECT_MODE_BROWSE, justification='left')]]),
     sg.Col([[sg.Text('Selected:')],
             [sg.Text('None', key='Selected_label')],
             [sg.Button('Description', key='Mod_description', disabled=True)],
             [sg.Button('Install', key='Mod_install', disabled=True)]])]]

if info.get('version') != version:
    update_scroll = ['Updates', ['Open updates manager']]
else:
    update_scroll = [' ', [' ']]
mod_manager = [[sg.MenubarCustom([['Main', ['Play!', 'Manage Themes', 'Reset this software', 'Exit']],
                                  ['About', ["Minskworks Discord", "Moojuiceman's Repo", 'Water Launcher Repo']],
                                  update_scroll])],
               [sg.TabGroup([[sg.Tab('Main Mod', install_mod), sg.Tab('Browser Mods', mod_browser,
                                                                      key='Browse-mod_tab')]],
                            size=(480, 130))],
               [stbar]]

window = sg.Window('Water Launcher!', mod_manager, default_element_size=(12, 1), size=(500, win_y))
print('Layouts sets\n\n============LAUNCHING...============')

while True:
    event, values = window.read()
    print(event, values)
    # Exit
    if event == sg.WIN_CLOSED or event == 'Exit' or event is None:
        window.close()
        sys.exit()

    window.set_title(values.get(0))  # Set good window title
    # Game tab
    if event == 'Reset this software':
        shutil.rmtree(os.getenv('APPDATA').replace('Roaming', r'LocalLow\Minskworks\Meb'))
        rs_software = sg.Window('Software has been reset!', [[sg.Text('This software has been reset.')],
                                                             [sg.Text('You can close this window!')]],
                                size=(200, 75))
        rs_software.read()
        rs_software.close()
        sys.exit()
    if event == 'Play!':
        os.popen(rf'{settings.get("lls_dir")}\LandlordsSuper.exe')

    # Updates manager
    if event == 'outdated_clicked' or event == 'Open updates manager':
        installer_layout = [[sg.Text('How to update:')], [sg.Button('Project Page', key='repo')], [sg.Button('Close')]]
        installer_window = sg.Window('Updates', installer_layout, size=(250, 100))
        while True:
            event, values = installer_window.read()

            if event == sg.WIN_CLOSED or event == 'Close':
                installer_window.close()
                break
            if event == 'repo':
                webbrowser.open('https://github.com/MeblIkea/Water-Launcher')

    # Change theme
    if event == 'Manage Themes':
        theme_layout = [[sg.Text('Put your theme name here:')],
                        [sg.Input('', key='Theme_input')],
                        [sg.Button('Set theme'), sg.Button('List themes'), sg.Text('', key='Theme_error')],
                        [sg.Button('Close'), sg.Button('Exit', key='Theme_exit')]]
        theme_window = sg.Window('Theme selector', theme_layout, size=(400, 130))
        while True:
            values: object
            event, values = theme_window.read()
            if event == 'List themes':
                sg.theme_previewer()
            if event == 'Set theme':
                if theme_window['Theme_input'].get() in sg.theme_list():
                    with open(rf'{meb_folder}\settings.json', 'w') as file:
                        settings = {'lls_dir': settings.get('lls_dir'), 'theme': theme_window['Theme_input'].get()}
                        json.dump(settings, file)
                    theme_window['Theme_error'].update("Theme set, now you click Exit", text_color='lime')
                    theme_window['Theme_exit'].update(button_color='green')
                else:
                    theme_window['Theme_error'].update("This theme don't exist", text_color='red')
            if event == sg.WIN_CLOSED or event == 'Close':
                theme_window.close()
                break
            if event == 'Theme_exit':
                sys.exit()
    # Install mod
    if event == 'Mod_install':
        mod_name = mods_installed[values.get('Mods_list')[0]][0]
        if mods_installed[values.get('Mods_list')[0]][1] == 'No':  # Install Mod
            url = mods.get(mod_name).get('dl_url')
            urllib.request.urlretrieve(url, rf'{settings.get("lls_dir")}\BepInEx\plugins\{mod_name}.dll')
            mods_installed[values.get('Mods_list')[0]] = [mod_name, 'Yes']
            window['Mod_install'].update('Remove')
        # Remove Mod
        else:
            os.remove(rf'{settings.get("lls_dir")}\BepInEx\plugins\{mod_name}.dll')
            if os.path.isfile(rf'{settings.get("lls_dir")}\BepInEx\config\{mod_name}.cfg'):
                os.remove(rf'{settings.get("lls_dir")}\BepInEx\config\{mod_name}.cfg')
            mods_installed[values.get('Mods_list')[0]] = [mod_name, 'No']
        window['Mods_list'].update(mods_installed)
    # Selected mod
    try:
        if len(values.get('Mods_list')) != 0:
            mod_name = mods_installed[values.get('Mods_list')[0]][0]
            window['Selected_label'].update(mod_name)
            if main_mod_install is True:
                window['Mod_install'].update(disabled=False)
                window['Mod_description'].update(disabled=False)
                if mods_installed[values.get('Mods_list')[0]][1] == 'Yes':
                    window['Mod_install'].update('Remove')
                else:
                    window['Mod_install'].update('Install')
            window.set_title('Mods Manager')
    except TypeError:
        pass
    if event == 'Mod_description':
        mod_name = mods_installed[values.get('Mods_list')[0]][0]
        description_window = sg.Window('Description', [[sg.Text(mod_name)],
                                                       [sg.Text(mods.get(mod_name).get('description'),
                                                                size=(350, 150), auto_size_text=True)]],
                                       size=(350, 45 + len(mods.get(mod_name).get('description').split('\n')) * 16))
        description_window.read()
    # Install main mod
    if event == 'Install_main_mod':
        window['state'].update('Installing BepInEx 5.4.19.0')
        window.read(timeout=0)
        http_response = urlopen('https://github.com/BepInEx/BepInEx/releases/download/v5.4.19/BepInEx_x64_5.4.19.0.zip')
        window['state'].update('Extracting...')
        window.read(timeout=0)
        zipfile = ZipFile(BytesIO(http_response.read()))
        zipfile.extractall(path=meb_folder + r'\BepInEx')
        for x in os.listdir(meb_folder + r'\BepInEx'):
            x = fr'\{x}'
            shutil.move(meb_folder + r'\BepInEx' + x, settings.get('lls_dir'))
        window['state'].update('Setup the main mod...')
        window.read(timeout=0)
        os.mkdir(rf"{settings.get('lls_dir')}\BepInEx\plugins")
        os.mkdir(rf"{settings.get('lls_dir')}\BepInEx\config")
        window['state'].update('Nothing to do.')
        window['Install_main_mod'].update(disabled=True)
        window['Uninstall_main_mod'].update(disabled=False)
        window['Is_Mod_installed'].update("Main mod is installed", text_color='lime')
        main_mod_install = True
    # Uninstall main mod
    if event == 'Uninstall_main_mod':
        shutil.rmtree(rf"{settings.get('lls_dir')}\BepInEx")
        os.remove(rf"{settings.get('lls_dir')}\changelog.txt")
        os.remove(rf"{settings.get('lls_dir')}\doorstop_config.ini")
        os.remove(rf"{settings.get('lls_dir')}\winhttp.dll")
        window['state'].update('Waiting...')
        window['Install_main_mod'].update(disabled=False)
        window['Uninstall_main_mod'].update(disabled=True)
        window['Is_Mod_installed'].update("Main mod is not installed", text_color='red')
        main_mod_install = False
        nmods_installed = []
        for x in mods_installed:
            nmods_installed.append([x[0], 'No'])
        mods_installed = nmods_installed
        window['Mods_list'].update(mods_installed)

    # Info
    if event == 'Minskworks Discord':
        webbrowser.open('https://discord.gg/A253AkJ2qv')
    if event == "Moojuiceman's Repo":
        webbrowser.open('https://github.com/orgs/Moojuiceman-LSMods/repositories')
    if event == 'Mod Manager Repo':
        webbrowser.open('https://github.com/MeblIkea/Water-Launcher')
