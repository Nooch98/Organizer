import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import OptionMenu, StringVar, filedialog
from tkinter import messagebox as ms
from tkinter import scrolledtext, ttk
from turtle import heading

import git
from github import Auth, Github
from ttkthemes import ThemedTk

main_version = "ver.1.7"
version = str(main_version)

archivo_configuracion_editores = "configuracion_editores.json"
archivo_confgiguracion_github = "configuracion_github.json"
selected_project_path = None

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
   
def abrir_proyecto(ruta, editor):
    configuracion_editores = cargar_configuracion_editores()
    ruta_editor = None

    if configuracion_editores and editor in configuracion_editores:
        ruta_editor = configuracion_editores[editor]
        subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
        subprocess.run(f'Start wt -d "{ruta}"', shell=True)
    
    else:
        if editor == "Visual Studio Code":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Sublime Text":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Atom":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Vim":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Emacs":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Notepad++":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Brackets":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "TextMate":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Geany":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "gedit":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Nano":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Kate":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Bluefish":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Eclipse":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "IntelliJ IDEA":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "PyCharm":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Visual Studio":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Code::Blocks":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "NetBeans":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
        elif editor == "Android Studio":
            subprocess.Popen(f'"{ruta_editor}" "{ruta}"')
            subprocess.run(f'Start wt -d "{ruta}"', shell=True)
            
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
    
    label = ttk.Label(ventana_lenguaje, text="Select the project language:")
    label.grid(row=0, columnspan=2, pady=5, padx=5)
    
    lenguaje_options = ["Selection lenguaje", "Python", "NodeJS", "React", "Vue", "C++", "C#", "Rust", "Go"]
    
    global seleccion
    
    seleccion = tk.StringVar()
    seleccion.set(lenguaje_options[0])
    
    menu_lenguaje = ttk.OptionMenu(ventana_lenguaje, seleccion, *lenguaje_options)
    menu_lenguaje.grid(row=1, columnspan=2, padx=5, pady=5)
    
    textbox = scrolledtext.ScrolledText(ventana_lenguaje)
    textbox.grid(row=2, columnspan=2, pady=5, padx=5)
    
    btn_selec = ttk.Button(ventana_lenguaje, text="Select", command=lambda: ejecutar_con_threading(seleccion.get(), textbox))
    btn_selec.grid(row=5, columnspan=2, pady=5, padx=5)
        
def ejecutar_con_threading(lenguaje, textbox):
    threading.Thread(target=iniciar_new_proyect, args=(lenguaje, textbox)).start()
    
def crear_repo_github(nombre_repo, descripcion_repo, ruta_local):
    token_github = cargar_configuracion_github()
    
    if token_github:
        g = Github(token_github)
        
        # Obtener el usuario
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
    # Obtener la instancia del repositorio local
    repo_local = git.Repo(ruta_local)

    # Añadir todos los cambios realizados
    repo_local.index.add('*')

    # Hacer un commit con los cambios
    repo_local.index.commit('Updated project')

    # Obtener la instancia del origen remoto
    origin = repo_local.remote('origin')

    # Realizar el push al repositorio remoto
    origin.push('master')
        
def iniciar_new_proyect(lenguaje, textbox):
    nombre = nombre_entry.get()
    descripcion = descripcion_entry.get()
    repo = repo_entry.get()
    
    if lenguaje == "Python":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'python -m venv "{os.path.join(ruta_completa, "app")}"'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
    elif lenguaje == "NodeJS":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'npm init -w "{os.path.join(ruta_completa)}" -y > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
            os.remove('output.txt')
    elif lenguaje == "React":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'npx create-react-app "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
            os.remove('output.txt')         
    elif lenguaje == "C#":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'dotnet new console -n "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
            os.remove('output.txt') 
    elif lenguaje == "Rust":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'cargo new "{ruta_completa}" --bin > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
            os.remove('output.txt')
    elif lenguaje == "go":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'go mod init "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            respuesta = ms.askyesno("Create Repo", "Do you want create a github repo?")
            if respuesta:
                crear_repo_github(nombre, descripcion, ruta_completa)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, lenguaje, ruta_completa, repo)
            os.remove('output.txt')
    
    nombre_entry.delete(0, tk.END)
    descripcion_entry.delete(0, tk.END)
    repo_entry.delete(0, tk.END)

def eliminar_proyecto(id, ruta):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
    conn.commit()
    shutil.rmtree(ruta)
    mostrar_proyectos()
    conn.close()

