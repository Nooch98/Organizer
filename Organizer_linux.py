import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import git
import time
import webbrowser
import importlib
import tkinter as tk
import jedi
import markdown
import requests
import pygments.lexers
import platform
import subprocess
import ttkbootstrap as ttk
import markdown2
import re
import glob
import webview
#--------------------------------------------------------#
from tkinter import OptionMenu, StringVar, filedialog, simpledialog
from urllib.parse import urlparse
from tkinter import messagebox as ms
from tkinter import scrolledtext, PhotoImage
from bs4 import BeautifulSoup
from github import Auth, Github
from openai import OpenAI
from tkhtmlview import HTMLLabel
from ttkthemes import ThemedTk
from chlorophyll import CodeView
from pathlib import Path
from ttkbootstrap.constants import *
from git import Repo
from datetime import datetime
from PIL import Image, ImageTk
import xml.etree.ElementTree as ET

main_version = "ver.1.9.5"
version = str(main_version)
archivo_configuracion_editores = "configuracion_editores.json"
archivo_confgiguracion_github = "configuracion_github.json"
archivo_configuracion_gpt = "configuration_gpt.json"
BACKUP_STATE_FILE = "backup_schedule.json"
security_backup = "security_backup.json"
config_file = "config.json"
selected_project_path = None
text_editor = None
app_name = "./Organizer_linux"
exe_path = os.path.abspath(sys.argv[0])
current_version = "v1.9.5"
img = "software.png"

VCS_DIR = ".myvcs"
vcs_configfile = ".myvcs/config.json"
vcs_githubconfigfile = ".myvcs/github_config.json"
selected_file = None
file_name = None

def search_github_key():
    posible_name = ["GITHUB", "TOKEN", "API", "KEY", "SECRET"]
    for name_var, valor in os.environ.items():
        if any(clave in name_var.upper() for clave in posible_name):
            if is_github_token_valid(valor):
                return valor
            else:
                ms.showerror("ERROR", f"No github api key found in your environment variables. Please agree github api key to your enviroment variables with the name: {posible_name}")
                return None
    
    return None
            
def is_github_token_valid(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def obtain_github_user():
    url = "https://api.github.com/user"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        user = response.json()
        return user["login"]
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Can't obtain the github user: {str(e)}")

GITHUB_TOKEN = search_github_key()
GITHUB_USER = obtain_github_user()

def check_new_version():
    try:
        url = "https://api.github.com/repos/Nooch98/Organizer/releases/latest"

        response = requests.get(url)

        if response.status_code == 200:
            release_data = response.json()
            latest_version = release_data.get("tag_name")

            if latest_version:
                if latest_version > current_version:
                    quest = ms.askyesno("Update", f"Version {latest_version} of Organizer Available.\n You want install")
                    if quest:
                        assets = release_data.get("assets", [])
                        if not assets:
                            return "Can't found any file to download"
                        
                        selectd_asset = None
                        for asset in assets:
                            if asset["name"] == "Organizer_linux.zip":
                                selectd_asset = asset
                                break
                        if not selectd_asset:
                            return "Can't found the file Organizer_linux.zip"
                        asset_url = selectd_asset["browser_download_url"]
                        current_directory = os.getcwd()
                        file_path = os.path.join(current_directory, selectd_asset["name"])
                        download_response = requests.get(asset_url)
                        with open(file_path, "wb") as file:
                            file.write(download_response)
                        ms.showinfo("Update", "Closing Organizer to update")
                        subprocess.Popen("./updater_linux")
                        root.after(1000, root.destroy())
                    else:
                        pass
                else:
                    pass
            else:
                ms.showerror("ERROR", "Can't Obtain the last version")
        else:
            ms.showerror("ERROR", f"Can't Verify the version: {response.status_code}")
    except Exception as e:
        ms.showerror("ERROR", f"Can't verify the version: {str(e)}")

def obtener_carpeta_proyectos_app():
    # Obtener la ruta de la carpeta _internal/projects en el directorio de instalación de la app
    ruta_base_app = Path(__file__).parent  # Obtiene la ruta donde está instalada la app
    carpeta_proyectos = ruta_base_app / "_internal" / "projects"
    
    # Crear la carpeta si no existe
    carpeta_proyectos.mkdir(parents=True, exist_ok=True)
    
    return carpeta_proyectos

# Ejemplo de uso en la función de sincronización
def obtener_ruta_copia_proyecto(nombre_proyecto):
    carpeta_proyectos = obtener_carpeta_proyectos_app()
    ruta_copia = carpeta_proyectos / nombre_proyecto
    ruta_copia.mkdir(parents=True, exist_ok=True)  # Asegurarse de que la carpeta del proyecto existe
    return ruta_copia

def obtener_info_proyecto(id_proyecto):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    # Obtener ruta y nombre del proyecto de la tabla de proyectos
    cursor.execute("SELECT ruta, nombre FROM proyectos WHERE id=?", (id_proyecto,))
    resultado = cursor.fetchone()
    if resultado:
        ruta_usuario, nombre_proyecto = resultado
        ruta_copia = os.path.join("MisProyectos", nombre_proyecto)
        
        # Obtener estado de sincronización de la tabla estado_proyectos
        cursor.execute("SELECT abierto_editor, ultima_sincronizacion FROM estado_proyectos WHERE id_proyecto=?", (id_proyecto,))
        estado = cursor.fetchone() or (0, None)  # Estado por defecto si no existe
        
        conn.close()
        return ruta_usuario, ruta_copia, estado[0], estado[1]
    
    conn.close()
    return None, None, None, None

# Función para actualizar el estado de sincronización en la tabla estado_proyectos
def actualizar_estado_proyecto(id_proyecto, sincronizado):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    # Crear o actualizar registro en estado_proyectos
    cursor.execute("""
        INSERT INTO estado_proyectos (id_proyecto, abierto_editor, ultima_sincronizacion)
        VALUES (?, ?, ?)
        ON CONFLICT(id_proyecto) DO UPDATE SET
            abierto_editor = ?,
            ultima_sincronizacion = ?
    """, (id_proyecto, int(sincronizado), datetime.now(), int(sincronizado), datetime.now()))
    
    conn.commit()
    conn.close()
    
# Función para sincronizar proyectos que estaban abiertos en un editor al iniciar la app
def sincronizar_proyectos_abiertos():
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id_proyecto FROM estado_proyectos WHERE abierto_editor=1")
    proyectos_abiertos = cursor.fetchall()
    conn.close()
    
    for (id_proyecto,) in proyectos_abiertos:
        ruta_usuario, ruta_copia, _, ultima_sincronizacion = obtener_info_proyecto(id_proyecto)
        if ruta_usuario and ruta_copia:
            sincronizar_diferencial(ruta_usuario, ruta_copia, ultima_sincronizacion)
            # Marcar proyecto como cerrado después de la sincronización
            actualizar_estado_proyecto(id_proyecto, False)
            
def thread_sinc():
    threading.Thread(sincronizar_proyectos_abiertos()).start()
            
# Función para obtener la última sincronización desde la tabla estado_proyectos
def obtener_ultima_sincronizacion(id_proyecto):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ultima_sincronizacion FROM estado_proyectos WHERE id_proyecto=?", (id_proyecto,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None
        
# Sincronización diferencial según la última marca de tiempo registrada
def sincronizar_diferencial(origen, destino, ultima_sincronizacion):
    origen_path = Path(origen)
    destino_path = Path(destino)

    # Convertir última sincronización en datetime si existe
    ultima_sync_time = datetime.fromisoformat(ultima_sincronizacion) if ultima_sincronizacion else None

    for origen_archivo in origen_path.rglob('*'):
        destino_archivo = destino_path / origen_archivo.relative_to(origen_path)

        if origen_archivo.is_dir():
            destino_archivo.mkdir(parents=True, exist_ok=True)
        elif origen_archivo.is_file():
            if ultima_sync_time is None or datetime.fromtimestamp(origen_archivo.stat().st_mtime) > ultima_sync_time:
                shutil.copy2(origen_archivo, destino_archivo)

    # Borrar archivos en destino que no están en origen
    for destino_archivo in destino_path.rglob('*'):
        origen_archivo = origen_path / destino_archivo.relative_to(destino_path)
        if not origen_archivo.exists():
            if destino_archivo.is_file():
                destino_archivo.unlink()
            elif destino_archivo.is_dir():
                shutil.rmtree(destino_archivo)

def crear_base_datos():
    conn = sqlite3.connect('proyectos.db')
    
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        descripcion TEXT,
        lenguaje TEXT,
        ruta TEXT,
        repo TEXT
        )''')
    cursor.execute("CREATE TABLE IF NOT EXISTS estado_proyectos (id_proyecto INTEGER PRIMARY KEY, abierto_editor INTEGER DEFAULT 0, ultima_sincronizacion TEXT)")
    
    conn.close()
    
def get_projects_from_database():

    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos")
    projects = cursor.fetchall()

    conn.close()

    projects_list = []
    for project in projects:
        project_dict = {'nombre': project[1], 'ruta': project[4]}
        projects_list.append(project_dict)

    return projects_list
    
def insertar_proyecto(nombre, descripcion, ruta, repo, lenguaje=None):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO proyectos (nombre, descripcion, lenguaje, ruta, repo)
                   VALUES (?, ?, ?, ?, ?)''', (nombre, descripcion, lenguaje, ruta, repo))
    
    conn.commit()
    conn.close()
    mostrar_proyectos()

def save_backup_schedule(next_backup_time, frequency_seconds):
    with open(BACKUP_STATE_FILE, "w") as file:
        json.dump({
            "next_backup_time": next_backup_time.isoformat(),
            "frequency_seconds": frequency_seconds
        }, file)

def load_backup_schedule():
    if os.path.exists(BACKUP_STATE_FILE):
        with open(BACKUP_STATE_FILE, "r") as file:
            data = json.load(file)
            next_backup_time = datetime.datetime.fromisoformat(data["next_backup_time"])
            frequency_seconds = data["frequency_seconds"]
            return next_backup_time, frequency_seconds
    return None, None
 
def get_selected_frequency():
    selected_option = combo_frequency.get()
    
    if selected_option == "Daily":
        frequency_seconds = 24 * 3600
    elif selected_option == "Weekly":
        frequency_seconds = 7 * 24 * 3600
    elif selected_option == "Monthly":
        frequency_seconds = 30 * 24 * 3600
    else:
        frequency_seconds = 24 * 3600
    
    next_backup_time = datetime.datetime.now() + datetime.timedelta(seconds=frequency_seconds)
    save_backup_schedule(next_backup_time, frequency_seconds)
    schedule_backup(next_backup_time, frequency_seconds)
    
def backup_now():
    while True:
        backup_thread()

def schedule_backup(next_backup_time, frequency_seconds):
    def backup_scheduler():
        while True:
            now = datetime.datetime.now()
            if now >= next_backup_time:
                backup_thread()
                next_backup_time = now + datetime.timedelta(seconds=frequency_seconds)
                save_backup_schedule(next_backup_time, frequency_seconds)
            time.sleep(5)
            
    threading.Thread(target=backup_scheduler, daemon=True).start()

def perform_backup():
    backups_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
    shutil.copyfile("proyectos.db", os.path.join(backups_dir, "proyectos_backup.db"))
    
    projects = get_projects_from_database()
    
    for project in projects:
        project_name = project['nombre']
        project_path = project['ruta']
        project_backup_dir = os.path.join(backups_dir, project_name)
        
        if 'status_label' in globals():
                status_label.config(text=f"Backup -> {project_name} -> {project_path}")
        
        shutil.copytree(project_path, project_backup_dir, dirs_exist_ok=True)
        
        if 'status_label' in globals():
            status_label.config(text="Backup success")

def backup_thread():
    threading.Thread(target=perform_backup, daemon=True).start()
    
def initialize_backup_schedule():
    next_backup_time, frequency_seconds = load_backup_schedule()
    if next_backup_time and frequency_seconds:
        now = datetime.datetime.now()
        if now >= next_backup_time:
            backup_thread()
            next_backup_time = now + datetime.timedelta(seconds=frequency_seconds)
        schedule_backup(next_backup_time, frequency_seconds)
    else:
        pass

def detectar_editores_disponibles():
    # Lista de editores de texto comunes
    editores = {
        "Visual Studio Code": "code",
        "Sublime Text": "subl",
        "Atom": "atom",
        "Vim": "vim",
        "Emacs": "emacs",
        "Notepad++": "notepad++",
        "Brackets": "brackets",
        "TextMate": "mate",
        "Geany": "geany",
        "gedit": "gedit",
        "Nano": "nano",
        "Kate": "kate",
        "Bluefish": "bluefish",
        "Eclipse": "eclipse",
        "IntelliJ IDEA": "idea",
        "PyCharm": "pycharm",
        "Visual Studio": "devenv",
        "Code::Blocks": "codeblocks",
        "NetBeans": "netbeans",
        "Android Studio": "studio",
        "neovim": "nvim"
    }
    return {nombre: shutil.which(binario) for nombre, binario in editores.items() if shutil.which(binario)}

def abrir_editor(ruta, ruta_editor):
    subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
    
def setting_backup():
    backup = tk.Toplevel(root)
    backup.title("Setting Security Backup")
    backup.iconphoto(True, tk.PhotoImage(file=path))
    
    main_frame = ttk.Frame(backup)
    main_frame.pack()
    
    global combo_frequency
    global status_label
    
    frequency_options = ["Daily", "Weekly", "Monthly"]
    combo_frequency = ttk.Combobox(main_frame, values=frequency_options)
    combo_frequency.set("Daily")
    combo_frequency.grid(row=0, columnspan=2, padx=5, pady=5)
    
    status_label = ttk.Label(main_frame, text="")
    status_label.grid(row=1, columnspan=2, padx=5, pady=5)
    
    btn_confirm = ttk.Button(main_frame, text="Confirm", command=get_selected_frequency)
    btn_confirm.grid(row=2, column=0, padx=5, pady=5)
    
    btn_backup_now = ttk.Button(main_frame, text="Create Now", command=backup_now)
    btn_backup_now.grid(row=2, column=1, padx=5, pady=5)
    
