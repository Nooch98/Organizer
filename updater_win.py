import os
import sys
import subprocess
import tkinter as tk
from ttkthemes import ThemedTk
from tkinter import ttk, messagebox as ms

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def update_organizer():
    subprocess.Popen("Organizer_setup.exe")
    main.after(1000, main.destroy())

# Configuración de la ventana principal
path = resource_path("software.ico")
main = ThemedTk(theme="arc")
main.title("Organizer Update")
main.iconbitmap(path)
frame = ttk.Frame(main)
frame.pack(expand=True, fill="both")

update_lbl = ttk.Label(frame, text="Update Organizer", font=("Cascadia", 20))
update_lbl.grid(row=0, padx=2, pady=2, columnspan=2)

update_btn = ttk.Button(frame, text="Update", command=lambda: update_organizer())
update_btn.grid(row=1, columnspan=2, padx=2, pady=2)

update_progress = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=300)
update_progress.grid(row=2, columnspan=2, padx=2, pady=2)

main.mainloop()