def config_editors():
    config_editor = tk.Toplevel(root)
    config_editor.title("Editors Config")
    config_editor.iconbitmap(path)
    
    rutas_editores = {}

    def guardar_y_cerrar():
        guardar_configuracion_editores(rutas_editores)
        config_editor.destroy()

    for i, programa in enumerate(editores_disponibles):
        label = ttk.Label(config_editor, text=programa)
        label.grid(row=i, column=0, padx=5, pady=5)
        
        entry = ttk.Entry(config_editor)
        entry.grid(row=i, column=1, padx=5, pady=5)
        
        btn = ttk.Button(config_editor, text="Agree", command=lambda prog=programa, ent=entry: seleccionar_ruta_editor(prog, ent))
        btn.grid(row=i, column=2, padx=5, pady=5)
        
        rutas_editores[programa] = entry

    aceptar_btn = ttk.Button(config_editor, text="Confirm", command=guardar_y_cerrar)
    aceptar_btn.grid(row=len(editores_disponibles), column=0, columnspan=3, padx=5, pady=5)
    
def config_github():
    config_github = tk.Toplevel(root)
    config_github.title("Api Key Github")
    config_github.iconbitmap(path)
    
    titulo = ttk.Label(config_github, text="Github Configuration")
    titulo.grid(row=0, columnspan=2, pady=5, padx=5)
    
    label = ttk.Label(config_github, text="Github Api Key: ")
    label.grid(row=1, column=0, pady=5, padx=5)
    
    api_entry = ttk.Entry(config_github, width=50)
    api_entry.grid(row=1, column=1, pady=5, padx=5)
    
    def guardar():
        api_key = api_entry.get()
        guardar_configuracion_github(api_key)
        config_github.destroy()
    
    sub_button = ttk.Button(config_github, text="Accept", command=guardar)
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
    # Obtener la fila seleccionada
    seleccion = tree.selection()
    
    # Ocultar la fila seleccionada y agregarla al registro de filas ocultas
    for rowid in seleccion:
        tree.detach(rowid)
        filas_ocultas.add(rowid)

def show_selected_row():
    # Obtener la fila seleccionada
    seleccion = tree.selection()
    
    # Mostrar la fila seleccionada y eliminarla del registro de filas ocultas
    for rowid in seleccion:
        tree.reattach(rowid, '', 'end')
        filas_ocultas.remove(rowid)
        
def show_context_menu(event):
    rowid = tree.identify_row(event.y)
    
    if rowid:
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Hide", command=hide_selected_row)
        context_menu.add_command(label="Show", command=show_selected_row)
        context_menu.add_command(label="Edit", command=modificar_proyecto)
        
        context_menu.post(event.x_root, event.y_root)

def abrir_repositorio(event):
    item_seleccionado = tree.item(tree.selection())
    url_repositorio = item_seleccionado['values'][5]

    webbrowser.open_new(url_repositorio)
    
def abrir_proyecto_github():
    url_repositorio = repo_entry.get()
    

    ruta_destino = filedialog.askdirectory()

    if ruta_destino:
        subprocess.run(['git', 'clone', url_repositorio], cwd=ruta_destino, check=True)
        
        nombre_repositorio = url_repositorio.split('/')[-1].replace('.git', '')
        ruta_repositorio_clonado = os.path.join(ruta_destino, nombre_repositorio)

        abrir_proyecto(ruta_repositorio_clonado, selected_editor.get())
        
        repo_entry.delete(0, tk.END)
        
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def obtener_informacion_proyectos_desde_bd():
    # Conectar a la base de datos
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()

    # Consultar la base de datos para obtener la información de los proyectos
    cursor.execute('SELECT * FROM proyectos')
    proyectos = cursor.fetchall()

    # Cerrar la conexión a la base de datos
    conn.close()

    # Estructurar la información de los proyectos en un formato adecuado
    informacion_proyectos = []
    for proyecto in proyectos:
        proyecto_info = {
            'id': proyecto[0],
            'nombre': proyecto[1],
            'lenguaje': proyecto[2],
            'descripcion': proyecto[3],
            'ruta': proyecto[4],
            'repo': proyecto[5]
        }
        informacion_proyectos.append(proyecto_info)

    return informacion_proyectos

def generar_informe_html(informacion):
    # Estructura HTML del informe
    informe_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Informe de Proyectos</title>
    </head>
    <body>
        <h1>Informe de Proyectos</h1>
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

    # Agregar información de los proyectos al informe HTML
    for proyecto in informacion:
        informe_html += f"""
                <tr>
                    <td>{proyecto['nombre']}</td>
                    <td>{proyecto['descripcion']}</td>
                    <td>{proyecto['Lenguaje']}</td>
                    <td>{proyecto['ruta']}</td>
                    <td>{proyecto['repo']}</td>
                </tr>
        """

    # Cerrar la estructura HTML del informe
    informe_html += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # Guardar el informe HTML en un archivo
    with open("informe.html", "w") as f:
        f.write(informe_html)
        
