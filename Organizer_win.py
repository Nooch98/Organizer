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
import tkinter as tk
import jedi
import markdown
import requests
import importlib.util
import pygments.lexers
import platform
import subprocess
import ttkbootstrap as ttk
import markdown2
#--------------------------------------------------------#
from tkinter import OptionMenu, StringVar, filedialog, simpledialog
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
import ttkthemes


main_version = "ver.1.9.2"
version = str(main_version)
archivo_configuracion_editores = "configuracion_editores.json"
archivo_confgiguracion_github = "configuracion_github.json"
archivo_configuracion_gpt = "configuration_gpt.json"
security_backup = "security_backup.json"
selected_project_path = None
text_editor = None

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

def abrir_editor(ruta, ruta_editor):
    subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
    
def setting_backup():
    backup = tk.Toplevel(root)
    backup.title("Setting Security Backup")
    backup.iconbitmap(path)
    
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

def detectar_editores_disponibles():
    editores = {
        "Visual Studio Code": "code",
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
        "Code::Blocks": "codeblocks.exe",
        "NetBeans": "netbeans.exe",
        "Android Studio": "studio64.exe",
        "neovim": "nvim.exe"
    }
    return {nombre: shutil.which(binario) for nombre, binario in editores.items() if shutil.which(binario)}

def abrir_proyecto(ruta, editor):
    configuracion_editores = cargar_configuracion_editores()
    ruta_editor = configuracion_editores.get(editor) if configuracion_editores and editor in configuracion_editores else None

    if not ruta_editor:
        editores_disponibles = detectar_editores_disponibles()
        ruta_editor = editores_disponibles.get(editor)
    
    if ruta_editor:
        subprocess.Popen([ruta_editor, ruta], shell=True)
        subprocess.run(f'Start wt -d "{ruta}"', shell=True)
    elif editor == "neovim":
        comando_ps = f"Start-Process nvim '{ruta}' -WorkingDirectory '{ruta}'"
        subprocess.Popen(["powershell", "-Command", comando_ps])
    elif editor == "Editor Integrated":
        subprocess.Popen(f'Start wt -d "{ruta}"', shell=True)
        abrir_editor_thread(ruta, tree.item(tree.selection())['values'][1])
    else:
        ms.showerror("ERROR", f"{editor} Not found")

def abrir_editor_thread(ruta, name):
    threading.Thread(target=abrir_editor_integrado, args=(ruta, name)).start()

def abrir_editor_integrado(ruta_proyecto, nombre_proyecto):
    import time
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
            new_tab_window.iconbitmap(path)
            
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
        new_theme.iconbitmap(path)
        
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
    ventana_lenguaje = tk.Toplevel(root)
    ventana_lenguaje.title("Selection lenguaje")
    ventana_lenguaje.iconbitmap(path)
    
    main_frame = ttk.Frame(ventana_lenguaje)
    main_frame.pack()
    
    label = ttk.Label(main_frame, text="Select the project language:")
    label.grid(row=0, columnspan=2, pady=5, padx=5)
    
    lenguaje_options = ["Selection lenguaje", "Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go"]
    
    global seleccion
    
    seleccion = tk.StringVar()
    seleccion.set(lenguaje_options[0])
    
    menu_lenguaje = ttk.OptionMenu(main_frame, seleccion, *lenguaje_options)
    menu_lenguaje.grid(row=1, columnspan=2, padx=5, pady=5)
    
    rules_label = ttk.Label(main_frame, text="If you create git repo insert in textbox your rules for the .gitignore")
    rules_label.grid(row=2, columnspan=2, padx=5, pady=5)
    
    textbox = scrolledtext.ScrolledText(main_frame)
    textbox.grid(row=3, columnspan=2, pady=5, padx=5)
    
    btn_selec = ttk.Button(main_frame, text="Select", command=lambda: ejecutar_con_threading(seleccion.get(), textbox))
    btn_selec.grid(row=5, columnspan=2, pady=5, padx=5)
        
def ejecutar_con_threading(lenguaje, textbox):
    threading.Thread(target=iniciar_new_proyect, args=(lenguaje, textbox)).start()
    
def crear_repo_github(nombre_repo, descripcion_repo, ruta_local):
    token_github = cargar_configuracion_github()
    
    if token_github:
        g = Github(token_github)
        
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
        