def get_selected_frequency():
    selected_option = combo_frequency.get()
    
    if selected_option == "Daily":
        frequency_seconds = 24 * 3600
    elif selected_option == "Weekly":
        frequency_seconds = 7 * 24 * 3600
    elif selected_option == "Monthly":
        frequency_seconds = 30 * 24 * 3600
    else:
        frequency_seconds = 24 * 3600
        
    schedule_backup(frequency_seconds)
    
def backup_now():
    while True:
        perform_backup()

def schedule_backup(frequency_seconds):
    while True:
        perform_backup()
        time.sleep(frequency_seconds)

def perform_backup():
    backups_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
    shutil.copyfile("proyectos.db", os.path.join(backups_dir, "proyectos_backup.db"))
    
    projects = get_projects_from_database()
    
    for project in projects:
        project_name = project['nombre']
        project_path = project['ruta']
        project_backup_dir = os.path.join(backups_dir, project_name)
        
        if os.path.exists(project_backup_dir):
            shutil.rmtree(project_backup_dir)
        
        shutil.copytree(project_path, project_backup_dir)

def update_status(file_name):
    status_label.config(text="Copying: {}".format(file_name))

def abrir_proyecto(ruta, editor):
    configuracion_editores = cargar_configuracion_editores()
    ruta_editor = configuracion_editores.get(editor) if configuracion_editores and editor in configuracion_editores else None

    if not ruta_editor:
        editores_disponibles = detectar_editores_disponibles()
        ruta_editor = editores_disponibles.get(editor)

    if ruta_editor:
        subprocess.Popen([ruta_editor, ruta])
        subprocess.run(f"gnome-terminal -- bash -c 'cd {ruta} && exec bash'", shell=True)
    elif editor == "Editor Integrated":
        subprocess.Popen(f'gnome-terminal -- bash -c "cd {ruta} && exec bash"', shell=True)
        abrir_editor_thread(ruta, tree.item(tree.selection())['values'][1])

def abrir_editor_thread(ruta, name):
    threading.Thread(target=abrir_editor_integrado, args=(ruta, name)).start()

