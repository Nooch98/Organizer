import json
import os
from pydoc import text
import shutil
import sqlite3
import subprocess
import sys
import threading
from urllib import response
import git
import time
import webbrowser
import tkinter as tk
import jedi
import markdown
import datetime
import requests
import pygments.lexers
import platform
import subprocess
import ttkbootstrap as ttk
import markdown2
import glob
import re
import xml.etree.ElementTree as ET
import webview
import base64
import hashlib
#--------------------------------------------------------#
from tkinter import OptionMenu, StringVar, filedialog, simpledialog
from tkinter.simpledialog import askstring 
from urllib.parse import urlparse
from tkinter import messagebox as ms
from tkinter import scrolledtext
from bs4 import BeautifulSoup
from github import Auth, Github
from openai import OpenAI
from tkhtmlview import HTMLLabel
from ttkthemes import ThemedTk
from chlorophyll import CodeView
from pathlib import Path
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Progressbar
from git import Repo
from tkinter.colorchooser import askcolor
from datetime import datetime
from pygments.lexers.markup import MarkdownLexer
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound


main_version = "ver.1.9.7"
version = str(main_version)
base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
db_path = os.path.join(base_path, "proyectos.db")
archivo_configuracion_editores = os.path.join(base_path, "configuracion_editores.json")
archivo_configuracion_gpt = os.path.join(base_path, "configuration_gpt.json")
BACKUP_STATE_FILE = os.path.join(base_path, "backup_schedule.json")
archivo_configuracion_editores = os.path.join(base_path, "configuracion_editores.json")
config_file = os.path.join(base_path, "config.json")
selected_project_path = None
text_editor = None
app_name = "Organizer_win.exe"
exe_path = os.path.abspath(sys.argv[0])
current_version = "v1.9.7"

# Integration with local control version app
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
                ms.showerror("ERROR", "No github api key found in your environment variables. Please agree github api key to your environment variables with the name: GITHUB, TOKEN, API, KEY or SECRET")
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
                    quest = ms.askyesno("Update", f"Version {latest_version} of Organizer Available.\n You want install?")
                    if quest:
                        assets = release_data.get("assets", [])
                        if not assets:
                            return "Can't found any file to download"
                        
                        selected_asset = None
                        for asset in assets:
                            if asset["name"] == "Organizer_setup.exe":
                                selected_asset = asset
                                break
                        if not selected_asset:
                            return "Can't found the file Organizer_setup.exe"
                        asset_url = selected_asset["browser_download_url"]
                        current_directory = os.getcwd()
                        file_path = os.path.join(current_directory, selected_asset["name"])
                        download_response = requests.get(asset_url)
                        with open(file_path, "wb") as file:
                            file.write(download_response.content)
                        ms.showinfo("Update", "Closing Organizer to update")
                        subprocess.Popen("updater_win.exe")
                        orga.after(1000, orga.destroy())
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