def push_actualizaciones_github(ruta_local):
    repo_local = git.Repo(ruta_local)

    repo_local.index.add('*')

    repo_local.index.commit('Updated project')

    origin = repo_local.remote('origin')

    origin.push('master')
        
def iniciar_new_proyect(lenguaje, textbox):
    nombre = nombre_entry.get()
    descripcion = descripcion_entry.get()
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
                print(f"Este es el lenguaje:{lenguaje}")
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
    
    nombre_entry.delete(0, tk.END)
    descripcion_entry.delete(0, tk.END)
    repo_entry.delete(0, tk.END)
    textbox.delete(0, tk.END)

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

def config_editors():
    config_editor = tk.Toplevel(root)
    config_editor.title("Editors Config")
    config_editor.iconbitmap(path)
    
    main_frame = ttk.Frame(config_editor)
    main_frame.pack()
    
    rutas_editores = {}
    
    configs_editors = cargar_configuracion_editores()
    if configs_editors is None:
        configs_editors = {}

    def guardar_y_cerrar():
        guardar_configuracion_editores(rutas_editores)
        config_editor.destroy()
    
    for i, programa in enumerate(editores_disponibles):
        label = ttk.Label(main_frame, text=programa)
        label.grid(row=i, column=0, padx=5, pady=5)
        
        entry = ttk.Entry(main_frame, width=80)
        entry.grid(row=i, column=1, padx=5, pady=5)
        
        if programa in configs_editors:
            entry.insert(0, configs_editors[programa])
        
        btn = ttk.Button(main_frame, text="Agree", command=lambda prog=programa, ent=entry: seleccionar_ruta_editor(prog, ent))
        btn.grid(row=i, column=2, padx=5, pady=5)
        
        rutas_editores[programa] = entry

    aceptar_btn = ttk.Button(main_frame, text="Confirm", command=guardar_y_cerrar)
    aceptar_btn.grid(row=len(editores_disponibles), column=0, columnspan=3, padx=5, pady=5)
    
def config_github():
    config_github = tk.Toplevel(root)
    config_github.title("Api Key Github")
    config_github.iconbitmap(path)
    
    main_frame = ttk.Frame(config_github)
    main_frame.pack()
    
    titulo = ttk.Label(main_frame, text="Github Configuration")
    titulo.grid(row=0, columnspan=2, pady=5, padx=5)
    
    label = ttk.Label(main_frame, text="Github Api Key: ")
    label.grid(row=1, column=0, pady=5, padx=5)
    
    api_entry = ttk.Entry(main_frame, width=50)
    api_entry.grid(row=1, column=1, pady=5, padx=5)
    
    def guardar():
        api_key = api_entry.get()
        guardar_configuracion_github(api_key)
        config_github.destroy()
    
    sub_button = ttk.Button(main_frame, text="Accept", command=guardar)
    sub_button.grid(row=2, columnspan=2, pady=5, padx=5)
    
def config_openai():
    config_openai = tk.Toplevel(root)
    config_openai.title("Api Key OpenAI")
    config_openai.iconbitmap(path)
    
    main_frame = ttk.Frame(config_openai)
    main_frame.pack()
    
    titulo = ttk.Label(main_frame, text="OpenAI Configuration")
    titulo.grid(row=0, columnspan=2, pady=5, padx=5)
    
    label = ttk.Label(main_frame, text="OpenAI Api Key: ")
    label.grid(row=1, column=0, pady=5, padx=5)
    
    api_gpt_entry = ttk.Entry(main_frame, width=50)
    api_gpt_entry.grid(row=1, column=1, pady=5, padx=5)
    
    def guardar():
        api_key = api_gpt_entry.get()
        save_config_gpt(api_key)
        config_openai.destroy()
    
    sub_button = ttk.Button(main_frame, text="Accept", command=guardar)
    sub_button.grid(row=2, columnspan=2, pady=5, padx=5)
    
def seleccionar_ruta_editor(editor, entry):
    ruta_editor = filedialog.askopenfilename(title=f"Seleccione el ejecutable de {editor}", filetypes=[("Ejecutables", "*.exe")])
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
        