def abrir_editor_integrado(ruta_proyecto, nombre_proyecto):
    global current_file

    editor = ThemedTk()
    editor.title("Editor Integrated")
    editor.geometry("800x400")
    
    current_file = None
    tabs = ttk.Notebook(editor)
    tabs.pack(expand=True, fill="both", side="right")
    text_editors = []
    global_plugins = []
    code_themes_dir = Path("./_internal/chlorophyll/colorschemes/")
    tom_files = [archivo.stem for archivo in code_themes_dir.glob("*.toml")]
    
    selected_theme = ""
    
    def load_plugins():
        nonlocal  global_plugins
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        for plugin_file in os.listdir(plugins_dir):
            if plugin_file.endswith('.py'):
                plugin_name = os.path.splitext(plugin_file)[0]
                spec = importlib.util.spec_from_file_location(plugin_name, os.path.join(plugins_dir, plugin_file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for member_name in dir(module):
                    member = getattr(module, member_name)
                    if callable(member) and member_name.startswith("plugin_"):
                        global_plugins.append(member)
    
    load_plugins()
    
    def current_theme_get():
        return selected_theme
    
    def read_requiriments(file_path):
        dependencies = []
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                match = re.match(r'^\s*([a-zA-Z0-9_\-]+)', line)
                if match:
                    dependencies.append(match.group(1))

        return dependencies
    
    def read_rust_dependencies(file_path):
        if not os.path.exists(file_path):
            return []
        
        libraries = set()
        with open(file_path, 'r') as f:
            in_dependencies_section = False
            for line in f:
                # Detectar si estamos en la sección [dependencies]
                if line.strip() == "[dependencies]":
                    in_dependencies_section = True
                elif line.strip().startswith("[") and in_dependencies_section:
                    # Salir si encontramos otra sección
                    break
                elif in_dependencies_section:
                    match = re.match(r'^\s*([a-zA-Z0-9\-_]+)', line)
                    if match:
                        libraries.add(match.group(1))  # Solo el nombre

        return list(libraries)
    
    def read_csharp_dependencies(file_path):
        if not os.path.exists(file_path):
            return []
        
        try:
            # Parsear el XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Intentar obtener el espacio de nombres del archivo
            namespaces = {'msbuild': root.tag.split('}')[0].strip('{') if '}' in root.tag else ''}
            
            libraries = set()
            
            # Buscar todos los PackageReference con o sin espacio de nombres
            if namespaces['msbuild']:
                for package in root.findall(".//msbuild:PackageReference", namespaces):
                    name = package.get("Include")
                    if name:
                        libraries.add(name)
            else:
                for package in root.findall(".//PackageReference"):
                    name = package.get("Include")
                    if name:
                        libraries.add(name)
            
            return list(libraries)
        
        except ET.ParseError:
            ms.showerror('ERROR', "Error: Could not parse .csproj file. Make sure it is well formed.")
            return []
        except Exception as e:
            ms.showerror('ERROR', f"Error reading dependencies from .csproj file: {e}")
            return []
        
    def read_cmake_dependencies(file_path):
        if not os.path.exists(file_path):
            return []
        
        libraries = set()
        with open(file_path, 'r') as f:
            for line in f:
                match = re.match(r'^\s*find_package\(\s*([a-zA-Z0-9\-_]+)', line)
                if match:
                    libraries.add(match.group(1))  # Solo el nombre

        return list(libraries)
    
    def read_vcpkg_dependencies(file_path):
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data.get("dependencies", [])
    
    def load_dependencies():
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de dependencias")
        
        if file_path.endswith(".toml"):
            libraries = read_rust_dependencies(file_path)
            show_requiriments(libraries)
        elif file_path.endswith(".csproj"):
            libraries = read_csharp_dependencies(file_path)
            show_requiriments(libraries)
        elif file_path.endswith("CMakeLists.txt"):
            libraries = read_cmake_dependencies(file_path)
            show_requiriments(libraries)
        elif file_path.endswith(".json"):
            libraries = read_vcpkg_dependencies(file_path)
            show_requiriments(libraries)
        elif file_path.endswith(".txt"):
            libraries = read_requiriments(file_path)
            show_requiriments(libraries)
        else:
            libraries = []

    def show_requiriments(libraries):
        global var
        for widget in lib_frame.winfo_children():
            widget.destroy()

        num_columns = 4
        row = 0
        col = 0

        for lib in libraries:
            var = tk.BooleanVar(value=False)
            libraries_vars[lib] = var
            # Pasar el valor de `lib` a la lambda usando `lib=lib`
            checkbox = ttk.Checkbutton(
                lib_frame,
                text=lib,
                variable=var,
                command=lambda lib=lib: update_command_label(file_entry.get())
            )
            checkbox.grid(row=row, column=col, sticky="ew", padx=2, pady=2)

            col += 1
            if col >= num_columns:
                col = 0
                row += 1

    def get_compiler_command(file_path, libraries):
        if file_path.endswith(".csproj"):
            return ["dotnet", "build", file_path]
        elif file_path.endswith("Cargo.toml"):
            return ["cargo", "build", "--release", "--manifest-path", file_path]
        elif file_path.endswith("CMakeLists.txt"):
            build_dir = os.path.join(os.path.dirname(file_path), "build")
            os.makedirs(build_dir, exist_ok=True)
            return ["cmake", "-S", os.path.dirname(file_path), "-B", build_dir, "&&", "cmake", "--build", build_dir]
        elif file_path.endswith(".txt") or file_path.endswith(".json"):
            # Usa PyInstaller para archivos Python
            command = ["pyinstaller"]
            if onefile_var.get():
                command.append("--onefile")
            if noconsole_var.get():
                command.append("--noconsole")
            if icon_entry.get():
                command.extend(["--icon", icon_entry.get()])
            if output_entry.get():
                command.extend(["--distpath", output_entry.get()])
            
            # Agregar dependencias seleccionadas para ocultarlas como imports
            for lib in libraries:
                command.extend(["--hidden-import", lib])
            
            command.append(file_entry.get())  # Añadir el archivo .py principal
            return command
        else:
            raise ValueError("No se reconoce el tipo de archivo para compilación.")
        
    def convert_to_exe(file_path):
        global exe_path
        
        # Determinar la extensión del archivo
        file_extension = os.path.splitext(file_path)[1]

        # Comando a ejecutar basado en la extensión del archivo
        if file_extension == ".csproj":
            command = ["dotnet", "build", file_path]
        elif file_extension == ".rs":
            command = ["cargo", "build", "--release", "--manifest-path", file_path]
        elif file_extension == ".c" or file_extension == ".cpp":
            # Asumimos que hay un CMakeLists.txt en el mismo directorio
            build_dir = os.path.join(os.path.dirname(file_path), "build")
            os.makedirs(build_dir, exist_ok=True)
            command = ["cmake", "-S", os.path.dirname(file_path), "-B", build_dir]
            command.extend(["&&", "cmake", "--build", build_dir])
        elif file_extension == ".py":
            command = ["pyinstaller"]
            if onefile_var.get():
                command.append("--onefile")
            if noconsole_var.get():
                command.append("--noconsole")
            if icon_entry.get():
                command.extend(["--icon", icon_entry.get()])
            if output_entry.get():
                command.extend(["--distpath", output_entry.get()])
            
            for lib, var in libraries_vars.items():
                if var.get():
                    command.extend(["--hidden-import", lib])
            
            for additional_file in additional_files:
                dest = "."  # Usar el directorio actual como destino
                command.extend(["--add-data", f"{additional_file};{dest}"])
            
            command.append(file_path)  # Añadir el archivo .py principal
        else:
            ms.showerror("ERROR", "Tipo de archivo no soportado para compilación.")
            return

        def run_conversion():
            output_box.insert(tk.END, f"\nEjecuting {command}\n")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            output_box.insert(tk.END, "\nWait to finish...\n")

            for line in iter(process.stdout.readline, ""):
                output_box.insert(tk.END, line)
                output_box.see(tk.END)
                output_box.update()

            stderr_output, _ = process.communicate()
            if stderr_output:
                output_box.insert(tk.END, stderr_output)

            output_box.insert(tk.END, "\nCompilación Complete.\n")

            # Obtener el archivo .exe generado si es un proyecto Python
            if file_extension == ".py":
                base_filename = os.path.splitext(os.path.basename(file_path))[0]
                output_dir = output_entry.get() if output_entry.get() else os.getcwd()
                exe_path = os.path.join(output_dir, base_filename + ".exe")

            open_explorer_button.config(state=tk.NORMAL)
            clear_output.config(state=tk.NORMAL)

        conversion_thread = threading.Thread(target=run_conversion)
        conversion_thread.start()
        
    def open_explorer():
        if exe_path and os.path.exists(exe_path):
            os.startfile(os.path.dirname(exe_path))
        else:
            ms.showwarning("Warning", "No se encontró el archivo .exe.")

    def update_command_label(file_path):
        command = ["pyinstaller"]

        if onefile_var.get():
            command.append("--onefile")
        if noconsole_var.get():
            command.append("--noconsole")
        if icon_entry.get():
            command.extend(["--icon", icon_entry.get()])
        if output_entry.get():
            command.extend(["--distpath", output_entry.get()])
        
        for additional_file in additional_files:
            dest = "."
            command.extend(["--add-data", f"{additional_file};{dest}"])

        for lib, var in libraries_vars.items():
            if var.get():
                command.extend(["--hidden-import", lib])

        command.append(file_path)

        command_str = "Command: " + ' '.join(command)

        max_line_length = 80
        command_with_line_breaks = '\n'.join([command_str[i:i+max_line_length] for i in range(0, len(command_str), max_line_length)])
        
        command_label.config(text=command_with_line_breaks)

    def select_file():
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, file_path)
            update_command_label(file_path)

    def select_icon():
        icon_path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico")])
        if icon_path:
            icon_entry.delete(0, tk.END)
            icon_entry.insert(0, icon_path)
            update_command_label(file_entry.get())

    def select_output_directory():
        output_dir = filedialog.askdirectory()
        if output_dir:
            output_entry.delete(0, tk.END)
            output_entry.insert(0, output_dir)
            update_command_label(file_entry.get())

    def execute_conversion():
        file_path = file_entry.get()
        if not file_path:
            ms.showwarning("Warning", "Seleccione un archivo para convertir o compilar.")
            return

        output_box.delete(1.0, tk.END)
        threading.Thread(target=convert_to_exe, args=(file_path,), daemon=True).start()
            
    def clear_all():
        output_box.delete(1.0, tk.END)
        open_explorer_button.config(state=tk.DISABLED)
        clear_output.config(state=tk.DISABLED)
        
    def import_configuration():
        config_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if config_path:
            with open(config_path, 'r') as f:
                config = json.load(f)

            file_entry.delete(0, tk.END)
            file_entry.insert(0, config.get("file_path", ""))
            
            output_entry.delete(0, tk.END)
            output_entry.insert(0, config.get("output_dir", ""))
            
            icon_entry.delete(0, tk.END)
            icon_entry.insert(0, config.get("icon_path", ""))
            
            onefile_var.set(config.get("onefile", False))
            noconsole_var.set(config.get("noconsole", False))
            
            load_dependencies()
            
            for lib, var in libraries_vars.items():
                var.set(lib in config.get("libraries", []))
                
            additional_files.clear()
            additional_files.extend(config.get("additional_files", []))

            update_command_label(file_entry.get())
            
    def export_configuration():
        config = {
            "file_path": file_entry.get(),
            "output_dir": output_entry.get(),
            "icon_path": icon_entry.get(),
            "onefile": onefile_var.get(),
            "noconsole": noconsole_var.get(),
            "libraries": [lib for lib, var in libraries_vars.items() if var.get()],
            "additional_files": additional_files
        }

        config_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if config_path:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
    def add_additional_files():
        files = filedialog.askopenfilenames(title="Select adicional files")
        for file in files:
            additional_files.append(file)
        update_command_label(file_entry.get())
        
    def add_additional_folder():
        folder_path = filedialog.askdirectory(title="Select adicional folder")
        if folder_path:
            additional_files.append(folder_path)
        update_command_label(file_entry.get())

    def converter_options():
        global file_entry, lib_frame, libraries_vars, icon_entry, onefile_var, noconsole_var, output_box, output_entry, command_label, open_explorer_button, clear_output, additional_files
        print("iniciando...")
        converter = ThemedTk()
        converter.title("Compiler")
        
        op_menu = tk.Menu(converter)
        converter.config(menu=op_menu)
        
        file_menu = tk.Menu(op_menu, tearoff=0)
        op_menu.add_cascade(label="Files", menu=file_menu)
        file_menu.add_command(label="Import Config", command=import_configuration)
        file_menu.add_command(label="Export Config", command=export_configuration)
        file_menu.add_command(label="Load Requiriments", command=load_dependencies)
        
        under_frame = ttk.Frame(converter)
        under_frame.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        frame = ttk.Frame(under_frame)
        frame.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        lib_frame = ttk.Frame(under_frame)
        lib_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

        libraries_vars = {}
        additional_files = []

        file_label = ttk.Label(frame, text="Main File:")
        file_label.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        file_entry = ttk.Entry(frame, width=40)
        file_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        file_btn = ttk.Button(frame, text="Select", command=select_file)
        file_btn.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        output_label = ttk.Label(frame, text="Output Dir:")
        output_label.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        output_entry = ttk.Entry(frame, width=40)
        output_entry.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        output_btn = ttk.Button(frame, text="Select", command=select_output_directory)
        output_btn.grid(row=1, column=2, padx=2, pady=2, sticky="ew")

        icon_label = ttk.Label(frame, text="Select Icon:")
        icon_label.grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        icon_entry = ttk.Entry(frame, width=40)
        icon_entry.grid(row=2, column=1, padx=2, pady=2, sticky="ew")

        icon_btn = ttk.Button(frame, text="Select Icon", command=select_icon)
        icon_btn.grid(row=2, column=2, padx=2, pady=2, sticky="ew")

        add_files_label = ttk.Label(frame, text="Additional Files")
        add_files_label.grid(row=3, column=0, padx=2, pady=2, sticky="ew")
        
        add_files_btn = ttk.Button(frame, text="Add Files", command=add_additional_files)
        add_files_btn.grid(row=3, column=1, padx=2, pady=2, sticky="ew")
        
        add_folder_btn = ttk.Button(frame, text="Add Folder", command=add_additional_folder)
        add_folder_btn.grid(row=3, column=2, padx=2, pady=2, sticky="ew")
        
        command_label = ttk.Label(frame, text="Command: ")  # Corregido el nombre de la variable
        command_label.grid(row=4, columnspan=3, padx=2, pady=2, sticky="ew")

        onefile_var = tk.BooleanVar(value=False)
        onefile_check = ttk.Checkbutton(frame, text="Onefile", variable=onefile_var,
                                        command=lambda: update_command_label(file_entry.get()))
        onefile_check.grid(row=5, column=0, padx=2, pady=2, sticky="ew")

        noconsole_var = tk.BooleanVar(value=False)
        noconsole_check = ttk.Checkbutton(frame, text="Noconsole", variable=noconsole_var,
                                        command=lambda: update_command_label(file_entry.get()))
        noconsole_check.grid(row=5, column=1, padx=2, pady=2, sticky="ew")

        output_box = tk.Text(frame, height=15, width=80, wrap='word')
        output_box.grid(row=6, columnspan=3, padx=2, pady=2, sticky="ew")

        clear_output = ttk.Button(frame, text="Clear Output", command=clear_all, state=tk.DISABLED)
        clear_output.grid(row=7, column=0, padx=2, pady=2, sticky="ew")

        convert_btn = ttk.Button(frame, text="Convert Py to exe", command=execute_conversion)
        convert_btn.grid(row=7, column=1, padx=2, pady=2, sticky="ew")
        
        open_explorer_button = ttk.Button(frame, text="Abrir Carpeta", command=open_explorer, state=tk.DISABLED)
        open_explorer_button.grid(row=7, column=2, padx=2, pady=2, sticky="ew")

        converter.mainloop()
    
    def change_code_theme(theme_name):
        global selected_theme
        selected_theme = theme_name
        for text_editor in text_editors:
            text_editor.config(color_scheme=theme_name)
            gpt_response.config(color_scheme=theme_name)
            
            
    def create_code_theme():
        ruta_new_theme = ".\\_internal\\chlorophyll\\colorschemes\\"
        def save_theme(name):
            default_content = "// Add your theme here"
            with open(f"{ruta_new_theme}{name}.toml", "w+") as file:
                file.write(default_content)
            
            new_theme.destroy()
            open_theme_editor(name)
        
        def guardar_cambios1(text_editors, file_path, event=None):
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(text_editors.get(1.0, tk.END))
                    ms.showinfo("Theme Saved", f"Theme saved successfully")
                text_editors.edit_modified(False)
                global builtin_color_schemes
                code_themes_dir = Path(".\\_internal\\chlorophyll\\colorschemes\\")
                builtin_color_schemes = set([archivo.stem for archivo in code_themes_dir.glob("*.toml")])
                
                theme_code_menu.delete(0, tk.END)
                theme_code_menu.add_command(label='Create Code Theme', command=create_code_theme)
                for code_theme in builtin_color_schemes:
                    theme_code_menu.add_command(label=code_theme, command=lambda theme=code_theme: change_code_theme(theme))
            else:
                ms.showerror("ERROR", "Error: There is no open file to save changes.")

        def example_code_theme():
            theme_file_path = ".\\_internal\\chlorophyll\\colorschemes\\monokai.toml"

            try:
                with open(theme_file_path, "r") as file:
                    theme_code = file.read()
                return theme_code
            except FileNotFoundError:
                ms.showerror("ERROR", "Theme file nor found")
                return ""
        
        def open_theme_editor(name):
            global example_theme
            new_tab_window = tk.Toplevel(editor)
            new_tab_window.title(f"New Theme: {name}")
            
            example_view = ttk.Frame(new_tab_window)
            example_view.pack(side='right', fill="both", expand=True)
            
            new_tab_frame = ttk.Frame(new_tab_window)
            new_tab_frame.pack(side='left', fill="both", expand=True)
            new_theme_path = f"{ruta_new_theme}{name}.toml"
            
            lexer = pygments.lexers.get_lexer_for_filename(new_theme_path)
                   
            text_editors = CodeView(new_tab_frame, lexer=lexer, color_scheme=current_theme_get())
            text_editors.pack(fill="both", expand=True)
            
            title_example_theme = ttk.Label(example_view, text="Example Theme: monokai.toml", foreground="purple", font=("Arial", 12))
            title_example_theme.pack() 
            
            example_theme_label = CodeView(example_view, lexer=lexer, color_scheme=current_theme_get(), wrap="none")
            example_theme_label.pack(fill="both", expand=True)
    
            example_theme_content = example_code_theme()
            example_theme_label.insert("1.0", example_theme_content)
            with open(new_theme_path, "r") as file:
                content = file.read()
                text_editors.insert(tk.END, content)
            
            text_editors.bind("<KeyPress>", on_key_press)
            tabs.bind("<Button-2>", cerrar_pestaña)
            editor.bind("<Control-w>", cerrar_pestaña_activa)
            text_editors.bind("<Control-s>", lambda event, te=text_editors, fp=new_theme_path: guardar_cambios1(te, fp))
        
        new_theme = tk.Toplevel(editor)
        new_theme.title("New Code Theme")
        
        main_frame = ttk.Frame(new_theme)
        main_frame.pack()
        
        title = ttk.Label(main_frame, text="Name of the new theme:")
        title.grid(row=0, column=0, padx=5, pady=5)
        
        name = ttk.Entry(main_frame, width=50)
        name.grid(row=0, column=1, padx=5, pady=5)
        
        save = ttk.Button(main_frame, text="Save", command=lambda: save_theme(name.get()))
        save.grid(row=1, columnspan=2, padx=5, pady=5)
    
    def show_plugin_selector(plugins_list):
        plugin_selector = tk.Toplevel()
        plugin_selector.title("Plugin Selector")
        
        main_frame = ttk.Frame(plugin_selector)
        main_frame.pack()
        
        selected_plugins = []

        for plugin in plugins_list:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(main_frame, text=plugin.__name__, variable=var)
            cb.pack(anchor=tk.W)
            selected_plugins.append((plugin, var))

        def execute_selected_plugins():
            for plugin, var in selected_plugins:
                if var.get():
                    plugin()

        execute_button = ttk.Button(main_frame, text="Execute Selected Plugins", command=execute_selected_plugins)
        execute_button.pack()
    
    def guardar_cambios(event=None):
        global current_file
        if current_file:
            index = tabs.index(tabs.select())
            with open(current_file, "w", encoding="utf-8") as file:
                file.write(text_editors[index].get(1.0, tk.END).strip())
            text_editors[index].edit_modified(False)  # Restablecer la marca de modificación
        else:
            ms.showerror("ERROR", "Error: There is no open file to save changes.")
    
    def show_file_content(file_path):
        with open(file_path, "r") as file:
            content = file.read()
        return content
    
    def open_selected_file(event=None):
        global current_file
        item = tree.focus()
        if item:
            item_path = get_item_path(item)
            if os.path.isfile(item_path):
                current_file = item_path
                
                for i, editor_tab in enumerate(text_editors):
                    if tabs.tab(i, "text") == os.path.basename(item_path):
                        tabs.select(i)
                        return
                    
                with open(item_path, "r") as file:
                    content = file.read()

                    new_tab_frame = ttk.Frame(tabs)
                    tabs.add(new_tab_frame, text=current_file)
                    
                    lexer = pygments.lexers.get_lexer_for_filename(item_path)
                    text_editor = CodeView(new_tab_frame, lexer=lexer, color_scheme=current_theme_get())
                    text_editor.pack(fill="both", expand=True)
                    text_editor.insert(tk.END, content)
                    text_editors.append(text_editor)
                    text_editor.bind("<KeyPress>", on_key_press)
                    tabs.bind("<Button-2>", cerrar_pestaña)
                    editor.bind("<Control-w>", cerrar_pestaña_activa)
                    text_editor.bind("<Control-s>", lambda event: guardar_cambios())
    
    def get_item_path(item):
        item_path = tree.item(item, "text")
        parent_item = tree.parent(item)
        while parent_item:
            parent_name = tree.item(parent_item, "text")
            item_path = os.path.join(parent_name, item_path)
            parent_item = tree.parent(parent_item)
        return item_path
    
    def name_new_file():
        global filename
        global name
        
        name = tk.Toplevel(editor)
        name.title('New File')
        
        main_frame = ttk.Frame(name)
        main_frame.pack()
        
        label = ttk.Label(main_frame, text='Name of your new file: ')
        label.grid(row=0, column=0, padx=5, pady=5)
        
        filename = ttk.Entry(main_frame, width=50)
        filename.grid(row=0, column=1, padx=5, pady=5)
        
        subbmit = ttk.Button(main_frame, text='Acept', command=create_new_file)
        subbmit.grid(row=1, columnspan=2, padx=5, pady=5)
    
    def name_new_folder():
        global foldere
        global foldername
        
        foldername = tk.Toplevel(editor)
        foldername.title('New Folder')
        
        main_frame = ttk.Frame(foldername)
        main_frame.pack()
        
        label = ttk.Label(main_frame, text='Name of your new folder: ')
        label.grid(row=0, column=0, padx=5, pady=5)
        
        foldere = ttk.Entry(main_frame, width=50)
        foldere.grid(row=0, column=1, padx=5, pady=5)
        
        subbmit = ttk.Button(main_frame, text='Acept', command=create_new_folder)
        subbmit.grid(row=1, columnspan=2, padx=5, pady=5)        
        
    def create_new_file():
        folder = tree.focus()
        if folder:
            folder_path = get_item_path(folder)
            file = filename.get()
            if file:
                file_path = os.path.join(folder_path, file)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as file:
                    file.write("File create with Python Editor.")
                tree.insert(folder, 'end', text=file)
                editor.update()
        name.destroy()
    
    def create_new_folder():
        folder = tree.focus()
        if folder:
            parent_folder_path = get_item_path(folder)
        else:
            parent_folder_path = ruta_proyecto
            
        folder_name = foldere.get()
        if folder_name:
            folder_path = os.path.join(parent_folder_path, folder_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                tree.insert(folder, 'end', text=folder_name)
                editor.update()
                ms.showinfo("Folder Created", f'Folder created successfully: {folder_path}')
            except OSError as e:
                ms.showerror('ERROR', f'Error creating folder: {e}')
        foldername.destroy()
    
    def delete_file():
        selected_item = tree.focus()
        if selected_item:
            file_path = get_item_path(selected_item)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    tree.delete(selected_item)
                    ms.showinfo("File Deleted", f'{file_path}')
                except OSError as e:
                    ms.showerror('ERROR', f'Error deleting file: {e}')
            elif os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                    tree.delete(selected_item)
                    ms.showinfo("Folder Deleted", f'{file_path}')
                except OSError as e:
                    ms.showerror('ERROR', f'Error deleting folder: {e}')
            else:
                ms.showwarning('Warning', f'Selected item is neither a file nor a folder: {file_path}')
    
    def cerrar_pestaña(event):
        widget = event.widget
        tab_index = widget.index("@%s,%s" % (event.x, event.y))
        
        if tab_index is not None:
            current_editor = text_editors[tab_index]
            
            if hay_cambios_sin_guardar(current_editor):
                respuesta = ms.askyesno("SAVE CHANGES", "You want Save Changes")
                if respuesta:
                    guardar_antes_de_cerrar(current_editor)
                    widget.forget(tab_index)
                    del text_editors[tab_index]
                else:
                    widget.forget(tab_index)
                    del text_editors[tab_index]
                
    def cerrar_pestaña_activa(event=None):
        current_tab_index = tabs.index(tabs.select())
        current_editor = text_editors[current_tab_index]

        if hay_cambios_sin_guardar(current_editor):
            respuesta = ms.askyesno("SAVE CHANGES", "You want Save Changes")
            if respuesta:
                guardar_antes_de_cerrar(current_editor)
                tabs.forget(current_tab_index)
                del text_editors[current_tab_index]
            else:
                tabs.forget(current_tab_index)
                del text_editors[current_tab_index]
   
    def hay_cambios_sin_guardar(editor):
        return editor.edit_modified()

    def guardar_antes_de_cerrar(editor):
        guardar_cambios()
                
    def get_item_path(item):
        item_path = tree.item(item, "text")
        parent_item = tree.parent(item)
        while parent_item:
            parent_name = tree.item(parent_item, "text")
            item_path = os.path.join(parent_name, item_path)
            parent_item = tree.parent(parent_item)
        item_path = os.path.join(ruta_proyecto, item_path)
        return item_path
    
    def expand_folder(event=None):
        def open_file_from_subfolder(event):
            item = tree.focus()
            if item:
                file_path = tree.item(item, "text")
                if os.path.isfile(file_path):
                    open_selected_file(file_path)
                    show_file_content(file_path)
        
        item = tree.focus()
        if item:
            folder_name = tree.item(item, "text")
            folder_path = os.path.join(ruta_proyecto, folder_name)
            if os.path.isdir(folder_path):
                tree.delete(*tree.get_children(item))
                for sub_item in os.listdir(folder_path):
                    sub_item_path = os.path.join(folder_path, sub_item)
                    if os.path.isfile(sub_item_path):
                        tree.insert(item, "end", text=sub_item)
                    elif os.path.isdir(sub_item_path):
                        sub_folder_id = tree.insert(item, "end", text=sub_item, open=False)
                        tree.insert(sub_folder_id, "end", text="")
    
    def on_key_press(event):
        if event.keysym == "F1":
            activate_autocomplete()

    def activate_autocomplete():
        index = tabs.index(tabs.select())
        text_editor = text_editors[index]
        row, col = text_editor.index(tk.INSERT).split('.')
        current_line = text_editor.get(f'{row}.0', f'{row}.{col}')
        
        script = jedi.Script(current_line, path=current_file)
        completions = script.complete()
        
        if completions:
            suggestions = [completion.complete for completion in completions]
            show_autocomplete_menu(suggestions)
    
    def show_autocomplete_menu(suggestions):
        index = tabs.index(tabs.select())
        text_editor = text_editors[index]
        max_items = 10
        suggestions_to_show = suggestions[:max_items]

        if hasattr(text_editor, '_autocomplete_menu'):
            text_editor._autocomplete_menu.delete(0, tk.END)
        else:
            text_editor._autocomplete_menu = tk.Menu(text_editor, tearoff=0)
            text_editor._autocomplete_menu.bind('<Escape>', lambda event: text_editor._autocomplete_menu.delete(0, tk.END))

        for suggestion in suggestions_to_show:
            text_editor._autocomplete_menu.add_command(label=suggestion, command=lambda s=suggestion: insert_autocomplete(s))

        text_editor._autocomplete_menu.post(text_editor.winfo_pointerx(), text_editor.winfo_pointery())

        if len(suggestions) > max_items:
            text_editor.bind('<Down>', lambda event: scroll_autocomplete_menu(1, suggestions))
            text_editor.bind('<Up>', lambda event: scroll_autocomplete_menu(-1, suggestions))
        
    def scroll_autocomplete_menu(direction, suggestions):
        index = tabs.index(tabs.select())
        text_editor = text_editors[index]
        current_items = text_editor._autocomplete_menu.index(tk.END)
        first_visible_item = text_editor._autocomplete_menu.index(tk.ACTIVE)

        if direction == 1:
            if first_visible_item < current_items - 1:
                text_editor._autocomplete_menu.yview_scroll(1, "units")
        elif direction == -1:
            if first_visible_item > 0:
                text_editor._autocomplete_menu.yview_scroll(-1, "units")

    def insert_autocomplete(suggestion):
        index = tabs.index(tabs.select())
        text_editor = text_editors[index]
        current_pos = text_editor.index(tk.INSERT)

        text_editor.insert(current_pos, suggestion)
        
    def toggle_gpt_visibility(event=None):
        if gpt_frame.winfo_ismapped():
            gpt_frame.pack_forget()
        else:
            gpt_frame.pack(side="right", fill="both")
            
    def toggle_tree_visibility(event=None):
        if tree_frame.winfo_ismapped():
            tree_frame.pack_forget()
        else:
            tree_frame.pack(side="left", fill="both")
            
    def change_theme(theme_name):
        editor.set_theme(theme_name)
        
    def create_theme():
        comando = "python -m ttkbootstrap"
        
        subprocess.run(f'{comando}', shell=True)
        
        
    def answer_question():
        quest = user_quest.get()
        client = OpenAI(
            api_key=load_config_gpt()
            )
        
        respuesta = client.chat.completions.create(
            message =[
                {
                "role": "user",
                "content": f"{quest}"    
                }
            ],
            model = "gpt-3.5-turbo",
            )
        
        respuesta_texto = respuesta.choices[0].text.strip()

        gpt_response.delete(1.0, tk.END)
        gpt_response.insert(tk.END, respuesta_texto)
    
    def tree_popup(event):
        tree_menu.post(event.x_root, event.y_root)
       
    builtin_color_schemes = set(tom_files)
    menu_bar = tk.Menu(editor)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Save", command=guardar_cambios)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Compiler", command=converter_options)
    
    settings_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label='Settings', menu=settings_menu)
    themes_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_command(label='Plugins', command=lambda: show_plugin_selector(global_plugins))
    settings_menu.add_cascade(label='Theme', menu=themes_menu)
    for tema in temas:
        themes_menu.add_command(label=tema, command=lambda tema=tema: change_theme(tema))
    themes_menu.add_command(label='Create Theme', command=create_theme)
    theme_code_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label='Code Theme', menu=theme_code_menu)
    theme_code_menu.add_command(label='Create Code Theme', command=create_code_theme)
    for code_theme in builtin_color_schemes:
        theme_code_menu.add_command(label=code_theme, command=lambda theme=code_theme: change_code_theme(theme))
    editor.config(menu=menu_bar)

    gpt_frame = ttk.Frame(editor)
    
    gpt_response = CodeView(gpt_frame, color_scheme=current_theme_get())
    gpt_response.pack(fill='both', expand=True)
    
    send_quest = ttk.Button(gpt_frame, text="Submit", command=answer_question)
    send_quest.pack(side='bottom')
    
    user_quest = ttk.Entry(gpt_frame, width=50)
    user_quest.pack(fill='x', side='bottom')
    
    tree_frame = ttk.Frame(editor)
    tree_frame.pack(side="left", fill="both")

    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side="right", fill="y")

    tree_menu = tk.Menu(editor, tearoff=0)
    tree_menu.add_command(label="New File", command=name_new_file)
    tree_menu.add_command(label='New Folder', command=name_new_folder)
    tree_menu.add_command(label='Delete', command=delete_file)
    
    tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set)
    tree.pack(side="left", fill="both")
    tree_scroll.config(command=tree.yview)
    tree.bind("<<TreeviewSelect>>", open_selected_file)
    tree.heading("#0", text=nombre_proyecto)
    
    
    editor.bind("<Control-b>", toggle_tree_visibility)
    editor.bind("<Control-Tab>", lambda event: tabs.select((tabs.index(tabs.select()) + 1) % tabs.index("end")))
    editor.bind("<Control-Shift-Tab>", lambda event: tabs.select((tabs.index(tabs.select()) - 1) % tabs.index("end")))
    tree.bind("<<TreeviewOpen>>", expand_folder)
    editor.bind("<Control-q>", lambda event: editor.destroy())
    editor.bind("<Control-g>", toggle_gpt_visibility)
    tree.bind("<Button-3>", tree_popup)
    
    for item in os.listdir(ruta_proyecto):
        item_path = os.path.join(ruta_proyecto, item)
        if os.path.isfile(item_path):
            tree.insert("", "end", text=item)
        elif os.path.isdir(item_path):
            folder_id = tree.insert("", "end", text=item, open=False)
            tree.insert(folder_id, "end", text="")

    editor.mainloop()

