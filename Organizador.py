import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as ms
from tkinter import ttk
from turtle import heading

from ttkthemes import ThemedTk

icono = "software.ico"

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
    
def abrir_proyecto(ruta):
    os.system('code "{}"'.format(ruta))
    
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

root = ThemedTk(theme='aqua')
root.title('Organizador de Proyectos')
root.geometry("835x380")
root.iconbitmap(icono)

menu = tk.Menu(root)
root.config(menu=menu)

menu_archivo = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Proyectos", menu=menu_archivo)
menu_archivo.add_command(label='Agregar Proyecto', command=agregar_proyecto_existente)
menu_archivo.add_command(label='Crear Nuevo', command=crear_nuevo_proyecto)
menu_archivo.add_command(label='Eliminar Proyecto', command=lambda: eliminar_proyecto(tree.item(tree.selection())['values'][0], tree.item(tree.selection())['values'][3]))

nombre_label = ttk.Label(root, text="Nombre:")
nombre_label.grid(row=0, column=0, pady=5, padx=5)

nombre_entry = ttk.Entry(root, width=100)
nombre_entry.grid(row=0, column=1, pady=5, padx=5)

descripcion_label = ttk.Label(root, text='Descripcion:')
descripcion_label.grid(row=1, column=0, padx=5, pady=5)

descripcion_entry = ttk.Entry(root, width=100)
descripcion_entry.grid(row=1, column=1, pady=5, padx=5)


tree = ttk.Treeview(root, columns=('ID', 'Nombre', 'Descripcion', 'Ruta'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Nombre')
tree.heading('Descripcion', text='Descripcion')
tree.heading('Ruta', text='Ruta')
tree.grid(row=3, columnspan=2, pady=5, padx=5)

scrollbar_y = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
scrollbar_y.grid(row=3, column=2, sticky='ns')

tree.configure(yscrollcommand=scrollbar_y.set)

btn_abrir = ttk.Button(root, text='Abrir Proyecto', command=lambda: abrir_proyecto(tree.item(tree.selection())['values'][3]))
btn_abrir.grid(row=8, columnspan=2, pady=5, padx=5)


crear_base_datos()

mostrar_proyectos()

root.mainloop()