def guardar_configuracion_github(api_key):
    configuracion = {"api_key_github": api_key}
    
    with open("configuracion_github.json", "w") as archivo_configuracion:
        json.dump(configuracion, archivo_configuracion)
        
def cargar_configuracion_github():
    try:
        with open(archivo_confgiguracion_github, "r") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)
            return configuracion.get("api_key_github", None)
    except FileNotFoundError:
        return None
    
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
        ("Delete", eliminar_proyecto),
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
         
def select_terminal():
    setting_terminal = tk.Toplevel(root)
    setting_terminal.title("Setting Terminal")
    setting_terminal.iconbitmap(path)
    
    main_frame = ttk.Frame(setting_terminal)
    main_frame.pack()
    
    terminal_label = ttk.Label(main_frame, text="Select Terminal")
    terminal_label.grid(row=0, columnspan=2, padx=5, pady=5)
    
    selected_terminal = tk.StringVar()
    terminal_choices = ["Select Terminal", "Command Pormpt", "Windows Terminal", "PowerShell", "Git Bash"]
    terminal_menu = ttk.OptionMenu(main_frame, selected_terminal, *terminal_choices)
    terminal_menu.grid(row=1, columnspan=2, pady=5, padx=5)
    
    terminal_path_label = ttk.Label(main_frame, text="Terminal Executable Path: ")
    terminal_path_label.grid(row=2, column=0, padx=5, pady=5)
    
    terminal_path_entry = ttk.Entry(main_frame, width=50)
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
            
        setting_terminal.destroy()
            
    save_button = ttk.Button(main_frame, text="Save", command=save_settigns)
    save_button.grid(row=3, columnspan=2, padx=5, pady=5)

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
        change_bootstrap_theme(theme_name="cyborg")
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

root = ThemedTk()
root.title('Proyect Organizer')
root.geometry("1230x420")
path = resource_path("software.ico")
root.iconbitmap(path)
temas = root.get_themes()
ttkbootstrap_themes = ttk_themes()

main_frame = ttk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew")

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
        

filas_ocultas = set()

editores_disponibles = ["Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio", "neovim"]

lenguajes = ["Python", "NodeJS", "bun", "React", "Vue", "C++", "C#", "Rust", "Go"]

menu = tk.Menu(root)
root.config(menu=menu)

menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Proyects", menu=menu_archivo)
menu_archivo.add_command(label='Agree Proyect', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Create New', command=crear_nuevo_proyecto)
menu_archivo.add_command(label="New Project Github", command=abrir_proyecto_github)
menu_archivo.add_command(label="Push Update Github", command=push_actualizaciones_github)
menu_archivo.add_command(label='Delete Proyect', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4]))
menu_archivo.add_command(label="Generate Report", command=generar_informe)

menu_settings = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Settings", menu=menu_settings)
menu_settings.add_command(label="Config Editor", command=config_editors)
menu_settings.add_command(label="Github", command=config_github)
menu_settings.add_command(label="OpenAI", command=config_openai)
lenguajes_menu = tk.Menu(menu_settings, tearoff=0)
menu_settings.add_cascade(label='Install Lenguajes', menu=lenguajes_menu)
for lenguaje in lenguajes:
    lenguajes_menu.add_command(label=lenguaje, command=lambda lenguaje=lenguaje: install_lenguaje(lenguaje))