def abrir_threading(ruta, editor):
    threading.Thread(target=abrir_proyecto, args=(ruta, editor)).start()
    
def mostrar_proyectos():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM proyectos')
    proyectos = cursor.fetchall()
    for proyecto in proyectos:
        tree.insert("", "end", values=proyecto)
        
    conn.close()
    
def agregar_proyecto_existente():
    descripcion = descripcion_entry.get()
    repo = repo_entry.get()
    ruta = filedialog.askdirectory()
    
    if ruta:
        nombre = os.path.basename(ruta)
        insertar_proyecto(nombre, descripcion, ruta, repo)
        descripcion_entry.delete(0, tk.END)
        repo_entry.delete(0, tk.END)

def crear_nuevo_proyecto():
    global new_description_entry, new_name_entry, ventana_lenguaje
    ventana_lenguaje = tk.Toplevel(root)
    ventana_lenguaje.title("Selection lenguaje")
    ventana_lenguaje.iconphoto(True, tk.PhotoImage(file=path))
    
    main_frame = ttk.Frame(ventana_lenguaje)
    main_frame.pack()
    
    new_name_label = ttk.Label(main_frame, text="Name")
    new_name_label.grid(row=0, columnspan=2, padx=2, pady=2, sticky="n")
    
    new_name_entry = ttk.Entry(main_frame, width=50)
    new_name_entry.grid(row=2, columnspan=2, padx=2, pady=2, sticky="ew")
    
    new_description_label = ttk.Label(main_frame, text="Desciption")
    new_description_label.grid(row=3, padx=2, pady=2, columnspan=2)
    
    new_description_entry = ttk.Entry(main_frame, width=50)
    new_description_entry.grid(row=4, padx=2, pady=2, columnspan=2, sticky="ew")
    
    label = ttk.Label(main_frame, text="Select the project language:")
    label.grid(row=5, columnspan=2, pady=5, padx=5)
    
    lenguaje_options = ["Selection lenguaje", "Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go", "flutter"]
    
    global seleccion
    
    seleccion = tk.StringVar()
    seleccion.set(lenguaje_options[0])
    
    menu_lenguaje = ttk.OptionMenu(main_frame, seleccion, *lenguaje_options)
    menu_lenguaje.grid(row=6, columnspan=2, padx=5, pady=5)
    
    rules_label = ttk.Label(main_frame, text="If you create git repo insert in textbox your rules for the .gitignore")
    rules_label.grid(row=7, columnspan=2, padx=5, pady=5)
    
    textbox = scrolledtext.ScrolledText(main_frame)
    textbox.grid(row=8, columnspan=2, pady=5, padx=5)
    
    btn_selec = ttk.Button(main_frame, text="Select", command=lambda: ejecutar_con_threading(seleccion.get(), textbox))
    btn_selec.grid(row=9, columnspan=2, pady=5, padx=5)
        
def ejecutar_con_threading(lenguaje, textbox):
    threading.Thread(target=iniciar_new_proyect, args=(lenguaje, textbox)).start()
    
def crear_repo_github(nombre_repo, descripcion_repo, ruta_local):
    if GITHUB_TOKEN:
        g = Github(GITHUB_TOKEN)
        
        user = g.get_user()
        
        repo = user.create_repo(nombre_repo, description=descripcion_repo)
        
        repo_local = git.Repo.init(ruta_local)
        
        origin = repo_local.create_remote('origin', repo.clone_url)
        
        repo_local.index.add('*')
        repo_local.index.commit('Initial commit')
        
        origin.push('master')
        
        ms.showinfo("COMPLETE" ,"Repository created on GitHub and locally.")
    else:
        ms.showerror("ERROR", "Could not retrieve the GitHub API key.")

def github_url_to_api_url_repo(github_url, branch_name='main'):
    parsed_url = urlparse(github_url)
    
    path_parts = parsed_url.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError("URL Github invalid. Check the URL is correct")
    
    repo_owner = path_parts[0]
    repo_name = path_parts[1]
    
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents?ref={branch_name}"
    
    return api_url

def push_actualizaciones_github(github_url):
    github_url_to_api_url_repo(github_url)
        
def iniciar_new_proyect(lenguaje, textbox):
    nombre = new_name_entry.get()
    descripcion = new_description_entry.get()
    ruta_proyecto = filedialog.askdirectory()
    repo = repo_entry.get()
    rules = textbox.get("1.0", "end")
    if ruta_proyecto:
        if lenguaje == "Python":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'python -m venv "{os.path.join(ruta_completa, "app")}"'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)
        elif lenguaje == "NodeJS":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'npm init -w "{os.path.join(ruta_completa)}" -y > output.txt 2>&1'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                with open('output.txt', 'r') as f:
                    output = f.read()
                    textbox.insert(tk.END, output)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                os.remove('output.txt')
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)
        elif lenguaje == "React":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'npx create-react-app "{ruta_completa}" > output.txt 2>&1'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                with open('output.txt', 'r') as f:
                    output = f.read()
                    textbox.insert(tk.END, output)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                os.remove('output.txt')
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)         
        elif lenguaje == "C#":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'dotnet new console -n "{ruta_completa}" > output.txt 2>&1'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                with open('output.txt', 'r') as f:
                    output = f.read()
                    textbox.insert(tk.END, output)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                os.remove('output.txt')
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)
        elif lenguaje == "Rust":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'cargo new "{ruta_completa}" --bin > output.txt 2>&1'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                with open('output.txt', 'r') as f:
                    output = f.read()
                    textbox.insert(tk.END, output)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                os.remove('output.txt')
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)
        elif lenguaje == "go":
                ruta_completa = os.path.join(ruta_proyecto, nombre)
                ruta_completa = os.path.normpath(ruta_completa)
                os.makedirs(ruta_completa, exist_ok=True)
                comando = f'go mod init "{ruta_completa}" > output.txt 2>&1'
                os.system(comando)
                respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
                if respuesta:
                    crear_repo_github(nombre, descripcion, ruta_completa)
                with open('output.txt', 'r') as f:
                    output = f.read()
                    textbox.insert(tk.END, output)
                insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
                os.remove('output.txt')
                git = ms.askyesno("Create Git", "Do you want create Git Repo")
                if git:
                    with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                        f.write(rules)
                        git_init(ruta_completa)
                        git_add(ruta_completa)
        elif lenguaje == "bun":
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            ruta_completa = os.path.normpath(ruta_completa)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'bun init "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
            os.remove('output.txt')
            git = ms.askyesno("Create Git", "Do you want create Git Repo")
            if git:
                with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                    f.write(rules)
                    git_init(ruta_completa)
                    git_add(ruta_completa)
        elif lenguaje == "flutter":
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            ruta_completa = os.path.normpath(ruta_completa)
            os.makedirs(ruta_completa, exist_ok=True)
            try:
                resultado = subprocess.run(['flutter', 'doctor'], capture_output=True, text=True)
                if resultado.returncode != 0:
                    ms.showerror("ERROR", f"Flutter is not configured correctly.\nDetails:\n{resultado.stderr}")
                    webbrowser.open("https://flutter.dev/docs/get-started/install")
                else:
                    pass
            except FileNotFoundError:
                pass
                
            comando = f'flutter create "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, ruta_completa, repo, lenguaje)
            os.remove('output.txt')
            git = ms.askyesno("Create Git", "Do you want create Git Repo")
            if git:
                with open(os.path.join(ruta_completa, '.gitignore'), 'w') as f:
                    f.write(rules)
                    git_init(ruta_completa)
                    git_add(ruta_completa)
    
    mostrar_proyectos()

