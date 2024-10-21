import os
import sys
import zipfile
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
    current_directory = os.getcwd()
    zip_file_path = os.path.join(current_directory, "Organizer_win.zip")
    
    if zipfile.is_zipfile(zip_file_path):
        os.remove("Organizer_win.exe")
        
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            file_list = zip_ref.infolist()
            total_files = len(file_list)
            
            update_progress["maximum"] = total_files

            for i, file in enumerate(file_list, 1):
                zip_ref.extract(file, current_directory)
                
                update_progress["value"] = i
                main.update_idletasks()
            
            ms.showinfo("Update", "Update complete opening Organizer...")
            subprocess.Popen("Organizer_win.exe")
            main.after(1000, main.destroy())

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
