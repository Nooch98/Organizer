import json, os, io, shutil, sqlite3, subprocess, sys, threading, git, time, webbrowser, jedi, markdown, datetime, requests, pygments.lexers, platform, markdown2, glob, re, webview, base64, hashlib, ctypes, contextlib, argparse, difflib, urllib.request
import tkinter as tk
import ttkbootstrap as ttk
import xml.etree.ElementTree as ET
#--------------------------------------------------------#
from tkinter.simpledialog import askstring 
from urllib.parse import urlparse
from tkinter import messagebox as ms, scrolledtext, filedialog, simpledialog
from github import Github
from openai import OpenAI
from tkhtmlview import HTMLLabel
from ttkthemes import ThemedTk
from chlorophyll import CodeView
from pathlib import Path
from ttkbootstrap.constants import *
from git import GitCommandError, InvalidGitRepositoryError, Repo
from tkinter.colorchooser import askcolor
from datetime import datetime
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound
from collections import Counter
from PIL import Image, ImageTk
from ttkbootstrap.tooltip import ToolTip


main_version = "ver.2.0"
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
current_version = "v2.0"

# Integration with local control version app
VCS_DIR = ".myvcs"
vcs_configfile = ".myvcs/config.json"
vcs_githubconfigfile = ".myvcs/github_config.json"
selected_file = None
file_name = None
loaded_plugins = {}
plugin_settings_registry = []
float_win = None

EXT_TO_LANG_CLI = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".java": "Java", ".c": "C", ".cpp": "C++", ".h": "C/C++",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".html": "HTML", ".css": "CSS",
    ".json": "JSON", ".sh": "Shell", ".php": "PHP", ".dart": "Dart", ".kt": "Kotlin",
    ".swift": "Swift", ".rb": "Ruby", ".lua": "Lua",
}

PLUGIN_REPO_INDEX = "https://raw.githubusercontent.com/Nooch98/Organizer-Plugins/refs/heads/main/index.json"
PLUGIN_REPO_BASE = "https://raw.githubusercontent.com/Nooch98/Organizer-Plugins/main/"

class PluginAPI:
    def __init__(self, main_window, menu, sidebar, tree, sandbox_fn=None):
        self.main_window = main_window
        self.menu = menu
        self.sidebar = sidebar
        self.tree = tree
        self.sandbox_fn = sandbox_fn
        self._menu_commands = {}
        self._commands = {}
        
    def get_selected_project_path(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0], "values")[3]
    
    def get_selected_node(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])
    
    def add_menu_command(self, label, command):
        index = self.menu.index("end") or -1
        self.menu.add_command(label=label, command=command)
        self._menu_commands[label] = index + 1
        
    def remove_menu_command(self, label):
        index = self._menu_commands.pop(label, None)
        if index is not None:
            try:
                self.menu.delete(index)
            except Exception as e:
                print(f"[PluginAPI] Error deleting menu '{label}': {e}")
        
    def add_sidebar_widget(self, widget):
        widget.pack(in_=self.sidebar, anchor="w", padx=5, pady=5)
        
    def add_main_button(self, text, command, row=99, column=0, **grid_kwargs):
        btn = ttk.Button(self.main_window, text=text, command=command)
        btn.grid(row=row, column=column, padx=5, pady=5, **grid_kwargs)
        return btn
    
    def register_settings_section(self, name, frame_builder):
        plugin_settings_registry.append((name, frame_builder))
        
    def unregister_settings_section(self, title):
        global plugin_settings_registry
        plugin_settings_registry = [entry for entry in plugin_settings_registry if entry[0] != title]
        
    def register_command(self, name, func, description=""):
        self._commands[name] = {
            "callback": func,
            "description": description
        }

    def run_command(self, name):
        if name in self._commands:
            self._commands[name]["callback"]()
        else:
            raise ValueError(f"Command '{name}' not found.")

class CollapsibleSection(ttk.LabelFrame):
    def __init__(self, parent, title, *args, **kwargs):
        super().__init__(parent, text=title, *args, **kwargs)
        self.columnconfigure(0, weight=1)

        # Etiqueta colapsable/expandible
        self.toggle_label = ttk.Label(self, text="▾", cursor="hand2", bootstyle="inverted-info")
        self.toggle_label.grid(row=0, column=0, sticky="ne", padx=4, pady=2)
        self.toggle_label.bind("<Button-1>", lambda e: self.toggle())

        # Contenedor de contenido
        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.collapsed = False

    def toggle(self):
        if self.collapsed:
            self.content_frame.grid()
            self.toggle_label.config(text="▾")
        else:
            self.content_frame.grid_remove()
            self.toggle_label.config(text="▸")
        self.collapsed = not self.collapsed

def load_plugins(api, config_path="plugin_config.json"):
    plugin_dir = os.path.join(os.getcwd(), "plugins")
    os.makedirs(plugin_dir, exist_ok=True)
    sys.path.insert(0, plugin_dir)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            plugin_active = config.get(module_name, True)
            if not plugin_active:
                continue
            
            try:
                plugin = __import__(module_name)
                if hasattr(plugin, "register"):
                    plugin.register(api)
                else:
                    ms.showinfo("Plugins", f"[⛔] Plugin {module_name} don't have register function")
            except Exception as e:
                ms.showinfo("Plugins", f"[⛔] Plugin {module_name} error: {e}")
                