def eliminar_proyecto(id, ruta):
    try:
        shutil.rmtree(ruta)
        conn = sqlite3.connect('proyectos.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        mostrar_proyectos()
    except shutil.Error as e:
        ms.showerror("ERROR", f"Error deleting project: {e}")
        conn = sqlite3.connect('proyectos.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        mostrar_proyectos()
    
def seleccionar_ruta_editor(editor, entry):
    ruta_editor = filedialog.askopenfilename(title=f"Seleccione el ejecutable de {editor}", filetypes=[("Ejecutables", "*")])
    if ruta_editor:
        entry.delete(0, tk.END)
        entry.insert(0, ruta_editor)
        
def guardar_configuracion_editores(rutas_editores):
    configuracion = {}
    for editor, entry in rutas_editores.items():
        ruta = entry.get()
        if ruta:
            configuracion[editor] = ruta
    with open("configuracion_editores.json", "w") as archivo_configuracion:
        json.dump(configuracion, archivo_configuracion)

def save_config_gpt(api_key):
    configuration = {"api_key_openai": api_key}
    
    with open(archivo_configuracion_gpt, "w") as archivo_configuracion:
        json.dump(configuration, archivo_configuracion)
    
def load_config_gpt():
    try:
        with open("configuration_gpt.json", "r") as config_archive:
            config = json.load(config_archive)
            return config.get("api_key_openai", None)
    except FileNotFoundError:
        return None
       
def cargar_configuracion_editores():
    try:
        with open(archivo_configuracion_editores, "r") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)
            return configuracion
    except FileNotFoundError:
        return None

def cargar_config_terminal():
    try:
        with open("terminal_config.json", "r") as config_terminal:
            config = json.load(config_terminal)
            return config
    except FileNotFoundError:
        return None

def hide_selected_row():
    seleccion = tree.selection()
    
    for rowid in seleccion:
        tree.detach(rowid)
        filas_ocultas.add(rowid)

def show_selected_row():
    seleccion = tree.selection()

    for rowid in seleccion:
        tree.reattach(rowid, '', 'end')
        filas_ocultas.remove(rowid)
        
def show_context_menu(event):
    menu_items = [
        ("Open Explorer", lambda: abrir_explorador(event)),
        ("Open Github", lambda: abrir_repositorio(event)),
        ("Edit", modificar_proyecto),
        ("Delete", lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4])),
        ("Version Control", show_controlversion),
        ("Detect Dependencies", detectar_dependencias),
        ("Git Init", lambda: git_init(selected_project_path)),
        ("Git Add", lambda: git_add(selected_project_path)),
        ("Git Commit", lambda: git_commit(selected_project_path)),
        ("Git Status", lambda: git_status(selected_project_path)),
        ("Git Log", lambda: git_log(selected_project_path)),
        ("Git Diff", lambda: git_diff(selected_project_path)),
        ("Git Pull", lambda: git_pull(selected_project_path)),
        ("Git Push", lambda: git_push(selected_project_path)),
        ("Git Branch", lambda: git_branch(selected_project_path)),
        ("Git Checkout", lambda: git_checkout(selected_project_path)),
        ("Git Merge", lambda: git_merge(selected_project_path)),
        ("Git Remote", lambda: git_remote(selected_project_path)),
        ("Git Fetch", lambda: git_fetch(selected_project_path)),
        ("Git Reset", lambda: git_reset(selected_project_path)),
        ("Git Revert", lambda: git_revert(selected_project_path))
    ]
    rowid = tree.identify_row(event.y)
    if rowid:
        context_menu = tk.Menu(root, tearoff=0)
        for label, command in menu_items:
            context_menu.add_command(label=label, command=command)
        
        context_menu.post(event.x_root, event.y_root)