# Función para obtener la ruta base de la carpeta de proyectos de la app
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS proyectos (id INTEGER PRIMARY KEY, nombre TEXT, descripcion TEXT, lenguaje TEXT, ruta TEXT, repo TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS estado_proyectos (id_proyecto INTEGER PRIMARY KEY, abierto_editor INTEGER DEFAULT 0, ultima_sincronizacion TEXT)")
    conn.close()

def insertar_proyecto(nombre, descripcion, ruta, repo, lenguaje=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO proyectos (nombre, descripcion, lenguaje, ruta, repo) VALUES (?, ?, ?, ?, ?)", (nombre, descripcion, lenguaje, ruta, repo))
    conn.commit()
    conn.close()
   
def get_projects_from_database():

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos")
    projects = cursor.fetchall()

    conn.close()

    projects_list = []
    for project in projects:
        project_dict = {'nombre': project[1], 'ruta': project[4]}
        projects_list.append(project_dict)

    return projects_list

def abrir_editor(ruta, ruta_editor):
    subprocess.Popen(f'"{ruta_editor}" "{ruta}"')

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
    editores = {
        "Visual Studio Code": "code.exe",
        "Sublime Text": "sublime_text.exe",
        "Atom": "atom.exe",
        "Vim": "vim.exe",
        "Emacs": "emacs.exe",
        "Notepad++": "notepad++.exe",
        "Brackets": "brackets.exe",
        "TextMate": "mate.exe",
        "Geany": "geany.exe",
        "gedit": "gedit.exe",
        "Nano": "nano.exe",
        "Kate": "kate.exe",
        "Bluefish": "bluefish.exe",
        "Eclipse": "eclipse.exe",
        "IntelliJ IDEA": "idea.exe",
        "PyCharm": "pycharm.exe",
        "Visual Studio": "devenv.exe",
        "Blend Visual Studio": "Blend.exe",
        "Code::Blocks": "codeblocks.exe",
        "NetBeans": "netbeans.exe",
        "Android Studio": "studio64.exe",
        "neovim": "nvim.exe"
    }
    return {nombre: shutil.which(binario) for nombre, binario in editores.items() if shutil.which(binario)}

def cargar_configuracion_editores():
    try:
        with open(archivo_configuracion_editores, "r") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)
            return configuracion
    except FileNotFoundError:
        ms.showwarning("WARNING", f"Config file not found")
        return None

def guardar_configuracion_editores(rutas_editores):
    configuracion = {}
    for editor, entry in rutas_editores.items():
        ruta = entry.get()
        if ruta:
            configuracion[editor] = ruta
    with open(archivo_configuracion_editores, "w") as archivo_configuracion:
        json.dump(configuracion, archivo_configuracion)

def abrir_proyecto(id_proyecto, ruta, editor):
    configuracion_editores = cargar_configuracion_editores()
    ruta_editor = configuracion_editores.get(editor) if configuracion_editores and editor in configuracion_editores else None

    if not ruta_editor:
        editores_disponibles = detectar_editores_disponibles()
        ruta_editor = editores_disponibles.get(editor)

    # Obtener la ruta de la copia en la carpeta _internal/projects de la app
    nombre_proyecto = os.path.basename(ruta)
    ruta_copia = obtener_ruta_copia_proyecto(nombre_proyecto)

    # Sincronización inicial usando la última sincronización registrada
    ultima_sincronizacion = obtener_ultima_sincronizacion(id_proyecto)
    sincronizar_diferencial(ruta, ruta_copia, ultima_sincronizacion)

    # Marcar proyecto como abierto en editor
    actualizar_estado_proyecto(id_proyecto, True)

    def execute_project_on_subprocess():
        try:
            process = []
            # Ejecutar el editor seleccionado
            if ruta_editor:
                editor_process = subprocess.Popen(
                    [ruta_editor, ruta], 
                    shell=True, 
                    start_new_session=True
                )
                process.append(editor_process)
                terminal_process = subprocess.Popen(
                    f'Start wt -d "{ruta}"', 
                    shell=True, 
                    start_new_session=True
                )
                process.append(terminal_process)
            elif editor == "neovim":
                comando_ps = f"Start-Process nvim '{ruta}' -WorkingDirectory '{ruta}'"
                editor_process = subprocess.Popen(
                    ["powershell", "-Command", comando_ps], 
                    start_new_session=True
                )
                process.append(editor_process)
            elif editor == "Integrated Editor":
                terminal_process = subprocess.Popen(
                    f'Start wt -d "{ruta}"', 
                    shell=True, 
                    start_new_session=True
                )
                process.append(terminal_process)
                abrir_editor_thread(ruta, tree.item(tree.selection())['values'][1])
            else:
                ms.showerror("ERROR", f"{editor} Not found")

            # Sincronización de los procesos en segundo plano
            threading.Thread(target=monitor_processes_and_sync, args=(process, id_proyecto, ruta, ruta_copia), daemon=True).start()

        except Exception as e:
            ms.showerror("ERROR", f"An error occurred while opening the project: {str(e)}")

    # Ejecutar el proceso de apertura en segundo plano
    threading.Thread(target=execute_project_on_subprocess, daemon=True).start()
    
def monitor_processes_and_sync(processes, id_proyecto, ruta, ruta_copia):
    # Esperar a que todos los procesos finalicen
    for process in processes:
        process.wait()

    ultima_sincronizacion = obtener_ultima_sincronizacion(id_proyecto)
    sincronizar_diferencial(ruta, ruta_copia, ultima_sincronizacion)

    # Actualizar el estado del proyecto a cerrado
    actualizar_estado_proyecto(id_proyecto, False)

def abrir_threading(id_proyecto, ruta, editor):
    threading.Thread(target=abrir_proyecto, args=(id_proyecto, ruta, editor)).start()

def abrir_editor_thread(ruta, name):
    threading.Thread(target=abrir_editor_integrado, args=(ruta, name)).start()

def abrir_editor_integrado(ruta_proyecto, nombre_proyecto):
    global current_file

    editor = ThemedTk(theme='')
    editor.title("Editor Integrated")
    editor.geometry("800x400")
    editor.iconbitmap(path)
    
    current_file = None
    tabs = ttk.Notebook(editor)
    tabs.pack(expand=True, fill="both", side="right")
    text_editors = []
    global_plugins = []
    code_themes_dir = Path(".\\_internal\\chlorophyll\\colorschemes\\")
    tom_files = [archivo.stem for archivo in code_themes_dir.glob("*.toml")]
    temas = editor.get_themes()
    
    selected_theme = ""
    
    def current_theme_get():
        return selected_theme
    
    def read_requirements(file_path):
        dependencies = []
        with open(file_path, 'r') as f:
            for line in f:
                # Ignorar líneas vacías o comentarios
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extraer solo el nombre del paquete, sin versiones o extras
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
            
    def load_dependencies(file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo de dependencias",
                filetypes=[("Text files", "*.txt;*.toml;*.csproj;*.json")]
            )
        
        if file_path:
            denpendencies_entry.delete(0, tk.END)
            denpendencies_entry.insert(0, file_path)
                
            if file_path.endswith(".toml"):
                libraries = read_rust_dependencies(file_path)
                show_requirements(libraries)
            elif file_path.endswith(".csproj"):
                libraries = read_csharp_dependencies(file_path)
                show_requirements(libraries)
            elif file_path.endswith("CMakeLists.txt"):
                libraries = read_cmake_dependencies(file_path)
                show_requirements(libraries)
            elif file_path.endswith(".json"):
                libraries = read_vcpkg_dependencies(file_path)
                show_requirements(libraries)
            elif file_path.endswith(".txt"):
                libraries = read_requirements(file_path)
                show_requirements(libraries)
            else:
                libraries = []
            
    
    def show_requirements(libraries):
        # Limpiar los widgets anteriores
        for widget in lib_frame.winfo_children():
            widget.destroy()

        # Número de columnas en la cuadrícula
        num_columns = 4
        row = 0
        col = 0

        # Titulo de la sección
        title_label = ttk.Label(lib_frame, text="Select Required Libraries", bootstyle=SUCCESS, font=("Helvetica", 16))
        title_label.grid(row=row, columnspan=num_columns, pady=10, padx=10)

        for lib in libraries:
            var = tk.BooleanVar(value=False)
            libraries_vars[lib] = var
            
            # Crear Checkbutton para cada librería
            checkbox = ttk.Checkbutton(
                lib_frame,
                text=lib,
                variable=var,
                bootstyle="secondary",
                command=lambda lib=lib: update_command_label(file_entry.get())  # Actualizar comando
            )
            
            checkbox.grid(row=row + 1, column=col, sticky="ew", padx=5, pady=5)

            # Ajustar la posición de los Checkbuttons en la cuadrícula
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

        # Ajustar las columnas para que se expandan y se alineen bien
        for col in range(num_columns):
            lib_frame.grid_columnconfigure(col, weight=1)

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
            ms.showerror("ERROR", "File type not supported for compilation.")
            return

        def run_conversion():
            convert_btn.config(state=tk.DISABLED)
            output_box.insert(tk.END, f"\nExecuting {command}\n")
            progressbar.grid(row=7, columnspan=2, padx=2, pady=2, sticky="ew")
            progressbar.start()
            process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True, shell=True)
            
            def read_output():
                global output_dir
                for line in iter(process.stderr.readline, ""):
                    output_box.insert(tk.END, line)
                    output_box.see(tk.END)
                    output_box.update_idletasks()
                
                process.wait()
                output_box.insert(tk.END, "\nCompilación Complete.\n")
                progressbar.stop()
                progressbar.grid_forget()

                base_filename = os.path.splitext(os.path.basename(file_path))[0]
                output_dir = output_entry.get() if output_entry.get() else os.getcwd()
                exe_path = os.path.join(output_dir, base_filename + ".exe")

                open_explorer_button.grid(row=8, column=2, padx=2, pady=2, sticky="ew")
                clear_output.grid(row=8, column=0, padx=2, pady=2, sticky="ew")
                convert_btn.config(state=tk.NORMAL)
            
            output_thread = threading.Thread(target=read_output)
            output_thread.start()

        conversion_thread = threading.Thread(target=run_conversion)
        conversion_thread.start()
        
    def open_explorer():
        if output_dir:
            os.startfile(output_dir)
        else:
            ms.showwarning("Warning", "The .exe file was not found.")

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
        open_explorer_button.grid_forget()
        clear_output.grid_forget()
        
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
            
            denpendencies_entry.delete(0, tk.END)
            denpendencies_entry.insert(0, config.get("dependencies_path"))
            
            dep_path = denpendencies_entry.get()
            if dep_path:
                load_dependencies(dep_path)
            
            selected_libraries = config.get("libraries", [])
            for lib, var in libraries_vars.items():
                var.set(lib in selected_libraries)
                
            additional_files.clear()
            additional_files.extend(config.get("additional_files", []))

            update_command_label(file_entry.get())
            
    def export_configuration():
        config = {
            "file_path": file_entry.get(),
            "output_dir": output_entry.get(),
            "icon_path": icon_entry.get(),
            "dependencies_path": denpendencies_entry.get(),
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
        global file_entry, lib_frame, libraries_vars, icon_entry, onefile_var, noconsole_var, output_box, output_entry, command_label, open_explorer_button, clear_output, additional_files, progressbar, convert_btn, denpendencies_entry

        # Crear ventana de conversión
        converter = ttk.Toplevel(editor)
        converter.title("Compiler")
        converter.iconbitmap(path)

        # Menú de opciones
        op_menu = tk.Menu(converter)
        converter.config(menu=op_menu)

        file_menu = tk.Menu(op_menu, tearoff=0)
        op_menu.add_cascade(label="Files", menu=file_menu)
        file_menu.add_command(label="Import Config", command=import_configuration)
        file_menu.add_command(label="Export Config", command=export_configuration)
        file_menu.add_command(label="Load Requiriments", command=load_dependencies)

        # Crear frames de contenido
        frame = ttk.Frame(converter)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        lib_frame = ttk.Frame(converter)
        lib_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Variables globales
        libraries_vars = {}
        additional_files = []

        # Etiquetas y campos de entrada con estilo mejorado
        file_label = ttk.Label(frame, text="Main File:", bootstyle="primary", font=("Helvetica", 10))
        file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        file_entry = ttk.Entry(frame, width=40, bootstyle="light")
        file_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        file_btn = ttk.Button(frame, text="Select", bootstyle="secondary", command=select_file)
        file_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        output_label = ttk.Label(frame, text="Output Dir:", bootstyle="primary", font=("Helvetica", 10))
        output_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        output_entry = ttk.Entry(frame, width=40, bootstyle="light")
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        output_btn = ttk.Button(frame, text="Select", bootstyle="secondary", command=select_output_directory)
        output_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        icon_label = ttk.Label(frame, text="Select Icon:", bootstyle="primary", font=("Helvetica", 10))
        icon_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        icon_entry = ttk.Entry(frame, width=40, bootstyle="light")
        icon_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        icon_btn = ttk.Button(frame, text="Select Icon", bootstyle="secondary", command=select_icon)
        icon_btn.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        # Agregar archivos adicionales
        add_files_label = ttk.Label(frame, text="Additional Files", bootstyle="primary", font=("Helvetica", 10))
        add_files_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        add_files_btn = ttk.Button(frame, text="Add Files", bootstyle="secondary", command=add_additional_files)
        add_files_btn.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        add_folder_btn = ttk.Button(frame, text="Add Folder", bootstyle="secondary", command=add_additional_folder)
        add_folder_btn.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        # Command label
        command_label = ttk.Label(frame, text="Command: ", bootstyle="info", font=("Helvetica", 10))
        command_label.grid(row=4, columnspan=3, padx=5, pady=5, sticky="w")

        # Checkbuttons para opciones de compilación
        onefile_var = tk.BooleanVar()
        onefile_check = ttk.Checkbutton(frame, text="Onefile", variable=onefile_var, bootstyle="info",
                                        command=lambda: update_command_label(file_entry.get()))
        onefile_check.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

        noconsole_var = tk.BooleanVar()
        noconsole_check = ttk.Checkbutton(frame, text="Noconsole", variable=noconsole_var, bootstyle="info",
                                        command=lambda: update_command_label(file_entry.get()))
        noconsole_check.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Caja de texto para salida
        output_box = tk.Text(frame, height=15, width=80, wrap='word')
        output_box.grid(row=6, columnspan=3, padx=5, pady=5, sticky="ew")

        # Botones de acción
        clear_output = ttk.Button(frame, text="Clear Output", bootstyle="danger", command=clear_all)
        clear_output.grid(row=7, column=0, padx=5, pady=5, sticky="ew")

        convert_btn = ttk.Button(frame, text="Compile", bootstyle="success", command=execute_conversion)
        convert_btn.grid(row=8, column=1, padx=5, pady=5, sticky="ew")

        open_explorer_button = ttk.Button(frame, text="Open Folder", bootstyle="info", command=open_explorer)
        open_explorer_button.grid(row=8, column=2, padx=5, pady=5, sticky="ew")

        # Barra de progreso
        progressbar = ttk.Progressbar(frame, orient="horizontal", mode='indeterminate', length=500, bootstyle="primary")
        progressbar.grid(row=9, columnspan=3, padx=5, pady=10, sticky="ew")

        # Campo para dependencias (oculto inicialmente)
        denpendencies_entry = ttk.Entry(frame, width=40, bootstyle="light")
        denpendencies_entry.grid_forget()

    def change_code_theme(theme_name):
        global selected_theme
        selected_theme = theme_name
        for text_editor in text_editors:
            text_editor.config(color_scheme=theme_name)
            gpt_response.config(color_scheme=theme_name)
            
            
    def create_code_theme():
        # Crear la ventana principal de la interfaz
        new_theme = tk.Toplevel()
        new_theme.title("Crear Nuevo Tema de Código")
        new_theme.geometry("900x600")  # Ajustamos el tamaño de la ventana
        new_theme.iconbitmap(path)  # Establecemos el icono de la ventana

        # Variables para almacenar los colores seleccionados (definir colores predeterminados)
        selected_colors = {
            'editor': {'bg': '#232136', 'fg': '#e0def4', 'select_bg': '#393552', 'select_fg': '#e0def4', 'inactive_select_bg': '#393552', 'caret': '#e0def4'},
            'general': {'comment': '#6e6a86', 'error': '#eb6f92', 'escape': '#908caa', 'keyword': '#eb6f92', 'name': '#f6c177', 'string': '#ea9a97', 'punctuation': '#eb6f92'},
            'keyword': {'constant': '#c4a7e7', 'declaration': '#eb6f92', 'namespace': '#eb6f92', 'pseudo': '#c4a7e7', 'reserved': '#eb6f92', 'type': '#eb6f92'},
            'name': {'attr': '#f6c177', 'builtin': '#9ccfd8', 'builtin_pseudo': '#f6c177', 'class': '#f6c177', 'class_variable': '#f6c177', 'constant': '#e0def4', 'decorator': '#9ccfd8', 'entity': '#f6c177', 'exception': '#9ccfd8', 'function': '#f6c177', 'global_variable': '#f6c177', 'instance_variable': '#f6c177', 'label': '#f6c177', 'magic_function': '#9ccfd8', 'magic_variable': '#f6c177', 'namespace': '#e0def4', 'tag': '#eb6f92', 'variable': '#eb6f92'},
            'operator': {'symbol': '#f83535', 'word': '#eb6f92'},
            'string': {'affix': '#ea9a97', 'char': '#ea9a97', 'delimeter': '#ea9a97', 'doc': '#ea9a97', 'double': '#ea9a97', 'escape': '#ea9a97', 'heredoc': '#ea9a97', 'interpol': '#ea9a97', 'regex': '#ea9a97', 'single': '#ea9a97', 'symbol': '#ea9a97'},
            'number': {'binary': '#c4a7e7', 'float': '#c4a7e7', 'hex': '#c4a7e7', 'integer': '#c4a7e7', 'long': '#c4a7e7', 'octal': '#c4a7e7'},
            'comment': {'hashbang': '#6e6a86', 'multiline': '#6e6a86', 'preproc': '#eb6f92', 'preprocfile': '#ea9a97', 'single': '#6e6a86', 'special': '#6e6a86'}
        }

        # Crear un diccionario para almacenar las etiquetas de los colores
        color_labels = {category: {} for category in selected_colors.keys()}

        # Función para elegir un color a través de un selector
        def choose_color(category, color_name):
            color = askcolor(initialcolor=selected_colors[category][color_name])[1]
            if color:
                selected_colors[category][color_name] = color
                color_labels[category][color_name].config(bg=color)  # Actualizar el color del label
                update_preview()  # Actualizar la previsualización
        
        def is_valid_color(color):
            return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))

        # Función para actualizar el color desde el campo Entry
        def update_color_from_entry(category, color_name, color_entry):
            color = color_entry.get()
            if is_valid_color(color):
                selected_colors[category][color_name] = color
                color_labels[category][color_name].config(bg=color)  # Actualizar el color del label
                update_preview()  # Actualizar la previsualización
            else:
               pass
        
        # Crear un fragmento de código para la previsualización
        code_sample = """
            # Este es un comentario simple
            # Otro comentario más largo que abarca varias líneas
            # Este comentario tiene una # escapatoria de caracteres

            def ejemplo_funcion(variable1, variable2):
                # Comentario dentro de una función
                if variable1 > 0:
                    # Comprobamos si el valor es mayor que cero
                    print('El valor es positivo: ', variable1)
                else:
                    print("El valor es negativo o cero")
                return variable1 + variable2  # Retorno de la suma

            # Este es un bloque de código de prueba con múltiples tipos de datos
            variable1 = 123  # Número entero
            variable2 = 3.14  # Número de punto flotante
            cadena = 'Hola Mundo'  # Cadena de texto
            booleano = True  # Booleano

            # Operaciones matemáticas con números y strings
            resultado = variable1 + variable2
            texto_completo = cadena + " y el número es: " + str(variable1)

            # Clases y funciones de Python
            class MiClase:
                def __init__(self):
                    self.variable_de_instancia = 5  # Atributo de clase
                def metodo(self):
                    return self.variable_de_instancia

            # Invocando una función y creando una instancia de clase
            instancia = MiClase()
            print(instancia.metodo())  # Llamada a un método de clase

            # Uso de palabras clave y declaraciones
            for i in range(5):
                print(i)
            """
        
        # Crear un área de texto para la previsualización del código
        preview_text = tk.Text(new_theme, height=50, width=70, wrap=tk.WORD, bg=selected_colors['editor']['bg'], fg=selected_colors['editor']['fg'], font=("Courier New", 12))
        preview_text.insert(tk.END, code_sample)
        preview_text.config(state=tk.DISABLED)  # Deshabilitar la edición
        preview_text.grid(row=0, column=3, rowspan=10, padx=10, pady=10)

        # Función para actualizar la previsualización en tiempo real
        def update_preview():
            preview_text.config(bg=selected_colors['editor']['bg'], fg=selected_colors['editor']['fg'])
            preview_text.tag_configure("keyword", foreground=selected_colors['general']['keyword'])
            preview_text.tag_configure("comment", foreground=selected_colors['general']['comment'])
            preview_text.tag_configure("string", foreground=selected_colors['general']['string'])
            preview_text.tag_configure("number", foreground=selected_colors['general']['error'])

            preview_text.delete(1.0, tk.END)
            preview_text.insert(tk.END, code_sample)

            # Aplicar colores de la previsualización
            for tag, content in [("comment", "# Comentario de prueba"), ("keyword", "def ejemplo_funcion"), ("string", "'cadena de texto'"), ("number", "123")]:
                start_idx = '1.0'
                while start_idx:
                    start_idx = preview_text.search(content, start_idx, stopindex=tk.END)
                    if start_idx:
                        end_idx = f"{start_idx}+{len(content)}c"
                        preview_text.tag_add(tag, start_idx, end_idx)
                        start_idx = end_idx

        # Inicializar la previsualización con los colores por defecto
        update_preview()

        ttk.Label(new_theme, text="Nombre del Tema:").grid(row=11, column=0, padx=10, pady=5, sticky="w")
        theme_name_entry = ttk.Entry(new_theme)
        theme_name_entry.grid(row=11, column=1, padx=10, pady=5, sticky="ew")
        
        # Crear un Canvas para el desplazamiento
        canvas = ttk.Canvas(new_theme)
        canvas.grid(row=0, column=0, rowspan=11, padx=10, pady=10, sticky="nswe")

        # Crear una barra de desplazamiento vertical
        scrollbar = ttk.Scrollbar(new_theme, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, rowspan=11, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Crear un frame dentro del canvas para contener los controles
        controls_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=controls_frame, anchor="nw")

        # Etiquetas para cada categoría de colores en el archivo TOML
        row = 0
        for category, colors in selected_colors.items():
            tk.Label(controls_frame, text=f"Colores para {category.capitalize()}").grid(row=row, column=0, columnspan=3, padx=10, pady=5, sticky="w")
            row += 1
            for color_name, default_color in colors.items():
                tk.Label(controls_frame, text=f"{color_name.capitalize()}").grid(row=row, column=0, padx=10, pady=5, sticky="w")
                color_button = tk.Button(controls_frame, text="Elegir Color", command=lambda category=category, color_name=color_name: choose_color(category, color_name))
                color_button.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                color_labels[category][color_name] = tk.Label(controls_frame, bg=default_color, width=10, height=1)
                color_labels[category][color_name].grid(row=row, column=2, padx=10, pady=5, sticky="ew")
                # Campo Entry al lado del botón para personalizar el color (si es necesario)
                color_entry = tk.Entry(controls_frame)
                color_entry.grid(row=row, column=3, padx=10, pady=5, sticky="ew")
                # Asociar la actualización del color al evento de ingreso de texto
                color_entry.bind("<FocusOut>", lambda event, category=category, color_name=color_name, entry=color_entry: update_color_from_entry(category, color_name, entry))
                row += 1

        # Asegurarse de que el canvas se pueda redimensionar y los elementos dentro de él también
        controls_frame.update_idletasks()  # Para actualizar el tamaño del frame
        canvas.config(scrollregion=canvas.bbox("all"))

        # Función para guardar el tema creado
        def save_theme():
            theme_name = theme_name_entry.get()
            if not theme_name:
                ms.showerror("Error", "Por favor, ingresa un nombre para el tema.")
                return

            # Crear el contenido del archivo TOML con todos los colores seleccionados
            theme_content = f"[editor]\n"
            for name, color in selected_colors['editor'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [general]
            theme_content += "\n[general]\n"
            for name, color in selected_colors['general'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [keyword]
            theme_content += "\n[keyword]\n"
            for name, color in selected_colors['keyword'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [name]
            theme_content += "\n[name]\n"
            for name, color in selected_colors['name'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [operator]
            theme_content += "\n[operator]\n"
            for name, color in selected_colors['operator'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [string]
            theme_content += "\n[string]\n"
            for name, color in selected_colors['string'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [number]
            theme_content += "\n[number]\n"
            for name, color in selected_colors['number'].items():
                theme_content += f'{name} = "{color}"\n'

            # Sección [comment]
            theme_content += "\n[comment]\n"
            for name, color in selected_colors['comment'].items():
                theme_content += f'{name} = "{color}"\n'

            # Guardar el tema en un archivo .toml
            ruta_new_theme = ".\\_internal\\chlorophyll\\colorschemes\\"
            try:
                with open(f"{ruta_new_theme}{theme_name}.toml", "w", encoding="utf-8") as file:
                    file.write(theme_content)
                ms.showinfo("Tema Guardado", f"El tema '{theme_name}' se ha guardado correctamente.")
                new_theme.destroy()
            except Exception as e:
                ms.showerror("Error", f"No se pudo guardar el tema. Error: {e}")

        # Botón para guardar el tema
        save_button = tk.Button(new_theme, text="Guardar Tema", command=save_theme)
        save_button.grid(row=row, column=0, columnspan=3, pady=20)

        # Hacer que la ventana principal se redimensione adecuadamente
        new_theme.grid_rowconfigure(0, weight=1)
        new_theme.grid_columnconfigure(0, weight=1)
        new_theme.grid_columnconfigure(3, weight=1)
    
    def show_plugin_selector(plugins_list):
        plugin_selector = tk.Toplevel()
        plugin_selector.title("Plugin Selector")
        plugin_selector.iconbitmap(path)
        
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
        global current_file, new_tab_frame
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
                    text_editor.pack(fill="both", padx=5, pady=5, expand=True)
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
        name.iconbitmap(path)
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
        foldername.iconbitmap(path)
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
            gpt_frame.pack(side="right", fill="both", expand=True)
            
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
        
    def actualizar_powerline(event=None):
        try:
            global current_file

            # Verificar si hay un editor de texto asociado
            index = tabs.index(tabs.select())
            text_editor = text_editors[index] if text_editors else None

            if text_editor is None:
                file_label.config(text="No file opened")
                line_info.config(text="Ln 0, Col 0")
                modified_label.config(text="✔")
                lang_label.config(text="Plain Text")
                return

            if isinstance(current_file, str):
                current_file = tk.StringVar(value=current_file)
                
            # Si current_file no está definido, inicializarlo correctamente
            if "current_file" not in globals():
                current_file = tk.StringVar(value="")

            file_name = current_file.get() if isinstance(current_file, tk.StringVar) else current_file
            file_size = os.path.getsize(file_name) if os.path.exists(file_name) else 0
            file_size_kb = f"{file_size / 1024:.1f} KB" if file_size > 1024 else f"{file_size} B"

            # Verificar que text_editor no sea None antes de obtener la posición del cursor
            if text_editor is not None:
                row, col = text_editor.index("insert").split(".")
                line_info.config(text=f"Ln {row}, Col {col}")

            modified_status = "●" if text_editor.edit_modified() else "✔"
            modified_label.config(text=modified_status)

            lexer = os.path.splitext(file_name)[1]
            language = lexer.replace(".", "") if lexer else "Plain Text"
            lang_label.config(text=language)

            file_label.config(text=f"{os.path.basename(file_name)} ({file_size_kb})")

        except Exception as e:
            ms.showerror("POWERLINE ERROR", f"Error in Powerline: {e}")
    
    main_frame = ttk.Frame(editor)
    main_frame.pack(fill="both", expand=True)
    
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=0)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=3)
       
    builtin_color_schemes = set(tom_files)
    menu_bar = tk.Menu(editor)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Save", command=guardar_cambios)
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
    
    tree_frame = ttk.Frame(main_frame, bootstyle="dark")
    tree_frame.pack(side="left", fill="y")

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
    
    gpt_frame = ttk.Frame(main_frame, bootstyle="dark")
    
    gpt_response = CodeView(gpt_frame, color_scheme=current_theme_get())
    gpt_response.pack(fill='both', expand=True)
    
    send_quest = ttk.Button(gpt_frame, text="Submit", command=answer_question)
    send_quest.pack(side='bottom')
    
    user_quest = ttk.Entry(gpt_frame, width=50)
    user_quest.pack(fill='x', side='bottom')
    
    
    file_label = ttk.Label(editor, text="Untitled", bootstyle="info", padding=5)
    file_label.pack(side="right")

    lang_label = ttk.Label(editor, text="Plain Text", bootstyle="primary", padding=5)
    lang_label.pack(side="right")

    line_info = ttk.Label(editor, text="Ln 1, Col 0", bootstyle="warning", padding=5)
    line_info.pack(side="right")

    modified_label = ttk.Label(editor, text="✔", bootstyle="success", padding=5)
    modified_label.pack(side="right")
    
    editor.bind("<Control-b>", toggle_tree_visibility)
    editor.bind("<Control-Tab>", lambda event: tabs.select((tabs.index(tabs.select()) + 1) % tabs.index("end")))
    editor.bind("<Control-Shift-Tab>", lambda event: tabs.select((tabs.index(tabs.select()) - 1) % tabs.index("end")))
    tree.bind("<<TreeviewOpen>>", expand_folder)
    editor.bind("<Control-q>", lambda event: editor.destroy())
    editor.bind("<Control-g>", toggle_gpt_visibility)
    tree.bind("<Button-3>", lambda event: tree_menu.post(event.x_root, event.y_root))
    
    for item in os.listdir(ruta_proyecto):
        item_path = os.path.join(ruta_proyecto, item)
        if os.path.isfile(item_path):
            tree.insert("", "end", text=item)
        elif os.path.isdir(item_path):
            folder_id = tree.insert("", "end", text=item, open=False)
            tree.insert(folder_id, "end", text="")
    
            
    editor.bind("<KeyRelease>", actualizar_powerline)
    editor.bind("<<Modified>>", actualizar_powerline)

    editor.mainloop()
   
def mostrar_proyectos():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect(db_path)
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
    ventana_lenguaje = tk.Toplevel(orga)
    ventana_lenguaje.title("Selection lenguaje")
    ventana_lenguaje.iconbitmap(path)
    
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
    
    menu_lenguaje = ttk.Combobox(main_frame, textvariable=seleccion, values=lenguaje_options, state="readonly", bootstyle='secondary')
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

def git_add(project_path):
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
    output_window = tk.Toplevel(orga)
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        mostrar_proyectos()
    except shutil.Error as e:
        ms.showerror("ERROR", f"Error deleting project: {e}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        mostrar_proyectos()
    
def seleccionar_ruta_editor(editor, entry):
    ruta_editor = filedialog.askopenfilename(title=f"Seleccione el ejecutable de {editor}", filetypes=[("Ejecutables", "*.exe")])
    if ruta_editor:
        entry.delete(0, tk.END)
        entry.insert(0, ruta_editor)

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
        ("Sync Files Locals", lambda: sync_repo_files(tree.item(tree.selection())['values'][5], tree.item(tree.selection())['values'][4])),
        ("Version Control", mostrar_control_versiones),
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
        context_menu = tk.Menu(orga, tearoff=0)
        for label, command in menu_items:
            context_menu.add_command(label=label, command=command)
        
        context_menu.post(event.x_root, event.y_root)

def abrir_repositorio(event):
    item_seleccionado = tree.item(tree.selection())
    url_repositorio = item_seleccionado['values'][5]

    webbrowser.open_new(url_repositorio)
    
def abrir_explorador(event):
    item_seleccionado = tree.item(tree.selection())
    ruta = item_seleccionado['values'][4]
    ruta_formateada = ruta.replace("/", "\\")
    subprocess.Popen(['explorer', ruta_formateada])
    
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
    conn = sqlite3.connect(db_path)
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

    mod_window = tk.Toplevel(orga)
    mod_window.title("Modify Project")
    mod_window.iconbitmap(path)
    
    main_frame = ttk.Frame(mod_window)
    main_frame.pack()

    entry_widgets = {}

    for field, index in field_index.items():
        field_label = ttk.Label(main_frame, text=f"{field}:")
        field_label.grid(row=index, column=0, padx=5, pady=5)

        new_value_entry = ttk.Entry(main_frame, width=50)
        new_value_entry.insert(0, current_values[index])
        new_value_entry.grid(row=index, column=1, padx=5, pady=5)

        entry_widgets[field] = new_value_entry

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
    conn = sqlite3.connect(db_path)
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
    orga.set_theme(theme_name)
    orga.update_idletasks()
    orga.geometry("")
    orga.geometry(f"{orga.winfo_reqwidth()}x{orga.winfo_reqheight()}")

def install_choco():
    subprocess.run("Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
    ms.showinfo("INSTALL COMPLETE", "Choco has install correctly")
    
def install_scoop():
    subprocess.run("Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression").wait()
    ms.showinfo("INSTALL COMPLETE", "Scoop has install correctly")

def install_lenguaje(lenguaje_selected):
    if lenguaje_selected == "Python":
        comando_python = 'choco install python3 -y'
        subprocess.Popen(["powershell", "-c", comando_python], shell=True).wait()
        ms.showinfo("INSTALL COMPLETE", f"{lenguaje_selected} Has been installed")
    elif lenguaje_selected == "NodeJS" or lenguaje_selected == "React":
        comando_node = 'choco install nodejs -y'
        subprocess.Popen(["powershell", "-c", comando_node], shell=True).wait()
        ms.showinfo("INSTALL COMPLETE", f"{lenguaje_selected} Has been installed")
    elif lenguaje_selected == "bun":
        comando_bun = 'irm bun.sh/install.ps1|iex'
        subprocess.Popen(["powershell", "-c", comando_bun], shell=True).wait()
        ms.showinfo("INSTALL COMPLETE", f"{lenguaje_selected} Has been installed")
    elif lenguaje_selected == "Rust":
        url = "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe"
        response = requests.get(url)
        file = url.split('/')[-1]
        with open(file, 'wb') as f:
            f.write(response.content)
        ms.showinfo(f"{lenguaje_selected} IS DOWNLOAD", f'{lenguaje_selected} has been downloaded and saved in the same folder as this app')
        quest = ms.askyesno("INSTALL", f"Do you want to install {lenguaje_selected} now?")
        if quest:
            subprocess.Popen([file], shell=True).wait()
            os.remove(file)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {lenguaje_selected} later, the installer is saved in the same folder as this app")
            
    elif lenguaje_selected == "Go":
        url = "https://go.dev/dl/go1.22.1.windows-amd64.msi"
        response = requests.get(url)
        file = url.split('/')[-1]
        with open(file, 'wb') as f:
            f.write(response.content)
        quest = ms.askyesno("INSTALL", f"Do you want to install {lenguaje_selected} now?")
        if quest:
            subprocess.Popen([file], shell=True).wait()
            os.remove(file)
        else:
            ms.showinfo("INSTALL LATER", f"You can install {lenguaje_selected} later, the installer is saved in the same folder as this app")
            
    elif lenguaje_selected == "flutter":
        url = "https://docs.flutter.dev/get-started/install"
        webbrowser.open_new(url)

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
    info_window = tk.Toplevel(orga)
    info_window.title("PATCH NOTES")
    info_window.geometry("1500x600")
    info_window.iconbitmap(path)

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
    
def create_theme():
        comando = "python -m ttkcreator"
        
        subprocess.run(f'{comando}', shell=True)
        
def ttk_themes():
    style = ttk.Style()
    
    themes = style.theme_names()
    
    return themes

def change_bootstrap_theme(theme_name):
    style = ttk.Style()
    
    style.theme_use(theme_name)
    
def add_to_startup():
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        open_key = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        open_key = reg.CreateKey(key, key_value)
    
    reg.SetValueEx(open_key, app_name, 0, reg.REG_SZ, exe_path)
    reg.CloseKey(open_key)
    
def remove_from_startup():
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        open_key = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(open_key, app_name)
        reg.CloseKey(open_key)
    except FileNotFoundError:
        pass
    
def check_state():
    if check_var.get() == 1:
        add_to_startup()
    else:
        remove_from_startup()
    save_config(check_var.get())

def is_in_startup():
    try:
        key = reg.HKEY_CURRENT_USER
        key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
        open = reg.OpenKey(key, key_value, 0, reg.KEY_READ)
        reg.QueryValueEx(open, app_name)
        reg.CloseKey(open)
        return True
    except FileNotFoundError:
        return False
    
def save_config(state):
    config = {"startup": state}
    with open(config_file, "w") as f:
        json.dump(config, f)
        
def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            return config.get("startup", 0)
    return 0

def setting_window():
    config_window = ttk.Toplevel(orga)
    config_window.title("Settings")
    config_window.iconbitmap(path)
    
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
    windows_context = ttk.Frame(main_frame)
    
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
    list_settings.insert(tk.END, "System Startup")
    list_settings.insert(tk.END, "Context Menu Windows")
    
    def hide_frames():
        theme_frame.grid_forget()
        ttktheme_frame.grid_forget()
        startup_frame.grid_forget()
        editor_frame.grid_forget()
        openai_frame.grid_forget()
        choco_frame.grid_forget()
        scoop_frame.grid_forget()
        editors_frame.grid_forget()
        lenguajes_frame.grid_forget()
        terminal_frame.grid_forget()
        backup_frame.grid_forget()
        windows_context.grid_forget()
        
    def select_user_config(event=None):
        selection = list_settings.curselection()
        if selection:
            index = selection[0]
            item = list_settings.get(index)
            
        if item == "Editors Configure":
            hide_frames()
            editor_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
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
            openai_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
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
            scoop_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
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
                orga.set_theme(theme_name)
                orga.update_idletasks()
            
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
        
        elif item == "System Startup":
            hide_frames()
            startup_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            quest_label = ttk.Label(startup_frame, text="You want this app to start with Windows")
            quest_label.grid(row=0,column=0, padx=2, pady=2, sticky="ew")
            
            check_btn = ttk.Checkbutton(startup_frame, variable=check_var, command=check_state)
            check_btn.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
            
        elif item == "Context Menu Windows":
            hide_frames()
            windows_context.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
            q_label = ttk.Label(windows_context, text="You want agree the app to windows context menu")
            q_label.grid(row=0,column=0, padx=2, pady=2, sticky="ew")
            
            si = ttk.Button(windows_context, text="Yes", command=lambda: agree_context_menu(menu_name, description_menu, ruta_icono, ruta_db))
            si.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
            
            no = ttk.Button(windows_context, text="No")
            no.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
            
            q_label2 = ttk.Label(windows_context, text="You want delete the app to windows context menu")
            q_label2.grid(row=2,column=0, padx=2, pady=2, sticky="ew")
            
            yes = ttk.Button(windows_context, text="Yes", command=lambda: delete_context_menu(menu_name))
            yes.grid(row=3, columnspan=2, padx=2, pady=2, sticky="nsew")
    
    list_settings.bind("<Double-1>", select_user_config)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=8)
    main_frame.grid_rowconfigure(2, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    
def previsualizar_proyecto(event=None):
    # Obtener la ruta del proyecto seleccionado desde la pantalla principal
    seleccion = tree.selection()
    if not seleccion:
        ms.showwarning("Advertencia", "Por favor selecciona un proyecto primero.")
        return

    ruta_proyecto = tree.item(seleccion, "values")[4]  # Tomar la ruta del proyecto desde los valores

    def cargar_contenido_carpeta(treeview, parent, ruta):
        """Cargar contenido de una carpeta (carpetas y archivos) de manera diferida."""
        try:
            for item in os.listdir(ruta):
                item_path = os.path.join(ruta, item)
                if os.path.isdir(item_path):
                    folder_id = treeview.insert(parent, "end", text=item, values=[item_path], open=False)
                    treeview.insert(folder_id, "end", text="(Cargando...)", tags=("placeholder",))
                else:
                    treeview.insert(parent, "end", text=item, values=[item_path])
        except PermissionError:
            ms.showwarning("Acceso denegado", f"No se pudo acceder a la carpeta: {ruta}")

    def expandir_nodo(event):
        """Cargar contenido cuando se expande un nodo con 'Cargando...'."""
        nodo = treeview.focus()
        if not nodo:
            return
        if treeview.tag_has("placeholder", treeview.get_children(nodo)):
            treeview.delete(*treeview.get_children(nodo))
            ruta_carpeta = treeview.item(nodo, "values")[0]
            cargar_contenido_carpeta(treeview, nodo, ruta_carpeta)

    def mostrar_contenido_archivo(event):
        """Mostrar el contenido del archivo seleccionado en el área de texto."""
        nodo = treeview.focus()
        if not nodo:
            return
        ruta_archivo = treeview.item(nodo, "values")[0]
        if os.path.isfile(ruta_archivo):
            try:
                with open(ruta_archivo, 'r', encoding="utf-8", errors="ignore") as file:
                    contenido = file.read()
                    scrolled_text.delete(1.0, tk.END)
                    scrolled_text.insert(tk.END, contenido)
            except Exception as e:
                ms.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def buscar_en_treeview(query):
        """Buscar archivos en el árbol y mostrar solo los que coincidan."""
        if not query.strip():
            _restaurar_treeview()
            return
        for item in treeview.get_children():
            _buscar_recursivo(item, query)

    def _restaurar_treeview():
        """Restaurar toda la estructura desde la raíz."""
        treeview.delete(*treeview.get_children())  # Limpiar el árbol actual
        root_id = treeview.insert("", "end", text=f"[Carpeta] {os.path.basename(ruta_proyecto)}", values=[ruta_proyecto], open=False)
        treeview.insert(root_id, "end", text="(Cargando...)", tags=("placeholder",))

    def _buscar_recursivo(item, query):
        """Buscar recursivamente en los hijos del nodo."""
        text = treeview.item(item, "text").lower()
        visible = query.lower() in text
        for child in treeview.get_children(item):
            visible = _buscar_recursivo(child, query) or visible
        if not visible:
            treeview.detach(item)
        else:
            parent = treeview.parent(item)
            treeview.reattach(item, parent, 'end')
        return visible

    preview_project = tk.Toplevel()
    preview_project.title(f"Previsualización del Proyecto: {ruta_proyecto}")
    preview_project.geometry("1000x700")
    preview_project.iconbitmap(path)

    estructura_frame = ttk.Frame(preview_project)
    estructura_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    scrollbar_y = ttk.Scrollbar(estructura_frame, orient="vertical")
    scrollbar_x = ttk.Scrollbar(estructura_frame, orient="horizontal")

    treeview = ttk.Treeview(estructura_frame, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    scrollbar_y.config(command=treeview.yview)
    scrollbar_x.config(command=treeview.xview)

    treeview.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    treeview.bind("<Double-1>", mostrar_contenido_archivo)
    treeview.bind("<<TreeviewOpen>>", expandir_nodo)

    estructura_frame.grid_rowconfigure(0, weight=1)
    estructura_frame.grid_columnconfigure(0, weight=1)

    search_frame = ttk.Frame(preview_project)
    search_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
    
    search_label = ttk.Label(search_frame, text="Buscar:")
    search_label.pack(side="left", padx=5)
    search_entry = ttk.Entry(search_frame)
    search_entry.pack(side="left", fill="x", expand=True, padx=5)

    search_entry.bind("<KeyRelease>", lambda event: buscar_en_treeview(search_entry.get()))

    scrolled_text = scrolledtext.ScrolledText(preview_project)
    scrolled_text.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    preview_project.grid_rowconfigure(0, weight=1)
    preview_project.grid_columnconfigure(0, weight=1)

    root_id = treeview.insert("", "end", text=f"[Carpeta] {os.path.basename(ruta_proyecto)}", values=[ruta_proyecto], open=False)
    treeview.insert(root_id, "end", text="(Cargando...)", tags=("placeholder",))
    
def mostrar_control_versiones():
    # Obtener la ruta del proyecto seleccionado desde la pantalla principal
    seleccion = tree.selection()
    if not seleccion:
        tk.messagebox.showwarning("Warning", "Please select a project first.")
        return

    ruta_proyecto = tree.item(seleccion, "values")[4]  # Tomar la ruta del proyecto desde los valores

    # Comprobar si es un repositorio Git
    if not os.path.exists(os.path.join(ruta_proyecto, '.git')):
        tk.messagebox.showerror("Error", "A Git repository was not found in the selected project.")
        return

    # Crear la ventana del panel de control de versiones
    control_versiones = tk.Toplevel(orga)
    control_versiones.title(f"Version Control: {ruta_proyecto}")
    control_versiones.iconbitmap(path)
    control_versiones.geometry("1155x600")

    # Frame para la lista de commits
    frame_commits = ttk.Frame(control_versiones)
    frame_commits.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # TreeView para mostrar los commits
    treeview_commits = ttk.Treeview(frame_commits, columns=("commit", "author", "date"), show="headings", height=36)
    treeview_commits.heading("commit", text="Commit")
    treeview_commits.heading("author", text="Autor")
    treeview_commits.heading("date", text="Fecha")

    treeview_commits.grid(row=0, column=0, sticky="nsew")

    # Scrollbar para el TreeView de commits
    scrollbar_y_commits = ttk.Scrollbar(frame_commits, orient="vertical", command=treeview_commits.yview)
    treeview_commits.configure(yscrollcommand=scrollbar_y_commits.set)
    scrollbar_y_commits.grid(row=0, column=1, sticky="ns")

    # Frame para mostrar los detalles del commit
    frame_detalles = ttk.Frame(control_versiones)
    frame_detalles.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    scrolled_text_detalles = scrolledtext.ScrolledText(frame_detalles, wrap=tk.WORD)
    scrolled_text_detalles.grid(row=0, column=0, sticky="nsew")

    # Configurar cómo se distribuyen las filas y columnas en el grid
    control_versiones.grid_rowconfigure(0, weight=1)  # Permitir que la fila del TreeView se expanda
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
        ventana_dependencias = tk.Toplevel(orga)
        ventana_dependencias.title("Dependencis Found")
        ventana_dependencias.iconbitmap(path)
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
    
def crear_plantilla():
    seleccion = tree.selection()
    if not seleccion:
        ms.showwarning("Warning", "Please select a project first.")
        return

    ruta_proyecto = tree.item(seleccion, "values")[4]  # Tomar la ruta del proyecto desde los valores

    # Escanear la estructura del proyecto
    estructura = escanear_estructura(ruta_proyecto)
    nombre_plantilla = simpledialog.askstring("Template Name", "Enter a name for the template")

    if nombre_plantilla:
        # Guardar la plantilla en formato JSON
        guardar_estructura_plantilla(nombre_plantilla, estructura)

def escanear_estructura(ruta):
    estructura = {}
    for carpeta, subcarpetas, archivos in os.walk(ruta):
        estructura[carpeta] = {
            "subcarpetas": subcarpetas,
            "archivos": archivos
        }
    return estructura

def guardar_estructura_plantilla(nombre, estructura):
    # Guardar la plantilla en un archivo JSON
    with open(f"{nombre}_plantilla.json", "w") as file:
        json.dump(estructura, file)
    ms.showinfo("Success", f"Template '{nombre}' save success.")

TEMPLATES = {
    "python": "_internal/templates/python/",
    "java": "_internal/templates/java/",
    "cpp": "_internal/templates/cpp/",
    "javascript": "_internal/templates/javascript/",
    "php": "_internal/templates/php/",
    "csharp": "_internal/templates/csharp/",
    "rust": "_internal/templates/rust/",
    "go": "_internal/templates/go/",
    "react": "_internal/templates/react/",
    "bun": "_internal/templates/bun/",
    "vue": "_internal/templates/vue/",
}

def aplicar_plantilla():
    """Permitir al usuario seleccionar una plantilla predefinida."""
    # Solicitar al usuario que seleccione un lenguaje para el proyecto
    lenguaje = askstring("Seleccionar Lenguaje", "Selecciona el lenguaje del proyecto:\n"
                                                "(python, java, cpp, javascript, php, csharp, rust, go, react, bun, vue)")

    if lenguaje and lenguaje in TEMPLATES:
        ruta_plantilla = TEMPLATES[lenguaje]
        ruta_nueva = filedialog.askdirectory(title="Select path folder for new Project")
        if not ruta_nueva:
            return

        crear_proyecto_desde_plantilla(ruta_plantilla, ruta_nueva)
    else:
        ms.showerror("Error", "Lenguaje no soportado o no válido.")


def crear_proyecto_desde_plantilla(ruta_plantilla, ruta_nueva):
    try:
        shutil.copytree(ruta_plantilla, ruta_nueva)

        ms.showinfo("Éxito", "Proyecto creado con éxito desde la plantilla.")
    except Exception as e:
        ms.showerror("Error", f"Error al crear el proyecto desde la plantilla: {e}")
    
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM proyectos WHERE nombre LIKE ? OR descripcion LIKE ? OR lenguaje LIKE ?"
        cursor.execute(query, ('%' + search_text + '%', '%' + search_text + '%', '%' + search_text + '%'))
        proyectos = cursor.fetchall()
        conn.close()

        # Insertar los resultados de búsqueda en el Treeview
        for proyecto in proyectos:
            tree.insert('', 'end', values=proyecto)
            
def agree_context_menu(name, description, ruta_icono=None, ruta_db=None):
    ruta_exe = os.path.abspath(sys.argv[0])
    ruta_icono = ruta_exe
    ruta_db = ruta_exe
    try:
        rutas = [
            r"Software\Classes\*\shell\{}".format(name),
            r"Software\Classes\Directory\shell\{}".format(name)
        ]
        
        for ruta in rutas:
            clave_menu = reg.CreateKey(reg.HKEY_CURRENT_USER, ruta)
            reg.SetValue(clave_menu, "", reg.REG_SZ, description)
            
            if ruta_icono:
                reg.SetValueEx(clave_menu, "Icon", 0, reg.REG_SZ, ruta_icono)
                
            if ruta_db:
                reg.SetValueEx(clave_menu, "db", 0, reg.REG_SZ, ruta_db)
            
            clave_comando = reg.CreateKey(clave_menu, r"command")
            reg.SetValue(clave_comando, "", reg.REG_SZ, f'"{ruta_exe}" "%1"')
            
            reg.CloseKey(clave_menu)
            reg.CloseKey(clave_comando)
            
        ms.showinfo("Organizer", f"{description} has been agree to windows context menu")
    except Exception as e:
        ms.showerror("ERROR", f"Error to agree on windows context menu: {e}")
        
def delete_context_menu(name):
    try:
        rutas = [
            r"Software\Classes\*\shell\{}".format(name),
            r"Software\Classes\Directory\shell\{}".format(name)
        ]
        
        for ruta in rutas:

            reg.DeleteKey(reg.HKEY_CURRENT_USER, ruta + r"\command")
            reg.DeleteKey(reg.HKEY_CURRENT_USER, ruta)
        
        ms.showinfo("Organizer", f"Removed '{name}' from the Windows context menu for the current user.")
    except FileNotFoundError:
        ms.showerror("ERROR", f"The entry '{name}' was not found in the context menu.")
    except Exception as e:
        ms.showerror("ERROR", f"Error removing context menu: {e}")

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
            
def open_project_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            project_data = json.load(file)
        
        id_project = project_data.get("id_project")
        project_path = project_data.get("project_path")
        editor = project_data.get("editor")
        
        if not id_project or not project_path or not editor:
            ms.showerror("ERROR", "The workspace file is invalid")
            
        configuracion_editores = cargar_configuracion_editores()
        ruta_editor = configuracion_editores.get(editor) if configuracion_editores and editor in configuracion_editores else None
        
        if not ruta_editor:
            editores_disponibles = detectar_editores_disponibles()
            ruta_editor = editores_disponibles.get(editor)
        
        nombre_proyecto = os.path.basename(project_path)
        ruta_copia = obtener_ruta_copia_proyecto(nombre_proyecto)

        # Sincronización inicial usando la última sincronización registrada
        ultima_sincronizacion = obtener_ultima_sincronizacion(id_project)
        sincronizar_diferencial(project_path, ruta_copia, ultima_sincronizacion)

        # Marcar proyecto como abierto en editor
        actualizar_estado_proyecto(id_project, True)
        
        
        def execute_project_on_subprocess1():
            try:
                process = []
                if ruta_editor:
                    editor_process = subprocess.Popen(
                        [ruta_editor, project_path], 
                        shell=True, 
                        start_new_session=True
                    )
                    process.append(editor_process)
                    terminal_process = subprocess.Popen(
                        f'Start wt -d "{project_path}"', 
                        shell=True, 
                        start_new_session=True
                    )
                    process.append(terminal_process)
                elif editor == "neovim":
                    comando_ps = f"Start-Process nvim '{project_path}' -WorkingDirectory '{project_path}'"
                    editor_process = subprocess.Popen(
                        ["powershell", "-Command", comando_ps], 
                        start_new_session=True
                    )
                    process.append(editor_process)
                elif editor == "Editor Integrated":
                    terminal_process = subprocess.Popen(
                        f'Start wt -d "{project_path}"', 
                        shell=True, 
                        start_new_session=True
                    )
                    process.append(terminal_process)
                    abrir_editor_thread(project_path, tree.item(tree.selection())['values'][1])
                else:
                    ms.showerror("ERROR", f"{editor} Not found")

                threading.Thread(target=monitor_processes_and_sync, args=(process, id_project, project_path, ruta_copia), daemon=True).start()
            except Exception as e:
                ms.showerror("ERROR", f"An error occurred while opening the project: {str(e)}")
            
        threading.Thread(target=execute_project_on_subprocess1, daemon=True).start()
        time.sleep(2)
        sys.exit(0)
            
    except Exception as e:
        ms.showerror("ERROR", f"Error to open workstation file: {e}")
        
def asociate_files_extension():
    exe_path = os.path.abspath(sys.argv[0])
    icon_path = exe_path    
    try:
        try:
            with reg.OpenKey(reg.HKEY_CLASSES_ROOT, ".orga", 0, reg.KEY_READ) as key:
                return
        except FileNotFoundError:
            pass
        # Crear clave para la extensión .myproj
        reg_key = reg.CreateKey(reg.HKEY_CLASSES_ROOT, ".orga")
        reg.SetValue(reg_key, "", reg.REG_SZ, "Organizer")
        reg.CloseKey(reg_key)

        # Crear clave para el tipo de archivo
        reg_key = reg.CreateKey(reg.HKEY_CLASSES_ROOT, "Organizer")
        reg.SetValue(reg_key, "", reg.REG_SZ, "Archivo de Proyecto Organizer")
        
        reg_key = reg.CreateKey(reg.HKEY_CLASSES_ROOT, r"Organizer\DefaultIcon")
        reg.SetValue(reg_key, "", reg.REG_SZ, f'"{icon_path}",0')
        reg.CloseKey(reg_key)

        # Comando para abrir los archivos .myproj con nuestro .exe
        command = f'"{exe_path}" "%1"'
        reg_key = reg.CreateKey(reg.HKEY_CLASSES_ROOT, r"Organizer\shell\open\command")
        reg.SetValue(reg_key, "", reg.REG_SZ, command)
        reg.CloseKey(reg_key)
        
        ms.showinfo("ASOCIATE", "Extension workstations asociate succes")
    except Exception as e:
        ms.showerror("ERROR", f"Error to asociate extension file: {e}")
       
def show_docu():
    docu = tk.Toplevel(orga)
    docu.title("Documentation Viewer")
    docu.iconbitmap(path)
    
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
                webview.start(icon=path2)
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
    
def list_repo_contents(repo_name):
    """
    Lista los contenidos de un repositorio en la raíz.
    """
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        contents = response.json()
        return contents
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error al obtener los contenidos del repositorio: {e}")
        return []
    
def view_file_contents(repo_name, file_path):
    """
    Obtiene el contenido de un archivo y lo muestra.
    """
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
    """
    Actualiza el contenido de un archivo en el repositorio.
    """
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

def create_repository_github(description="", private=False):
    name = simpledialog.askstring("Repo Name", "Name of you new repo")
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
    
def sync_repo_files(repo_url, local_path):
    def list_files_in_repo(repo_owner, repo_name):
        """Obtiene la lista de archivos en la raíz del repositorio."""
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Failed to fetch files from the repository: {e}")
            return []

    def get_last_modified(repo_owner, repo_name, file_path):
        """Obtiene la fecha del último commit en GitHub para un archivo."""
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
        params = {"path": file_path, "page": 1, "per_page": 1}
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            commits = response.json()
            return commits[0]["commit"]["committer"]["date"] if commits else "No commits"
        except requests.exceptions.RequestException:
            return "Unknown"

    def find_local_file(file_name, search_path):
        for root, _, files in os.walk(search_path):
            if file_name in files:
                return os.path.join(root, file_name)
        return None

    def hash_file(file_path):
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def download_file(repo_owner, repo_name, file_path, local_file_path):
        url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{file_path}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            new_content = response.content

            existing_hash = hash_file(local_file_path)
            new_hash = hashlib.md5(new_content).hexdigest()

            if existing_hash == new_hash:
                ms.showinfo("SYNC FILE",f"✅ {local_file_path} it is already updated.")
                return

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            with open(local_file_path, "wb") as file:
                file.write(new_content)

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Failed to download {file_path}: {e}")

    repo_parts = repo_url.replace("https://github.com/", "").strip().split("/")
    if len(repo_parts) < 2:
        ms.showerror("Error", "Invalid repository URL.")
        return
    repo_owner, repo_name = repo_parts[:2]

    repo_files = list_files_in_repo(repo_owner, repo_name)
    if not repo_files:
        return

    files_with_dates = []
    for file in repo_files:
        if file["type"] == "file":
            file_path = file["path"]
            last_modified = get_last_modified(repo_owner, repo_name, file_path)
            files_with_dates.append({"path": file_path, "last_modified": last_modified})

    window = tk.Toplevel()
    window.title("Select Files to Sync")
    window.geometry("600x400")

    ttk.Label(window, text="Select Files to Sync", bootstyle="success", font=("Helvetica", 16)).pack(pady=10)

    files_var = {}
    for file in files_with_dates:
        file_path = file["path"]
        last_modified = file["last_modified"]
        files_var[file_path] = tk.BooleanVar()

        ttk.Checkbutton(
            window,
            text=f"{file_path} (Last Modified: {last_modified})",
            variable=files_var[file_path],
            bootstyle="secondary",
            style="Toolbutton",
        ).pack(anchor="w", padx=20, pady=5)

    def sync_selected_files():
        selected_files = [file for file, var in files_var.items() if var.get()]
        if not selected_files:
            ms.showerror("Error", "No files selected for synchronization.")
            return

        for file in selected_files:
            local_file_path = find_local_file(os.path.basename(file), local_path)

            if local_file_path:
                download_file(repo_owner, repo_name, file, local_file_path)
            else:
                ms.showerror("SYNC FILE ERROR", f"⚠ '{file}' was not found in {local_path}, it will be skipped.")

        ms.showinfo("Success", "Selected files have been synchronized.")

    ttk.Button(window, text="Sync Selected Files", bootstyle="primary", command=sync_selected_files).pack(pady=10, padx=10)
    ttk.Button(window, text="Cancel", bootstyle="secondary", command=window.destroy).pack(pady=10, padx=10)

def unify_windows():
    """Unifies all the separate windows into a single window."""
    def check_api_limits():
        url = "https://api.github.com/rate_limit"
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        
        if response.status_code == 200:
            remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 0))
            limit = int(response.headers.get("X-RateLimit-Limit", 0))
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            
            ms.showinfo("API Limits", f"Remaining Requests: {remaining_requests}/{limit}\nReset Time: {time.ctime(reset_time)}")
            
        else:
            ms.showerror("Error", f"Can't get the API limits: {response.status_code}")
    
    github = tk.Toplevel(orga)
    github.title("GitHub Repository Manager")
    github.iconbitmap(path)
    
    menu = tk.Menu(github, tearoff=0)
    github.config(menu=menu)
    help_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label='Help', menu=help_menu)
    help_menu.add_cascade(label='API Limits', command=check_api_limits)
    
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

    # Add tabs to the notebook
    notebook.add(mygithub_frame, text="My GitHub", padding=5)
    notebook.add(commits_frame, text="Repo Commits", padding=5)
    notebook.add(file_frame, text="Files", padding=5)
    notebook.add(release_frame, text="Releases", padding=5)
    notebook.add(edit_frame, text="Edit Repository", padding=5)
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
    
    repostree.pack(expand=True, fill="both", padx=5, pady=5)
    
    def filter_repositories(event):
        query = search_var.get().lower()
        for item in repostree.get_children():
            repo_name = repostree.item(item, "values")[0].lower()
            if query in repo_name:
                repostree.item(item, open=True)
                repostree.selection_set(item)
            else:
                repostree.selection_remove(item)
    
    search_label = ttk.Label(mygithub_frame, text="Search", bootstyle='info')
    search_label.pack(padx=5, pady=5, side='left', fill='x')
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(mygithub_frame, textvariable=search_var, width=40)
    search_entry.pack(pady=5, padx=5, side='left', fill='x', expand=True)
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
            progress_window = tk.Toplevel(orga)
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
    context_menu.add_command(label="➕ Create New Repository", command=create_repository_github)
    context_menu.add_command(label="📂 Clone Repository", command=clone_respository)
    context_menu.add_command(label="🗂️View Files", command=lambda: open_repo_files1(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="📊 Show Statistics", command=lambda: show_repo_stats(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="📦 Create Backup", command=lambda: backup_repository(repostree.item(repostree.selection()[0], "values")[0]))
    context_menu.add_command(label="🐞 Show Issues", command=lambda: show_repo_issues(repostree.item(repostree.selection()[0], "values")[0]))
    
    def show_github_repos():
        for item in repostree.get_children():
            repostree.delete(item)
        
        repos = obtain_github_repos()
        for repo in repos:
            repostree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], repo["visibility"], repo["clone_url"]))
    
    show_github_repos()
    
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
    
    def search_repositories():
        def search_repositories_global():
            query = search_var.get().strip()
            if not query:
                ms.showerror("Error", "Escribe algo para buscar.")
                return

            load_bar = Progressbar(github, orient=tk.HORIZONTAL, mode='indeterminate')
            load_bar.pack(side='bottom', padx=5, pady=5, fill='x')
            load_bar.start()

            repo_count = 0
            page = 1
            max_pages = 30

            try:
                while page <= max_pages:
                    url = f"https://api.github.com/search/repositories?q={query}&page={page}"
                    response = requests.get(
                        url,
                        headers={
                            "Authorization": f"token {GITHUB_TOKEN}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                    )

                    if response.status_code != 200:
                        ms.showerror("Error", f"No se pudo buscar en GitHub: {response.status_code}")
                        break

                    data = response.json()

                    if "items" in data and isinstance(data["items"], list):
                        if not data["items"]:
                            break

                        for repo in data["items"]:
                            search_tree.insert(
                                "",
                                "end",
                                values=(
                                    repo["name"],
                                    repo["owner"]["login"],
                                    repo["stargazers_count"],
                                    repo["html_url"],
                                    repo["clone_url"],
                                ),
                            )
                            repo_count += 1
                            repo_count_label.config(text=f"Found Repos: {repo_count}")
                            load_bar.step(1)

                        page += 1
                    else:
                        break

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"No se pudo buscar en GitHub: {e}")

            finally:
                load_bar.stop()
                load_bar.pack_forget()

        
        def threading_search():
            threading.Thread(target=search_repositories_global).start()
        
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
                
        def search_repos_in_treeview(event):
            search_query = search_entry_repos.get().strip().lower()
            found_items = []

            for item in search_tree.get_children():
                values = search_tree.item(item, "values")
                repo_name = values[0].lower()
                owner_name = values[1].lower()
                stars = str(values[2])

                if search_query in repo_name or search_query in owner_name or search_query in stars:
                    search_tree.item(item, tags=("match",))
                    found_items.append(item)
                else:
                    search_tree.item(item, tags=("nomatch",))

            if found_items:
                search_tree.selection_set(found_items[0])
                search_tree.focus(found_items[0])
                search_tree.see(found_items[0])
                
        def clone_repository_from_search():
            selected_item = search_tree.selection()
            if not selected_item:
                ms.showerror("ERROR", "Select a repo to clone")
                return
            
            repo_name = search_tree.item(selected_item, "values")[0]
            repo_owner = search_tree.item(selected_item, "values")[1]
            clone_url = search_tree.item(selected_item, "values")[4]

            save_path = tk.filedialog.askdirectory(title="Select Path folder")
            if not save_path:
                return

            dest_folder = os.path.join(save_path, repo_name)

            load_bar = Progressbar(github, orient=tk.HORIZONTAL, mode='indeterminate')
            load_bar.pack(side='bottom', padx=5, pady=5, fill='x')
            load_bar.start()
            
            def clone_repo():
                try:
                    subprocess.run(["git", "clone", clone_url, dest_folder], check=True)
                    ms.showinfo("Success", f"Repo '{repo_name}' successfully cloned in:\n{dest_folder}")
                except subprocess.CalledProcessError:
                    ms.showerror("Error", "The repository could not be cloned. Please verify that Git is installed.")
                finally:
                    load_bar.stop()
                    load_bar.pack_forget()
            
            threading.Thread(target=clone_repo).start()
                    

        search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=search_var, width=50).pack(pady=5, padx=10)
        ttk.Button(search_frame, text="🔍 Search", command=threading_search).pack(pady=5)

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
        
        scrolls = ttk.Scrollbar(search_frame, orient='vertical', command=search_tree.yview,
        bootstyle='primary-rounded')
        search_tree.configure(yscrollcommand=scrolls.set)
        scrolls.pack(side='right', fill='y', padx=5)
        
        search_tree.pack(expand=True, fill="both", padx=5, pady=5)
        search_tree.bind("<Double-1>", on_repo_search_double_click)
        search_tree.bind("<Button-3>", search_menu_context)
        
        repo_count_label = ttk.Label(search_frame, text="Found Repos: 0", bootstyle='info')
        repo_count_label.pack(side='left', fill='x', padx=5, pady=5, expand=True)
        
        search_repos_label = ttk.Label(search_frame, text="Search on Repos", bootstyle='info')
        search_repos_label.pack(side='left', fill='x', padx=5, pady=5, expand=True)
        
        search_entry_repos = ttk.Entry(search_frame, width=250)
        search_entry_repos.pack(side='left', fill='x', padx=5, pady=5, expand=True)
        search_entry_repos.bind("<KeyRelease>", search_repos_in_treeview)
        
        search_context_menu = tk.Menu(github, tearoff=0)
        search_context_menu.add_command(label="⭐ Agregar a Favoritos", command=lambda: star_repository(search_tree.item(search_tree.selection()[0], "values")[0], search_tree.item(search_tree.selection()[0], "values")[1]))
        search_context_menu.add_command(label="🛠️ Clonar Repositorio", command=lambda: clone_repository_from_search())

    def go_back(repo_name, repo_owner):
        if repo_history:
            repo_history.pop()
            prev_path = repo_history[-1] if repo_history else ""
            view_repo_details(repo_name, repo_owner, prev_path)

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

            file_window = tk.Toplevel(orga)
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
            
    def search_code_on_github():
        """Búsqueda de código en GitHub con paginación, scroll y visualización de código."""
        global results, current_page, max_results_per_page, prev_button, next_button

        results = []
        current_page = 0
        max_results_per_page = 10

        def search_code():
            global results, current_page

            query = search_code_var.get().strip()
            if not query:
                ms.showerror("Error", "Please enter something to search for code on GitHub.")
                return

            loading_bar.pack(side='bottom', pady=5)
            loading_bar.start(10)

            results.clear()
            page = 1

            try:
                while True:
                    url = f"https://api.github.com/search/code?q={query}&page={page}"
                    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                        "Accept": "application/vnd.github.v3+json"})
                    
                    remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 0))
                    if remaining_requests == 0:
                        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                        wait_time = reset_time - int(time.time())
                        
                        if wait_time > 0:
                            update_rate_limit_label(wait_time)
                            time.sleep(wait_time)
                            continue

                    response.raise_for_status()
                    data = response.json()
                    items = data.get("items", [])

                    if not items:
                        break

                    results.extend(items)
                    if len(items) < 30:
                        break
                    page += 1

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Could not search for code on GitHub: {e}")

            finally:
                loading_bar.stop()
                loading_bar.pack_forget()
                rate_limit_label.config(text="")
                github.after(0, update_results_display)

        def update_rate_limit_label(wait_time):
            if wait_time > 0:
                rate_limit_label.config(text=f"Rate limit reached. Please wait {wait_time} seconds.")
                if wait_time > 0:
                    github.after(1000, update_rate_limit_label, wait_time - 1)
        
        def update_results_display():
            global current_page

            if 'prev_button' in globals() and 'next_button' in globals():
                prev_button.config(state=tk.NORMAL if current_page > 0 else tk.DISABLED)
                next_button.config(state=tk.NORMAL if (current_page + 1) * max_results_per_page < len(results) else tk.DISABLED)

            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            start_index = current_page * max_results_per_page
            end_index = start_index + max_results_per_page
            page_results = results[start_index:end_index]

            for item in page_results:
                display_file_result(item)
                
        def threading_update_results_display():
            threading.Thread(target=update_results_display, daemon=True).start()

        def next_page():
            global current_page
            if (current_page + 1) * max_results_per_page < len(results):
                current_page += 1
                threading_update_results_display()

        def prev_page():
            global current_page
            if current_page > 0:
                current_page -= 1
                threading_update_results_display()

        def thread_search_code():
            threading.Thread(target=search_code, daemon=True).start()

        def display_file_result(item):
            file_name = item["name"]
            repo_full_name = item["repository"]["full_name"]
            file_path = item["path"]
            file_url = item["html_url"]
            repo_owner, repo_name = repo_full_name.split("/")

            path_label = ttk.Label(scrollable_frame, text=f"{file_path} - {repo_full_name}",
                                font=("Arial", 10, "bold"), anchor="w", foreground="blue")
            path_label.pack(fill="x", padx=10, pady=5)
            path_label.bind("<Enter>", lambda e: path_label.config(cursor="hand2"))
            path_label.bind("<Leave>", lambda e: path_label.config(cursor=""))
            path_label.bind("<Button-1>", lambda e: open_link(file_url))

            file_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"

            try:
                response = requests.get(file_api_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
                response.raise_for_status()
                file_data = response.json()

                if "encoding" in file_data and file_data["encoding"] == "base64":
                    file_content = base64.b64decode(file_data["content"]).decode("utf-8")

                    try:
                        lexer = get_lexer_for_filename(file_name)
                    except ClassNotFound:
                        lexer = pygments.lexers.get_lexer_by_name("text")
                    except Exception as e:
                        ms.showerror("Error", f"Error getting lexer for {file_name}: {e}")
                        return

                    code_view_frame = ttk.Frame(scrollable_frame)
                    code_view_frame.pack(fill="both", padx=10, pady=5)

                    code_view = CodeView(code_view_frame, wrap="word", height=20, lexer=lexer)
                    code_view.pack(expand=True, fill="both")
                    code_view.insert("end", file_content)
                    code_view.config(state=tk.DISABLED)

                else:
                    not_text_label = ttk.Label(scrollable_frame, text=f"{file_path} is not a text file and cannot be displayed.",
                                            foreground="gray")
                    not_text_label.pack(fill="x", padx=10, pady=5)

            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Could not get the code file: {e}")

        def open_link(url):
            webbrowser.open(url)

        search_bar_frame = ttk.Frame(search_code_frame)
        search_bar_frame.pack(fill="x", padx=10, pady=5)

        search_code_var = tk.StringVar()
        search_box = ttk.Entry(search_bar_frame, textvariable=search_code_var, width=60)
        search_box.pack(side="left", padx=5, expand=True, fill="x")

        search_button = ttk.Button(search_bar_frame, text="🔍 Search", command=thread_search_code)
        search_button.pack(side="right", padx=5)
        
        rate_limit_label = ttk.Label(search_code_frame, text="", foreground="red", font=("Arial", 10, "bold"))
        rate_limit_label.pack(side="bottom", pady=5)
        
        canvas = tk.Canvas(search_code_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(search_code_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        loading_bar = ttk.Progressbar(github, mode="indeterminate", bootstyle="info")
        loading_bar.pack(side='bottom', pady=5)
        loading_bar.pack_forget()

        pagination_frame = ttk.Frame(search_code_frame)  
        pagination_frame.pack(fill="x", padx=10, pady=5, side="bottom")  

        prev_button = ttk.Button(pagination_frame, text="⬅️ Previous", command=prev_page, state=tk.DISABLED)
        prev_button.pack(side="left", padx=5, pady=5)

        next_button = ttk.Button(pagination_frame, text="Next ➡️", command=next_page, state=tk.DISABLED)
        next_button.pack(side="right", padx=5, pady=5)

    
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
        
        context_menu_file = tk.Menu(orga, tearoff=0)
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
                progress_window = tk.Toplevel(orga)
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
    
    search_repositories()
    search_code_on_github()
        
menu_name = "Organizer"
description_menu = "Open Organizer"
ruta_exe = os.path.abspath(sys.argv[0])
ruta_icono = ruta_exe
ruta_db = ruta_exe
orga = ThemedTk()
orga.title('Project Organizer')
orga.geometry("1230x500")
orga.resizable(True, True)
path = resource_path("software.ico")
path2 = resource_path2("./software.png")
orga.iconbitmap(path)
temas = orga.get_themes()
ttkbootstrap_themes = ttk_themes()

saved_state = load_config()
check_var = tk.IntVar(value=saved_state if saved_state else (1 if is_in_startup() else 0))

main_frame = ttk.Frame(orga, bootstyle="default")
main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
orga.grid_rowconfigure(0, weight=1)
orga.grid_columnconfigure(0, weight=1)
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
menu = tk.Menu(orga)
orga.config(menu=menu)
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

main_frame.grid_rowconfigure(4, weight=1)

if len(sys.argv) > 1:
    open_project_file(sys.argv[1],)

crear_base_datos()
mostrar_proyectos()
set_default_theme()
check_new_version()
thread_sinc()
initialize_backup_schedule()
asociate_files_extension()
orga.mainloop()