menu_settings.add_command(label='Install Choco', command=lambda: install_choco)
menu_settings.add_command(label="Install Scoop", command=lambda: install_scoop)
menu_editor = tk.Menu(menu_settings, tearoff=0)
menu_settings.add_cascade(label="Instalar Editor", menu=menu_editor)
menu_editor.add_command(label="Visual Studio Code", command=lambda: install_editor("Visual Studio Code"))
menu_editor.add_command(label="Sublime Text", command=lambda: install_editor("Sublime Text"))
menu_editor.add_command(label="Vim",  command=lambda: install_editor("Vim"))
menu_editor.add_command(label="Neovim", command=lambda: install_editor("Neovim"))
menu_editor.add_command(label="Emacs", command=lambda: install_editor("Emacs"))
menu_editor.add_command(label="Notepad++", command=lambda: install_editor("Notepad++"))
menu_editor.add_command(label="Brackets", command=lambda: install_editor("Brackets"))
menu_editor.add_command(label="Geany", command=lambda: install_editor("Geany"))
menu_editor.add_command(label="gedit", command=lambda: ms.showinfo("gedit", "gedit is a opensource editor for linux but in windows you can buy on microsoft store for 4$"))
menu_editor.add_command(label="Nano", command=lambda: install_editor("Nano"))
menu_editor.add_command(label="Kate", command=lambda: install_editor("Kate"))
menu_editor.add_command(label="Eclipse", command=lambda: install_editor("Eclipse"))
menu_editor.add_command(label="IntelliJ IDEA", command=lambda: install_editor("Intellij IDEA"))
menu_editor.add_command(label="PyCharm")
menu_editor.add_command(label="Visual Studio")
menu_editor.add_command(label="Code::Blocks")
menu_editor.add_command(label="NetBeans")
menu_editor.add_command(label="Android Studio")
menu_settings.add_command(label="Backup Setting", command=setting_backup)
menu_settings.add_command(label="Terminal", command=select_terminal)
theme_menu = tk.Menu(menu_settings, tearoff=0)
ttkmenu = tk.Menu(menu_settings, tearoff=0)
menu_settings.add_cascade(label="Theme", menu=theme_menu)
for tema in temas:
    theme_menu.add_command(label=tema, command=lambda tema=tema: change_theme(tema))
ttkmenu.add_command(label="Create Theme", command=create_theme)
menu_settings.add_cascade(label="ttkbootstrap Themes", menu=ttkmenu)
for tema in ttkbootstrap_themes:
    ttkmenu.add_command(label=tema, command=lambda theme_name=tema: change_bootstrap_theme(theme_name))
    
menu_help = tk.Menu(menu, tearoff=0)

menu.add_cascade(label="Help", menu=menu_help)
menu_help.add_command(label="Version", command=show_version)
menu_help.add_command(label="Changelog", command=ver_info)


nombre_label = ttk.Label(main_frame, text="Name:")
nombre_label.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

nombre_entry = ttk.Entry(main_frame, width=100)
nombre_entry.grid(row=1, column=1, pady=5, padx=5, sticky="ew")

descripcion_label = ttk.Label(main_frame, text='Description:')
descripcion_label.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

descripcion_entry = ttk.Entry(main_frame, width=100)
descripcion_entry.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

repo_label = ttk.Label(main_frame, text="Repository URL:")
repo_label.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

repo_entry = ttk.Entry(main_frame, width=100)
repo_entry.grid(row=3, column=1, pady=5, padx=5, sticky="ew")

depen_label = ttk.Label(main_frame, text="Dependencies:")
depen_label.grid(row=4, column=0, pady=5, padx=5, sticky="nsew")

depen_entry = ttk.Entry(main_frame, width=100)
depen_entry.grid(row=4, column=1, pady=5, padx=5, sticky="ew")

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
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio", "Editor Integrated", "neovim"
    ]
selected_editor.set(editor_options[0])
editor_menu = ttk.OptionMenu(main_frame, selected_editor, *editor_options)
editor_menu.grid(row=9, column=0, padx=5, pady=5, sticky="sw")

tree.bind("<Button-3>", show_context_menu)
tree.bind("<Double-1>", abrir_repositorio)
tree.bind("<Control-1>", abrir_explorador)
tree.bind("<<TreeviewSelect>>", on_project_select)

btn_abrir = ttk.Button(main_frame, text='Open Proyect', command=lambda: abrir_threading(tree.item(tree.selection())['values'][4], selected_editor.get()))
btn_abrir.grid(row=9, columnspan=2, pady=5, padx=5, sticky="s")

btn_install = ttk.Button(main_frame, text="Install dependencies", command=lambda: install_librarys(tree.item(tree.selection())['values'][3]))
btn_install.grid(row=4, column=1, padx=5, pady=5, sticky="e")

version_label = ttk.Label(main_frame, text=version)
version_label.grid(row=9, column=1, pady=5, padx=5, sticky="se")

root.bind("<Control-q>", lambda e: root.quit())

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

main_frame.grid_rowconfigure(5, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

crear_base_datos()
mostrar_proyectos()
set_default_theme()
root.mainloop()
