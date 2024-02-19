import json
import os
import shutil
import sqlite3
import subprocess
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog
from tkinter import messagebox as ms
from tkinter import scrolledtext, ttk
from turtle import heading

from ttkthemes import ThemedTk

main_version = "ver.1.1"
version = str(main_version)

icono = "software.ico"
archivo_configuracion_editores = "configuracion_editores.json"

def crear_base_datos():
    conn = sqlite3.connect('proyectos.db')
    
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        descripcion TEXT,
        ruta TEXT,
        repo TEXT
        )''')
    
    conn.close()
    
def insertar_proyecto(nombre, descripcion, ruta, repo):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO proyectos (nombre, descripcion, ruta, repo)
                   VALUES (?, ?, ?, ?)''', (nombre, descripcion, ruta, repo))
    
    conn.commit()
    conn.close()
    mostrar_proyectos()
    
def abrir_proyecto(ruta, editor):
    configuracion_editores = cargar_configuracion_editores()

    if configuracion_editores and editor in configuracion_editores:
        ruta_editor = configuracion_editores[editor]
        subprocess.run([ruta_editor, ruta], check=True)
    else:
        if editor == "Visual Studio Code":
            subprocess.run(['code', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Sublime Text":
            subprocess.run(['subl', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Atom":
            subprocess.run(['atom', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Vim":
            subprocess.run(['vim', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Emacs":
            subprocess.run(['emacs', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Notepad++":
            subprocess.run(['notepad++', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Brackets":
            subprocess.run(['brackets', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "TextMate":
            subprocess.run(['mate', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Geany":
            subprocess.run(['geany', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "gedit":
            subprocess.run(['gedit', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Nano":
            subprocess.run(['nano', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Kate":
            subprocess.run(['kate', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Bluefish":
            subprocess.run(['bluefish', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Eclipse":
            subprocess.run(['eclipse', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "IntelliJ IDEA":
            subprocess.run(['idea', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "PyCharm":
            subprocess.run(['pycharm', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Visual Studio":
            subprocess.run(['visualstudio', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Code::Blocks":
            subprocess.run(['codeblocks', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "NetBeans":
            subprocess.run(['netbeans', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
        elif editor == "Android Studio":
            subprocess.run(['studio', ruta], check=True)
            subprocess.run(['pwsh', '-Command', f'cd "{ruta}"'])
         
    
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

def crear_nuevo_proyecto():    
    ventana_lenguaje = tk.Toplevel(root)
    ventana_lenguaje.title("Selection lenguaje")
    
    label = ttk.Label(ventana_lenguaje, text="Select the project language:")
    label.grid(row=0, columnspan=2, pady=5, padx=5)
    
    lenguaje_options = ["Selection lenguaje", "Python", "NodeJS", "React", "Java", "JS", "C++", "C#", "TypeScript", "Ruby", "Go"]
    
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
        
def iniciar_new_proyect(lenguaje, textbox):
    nombre = nombre_entry.get()
    descripcion = descripcion_entry.get()
    repo = repo_entry.get()
    
    if lenguaje == "Python":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            os.system(f'python -m venv "{os.path.join(ruta_completa, "venv")}')
            insertar_proyecto(nombre, descripcion, ruta_completa, repo)
    elif lenguaje == "NodeJS":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            os.system(f'npm init -w "{os.path.join(ruta_completa)}" -y')
            insertar_proyecto(nombre, descripcion, ruta_completa, repo)
    elif lenguaje == "React":
        ruta_proyecto = filedialog.askdirectory()
        if ruta_proyecto:
            ruta_completa = os.path.join(ruta_proyecto, nombre)
            os.makedirs(ruta_completa, exist_ok=True)
            comando = f'npx create-react-app "{ruta_completa}" > output.txt 2>&1'
            os.system(comando)
            with open('output.txt', 'r') as f:
                output = f.read()
                textbox.insert(tk.END, output)
            insertar_proyecto(nombre, descripcion, ruta_completa, repo)
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
    
    rutas_editores = {}

    def guardar_y_cerrar():
        guardar_configuracion_editores(rutas_editores)
        config_editor.destroy()

    for i, programa in enumerate(editores_disponibles):
        label = ttk.Label(config_editor, text=programa)
        label.grid(row=i, column=0, padx=5, pady=5)
        
        entry = ttk.Entry(config_editor)
        entry.grid(row=i, column=1, padx=5, pady=5)
        
        btn = ttk.Button(config_editor, text="Agregar", command=lambda prog=programa, ent=entry: seleccionar_ruta_editor(prog, ent))
        btn.grid(row=i, column=2, padx=5, pady=5)
        
        rutas_editores[programa] = entry

    aceptar_btn = ttk.Button(config_editor, text="Aceptar", command=guardar_y_cerrar)
    aceptar_btn.grid(row=len(editores_disponibles), column=0, columnspan=3, padx=5, pady=5)

    
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
        
def cargar_configuracion_editores():
    try:
        with open(archivo_configuracion_editores, "r") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)
            return configuracion
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
        
        context_menu.post(event.x_root, event.y_root)

def abrir_repositorio(event):
    item_seleccionado = tree.item(tree.selection())
    url_repositorio = item_seleccionado['values'][4]

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
                

root = ThemedTk(theme='aqua')
root.title('Proyect Organizer')
root.geometry("1045x380")
root.iconbitmap(icono)
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
menu_archivo.add_command(label='Delete Proyect', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][3]))

menu_settings = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Settings", menu=menu_settings)
menu_settings.add_command(label="Config Editor", command=config_editors)

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


tree = ttk.Treeview(root, columns=('ID', 'Nombre', 'Descripcion', 'Ruta', 'Repositorio'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Name')
tree.heading('Descripcion', text='Description')
tree.heading('Ruta', text='Path')
tree.heading('Repositorio', text='Repository')
tree.grid(row=4, columnspan=2, pady=5, padx=5)

scrollbar_y = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
scrollbar_y.grid(row=4, column=2, sticky='ns')

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
editor_menu.grid(row=8, column=0, padx=5, pady=5, sticky="sw")

tree.bind("<Button-3>", show_context_menu)
tree.bind("<Double-1>", abrir_repositorio)

btn_abrir = ttk.Button(root, text='Open Proyect', command=lambda: abrir_proyecto(tree.item(tree.selection())['values'][3], selected_editor.get()))
btn_abrir.grid(row=8, columnspan=2, pady=5, padx=5)

btn_repos = ttk.Button(root, text="Open Github Repository", command=abrir_proyecto_github)
btn_repos.grid(row=8, column=1, pady=5, padx=5)

version_label = ttk.Label(root, text=version)
version_label.grid(row=8, column=1, pady=5, padx=5, sticky="se")


crear_base_datos()

mostrar_proyectos()

root.mainloop()