def on_project_select(event):
    global selected_project_path
    item = tree.selection()[0]
    selected_project_path = tree.item(item, "values")[4]
        
def generar_informe():
    # Obtener la información de los proyectos desde la base de datos
    informacion_proyectos = obtener_informacion_proyectos_desde_bd()
    
    # Generar el informe HTML con la información obtenida
    generar_informe_html(informacion_proyectos)
    
    # Mostrar un mensaje indicando que el informe se ha generado exitosamente
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
    # Verificar si se ha seleccionado una fila en el TreeView
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
    'Repositorio': 5
    }
    
    # Obtener la fila seleccionada
    selected_row = selected_row[0]
    current_values = tree.item(selected_row, "values")

    # Crear una ventana secundaria para la modificación
    mod_window = tk.Toplevel(root)
    mod_window.title("Modify Project")

    # Etiqueta y menú desplegable para seleccionar el campo a modificar
    field_label = ttk.Label(mod_window, text="Select Field to Modify:")
    field_label.grid(row=0, column=0, padx=5, pady=5)

    selected_field = tk.StringVar()
    field_menu = ttk.OptionMenu(mod_window, selected_field, "", *['ID', 'Nombre', 'Descripcion', 'Lenguaje', 'Ruta', 'Repositorio'])
    field_menu.grid(row=0, column=1, padx=5, pady=5)

    # Etiqueta y entrada para el nuevo valor
    new_value_label = ttk.Label(mod_window, text="New Value:")
    new_value_label.grid(row=1, column=0, padx=5, pady=5)

    new_value_entry = ttk.Entry(mod_window)
    new_value_entry.grid(row=1, column=1, padx=5, pady=5)

    # Función para aplicar la modificación
    def apply_modification():
        new_value = new_value_entry.get()
        field = selected_field.get()
        
        # Verificar si se ha seleccionado un campo y se ha ingresado un nuevo valor
        if field and new_value:
            # Obtener la lista de valores actuales y modificar el valor deseado
            current_values = list(tree.item(selected_row, "values"))
            current_values[field_index[field]] = new_value
            
            # Actualizar la fila en el TreeView con los nuevos valores
            tree.item(selected_row, values=current_values)
            
            # Actualizar la base de datos
            update_project(current_values[field_index['ID']], field, new_value)
            
            # Cerrar la ventana secundaria
            mod_window.destroy()
        else:
            ms.showerror("Error", "Please select a field and provide a new value.")

    # Botón para aplicar la modificación
    apply_button = ttk.Button(mod_window, text="Apply", command=apply_modification)
    apply_button.grid(row=2, columnspan=2, padx=5, pady=5)

def update_project(project_id, field, new_value):
    # Conectar a la base de datos
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()

    # Crear y ejecutar la consulta SQL de actualización
    update_query = f"UPDATE proyectos SET {field.lower()}=? WHERE id=?"
    cursor.execute(update_query, (new_value, project_id))

    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()
  
def config_theme():
    def change_theme():
        # Selecciona el tema especificado por el usuario
        theme = selected_theme.get()
        root.set_theme(theme)
        root.update_idletasks()
        root.geometry("")  # Restaurar la geometría predeterminada
        root.geometry(f"{root.winfo_reqwidth()}x{root.winfo_reqheight()}") 

    themes = tk.Toplevel(root)
    themes.title("Change Theme")
    themes.iconbitmap(path)
    
    selected_theme = tk.StringVar(themes)
    selected_theme.set([0])
    
    theme_label = ttk.Label(themes, text="Select Theme:")
    theme_label.pack(padx=10, pady=(10, 0))
    
    theme_menu = tk.OptionMenu(themes, selected_theme, "Select Theme", "arc", "equilux", "radiance", "blue", "ubuntu", "aqua", "plastik", "smog", "adapta", "aquativo", "black", "breeze", "clearlooks", "elegance", "itft1", "keramik", "plastik")
    theme_menu.pack(padx=10, pady=(0, 10))
    
    
    apply_button = tk.Button(themes, text="Apply", command=change_theme)
    apply_button.pack(padx=10, pady=10)
    
