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
import base64
#---------------------------------------------------------#
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
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Progressbar

main_version = "ver.1.9.6"
version = str(main_version)
archivo_configuracion_editores = "configuracion_editores.json"
archivo_confgiguracion_github = "configuracion_github.json"
archivo_configuracion_gpt = "configuration_gpt.json"
BACKUP_STATE_FILE = "backup_schedule.json"
security_backup = "security_backup.json"
config_file = "config.json"
cache_file = "cache.json"
selected_project_path = None
text_editor = None
app_name = "./Organizer_linux"
exe_path = os.path.abspath(sys.argv[0])
current_version = "v1.9.6"
img = "software.png"

VCS_DIR = ".myvcs"
vcs_configfile = ".myvcs/config.json"
vcs_githubconfigfile = ".myvcs/github_config.json"
selected_file = None
file_name = None

def search_github_key():
    config = load_config()
    
    if "GITHUB_TOKEN" in config and is_github_token_valid(config["GITHUB_TOKEN"]):
        return config["GITHUB_TOKEN"]
    
    if not check_network():
        ms.showwarning("⚠️ No Network Connection", "No network connection. Unable to validate the API Key.")
        token = config.get("GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token:
            return token
        else:
            return None
    
    posible_name = ["GITHUB", "TOKEN", "API", "KEY", "SECRET"]

    for name_var, valor in os.environ.items():
        if any(clave in name_var.upper() for clave in posible_name):
            if is_github_token_valid(valor):
                config["GITHUB_TOKEN"] = valor
                save_config(config)
                return valor

    posibles_archivos = ["~/.bashrc", "~/.profile", "~/.zshrc", "/etc/environment"]
    for archivo in posibles_archivos:
        ruta_exp = os.path.expanduser(archivo)
        if os.path.exists(ruta_exp):
            with open(ruta_exp, "r") as f:
                for linea in f:
                    if any(clave in linea.upper() for clave in posible_name):
                        valor = extraer_variable(linea)
                        if valor and is_github_token_valid(valor):
                            return valor

    ms.showwarning("⚠️ GitHub API Key Not Found", "No API Key found. Please enter one to continue.")
    
    while True:
        token = simpledialog.askstring("🔑 Enter GitHub API Key", "Enter your GitHub API Key:", show="*")
        
        if not token:
            ms.showerror("❌ Error", "No API Key entered.")
            return None
        
        if is_github_token_valid(token):
            config["GITHUB_TOKEN"] = token
            save_config(config)
            return token
        else:
            ms.showerror("❌ Error", "Invalid API Key. Try again.")
    
def extraer_variable(linea):
    partes = linea.strip().split("=")
    if len(partes) == 2:
        return partes[1].strip().replace('"', '')
    return None

def is_github_token_valid(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def obtain_github_user():
    url = "https://api.github.com/user"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        user = response.json()
        return user["login"]
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Can't obtain the GitHub user: {str(e)}")

def check_network():
    try:
        requests.get("https://api.github.com", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False 

def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}
    
def save_config(data):
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

GITHUB_TOKEN = search_github_key()
GITHUB_USER = obtain_github_user() if GITHUB_TOKEN else None

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
        ("Create Workspace", lambda: save_project_file(tree.item(tree.selection())['values'][0],tree.item(tree.selection())['values'][4], selected_editor.get())),
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

def save_project_file(id_project, project_path, editor):
    project_data = {
        "id_project": id_project,
        "project_path": project_path,
        "editor": editor
        }
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".orga",
        filetypes=[("Project Files", ".orga")],
        title="Project Save",
        )
    
    if file_path:
        try:
            with open(file_path, 'w') as file:
                json.dump(project_data, file, indent=4)
            ms.showinfo("Success", f"Project workstation save on: {file_path}")
        except Exception as e:
            ms.showerror("ERROR", f"Can't save file: {e}")

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

def view_file_contents(repo_name, file_path):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        file_data = response.json()
        file_content = base64.b64decode(file_data["content"]).decode("utf-8")
        return file_content
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error al obtener el contenido del archivo: {e}")
        return ""

def update_file_content(repo_name, file_path, new_content, commit_message):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}"
    try:
        # Obtener el SHA actual del archivo
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        file_data = response.json()
        sha = file_data["sha"]

        # Crear el payload para actualizar el archivo
        data = {
            "message": commit_message,
            "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }

        # Enviar la solicitud de actualización
        response = requests.put(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"},
                                json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error al actualizar el archivo: {e}")

def list_repo_contents(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        contents = response.json()
        return contents
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error al obtener los contenidos del repositorio: {e}")
        return []

def unify_windows():
    """Unifies all the separate windows into a single window."""
    github = tk.Toplevel(root)
    github.title("GitHub Repository Manager")
    github.iconphoto(True, tk.PhotoImage(file=path))
    
    # Create a notebook (tabbed interface)
    notebook = ttk.Notebook(github, bootstyle='primary')
    notebook.pack(expand=True, fill="both")

    # Create frames for each tab
    mygithub_frame = ttk.Frame(notebook)
    commits_frame = ttk.Frame(notebook)
    file_frame = ttk.Frame(notebook)
    release_frame = ttk.Frame(notebook)
    edit_frame = ttk.Frame(notebook)
    issues_frame = ttk.Frame(notebook)
    stats_frame = ttk.Frame(notebook)
    search_frame = ttk.Frame(notebook)
    repo_view_frame = ttk.Frame(notebook)
    search_code_frame = ttk.Frame(notebook)
    security_frame = ttk.Frame(notebook)

    # Add tabs to the notebook
    notebook.add(mygithub_frame, text="My GitHub", padding=5)
    notebook.add(commits_frame, text="Repo Commits", padding=5)
    notebook.add(file_frame, text="Files", padding=5)
    notebook.add(release_frame, text="Releases", padding=5)
    notebook.add(edit_frame, text="Edit Repository", padding=5)
    notebook.add(security_frame, text="Security", padding=5)
    notebook.add(issues_frame, text="Issues", padding=5)
    notebook.add(stats_frame, text="Stats", padding=5)
    notebook.add(search_frame, text="Search Repos", padding=5)
    notebook.add(repo_view_frame, text="Repos View", padding=5)
    notebook.add(search_code_frame, text="Gtihub Search", padding=5)
    
    # Define columns for the repository Treeview
    columns = ("Name", "Description", "Language", "URL", "Visibility", "Clone URL")
    
    repostree = ttk.Treeview(mygithub_frame, columns=columns, show="headings", height=20, bootstyle="secondary")
    
    repostree.heading("Name", text="Name")
    repostree.heading("Description", text="Description")
    repostree.heading("Language", text="Language")
    repostree.heading("URL", text="URL")
    repostree.heading("Visibility", text="Visibility")
    repostree.heading("Clone URL", text="Clone URL")
    
    # Add a scrollbar to the Treeview
    scrollb = ttk.Scrollbar(mygithub_frame, orient="vertical", command=repostree.yview, bootstyle="info")
    repostree.configure(yscrollcommand=scrollb.set)
    scrollb.pack(side=RIGHT, fill=Y, padx=5, pady=5)
    
    repostree.pack(expand=True, fill="both", padx=10, pady=10)
    
    columns = ("Package", "Severity", "Description", "Fix Version")
    security_tree = ttk.Treeview(security_frame, columns=columns, show="headings", height=20, bootstyle='primary')
    security_tree.pack(padx=10, pady=10, fill="both", expand=True)

    security_tree.heading("Package", text="Package")
    security_tree.heading("Severity", text="Severity")
    security_tree.heading("Description", text="Description")
    security_tree.heading("Fix Version", text="Fix Version")

    scrollb_security = ttk.Scrollbar(security_frame, orient="vertical", command=security_tree.yview)
    scrollb_security.pack(side=RIGHT, fill=Y, padx=5)
    security_tree.configure(yscrollcommand=scrollb_security.set)

    fix_security_btn = ttk.Button(security_frame, text="Fix Vulnerability", bootstyle=SUCCESS)
    fix_security_btn.pack(side='bottom', pady=5, fill='x', expand=True)
    
    version_label = ttk.Label(github, text=f'{version}', bootstyle='info')
    version_label.pack(side='right', fill='x', padx=5, pady=5)

    status_label = ttk.Label(github, text=f'Github Connection Status: 🔵 Checking...', bootstyle='info')
    status_label.pack(side='left', fill='x', padx=5, pady=5)
    
    def check_github_status():
        try:
            response = requests.get("https://www.githubstatus.com/api/v2/status.json")
            response.raise_for_status()

            status = response.json()

            if status['status']['indicator'] == 'none':
                status_label.config(text="Github Connection Status: 🟢", bootstyle='success')
            else:
                status_label.config(text="Github Connection Status: 🔴", bootstyle='danger')
        except requests.exceptions.RequestException as e:
            status_label.config(text="Error checking GitHub status: 🔴 No internet connection", bootstyle='danger')
    
    def filter_repositories(event):
        query = search_var.get().lower()
        for item in repostree.get_children():
            repo_name = repostree.item(item, "values")[0].lower()
            if query in repo_name:
                repostree.item(item, open=True)
                repostree.selection_set(item)
            else:
                repostree.selection_remove(item)
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(mygithub_frame, textvariable=search_var, width=40)
    search_entry.pack(pady=5)
    search_entry.bind("<KeyRelease>", filter_repositories)
    
    def menu_contextual(event):
        """Muestra el menú contextual en el Treeview."""
        # Seleccionar el elemento en el que se hizo clic
        item = repostree.identify_row(event.y)
        if item:
            repostree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
        else:
            repostree.selection_remove(tree.selection())
            
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
            
    def backup_repository(repo_name):
        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/zipball"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()

            save_path = filedialog.asksaveasfilename(initialfile=f"{repo_name}.zip", defaultextension=".zip", filetypes=[("ZIP Files", "*.zip")])
            if not save_path:
                return

            # 🔹 Crear ventana con Progressbar
            progress_window = tk.Toplevel(root)
            progress_window.title("Creating Backup...")
            ttk.Label(progress_window, text=f"Creating backup of {repo_name}...").pack(pady=5)
            progress = Progressbar(progress_window, mode="determinate", length=300)
            progress.pack(padx=10, pady=10)

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:  # Evitar división por cero
                            progress["value"] = (downloaded_size / total_size) * 100
                        else:
                            progress["value"] = 100  # Completar el progreso si no hay tamaño total
                        progress_window.update_idletasks()

            progress["value"] = 100
            progress_window.destroy()
            ms.showinfo("Éxito", f"Backup of '{repo_name}' save on {save_path}")

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Cant't create the backup: {e}")
            
    def show_repo_issues(repo_name):
        notebook.select(issues_frame)

        for widget in issues_frame.winfo_children():
            widget.destroy()

        ttk.Label(issues_frame, text=f"🐞 Issues of {repo_name}", font=("Arial", 14, "bold")).pack(pady=10)

        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            issues = response.json()

            for issue in issues:
                ttk.Label(issues_frame, text=f"#{issue['number']} - {issue['title']}", font=("Arial", 12, "bold")).pack(anchor="w")
                ttk.Label(issues_frame, text=issue["body"], wraplength=600, justify="left").pack(anchor="w", padx=10, pady=5)

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"cant't obtain the issues: {e}")
            
    def open_repository(event):
        item = repostree.selection()
        if item:
            repo_url = repostree.item(item, "values")[3]
            webbrowser.open_new_tab(repo_url)
    
    repostree.bind("<Double-1>", open_repository)
    repostree.bind("<Button-3>", menu_contextual)
    
    context_menu = tk.Menu(github, tearoff=0)
    context_menu.add_command(label="🗑️Delete Repository", command=lambda: delete_repository_github(repostree.item(repostree.selection(), "values")[0]))
    context_menu.add_command(label="✏️ Edit Repository", command=lambda: edit_repository1(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="🚀 Github Releases", command=lambda: manage_github_release1(repostree.item(repostree.selection(), "values")[0]))
    context_menu.add_command(label="🔄 Commits History", command=lambda: show_github_comits1(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="⭐ Quit Star", command=lambda: unstar_repository(repostree.item(repostree.selection()[0], "values")[0], repostree.item(repostree.selection()[0], "values")[3].split('/')[-2]))
    context_menu.add_command(label="🔐 Security Alerts", command=lambda: on_security_analysis_button_click())
    context_menu.add_command(label="➕ Create New Repository", command=create_repository_github)
    context_menu.add_command(label="📂 Clone Repository", command=clone_respository)
    context_menu.add_command(label="🗂️View Files", command=lambda: open_repo_files1(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="📊 Show Statistics", command=lambda: show_repo_stats(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="📦 Create Backup", command=lambda: backup_repository(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="🐞 Show Issues", command=lambda: show_repo_issues(repostree.item(repostree.selection()[0], "values")[0]))
    
    def unstar_repository(repo_name, repo_owner):
        url = f"https://api.github.com/user/starred/{repo_owner}/{repo_name}"
        try:
            response = requests.delete(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            if response.status_code == 204:
                ms.showinfo("Éxito", f"Has quitado la estrella del repositorio '{repo_name}'.")
                show_github_repos()
            else:
                ms.showerror("Error", f"No se pudo quitar la estrella: {response.status_code}")
        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Error al quitar la estrella: {e}")
    
    def on_security_analysis_button_click():
        selected_item = repostree.selection()
        
        if not selected_item:
            ms.showwarning("No selection", "Please select a repository first.")
            return
        
        selected_repo = repostree.item(selected_item, "values")
        repo_name = selected_repo[0]
        owner_name = selected_repo[3].split('/')[-2]
        
        token = GITHUB_TOKEN
        
        notebook.select(security_frame)
        
        security_check(owner_name, repo_name, token)
    
    def security_check(owner, repo, token):
        def show_security_alerts(owner, repo, token):
            url = f"https://api.github.com/repos/{owner}/{repo}/dependabot/alerts"
        
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                alerts = response.json()
                
                for row in security_tree.get_children():
                    security_tree.delete(row)
                
                if alerts:
                    for alert in alerts:
                        if alert.get('state') == 'open':
                            package = alert['dependency']['package']['name']
                            severity = alert.get('severity', 'Unknown')
                            description = alert.get('description', 'No description available')
                            fix_version = alert.get('fixed_in', 'Not fixed')
                            

                            if severity == "high":
                                tag = "high_severity"
                            elif severity == "medium":
                                tag = "medium_severity"
                            elif severity == "low":
                                tag = "low_severity"
                            else:
                                tag = "unknown_severity"
                            
                            security_tree.insert("", "end", values=(package, severity, description, fix_version), tags=(tag,))
                
                else:
                    security_tree.insert("", "end", values=("No open security vulnerabilities found.", "", "", ""), tags=("no_vulnerabilities",))
                
                security_tree.tag_configure("high_severity", background="red", foreground="white")
                security_tree.tag_configure("medium_severity", background="yellow", foreground="black")
                security_tree.tag_configure("low_severity", background="green", foreground="white")
                security_tree.tag_configure("unknown_severity", background="gray", foreground="black")
                security_tree.tag_configure("no_vulnerabilities", background="lightgray", foreground="black")
            
            else:
                ms.showerror("Error", f"Error fetching security alerts: {response.status_code}")
            
        def fix_all_security_issues(owner, repo, token):
            vulnerabilities = []
            for item in security_tree.get_children():
                selected_values = security_tree.item(item, "values")
                if selected_values:
                    package = selected_values[0]
                    fix_version = selected_values[3]
                    
                    if fix_version and fix_version != "Not fixed":
                        vulnerabilities.append((package, fix_version))

            if not vulnerabilities:
                ms.showinfo("No vulnerabilities", "No vulnerabilities with fix versions available.")
                return

            for vulnerable_package, fix_version in vulnerabilities:
                fix_dependency(owner, repo, token, vulnerable_package, fix_version)

            ms.showinfo("Success", "All vulnerabilities with fix versions have been corrected.")
        
        fix_security_btn.config(command=lambda: fix_all_security_issues(owner, repo, token))    
            
        show_security_alerts(owner, repo, token)
    
    def fix_dependency(owner, repo, token, vulnerable_package, fix_version, branch="main"):
        file_paths = ["requirements.txt", "package.json", "pom.xml", "composer.json"]
        file_to_update = None
        
        for file_path in file_paths:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                file_to_update = file_path
                content_data = response.json()
                sha = content_data['sha']
                content = content_data['content']
                break
        
        if not file_to_update:
            ms.showerror("Error", "No dependency file found.")
            return
        
        decoded_content = base64.b64decode(content).decode('utf-8')

        updated_content = update_dependency_in_file(decoded_content, vulnerable_package, fix_version, file_to_update)

        commit_message = f"Update {vulnerable_package} to version {fix_version} in {file_to_update}"
        commit_data = {
            "message": commit_message,
            "sha": sha,
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        }

        commit_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_to_update}"
        commit_response = requests.put(commit_url, headers=headers, data=json.dumps(commit_data))

        if commit_response.status_code == 200:
            ms.showinfo("Success", f"Dependency {vulnerable_package} updated successfully in {file_to_update}!")
            
            pr_data = {
                "title": f"Update {vulnerable_package} to {fix_version} in {file_to_update}",
                "head": branch,
                "base": "main",
                "body": f"This PR updates {vulnerable_package} to the latest secure version {fix_version} in {file_to_update}"
            }

            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            pr_response = requests.post(pr_url, headers=headers, data=json.dumps(pr_data))

            if pr_response.status_code == 201:
                ms.showinfo("Pull Request Created", "A pull request has been created for review.")
            else:
                ms.showerror("Error", "Failed to create pull request.")
        else:
            ms.showerror("Error", "Failed to commit the updated dependency.")
    
    def update_dependency_in_file(file_content, vulnerable_package, fix_version, file_type):
        if file_type == "requirements.txt":
            updated_content = file_content.replace(f"{vulnerable_package}==", f"{vulnerable_package}=={fix_version}")
        elif file_type == "package.json":
            updated_content = file_content.replace(f'"{vulnerable_package}": "', f'"{vulnerable_package}": "{fix_version}",')
        elif file_type == "pom.xml":
            updated_content = file_content.replace(f"<version>{vulnerable_package}</version>", f"<version>{fix_version}</version>")
        elif file_type == "composer.json":
            updated_content = file_content.replace(f'"{vulnerable_package}": "', f'"{vulnerable_package}": "{fix_version}",')
        else:
            updated_content = file_content
        return updated_content
    
    def show_github_repos():
        for item in repostree.get_children():
            repostree.delete(item)
        
        repos = obtain_github_repos()
        starred_repos = obtain_starred_repos()
        for repo in repos:
            repostree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], repo["visibility"], repo["clone_url"]))

        for repo in starred_repos:
            repostree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], "⭐ Destacado", repo["clone_url"]))
    
    def obtain_starred_repos():
        url = "https://api.github.com/user/starred"
        try:
            response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                "Accept": "application/vnd.github.v3+json"})
            response.raise_for_status()
            repos = response.json()
            return repos
        except requests.exceptions.RequestException as e:
            ms.showerror("ERROR", f"No se pueden obtener los repositorios con estrella: {e}")
            return []
            
    show_github_repos()
    
    def search_repositories():
        def search_repositories_global():
            query = search_var.get().strip()
            if not query:
                ms.showerror("Error", "Escribe algo para buscar.")
                return

            url = f"https://api.github.com/search/repositories?q={query}"
            try:
                response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                    "Accept": "application/vnd.github.v3+json"})
                response.raise_for_status()
                repos = response.json()["items"]

                for item in search_tree.get_children():
                    search_tree.delete(item)

                for repo in repos:
                    search_tree.insert("", "end", values=(repo["name"], repo["owner"]["login"], repo["stargazers_count"], repo["html_url"], repo["clone_url"]))

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"No se pudo buscar en GitHub: {e}")
        
        def star_repository(repo_name, repo_owner):
            url = f"https://api.github.com/user/starred/{repo_owner}/{repo_name}"
            try:
                response = requests.put(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
                if response.status_code == 204:
                    ms.showinfo("Éxito", f"Has dado estrella a '{repo_name}'.")
                else:
                    ms.showerror("Error", f"No se pudo dar estrella: {response.status_code}")
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Error al dar estrella: {e}")
        
        def search_menu_context(event):
            item = search_tree.identify_row(event.y)
            if item:
                search_tree.selection_set(item)
                search_context_menu.post(event.x_root, event.y_root)
                
        def on_repo_search_double_click(event):
            selected_item = search_tree.selection()
            if selected_item:
                repo_name = search_tree.item(selected_item, "values")[0]
                repo_owner = search_tree.item(selected_item, "values")[1]
                
                global repo_history
                repo_history = []

                view_repo_details(repo_name, repo_owner)

        search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=search_var, width=50).pack(pady=5, padx=10)
        ttk.Button(search_frame, text="🔍 Search", command=search_repositories_global).pack(pady=5)

        columns = ("Name", "Owner", "Stars", "URL", "Clone URL")
        search_tree = ttk.Treeview(search_frame, columns=columns, show="headings", height=15)

        search_tree.heading("Name", text="Name")
        search_tree.heading("Owner", text="Owner")
        search_tree.heading("Stars", text="⭐ Stars")
        search_tree.heading("URL", text="URL")
        search_tree.heading("Clone URL", text="Clone URL")

        search_tree.column("Name", width=200)
        search_tree.column("Owner", width=150)
        search_tree.column("Stars", width=100)
        search_tree.column("URL", width=250)
        search_tree.column("Clone URL", width=250)

        search_tree.pack(expand=True, fill="both", padx=5, pady=5)
        search_tree.bind("<Double-1>", on_repo_search_double_click)
        
        search_context_menu = tk.Menu(github, tearoff=0)
        search_context_menu.add_command(label="⭐ Agregar a Favoritos", command=lambda: star_repository(search_tree.item(search_tree.selection()[0], "values")[0], search_tree.item(search_tree.selection()[0], "values")[1]))
        #search_context_menu.add_command(label="🛠️ Clonar Repositorio", command=lambda: clone_repository_from_search())
    
    def view_repo_details(repo_name, repo_owner, path=""):
        notebook.select(repo_view_frame)


        if path and (not repo_history or repo_history[-1] != path):
            repo_history.append(path)

        for widget in repo_view_frame.winfo_children():
            widget.destroy()

        back_button = ttk.Button(repo_view_frame, text="⬅️ Atrás", command=lambda: go_back(repo_name, repo_owner))
        back_button.pack(pady=5, padx=10, anchor="w")

        if not repo_history:
            back_button["state"] = "disabled"

        ttk.Label(repo_view_frame, text=f"📂 Explorando {repo_owner}/{repo_name}/{path}", font=("Arial", 14, "bold")).pack(pady=5)

        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        if path == "":
            readme_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/readme"
            response_readme = requests.get(readme_url, headers=headers)

            if response_readme.status_code == 200:
                readme_data = response_readme.json()
                readme_content = base64.b64decode(readme_data["content"]).decode("utf-8")
                readme_html = markdown.markdown(readme_content)
            else:
                readme_html = "<p>This repository does not have a README.md.</p>"

            readme_frame = ttk.LabelFrame(repo_view_frame, text="📖 README.md", padding=10, bootstyle="info")
            readme_frame.pack(fill="both", padx=10, pady=5)

            readme_label = HTMLLabel(readme_frame, html=readme_html, background="white", padx=5, pady=5)
            readme_label.pack(expand=True, fill="both")

            ttk.Separator(repo_view_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

        file_list_frame = ttk.LabelFrame(repo_view_frame, text="📂 Files", padding=10, bootstyle="success")
        file_list_frame.pack(fill="both", padx=10, pady=5)

        file_tree = ttk.Treeview(file_list_frame, columns=("Name", "Type", "Path"), show="headings", height=15)
        file_tree.heading("Name", text="Name")
        file_tree.heading("Type", text="Type")
        file_tree.heading("Path", text="Full Path")
        file_tree.column("Name", width=300)
        file_tree.column("Type", width=100)
        file_tree.column("Path", width=0, stretch=False)
        file_tree.pack(expand=True, fill="both", padx=5, pady=5)

        files_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
        response_files = requests.get(files_url, headers=headers)

        if response_files.status_code == 200:
            files = response_files.json()
            for file in files:
                file_tree.insert("", "end", values=(file.get("name"), file.get("type"), file.get("path")))

        else:
            ms.showerror("Error", f"Could not get the files of the repository: {response_files.status_code}")

        def on_file_double_click(event):
            selected_item = file_tree.selection()
            if selected_item:
                file_name, file_type, file_path = file_tree.item(selected_item, "values")
                if file_type == "dir":
                    view_repo_details(repo_name, repo_owner, file_path)
                elif file_type == "file":
                    view_file_content(repo_name, repo_owner, file_path)

        file_tree.bind("<Double-1>", on_file_double_click)
        
    def view_file_content(repo_name, repo_owner, file_path):
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"

        try:
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            file_data = response.json()
            file_content = base64.b64decode(file_data["content"]).decode("utf-8")

            file_window = tk.Toplevel(github)
            file_window.title(f"📄 {file_path}")
            file_window.iconbitmap(path)

            ttk.Label(file_window, text=f"📄 {file_path}", font=("Arial", 12, "bold")).pack(pady=5)

            text_editor = CodeView(file_window, wrap="word", height=25)
            text_editor.pack(expand=True, fill="both", padx=10, pady=10)

            try:
                lexer = pygments.lexers.get_lexer_for_filename(file_path)
            except:
                lexer = pygments.lexers.get_lexer_by_name("text")

            text_editor.config(lexer=lexer)
            text_editor.insert("1.0", file_content)

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"No se pudo obtener el archivo: {e}")
    
    def go_back(repo_name, repo_owner):
        if repo_history:
            repo_history.pop()
            prev_path = repo_history[-1] if repo_history else ""
            view_repo_details(repo_name, repo_owner, prev_path)
    
    def show_repo_stats(repo_name):
        notebook.select(stats_frame)  # Cambia a la pestaña de estadísticas
        
        # Limpiar la pestaña antes de cargar nuevas estadísticas
        for widget in stats_frame.winfo_children():
            widget.destroy()

        ttk.Label(stats_frame, text=f"📊 Estadísticas de {repo_name}", font=("Arial", 16, "bold")).pack(pady=10)

        try:
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            repo_data = response.json()

            description = repo_data.get("description", "Este repositorio no tiene descripción.")

            # 🔹 Intentamos obtener el README.md
            readme_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/readme"
            response_readme = requests.get(readme_url, headers=headers)

            if response_readme.status_code == 200:
                readme_data = response_readme.json()
                readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8")
                readme_html = markdown.markdown(readme_content)  # Convertimos el README a HTML
            else:
                readme_html = f"<p>{description}</p>"  # Si no hay README, mostramos la descripción
                
            def get_total_downloads(repo_name, headers):
                total_downloads = 0
                releases_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases"
                response_releases = requests.get(releases_url, headers=headers)
                if response_releases.status_code == 200:
                    releases = response_releases.json()
                    for release in releases:
                        for asset in release.get("assets", []):
                            total_downloads += asset.get("download_count", 0)
                return total_downloads

            # 🔹 Función auxiliar para obtener clones del repo
            def get_total_clones(repo_name, headers):
                clones_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/traffic/clones"
                response_clones = requests.get(clones_url, headers=headers)
                if response_clones.status_code == 200:
                    clone_data = response_clones.json()
                    return clone_data.get("count", 0)  # Suma de clones en los últimos 14 días
                return 0

            # 🔹 Agregar un Frame para el README / Descripción
            readme_frame = ttk.LabelFrame(stats_frame, text="📖 README / Description", padding=10, bootstyle="info")
            readme_frame.pack(fill="both", padx=10, pady=5)

            readme_label = HTMLLabel(readme_frame, html=readme_html, background="white", padx=5, pady=5)
            readme_label.pack(expand=True, fill="both")

            # 🔹 Separador visual
            ttk.Separator(stats_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

            # 🔹 Sección de Estadísticas
            popularity_frame = ttk.LabelFrame(stats_frame, text="🌟 Popularity", padding=10, bootstyle="primary")
            popularity_frame.pack(fill="x", padx=10, pady=5)

            ttk.Label(popularity_frame, text=f"⭐ Estrellas: {repo_data.get('stargazers_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")
            ttk.Label(popularity_frame, text=f"🍴 Forks: {repo_data.get('forks_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")
            ttk.Label(popularity_frame, text=f"👀 Watchers: {repo_data.get('watchers_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")

            # 🔹 Separador
            ttk.Separator(stats_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

            # 🔹 Sección de Tráfico
            traffic_frame = ttk.LabelFrame(stats_frame, text="📈 Tráfic", padding=10, bootstyle="success")
            traffic_frame.pack(fill="x", padx=10, pady=5)

            ttk.Label(traffic_frame, text=f"📥 Releases Downloads: {get_total_downloads(repo_name, headers)}", font=("Arial", 12, "bold")).pack(anchor="w")
            ttk.Label(traffic_frame, text=f"🔄 Repo Clones (Last 14 days): {get_total_clones(repo_name, headers)}", font=("Arial", 12, "bold")).pack(anchor="w")

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Can't obtain the statistics of the repository: {e}")
    
    def edit_repository1(name):
        notebook.select(edit_frame)
        user = GITHUB_USER
        url = f"https://api.github.com/repos/{user}/{name}"

        # Obtener detalles actuales del repositorio para prellenar los valores
        try:
            response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            response.raise_for_status()
            repo_data = response.json()
        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"cant't obtain the repository data: {e}")
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
                ms.showinfo("Success", f"Repositorio '{name}' updated successfully.")
                for widget in edit_frame.winfo_children():
                    widget.destroy()
                notebook.select(mygithub_frame)# Cerrar la ventana de edición
                show_github_repos()  # Actualizar la lista de repositorios
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Error updating the repository: {e}")
                
        # Campos para nombre, descripción y visibilidad
        ttk.Label(edit_frame, text="Name of repository:", style="TLabel").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        nombre_var = tk.StringVar(value=repo_data.get("name", ""))
        ttk.Entry(edit_frame, textvariable=nombre_var, width=40, style="TEntry").grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(edit_frame, text="Description:", style="TLabel").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        descripcion_var = tk.StringVar(value=repo_data.get("description", ""))
        ttk.Entry(edit_frame, textvariable=descripcion_var, width=40, style="TEntry").grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(edit_frame, text="Visibility:", style="TLabel").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        visibilidad_var = tk.StringVar(value="Private" if repo_data.get("private", False) else "Públic")
        ttk.OptionMenu(edit_frame, visibilidad_var, "Públic", "Private", style="TMenubutton").grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Botón para guardar los cambios con estilo de ttkbootstrap
        ttk.Button(edit_frame, text="Save Changes", command=guardar_cambios, style="Success.TButton").grid(row=3, columnspan=2, pady=15)
        
    def open_repo_files1(repo_name):
        for widget in file_frame.winfo_children():
            widget.destroy()
            
        notebook.select(file_frame)
        
        # Frame para la lista de archivos
        file_list_frame = ttk.Frame(file_frame, padding=(5, 10))
        file_list_frame.pack(side="left", fill="y", padx=5, pady=5)

        # Treeview para listar archivos con estilo
        file_list = ttk.Treeview(file_list_frame, columns=("name", "type"), show="headings", selectmode="browse", style="success.Treeview")
        file_list.heading("name", text="Name", anchor="w")
        file_list.heading("type", text="Type", anchor="w")
        file_list.column("name", anchor="w", width=250)
        file_list.column("type", anchor="w", width=100)
        file_list.pack(expand=True, fill="y", padx=5)

        # Separador visual con estilo
        separator = ttk.Separator(file_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=5)

        # Frame para el editor de texto
        editor_frame = ttk.Frame(file_frame, padding=(10, 5))
        editor_frame.pack(side="right", expand=True, fill="both", padx=5, pady=5)

        # Editor de código (CodeView) con estilo
        text_editor = CodeView(editor_frame, wrap="word", width=150, height=20)
        text_editor.pack(expand=True, fill="both", padx=10, pady=10)

        # Campo para el mensaje del commit con estilo
        ttk.Label(editor_frame, text="Commit Message:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        commit_var = tk.StringVar()
        commit_entry = ttk.Entry(editor_frame, textvariable=commit_var, width=150, bootstyle=PRIMARY)
        commit_entry.pack(padx=5, pady=5)

        # Botón para guardar cambios con estilo mejorado
        save_button = ttk.Button(editor_frame, text="Save Changes", command=lambda: save_changes1(repo_name), width=20, bootstyle=SUCCESS)
        save_button.pack(pady=10)

        # Variable para rastrear el archivo actual
        current_file = tk.StringVar()
        
        # Función para cargar el contenido del archivo
        def load_file_content1(file_path):
            content = view_file_contents(repo_name, file_path)
            if content == "":
                return
            text_editor.delete("1.0", "end")
            try:
                lexer = pygments.lexers.get_lexer_for_filename(file_path)
            except Exception:
                lexer = pygments.lexers.get_lexer_by_name("text")
            text_editor.config(lexer=lexer)
            text_editor.insert("1.0", content)
            current_file.set(file_path)

        # Función para guardar los cambios
        def save_changes1(repo_name):
            file_path = current_file.get()
            if not file_path:
                ms.showerror("Error", "Don't have selected file to save.")
                return
            new_content = text_editor.get("1.0", "end-1c")
            commit_message = commit_var.get().strip()
            if not commit_message:
                ms.showerror("Error", "The commit message can't be empty.")
                return
            update_file_content(repo_name, file_path, new_content, commit_message)
            ms.showinfo("Success", f"File '{file_path}' saved successfully.")

        # Llenar la lista de archivos
        contents = list_repo_contents(repo_name)
        for item in contents:
            name = item.get("name", "Unknown")
            path = item.get("path", "")
            content_type = item.get("type", "Unknown")
            if content_type == "file":
                file_list.insert("", "end", values=(name, content_type))

        # Manejar selección de archivo
        def on_file_select1(event):
            selected_item = file_list.selection()
            if selected_item:
                file_path = file_list.item(selected_item, "values")[0]
                load_file_content1(file_path)

        file_list.bind("<<TreeviewSelect>>", on_file_select1)
    
    def manage_github_release1(repo_name):
        notebook.select(release_frame)
        def fetch_releases():
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases"
            try:
                response = requests.get(url, headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                })
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't fetch releases: {e}")
                return []
            
        def fetch_release_assets(release_id):
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases/{release_id}/assets"
            try:
                response = requests.get(url, headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                })
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't fetch assets: {e}")
                return []
        
        def populate_release_combobox():
            release_combobox["values"] = [
                f"{release['tag_name']} (Draft: {release['draft']}, Pre-release: {release['prerelease']})"
                for release in releases
            ]
            if releases:
                release_combobox.current(0)  # Seleccionar la primera opción
                on_release_select()
                
        def load_release_data(release_id):
            release = next((r for r in releases if str(r["id"]) == str(release_id)), None)
            if release:
                tag_var.set(release["tag_name"])
                name_var.set(release["name"])
                description_text.delete("1.0", "end")
                description_text.insert("1.0", release["body"] or "")
                draft_var.set(release["draft"])
                prerelease_var.set(release["prerelease"])
                current_release_id.set(release_id)

                # 📌 Cargar archivos adjuntos en el Treeview
                populate_asset_tree(release_id)
                update_preview()
            else:
                ms.showerror("Error", f"Release with ID {release_id} not found.")
                
        def populate_asset_tree(release_id):
            asset_tree.delete(*asset_tree.get_children())  # 🔄 Limpiar el Treeview antes de actualizar
            assets = fetch_release_assets(release_id)

            for asset in assets:
                asset_tree.insert("", "end", values=(asset["name"], asset["browser_download_url"], asset["id"]))

        def update_preview(event=None, clear=False):
            try:
                if clear:
                    preview_label.set_html("")  # 📌 Deja la vista previa vacía
                else:
                    raw_text = description_text.get("1.0", "end-1c")
                    html_content = markdown.markdown(raw_text)  # Convertir a HTML
                    preview_label.set_html(html_content)
            except Exception as e:
                preview_label.set_html(f"<p>Error rendering preview: {e}</p>")
        
        def save_release():
            tag_name = tag_var.get().strip()
            release_name = name_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            draft = draft_var.get()
            prerelease = prerelease_var.get()

            if not tag_name or not release_name:
                ms.showerror("Error", "The tag and release name are required.")
                return

            payload = {
                "tag_name": tag_name,
                "name": release_name,
                "body": description,
                "draft": draft,
                "prerelease": prerelease
            }

            release_id = current_release_id.get()

            if release_id:  # Si hay un ID de release, es una edición
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases/{release_id}"
                method = "PATCH"
            else:  # Si no hay ID de release, es una creación
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases"
                method = "POST"

            try:
                response = requests.request(method, url, headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }, json=payload)
                response.raise_for_status()

                ms.showinfo("Success", f"Release '{release_name}' saved successfully.")
                reload_releases()
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't save the release: {e}")

        def reload_releases():
            nonlocal releases
            releases = fetch_releases()
            populate_release_combobox()

        def reset_form():
            tag_var.set("")
            name_var.set("")
            description_text.delete("1.0", "end")
            draft_var.set(False)
            prerelease_var.set(False)
            current_release_id.set(None)
            asset_tree.delete(*asset_tree.get_children())
            update_preview(clear=True)
        
        def on_release_select(event=None):
            selected_index = release_combobox.current()
            if selected_index >= 0:
                selected_release = releases[selected_index]
                load_release_data(selected_release["id"])
                
        def add_files():
            release_id = current_release_id.get()
            if not release_id:
                ms.showerror("Error", "No release selected.")
                return

            file_paths = filedialog.askopenfilenames(title="Select files for the release", filetypes=[("All Files", "*.*")])
            if not file_paths:
                return

            for file_path in file_paths:
                try:
                    upload_file(file_path, release_id)
                except Exception as e:
                    ms.showerror("Error", f"Failed to upload {file_path}: {e}")

            # Recargar la lista de archivos
            load_release_data(release_id)

        def upload_file(file_path, release_id):
            with open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                url = f"https://uploads.github.com/repos/{GITHUB_USER}/{repo_name}/releases/{release_id}/assets?name={file_name}"
                headers = {
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }
                response = requests.post(url, headers=headers, files={'file': (file_name, file)})
                response.raise_for_status()

        def remove_files():
            selected_items = asset_tree.selection()  # 📌 Obtiene las filas seleccionadas en el Treeview

            if not selected_items:
                ms.showerror("Error", "No file selected.")
                return

            release_id = current_release_id.get()
            if not release_id:
                ms.showerror("Error", "No release selected.")
                return

            for item in selected_items:
                file_name, file_url, asset_id = asset_tree.item(item, "values")  # 📌 Obtiene los valores de la fila seleccionada
                try:
                    delete_file(asset_id)  # 📌 Eliminar el archivo en GitHub
                    asset_tree.delete(item)  # 📌 Eliminar la fila del Treeview
                except Exception as e:
                    ms.showerror("Error", f"Failed to delete {file_name}: {e}")

            # Recargar la lista de archivos
            load_release_data(release_id)

        def delete_file(asset_id):
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases/assets/{asset_id}"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
        def delete_release():
            selected_index = release_combobox.current()  # 📌 Obtiene el índice seleccionado
            if selected_index == -1:
                ms.showerror("Error", "No release selected.")
                return

            release = releases[selected_index]  # 📌 Obtiene la release seleccionada
            confirm = ms.askyesno("Confirm Delete", f"Are you sure you want to delete the release '{release['name']}'?")
            if not confirm:
                return

            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases/{release['id']}"
            try:
                response = requests.delete(url, headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                })
                response.raise_for_status()
                ms.showinfo("Success", f"Release '{release['name']}' deleted successfully.")
                reload_releases()  # 📌 Recargar el Combobox después de eliminar
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't delete the release: {e}")
                
        # Variables
        releases = fetch_releases()
        current_release_id = tk.StringVar()
        lexer = pygments.lexers.get_lexer_by_name("markdown")

        release_frame.grid_columnconfigure(0, weight=2)
        release_frame.grid_columnconfigure(1, weight=3)
        release_frame.grid_columnconfigure(2, weight=2)  # Ajuste para editor_frame
        release_frame.grid_rowconfigure(1, weight=1)
        release_frame.grid_rowconfigure(3, weight=1) 

        # Frame para seleccionar la release
        select_frame = ttk.LabelFrame(release_frame, text="Select Release", padding=10, bootstyle=INFO)
        select_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=5, pady=5)

        # Combobox para listar las releases
        ttk.Label(select_frame, text="Select Release:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        release_combobox = ttk.Combobox(select_frame, state="readonly", width=50)
        release_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        release_combobox.bind("<<ComboboxSelected>>", on_release_select)

        # Menú contextual para eliminar releases
        context_menu = tk.Menu(select_frame, tearoff=0)
        context_menu.add_command(label="Delete Release", command=delete_release)

        # Treeview para los archivos adjuntos (assets)
        ttk.Label(select_frame, text="Attached Files:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        asset_tree = ttk.Treeview(select_frame, columns=("Name", "URL"), show="headings", height=8)
        asset_tree.heading("Name", text="File Name")
        asset_tree.heading("URL", text="Download URL")
        asset_tree.column("Name", width=250, anchor="w")
        asset_tree.column("URL", width=400, anchor="w")
        asset_tree.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Botones de acción para releases y archivos
        button_frame = ttk.Frame(select_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        ttk.Button(button_frame, text="New Release", command=lambda: [reset_form(), release_combobox.set('')], bootstyle=PRIMARY).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Add File(s)", command=add_files, bootstyle=PRIMARY).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Remove Selected File(s)", command=remove_files, bootstyle=DANGER).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Frame para crear/editar releases
        editor_frame = ttk.LabelFrame(release_frame, text="Release Editor", padding=10, bootstyle=SUCCESS)
        editor_frame.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=5)

        # Ajustar la estructura del `editor_frame`
        editor_frame.grid_columnconfigure(1, weight=1)
        editor_frame.grid_rowconfigure(3, weight=1)

        ttk.Label(editor_frame, text="Tag:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tag_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=tag_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(editor_frame, text="Release Name:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        name_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=name_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(editor_frame, text="Description:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        description_text = CodeView(editor_frame, wrap="word", height=10, lexer=lexer)
        description_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        description_text.bind("<KeyRelease>", lambda e: update_preview())

        # Preview de la descripción
        ttk.Label(editor_frame, text="Preview:", font=("Arial", 10)).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        preview_label = HTMLLabel(editor_frame, background="white")
        preview_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Opciones adicionales
        options_frame = ttk.Frame(editor_frame)
        options_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        draft_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Mark as Draft", variable=draft_var, bootstyle=INFO).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        prerelease_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Mark as Pre-release", variable=prerelease_var, bootstyle=INFO).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Botón de Guardar
        ttk.Button(release_frame, text="✅ Save Release", command=save_release).grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")

        # Inicializar el Combobox
        populate_release_combobox()
      
    def show_github_comits1(repo_name):
        notebook.select(commits_frame)

        frame = ttk.Frame(commits_frame)
        frame.pack(expand=True, fill="both")

        paned_window = ttk.Panedwindow(frame, orient="horizontal")
        paned_window.pack(expand=True, fill="both")

        # Panel izquierdo - Archivos del repo
        files_frame = ttk.Labelframe(paned_window, text="Repository Files", padding=10, bootstyle=INFO)
        paned_window.add(files_frame, weight=2)

        file_tree = ttk.Treeview(files_frame, columns=("Path", "Type", "Size"), show="headings", height=15)
        file_tree.heading("Path", text="File Path")
        file_tree.heading("Type", text="Type")
        file_tree.heading("Size", text="Size (bytes)")
        file_tree.column("Path", width=300)
        file_tree.column("Type", width=100)
        file_tree.column("Size", width=100)
        file_tree.pack(expand=True, fill="both", padx=5, pady=5)
        
        def menu_contextual_file(event):
            item = file_tree.identify_row(event.y)
            if item:
                file_tree.selection_set(item)
                context_menu_file.post(event.x_root, event.y_root)
            else:
                file_tree.selection_remove(file_tree.selection())
                
        file_tree.bind("<Button-3>", menu_contextual_file)
        
        context_menu_file = tk.Menu(root, tearoff=0)
        context_menu_file.add_command(label="⬇️ Descargar Archivo", command=lambda: download_file(repo_name, file_tree.item(file_tree.selection(), "values")[0]))
        
        # Panel derecho - Historial de commits
        commits1_frame = ttk.Labelframe(paned_window, text="Commit History", padding=10, bootstyle=SUCCESS)
        paned_window.add(commits1_frame, weight=3)

        commit_tree = ttk.Treeview(commits1_frame, columns=("SHA", "Author", "Date", "Message"), show="headings", height=15)
        commit_tree.heading("SHA", text="Commit SHA")
        commit_tree.heading("Author", text="Author")
        commit_tree.heading("Date", text="Date")
        commit_tree.heading("Message", text="Message")
        commit_tree.column("SHA", width=100)
        commit_tree.column("Author", width=150)
        commit_tree.column("Date", width=150)
        commit_tree.column("Message", width=300)
        commit_tree.pack(expand=True, fill="both", padx=5, pady=5)

        # Panel inferior - CodeView para mostrar cambios
        changes_frame = ttk.Labelframe(commits1_frame, text="Code Changes", padding=10, bootstyle=INFO)
        changes_frame.pack(expand=True, fill="both", padx=5, pady=5)

        diff_viewer = CodeView(changes_frame, wrap="word", height=10)
        diff_viewer.pack(expand=True, fill="both", padx=10, pady=10)

        def download_file(repo_name, file_path):
            try:
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}"
                headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                file_data = response.json()

                file_content = base64.b64decode(file_data["content"])
                save_path = filedialog.asksaveasfilename(initialfile=file_path.split("/")[-1])

                if not save_path:
                    return

                # 🔹 Mostrar Progressbar
                progress_window = tk.Toplevel(root)
                progress_window.title("Downloading...")
                ttk.Label(progress_window, text=f"Downloading {file_path}...").pack(pady=5)
                progress = Progressbar(progress_window, mode="determinate", length=300)
                progress.pack(padx=10, pady=10)

                with open(save_path, "wb") as f:
                    chunk_size = 1024
                    total_size = len(file_content)
                    for i in range(0, total_size, chunk_size):
                        f.write(file_content[i:i+chunk_size])
                        progress["value"] = (i / total_size) * 100
                        progress_window.update_idletasks()

                progress["value"] = 100
                progress_window.destroy()
                ms.showinfo("Success", f"File '{file_path}' downloaded successfully.")

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't download the file: {e}")
        
        # Función para obtener los archivos del repositorio
        def load_files():
            file_tree.delete(*file_tree.get_children())
            try:
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents"
                headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                files = response.json()

                for file in files:
                    file_tree.insert("", "end", values=(file.get("path"), file.get("type"), file.get("size", "Unknown")))
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Unable to fetch files: {e}")

        # Función para obtener el historial de commits de un archivo
        def load_commit_history(event=None):
            commit_tree.delete(*commit_tree.get_children())
            selected_item = file_tree.selection()
            if not selected_item:
                return

            file_path = file_tree.item(selected_item, "values")[0]

            try:
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/commits"
                headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
                params = {"path": file_path}
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                commits = response.json()

                for commit in commits:
                    commit_tree.insert("", "end", values=(
                        commit.get("sha"),
                        commit.get("commit", {}).get("author", {}).get("name"),
                        commit.get("commit", {}).get("author", {}).get("date"),
                        commit.get("commit", {}).get("message"),
                    ))
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Unable to fetch commit history: {e}")

        # Función para obtener los cambios en un commit específico de un archivo
        def load_commit_changes(event=None):
            selected_commit = commit_tree.selection()
            selected_file = file_tree.selection()

            if not selected_commit or not selected_file:
                return

            commit_sha = commit_tree.item(selected_commit, "values")[0]
            file_path = file_tree.item(selected_file, "values")[0]

            diff_viewer.delete("1.0", "end")

            try:
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/commits/{commit_sha}"
                headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                commit_data = response.json()

                files = commit_data.get("files", [])
                for file in files:
                    if file.get("filename") == file_path:
                        patch = file.get("patch", "No changes found.")
                        lexer = pygments.lexers.get_lexer_for_filename(file_path)
                        diff_viewer.config(lexer=lexer)
                        diff_viewer.insert("1.0", patch)

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Unable to fetch commit changes: {e}")

        # Bind para seleccionar un archivo y ver su historial de commits
        file_tree.bind("<Double-Button-1>", load_commit_history)

        # Bind para seleccionar un commit y ver los cambios en el archivo
        commit_tree.bind("<Double-Button-1>", load_commit_changes)

        load_files()
        
    def search_code_on_github():
        def search_code():
            query = search_code_var.get().strip()
            if not query:
                ms.showerror("Error", "Please enter something to search for code on GitHub.")
                return

            url = f"https://api.github.com/search/code?q={query}"

            try:
                response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                    "Accept": "application/vnd.github.v3+json"})
                response.raise_for_status()
                results = response.json()["items"]

                for widget in results_frame.winfo_children():
                    widget.destroy()

                for item in results:
                    display_file_result(item)

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Could not search for code on GitHub: {e}")

        def display_file_result(item):
            file_name, repo_full_name, file_path, file_url = item["name"], item["repository"]["full_name"], item["path"], item["html_url"]
            repo_owner, repo_name = repo_full_name.split("/")

            path_label = ttk.Label(results_frame, text=f"{file_path} - {repo_full_name}", font=("Arial", 10, "bold"), anchor="w", foreground="blue")
            path_label.pack(fill="x", padx=10, pady=5)
            path_label.bind("<Enter>", lambda e: path_label.config(cursor="hand2"))
            path_label.bind("<Leave>", lambda e: path_label.config(cursor=""))
            path_label.bind("<Button-1>", lambda e: open_link(file_url))

            file_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"

            try:
                response = requests.get(file_api_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
                response.raise_for_status()
                file_data = response.json()
                file_content = base64.b64decode(file_data["content"]).decode("utf-8")

                try:
                    lexer = get_lexer_for_filename(file_name)
                except ClassNotFound:
                    lexer = get_lexer_for_filename("text")

                code_view_frame = ttk.Frame(results_frame)
                code_view_frame.pack(fill="both", padx=10, pady=5)

                code_view = CodeView(code_view_frame, wrap="word", height=20, lexer=lexer)
                code_view.pack(expand=True, fill="both")
                code_view.insert("end", file_content)
                code_view.config(state=tk.DISABLED)

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Could not get the code file: {e}")
            
        def open_link(url):
            webbrowser.open(url)

        canvas = tk.Canvas(search_code_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(search_code_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        search_code_var = tk.StringVar()
        search_box = ttk.Entry(scrollable_frame, textvariable=search_code_var, width=60)
        search_box.pack(pady=5, padx=10)
        search_button = ttk.Button(scrollable_frame, text="Search Code on GitHub", command=search_code)
        search_button.pack(pady=5)

        results_frame = ttk.Frame(scrollable_frame)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
    search_repositories()
    search_code_on_github()
    check_github_status()

def show_docu():
    docu = tk.Toplevel(root)
    docu.title("Documentation Viewer")
    docu.iconphoto(True, tk.PhotoImage(file=path))
    
    def load_documentation():
        language = lang_var.get().strip().lower()
        topic = m_var.get().strip()
        
        if not language:
            ms.showerror("ERROR", "Please select a language.")
            return
        
        # Mapeo de lenguajes a sus URLs de documentación
        doc_urls = {
            "python": "https://docs.python.org/3/",
            "javascript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
            "java": "https://docs.oracle.com/javase/8/docs/",
            "c++": "https://cplusplus.com/reference/",
            "html": "https://developer.mozilla.org/en-US/docs/Web/HTML",
            "css": "https://developer.mozilla.org/en-US/docs/Web/CSS",
            "ruby": "https://ruby-doc.org/",
            "go": "https://pkg.go.dev/",
            "rust": "https://doc.rust-lang.org/",
            "php": "https://www.php.net/docs.php",
            "kotlin": "https://kotlinlang.org/docs/",
            "swift": "https://developer.apple.com/documentation/",
            "mysql": "https://dev.mysql.com/doc/",
            "postgresql": "https://www.postgresql.org/docs/",
            "r": "https://cran.r-project.org/manuals.html",
            "bash": "https://tldp.org/LDP/abs/html/",
            "typescript": "https://www.typescriptlang.org/docs/",
            "dart": "https://dart.dev/guides",
            "perl": "https://perldoc.perl.org/",
            "c#": "https://learn.microsoft.com/en-us/dotnet/csharp/",
            "lua": "https://www.lua.org/manual/5.4/",
            "matlab": "https://www.mathworks.com/help/matlab/",
            "scala": "https://docs.scala-lang.org/",
            "haskell": "https://www.haskell.org/documentation/",
            "elixir": "https://elixir-lang.org/docs.html",
            "assembly": "https://cs.lmu.edu/~ray/notes/nasmtutorial/"
        }
        
        base_url = doc_urls.get(language)
        if not base_url:
            ms.showerror("ERROR", f"Documentation for language '{language}' is not supported.")
            return
        
        url = f"{base_url}{topic}.html" if topic else base_url
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                webview.create_window(f"{language.capitalize()} Documentation", url)
                webview.start()
            else:
                ms.showerror("ERROR", f"Documentation for '{topic}' in {language.capitalize()} not found.")
        except requests.exceptions.RequestException as e:
            ms.showerror("ERROR", f"Error loading documentation: {e}")
    
    # Etiqueta para seleccionar el lenguaje
    lang_label = ttk.Label(docu, text="Select Language:")
    lang_label.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
    
    # Combobox para seleccionar el lenguaje
    lang_var = tk.StringVar()
    lang_combobox = ttk.Combobox(docu, textvariable=lang_var, state="readonly")
    lang_combobox["values"] = [
        "Python", "JavaScript", "Java", "C++", "HTML", "CSS", 
        "Ruby", "Go", "Rust", "PHP", "Kotlin", "Swift", 
        "MySQL", "PostgreSQL", "R", "Bash", "TypeScript", 
        "Dart", "Perl", "C#", "Lua", "MATLAB", "Scala", 
        "Haskell", "Elixir", "Assembly"
    ]
    lang_combobox.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
    lang_combobox.current(0)  # Selecciona Python por defecto

    # Etiqueta para ingresar el tema
    t_label = ttk.Label(docu, text="Enter topic (e.g., json, Array, div):")
    t_label.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
    
    # Campo de entrada para el tema
    m_var = tk.StringVar()
    m_entry = ttk.Entry(docu, width=50, textvariable=m_var)
    m_entry.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
    
    # Botón para cargar la documentación
    load_button = ttk.Button(docu, text="Load Documentation", command=load_documentation)
    load_button.grid(row=2, columnspan=2, padx=2, pady=2, sticky="ew")

def register_linux_integration():
    exe_path = os.path.abspath(sys.argv[0])
    icon_path = os.path.join(os.path.dirname(exe_path), 'software.png')

    desktop_entry_path = os.path.expanduser("~/.local/share/applications/organizer.desktop")
    mime_dir = os.path.expanduser("~/.local/share/mime/packages/")
    mime_xml_path = os.path.join(mime_dir, "organizer.xml")

    os.makedirs(mime_dir, exist_ok=True)

    desktop_entry_content = f"""[Desktop Entry]
    Name=Organizer
    Comment=Open proyect files .orga with organizer
    Exec="{exe_path}" %f
    Icon="{icon_path}"
    Terminal=false
    Type=Application
    MimeType=application/x-organizer;
    Categories=Development;Utility;
    """

    with open(desktop_entry_path, "w") as desktop_file:
        desktop_file.write(desktop_entry_content)

    
    mime_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
        <mime-type type="application/x-organizer">
            <comment>File of organizer project</comment>
            <glob pattern="*.orga"/>
        </mime-type>
    </mime-info>
    """

    with open(mime_xml_path, "w") as mime_file:
        mime_file.write(mime_xml_content)

    subprocess.run(["xdg-mime", "install", "--mode", "user", mime_xml_path], check=True)
    subprocess.run(["update-mime-database", os.path.expanduser("~/.local/share/mime")], check=True)
    subprocess.run(["xdg-mime", "default", "organizer.desktop", "application/x-organizer"], check=True)

    ms.showinfo("INTEGRATION COMPLETE", "✅ Integration wiht linux complete. Now .orga files will be opened with Organizer")

def open_project_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            project_data = json.load(file)

        project_id = project_data.get("id_project")
        project_path = project_data.get("project_path")
        editor = project_data.get("editor")

        if not project_id or not project_path or not editor:
            ms.showerror("ERROR", "The file is invalid or incomplete")
            return
        
        configuracion_editores = cargar_configuracion_editores()
        ruta_editor = configuracion_editores.get(editor) if configuracion_editores and editor in configuracion_editores else None

        if not ruta_editor:
            editores_disponibles = detectar_editores_disponibles()
            ruta_editor = editores_disponibles.get(editor)

        if ruta_editor:
            subprocess.Popen([ruta_editor, project_path])
            subprocess.run(f"gnome-terminal -- bash -c 'cd {project_path} && exec bash'", shell=True)
            sys.exit(0)
        elif editor == "Editor Integrated":
            subprocess.Popen(f'gnome-terminal -- bash -c "cd {project_path} && exec bash"', shell=True)
            abrir_editor_thread(project_path, tree.item(tree.selection())['values'][1])
            

    except Exception as e:
        ms.showerror("ERROR", f"Error opening project file: {e}")

path = resource_path(img)
path2 = resource_path2("./software.png")
root = ThemedTk()
root.title('Proyect Organizer')
root.geometry("1550x500")
root.iconphoto(True, tk.PhotoImage(file=path))
temas = root.get_themes()
ttkbootstrap_themes = ttk_themes()

main_frame = ttk.Frame(root, bootstyle="default")
main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=3)

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

# Establecer temas y editor
editores_disponibles = ["Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
                        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
                        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
                        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
                        "Android Studio", "neovim"]

lenguajes = ["Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go", "flutter"]

# Menú
menu = tk.Menu(root)
root.config(menu=menu)
menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Proyectos", menu=menu_archivo)
menu_archivo.add_command(label='Agree Project', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Create New', command=crear_nuevo_proyecto)
menu_archivo.add_command(label="My Github Profile", command=unify_windows)
menu_archivo.add_command(label="New Project Github", command=abrir_proyecto_github)
menu_archivo.add_command(label="Push Update Github", command=lambda: push_actualizaciones_github(tree.item(tree.selection())['values'][5]))
menu_archivo.add_command(label='Delete Project', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4]))
menu_archivo.add_command(label="Generate Report", command=generar_informe)
menu_settings = tk.Menu(menu, tearoff=0)
menu.add_command(label="Settings", command=setting_window)   
help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="InfoVersion", command=ver_info)
help_menu.add_command(label="Documentation", command=show_docu)

# Labels y campos de entrada
ttk.Label(main_frame, text="Name:", bootstyle='info').grid(row=0, column=0, padx=5, pady=5, sticky="w")
nombre_entry = ttk.Entry(main_frame, width=170)
nombre_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(main_frame, text="Description:", bootstyle='info').grid(row=1, column=0, padx=5, pady=5, sticky="w")
descripcion_entry = ttk.Entry(main_frame, width=170)
descripcion_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(main_frame, text="Repository URL:", bootstyle='info').grid(row=2, column=0, padx=5, pady=5, sticky="w")
repo_entry = ttk.Entry(main_frame, width=170)
repo_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")


# Árbol de proyectos
tree = ttk.Treeview(main_frame, columns=('ID', 'Name', 'Description', 'Language', 'Path', 'Repository'), show='headings', bootstyle='primary')
for col in ('ID', 'Name', 'Description', 'Language', 'Path', 'Repository'):
    tree.heading(col, text=col)
    tree.column(col, width=150)
tree.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

scrollbar_y = ttk.Scrollbar(main_frame, orient='vertical', command=tree.yview, bootstyle='round-primary')
scrollbar_y.grid(row=4, columnspan=2, padx=5, pady=5, sticky='nse')
tree.configure(yscrollcommand=scrollbar_y.set)
tree.bind("<Button-3>", show_context_menu)

# Campo de búsqueda
ttk.Label(main_frame, text="Search Project:", bootstyle='info').grid(row=5, column=0, padx=5, pady=5, sticky="w")
search_entry = ttk.Entry(main_frame, width=170)
search_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
search_entry.bind("<KeyRelease>", on_key_release)

# Selector de editor
selected_editor = tk.StringVar()
editor_options = [
    "Select a Editor", "Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
    "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
    "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
    "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
    "Android Studio", "Integrated Editor", "neovim"
]
selected_editor.set(editor_options[0])

ttk.Label(main_frame, text="Editor:", bootstyle='info').grid(row=6, column=0, padx=5, pady=5, sticky="w")
editor_menu = ttk.Combobox(main_frame, textvariable=selected_editor, values=editor_options, state="readonly", bootstyle='secondary')
editor_menu.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

# Botones de acción
btn_abrir = ttk.Button(main_frame, text='Open Project', command=lambda: abrir_threading(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4], selected_editor.get()), bootstyle='success')
btn_abrir.grid(row=7, column=0, columnspan=2, pady=10, padx=5, sticky="s")

version_label = ttk.Label(main_frame, text=f'{version}', bootstyle='info')
version_label.grid(row=7, column=1, pady=5, padx=5, sticky="se")

# Configuración de peso y distribución
main_frame.grid_rowconfigure(4, weight=1)

if not os.path.exists(os.path.expanduser("~/.local/share/applications/organizer.desktop")):
    register_linux_integration()

if len(sys.argv) > 1:
    ruta_proyecto = " ".join(sys.argv[1:])
    threading.Thread(target=open_project_file, args=(ruta_proyecto,), daemon=True).start()
    
crear_base_datos()
mostrar_proyectos()
set_default_theme()
check_new_version()
thread_sinc()
initialize_backup_schedule()
root.mainloop()
