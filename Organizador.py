import json
import os
import shutil
import sqlite3
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as ms
from tkinter import ttk
from turtle import heading

from ttkthemes import ThemedTk

icono = "software.ico"
archivo_configuracion_editores = "configuracion_editores.json"

def crear_base_datos():
    conn = sqlite3.connect('proyectos.db')
    
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY,
        nombre TEXT,
        descripcion TEXT,
        ruta TEXT
        )''')
    
    conn.close()
    
def insertar_proyecto(nombre, descripcion, ruta):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO proyectos (nombre, descripcion, ruta)
                   VALUES (?, ?, ?)''', (nombre, descripcion, ruta))
    
    conn.commit()
    conn.close()
    mostrar_proyectos()
    
def abrir_proyecto(ruta, editor):
    configuracion_editores = cargar_configuracion_editores()

    if configuracion_editores and editor in configuracion_editores:
        ruta_editor = configuracion_editores[editor]
        subprocess.run([ruta_editor, ruta], check=True)
    else:
        # Si no hay configuración o el editor no está en la configuración, usar editor por defecto
        if editor == "Visual Studio Code":
            subprocess.run(['code', ruta], check=True)
        elif editor == "Sublime Text":
            subprocess.run(['subl', ruta], check=True)
        elif editor == "Atom":
            subprocess.run(['atom', ruta], check=True)
        elif editor == "Vim":
            subprocess.run(['vim', ruta], check=True)
        elif editor == "Emacs":
            subprocess.run(['emacs', ruta], check=True)
        elif editor == "Notepad++":
            subprocess.run(['notepad++', ruta], check=True)
        elif editor == "Brackets":
            subprocess.run(['brackets', ruta], check=True)
        elif editor == "TextMate":
            subprocess.run(['mate', ruta], check=True)
        elif editor == "Geany":
            subprocess.run(['geany', ruta], check=True)
        elif editor == "gedit":
            subprocess.run(['gedit', ruta], check=True)
        elif editor == "Nano":
            subprocess.run(['nano', ruta], check=True)
        elif editor == "Kate":
            subprocess.run(['kate', ruta], check=True)
        elif editor == "Bluefish":
            subprocess.run(['bluefish', ruta], check=True)
        elif editor == "Eclipse":
            subprocess.run(['eclipse', ruta], check=True)
        elif editor == "IntelliJ IDEA":
            subprocess.run(['idea', ruta], check=True)
        elif editor == "PyCharm":
            subprocess.run(['pycharm', ruta], check=True)
        elif editor == "Visual Studio":
            subprocess.run(['visualstudio', ruta], check=True)
        elif editor == "Code::Blocks":
            subprocess.run(['codeblocks', ruta], check=True)
        elif editor == "NetBeans":
            subprocess.run(['netbeans', ruta], check=True)
        elif editor == "Android Studio":
            subprocess.run(['studio', ruta], check=True)
    
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
    ruta = filedialog.askdirectory()
    
    if ruta:
        nombre = os.path.basename(ruta)
        insertar_proyecto(nombre, descripcion, ruta)
        descripcion_entry.delete(0, tk.END)

def crear_nuevo_proyecto():
    nombre = nombre_entry.get()
    descripcion = descripcion_entry.get()
    
    ruta_proyecto = filedialog.askdirectory()
    if ruta_proyecto:
        ruta_completa = os.path.join(ruta_proyecto, nombre)
        os.makedirs(ruta_completa, exist_ok=True)
        os.system(f'python -m venv "{os.path.join(ruta_completa, "venv")}')
        insertar_proyecto(nombre, descripcion, ruta_completa)
        
        nombre_entry.delete(0, tk.END)
        descripcion_entry.delete(0, tk.END)

def eliminar_proyecto(id, ruta):
    conn = sqlite3.connect('proyectos.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM proyectos WHERE id = ?', (id,))
    conn.commit()
    shutil.rmtree(ruta)
    mostrar_proyectos()
    conn.close()
    
def aviso():
    ms.showwarning("ADVERTENCIA", "Necesitas tener los editores disponibles en el PATH para que Organizer sea capaz de ejecutarlos")
    
def seleccionar_rutas_editores():
    rutas_editores = {}
    for editor in editores_disponibles:
        respuesta = ms.askyesno("Agregar Ruta", f"¿Desea agregar la ruta del ejecutable de {editor}?")
        if respuesta:
            ruta_editor = filedialog.askopenfilename(title=f"Seleccione el ejecutable de {editor}", filetypes=[("Ejecutables", "*.exe")])
            if ruta_editor:
                rutas_editores[editor] = ruta_editor
    if rutas_editores:
        guardar_configuracion_editores(rutas_editores)
        
def guardar_configuracion_editores(rutas_editores):
    # Guardar las rutas de los editores en un archivo de configuración
    with open("configuracion_editores.json", "w") as archivo_configuracion:
        json.dump(rutas_editores, archivo_configuracion)
        
def cargar_configuracion_editores():
    try:
        with open(archivo_configuracion_editores, "r") as archivo_configuracion:
            configuracion = json.load(archivo_configuracion)
            return configuracion
    except FileNotFoundError:
        return None
                

root = ThemedTk(theme='aqua')
root.title('Organizador de Proyectos')
root.geometry("835x380")
root.iconbitmap(icono)

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
menu_settings.add_command(label="Config Editor", command=seleccionar_rutas_editores)

nombre_label = ttk.Label(root, text="Name:")
nombre_label.grid(row=1, column=0, pady=5, padx=5)

nombre_entry = ttk.Entry(root, width=100)
nombre_entry.grid(row=1, column=1, pady=5, padx=5)

descripcion_label = ttk.Label(root, text='Description:')
descripcion_label.grid(row=2, column=0, padx=5, pady=5)

descripcion_entry = ttk.Entry(root, width=100)
descripcion_entry.grid(row=2, column=1, pady=5, padx=5)


tree = ttk.Treeview(root, columns=('ID', 'Nombre', 'Descripcion', 'Ruta'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Name')
tree.heading('Descripcion', text='Description')
tree.heading('Ruta', text='Path')
tree.grid(row=3, columnspan=2, pady=5, padx=5)

scrollbar_y = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
scrollbar_y.grid(row=3, column=2, sticky='ns')

tree.configure(yscrollcommand=scrollbar_y.set)

selected_editor = tk.StringVar()
editor_options = [
        "Select one Editor",
        "Visual Studio Code", "Sublime Text", "Atom", "Vim", "Emacs", 
        "Notepad++", "Brackets", "TextMate", "Geany", "gedit", 
        "Nano", "Kate", "Bluefish", "Eclipse", "IntelliJ IDEA", 
        "PyCharm", "Visual Studio", "Code::Blocks", "NetBeans", 
        "Android Studio"
    ]
selected_editor.set(editor_options[0])
editor_menu = ttk.OptionMenu(root, selected_editor, *editor_options)
editor_menu.grid(row=0, column=0, padx=5, pady=5)

btn_abrir = ttk.Button(root, text='Open Proyect', command=lambda: abrir_proyecto(tree.item(tree.selection())['values'][3], selected_editor.get()))
btn_abrir.grid(row=8, columnspan=2, pady=5, padx=5)


crear_base_datos()

mostrar_proyectos()
aviso()

root.mainloop()