def gestor_plugins(api, config_path="plugin_config.json"):
    top = tk.Toplevel(orga)
    top.title("Plugin Manager")
    top.geometry("500x600")
    top.iconbitmap(path)

    plugin_dir = os.path.join(os.getcwd(), "plugins")
    os.makedirs(plugin_dir, exist_ok=True)
    sys.path.insert(0, plugin_dir)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    plugin_vars = {}

    def reload_plugin(name):
        try:
            if name in sys.modules:
                plugin = sys.modules[name]

                if hasattr(plugin, "unregister"):
                    plugin.unregister(api)

                del sys.modules[name]
                loaded_plugins.pop(name, None)

            # Volver a importar
            plugin = __import__(name)
            if var.get():
                if hasattr(plugin, "register"):
                    plugin.register(api)
                    loaded_plugins[name] = plugin
                else:
                    ms.showerror("Plugin", f"[⚠️] {name} has no 'register'")
            else:
                ms.showinfo("Plugin", f"[ℹ️] {name} is disabled")
        except Exception as e:
            ms.showerror("Plugin", f"[⛔] Error reloading {name}: {e}")

    def guardar_config():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({n: v.get() for n, v in plugin_vars.items()}, f, indent=4)
        ms.showinfo("Plugins", "Save Changes.")

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            plugin_path = os.path.join(plugin_dir, filename)

            frame = ttk.Frame(top, padding=5)
            frame.pack(fill="x", padx=5, pady=5)

            var = tk.BooleanVar(value=config.get(module_name, True))
            plugin_vars[module_name] = var

            def toggle_plugin(name=module_name, var=var):
                try:
                    if name in sys.modules:
                        plugin = sys.modules[name]
                        if hasattr(plugin, "unregister"):
                            plugin.unregister(api)
                        del sys.modules[name]
                        loaded_plugins.pop(name, None)

                    if var.get():
                        plugin = __import__(name)
                        if hasattr(plugin, "register"):
                            plugin.register(api)
                            loaded_plugins[name] = plugin
                            print(f"[✓] {name} activado")
                        else:
                            ms.showerror("Plugin", f"[⚠️] {name} It does not have a register() function")
                    else:
                        print(f"[🛑] {name} desactivado")
                except Exception as e:
                    ms.showerror("Plugin", f"[⛔] Error updating {name}:\n{e}")

            cb = ttk.Checkbutton(frame, text=module_name, variable=var, command=toggle_plugin)
            cb.grid(row=0, column=0, sticky="w")

            metadata = {}
            try:
                metadata_path = os.path.join(plugin_dir, module_name + "_meta.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                desc = metadata.get("description", "No description.")
                version = metadata.get("version", "1.0")
                author = metadata.get("author", "Unknown")

                ttk.Label(frame, text=f"📦 {desc}", font=("Segoe UI", 8), wraplength=400).grid(row=1, column=0, columnspan=2, sticky="w")
                ttk.Label(frame, text=f"👤 {author} | 🔢 v{version}", font=("Segoe UI", 7), foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w")

                reload_label = ttk.Label(frame, text="🔄", cursor="hand2")
                reload_label.grid(row=0, column=1, sticky="e", padx=5)
                reload_label.bind("<Button-1>", lambda e, name=module_name, var=var: toggle_plugin(name, var))

            except Exception as e:
                ttk.Label(frame, text=f"[Error loading plugin]: {e}", foreground="red").grid(row=1, column=0, columnspan=2)

    ttk.Button(top, text="Save Changes", command=guardar_config).pack(pady=10)
    ttk.Button(top, text="Marketplace", command=open_marketplace).pack(pady=10)

def descargar_json(url):
    with urllib.request.urlopen(url) as response:
        return json.load(response)

def descargar_y_instalar_plugin(nombre_plugin, repo_path):
    plugin_url_base = f"{PLUGIN_REPO_BASE}{repo_path}/"
    files = ["{}.py".format(nombre_plugin), "{}_meta.json".format(nombre_plugin)]

    for file in files:
        try:
            file_url = plugin_url_base + file
            plugin_dir = os.path.join("plugins", file)
            with urllib.request.urlopen(file_url) as response:
                with open(plugin_dir, "wb") as f:
                    f.write(response.read())
        except Exception as e:
            ms.showerror("Marketplace", f"Failed to download {file}: {e}")
            return

    ms.showinfo("Marketplace", f"✅ {nombre_plugin} installed!")

def open_marketplace():
    top = tk.Toplevel()
    top.title("Plugin Marketplace")
    top.geometry("650x600")

    canvas = tk.Canvas(top)
    scrollbar = ttk.Scrollbar(top, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    try:
        index = descargar_json(PLUGIN_REPO_INDEX)
    except Exception as e:
        ms.showerror("Marketplace", f"Failed to fetch plugin list:\n{e}")
        return

    for plugin in index:
        frame = ttk.Frame(scrollable_frame, padding=10, relief="ridge")
        frame.pack(fill="x", padx=10, pady=5)

        # Título
        ttk.Label(frame, text=f"🔌 {plugin['name']}  🔢 v{plugin['version']}", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        # Autor
        ttk.Label(frame, text=f"👤 {plugin['author']}", font=("Segoe UI", 8), foreground="gray").pack(anchor="w")

        # Descripción corta
        ttk.Label(frame, text=f"📄 {plugin['description']}", font=("Segoe UI", 9), wraplength=500).pack(anchor="w", pady=2)

        # Long description si existe
        if "long_description" in plugin:
            ttk.Label(frame, text=plugin["long_description"], font=("Segoe UI", 8), foreground="gray", wraplength=500).pack(anchor="w", pady=2)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="🛠 Install / Update", command=lambda p=plugin: descargar_y_instalar_plugin(p["name"], p["repo_path"])).pack(side="right")

        if "repository" in plugin:
            ttk.Button(btn_frame, text="🔗 View Repo", command=lambda: webbrowser.open(plugin["repository"])).pack(side="right", padx=5)

def plugin_needs_update(local_meta, remote_version):
    return local_meta.get("version") != remote_version

def show_notification(message, duration=3000, type_="info"):
    styles = {
        "info":     {"bg": "#3498db", "fg": "white", "icon": "ℹ️"},
        "success":  {"bg": "#27ae60", "fg": "white", "icon": "✅"},
        "warning":  {"bg": "#f39c12", "fg": "black", "icon": "⚠️"},
        "error":    {"bg": "#e74c3c", "fg": "white", "icon": "❌"},
    }

    style = styles.get(type_, styles["info"])
    full_msg = f"{style['icon']} {message}"

    notif = tk.Toplevel(orga)
    notif.overrideredirect(True)
    notif.attributes("-topmost", True)
    notif.configure(bg=style["bg"])

    label = ttk.Label(
        notif, text=full_msg,
        background=style["bg"], foreground=style["fg"],
        anchor="center", font=("Segoe UI", 9, "bold")
    )
    label.pack(ipadx=10, ipady=5)

    orga.update_idletasks()
    notif.update_idletasks()
    notif_width = 240
    notif_height = 40
    x = orga.winfo_x() + orga.winfo_width() - notif_width - 20
    y = orga.winfo_y() + orga.winfo_height() - notif_height - 20
    notif.geometry(f"{notif_width}x{notif_height}+{x}+{y}")

    notif.after(duration, notif.destroy)

def make_file_hide(path):
    FILE_ATTRIBUTE_HIDDEN = 0x02
    
    try:
        ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)
    except Exception as e:
        show_notification(f"[ERROR] The file could not be hidden: {e}", type_="error")
        
def quit_attribute_only_read_hide(path):
    try:
        FILE_ATTRIBUTE_NORMAL = 0x80
        ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_NORMAL)
    except Exception as e:
         show_notification(f"[ERROR] Attributes could not be cleared: {e}", type_="error")

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
        ms.showerror("ERROR", f"Failed to obtain GitHub user. Check your network connection and GitHub token. Error: {str(e)}")

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
                        platform_name = platform.system()
                        if platform_name == "Windows":
                            asset_name = "Organizer_setup.exe"
                        elif platform_name == "Linux":
                            asset_name = "Organizer_linux.zip"
                        else:
                            ms.showerror("ERROR", f"Unsupported platform: {platform_name}")
                            return "Unsupported platform"

                        for asset in assets:
                            if asset["name"] == asset_name:
                                selected_asset = asset
                                break

                        if not selected_asset:
                            ms.showerror("ERROR", f"Can't found the file {asset_name} for {platform_name}. Please check the release assets on GitHub.")
                            return f"Can't found the file {asset_name}"
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
        ms.showerror("ERROR", f"Failed to verify the latest version. Check your network connection or GitHub API availability. Error: {str(e)}")

def thread_check_update():
    threading.Thread(target=check_new_version, daemon=True).start()

def obtener_carpeta_proyectos_app():
    ruta_base_app = Path(__file__).parent  # Obtiene la ruta donde está instalada la app
    carpeta_proyectos = ruta_base_app / "_internal" / "projects"

    carpeta_proyectos.mkdir(parents=True, exist_ok=True)
    
    return carpeta_proyectos

def obtener_ruta_copia_proyecto(nombre_proyecto):
    carpeta_proyectos = obtener_carpeta_proyectos_app()
    ruta_copia = carpeta_proyectos / nombre_proyecto
    ruta_copia.mkdir(parents=True, exist_ok=True)
    return ruta_copia

def obtener_info_proyecto(id_proyecto):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT ruta, nombre FROM proyectos WHERE id=?", (id_proyecto,))
    resultado = cursor.fetchone()
    if resultado:
        ruta_usuario, nombre_proyecto = resultado
        ruta_copia = os.path.join("MisProyectos", nombre_proyecto)

        cursor.execute("SELECT abierto_editor, ultima_sincronizacion FROM estado_proyectos WHERE id_proyecto=?", (id_proyecto,))
        estado = cursor.fetchone() or (0, None)
        
        conn.close()
        return ruta_usuario, ruta_copia, estado[0], estado[1]
    
    conn.close()
    return None, None, None, None

# Función para actualizar el estado de sincronización en la tabla estado_proyectos
def actualizar_estado_proyecto(id_proyecto, sincronizado, editor_usado=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    if editor_usado is None:
        editor_usado = obtener_editor_por_defecto()
    
    cursor.execute("""
        INSERT INTO estado_proyectos (id_proyecto, abierto_editor, ultima_sincronizacion, editor_utilizado)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id_proyecto) DO UPDATE SET
            abierto_editor = ?,
            ultima_sincronizacion = ?,
            editor_utilizado = ?
    """, (
        id_proyecto, int(sincronizado), now, editor_usado,
        int(sincronizado), now, editor_usado
    ))

    conn.commit()
    conn.close()

def asegurar_editor_utilizado_column():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(estado_proyectos)")
    columnas = [col[1] for col in cursor.fetchall()]

    if "editor_utilizado" not in columnas:
        cursor.execute("ALTER TABLE estado_proyectos ADD COLUMN editor_utilizado TEXT")
        conn.commit()

    conn.close()

def registry_activity(name, project_path):
    activity_file = "organizer_recent.json"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {"name": name, "path": project_path, "timestamp": now}
    
    try:
        with open(activity_file, "r", encoding="utf-8") as f:
            data  = json.load(f)
            
    except:
        data = []
        
    data = [item for item in data if item["path"] != project_path]
    data.insert(0, entry)
    data = data[:10]
    with open(activity_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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
        with open(archivo_configuracion_editores, "r", encoding="utf-8") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)

            if isinstance(configuracion.get("default"), dict):
                default_dict = configuracion["default"]
                if "default" in default_dict:
                    configuracion["default"] = default_dict["default"]

            return configuracion

    except FileNotFoundError:
        ms.showwarning("WARNING", "Config file not found")
        return None
    except json.JSONDecodeError:
        ms.showerror("ERROR", "Config file is corrupted or invalid JSON")
        return None

def guardar_configuracion_editores(rutas_editores, editor_por_defecto=None):
    configuracion = {}

    for editor, entry in rutas_editores.items():
        ruta = entry.get()
        if ruta:
            configuracion[editor] = ruta

    if editor_por_defecto:
        if isinstance(editor_por_defecto, dict) and "default" in editor_por_defecto:
            configuracion["default"] = editor_por_defecto["default"]
        elif isinstance(editor_por_defecto, str):
            configuracion["default"] = editor_por_defecto
        else:
            ms.showwarning("WARNING", "'default_editor' has an invalid format and will not be saved.")

    with open(archivo_configuracion_editores, "w", encoding="utf-8") as archivo_configuracion:
        json.dump(configuracion, archivo_configuracion, indent=4)
        
def obtener_editor_por_defecto():
    config = cargar_configuracion_editores()
    if not config:
        return None
    predeterminado = config.get("default")
    return config.get(predeterminado) if predeterminado else None

def abrir_proyecto(id_proyecto, ruta, editor):
    ruta_formateada = ruta.replace("/", "\\")

    configuracion_editores = cargar_configuracion_editores()
    ruta_editor = None
    
    if editor and configuracion_editores:
        ruta_editor = configuracion_editores.get(editor)

    if not ruta_editor and configuracion_editores:
        editor_por_defecto = configuracion_editores.get("default")
        ruta_editor = configuracion_editores.get(editor_por_defecto)

    if not ruta_editor:
        editores_disponibles = detectar_editores_disponibles()
        ruta_editor = editores_disponibles.get(editor or editor_por_defecto)

    nombre_proyecto = os.path.basename(ruta)
    ruta_copia = obtener_ruta_copia_proyecto(nombre_proyecto)

    ultima_sincronizacion = obtener_ultima_sincronizacion(id_proyecto)
    sincronizar_diferencial(ruta_formateada, ruta_copia, ultima_sincronizacion)
    
    registry_activity(nombre_proyecto, ruta_formateada)

    def execute_project_on_subprocess():
        try:
            process = []
            if ruta_editor:
                editor_process = subprocess.Popen(
                    [ruta_editor, ruta_formateada], 
                    shell=True, 
                    start_new_session=True
                )
                process.append(editor_process)
                terminal_process = subprocess.Popen(
                    f'Start wt -d "{ruta_formateada}"', 
                    shell=True, 
                    start_new_session=True
                )
                process.append(terminal_process)
            elif editor == "neovim":
                comando_ps = f"Start-Process nvim '{ruta_formateada}' -WorkingDirectory '{ruta_formateada}'"
                editor_process = subprocess.Popen(
                    ["powershell", "-Command", comando_ps], 
                    start_new_session=True
                )
                process.append(editor_process)
            elif editor == "Integrated Editor":
                terminal_process = subprocess.Popen(
                    f'Start wt -d "{ruta_formateada}"', 
                    shell=True, 
                    start_new_session=True
                )
                process.append(terminal_process)
                abrir_editor_thread(ruta, id_proyecto)
            else:
                show_notification(f"{editor} Not found", type_="warning")

            threading.Thread(target=monitor_processes_and_sync, args=(process, id_proyecto, ruta, ruta_copia), daemon=True).start()

        except Exception as e:
            show_notification(f"An error occurred while opening the project. Check the editor path and project files. Error: {str(e)}", type_="error")

    threading.Thread(target=execute_project_on_subprocess, daemon=True).start()
    
def monitor_processes_and_sync(processes, id_proyecto, ruta, ruta_copia, editor_usado=None):
    # Esperar a que todos los procesos finalicen
    for process in processes:
        process.wait()

    ultima_sincronizacion = obtener_ultima_sincronizacion(id_proyecto)
    sincronizar_diferencial(ruta, ruta_copia, ultima_sincronizacion)

    # Actualizar el estado del proyecto a cerrado
    if editor_usado is None:
        editor_usado = obtener_editor_por_defecto()
    
    actualizar_estado_proyecto(id_proyecto, False, editor_usado)

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

        proj_id, name, description, language, path, repo = proyecto

        tree.insert(
            "", "end", iid=path, text=name,
            values=(proj_id, description, language, path, repo)
        )

        tree.insert(path, "end", iid=f"{path}_dummy", text="(loading...)")

    conn.close()
    
def show_projects_thread():
    threading.Thread(target=mostrar_proyectos, daemon=True).start()
    
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
        ("Create Workspace", lambda: save_project_file(tree.item(tree.selection())['values'][1],tree.item(tree.selection())['values'][3], selected_editor.get())),
        ("Edit", modificar_proyecto),
        ("Show Tasks", lambda: open_tasks_projects(tree.item(tree.selection())['values'][3])),
        ("Save version", lambda: promp_coment_and_save_version(tree.item(tree.selection())['values'][3])),
        ("Show Versions History", lambda: show_versions_historial(tree.item(tree.selection())['values'][3])),
        ("Show Resumen", lambda: show_dashboard_proyect(tree.item(tree.selection())['values'][3])),
        ("TreeMap", lambda: show_project_hierarchy_map(tree.item(tree.selection())['values'][3])),
        ("Delete", lambda: eliminar_proyecto(tree.item(tree.selection())['values'][1], tree.item(tree.selection())['values'][3])),
        ("Notes", lambda: open_project_notes(tree.item(tree.selection())['values'][3])),
        ("Sync Files Locals", lambda: sync_repo_files(tree.item(tree.selection())['values'][4], tree.item(tree.selection())['values'][3])),
        ("Version Control", mostrar_control_versiones),
        ("Detect Dependencies", detectar_dependencias),
        #("Git Init", lambda: git_init(selected_project_path)),
        #("Git Add", lambda: git_add(selected_project_path)),
        #("Git Commit", lambda: git_commit(selected_project_path)),
        #("Git Status", lambda: git_status(selected_project_path)),
        #("Git Log", lambda: git_log(selected_project_path)),
        #("Git Diff", lambda: git_diff(selected_project_path)),
        #("Git Pull", lambda: git_pull(selected_project_path)),
        #("Git Push", lambda: git_push(selected_project_path)),
        #("Git Branch", lambda: git_branch(selected_project_path)),
        #("Git Checkout", lambda: git_checkout(selected_project_path)),
        #("Git Merge", lambda: git_merge(selected_project_path)),
        #("Git Remote", lambda: git_remote(selected_project_path)),
        #("Git Fetch", lambda: git_fetch(selected_project_path)),
        #("Git Reset", lambda: git_reset(selected_project_path)),
        #("Git Revert", lambda: git_revert(selected_project_path))
    ]
    rowid = tree.identify_row(event.y)
    if rowid:
        context_menu = tk.Menu(orga, tearoff=0)
        for label, command in menu_items:
            context_menu.add_command(label=label, command=command)
        
        context_menu.post(event.x_root, event.y_root)

def abrir_repositorio(event):
    item_seleccionado = tree.item(tree.selection())
    url_repositorio = item_seleccionado['values'][4]

    webbrowser.open_new(url_repositorio)
    
def abrir_explorador(event):
    item_seleccionado = tree.item(tree.selection())
    ruta = item_seleccionado['values'][3]
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
    try:
        with open("user_theme_config.json", "r", encoding="utf-8") as f:
            saved = json.load(f)
            theme_name = saved.get("theme")
            library = saved.get("library")

            if library == "ttkbootstrap" and theme_name in temas:
                orga.set_theme(theme_name)
                return

            elif library == "ttk" and theme_name in ttk.Style().theme_names():
                style = ttk.Style()
                style.theme_use(theme_name)
                return
    except Exception as e:
            return

    system_theme = get_system_theme()
    default_theme = "darkly" if system_theme == "dark" else "cosmo"
    change_bootstrap_theme(theme_name=default_theme)

    
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
    for plugin_section, _ in plugin_settings_registry:
        list_settings.insert(tk.END, plugin_section)
    
    
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
            configs_editors = cargar_configuracion_editores() or {}

            def guardar_y_cerrar():
                guardar_configuracion_editores(rutas_editores, configs_editors)
                show_notification("Editor configuration saved")

            def set_default_editor(editor_name):
                configs_editors["default"] = editor_name
                guardar_configuracion_editores(rutas_editores, configs_editors)
                show_notification(f"'{editor_name}' set as default editor ✅")

            for i, programa in enumerate(editores_disponibles):
                # Label
                label = ttk.Label(editor_frame, text=programa)
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                # Entry
                entry = ttk.Entry(editor_frame, width=60)
                entry.grid(row=i, column=1, padx=5, pady=5)
                if programa in configs_editors:
                    entry.insert(0, configs_editors[programa])
                rutas_editores[programa] = entry

                # Agree button
                agree_btn = ttk.Button(editor_frame, text="Agree", command=lambda p=programa, e=entry: seleccionar_ruta_editor(p, e))
                agree_btn.grid(row=i, column=2, padx=2, pady=5)

                # Set Default button
                default_btn = ttk.Button(editor_frame, text="Set Default", command=lambda p=programa: set_default_editor(p))
                default_btn.grid(row=i, column=3, padx=2, pady=5)

                # Confirm button (individual)
                confirm_btn = ttk.Button(editor_frame, text="Confirm", command=guardar_y_cerrar)
                confirm_btn.grid(row=i, column=4, padx=2, pady=5)
        
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
            
            for widget in theme_frame.winfo_children():
                widget.destroy()

            num_columns = 4
            style = ttk.Style()

            for index, theme in enumerate(temas):
                row = index // num_columns
                column = index % num_columns

                preview = ttk.Frame(theme_frame, borderwidth=2, relief="ridge", padding=8)
                preview.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

                ttk.Label(preview, text=theme, font=("Segoe UI", 9, "bold")).pack(anchor="center", pady=(0, 5))
                sample_btn = ttk.Button(preview, text="Sample")
                sample_entry = ttk.Entry(preview)
                sample_btn.pack(fill="x", pady=2)
                sample_entry.pack(fill="x", pady=2)

                def apply_theme(theme_name=theme):
                    orga.set_theme(theme_name)
                    orga.update_idletasks()
                    with open("user_theme_config.json", "w", encoding="utf-8") as f:
                        json.dump({"library": "ttk", "theme": theme_name}, f)

                preview.bind("<Button-1>", lambda e, t=theme: apply_theme(t))
                for child in preview.winfo_children():
                    child.bind("<Button-1>", lambda e, t=theme: apply_theme(t))

        elif item == "TTKTheme":
            hide_frames()
            ttktheme_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

            def ttk_themes():
                style = ttk.Style()
                return style.theme_names()

            def change_ttktheme(theme_name):
                style.theme_use(theme_name)
                with open("user_theme_config.json", "w", encoding="utf-8") as f:
                    json.dump({"library": "ttkbootstrap", "theme": theme_name}, f)

            themes = ttk_themes()

            for widget in ttktheme_frame.winfo_children():
                widget.destroy()

            num_columns = 4
            style = ttk.Style()

            for index, theme in enumerate(themes):
                row = index // num_columns
                column = index % num_columns

                preview = ttk.Frame(ttktheme_frame, borderwidth=2, relief="groove", padding=8)
                preview.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

                ttk.Label(preview, text=theme, font=("Segoe UI", 9, "bold")).pack(pady=(0, 5))
                ttk.Button(preview, text="Button").pack(fill="x", pady=2)
                ttk.Entry(preview).pack(fill="x", pady=2)

                # Aplica tema al hacer clic
                preview.bind("<Button-1>", lambda e, t=theme: change_ttktheme(t))
                for child in preview.winfo_children():
                    child.bind("<Button-1>", lambda e, t=theme: change_ttktheme(t))

            # Botón para crear nuevo tema (si lo tienes definido)
            ttk.Button(ttktheme_frame, text="🎨 Create Theme", command=create_theme).grid(
                row=row + 1, column=0, columnspan=num_columns, padx=10, pady=10, sticky="ew"
            )
        
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
            
        for plugin_section, frame_builder in plugin_settings_registry:
            if item == plugin_section:
                hide_frames()
                plugin_frame = ttk.Frame(main_frame)
                plugin_frame.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
                frame_builder(plugin_frame)
    
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
    complemento = "Github_control.exe"

    if os.path.exists(complemento):
        subprocess.Popen([complemento], shell=True)
    else:
        if ms.askyesno("File not found", f"{complemento} not found.\nDo you want to download and install it?"):
            url = "https://github.com/Nooch98/Organizer/releases/latest/download/GithubControl_SilenInstall_x64.exe"
            file_name = "GithubControl_SilenInstall_x64.exe"
            
            # Crear ventana de progreso
            progress_win = tk.Toplevel()
            progress_win.title("Downloading...")
            tk.Label(progress_win, text="Downloading file...").pack(pady=10)
            progress = ttk.Progressbar(progress_win, orient="horizontal", length=300, mode="determinate")
            progress.pack(pady=10)
            
            progress_win.update()

            try:
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    total = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    chunk_size = 8192

                    with open(file_name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                percent = (downloaded / total) * 100
                                progress['value'] = percent
                                progress_win.update_idletasks()
                
                progress_win.destroy()

                subprocess.Popen([file_name, "/SP-", "/VERYSILENT", "/NORESTART"], shell=True)

                ms.showinfo("SUCCESS", "File has been downloaded and is being installed.")
                os.remove(file_name)

            except Exception as e:
                progress_win.destroy()
                ms.showerror("Download Failed", str(e))

def open_project_notes(project_path):
    notes_path = os.path.join(project_path, ".organizer_notes.txt")
    
    notes = tk.Toplevel(orga)
    notes.title("Project Notes")
    notes.iconbitmap(path)
    
    text_area = scrolledtext.ScrolledText(notes)
    text_area.pack(fill='both', expand=True)
    
    if os.path.exists(notes_path):
        with open(notes_path, "r", encoding="utf-8") as f:
            text_area.insert("1.0", f.read())
    
    def save_close():
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write(text_area.get("1.0", "end-1c"))
        notes.destroy()
        
    notes.protocol("WM_DELETE_WINDOW", save_close)
    
def create_control_versions_structure(project_path):
    project_name = os.path.basename(project_path)

    projects_versions_folder = "projects_versions"
    versions_folder = os.path.join(projects_versions_folder, project_name)

    if not os.path.exists(projects_versions_folder):
        os.makedirs(projects_versions_folder)
        make_file_hide(projects_versions_folder)

    os.makedirs(versions_folder, exist_ok=True)
    make_file_hide(versions_folder)
    
    metadata_path = os.path.join(versions_folder, "versions.json")
    if not os.path.exists(metadata_path):
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump([], f)

def promp_coment_and_save_version(project_path):
    win = tk.Toplevel(orga)
    win.title("Save project version")
    win.iconbitmap(path)
    
    ttk.Label(win, text="Coment for version:").pack(padx=5, pady=5)
    
    entry = tk.Text(win, height=5, wrap="word")
    entry.pack(padx=5, fill='both', expand=True)
    
    def confirm():
        coment = entry.get("1.0", "end-1c").strip()
        save_project_version(project_path, coment)
        win.destroy()
        ms.showinfo("Save Version", f"Version successfully created for: {os.path.basename(project_path)}.")
        
    ttk.Button(win, text="Confirm", command=confirm).pack(padx=5)     
        
def save_project_version(project_path, coment=""):
    create_control_versions_structure(project_path)
    
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    version_name = f"v_{timestamp}"
    
    project_name = os.path.basename(project_path)
    destini_path = os.path.join("projects_versions", project_name, version_name)
    
    shutil.copytree(project_path, destini_path, ignore=shutil.ignore_patterns("projects_versions", ".git", "__pycache__"))
    
    metadata_path = os.path.join("projects_versions", project_name, "versions.json")
    with open(metadata_path, "r+", encoding="utf-8") as f:
        versions = json.load(f)
        versions.append({
            "name": version_name,
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "coment": coment})
        f.seek(0)
        json.dump(versions, f, indent=4)
        f.truncate()
        
def show_versions_historial(project_path):
    project_name = os.path.basename(project_path)
    metadata_path = os.path.join("projects_versions", project_name, "versions.json")
    if not os.path.exists(metadata_path):
        ms.showinfo("No versions", "This project has no saved versions")
        return
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        versions = json.load(f)
        
    window = tk.Toplevel(orga)
    window.title("Versions History")
    window.iconbitmap(path)
    
    tree = ttk.Treeview(window, columns=("date", "coment"), show="headings")
    tree.heading("date", text="Date")
    tree.heading("coment", text="Coment")
    tree.pack(fill='both', expand=True)
    
    for v in versions:
        tree.insert("", "end", iid=v["name"], values=(v["date"], v["coment"]))
        
    def restore():
        selection = tree.selection()
        if not selection:
            ms.showwarning("Warning", "No version selected.")
            return

        version_name = selection[0]
        if not version_name.startswith("v_"):
            ms.showerror("Error", "Invalid version selected.")
            return

        project_base = os.path.dirname(os.path.abspath(__file__))
        origin_path = os.path.join(project_base, "projects_versions", project_name, version_name)

        if not os.path.exists(origin_path):
            ms.showerror("Error", f"Version folder not found:\n{origin_path}")
            return

        confirm = ms.askyesno(
            "Confirm Restore",
            f"Do you want to restore version '{version_name}'?\nThis will overwrite the current project:\n{project_path}"
        )
        if not confirm:
            return

        try:
            for item in os.listdir(project_path):
                if item == "projects_versions":
                    continue
                item_path = os.path.join(project_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

            for item in os.listdir(origin_path):
                src = os.path.join(origin_path, item)
                dst = os.path.join(project_path, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            show_notification(f"✅ Project restored to version: {version_name}", type_="success")
            mostrar_proyectos()

        except Exception as e:
            ms.showerror("Restore Error", f"Failed to restore version:\n{e}")
                
    btn_restore = ttk.Button(window, text="Restore version", command=restore)
    btn_restore.pack(padx=5, pady=5)

def open_tasks_projects(project_path):
    import re

    task_path = os.path.join(project_path, ".organizer_tasks.json")
    scan_config_path = os.path.join(project_path, ".organizer_taskscan.json")

    if not os.path.exists(task_path):
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        make_file_hide(task_path)

    with open(task_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    window = tk.Toplevel(orga)
    window.title("Project Tasks")
    window.geometry("400x500")
    window.iconbitmap(path)

    list_frame = ttk.Frame(window)
    list_frame.pack(fill='both', expand=True, padx=5, pady=5)

    entrys = []

    def save_task():
        new = []
        for text, var in entrys:
            new.append({"text": text.get(), "done": var.get()})
        quit_attribute_only_read_hide(task_path)
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump(new, f, indent=4)
        make_file_hide(task_path)

    def agree_task():
        text = new_task_entry.get().strip()
        if text:
            var = tk.BooleanVar()
            entrys.append((tk.StringVar(value=text), var))
            ttk.Checkbutton(list_frame, text=text, variable=var).pack(anchor="w")
            new_task_entry.delete(0, "end")
            save_task()

    def load_task():
        for task in tasks:
            text = tk.StringVar(value=task["text"])
            var = tk.BooleanVar(value=task["done"])
            chk = ttk.Checkbutton(list_frame, textvariable=text, variable=var)
            chk.pack(anchor="w")
            entrys.append((text, var))

    def delete_complete_task():
        for widget in list_frame.winfo_children():
            widget.destroy()
        filtered = [(t, v) for (t, v) in entrys if not v.get()]
        entrys.clear()
        entrys.extend(filtered)
        for text, var in entrys:
            chk = ttk.Checkbutton(list_frame, textvariable=text, variable=var)
            chk.pack(anchor="w")
        save_task()

    def import_tasks_from_code():
        if not os.path.exists(scan_config_path):
            ms.showwarning("Missing Config", "No .organizer_taskscan.json found.")
            return

        try:
            with open(scan_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            paths = config.get("paths", [])
        except Exception as e:
            ms.showerror("Error", f"Failed to read .organizer_taskscan.json:\n{e}")
            return

        patterns = [
            r"#\s*(TODO|BUG|FIX)\s*[:：]\s*(.+)",
            r"//\s*(TODO|BUG|FIX)\s*[:：]\s*(.+)"
        ]
        new_tasks = []

        for rel_path in paths:
            abs_path = os.path.join(project_path, rel_path)
            if os.path.isfile(abs_path):
                files_to_check = [abs_path]
            elif os.path.isdir(abs_path):
                files_to_check = []
                for root, _, files in os.walk(abs_path):
                    for file in files:
                        if file.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
                            files_to_check.append(os.path.join(root, file))
            else:
                continue

            for file_path in files_to_check:
                try:
                    rel_file_path = os.path.relpath(file_path, project_path).replace("\\", "/")
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            for pat in patterns:
                                match = re.search(pat, line.strip())
                                if match:
                                    task_text = match.group(2).strip()
                                    new_tasks.append({
                                        "text": task_text,
                                        "done": False,
                                        "source": "code",
                                        "file": rel_file_path
                                    })
                except:
                    continue

        count = 0
        for task in new_tasks:
            task_text = task["text"]
            if not any(task_text == t.get() for (t, _) in entrys):
                var = tk.BooleanVar()
                tvar = tk.StringVar(value=task_text)
                chk = ttk.Checkbutton(list_frame, textvariable=tvar, variable=var)
                chk.pack(anchor="w")
                entrys.append((tvar, var))
                tasks.append(task)
                count += 1

        if count:
            save_task()
            ms.showinfo("Tasks Imported", f"{count} tasks added from code.")
        else:
            ms.showinfo("No New Tasks", "No new TODO/BUG/FIX comments found.")

    load_task()

    new_task_entry = ttk.Entry(window)
    new_task_entry.pack(fill="x", padx=5, pady=5)

    ttk.Button(window, text="➕ Add Task", command=agree_task).pack(side="left", padx=5, pady=5)
    ttk.Button(window, text="🧹 Delete Completed", command=delete_complete_task).pack(side="left", padx=5, pady=5)
    ttk.Button(window, text="📂 Import tasks from code", command=import_tasks_from_code).pack(side="left", padx=5, pady=5)

# TODO: Mejorar las task y su UI    
def open_taskscan_config(project_path):
    config_file = os.path.join(project_path, ".organizer_taskscan.json")

    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {"paths": []}

    paths = config.get("paths", [])

    window = tk.Toplevel(orga)
    window.title("📂 Configure Task Scan Paths")
    window.geometry("500x420")
    window.iconbitmap(path)

    ttk.Label(window, text="🔍 Paths to scan for code tasks", font=("Segoe UI", 10, "bold")).pack(pady=10)

    listbox = tk.Listbox(window, selectmode="single", height=12)
    listbox.pack(fill="both", expand=True, padx=10, pady=5)

    for p in paths:
        listbox.insert("end", p)

    def save_config():
        new_paths = list(listbox.get(0, "end"))
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"paths": new_paths}, f, indent=4)
        make_file_hide(config_file)
        show_notification("Scan paths updated", type_="success")
        window.destroy()

    def add_path():
        selected = filedialog.askopenfilename(
            title="Select file or folder",
            initialdir=project_path
        )
        if not selected:
            return

        rel = os.path.relpath(selected, start=project_path).replace("\\", "/")
        if rel not in listbox.get(0, "end"):
            listbox.insert("end", rel)

    def add_folder():
        folder = filedialog.askdirectory(
            title="Select folder",
            initialdir=project_path
        )
        if not folder:
            return

        rel = os.path.relpath(folder, start=project_path).replace("\\", "/")
        if rel not in listbox.get(0, "end"):
            listbox.insert("end", rel)

    def delete_selected():
        selected = listbox.curselection()
        if selected:
            listbox.delete(selected[0])

    button_frame = ttk.Frame(window)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="📄 Add File", command=add_path, bootstyle="secondary").pack(side="left", padx=5)
    ttk.Button(button_frame, text="📁 Add Folder", command=add_folder, bootstyle="secondary").pack(side="left", padx=5)
    ttk.Button(button_frame, text="🗑 Delete", command=delete_selected, bootstyle="danger").pack(side="left", padx=5)
    ttk.Button(button_frame, text="💾 Save", command=save_config, bootstyle="success").pack(side="right", padx=5)

def show_dashboard_proyect(project_path):
    dashboard = tk.Toplevel(orga)
    dashboard.title("Project Summary")
    dashboard.iconbitmap(path)

    frame = ttk.Frame(dashboard)
    frame.pack(fill='both', expand=True, padx=10, pady=10)

    total_files = 0
    total_folders = 0
    total_size = 0
    total_tests = 0
    extensions = Counter()

    for folder, subdirs, files in os.walk(project_path):
        if "projects_versions" in folder:
            continue

        total_folders += len(subdirs)
        total_files += len(files)

        for file in files:
            file_path = os.path.join(folder, file)
            try:
                total_size += os.path.getsize(file_path)
            except:
                continue

            ext = os.path.splitext(file)[1].lower()
            extensions[ext] += 1

            if file.lower().startswith("test_") or file.endswith((".spec.js", ".spec.ts", ".test.js", ".test.ts")):
                total_tests += 1

    versions_folder = os.path.join("projects_versions")
    version_size = 0
    version_count = 0
    if os.path.exists(versions_folder):
        for foldername, _, filenames in os.walk(versions_folder):
            for f in filenames:
                try:
                    version_size += os.path.getsize(os.path.join(foldername, f))
                except:
                    continue
            version_count += 1

    task_path = os.path.join(project_path, ".organizer_tasks.json")
    pending_task = 0
    if os.path.exists(task_path):
        try:
            quit_attribute_only_read_hide(task_path)
            with open(task_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                pending_task = sum(1 for t in tasks if not t.get("done"))
        except:
            pass

    try:
        last_mod = max(
            os.path.getmtime(os.path.join(dp, f))
            for dp, dn, fn in os.walk(project_path)
            for f in fn
        )
        last_date = datetime.fromtimestamp(last_mod).strftime("%Y-%m-%d %H:%M:%S")
    except:
        last_date = "Not available"

    ttk.Label(frame, text="📊 General", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"📁 Folders: {total_folders}").pack(anchor="w")
    ttk.Label(frame, text=f"📄 Files: {total_files}").pack(anchor="w")
    ttk.Label(frame, text=f"📦 Size: {round(total_size / 1024, 2)} KB").pack(anchor="w")
    ttk.Label(frame, text=f"🕓 Last Modified: {last_date}").pack(anchor="w")

    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)

    ttk.Label(frame, text="🛠 Dev Info", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"🧪 Test files: {total_tests}").pack(anchor="w")
    ttk.Label(frame, text=f"📝 Pending Tasks: {pending_task}").pack(anchor="w")

    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)

    ttk.Label(frame, text="🧬 Versions", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"🧾 Saved versions: {version_count}").pack(anchor="w")
    ttk.Label(frame, text=f"💾 Version folder size: {round(version_size / 1024, 2)} KB").pack(anchor="w")

    if extensions:
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Label(frame, text="🧠 File Types / Languages", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        for ext, count in extensions.most_common(10):
            ttk.Label(frame, text=f"  • {ext or '[no extension]'}: {count}").pack(anchor="w")

def open_sandbox():
    sandbox = tk.Toplevel(orga)
    sandbox.title("Sandbox")
    sandbox.iconbitmap(path)
    
    entry = scrolledtext.ScrolledText(sandbox)
    entry.pack(side="left",fill='both', expand=True, padx=5, pady=5)
    
    output = scrolledtext.ScrolledText(sandbox)
    output.pack(side="right",fill='both', expand=True, padx=5, pady=5)
    
    def execute_code():
        code  = entry.get("1.0", "end-1c")
        buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(buffer):
                exec(code, {})
            output.delete("1.0", "end")
            output.insert("1.0", buffer.getvalue())
        except Exception as e:
            output.delete("1.0", "end")
            output.insert("1.0", f"Error: {str(e)}")
        
    btn_execute = ttk.Button(sandbox, text="Execute", command=execute_code)
    btn_execute.pack(side="bottom", fill="x", padx=5, pady=5)
    
def insert_project_tree_node(name, description, language, path, repo):
    tree.insert(
        "", "end", iid=path, text=name,
        values=("", description, language, path, repo)
    )
    tree.insert(path, "end", iid=f"{path}_dummy", text="(loading...)")

def load_project_structure_on_expand(event):
    item_id = tree.focus()

    try:
        values = tree.item(item_id, "values")
        if len(values) < 4:
            return
        project_path = values[3]
    except Exception as e:
        return

    if not os.path.isdir(project_path):
        return

    for child in tree.get_children(item_id):
        if "dummy" in child:
            tree.delete(child)

    try:
        for name in sorted(os.listdir(project_path)):
            sub_path = os.path.join(project_path, name)
            if not os.path.exists(sub_path):
                continue

            item_type = "folder" if os.path.isdir(sub_path) else "file"

            tree.insert(item_id, "end", iid=sub_path, text=name,
                        values=("", "", item_type, sub_path, ""))

            if os.path.isdir(sub_path):
                tree.insert(sub_path, "end", iid=f"{sub_path}_dummy", text="(loading...)")

    except Exception as e:
        ms.showerror("ERROR", f"Error loading content: {e}")

def open_link_panel(project_path):
    links_path = os.path.join(project_path, ".organizer_links.json")
    
    if not os.path.exists(links_path):
        with open(links_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        make_file_hide(links_path)
        
    with open(links_path, "r", encoding="utf-8") as f:
        links = json.load(f)
        
    win = tk.Toplevel(orga)
    win.title("Project Resources")
    win.iconbitmap(path)
    
    frame_links = ttk.Frame(win)
    frame_links.pack(fill="both", expand=True, padx=5, pady=5)
    
    listbox = tk.Listbox(frame_links)
    listbox.pack(fill="both", expand=True)
    
    for link in links:
        listbox.insert("end", f"{link['label']} -> {link['url']}")
        
    entry_label = ttk.Entry(win)
    entry_label.pack(fill="x", padx=5, pady=5)
    entry_label.insert(0, "Label")

    entry_url = ttk.Entry(win)
    entry_url.pack(fill="x", padx=5, pady=5)
    entry_url.insert(0, "https://")
    
    def save_links():
        quit_attribute_only_read_hide(links_path)
        with open(links_path, "w", encoding="utf-8") as f:
            json.dump(links, f, indent=4)
        make_file_hide(links_path)
        
    def add_link():
        label = entry_label.get().strip()
        url = entry_url.get().strip()
        if label and url:
            links.append({"label": label, "url": url})
            listbox.insert("end", f"{label} → {url}")
            save_links()
            entry_label.delete(0, "end")
            entry_url.delete(0, "end")
            
    def delete_link():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        del links[idx]
        listbox.delete(idx)
        save_links()
        
    def open_selected():
        sel = listbox.curselection()
        if not sel: return
        url = links[sel[0]]["url"]
        webbrowser.open(url)
        
    ttk.Button(win, text="Add Link", command=add_link).pack(pady=5)
    ttk.Button(win, text="Delete Selected", command=delete_link).pack(pady=5)
    ttk.Button(win, text="Open Selected", command=open_selected).pack(pady=5)

def restore_version_from_sidebar(project_path, version_name):
    project_name = os.path.basename(project_path)
    origin_path = os.path.join("projects_versions", project_name, version_name)

    if not os.path.exists(origin_path):
        ms.showerror("Restore Error", f"Version not found:\n{origin_path}")
        return

    confirm = ms.askyesno(
        "Confirm Restore",
        f"Do you want to restore version '{version_name}'?\nThis will overwrite the current project:\n{project_path}"
    )
    if not confirm:
        return

    try:
        for item in os.listdir(project_path):
            if item == "projects_versions":
                continue
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        for item in os.listdir(origin_path):
            src = os.path.join(origin_path, item)
            dst = os.path.join(project_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        show_notification(f"Restored version: {version_name}", type_="success")
        orga.after(500, mostrar_proyectos)
    except Exception as e:
        ms.showerror("Restore Error", f"Failed to restore:\n{e}")

def calcular_resumen_proyecto(project_path):
    resumen = {
        "folders": 0,
        "files": 0,
        "size": 0,
        "tests": 0,
        "tasks": 0,
        "exts": Counter(),
        "resources": [],
        "tasks_list": []
    }

    for folder, subdirs, files in os.walk(project_path):
        if "projects_versions" in folder:
            continue
        resumen["folders"] += len(subdirs)
        resumen["files"] += len(files)
        for file in files:
            file_path = os.path.join(folder, file)
            try:
                resumen["size"] += os.path.getsize(file_path)
            except:
                continue
            ext = os.path.splitext(file)[1].lower()
            resumen["exts"][ext] += 1
            if file.startswith("test_") or file.endswith((".spec.js", ".test.js", ".test.py", ".spec.ts", ".test.ts")):
                resumen["tests"] += 1

    task_path = os.path.join(project_path, ".organizer_tasks.json")
    if os.path.exists(task_path):
        try:
            quit_attribute_only_read_hide(task_path)
            with open(task_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                resumen["tasks"] = sum(1 for t in tasks if not t.get("done"))
                resumen["tasks_list"] = tasks
        except:
            pass

    links_path = os.path.join(project_path, ".organizer_links.json")
    if os.path.exists(links_path):
        try:
            with open(links_path, "r", encoding="utf-8") as f:
                resumen["resources"] = json.load(f)
        except:
            pass

    return resumen

def cargar_sidebar_config(project_path):
    config_path = os.path.join(project_path, ".organizer_sidebar_config.json")
    default_config = {
        "Languages": True,
        "Dependencies": True,
        "Git": True,
        "Tasks": True,
        "Links": True,
        "Versions": True,
        "Board": True
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            return {**default_config, **user_config}
        except Exception:
            return default_config
    return default_config

def guardar_sidebar_config(project_path, config):
    config_path = os.path.join(project_path, ".organizer_sidebar_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def open_sidebar_section_config_ui(project_path, current_config, refresh_callback=None):
    win = tk.Toplevel()
    win.title("Sidebar Configuration")
    win.geometry("300x300")
    win.iconbitmap(path)
    win.resizable(False, False)

    new_config = current_config.copy()
    vars = {}

    def save_and_close():
        for k, var in vars.items():
            new_config[k] = var.get()
        guardar_sidebar_config(project_path, new_config)
        if refresh_callback:
            refresh_callback()
        win.destroy()

    for section, enabled in current_config.items():
        var = tk.BooleanVar(value=enabled)
        chk = ttk.Checkbutton(win, text=section, variable=var)
        chk.pack(anchor="w", padx=10, pady=5)
        vars[section] = var

    ttk.Button(win, text="💾 Save", command=save_and_close).pack(pady=10)

def renderizar_sidebar(project_path, resumen, container=None):
    if container is None:
        container = sidebar
    
    sidebar_config = cargar_sidebar_config(project_path)
    
    for widget in sidebar.winfo_children():
        widget.destroy()
        
    if container == sidebar:
        top_controls = ttk.Frame(container)
        top_controls.pack(fill="x", padx=6, pady=(6, 0))

        lbl_popout = ttk.Label(
            top_controls,
            text="↗️",
            cursor="hand2",
            bootstyle='info'
        )
        lbl_popout.pack(side="right", padx=(4, 0))
        lbl_popout.bind("<Button-1>", lambda e: open_sidebar_floating(project_path, resumen))
        ToolTip(lbl_popout, text="Open in floating window")

        config_icon = ttk.Label(top_controls, text="⚙️", cursor="hand2")
        config_icon.pack(side="right", padx=(0, 4))
        config_icon.bind(
            "<Button-1>",
            lambda e: open_sidebar_section_config_ui(
                project_path,
                cargar_sidebar_config(project_path),
                lambda: renderizar_sidebar(project_path, resumen, container)
            )
        )
        ToolTip(config_icon, text="Customize sidebar sections")
        
    def create_section(title, emoji="📁"):
        section = CollapsibleSection(container, f"{emoji} {title}", bootstyle="info")
        section.pack(fill="x", padx=6, pady=6)
        return section.content_frame

    def guardar_tasks():
        task_path = os.path.join(project_path, ".organizer_tasks.json")
        with open(task_path, "w", encoding="utf-8") as f:
            json.dump(resumen["tasks_list"], f, indent=2)

    def guardar_links():
        link_path = os.path.join(project_path, ".organizer_links.json")
        with open(link_path, "w", encoding="utf-8") as f:
            json.dump(resumen["resources"], f, indent=2)
    
    # -- LANGUAGE BREAKDOWN SECTION --
    if sidebar_config.get("Languages", True):
        lang_frame = create_section("Languages", "🧪")

        EXT_TO_LANG = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".sh": "Shell",
            ".php": "PHP",
            ".dart": "Dart",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".rb": "Ruby",
            ".lua": "Lua",
        }

        LANG_COLORS = {
            "Python": "#3572A5",
            "JavaScript": "#f1e05a",
            "TypeScript": "#2b7489",
            "Java": "#b07219",
            "C": "#555555",
            "C++": "#f34b7d",
            "C/C++": "#6e4c13",
            "C#": "#178600",
            "Go": "#00ADD8",
            "Rust": "#dea584",
            "HTML": "#e34c26",
            "CSS": "#563d7c",
            "JSON": "#292929",
            "Shell": "#89e051",
            "PHP": "#4F5D95",
            "Dart": "#00B4AB",
            "Kotlin": "#F18E33",
            "Swift": "#ffac45",
            "Ruby": "#701516",
            "Lua": "#000080"
        }

        lang_counter = {}

        for ext, count in resumen["exts"].items():
            if count <= 0:
                continue
            lang = EXT_TO_LANG.get(ext)
            if lang:
                lang_counter[lang] = lang_counter.get(lang, 0) + count

        if not lang_counter:
            ttk.Label(lang_frame, text="No code files detected", foreground="gray").pack(anchor="w", padx=10)
        else:
            total = sum(lang_counter.values())
            sorted_langs = sorted(lang_counter.items(), key=lambda x: x[1], reverse=True)

            for lang, count in sorted_langs:
                percent = round((count / total) * 100)
                if percent == 0:
                    continue

                row = ttk.Frame(lang_frame)
                row.pack(anchor="w", padx=10, pady=2, fill="x")

                color = LANG_COLORS.get(lang, "#888888")
                canvas = tk.Canvas(row, width=10, height=10, highlightthickness=0)
                canvas.create_oval(2, 2, 9, 9, fill=color, outline=color)
                canvas.pack(side="left", padx=(0, 6))

                label = ttk.Label(row, text=f"{lang} ({percent}%)", font=("Segoe UI", 9))
                label.pack(side="left", anchor="w")

                ToolTip(label, text=f"{count} file(s)")

    # -- DEPENDENCIES SECTION --
    if sidebar_config.get("Dependencies", True):
        deps_frame = create_section("Dependencies", "📦")
        
        def parse_dependencies():
            deps = []
            
            req_path = os.path.join(project_path, "requirements.txt")
            if os.path.exists(req_path):
                try:
                    with open(req_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                deps.append(line)
                except Exception as e:
                    deps.append(f"[ERROR reading requirements.txt: {e}]")
                    
            # Python - pyproject.toml
            pyproject_path = os.path.join(project_path, "pyproject.toml")
            if os.path.exists(pyproject_path):
                try:
                    import tomllib  # Python 3.11+
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)
                        requires = data.get("project", {}).get("dependencies", [])
                        deps.extend(requires)
                except Exception:
                    pass

            # JavaScript - package.json
            package_json = os.path.join(project_path, "package.json")
            if os.path.exists(package_json):
                try:
                    with open(package_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for section in ("dependencies", "devDependencies"):
                            for name, ver in data.get(section, {}).items():
                                deps.append(f"{name} {ver}")
                except Exception:
                    pass

            # Rust - Cargo.toml
            cargo_toml = os.path.join(project_path, "Cargo.toml")
            if os.path.exists(cargo_toml):
                try:
                    with open(cargo_toml, "r", encoding="utf-8") as f:
                        for line in f:
                            if "=" in line and "[" not in line and "version" not in line:
                                deps.append(line.strip())
                except Exception:
                    pass

            # Go - go.mod
            go_mod = os.path.join(project_path, "go.mod")
            if os.path.exists(go_mod):
                try:
                    with open(go_mod, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("require"):
                                deps.append(line.replace("require", "").strip())
                except Exception:
                    pass

            return deps


        dependencies = parse_dependencies()
        if not dependencies:
            ttk.Label(deps_frame, text="No dependencies found", foreground="gray").pack(anchor="w", padx=10, pady=5)
        else:
            for dep in dependencies[:25]:  # Limit display
                lbl = ttk.Label(deps_frame, text=f"📄 {dep}", font=("Segoe UI", 9))
                lbl.pack(anchor="w", padx=10, pady=1)
    
    # -- GIT SECTION --
    if sidebar_config.get("Git", True):
        try:
            repo = Repo(project_path)
            if not repo.bare:
                git_frame = create_section("Git Status", "🌿")
                
                branch = repo.active_branch.name
                ttk.Label(git_frame, text=f"🌿 Branch: {branch}").pack(anchor="w", padx=5, pady=5)
                
                changed = [item.a_path for item in repo.index.diff(None)]
                if changed:
                    ttk.Label(git_frame, text=f"✏️ Modified: {len(changed)}").pack(anchor="w", padx=5)
                    for file in changed[:3]:
                        ttk.Label(git_frame, text=f"• {file}", font=("Segoe UI", 8)).pack(anchor="w", padx=5)
                        
                
                untracked = repo.untracked_files
                if untracked:
                    ttk.Label(git_frame, text=f"📦 Untracked: {len(untracked)}").pack(anchor="w", padx=5)
                    for file in untracked[:3]:
                        ttk.Label(git_frame, text=f"• {file}", font=("Segoe UI", 8)).pack(anchor="w", padx=5)
                        
                
                try:
                    last_commit = next(repo.iter_commits())
                    date = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_commit.committed_date))
                    msg = last_commit.message.strip().split("\n")[0][:60]
                    ttk.Label(git_frame, text=f"🕓 Last commit: {date}").pack(anchor="w", padx=5, pady=2)
                    ttk.Label(git_frame, text=f"• {msg}", font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=5)
                except:
                    pass
        except (InvalidGitRepositoryError, GitCommandError):
            pass
    
    # -- TASKS SECTION --
    if sidebar_config.get("Tasks", True):
        tasks_frame = create_section("Tasks", "✅")

        def guardar_tasks():
            try:
                task_path = os.path.join(project_path, ".organizer_tasks.json")
                with open(task_path, "w", encoding="utf-8") as f:
                    json.dump(resumen["tasks_list"], f, indent=4)
                show_notification("Tasks updated", type_="success")
            except Exception as e:
                ms.showerror("Error", f"Failed to save tasks:\n{e}")

        def toggle_task(idx, var):
            resumen["tasks_list"][idx]["done"] = var.get()
            guardar_tasks()
            update_sidebar_project()

        def delete_task(idx):
            del resumen["tasks_list"][idx]
            guardar_tasks()
            update_sidebar_project()

        def auto_import_code_tasks():
            import re
            config_path = os.path.join(project_path, ".organizer_taskscan.json")
            if not os.path.exists(config_path):
                return

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                paths = config.get("paths", [])
            except:
                return

            patterns = [
                r"#\s*(TODO|BUG|FIX)\s*[:：]\s*(.+)",
                r"//\s*(TODO|BUG|FIX)\s*[:：]\s*(.+)"
            ]
            existing_texts = {t["text"] for t in resumen["tasks_list"]}

            for rel_path in paths:
                abs_path = os.path.join(project_path, rel_path)
                if os.path.isfile(abs_path):
                    files = [abs_path]
                elif os.path.isdir(abs_path):
                    files = []
                    for root, _, filenames in os.walk(abs_path):
                        for fname in filenames:
                            if fname.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
                                files.append(os.path.join(root, fname))
                else:
                    continue

                for fpath in files:
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            for line in f:
                                for pat in patterns:
                                    match = re.search(pat, line.strip())
                                    if match:
                                        txt = match.group(2).strip()
                                        if txt not in existing_texts:
                                            resumen["tasks_list"].append({
                                                "text": txt,
                                                "done": False,
                                                "source": "code",
                                                "file": os.path.relpath(fpath, project_path).replace("\\", "/")
                                            })
                                            existing_texts.add(txt)
                    except:
                        continue

            guardar_tasks()

        auto_import_code_tasks()
        
        config_btn = ttk.Label(tasks_frame, text="⚙️", cursor="hand2")
        config_btn.pack(anchor="e", padx=6, pady=(0, 4))
        config_btn.bind("<Button-1>", lambda e: open_taskscan_config(project_path))
        ToolTip(config_btn, text="Edit scanned files/folders")

        for i, task in enumerate(resumen["tasks_list"]):
            row = ttk.Frame(tasks_frame)
            row.pack(fill="x", padx=5, pady=1)

            var = tk.BooleanVar(value=task["done"])
            is_code_task = task.get("source") == "code"
            display_text = f"🧩 {task['text']}" if is_code_task else task["text"]

            cb = ttk.Checkbutton(
                row, text=display_text, variable=var,
                command=lambda idx=i, v=var: toggle_task(idx, v)
            )
            cb.pack(side="left", expand=True, anchor="w")

            if is_code_task and task.get("file"):
                ToolTip(cb, text=f"{task['file']}")

            icon = ttk.Label(row, text="🗑", cursor="hand2", foreground="red")
            icon.pack(side="right", padx=4)
            icon.bind("<Button-1>", lambda e, idx=i: delete_task(idx))
            ToolTip(icon, text="Delete")

        def add_task():
            new = simpledialog.askstring("➕ New Task", "Enter task:")
            if new:
                resumen["tasks_list"].append({
                    "text": new,
                    "done": False,
                    "source": "manual"
                })
                guardar_tasks()
                update_sidebar_project()

        ttk.Button(tasks_frame, text="➕ Add Task", command=add_task, bootstyle="secondary").pack(fill="x", padx=5, pady=5)
        ttk.Button(tasks_frame, text="✏️ Edit Tasks", command=lambda: open_tasks_projects(project_path), bootstyle="outline").pack(fill="x", padx=5, pady=2)

    # -- LINKS SECTION --
    if sidebar_config.get("Links", True):
        links_frame = create_section("Resources", "🔗")

        def delete_link(i):
            del resumen["resources"][i]
            guardar_links()
            update_sidebar_project()

        for i, link in enumerate(resumen["resources"]):
            row = ttk.Frame(links_frame)
            row.pack(fill="x", padx=5, pady=2)
            lbl = ttk.Label(row, text=f"🌐 {link['label']}", foreground="blue", cursor="hand2")
            lbl.pack(side="left", expand=True, anchor="w")
            lbl.bind("<Button-1>", lambda e, url=link["url"]: webbrowser.open(url))
            ToolTip(lbl, text=link["url"])

            icon = ttk.Label(row, text="🗑", cursor="hand2", foreground="red")
            icon.pack(side="right", padx=4)
            icon.bind("<Button-1>", lambda e, i=i: delete_link(i))
            ToolTip(icon, text="Delete")

        def add_link():
            label = simpledialog.askstring("Label", "Enter label:")
            url = simpledialog.askstring("URL", "Enter URL:")
            if label and url:
                resumen["resources"].append({"label": label, "url": url})
                guardar_links()
                update_sidebar_project()

        ttk.Button(links_frame, text="➕ Add Link", command=add_link, bootstyle="secondary").pack(fill="x", padx=5, pady=5)
        ttk.Button(links_frame, text="🔧 Edit Links", command=lambda: open_link_panel(project_path), bootstyle="outline").pack(fill="x", padx=5, pady=2)

    # -- VERSIONS SECTION --
    if sidebar_config.get("Versions", True):
        versions_metadata = os.path.join("projects_versions", os.path.basename(project_path), "versions.json")
        if os.path.exists(versions_metadata):
            try:
                with open(versions_metadata, "r", encoding="utf-8") as f:
                    versions = json.load(f)
            except Exception as e:
                versions = []
                show_notification(f"Error loading versions: {e}", type_="error")

            if versions:
                versions_frame = create_section("Versions", "🕓")
                for v in versions[-3:][::-1]:
                    label = f"{v['name']} ({v['date']})"
                    btn = ttk.Button(
                        versions_frame,
                        text=label,
                        bootstyle="link",
                        command=lambda vn=v["name"]: restore_version_from_sidebar(project_path, vn)
                    )
                    btn.pack(anchor="w", padx=10, pady=2)
                ttk.Button(versions_frame, text="🗂 View All", command=lambda: show_versions_historial(project_path), bootstyle="outline").pack(fill="x", padx=5, pady=5)
            
    # -- BOARD SECTION --
    if sidebar_config.get("Board", True):
        priority_fg_colors = {
            "high": "#e74c3c",
            "medium": "#f39c12",
            "low": "#27ae60"
        }
        
        board_section = create_section("Board", "🗂")

        board_path = os.path.join(project_path, ".organizer_board.json")
        if os.path.exists(board_path):
            try:
                with open(board_path, "r", encoding="utf-8") as f:
                    board_data = json.load(f)
            except:
                board_data = {}
        else:
            board_data = {}

        for col in ["To Do", "In Progress", "Done"]:
            ttk.Label(board_section, text=f"📌 {col}", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=5, pady=(4, 1))
            for card in board_data.get(col, [])[:2]:
                emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(card.get("priority", "medium"), "⚪")
                fg_color = priority_fg_colors.get(card.get("priority", "medium"), "#555")
                label = ttk.Label(
                    board_section,
                    text=f"{emoji} {card['text']}",
                    wraplength=240,
                    font=("Segoe UI", 8),
                    foreground=fg_color,
                )
                label.pack(anchor="w", padx=12, pady=1)

        ttk.Button(
            board_section,
            text="📝 Open Board",
            command=lambda: open_trello_board(project_path),
            bootstyle="outline-info"
        ).pack(fill="x", padx=6, pady=6)
    
def open_sidebar_floating(project_path, resumen):
    global float_win
    
    if float_win and float_win.winfo_exists():
        float_win.lift()
        return
    
    sidebar.grid_remove()
    
    float_win = tk.Toplevel(orga)
    float_win.title("Organizer - Sidebar")
    float_win.iconbitmap(path)
    float_win.transient(orga)
    float_win.protocol("WM_DELETE_WINDOW", lambda: close_sidebar_popout())
    
    float_sidebar = ttk.Frame(float_win)
    float_sidebar.pack(fill='both', expand=True)
    
    renderizar_sidebar(project_path, resumen, container=float_sidebar)
    
def close_sidebar_popout():
    global float_win
    
    float_win.destroy()
    float_win = None
    
    sidebar.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

def update_sidebar_project(event=None):
    sidebar.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

    selection = tree.selection()
    if not selection:
        return

    item_id = selection[0]
    values = tree.item(item_id, "values")
    if len(values) < 4:
        return

    project_path = values[3]

    def cargar_sidebar_en_hilo():
        resumen = calcular_resumen_proyecto(project_path)
        orga.after(0, lambda: renderizar_sidebar(project_path, resumen))

    threading.Thread(target=cargar_sidebar_en_hilo, daemon=True).start()

def open_trello_board(project_path):
    window = tk.Toplevel(orga)
    window.title("🗂 Trello-style Board")
    window.geometry("1100x650")
    window.iconbitmap(path)
    window.minsize(900, 600)

    board_file = os.path.join(project_path, ".organizer_board.json")

    if os.path.exists(board_file):
        with open(board_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "To Do": [],
            "In Progress": [],
            "Done": []
        }

    columns = list(data.keys())
    cards = data
    column_frames = {}
    collapsed_columns = set()

    priority_colors = {
        "high": "#e74c3c",
        "medium": "#f39c12",
        "low": "#27ae60"
    }

    priority_emojis = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }

    search_var = tk.StringVar()
    search_frame = ttk.Frame(window)
    search_frame.pack(fill="x", padx=10, pady=(8, 0))
    ttk.Label(search_frame, text="🔍 Search:", font=("Segoe UI", 9, "bold")).pack(side="left")
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5)
    ttk.Button(search_frame, text="🔃 Refresh", command=lambda: render_board(), bootstyle="secondary").pack(side="right")

    board_frame = ttk.Frame(window)
    board_frame.pack(fill="both", expand=True, padx=10, pady=10)

    drag_data = {"text": "", "source": ""}

    def save_board():
        with open(board_file, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2)
        update_sidebar_project()

    def ask_card_details(existing=None):
        top = tk.Toplevel(window)
        top.title("📝 Card Details")
        top.geometry("300x160")
        top.grab_set()

        ttk.Label(top, text="Card Text:", font=("Segoe UI", 10)).pack(pady=(10, 2))
        entry = ttk.Entry(top, width=35)
        entry.insert(0, existing["text"] if existing else "")
        entry.pack(pady=5)

        ttk.Label(top, text="Priority:", font=("Segoe UI", 10)).pack(pady=(10, 2))
        priority_var = tk.StringVar(value=existing["priority"] if existing else "medium")
        combo = ttk.Combobox(top, textvariable=priority_var, values=["low", "medium", "high"], state="readonly")
        combo.pack()

        result = {}

        def submit():
            text = entry.get().strip()
            if not text:
                ms.showwarning("Empty", "Card text cannot be empty")
                return
            result["text"] = text
            result["priority"] = priority_var.get()
            top.destroy()

        ttk.Button(top, text="Save", command=submit).pack(pady=10)
        top.wait_window()
        return result if result else None

    def render_board():
        query = search_var.get().strip().lower()
        for col in columns:
            frame = column_frames[col]

            for widget in frame.card_container.winfo_children():
                widget.destroy()

            if col in collapsed_columns:
                frame.card_container.pack_forget()
                frame.counter_label.config(text="(collapsed)")
            else:
                if not frame.card_container.winfo_ismapped():
                    frame.card_container.pack(fill="both", expand=True, pady=(0,5))
                    frame.card_container.lift(frame.action_frame)

                frame.counter_label.config(text=f"Cards: {len(cards[col])}")

                filtered = [c for c in cards[col] if query in c["text"].lower()] if query else cards[col]

                for i, card in enumerate(filtered):
                    text, priority = card["text"], card.get("priority", "medium")
                    emoji = priority_emojis.get(priority, "")
                    color = priority_colors.get(priority, "#000")

                    row = ttk.Frame(frame.card_container)
                    row.pack(fill="x", padx=3, pady=3)

                    label = ttk.Label(
                        row,
                        text=f"{emoji} {text}",
                        foreground=color,
                        anchor="w",
                        font=("Segoe UI", 9),
                        wraplength=240,
                        cursor="hand2"
                    )
                    label.pack(side="left", fill="x", expand=True)
                    label.bind("<Double-Button-1>", lambda e, c=card, col=col: edit_card(col, c))
                    label.bind("<ButtonPress-1>", lambda e, text=text, src=col: start_drag(e, text, src))

                    ToolTip(label, text=f"Priority: {priority.capitalize()}")

                    delete = ttk.Label(row, text="🗑", foreground="red", cursor="hand2")
                    delete.pack(side="right", padx=5)
                    delete.bind("<Button-1>", lambda e, i=i, col=col: delete_card(col, i))

    def delete_card(col, idx):
        del cards[col][idx]
        render_board()
        save_board()

    def clear_column(col):
        if ms.askyesno("Clear Column", f"Delete ALL cards in '{col}'?"):
            cards[col].clear()
            render_board()
            save_board()

    def edit_card(col, card):
        updated = ask_card_details(existing=card)
        if updated:
            card.update(updated)
            render_board()
            save_board()

    def start_drag(event, text, source_col):
        drag_data["text"] = text
        drag_data["source"] = source_col
        window.bind("<B1-Motion>", dragging)
        window.bind("<ButtonRelease-1>", drop_card)

    def dragging(event): pass

    def drop_card(event):
        x, y = event.x_root, event.y_root
        for col in columns:
            frame = column_frames[col]
            if frame.winfo_rootx() < x < frame.winfo_rootx() + frame.winfo_width() and \
               frame.winfo_rooty() < y < frame.winfo_rooty() + frame.winfo_height():
                move_card(drag_data["text"], drag_data["source"], col)
                break
        window.unbind("<B1-Motion>")
        window.unbind("<ButtonRelease-1>")
        drag_data["text"] = ""
        drag_data["source"] = ""

    def move_card(text, from_col, to_col):
        if from_col == to_col:
            return
        found = None
        for card in cards[from_col]:
            if card["text"] == text:
                found = card
                break
        if found:
            cards[from_col].remove(found)
            cards[to_col].append(found)
            render_board()
            save_board()

    for col in columns:
        col_frame = ttk.Frame(board_frame, relief="ridge", borderwidth=2)
        col_frame.pack(side="left", fill="both", expand=True, padx=6, pady=5)
        column_frames[col] = col_frame

        title_frame = ttk.Frame(col_frame)
        title_frame.pack(fill="x", pady=(5, 0))

        col_label = ttk.Label(title_frame, text=f"{col}", font=("Segoe UI", 10, "bold"))
        col_label.pack(side="left", padx=5)

        counter_label = ttk.Label(title_frame, text="", font=("Segoe UI", 9, "italic"))
        counter_label.pack(side="right", padx=5)
        col_frame.counter_label = counter_label

        card_container = ttk.Frame(col_frame)
        card_container.pack(fill="both", expand=True, pady=(0,5))
        col_frame.card_container = card_container

        action_frame = ttk.Frame(col_frame)
        action_frame.pack(pady=5, fill="x")
        col_frame.action_frame = action_frame

        ttk.Button(action_frame, text="➕ Add", command=lambda c=col: add_card(c), bootstyle="success").pack(side="left", padx=3)
        ttk.Button(action_frame, text="🪑 Clear", command=lambda c=col: clear_column(c), bootstyle="danger").pack(side="right", padx=3)

    def add_card(col):
        result = ask_card_details()
        if result:
            cards[col].append(result)
            render_board()
            save_board()

    search_var.trace_add("write", lambda *_: render_board())
    render_board()

def show_project_hierarchy_map(project_path):
    window = tk.Toplevel(orga)
    window.title("Project Structure Map")
    window.geometry("1000x650")
    window.transient() 
    window.iconbitmap(path)

    topbar = ttk.Frame(window)
    topbar.pack(fill="x", padx=10, pady=5)

    ttk.Label(topbar, text="🔍 Search:").pack(side="left")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(topbar, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5)

    main_frame = ttk.Frame(window)
    main_frame.pack(fill="both", expand=True)

    left_frame = ttk.Frame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    canvas = tk.Canvas(left_frame, bg="white", highlightthickness=0)
    vsb = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    content_frame = ttk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

    preview_frame = ttk.Frame(main_frame, width=350)
    preview_frame.pack(side="right", fill="both", expand=False)
    ttk.Label(preview_frame, text="📄 File Preview", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=5)

    preview_code = CodeView(preview_frame, wrap="none", font=("Consolas", 10))
    preview_code.pack(fill="both", expand=True, padx=5, pady=5)

    code_languages = {
        ".py": "python", ".js": "javascript", ".html": "html", ".css": "css", ".json": "json",
        ".java": "java", ".c": "c", ".cpp": "cpp", ".sh": "bash", ".xml": "xml", ".yml": "yaml",
        ".md": "markdown", ".rb": "ruby", ".php": "php", ".ts": "typescript"
    }

    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    content_frame.bind("<Configure>", update_scroll_region)

    label_font = ("Segoe UI", 9)
    box_height = 22
    spacing = 6
    indent = 25
    expanded_dirs = set()
    search_lock = threading.Lock()
    search_thread = None

    icon_map = {
        ".py": "🐍", ".js": "🟨", ".html": "🌐", ".css": "🎨", ".json": "🗂",
        ".txt": "📄", ".md": "📘", ".exe": "🧱", ".png": "🖼", ".jpg": "📷",
        ".java": "☕", ".c": "🔧", ".cpp": "➕", ".sh": "🐚", ".bat": "⚙️",
        ".csv": "📊", ".xml": "📰"
    }

    color_map = {
        ".py": "#3572A5", ".js": "#f1e05a", ".html": "#e34c26", ".css": "#563d7c", ".json": "#cbcb41",
        ".txt": "#555", ".md": "#083fa1", ".exe": "#999", ".png": "#679", ".jpg": "#756", ".jpeg": "#756",
        ".java": "#b07219", ".c": "#555555", ".cpp": "#f34b7d", ".sh": "#89e051", ".bat": "#8f8f8f",
        ".csv": "#22863a", ".xml": "#006", ".yml": "#cb1717"
    }

    def get_icon_color(path, is_dir):
        if is_dir:
            return "📂" if path in expanded_dirs else "📁", "#1976d2"
        ext = os.path.splitext(path)[1].lower()
        return icon_map.get(ext, "📄"), color_map.get(ext, "#bbbbbb")

    def draw_tree(path, x, y, depth=0, max_depth=30):
        if depth > max_depth or os.path.islink(path):
            return y

        skip_dirs = {".git", "__pycache__", "venv", "node_modules", "env"}
        is_dir = os.path.isdir(path)
        name = os.path.basename(path)

        if name in skip_dirs:
            return y

        arrow_expanded = "▼"
        arrow_collapsed = "▶"

        arrow = ""
        if is_dir:
            arrow = arrow_expanded if path in expanded_dirs else arrow_collapsed
        else:
            arrow = " "

        emoji, base_color = get_icon_color(path, is_dir)
        search = search_var.get().lower()
        match = search in name.lower() if search else False

        file_count = ""
        if is_dir:
            try:
                contents = os.listdir(path)
                file_count = f" ({len(contents)})"
            except:
                contents = []
                file_count = ""
        else:
            contents = []

        display_name = f"{arrow} {emoji} {name}{file_count}"
        node_color = "#d63384" if match else base_color
        font_style = ("Segoe UI", 9, "underline bold") if match else label_font

        node_id = canvas.create_text(x, y, anchor="nw", text=display_name, font=font_style, fill=node_color, tags=("node", path))

        def on_enter(e):
            canvas.itemconfig(node_id, fill="#007acc")
        def on_leave(e):
            canvas.itemconfig(node_id, fill=node_color)

        canvas.tag_bind(node_id, "<Enter>", on_enter)
        canvas.tag_bind(node_id, "<Leave>", on_leave)

        def toggle(event, current=path):
            if is_dir:
                if current in expanded_dirs:
                    expanded_dirs.remove(current)
                else:
                    expanded_dirs.add(current)
                rebuild_tree()
            else:
                show_preview(current)

        canvas.tag_bind(node_id, "<Button-1>", toggle)

        next_y = y + box_height + spacing

        if is_dir and path in expanded_dirs:
            for item in sorted(contents):
                child = os.path.join(path, item)
                if os.path.exists(child):
                    next_y = draw_tree(child, x + indent, next_y, depth + 1, max_depth)

        return next_y
    
    def expand_matching_dirs(path, search_text, max_depth=30, depth=0):
        if depth > max_depth or os.path.islink(path):
            return False

        is_dir = os.path.isdir(path)
        name = os.path.basename(path)
        skip_dirs = {".git", "__pycache__", "venv", "node_modules", "env"}

        if name in skip_dirs:
            return False

        match_found = search_text in name.lower()

        if is_dir:
            try:
                children = os.listdir(path)
            except:
                children = []

            child_matches = False
            for child in children:
                child_path = os.path.join(path, child)
                if expand_matching_dirs(child_path, search_text, max_depth, depth + 1):
                    child_matches = True

            if child_matches or match_found:
                expanded_dirs.add(path)
                return True
            else:
                if path in expanded_dirs:
                    expanded_dirs.remove(path)
                return False
        else:
            return match_found

    def rebuild_tree():
        canvas.delete("all")
        draw_tree(project_path, 10, 10)

    def do_search_and_expand(search_text):
        with search_lock:
            expanded_dirs.clear()
            if search_text:
                expand_matching_dirs(project_path, search_text)
            orga.after(0, rebuild_tree)

    def rebuild_tree_async():
        nonlocal search_thread
        search_text = search_var.get().lower().strip()

        if search_thread and search_thread.is_alive():
            pass

        else:
            search_thread = threading.Thread(target=do_search_and_expand, args=(search_text,), daemon=True)
            search_thread.start()

    def show_preview(file_path):
        preview_code.configure(state="normal")
        preview_code.delete("1.0", "end")

        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".exe", ".png", ".jpg", ".jpeg", ".ico", ".dll"]:
            preview_code.insert("1.0", f"[Binary or unsupported file: {ext}]")
            preview_code.configure(state="disabled")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(20000)

            lang = pygments.lexers.get_lexer_for_filename(file_path)
            preview_code.configure(lexer=lang)
            preview_code.insert("1.0", content)
        except Exception as e:
            preview_code.insert("1.0", f"[Error reading file: {e}]")
            preview_code.configure(lexer=None)

        preview_code.configure(state="disabled")

    search_entry.bind("<KeyRelease>", lambda e: rebuild_tree_async())
    rebuild_tree()


path = resource_path("software.ico")
path2 = resource_path2("software.png")

def show_splash(duration=3000):
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    splash.configure(bg="#222")
    
    width, height = 450, 300
    x = (splash.winfo_screenwidth() - width) // 2
    y = (splash.winfo_screenheight() - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")

    try:
        logo_img = Image.open(path2)
        logo_img = logo_img.resize((100, 100))
        logo_photo = ImageTk.PhotoImage(logo_img)

        img_label = ttk.Label(splash, image=logo_photo)
        img_label.image = logo_photo
        img_label.pack(pady=(30, 10))
    except Exception as e:
        ms.showerror("ERROR", f"Error logo loading: {e}")

    ttk.Label(splash, text="Organizer", font=("Segoe UI", 16, "bold")).pack()
    
    ttk.Label(splash, text=f"{main_version}", font=("Segoe UI", 16, "bold")).pack()
    
    style = ttk.Style()
    style.configure("Custom.Horizontal.TProgressbar", troughcolor="#333", background="#27ae60", thickness=12, borderwidth=0)
    
    progress = ttk.Progressbar(splash, mode="determinate", length=240, style="Custom.Horizontal.TProgressbar", maximum=100)
    progress.pack(pady=20)
    
    messages = [
        "Loading modules...",
        "Initializing plugins...",
        "Scanning projects...",
        "Syncing configuration...",
        "Preparing UI...",
        "Starting Organizer..."
    ]
    
    loading_label = ttk.Label(splash, text=messages[0], background="#222", foreground="#aaa", font=("Segoe UI", 9))
    loading_label.pack()

    step_delay = 50
    steps = duration // step_delay
    increment = 100 / steps
    message_interval = 600
    msg_index = 0
    
    def rotate_message():
        nonlocal msg_index
        msg_index = (msg_index + 1) % len(messages)
        loading_label.config(text=messages[msg_index])
        if splash.winfo_exists():
            splash.after(message_interval, rotate_message)

    def update_progress(i=0):
        if i <= steps:
            progress["value"] = i * increment
            splash.after(step_delay, lambda: update_progress(i + 1))
        else:
            splash.destroy()
            orga.deiconify()

    def close_splash():
        splash.destroy()
        orga.deiconify()

    update_progress()
    splash.after(message_interval, rotate_message)
    splash.after(duration, close_splash)

def run_cli_commands():
    parser = argparse.ArgumentParser(description="Organizer CLI")
    subparsers = parser.add_subparsers(dest="command")

    # list-projects
    subparsers.add_parser("list-projects", help="List all projects")

    # add-project
    add_project = subparsers.add_parser("add-project", help="Add a new project")
    add_project.add_argument("name")
    add_project.add_argument("path")
    add_project.add_argument("--desc", default="")
    add_project.add_argument("--lang", default="")
    add_project.add_argument("--repo", default="")

    # open-project
    open_proj = subparsers.add_parser("open-project", help="Open a project by name")
    open_proj.add_argument("name")

    # version
    subparsers.add_parser("version", help="Show Organizer version")

    # task group
    task = subparsers.add_parser("task", help="Task-related commands")
    task_sub = task.add_subparsers(dest="task_cmd")

    task_list = task_sub.add_parser("list", help="List tasks")
    task_list.add_argument("project")

    task_add = task_sub.add_parser("add", help="Add task")
    task_add.add_argument("project")
    task_add.add_argument("text")

    task_done = task_sub.add_parser("complete", help="Mark task as completed")
    task_done.add_argument("project")
    task_done.add_argument("index", type=int)

    # language usage
    lang = subparsers.add_parser("get-language", help="Analyze language usage")
    lang.add_argument("project")

    # version list
    ver = subparsers.add_parser("list-versions", help="List saved versions")
    ver.add_argument("project")

    args = parser.parse_args()

    # Helper paths
    def task_file(project): return os.path.join(project, ".organizer_tasks.json")
    def versions_file(project): return os.path.join("projects_versions", os.path.basename(project), "versions.json")

    def load_json(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_json(path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # Execute commands
    if args.command == "list-projects":
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, ruta FROM proyectos")
        for name, path in cursor.fetchall():
            print(f"📁 {name}: {path}")
        conn.close()

    elif args.command == "add-project":
        insertar_proyecto(args.name, args.desc, args.path, args.repo)
        print(f"✅ Project '{args.name}' added.")

    elif args.command == "open-project":
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ruta FROM proyectos WHERE nombre=?", (args.name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            abrir_threading("", row[0], selected_editor.get())
            print(f"🚀 Opening '{args.name}'...")
        else:
            print("❌ Project not found.")

    elif args.command == "version":
        print(f"📦 Organizer version {version}")

    elif args.command == "task":
        project_path = resolver_ruta_proyecto(args.project)
        if args.task_cmd == "list":
            tasks = load_json(task_file(project_path))
            for i, t in enumerate(tasks):
                status = "✅" if t.get("done") else "❌"
                print(f"{i}. {status} {t['text']}")
        elif args.task_cmd == "add":
            tasks = load_json(task_file(project_path))
            tasks.append({"text": args.text, "done": False})
            save_json(task_file(project_path), tasks)
            print("📝 Task added.")
        elif args.task_cmd == "complete":
            tasks = load_json(task_file(project_path))
            if 0 <= args.index < len(tasks):
                tasks[args.index]["done"] = True
                save_json(task_file(project_path), tasks)
                print("✅ Task marked as done.")
            else:
                print("❌ Invalid task index.")

    elif args.command == "get-language":
        project_path = resolver_ruta_proyecto(args.project)
        ext_counter = Counter()
        for root, _, files in os.walk(project_path):
            if "projects_versions" in root:
                continue
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                ext_counter[ext] += 1

        lang_counter = {}
        for ext, count in ext_counter.items():
            lang = EXT_TO_LANG_CLI.get(ext)
            if lang:
                lang_counter[lang] = lang_counter.get(lang, 0) + count

        total = sum(lang_counter.values())
        for lang, count in sorted(lang_counter.items(), key=lambda x: x[1], reverse=True):
            percent = round((count / total) * 100, 2)
            print(f"{lang}: {percent}%")

    elif args.command == "list-versions":
        project_path = resolver_ruta_proyecto(args.project)
        versions = load_json(versions_file(project_path))
        for v in versions:
            print(f"{v['name']} - {v['date']} :: {v.get('coment', '')}")

    else:
        return False
        
    return True

def resolver_ruta_proyecto(input_path_o_nombre):
    if os.path.isdir(input_path_o_nombre):
        return input_path_o_nombre

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ruta FROM proyectos WHERE nombre=?", (input_path_o_nombre,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    else:
        print(f"❌ No project found with name or path: '{input_path_o_nombre}'")
        sys.exit(1)

def open_command_palette(plugin_api=None):
    palette = tk.Toplevel(orga)
    palette.title("Command Palette")
    palette.geometry("520x320")
    palette.transient(orga)
    palette.grab_set()

    palette.configure(bg="#2b2b2b")
    x = (palette.winfo_screenwidth() - 520) // 2
    y = (palette.winfo_screenheight() - 320) // 2
    palette.geometry(f"+{x}+{y}")
    
    entry_var = tk.StringVar()
    entry = ttk.Entry(palette, textvariable=entry_var, font=("Segoe UI", 11))
    entry.pack(fill="x", padx=12, pady=(12, 5))

    listbox = tk.Listbox(palette, font=("Segoe UI", 10), activestyle="dotbox", height=12)
    listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    all_commands = []
    if plugin_api and hasattr(plugin_api, "_commands"):
        for name, meta in plugin_api._commands.items():
            desc = meta.get("description", "")
            all_commands.append((name, desc))

    def render_commands(filter_txt=""):
        listbox.delete(0, "end")
        for cmd, desc in all_commands:
            if filter_txt.lower() in cmd.lower() or filter_txt.lower() in desc.lower():
                listbox.insert("end", f"{cmd} — {desc}")

    render_commands()

    entry_var.trace_add("write", lambda *_: render_commands(entry_var.get()))

    def execute_selected():
        if not listbox.curselection():
            return
        selected = listbox.get(listbox.curselection()[0])
        command = selected.split(" — ")[0].strip()
        if plugin_api:
            try:
                plugin_api.run_command(command)
            except Exception as e:
                ms.showerror("Command Error", f"Error running command '{command}':\n{e}")
        palette.destroy()

    entry.bind("<Return>", lambda e: execute_selected())
    listbox.bind("<Double-1>", lambda e: execute_selected())
    entry.bind("<Escape>", lambda e: palette.destroy())
    listbox.bind("<Escape>", lambda e: palette.destroy())

    palette.deiconify()
    entry.focus_set()

def abrir_fuzzy_finder(project_path):
    finder = tk.Toplevel(orga)
    finder.overrideredirect(True)
    finder.configure(bg="#222")
    finder.attributes("-topmost", True)
    finder.grab_set()

    w, h = 800, 490
    x = orga.winfo_rootx() + (orga.winfo_width() - w) // 2
    y = orga.winfo_rooty() + 60
    finder.geometry(f"{w}x{h}+{x}+{y}")

    frame = ttk.Frame(finder, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="🔍 Search file", font=("Segoe UI", 10, "bold")).pack(anchor="w")

    query_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=query_var, font=("Segoe UI", 10))
    entry.pack(fill="x", pady=(6, 8))
    entry.focus()

    content_frame = ttk.Frame(frame)
    content_frame.pack(fill="both", expand=True)

    listbox = tk.Listbox(content_frame, font=("Consolas", 9), width=40)
    listbox.pack(side="left", fill="y")

    preview = CodeView(content_frame, wrap="none", font=("Consolas", 9))
    preview.pack(side="left", fill="both", expand=True, padx=(10, 0))

    # 🔽 Barra inferior
    status_bar = ttk.Frame(frame)
    status_bar.pack(fill="x", side="bottom")
    status_label = ttk.Label(status_bar, text="📄 No file selected", font=("Segoe UI", 9, "italic"))
    status_label.pack(anchor="w", padx=5)

    file_index = []

    def index_files():
        for root, _, filenames in os.walk(project_path):
            for file in filenames:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start=project_path).replace("\\", "/")
                file_index.append((file, rel_path, full_path))

    threading.Thread(target=index_files, daemon=True).start()

    def update_preview(path):
        preview.configure(state="normal")
        preview.delete("1.0", "end")
        status_label.config(text="📄 Loading...")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(3000)

            try:
                lexer = get_lexer_for_filename(path)
                preview.configure(lexer=lexer)
            except ClassNotFound:
                preview.configure(lexer=None)

            preview.insert("1.0", content)
            lines = content.count("\n") + 1
            size_kb = os.path.getsize(path) / 1024
            ext = os.path.splitext(path)[1]
            name = os.path.basename(path)

            status_label.config(
                text=f"📄 {name}   |   🧾 {lines} lines   |   💾 {size_kb:.1f} KB   |   📦 {ext or 'unknown'}"
            )

        except Exception as e:
            preview.insert("1.0", f"[Error previewing file: {e}]")
            status_label.config(text="❌ Error loading file")

        preview.configure(state="disabled")

    def update_results(*args):
        query = query_var.get().lower().strip()
        listbox.delete(0, "end")
        if not query or not file_index:
            return
        matches = difflib.get_close_matches(query, [f[1] for f in file_index], n=50, cutoff=0.2)
        for match in matches:
            listbox.insert("end", match)

    def on_select(event=None):
        try:
            selected = listbox.get(listbox.curselection())
            for name, rel_path, abs_path in file_index:
                if rel_path == selected:
                    update_preview(abs_path)
                    return
        except:
            pass

    def on_open(event=None):
        try:
            selected = listbox.get(listbox.curselection())
            for _, rel, abs_path in file_index:
                if rel == selected:
                    finder.destroy()
                    #abrir_editor_codigo(abs_path)
                    break
        except:
            pass

    listbox.bind("<<ListboxSelect>>", on_select)
    listbox.bind("<Return>", on_open)
    entry.bind("<Down>", lambda e: listbox.focus_set() or listbox.selection_set(0))

    query_var.trace_add("write", update_results)
    finder.bind("<Escape>", lambda e: finder.destroy())

def search_on_files(project_path):
    import queue
    search_win = tk.Toplevel(orga)
    search_win.title("🔎 Global Search")
    search_win.geometry("800x600")
    search_win.iconbitmap(path)
    search_win.configure(bg="#222")
    search_win.grab_set()

    frame = ttk.Frame(search_win, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="🔍 Search Text", font=("Segoe UI", 10, "bold")).pack(anchor="w")

    query_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=query_var, font=("Segoe UI", 10))
    entry.pack(fill="x", pady=6)
    entry.focus()

    results_list = tk.Listbox(frame, font=("Consolas", 9), height=12)
    results_list.pack(fill="both", expand=True, side="left", padx=(0, 5))

    preview = CodeView(frame, wrap="none", height=15)
    preview.pack(fill="both", expand=True, side="right")

    status = ttk.Label(search_win, text="", anchor="w")
    status.pack(fill="x", padx=10, pady=4)

    result_queue = queue.Queue()

    def search_in_files(query):
        results = []
        for root, _, files in os.walk(project_path):
            for fname in files:
                if not fname.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp", ".json", ".txt")):
                    continue
                full_path = os.path.join(root, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for i, line in enumerate(lines):
                        if query.lower() in line.lower():
                            rel_path = os.path.relpath(full_path, project_path).replace("\\", "/")
                            results.append((rel_path, i + 1, line.strip(), full_path))
                except:
                    continue
        result_queue.put(results)

    def do_search():
        query = query_var.get().strip()
        if not query:
            return
        results_list.delete(0, "end")
        preview.configure(state="normal")
        preview.delete("1.0", "end")
        preview.configure(state="disabled")
        status.config(text="Searching...")

        threading.Thread(target=search_in_files, args=(query,), daemon=True).start()
        check_results()

    def check_results():
        try:
            results = result_queue.get_nowait()
            for r in results:
                results_list.insert("end", f"{r[0]} (line {r[1]})")
            status.config(text=f"{len(results)} result(s) found.")
            results_list.results = results
        except queue.Empty:
            search_win.after(100, check_results)

    def show_preview(event):
        selection = results_list.curselection()
        if not selection:
            return
        idx = selection[0]
        result = results_list.results[idx]
        _, line_number, _, file_path = result

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lexer = get_lexer_for_filename(file_path)
            preview.configure(state="normal", lexer=lexer)
            preview.delete("1.0", "end")
            preview.insert("1.0", content)
            preview.mark_set("insert", f"{line_number}.0")
            preview.see(f"{line_number}.0")
            preview.configure(state="disabled")
        except Exception as e:
            preview.configure(state="normal", lexer=lexer)
            preview.delete("1.0", "end")
            preview.insert("1.0", f"Error loading file:\n{e}")
            preview.configure(state="disabled")

    entry.bind("<Return>", lambda e: do_search())
    results_list.bind("<<ListboxSelect>>", show_preview)
    search_win.bind("<Escape>", lambda e: search_win.destroy())


menu_name = "Organizer"
description_menu = "Open Organizer"
ruta_exe = os.path.abspath(sys.argv[0])
ruta_icono = ruta_exe
ruta_db = ruta_exe

orga = ThemedTk()
orga.withdraw()
show_splash(duration=3000)
orga.title('Project Organizer')
orga.geometry("1230x500")
orga.resizable(True, True)
orga.iconbitmap(path)
temas = orga.get_themes()
ttkbootstrap_themes = ttk_themes()

saved_state = load_config()
check_var = tk.IntVar(value=saved_state if saved_state else (1 if is_in_startup() else 0))

main_frame = ttk.Frame(orga, bootstyle="default")
main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

sidebar = ttk.Frame(orga, width=300)

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

editores_disponibles = ["Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
                        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
                        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
                        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
                        "Android Studio", "neovim"]

lenguajes = ["Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go", "flutter"]

menu = tk.Menu(orga)
orga.config(menu=menu)
menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Projects", menu=menu_archivo)
menu_archivo.add_command(label='Agree Project', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Create New', command=crear_nuevo_proyecto)
menu_archivo.add_command(label='sandbox', command=open_sandbox)
menu_archivo.add_command(label="My Github Profile", command=unify_windows)
menu_archivo.add_command(label="New Project Github", command=abrir_proyecto_github)
menu_archivo.add_command(label="Push Update Github", command=lambda: push_actualizaciones_github(tree.item(tree.selection())['values'][4]))
menu_archivo.add_command(label='Delete Project', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][1], tree.item(tree.selection())['values'][3]))
menu_archivo.add_command(label="Generate Report", command=generar_informe)
menu_settings = tk.Menu(menu, tearoff=0)
menu.add_command(label="Settings", command=setting_window)   
help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="Plugins", command=lambda: gestor_plugins(plugin_api))
help_menu.add_command(label="InfoVersion", command=ver_info)
help_menu.add_command(label="Documentation", command=show_docu)

ttk.Label(main_frame, text="Name:", bootstyle='info').grid(row=0, column=0, padx=5, pady=5, sticky="w")
nombre_entry = ttk.Entry(main_frame, width=170)
nombre_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(main_frame, text="Description:", bootstyle='info').grid(row=1, column=0, padx=5, pady=5, sticky="w")
descripcion_entry = ttk.Entry(main_frame, width=170)
descripcion_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(main_frame, text="Repository URL:", bootstyle='info').grid(row=2, column=0, padx=5, pady=5, sticky="w")
repo_entry = ttk.Entry(main_frame, width=170)
repo_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

tree = ttk.Treeview(
    main_frame,
    columns=('id','Description', 'Language', 'Path', 'Repository'),
    show='tree headings',
    bootstyle='primary'
)

tree.heading('#0', text='Project')
tree.column('#0', width=200)

for col in ('id', 'Description', 'Language', 'Path', 'Repository'):
    tree.heading(col, text=col)
    tree.column(col, width=150)

tree.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

scrollbar_y = ttk.Scrollbar(main_frame, orient='vertical', command=tree.yview, bootstyle='round-primary')
scrollbar_y.grid(row=4, columnspan=2, padx=5, pady=5, sticky='nse')
tree.configure(yscrollcommand=scrollbar_y.set)
tree.bind("<Button-3>", show_context_menu)
tree.bind("<<TreeviewOpen>>", load_project_structure_on_expand)
tree.bind("<<TreeviewSelect>>", update_sidebar_project)
orga.bind_all("<Control-p>", lambda e: abrir_fuzzy_finder(tree.item(tree.selection())['values'][3]))
orga.bind_all("<Control-f>", lambda e: search_on_files(tree.item(tree.selection())['values'][3]))

ttk.Label(main_frame, text="Search Project:", bootstyle='info').grid(row=6, column=0, padx=5, pady=5, sticky="w")
search_entry = ttk.Entry(main_frame, width=170)
search_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
search_entry.bind("<KeyRelease>", on_key_release)

selected_editor = tk.StringVar()
editor_options = [
    "Select a Editor", "Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
    "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
    "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
    "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
    "Android Studio", "Integrated Editor", "neovim"
]
selected_editor.set(editor_options[0])

ttk.Label(main_frame, text="Editor:", bootstyle='info').grid(row=7, column=0, padx=5, pady=5, sticky="w")
editor_menu = ttk.Combobox(main_frame, textvariable=selected_editor, values=editor_options, state="readonly", bootstyle='secondary')
editor_menu.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

def obtener_datos_seleccionado(tree):
    seleccionados = tree.selection()
    if not seleccionados:
        ms.showinfo("Error", "No project selected.")
        return None, None
    item_seleccionado = seleccionados[0]
    item_data = tree.item(item_seleccionado)['values']
    id_proyecto = item_data[0]  # id
    ruta = item_data[3]  # ruta
    return id_proyecto, ruta

btn_abrir = ttk.Button(main_frame, text='Open Project', command=lambda: abrir_threading(
    *obtener_datos_seleccionado(tree),
    selected_editor.get()
), bootstyle='success')
btn_abrir.grid(row=8, column=0, columnspan=2, pady=10, padx=5, sticky="s")

version_label = ttk.Label(main_frame, text=f'{version}', bootstyle='info')
version_label.grid(row=8, column=1, pady=5, padx=5, sticky="se")

main_frame.grid_rowconfigure(4, weight=1)

plugin_api = PluginAPI(
    main_window=main_frame,
    menu=menu_archivo,
    sidebar=sidebar,
    tree=tree,
)

plugin_api.register_command("refresh_sidebar", update_sidebar_project, "Refresh sidebar")
plugin_api.register_command("open_terminal", lambda: os.system("start cmd"), "Open system terminal")
orga.bind_all("<Control-Shift-P>", lambda e: open_command_palette(plugin_api))

def start_gui():
    crear_base_datos()
    asegurar_editor_utilizado_column()
    orga.after(0, mostrar_proyectos)
    set_default_theme()
    thread_check_update()
    thread_sinc()
    initialize_backup_schedule()
    asociate_files_extension()
    load_plugins(plugin_api)
    orga.mainloop()

if __name__ == "__main__":
    if run_cli_commands():
        sys.exit()

    if len(sys.argv) > 1:
        open_project_file(sys.argv[1],)
        
    start_gui()