def select_terminal():
    setting_terminal = tk.Toplevel(root)
    setting_terminal.title("Setting Terminal")
    setting_terminal.iconbitmap(path)
    
    terminal_label = ttk.Label(setting_terminal, text="Select Terminal")
    terminal_label.grid(row=0, columnspan=2, padx=5, pady=5)
    
    selected_terminal = tk.StringVar()
    terminal_choices = ["Select Terminal", "Command Pormpt", "Windows Terminal", "PowerShell", "Git Bash"]
    terminal_menu = ttk.OptionMenu(setting_terminal, selected_terminal, *terminal_choices)
    terminal_menu.grid(row=1, columnspan=2, pady=5, padx=5)
    
    terminal_path_label = ttk.Label(setting_terminal, text="Terminal Executable Path: ")
    terminal_path_label.grid(row=2, column=0, padx=5, pady=5)
    
    terminal_path_entry = ttk.Entry(setting_terminal, width=50)
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
            
    save_button = ttk.Button(setting_terminal, text="Save", command=save_settigns)
    save_button.grid(row=3, columnspan=2, padx=5, pady=5) 
    
    

root = ThemedTk(theme='aqua')
root.title('Proyect Organizer')
root.geometry("1230x420")
path = resource_path("software.ico")
root.iconbitmap(path)
filas_ocultas = set()

editores_disponibles = ["Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio"]

menu = tk.Menu(root)
root.config(menu=menu)

menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Proyects", menu=menu_archivo)
menu_archivo.add_command(label='Agree Proyect', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Create New', command=crear_nuevo_proyecto)
menu_archivo.add_command(label="Push Update Github", command=push_actualizaciones_github)
menu_archivo.add_command(label='Delete Proyect', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][4]))
menu_archivo.add_command(label="Generate Report", command=generar_informe)

menu_settings = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Settings", menu=menu_settings)
menu_settings.add_command(label="Config Editor", command=config_editors)
menu_settings.add_command(label="Github", command=config_github)
menu_settings.add_command(label="Terminal", command=select_terminal)
menu_settings.add_command(label="Theme", command=config_theme)

nombre_label = ttk.Label(root, text="Name:")
nombre_label.grid(row=1, column=0, pady=5, padx=5)

nombre_entry = ttk.Entry(root, width=100)
nombre_entry.grid(row=1, column=1, pady=5, padx=5)

descripcion_label = ttk.Label(root, text='Description:')
descripcion_label.grid(row=2, column=0, padx=5, pady=5)

descripcion_entry = ttk.Entry(root, width=100)
descripcion_entry.grid(row=2, column=1, pady=5, padx=5)

repo_label = ttk.Label(root, text="Repository URL:")
repo_label.grid(row=3, column=0, padx=5, pady=5)

repo_entry = ttk.Entry(root, width=100)
repo_entry.grid(row=3, column=1, pady=5, padx=5)

depen_label = ttk.Label(root, text="Dependencies:")
depen_label.grid(row=4, column=0, pady=5, padx=5)

depen_entry = ttk.Entry(root, width=100)
depen_entry.grid(row=4, column=1, pady=5, padx=5)

tree = ttk.Treeview(root, columns=('ID', 'Nombre', 'Descripcion', 'Lenguaje', 'Ruta', 'Repositorio'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Name')
tree.heading('Descripcion', text='Description')
tree.heading('Lenguaje', text='Lenguaje')
tree.heading('Ruta', text='Path')
tree.heading('Repositorio', text='Repository')
tree.grid(row=5, columnspan=2, pady=5, padx=5)

scrollbar_y = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
scrollbar_y.grid(row=5, column=2, sticky='ns')

tree.configure(yscrollcommand=scrollbar_y.set)

selected_editor = tk.StringVar()
editor_options = [
        "Select a Editor",
        "Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio"
    ]
selected_editor.set(editor_options[0])
editor_menu = ttk.OptionMenu(root, selected_editor, *editor_options)
editor_menu.grid(row=9, column=0, padx=5, pady=5, sticky="sw")

tree.bind("<Button-3>", show_context_menu)
tree.bind("<Double-1>", abrir_repositorio)
tree.bind("<<TreeviewSelect>>", on_project_select)

btn_abrir = ttk.Button(root, text='Open Proyect', command=lambda: abrir_threading(tree.item(tree.selection())['values'][4], selected_editor.get()))
btn_abrir.grid(row=9, columnspan=2, pady=5, padx=5)

btn_repos = ttk.Button(root, text="Open Github Repository", command=abrir_proyecto_github)
btn_repos.grid(row=9, column=1, pady=5, padx=5)

btn_install = ttk.Button(root, text="Install dependencies", command=lambda: install_librarys(tree.item(tree.selection())['values'][3]))
btn_install.grid(row=4, column=1, padx=5, pady=5, sticky="e")

version_label = ttk.Label(root, text=version)
version_label.grid(row=9, column=1, pady=5, padx=5, sticky="se")


crear_base_datos()

mostrar_proyectos()

root.mainloop()