def git_add(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git Add")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "add", "."], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_commit(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git Commit")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "commit", "-m", "'Commit desde GUI'"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_status(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git Status")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "status"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_pull(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git Pull")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "pull"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_init(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git Init")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "init"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_log(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Salida de Git")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "log"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_diff(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Diff Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "diff"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_push(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Push Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "push"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_branch(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Branch Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "branch"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_checkout(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Checkout Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "checkout"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_merge(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Merge Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "merge"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_remote(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Remote Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "remote", "-v"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_fetch(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Fetch Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "fetch"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_reset(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Reset Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "reset"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def git_revert(project_path):
    output_window = tk.Toplevel(root)
    output_window.title("Git Revert Output")
    
    main_frame = ttk.Frame(output_window)
    main_frame.pack()

    output_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
    output_text.pack()

    try:
        output = run_git_command(["git", "revert"], cwd=project_path)
        output_text.insert(tk.END, output)
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def run_git_command(command, cwd=None):
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, cwd=cwd).decode()
        return output
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error: {e.output.decode()}")

def abrir_repositorio(event):
    item_seleccionado = tree.item(tree.selection())
    url_repositorio = item_seleccionado['values'][5]

    webbrowser.open_new(url_repositorio)
    
def abrir_explorador(event):
    item_seleccionado = tree.item(tree.selection())
    ruta = item_seleccionado['values'][4]

    exploradores = ['thunar', 'nautilus', 'dolphin', 'nemo', 'pcmanfm', 'konqueror', 'caja']

    explorador_disponibles = None
    for explorador in exploradores:
        if shutil.which(explorador):
            explorador_disponibles = explorador
            break

    if explorador_disponibles:
        subprocess.Popen([explorador_disponibles, ruta])
    else:
        ms.showerror("ERROR", "Can't found any explorer available")
    
def abrir_proyecto_github():
    url_repositorio = simpledialog.askstring("GITHUB REPO", "Insert the url of the github repository you want to add")
    description = descripcion_entry.get()

    ruta_destino = filedialog.askdirectory()

    if ruta_destino:
        subprocess.run(['git', 'clone', url_repositorio], cwd=ruta_destino, check=True)
        
        nombre_repositorio = url_repositorio.split('/')[-1].replace('.git', '')
        ruta_repositorio_clonado = os.path.join(ruta_destino, nombre_repositorio)

        insertar_proyecto(nombre_repositorio, description, ruta_repositorio_clonado, url_repositorio)
        abrir_proyecto(ruta_repositorio_clonado, selected_editor.get())
        
        repo_entry.delete(0, tk.END)
        
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def resource_path2(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def obtener_informacion_proyectos_desde_bd():
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM proyectos')
    proyectos = cursor.fetchall()

    conn.close()

    informacion_proyectos = []
    for proyecto in proyectos:
        proyecto_info = {
            'id': proyecto[0],
            'nombre': proyecto[1],
            'descripcion': proyecto[2],
            'lenguaje': proyecto[3],
            'ruta': proyecto[4],
            'repo': proyecto[5]
        }
        informacion_proyectos.append(proyecto_info)

    return informacion_proyectos

def listar_archivos(ruta):
    try:
        archivos = os.listdir(ruta)
        return '\n'.join(archivos)
    except Exception as e:
        return str(e)

def generar_informe_html(informacion):
    informe_html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Proyectos</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .container {
                width: 80%;
                margin: 20px auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                box-shadow: 0px 0px 10px 0px rgba(0,0,0,0.1);
                border-radius: 5px;
                overflow: hidden;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 12px;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #ffffff;
            }
            tr:hover {
                background-color: #f0f0f0;
            }
            .project-description {
                max-width: 400px;
                word-wrap: break-word;
                padding-right: 40px;
                position: relative;
            }
            .project-link {
                color: #007bff;
                text-decoration: none;
            }
            .project-link:hover {
                text-decoration: underline;
            }
            tbody tr:hover {
                background-color: #e3e3e3;
            }
        </style>
        <script>
            function abrirProyectoEnEditor(ruta) {
                var selector = document.getElementById("editores");
                var editor = selector.value;
                ruta = encodeURIComponent(ruta);
                switch (editor) {
                    case "Visual Studio Code":
                        window.open("vscode://file/" + ruta);
                        break;
                    case "Sublime Text":
                        window.open("subl://" + ruta);
                        break;
                    case "Atom":
                        window.open("atom://open?url=" + ruta);
                        break;
                    case "Vim":
                        window.open("vim://" + ruta);
                        break;
                    case "Emacs":
                        window.open("emacs://" + ruta);
                        break;
                    case "Notepad++":
                        window.open("notepad++://" + ruta);
                        break;
                    
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align:center;">Informe de Proyectos</h1>
            <label for="editores">Selecciona un editor:</label>
            <select id="editores">
                <option value="Visual Studio Code">Visual Studio Code</option>
                <option value="Sublime Text">Sublime Text</option>
                <option value="Atom">Atom</option>
                <option value="Vim">Vim</option>
                <option value="Emacs">Emacs</option>
                <option value="Notepad++">Notepad++</option>
                <option value="Brackets">Brackets</option>
                <option value="TextMate">TextMate</option>
                <option value="Geany">Geany</option>
                <option value="gedit">gedit</option>
                <option value="Nano">Nano</option>
                <option value="Kate">Kate</option>
                <option value="Bluefish">Bluefish</option>
                <option value="Eclipse">Eclipse</option>
                <option value="IntelliJ IDEA">IntelliJ IDEA</option>
                <option value="PyCharm">PyCharm</option>
                <option value="Visual Studio">Visual Studio</option>
                <option value="Code::Blocks">Code::Blocks</option>
                <option value="NetBeans">NetBeans</option>
                <option value="Android Studio">Android Studio</option>
            </select>
            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Descripción</th>
                        <th>Lenguaje</th>
                        <th>Ruta</th>
                        <th>Repositorio</th>
                    </tr>
                </thead>
                <tbody>
    """

    for proyecto in informacion:
        archivos_ruta = listar_archivos(proyecto['ruta'])
        informe_html += f"""
            <tr>
                <td>{proyecto['nombre']}</td>
                <td class="project-description" title="{proyecto['descripcion']}">{proyecto['descripcion']}</td>
                <td>{proyecto['lenguaje']}</td>
                <td><a href="#" onclick="abrirProyectoEnEditor('{proyecto['ruta']}')" title="{archivos_ruta}">{proyecto['ruta']}</a></td>
                <td><a href="{proyecto['repo']}" target="_blank">{proyecto['repo']}</a></td>
            </tr>
        """

    informe_html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    with open("informe.html", "w") as f:
        f.write(informe_html)
        
def on_project_select(event):
    global selected_project_path
    selected_item = tree.selection()
    if selected_item:
        item = tree.item(selected_item[0], 'values')[0]
        selected_project_path = tree.item(selected_item, "values")[4]
        
def generar_informe():
    informacion_proyectos = obtener_informacion_proyectos_desde_bd()

    generar_informe_html(informacion_proyectos)

    ms.showinfo("Report Generate", "The report has been successfully generated. You can find it in the 'informe.html' file.")
    
    os.system('informe.html')
    
def install_librarys(lenguaje):
    global selected_project_path
    
    
    if selected_project_path is None:
        ms.showerror("ERROR", "No project selected")
        return
    
    libreria = depen_entry.get()
    librerias = libreria.split()
    
    if lenguaje == "Python":
        env_activate_script = os.path.join(selected_project_path, "app", "Scripts", "activate")
        if os.path.exists(env_activate_script):
            cmd = [env_activate_script, "&&", "python", "-m", "pip", "install"] + librerias
            subprocess.run(cmd, shell=True)
            ms.showinfo("Complete", f"{librerias} Has been installed.")
        else:
            ms.showerror("ERROR", "No virtual environment found in the project.")
    else:
        if lenguaje.lower() == "nodejs":
            subprocess.run(["npm", "install", librerias], cwd=selected_project_path, shell=True)
            ms.showinfo("Complete", f"{librerias} Has been installed.")
        elif lenguaje.lower() == "react":
            subprocess.run(["npm", "install", librerias], cwd=selected_project_path, shell=True)
            ms.showinfo("Complete", f"{librerias} Has been installed.")
        elif lenguaje.lower() == "vue":
            subprocess.run(["npm", "install", librerias], cwd=selected_project_path, shell=True)
            ms.showinfo("Complete", f"{librerias} Has been installed.")
        elif lenguaje.lower() == "rust":
            subprocess.run(["cargo", "install", librerias], cwd=selected_project_path, shell=True)
            ms.showinfo("Complete", f"{librerias} Has been installed.")
        elif lenguaje.lower() == "go":
            subprocess.run(["go", "get", librerias], cwd=selected_project_path, shell=True)
            ms.showinfo("Complete", f"{libreria} Has been installed.")
           
def modificar_proyecto():
    selected_row = tree.selection()
    if not selected_row:
        ms.showerror("Error", "Please select a project to modify.")
        return

    field_index = {
        'ID': 0,
        'Nombre': 1,
        'Descripcion': 2,
        'Lenguaje': 3,
        'Ruta': 4,
        'repo': 5
    }

    selected_row = selected_row[0]
    current_values = tree.item(selected_row, "values")

    mod_window = tk.Toplevel(root)
    mod_window.title("Modify Project")
    mod_window.iconphoto(True, tk.PhotoImage(file=path))
    
    main_frame = ttk.Frame(mod_window)
    main_frame.pack()

    entry_widgets = {}  # Diccionario para almacenar los widgets de entrada

    for field, index in field_index.items():
        field_label = ttk.Label(main_frame, text=f"{field}:")
        field_label.grid(row=index, column=0, padx=5, pady=5)

        new_value_entry = ttk.Entry(main_frame, width=50)
        new_value_entry.insert(0, current_values[index])
        new_value_entry.grid(row=index, column=1, padx=5, pady=5)

        entry_widgets[field] = new_value_entry  # Almacenar el widget en el diccionario

    def apply_modification():
        new_values = []
        for field, index in field_index.items():
            entry = entry_widgets[field]
            value = entry.get()
            new_values.append(value if value.strip() else None)
        project_id = current_values[field_index['ID']]
        update_project(project_id, field_index, new_values)
        mod_window.destroy()

    apply_button = ttk.Button(main_frame, text="Apply", command=apply_modification)
    apply_button.grid(row=9, columnspan=2, padx=5, pady=5)

def update_project(project_id, field_index, new_values):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()

    set_fields = [f"{field.lower()}=?" for field, value in zip(field_index.keys(), new_values) if value is not None]
    update_query = "UPDATE proyectos SET " + ", ".join(set_fields)

    update_query += " WHERE id=?"

    filtered_values = [value for value in new_values if value is not None]
    filtered_values.append(project_id)

    cursor.execute(update_query, filtered_values)

    conn.commit()
    conn.close()
    mostrar_proyectos()
  
def change_theme(theme_name):
    root.set_theme(theme_name)
    root.update_idletasks()
    root.geometry("")
    root.geometry(f"{root.winfo_reqwidth()}x{root.winfo_reqheight()}")

def install_choco():
    subprocess.run("Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
    ms.showinfo("INSTALL COMPLETE", "Choco has install correctly")
    
def install_scoop():
    subprocess.run("Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression").wait()
    ms.showinfo("INSTALL COMPLETE", "Scoop has install correctly")

def install_lenguaje(lenguaje_selected):
    distro = detect_distro()
    
    def run_command(command):
        try:
            subprocess.run(command, shell=True, check=True)
            ms.showinfo("INSTALL COMPLETE", f"{lenguaje_selected} has been installed")
        except subprocess.CalledProcessError:
            ms.showerror("INSTALL FAILED", f"Failed to install {lenguaje_selected}")

    if lenguaje_selected == "Python":
        if distro == "debian":
            run_command("sudo apt-get install python3 -y")
        elif distro == "fedora":
            run_command("sudo dnf install python3 -y")
        elif distro == "arch":
            run_command("sudo pacman -S python --noconfirm")
    
    elif lenguaje_selected in ["NodeJS", "React"]:
        if distro == "debian":
            run_command("sudo apt-get install nodejs npm -y")
        elif distro == "fedora":
            run_command("sudo dnf install nodejs npm -y")
        elif distro == "arch":
            run_command("sudo pacman -S nodejs npm --noconfirm")
    
    elif lenguaje_selected == "bun":
        run_command("curl -fsSL https://bun.sh/install | bash")
    
    elif lenguaje_selected == "Rust":
        run_command("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
    
    elif lenguaje_selected == "Go":
        url = "https://go.dev/dl/go1.22.1.linux-amd64.tar.gz"
        response = requests.get(url)
        file = url.split('/')[-1]
        with open(file, 'wb') as f:
            f.write(response.content)
        run_command(f"sudo tar -C /usr/local -xzf {file}")
        os.remove(file)

    elif lenguaje_selected == "flutter":
        url = "https://docs.flutter.dev/get-started/install"
        webbrowser.open_new(url)

def detect_distro():
    try:
        with open("/etc/os-release") as f:
            os_release = f.read()
            if "Debian" in os_release or "Ubuntu" in os_release:
                return "debian"
            elif "Fedora" in os_release:
                return "fedora"
            elif "Arch" in os_release:
                return "arch"
    except FileNotFoundError:
        ms.showerror("ERROR", "Cannot detect Linux distribution.")
        return None

def label_hover_in(event):
    version_label.config(background="gray", cursor='hand2')

def label_hover_out(event):
    version_label.config(background="",cursor='')

def renderizar_markdown(texto):
    html = markdown(texto)
    return html

def obtener_ultima_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def ver_info():
    info_window = tk.Toplevel(root)
    info_window.title("PATCH NOTES")
    info_window.geometry("1500x600")
    info_window.iconphoto(True, tk.PhotoImage(file=path))

    repo = "Nooch98/Organizer"
    release_info = obtener_ultima_release(repo)

    notas_markdown = release_info.get('body', 'No release notes available.')
    html = markdown2.markdown(notas_markdown)

    notas_html = HTMLLabel(info_window, html=html)
    notas_html.pack(expand=True, fill="both", side="left")

    scrollbar_vertical = ttk.Scrollbar(info_window, orient="vertical", command=notas_html.yview)
    scrollbar_vertical.pack(side="right", fill="y")
    notas_html.configure(yscrollcommand=scrollbar_vertical.set)
    
if platform.system() == "Windows":
    import winreg as reg

def get_windows_theme():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize')
        current_theme = reg.QueryValueEx(key, "AppsUseLightTheme")[0]
        reg.CloseKey(key)
        
        return "light" if current_theme == 1 else "dark"
    except Exception as e:
        ms.showerror("ERROR", f"Can't Obtain theme of your system: {str(e)}")
        return "light"
    
def get_mac_theme():
    try:
        from subprocess import run, PIPE
        result = run(['defaults', 'read', 'g', 'AppleInterfaceStyle'], stdout=PIPE, stderr=PIPE, text=True)
        if 'Dark' in result.stdout:
            return 'dark'
        else:
            return 'light'
    except Exception as e:
        ms.showerror("ERROR", f"Can't obtain the theme of your system: {str(e)}")
        return "light"

def get_linux_theme():
    try:
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                gtk_theme = result.stdout.strip().strip("'")
                if "dark" in gtk_theme.lower():
                    return "dark"
                else:
                    return "light"
        except Exception:
            pass

        try:
            kde_config = os.path.expanduser('~/.config/kdeglobals')
            if os.path.isfile(kde_config):
                with open(kde_config, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if "ColorScheme=" in line:
                        if "Dark" in line:
                            return "dark"
                        else:
                            return "light"
        except Exception:
            pass

        try:
            result = subprocess.run(['xfconf-query', '--channel', 'xsettings', '--property', '/Net/ThemeName'], stdout=subprocess.PIPE, text=True)
            if "dark" in result.stdout.lower():
                return "dark"
            else:
                return "light"
        except Exception:
            pass

        return "light"

    except Exception as e:
        ms.showerror("ERROR", f"Can't obtain the theme of your system: {str(e)}")
        return "light"
    
def get_system_theme():
    system = platform.system()
    if system == "Windows":
        return get_windows_theme()
    elif system == "Darwin":
        return get_mac_theme()
    elif system == "Linux":
        return get_linux_theme()
    else:
        ms.showerror("ERROR", f"Unsupported operating system: {system}")
        return "light"
    
def set_default_theme():
    system_theme = get_system_theme()
    
    if system_theme == "dark":
        change_bootstrap_theme(theme_name="darkly")
    else:
        change_bootstrap_theme(theme_name="cosmo")

def ttk_themes():
    style = ttk.Style()
    themes = style.theme_names()
    return themes

def change_bootstrap_theme(theme_name):
    style = ttk.Style()
    style.theme_use(theme_name)

def create_theme():
    command = "python3 -m ttkcreator"
    subprocess.run(f'{command}', shell=True)

def setting_window():
    config_window = tk.Toplevel(root)
    config_window.title("Settings")
    config_window.iconphoto(True, tk.PhotoImage(file=path))
    
    main_frame = ttk.Frame(config_window)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    theme_frame = ttk.Frame(main_frame)
    ttktheme_frame = ttk.Frame(main_frame)
    startup_frame = ttk.Frame(main_frame)
    editor_frame = ttk.Frame(main_frame)
    openai_frame = ttk.Frame(main_frame)
    choco_frame = ttk.Frame(main_frame)
    scoop_frame = ttk.Frame(main_frame)
    editors_frame = ttk.Frame(main_frame)
    lenguajes_frame = ttk.Frame(main_frame)
    terminal_frame = ttk.Frame(main_frame)
    backup_frame = ttk.Frame(main_frame)
    
    list_settings = tk.Listbox(main_frame, height=33, width=40)
    list_settings.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
    
    list_settings.insert(tk.END, "Editors Configure")
    list_settings.insert(tk.END, "Open Ai")
    list_settings.insert(tk.END, "Install Lenguajes")
    list_settings.insert(tk.END, "Install choco")
    list_settings.insert(tk.END, "Install scoop")
    list_settings.insert(tk.END, "Install Editors")
    list_settings.insert(tk.END, "Backup Settings")
    list_settings.insert(tk.END, "Terminal Setting")
    list_settings.insert(tk.END, "Theme")
    list_settings.insert(tk.END, "TTKTheme")
    
    def hide_frames():
        theme_frame.grid_forget()
        ttktheme_frame.grid_forget()
        editor_frame.grid_forget()
        openai_frame.grid_forget()
        choco_frame.grid_forget()
        scoop_frame.grid_forget()
        editors_frame.grid_forget()
        lenguajes_frame.grid_forget()
        terminal_frame.grid_forget()
        backup_frame.grid_forget()
        
    def select_user_config(event=None):
        selection = list_settings.curselection()
        if selection:
            index = selection[0]
            item = list_settings.get(index)
            
        if item == "Editors Configure":
            hide_frames()
            editor_frame.grid(row=0, column=1, sticky="nsew")
            rutas_editores = {}
    
            configs_editors = cargar_configuracion_editores()
            if configs_editors is None:
                configs_editors = {}

            def guardar_y_cerrar():
                guardar_configuracion_editores(rutas_editores)
            
            for i, programa in enumerate(editores_disponibles):
                label = ttk.Label(editor_frame, text=programa)
                label.grid(row=i, column=0, padx=5, pady=5)
                
                entry = ttk.Entry(editor_frame, width=80)
                entry.grid(row=i, column=1, padx=5, pady=5)
                
                if programa in configs_editors:
                    entry.insert(0, configs_editors[programa])
                
                btn = ttk.Button(editor_frame, text="Agree", command=lambda prog=programa, ent=entry: seleccionar_ruta_editor(prog, ent))
                btn.grid(row=i, column=2, padx=5, pady=5)
                
                rutas_editores[programa] = entry

            aceptar_btn = ttk.Button(editor_frame, text="Confirm", command=guardar_y_cerrar)
            aceptar_btn.grid(row=len(editores_disponibles), column=0, columnspan=3, padx=5, pady=5)
        
        elif item == "Open Ai":
            hide_frames()
            openai_frame.grid(row=0, column=1, sticky="nsew")
            titulo = ttk.Label(openai_frame, text="OpenAI Configuration")
            titulo.grid(row=0, columnspan=2, pady=5, padx=5)
            
            label = ttk.Label(openai_frame, text="OpenAI Api Key: ")
            label.grid(row=1, column=0, pady=5, padx=5)
            
            api_gpt_entry = ttk.Entry(openai_frame, width=50)
            api_gpt_entry.grid(row=1, column=1, pady=5, padx=5)
            
            def guardar():
                api_key = api_gpt_entry.get()
                save_config_gpt(api_key)
            
            sub_button = ttk.Button(openai_frame, text="Accept", command=guardar)
            sub_button.grid(row=2, columnspan=2, pady=5, padx=5)
        
        elif item == "Install Lenguajes":
            hide_frames()
            lenguajes_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            
            for widget in lenguajes_frame.winfo_children():
                widget.destroy()
                
            num_columns = 3
            
            for index, lenguaje in enumerate(lenguajes):
                row = index // num_columns
                column = index % num_columns
                button = ttk.Button(lenguajes_frame, text=lenguaje, command=lambda lenguaje=lenguaje: install_lenguaje(lenguaje))
                button.grid(row=row, column=column, sticky="ew", padx=2, pady=2)
        
        elif item == "Install choco":
            hide_frames()
            choco_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            quest_label = ttk.Label(choco_frame, text="You want install pakage manager Chocolatey in your powersell")
            quest_label.grid(row=0,columnspan=2, sticky="ew")
            
            yes_btn = ttk.Button(choco_frame, text="YES", command=install_choco)
            yes_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
            
            no_btn = ttk.Button(choco_frame, text="NO", command=hide_frames)
            no_btn.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
            
        
        elif item == "Install scoop":
            hide_frames()
            scoop_frame.grid(row=0, column=1, sticky="nsew")
            quest_label = ttk.Label(scoop_frame, text="You want install pakage manager Scoop in your powersell")
            quest_label.grid(row=0,columnspan=2, sticky="ew")
            
            yes_btn = ttk.Button(scoop_frame, text="YES", command=install_scoop)
            yes_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
            
            no_btn = ttk.Button(scoop_frame, text="NO", command=hide_frames)
            no_btn.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        
        elif item == "Install Editors":
            hide_frames()
            editors_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            
            for widget in editors_frame.winfo_children():
                widget.destroy()

            num_columns = 3
            
            for index, editor in enumerate(editores_disponibles):
                row = index // num_columns
                column = index % num_columns
                button = ttk.Button(editors_frame, text=editor, command=lambda editor=editor: install_editor(editor))
                button.grid(row=row, column=column, sticky="ew", padx=2, pady=2)
            
            
        elif item == "Backup Settings":
            hide_frames()
            backup_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            
            global combo_frequency
            global status_label
            
            frequency_options = ["Daily", "Weekly", "Monthly"]
            combo_frequency = ttk.Combobox(backup_frame, values=frequency_options)
            combo_frequency.set("Daily")
            combo_frequency.grid(row=0, columnspan=2, padx=2, pady=2)
            
            status_label = ttk.Label(backup_frame, text="Backup")
            status_label.grid(row=2, column=0, padx=2, pady=2)
            
            btn_confirm = ttk.Button(backup_frame, text="Confirm", command=get_selected_frequency)
            btn_confirm.grid(row=1, column=0, padx=2, pady=2)
            
            btn_backup_now = ttk.Button(backup_frame, text="Create Now", command=backup_thread)
            btn_backup_now.grid(row=1, column=1, padx=2, pady=2)
        
        elif item == "Terminal Setting":
            hide_frames()
            terminal_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            
            terminal_label = ttk.Label(terminal_frame, text="Select Terminal")
            terminal_label.grid(row=0, columnspan=2, padx=5, pady=5)
            
            selected_terminal = tk.StringVar()
            terminal_choices = ["Select Terminal", "Command Pormpt", "Windows Terminal", "PowerShell", "Git Bash", "wezterm", "Kitty", "Alacrity"]
            terminal_menu = ttk.OptionMenu(terminal_frame, selected_terminal, *terminal_choices)
            terminal_menu.grid(row=1, columnspan=2, pady=5, padx=5)
            
            terminal_path_label = ttk.Label(terminal_frame, text="Terminal Executable Path: ")
            terminal_path_label.grid(row=2, column=0, padx=5, pady=5)
            
            terminal_path_entry = ttk.Entry(terminal_frame, width=50)
            terminal_path_entry.grid(row=2, column=1, padx=5, pady=5)
            
            def save_settigns():
                selected_terminal_value = selected_terminal.get()
                terminal_path_value = terminal_path_entry.get()
                
                config = {
                    "Selected_terminal": selected_terminal_value,
                    "terminal_path": terminal_path_value
                    }
                with open("terminal_config.json", "w") as f:
                    json.dump(config, f)
                    
                    
            save_button = ttk.Button(terminal_frame, text="Save", command=save_settigns)
            save_button.grid(row=3, columnspan=2, padx=5, pady=5)
        
        elif item == "Theme":
            hide_frames()
            theme_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            
            def change_theme1(theme_name):
                root.set_theme(theme_name)
                root.update_idletasks()
            
            for widget in theme_frame.winfo_children():
                widget.destroy()
            
            num_columns = 3

            for index, theme in enumerate(temas):
                row = index // num_columns
                column = index % num_columns
                button = ttk.Button(theme_frame, text=theme, command=lambda theme=theme: change_theme1(theme))
                button.grid(row=row, column=column, sticky="ew", padx=2, pady=2)

        elif item == "TTKTheme":
            hide_frames()
            ttktheme_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            def ttk_themes():
                style = ttk.Style()
                themes = style.theme_names()
                return themes
            
            def change_ttktheme(theme_name):
                style = ttk.Style()
                style.theme_use(theme_name)
                            
            themes = ttk_themes()
            
            for widget in ttktheme_frame.winfo_children():
                widget.destroy()
                
            num_columns = 3
            
            for index, theme in enumerate(themes):
                row = index // num_columns
                column = index % num_columns
                button1 = ttk.Button(ttktheme_frame, text=theme, command=lambda theme=theme: change_ttktheme(theme))
                button1.grid(row=row, column=column, sticky="ew", padx=2, pady=2)
            button2 = ttk.Button(ttktheme_frame, text="Create Theme", command=create_theme)
            button2.grid(row=row, column=column, sticky="ew", padx=2, pady=2)
    
    list_settings.bind("<Double-1>", select_user_config)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=8)
    main_frame.grid_rowconfigure(2, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)

def on_key_release(event):
    search_text = search_entry.get().strip()

    # Limpiar el Treeview antes de mostrar nuevos resultados
    for item in tree.get_children():
        tree.delete(item)

    # Si el campo de búsqueda está vacío, mostrar todos los proyectos
    if not search_text:
        mostrar_proyectos()
    else:
        # Conectar a la base de datos y buscar los proyectos que coinciden
        conn = sqlite3.connect('proyectos.db')
        cursor = conn.cursor()
        query = "SELECT * FROM proyectos WHERE nombre LIKE ? OR descripcion LIKE ? OR lenguaje LIKE ?"
        cursor.execute(query, ('%' + search_text + '%', '%' + search_text + '%', '%' + search_text + '%'))
        proyectos = cursor.fetchall()
        conn.close()

        # Insertar los resultados de búsqueda en el Treeview
        for proyecto in proyectos:
            tree.insert('', 'end', values=proyecto)

def show_controlversion():
    seleccion = tree.selection()
    if not seleccion:
        ms.showwarning("Warning", "Please select a project first.")
        return

    ruta_proyecto = tree.item(seleccion, "values")[4]

    if not os.path.exists(os.path.join(ruta_proyecto, '.git')):
        ms.showerror("ERROR", "A Git repository was not found in the selected project.")
        return

    control_version = tk.Toplevel(root)
    control_version.title(f"Version Control: {ruta_proyecto}")
    control_version.geometry("1320x740")

    frame_commits = ttk.Frame(control_version)
    frame_commits.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    treeview_commits = ttk.Treeview(frame_commits, columns=("commit", "author", "date"), show='headings', height=36)
    treeview_commits.heading("commit", text="commit")
    treeview_commits.heading("author", text="author")
    treeview_commits.heading("date", text="Date")

    treeview_commits.grid(row=0, column=0, sticky="nsew")

    scrollbar_y_commits = ttk.Scrollbar(frame_commits, orient="vertical", command=treeview_commits.yview)
    treeview_commits.configure(yscrollcommand=scrollbar_y_commits.set)
    scrollbar_y_commits.grid(row=0, column=1, sticky="ns")

    frame_detalles = ttk.Frame(control_version)
    frame_detalles.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    scrolled_text_detalles = scrolledtext.ScrolledText(frame_detalles, wrap=tk.WORD)
    scrolled_text_detalles.grid(row=0, column=0, sticky="nsew")

    # Configurar cómo se distribuyen las filas y columnas en el grid
    control_version.grid_rowconfigure(0, weight=1)  # Permitir que la fila del TreeView se expanda
    frame_commits.grid_columnconfigure(0, weight=1)  # Permitir que el TreeView se expanda
    frame_detalles.grid_rowconfigure(0, weight=1)  # Permitir que el área de detalles se expanda

    # Cargar el historial de commits
    repo = Repo(ruta_proyecto)
    for commit in repo.iter_commits():
        treeview_commits.insert("", "end", values=(commit.hexsha[:7], commit.author.name, commit.committed_datetime))

    # Función para mostrar detalles del commit al hacer clic
    def mostrar_detalles(event):
        seleccion = treeview_commits.selection()
        if seleccion:
            item = seleccion[0]
            commit_sha = treeview_commits.item(item, "values")[0]
            commit = repo.commit(commit_sha)
            
            # Verificar si el commit tiene padres antes de calcular el diff
            if commit.parents:
                dif = commit.diff(commit.parents[0])  # Diferencia con el primer padre
            else:
                dif = []  # Si no hay padres, no hay diferencias que mostrar

            detalles = f"Commit: {commit.hexsha}\nAutor: {commit.author.name}\nFecha: {commit.committed_datetime}\n\nMensaje:\n{commit.message}\n\nDiferencias:\n"
            for cambio in dif:
                detalles += f"{cambio}\n"
            
            scrolled_text_detalles.delete(1.0, tk.END)
            scrolled_text_detalles.insert(tk.END, detalles)

    treeview_commits.bind("<Double-1>", mostrar_detalles)
    
def detectar_dependencias():
    # Obtener la ruta del proyecto seleccionado desde la pantalla principal
    seleccion = tree.selection()
    if not seleccion:
        ms.showwarning("Warning", "Please select a project first.")
        return

    ruta_proyecto = tree.item(seleccion, "values")[4]  # Tomar la ruta del proyecto desde los valores

    # Lista para almacenar dependencias encontradas
    dependencias = []

    # Comprobar si existen archivos de dependencias
    archivos_dependencias = {
        # Python
        "requirements.txt": "pip install -r requirements.txt",
        "setup.py": "pip install .",
        "Pipfile": "pipenv install",
        "pyproject.toml": "pip install .",

        # JavaScript
        "package.json": "npm install",
        "yarn.lock": "yarn install",

        # Ruby
        "Gemfile": "bundle install",
        
        # PHP
        "composer.json": "composer install",
        
        # Java
        "pom.xml": "mvn install",
        "build.gradle": "gradle build",

        # .NET
        "project.json": "dotnet restore",
        "*.csproj": "dotnet restore",
        
        # R
        "DESCRIPTION": "Rscript -e 'devtools::install()'",

        # Elixir
        "mix.exs": "mix deps.get",

        # Haskell
        "cabal.config": "cabal install",

        # Rust
        "Cargo.toml": "cargo build"
    }

    for archivo, comando in archivos_dependencias.items():
        # Usar glob para detectar patrones como "*.csproj"
        if '*' in archivo:
            for file in glob.glob(os.path.join(ruta_proyecto, archivo)):
                dependencias.append((file, comando))
        else:
            ruta_archivo = os.path.join(ruta_proyecto, archivo)
            if os.path.exists(ruta_archivo):
                dependencias.append((archivo, comando))

    # Si se encuentran dependencias, mostrarlas en una ventana
    if dependencias:
        ventana_dependencias = tk.Toplevel(root)
        ventana_dependencias.title("Dependencis Found")
        ventana_dependencias.geometry("600x400")

        # Crear un canvas para permitir el desplazamiento
        canvas = tk.Canvas(ventana_dependencias)
        scrollbar = tk.Scrollbar(ventana_dependencias, orient="vertical", command=canvas.yview)
        frame_dependencias = tk.Frame(canvas)

        frame_dependencias.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=frame_dependencias, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Empaquetar el canvas y la barra de desplazamiento
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Función para desplazar el canvas usando la rueda del ratón
        def desplazar_canvas(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")  # Ajusta el desplazamiento por la rueda

        # Vincular la rueda del ratón al canvas
        canvas.bind_all("<MouseWheel>", desplazar_canvas)  # Para Windows
        canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))  # Para Linux
        canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))

        # Mostrar dependencias encontradas
        for idx, (archivo, comando) in enumerate(dependencias):
            label = tk.Label(frame_dependencias, text=f"{archivo} found.")
            label.pack(anchor="w", padx=5, pady=5)

            # Leer las librerías o dependencias a instalar
            if archivo == "requirements.txt":
                with open(os.path.join(ruta_proyecto, archivo), "r") as f:
                    librerias = f.readlines()
                    librerias = [lib.strip() for lib in librerias if lib.strip()]

                librerias_label = tk.Label(frame_dependencias, text="Libraries to install:")
                librerias_label.pack(anchor="w", padx=5, pady=5)

                for libreria in librerias:
                    libreria_label = tk.Label(frame_dependencias, text=f"- {libreria}")
                    libreria_label.pack(anchor="w", padx=5)

            elif archivo == "package.json":
                with open(os.path.join(ruta_proyecto, archivo), "r") as f:
                    data = json.load(f)
                    if "dependencies" in data:
                        librerias = data["dependencies"]
                        librerias_label = tk.Label(frame_dependencias, text="Dependencies to install:")
                        librerias_label.pack(anchor="w", padx=5, pady=5)

                        for libreria, version in librerias.items():
                            libreria_label = tk.Label(frame_dependencias, text=f"- {libreria} ({version})")
                            libreria_label.pack(anchor="w", padx=5)

            # Botón para instalar las dependencias
            boton_instalar = tk.Button(ventana_dependencias, text="Install", command=lambda cmd=comando: instalar_dependencias(ruta_proyecto, cmd))
            boton_instalar.pack(anchor="w", padx=5, pady=5)

    else:
        ms.showinfo("Information", "No dependency files were found in the project.")

def instalar_dependencias(ruta_proyecto, comando):
    try:
        # Cambiar al directorio del proyecto
        subprocess.run(comando, cwd=ruta_proyecto, shell=True, check=True)
        ms.showinfo("Success", "Dependencies installed correctly.")
    except subprocess.CalledProcessError:
        ms.showerror("Error", "There was a problem installing the dependencies.")

def obtain_github_repos():
    url = "https://api.github.com/user/repos"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        repos = response.json()
        return repos
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Error loading GitHub repositories: {e}")
        return []
    
def show_github_repos():
    for item in repostree.get_children():
        repostree.delete(item)
    
    repos = obtain_github_repos()
    for repo in repos:
        repostree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], repo["visibility"], repo["clone_url"]))
        
def open_repository(event):
    item = repostree.selection()
    if item:
        repo_url = repostree.item(item, "values")[3]
        webbrowser.open_new_tab(repo_url)

def create_repository_github(name, description="", private=False):
    url = "https://api.github.com/user/repos"
    data = {
        "name": name,
        "description": description,
        "private": private
    }
    
    try:
        response = requests.post(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                               "Accept": "application/vnd.github.v3+json"},
                                 json=data)
        response.raise_for_status()
        ms.showinfo("SUCCESS", f"Repository '{name}' created successfully.")
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Error creating repository: {e}")
        
def delete_repository_github(name):
    user = GITHUB_USER
    url = f"https://api.github.com/repos/{user}/{name}"
    
    try:
        response = requests.delete(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                 "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        ms.showinfo("SUCCESS", f"Repository '{name}' deleted successfully.")
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Error deleting repository: {e}")

def edit_repository(name):
    """
    Edita un repositorio por su nombre, permitiendo modificar varias propiedades.
    """
    user = GITHUB_USER
    url = f"https://api.github.com/repos/{user}/{name}"

    # Obtener detalles actuales del repositorio para prellenar los valores
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        repo_data = response.json()
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"No se pudo obtener los datos del repositorio: {e}")
        return

    # Crear un cuadro de diálogo para editar los campos del repositorio
    def guardar_cambios():
        # Recopilar los valores actualizados
        nuevo_nombre = nombre_var.get().strip()
        nueva_descripcion = descripcion_var.get().strip()
        nueva_visibilidad = visibilidad_var.get()

        # Crear el payload con los datos actualizados
        data = {
            "name": nuevo_nombre,
            "description": nueva_descripcion,
            "private": nueva_visibilidad == "Privado"
        }

        # Enviar los cambios a la API
        try:
            response = requests.patch(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                    "Accept": "application/vnd.github.v3+json"}, json=data)
            response.raise_for_status()
            ms.showinfo("Éxito", f"Repositorio '{name}' actualizado con éxito.")
            edit_window.destroy()  # Cerrar la ventana de edición
            show_github_repos()  # Actualizar la lista de repositorios
        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Error al actualizar el repositorio: {e}")

    # Crear la ventana de edición
    edit_window = ttk.Toplevel()
    edit_window.title(f"Editar Repositorio: {name}")
    edit_window.iconphoto(True, tk.PhotoImage(file=path))

    # Campos para nombre, descripción y visibilidad
    ttk.Label(edit_window, text="Nombre del repositorio:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    nombre_var = tk.StringVar(value=repo_data.get("name", ""))
    ttk.Entry(edit_window, textvariable=nombre_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(edit_window, text="Descripción:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    descripcion_var = tk.StringVar(value=repo_data.get("description", ""))
    ttk.Entry(edit_window, textvariable=descripcion_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(edit_window, text="Visibilidad:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    visibilidad_var = tk.StringVar(value="Privado" if repo_data.get("private", False) else "Público")
    ttk.OptionMenu(edit_window, visibilidad_var, "Público", "Privado").grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # Botón para guardar los cambios
    ttk.Button(edit_window, text="Guardar Cambios", command=guardar_cambios).grid(row=3, columnspan=2, pady=10)

def clone_respository():
    try:
        item = repostree.selection()[0]
        clone_url = repostree.item(item, "values")[5]
        path_folder = filedialog.askdirectory(title="Select the folder where you want to clone the repository")
        
        if not path_folder:
            return
        
        command = ["git", "clone", clone_url, path_folder]
        subprocess.Popen(command, shell=True)
        
        ms.showinfo("SUCCESS", f"Repository cloned successfully in: {path_folder}.")
    except IndexError:
        ms.showerror("ERROR", "Please select a repository to clone.")
    except subprocess.CalledProcessError as e:
        ms.showerror("ERROR", f"Error cloning repository:\n{e}")
    except Exception as e:
        ms.showerror("ERROR", f"Inesperated error:\n{e}")

def github_profile():
    mygithub = ttk.Toplevel(root)
    mygithub.title("My GitHub Profile")
    mygithub.iconphoto(True, tk.PhotoImage(file=path))
    
    global repostree
    
    frame = ttk.Frame(mygithub)
    frame.pack(expand=True, fill="both")
    
    columns = ("Name", "Description", "Language", "URL", "Visibility", "Clone URL")
    repostree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
    repostree.heading("Name", text="Name")
    repostree.heading("Description", text="Description")
    repostree.heading("Language", text="Language")
    repostree.heading("URL", text="URL")
    repostree.heading("Visibility", text="Visibility")
    repostree.heading("Clone URL", text="Clone URL")
    
    repostree.pack(expand=True, fill="both")
    
    def menu_contextual(event):
        """Muestra el menú contextual en el Treeview."""
        # Seleccionar el elemento en el que se hizo clic
        item = repostree.identify_row(event.y)
        if item:
            repostree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
        else:
            repostree.selection_remove(tree.selection())
    
    repostree.bind("<Double-1>", open_repository)
    repostree.bind("<Button-3>", menu_contextual)
    
    context_menu = tk.Menu(mygithub, tearoff=0)
    context_menu.add_command(label="Delete Repository", command=lambda: delete_repository_github(repostree.item(repostree.selection(), "values")[0]))
    context_menu.add_command(label="Editr Repository", command=lambda: edit_repository(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="Crear Nuevo Repositorio", command=create_repository_github)
    context_menu.add_command(label="Clone Repository", command=clone_respository)
    
    btn_load = ttk.Button(frame, text="Load Repositories", command=show_github_repos)
    btn_load.pack(pady=5)
    show_github_repos()

def show_docu():
    docu = tk.Toplevel(root)
    docu.title("Python Documentation")
    docu.iconphoto(True, tk.PhotoImage(file=path))
    
    def load_documentation():
        topic = m_var.get().strip()
        url = f"https://docs.python.org/3/library/{topic}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                url = f"https://docs.python.org/3/library/{topic}"
                webview.create_window("Python Documentation", url)
                docu.destroy()
                webview.start(icon=path2)
            else:
                ms.showerror("ERROR", f"Documentation for '{topic}' not found.")
        except requests.exceptions.RequestException as e:
            ms.showerror("ERROR",f"Error loading documentation: {e}")
    
    t_label = ttk.Label(docu, text="Enter module name (e.g., json, os, sys):")
    t_label.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
    
    m_var = tk.StringVar()
    m_entry = ttk.Entry(docu, width=50, textvariable=m_var)
    m_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
    
    load_button = ttk.Button(docu, text="Load Documentation", command=load_documentation)
    load_button.grid(row=5, columnspan=2, padx=2, pady=2, sticky="ew")

path = resource_path(img)
path2 = resource_path2("./software.png")
root = ThemedTk()
root.title('Proyect Organizer')
root.geometry("1550x500")
root.iconphoto(True, tk.PhotoImage(file=path))
temas = root.get_themes()
ttkbootstrap_themes = ttk_themes()

main_frame = ttk.Frame(root)
main_frame.pack()

def adjust_window_size(event=None):
    root.update_idletasks()
    tree.config(height=root.winfo_height() - 310)
    
    new_width = 300
    depend_widht = 280
    nombre_entry.config(width=new_width)
    descripcion_entry.config(width=new_width)
    repo_entry.config(width=new_width)
    depen_entry.config(width=depend_widht)
    
def restore_window_size(event=None):
    root.update_idletasks()
    tree.config(height=root.winfo_height() - 310)
    
    new_width = 300
    depend_width = 280
    nombre_entry.config(width=new_width)
    descripcion_entry.config(width=new_width)
    repo_entry.config(width=new_width)
    depen_entry.config(width=depend_width)

    if root.state() != "zoomed": 
        nombre_entry.config(width=100)
        descripcion_entry.config(width=100)
        repo_entry.config(width=100)
        depen_entry.config(width=100)

def install_editor(name=""):
    if name == "Visual Studio Code":
        url = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
        file_name = 'vscode_win64.exe'
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Sublime Text":
        url = "https://download.sublimetext.com/Sublime%20Text%20Build%203211%20x64%20Setup.exe"
        file_name = "SubText_win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Vim":
        hvim = ms.askyesno("VIM", "You have choco install on your pc")
        if hvim:
            command = "choco install vim"
            subprocess.Popen([command], shell=True)
        else:
            scoop_install = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
            command = "scoop install vim"
            subprocess.Popen([scoop_install], shell=True).wait()
            subprocess.Popen([command], shell=True).wait()
            ms.showinfo("Vim", F"{name} has been installed")
    elif name == "Neovim":
        hvim = ms.askyesno(f"{name}", "You have scoop install on your pc")
        if hvim:
            command = "scoop install neovim"
            subprocess.Popen([command], shell=True)
        else:
            scoop_install = "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"
            command = "scoop install neovim"
            subprocess.Popen([scoop_install], shell=True).wait()
            subprocess.Popen([command], shell=True).wait()
            ms.showinfo(f"{name}", f"{name} has been installed")
    elif name == "Emacs":
        url = "http://ftp.rediris.es/mirror/GNU/emacs/windows/emacs-29/emacs-29.1-installer.exe"
        file_name = "Emacs_win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Notepad++":
        url = "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.4/npp.8.6.4.Installer.x64.exe"
        file_name = "Notepad++_win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Brackets":
        url = "https://github.com/brackets-cont/brackets/releases/download/v2.1.3/Brackets-2.1.3.exe"
        file_name = "Brackets_Win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Geany":
        url = "https://download.geany.org/geany-2.0_setup.exe"
        file_name = "Geany2.0_Win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
            geany_plugins = ms.askyesno(f"{name} PLUGINS", f"You want install {name}-Plugins to have more plugins")
            if geany_plugins:
                url = "https://plugins.geany.org/geany-plugins/geany-plugins-2.0_setup.exe"
                file_name  = "Geany_plugins_Win64.exe"
                response = requests.get(url)
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                quest = ms.askyesno("INSTALL", f"Do you want to install Geany-Plugins now?")
                if quest:
                    subprocess.Popen([file_name], shell=True).wait()
                    os.remove(file_name)
                else:
                    ms.showinfo("INSTALL LATER", f"You can install Geany-Plugins later, the installer is saved in the same folder as this app")
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Nano":
        hnano = ms.askyesno(f"{name}", f"you have scoop installed")
        if hnano:
            command = "scoop install nano"
            subprocess.Popen([command], shell=True).wait()
            ms.showinfo(f"{name}", f"{name} has been installed")
        else:
            scoop_install = "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"
            command = "scoop install nano"
            subprocess.Popen([scoop_install], shell=True).wait()
            ms.showinfo("Scoop", "Scoop has ben installed")
            subprocess.Popen([command], shell=True).wait()
            ms.showinfo(f"{name}", f"{name} has been installed")
    elif name ==  "Kate":
        url = "https://cdn.kde.org/ci-builds/utilities/kate/master/windows/kate-master-7254-windows-cl-msvc2022-x86_64.exe"
        file_name = "Kate_Win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Eclipse":
        url = "https://www.eclipse.org/downloads/download.php?file=/oomph/epp/2024-03/R/eclipse-inst-jre-win64.exe&mirror_id=1285"
        file_name = "Eclipse_X86_64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
    elif name == "Intellij IDEA":
        url = "https://www.jetbrains.com/idea/download/download-thanks.html?platform=windows"
        file_name = "Intellij_Win64.exe"
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {name} now?")
        if quest:
            subprocess.Popen([file_name], shell=True).wait()
            os.remove(file_name)
            buy = ms.askyesno("Intellij IDEA", "Free 30-day trial.If you want to buy a license, go to this link https://www.jetbrains.com/idea/buy/?section=personal&billing=monthly")
            if buy:
                webbrowser.open("https://www.jetbrains.com/idea/buy/?section=personal&billing=monthly")
        else:
            ms.showinfo("INSTALL LATER", f"You can install {name} later, the installer is saved in the same folder as this app")
            buy = ms.askyesno("Intellij IDEA", "Free 30-day trial.you want buy a license?")
            if buy:
                webbrowser.open("https://www.jetbrains.com/idea/buy/?section=personal&billing=monthly")
    elif name == "Android Studio":
        ms.showinfo("ANDROID STUDIO", "Android Studio can't be installed automatically. You go to the web for download")
        webbrowser.open("https://developer.android.com/studio")
        

filas_ocultas = set()

editores_disponibles = ["Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio", "neovim"]

lenguajes = ["Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go", "flutter"]

menu = tk.Menu(root)
root.config(menu=menu)

menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Proyects", menu=menu_archivo)
menu_archivo.add_command(label='Agree Proyect', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Create New', command=crear_nuevo_proyecto)
#menu_archivo.add_command(label="Create Template", command=crear_plantilla)
#menu_archivo.add_command(label="Apply template", command=aplicar_plantilla)
menu_archivo.add_command(label="My Github profile", command=github_profile)
menu_archivo.add_command(label="New Project Github", command=abrir_proyecto_github)
menu_archivo.add_command(label="Push Update Github", command=lambda: push_actualizaciones_github(tree.item(tree.selection())['values'][5]))
menu_archivo.add_command(label='Delete Proyect', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4]))
menu_archivo.add_command(label="Generate Report", command=generar_informe)

menu.add_command(label="Settings", command=setting_window)

help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="InfoVersion", command=ver_info)
help_menu.add_command(label="Documentation", command=show_docu)

nombre_label = ttk.Label(main_frame, text="Name:")
nombre_label.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

nombre_entry = ttk.Entry(main_frame, width=100)
nombre_entry.grid(row=1, column=1, pady=5, padx=5)

descripcion_label = ttk.Label(main_frame, text='Description:')
descripcion_label.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

descripcion_entry = ttk.Entry(main_frame, width=100)
descripcion_entry.grid(row=2, column=1, pady=5, padx=5)

repo_label = ttk.Label(main_frame, text="Repository URL:")
repo_label.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

repo_entry = ttk.Entry(main_frame, width=100)
repo_entry.grid(row=3, column=1, pady=5, padx=5)

depen_label = ttk.Label(main_frame, text="Dependencies:")
depen_label.grid(row=4, column=0, pady=5, padx=5, sticky="nsew")

depen_entry = ttk.Entry(main_frame, width=100)
depen_entry.grid(row=4, column=1, pady=5, padx=5)

tree = ttk.Treeview(main_frame, columns=('ID', 'Nombre', 'Descripcion', 'Lenguaje', 'Ruta', 'Repositorio'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Name')
tree.heading('Descripcion', text='Description')
tree.heading('Lenguaje', text='Lenguaje')
tree.heading('Ruta', text='Path')
tree.heading('Repositorio', text='Repository')
tree.grid(row=5, columnspan=2, pady=5, padx=5, sticky="nsew")


scrollbar_y = ttk.Scrollbar(main_frame, orient='vertical', command=tree.yview)
scrollbar_y.grid(row=5, column=2, sticky='ns')

tree.configure(yscrollcommand=scrollbar_y.set)

selected_editor = tk.StringVar()
editor_options = [
        "Select a Editor",
        "Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Blend Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio", "Editor Integrated", "neovim"
    ]
selected_editor.set(editor_options[0])
editor_menu = ttk.OptionMenu(main_frame, selected_editor, *editor_options)
editor_menu.grid(row=10, column=0, padx=5, pady=5, sticky="sw")

tree.bind("<Button-3>", show_context_menu)
tree.bind("<Double-1>", abrir_repositorio)
tree.bind("<Control-1>", abrir_explorador)
tree.bind("<<TreeviewSelect>>", on_project_select)

search_label = ttk.Label(main_frame, text="Search")
search_label.grid(row=9, column=0, padx=2, pady=2, sticky="ew")

search_entry = ttk.Entry(main_frame, width=170)
search_entry.grid(row=9, column=1, padx=2, pady=2, sticky="ew")
search_entry.bind("<KeyRelease>", on_key_release)

btn_abrir = ttk.Button(main_frame, text='Open Proyect', command=lambda: abrir_threading(tree.item(tree.selection())['values'][4], selected_editor.get()))
btn_abrir.grid(row=10, columnspan=2, pady=5, padx=5, sticky="s")

btn_install = ttk.Button(main_frame, text="Install dependencies", command=lambda: install_librarys(tree.item(tree.selection())['values'][3]))
btn_install.grid(row=4, column=1, padx=5, pady=5, sticky="e")

version_label = ttk.Label(main_frame, text=version)
version_label.grid(row=10, column=1, pady=5, padx=5, sticky="se")

root.bind("<Control-q>", lambda e: root.quit())

root.grid_rowconfigure(5, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(2, weight=1)

crear_base_datos()
mostrar_proyectos()
set_default_theme()
check_new_version()
thread_sinc()
initialize_backup_schedule()
root.mainloop()
