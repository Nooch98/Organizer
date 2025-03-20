import tkinter as tk
import sys
import ttkbootstrap as ttk
import requests
import os
import webbrowser
import subprocess
import markdown
import pygments.lexers
import base64
import markdown2
import json

from ttkbootstrap.constants import *
from tkinter import messagebox as ms, filedialog, simpledialog
from chlorophyll import CodeView
from tkhtmlview import HTMLLabel
from ttkbootstrap.widgets import Progressbar
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

main_version = "Version: 0.0.1"
title_version = "_V.0.0.1"
str_title_version = str(title_version)
version = str(main_version)
issue_list = None

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def search_github_key():
    config = load_config()

    if "GITHUB_TOKEN" in config and is_github_token_valid(config["GITHUB_TOKEN"]):
        return config["GITHUB_TOKEN"]

    posible_names = ["GITHUB", "TOKEN", "API", "KEY", "SECRET"]
    for name_var, valor in os.environ.items():
        if any(clave in name_var.upper() for clave in posible_names):
            if is_github_token_valid(valor):
                config["GITHUB_TOKEN"] = valor
                save_config(config)
                return valor
    
    ms.showwarning("⚠️ GitHub API Key Not Found", 
                   "No API Key found. Please enter one to continue.")

    while True:
        token = simpledialog.askstring("🔑 Enter GitHub API Key", 
                                       "Enter your GitHub API Key:", show="*")

        if not token:
            ms.showerror("❌ Error", "No API Key entered.")
            return None

        if is_github_token_valid(token):
            config["GITHUB_TOKEN"] = token
            save_config(config)
            return token
        else:
            ms.showerror("❌ Error", "Invalid API Key. Try again.")

def is_github_token_valid(token):

    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def obtain_github_repos():
    url = "https://api.github.com/user/repos"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        ms.showerror("❌ Error", f"No se pudieron obtener los repositorios: {str(e)}")
        return []

def obtain_github_user():
    url = "https://api.github.com/user"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        return response.json()["login"]
    except requests.exceptions.RequestException as e:
        ms.showerror("❌ Error", f"No se pudo obtener el usuario de GitHub: {str(e)}")
        return None

GITHUB_TOKEN = search_github_key()
GITHUB_USER = obtain_github_user() if GITHUB_TOKEN else None

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

def show_github_repos():
    for item in projectstree.get_children():
        projectstree.delete(item)
        
    repos = obtain_github_repos()
    starred_repos = obtain_starred_repos()
    
    for repo in repos:
        projectstree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], repo["visibility"], repo["clone_url"], "📁 Propio"))
        
    for repo in starred_repos:
        projectstree.insert("", "end", values=(repo["name"], repo["description"], repo["language"], repo["html_url"], "⭐ Destacado", repo["clone_url"], "⭐ Favorito"))
    
def menu_contextual(event):
    item = projectstree.identify_row(event.y)
    if item:
        projectstree.selection_set(item)
        context_menu.post(event.x_root, event.y_root)
    else:
        projectstree.selection_remove(projectstree.selection())
        
def open_repository(event):
    item = projectstree.selection()
    if item:
        repo_url = projectstree.item(item, "values")[3]
        webbrowser.open_new(repo_url)
        
def clone_repository():
    try:
        item = projectstree.selection()
        clone_url = projectstree.item(item, "values")[5]
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
        ms.showerror("ERROR", f"Can't create repository: {e}")
        
def delete_repository_github(name):
    user = GITHUB_USER
    url = f"https://api.github.com/repos/{user}/{name}"
    
    try:
        response = requests.delete(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                 "Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        ms.showinfo("SUCCESS", f"Repository '{name}' deleted successfully.")
    except requests.exceptions.RequestException as e:
        ms.showerror("ERROR", f"Can't delete the repository: {e}")
            
def edit_repository1(name):
        notebook.select(edit_frame)
        user = GITHUB_USER
        url = f"https://api.github.com/repos/{user}/{name}"

        try:
            response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            response.raise_for_status()
            repo_data = response.json()
        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Can't obtain the repository data: {e}")
            return

        def guardar_cambios():
            nuevo_nombre = nombre_var.get().strip()
            nueva_descripcion = descripcion_var.get().strip()
            nueva_visibilidad = visibilidad_var.get()

            data = {
                "name": nuevo_nombre,
                "description": nueva_descripcion,
                "private": nueva_visibilidad == "Privado"
            }

            try:
                response = requests.patch(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                                        "Accept": "application/vnd.github.v3+json"}, json=data)
                response.raise_for_status()
                ms.showinfo("Éxito", f"Repository '{name}' updated successfully.")
                for widget in edit_frame.winfo_children():
                    widget.destroy()
                notebook.select(mygithub_frame)
                show_github_repos()
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Error updating the repository: {e}")
                
        ttk.Label(edit_frame, text="Repository Name:", style="TLabel").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        nombre_var = tk.StringVar(value=repo_data.get("name", ""))
        ttk.Entry(edit_frame, textvariable=nombre_var, width=40, style="TEntry").grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(edit_frame, text="Description:", style="TLabel").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        descripcion_var = tk.StringVar(value=repo_data.get("description", ""))
        ttk.Entry(edit_frame, textvariable=descripcion_var, width=40, style="TEntry").grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(edit_frame, text="Visibilidad:", style="TLabel").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        visibilidad_var = tk.StringVar(value="Privado" if repo_data.get("private", False) else "Público")
        ttk.OptionMenu(edit_frame, visibilidad_var, "Público", "Privado", style="TMenubutton").grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ttk.Button(edit_frame, text="Save Changes", command=guardar_cambios, style="Success.TButton").grid(row=3, columnspan=2, pady=15)
        
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
                release_combobox.current(0)
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

                populate_asset_tree(release_id)
                update_preview()
            else:
                ms.showerror("Error", f"Release with ID {release_id} not found.")
                
        def populate_asset_tree(release_id):
            asset_tree.delete(*asset_tree.get_children())
            assets = fetch_release_assets(release_id)

            for asset in assets:
                asset_tree.insert("", "end", values=(asset["name"], asset["browser_download_url"], asset["id"]))

        def update_preview(event=None, clear=False):
            try:
                if clear:
                    preview_label.set_html("")
                else:
                    raw_text = description_text.get("1.0", "end-1c")
                    html_content = markdown.markdown(raw_text)
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

            if release_id:
                url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/releases/{release_id}"
                method = "PATCH"
            else:
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
            selected_items = asset_tree.selection()

            if not selected_items:
                ms.showerror("Error", "No file selected.")
                return

            release_id = current_release_id.get()
            if not release_id:
                ms.showerror("Error", "No release selected.")
                return

            for item in selected_items:
                file_name, file_url, asset_id = asset_tree.item(item, "values")
                try:
                    delete_file(asset_id)
                    asset_tree.delete(item)
                except Exception as e:
                    ms.showerror("Error", f"Failed to delete {file_name}: {e}")

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
            selected_index = release_combobox.current()
            if selected_index == -1:
                ms.showerror("Error", "No release selected.")
                return

            release = releases[selected_index]
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
                reload_releases()
            except requests.exceptions.RequestException as e:
                ms.showerror("Error", f"Can't delete the release: {e}")
                
        releases = fetch_releases()
        current_release_id = tk.StringVar()
        lexer = pygments.lexers.get_lexer_by_name("markdown")

        release_frame.grid_columnconfigure(0, weight=2)
        release_frame.grid_columnconfigure(1, weight=3)
        release_frame.grid_columnconfigure(2, weight=2)
        release_frame.grid_rowconfigure(1, weight=1)
        release_frame.grid_rowconfigure(3, weight=1) 

        select_frame = ttk.LabelFrame(release_frame, text="Select Release", padding=10, bootstyle=INFO)
        select_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=5, pady=5)

        ttk.Label(select_frame, text="Select Release:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        release_combobox = ttk.Combobox(select_frame, state="readonly", width=50)
        release_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        release_combobox.bind("<<ComboboxSelected>>", on_release_select)

        context_menu = tk.Menu(select_frame, tearoff=0)
        context_menu.add_command(label="Delete Release", command=delete_release)

        ttk.Label(select_frame, text="Attached Files:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        asset_tree = ttk.Treeview(select_frame, columns=("Name", "URL"), show="headings", height=8)
        asset_tree.heading("Name", text="File Name")
        asset_tree.heading("URL", text="Download URL")
        asset_tree.column("Name", width=250, anchor="w")
        asset_tree.column("URL", width=400, anchor="w")
        asset_tree.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        button_frame = ttk.Frame(select_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        ttk.Button(button_frame, text="New Release", command=lambda: [reset_form(), release_combobox.set('')], bootstyle=PRIMARY).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Add File(s)", command=add_files, bootstyle=PRIMARY).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Remove Selected File(s)", command=remove_files, bootstyle=DANGER).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        editor_frame = ttk.LabelFrame(release_frame, text="Release Editor", padding=10, bootstyle=SUCCESS)
        editor_frame.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=5)

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

        ttk.Label(editor_frame, text="Preview:", font=("Arial", 10)).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        preview_label = HTMLLabel(editor_frame, background="white")
        preview_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        options_frame = ttk.Frame(editor_frame)
        options_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        draft_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Mark as Draft", variable=draft_var, bootstyle=INFO).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        prerelease_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Mark as Pre-release", variable=prerelease_var, bootstyle=INFO).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(release_frame, text="✅ Save Release", command=save_release).grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")

        populate_release_combobox()
        
def show_github_comits1(repo_name):
    notebook.select(commits_frame)

    frame = ttk.Frame(commits_frame)
    frame.pack(expand=True, fill="both")

    paned_window = ttk.Panedwindow(frame, orient="horizontal")
    paned_window.pack(expand=True, fill="both")

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

    changes_frame = ttk.Labelframe(commits1_frame, text="Code Changes", padding=10, bootstyle=INFO)
    changes_frame.pack(expand=True, fill="both", padx=5, pady=5)

    diff_viewer = CodeView(changes_frame, wrap="word", height=10)
    diff_viewer.pack(expand=True, fill="both", padx=10, pady=10)
    
    lines_added_label = ttk.Label(changes_frame, text="Lines Added: 0 | ", bootstyle="success")
    lines_added_label.pack(pady=5, side="left")

    lines_deleted_label = ttk.Label(changes_frame, text="Lines Deleted: 0", bootstyle="danger")
    lines_deleted_label.pack(pady=5, side="left")

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
            total_additions = 0
            total_deletions = 0

            for file in files:
                if file.get("filename") == file_path:
                    patch = file.get("patch", "No changes found.")
                    lexer = pygments.lexers.get_lexer_for_filename(file_path)
                    diff_viewer.config(lexer=lexer)
                    diff_viewer.insert("1.0", patch)

                    total_additions += file.get("additions", 0)
                    total_deletions += file.get("deletions", 0)

            lines_added_label.config(text=f"Lines Added: {total_additions} | ")
            lines_deleted_label.config(text=f"Lines Deleted: {total_deletions}")

        except requests.exceptions.RequestException as e:
            ms.showerror("Error", f"Unable to fetch commit changes: {e}")

    file_tree.bind("<Double-Button-1>", load_commit_history)

    commit_tree.bind("<Double-Button-1>", load_commit_changes)

    load_files()

def update_file_content(repo_name, file_path, new_content, commit_message):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        file_data = response.json()
        sha = file_data["sha"]

        data = {
            "message": commit_message,
            "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }

        response = requests.put(url, headers={"Authorization": f"token {GITHUB_TOKEN}",
                                              "Accept": "application/vnd.github.v3+json"},
                                json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error al actualizar el archivo: {e}")

def view_file_contents(repo_name, file_path):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{file_path}"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        file_data = response.json()
        file_content = base64.b64decode(file_data["content"]).decode("utf-8")
        return file_content
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Error getting the file content: {e}")
        return ""
    
def list_repo_contents(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents"
    try:
        response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        response.raise_for_status()
        contents = response.json()
        return contents
    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"Could not get the contents of the repository: {e}")
        return []

def open_repo_files1(repo_name):
        for widget in file_frame.winfo_children():
            widget.destroy()
            
        notebook.select(file_frame)
        
        file_list_frame = ttk.Frame(file_frame, padding=(5, 10))
        file_list_frame.pack(side="left", fill="y", padx=5, pady=5)

        file_list = ttk.Treeview(file_list_frame, columns=("name", "type"), show="headings", selectmode="browse", style="success.Treeview")
        file_list.heading("name", text="Name", anchor="w")
        file_list.heading("type", text="Type", anchor="w")
        file_list.column("name", anchor="w", width=250)
        file_list.column("type", anchor="w", width=100)
        file_list.pack(expand=True, fill="y", padx=5)

        separator = ttk.Separator(file_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=5)

        editor_frame = ttk.Frame(file_frame, padding=(10, 5))
        editor_frame.pack(side="right", expand=True, fill="both", padx=5, pady=5)

        text_editor = CodeView(editor_frame, wrap="word", width=150, height=20)
        text_editor.pack(expand=True, fill="both", padx=10, pady=10)

        ttk.Label(editor_frame, text="Commit Message:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        commit_var = tk.StringVar()
        commit_entry = ttk.Entry(editor_frame, textvariable=commit_var, width=150, bootstyle=PRIMARY)
        commit_entry.pack(padx=5, pady=5)

        save_button = ttk.Button(editor_frame, text="Save Changes", command=lambda: save_changes1(repo_name), width=20, bootstyle=SUCCESS)
        save_button.pack(pady=10)

        current_file = tk.StringVar()
        
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

        def save_changes1(repo_name):
            file_path = current_file.get()
            if not file_path:
                ms.showerror("Error", "Don't have selected file to save.")
                return
            new_content = text_editor.get("1.0", "end-1c")
            commit_message = commit_var.get().strip()
            if not commit_message:
                ms.showerror("Error", "The commit message cannot be empty.")
                return
            update_file_content(repo_name, file_path, new_content, commit_message)
            ms.showinfo("Éxito", f"File '{file_path}' saved successfully.")

        contents = list_repo_contents(repo_name)
        for item in contents:
            name = item.get("name", "Unknown")
            path = item.get("path", "")
            content_type = item.get("type", "Unknown")
            if content_type == "file":
                file_list.insert("", "end", values=(name, content_type))

        def on_file_select1(event):
            selected_item = file_list.selection()
            if selected_item:
                file_path = file_list.item(selected_item, "values")[0]
                load_file_content1(file_path)

        file_list.bind("<<TreeviewSelect>>", on_file_select1)
        
def show_repo_stats(repo_name):
    notebook.select(stats_frame)
    
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

        readme_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/readme"
        response_readme = requests.get(readme_url, headers=headers)

        if response_readme.status_code == 200:
            readme_data = response_readme.json()
            readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8")
            readme_html = markdown.markdown(readme_content)
        else:
            readme_html = f"<p>{description}</p>" 

        readme_frame = ttk.LabelFrame(stats_frame, text="📖 README / Descripción", padding=10, bootstyle="info")
        readme_frame.pack(fill="both", padx=10, pady=5)

        readme_label = HTMLLabel(readme_frame, html=readme_html, background="white", padx=5, pady=5)
        readme_label.pack(expand=True, fill="both")

        ttk.Separator(stats_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

        popularity_frame = ttk.LabelFrame(stats_frame, text="🌟 Popularidad", padding=10, bootstyle="primary")
        popularity_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(popularity_frame, text=f"⭐ Estrellas: {repo_data.get('stargazers_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(popularity_frame, text=f"🍴 Forks: {repo_data.get('forks_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(popularity_frame, text=f"👀 Watchers: {repo_data.get('watchers_count', 0)}", font=("Arial", 12, "bold")).pack(anchor="w")

        ttk.Separator(stats_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

        traffic_frame = ttk.LabelFrame(stats_frame, text="📈 Tráfico", padding=10, bootstyle="success")
        traffic_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(traffic_frame, text=f"📥 Descargas de Releases: {get_total_downloads(repo_name, headers)}", font=("Arial", 12, "bold")).pack(anchor="w")
        ttk.Label(traffic_frame, text=f"🔄 Clones del Repo (últimos 14 días): {get_total_clones(repo_name, headers)}", font=("Arial", 12, "bold")).pack(anchor="w")

    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"No se pudieron obtener las estadísticas del repositorio: {e}")

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

def get_total_clones(repo_name, headers):
    clones_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/traffic/clones"
    response_clones = requests.get(clones_url, headers=headers)
    if response_clones.status_code == 200:
        clone_data = response_clones.json()
        return clone_data.get("count", 0)
    return 0

def show_repo_issues(repo_name):
    global issue_list
    notebook.select(issues_frame)

    for widget in issues_frame.winfo_children():
        widget.destroy()

    ttk.Label(issues_frame, text=f"🐞 Issues de {repo_name}", font=("Arial", 14, "bold")).pack(pady=10)

    if not issue_list:
        issue_list = ttk.Treeview(issues_frame, columns=("Number", "Title", "State", "URL"), show="headings")
        issue_list.heading("Number", text="#")
        issue_list.heading("Title", text="Title")
        issue_list.heading("State", text="State")
        issue_list.heading("URL", text="URL")

        issue_list.column("Number", width=50)
        issue_list.column("Title", width=300)
        issue_list.column("State", width=100)
        issue_list.column("URL", width=250)

        issue_list.pack(expand=True, fill="both", padx=5, pady=5)
        issue_context_menu = tk.Menu(root, tearoff=0)
        issue_context_menu.add_command(label="✅ Close Issue", command=lambda: close_selected_issue(issue_list, repo_name))
        issue_context_menu.add_command(label="💬 Add Comment", command=lambda: comment_selected_issue(issue_list, repo_name))

        issue_list.bind("<Button-3>", lambda event: issue_context_menu.post(event.x_root, event.y_root))
        
    def comment_selected_issue(issue_list, repo_name):
        selected_item = issue_list.selection()
        if selected_item:
            issue_number = issue_list.item(selected_item, "values")[0]
            comment_on_issue(repo_name, issue_number)
            
    def close_selected_issue(issue_list, repo_name):
        selected_item = issue_list.selection()
        if selected_item:
            issue_number = issue_list.item(selected_item, "values")[0]
            close_issue(repo_name, issue_number)
            issue_list.delete(selected_item)

    show_issues(repo_name)

def close_issue(repo_name, issue_number):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues/{issue_number}"
    response = requests.patch(url, json={"state": "closed"},
                              headers={"Authorization": f"token {GITHUB_TOKEN}"})

    if response.status_code == 200:
        ms.showinfo("✅ Success", f"Issue #{issue_number} closed successfully!")
    else:
        ms.showerror("❌ Error", "Failed to close issue.")

def comment_on_issue(repo_name, issue_number):
    comment_text = simpledialog.askstring("💬 Add Comment", "Enter your comment:")

    if not comment_text:
        return

    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues/{issue_number}/comments"
    response = requests.post(url, json={"body": comment_text},
                             headers={"Authorization": f"token {GITHUB_TOKEN}"})

    if response.status_code == 201:
        ms.showinfo("✅ Success", "Comment added successfully!")
    else:
        ms.showerror("❌ Error", "Failed to add comment.")
    
def show_issues(repo_name):
    global issue_list

    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        issues = response.json()

        # Limpiar el Treeview antes de mostrar nuevos resultados
        for item in issue_list.get_children():
            issue_list.delete(item)

        # Verificar si no hay issues
        if not issues:
            # Si no hay issues, mostrar un mensaje y un botón para crear uno nuevo
            ttk.Label(issues_frame, text="No hay issues en este repositorio. ¿Quieres crear uno?", font=("Arial", 12)).pack(pady=10)
            create_issue_button = ttk.Button(issues_frame, text="Crear nuevo issue", command=lambda: create_new_issue(repo_name))
            create_issue_button.pack(pady=10)
        else:
            # Si hay issues, agregarlos al Treeview
            for issue in issues:
                issue_list.insert("", "end", values=(
                    issue['number'],
                    issue['title'],
                    issue['state'],
                    issue['html_url']
                ))

    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"No se pudieron obtener los issues: {e}")
        
def create_new_issue(repo_name):
    # Crear un cuadro de entrada para el título del issue
    def submit_new_issue():
        title = title_entry.get()
        description = description_entry.get("1.0", "end-1c")  # Obtener texto de la caja de descripción

        if title and description:
            # Crear un issue usando la API de GitHub
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            data = {
                "title": title,
                "body": description
            }
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                ms.showinfo("Éxito", "Issue creado exitosamente.")
                # Recargar los issues después de crear uno nuevo
                show_issues(repo_name)
                create_issue_window.destroy()
            else:
                ms.showerror("Error", "No se pudo crear el issue.")
        else:
            ms.showerror("Error", "El título y la descripción son obligatorios.")

    # Crear una ventana para ingresar el título y la descripción
    create_issue_window = tk.Toplevel(root)
    create_issue_window.title("Crear Nuevo Issue")
    create_issue_window.geometry("400x300")

    ttk.Label(create_issue_window, text="Título del Issue").pack(pady=5)
    title_entry = ttk.Entry(create_issue_window, width=50)
    title_entry.pack(pady=5)

    ttk.Label(create_issue_window, text="Descripción del Issue").pack(pady=5)
    description_entry = tk.Text(create_issue_window, width=50, height=6)
    description_entry.pack(pady=5)

    submit_button = ttk.Button(create_issue_window, text="Crear Issue", command=submit_new_issue)
    submit_button.pack(pady=10)

def filter_repositories(event):
    query = search_var.get().lower()
    for item in projectstree.get_children():
        repo_name = projectstree.item(item, "values")[0].lower()
        if query in repo_name:
            projectstree.item(item, open=True)
            projectstree.selection_set(item)
        else:
            projectstree.selection_remove(item)
            
def backup_repository(repo_name):
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/zipball"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        save_path = filedialog.asksaveasfilename(initialfile=f"{repo_name}.zip", defaultextension=".zip", filetypes=[("ZIP Files", "*.zip")])
        if not save_path:
            return

        progress_window = tk.Toplevel(root)
        progress_window.title("Creando Backup...")
        ttk.Label(progress_window, text=f"Creando backup de {repo_name}...").pack(pady=5)
        progress = Progressbar(progress_window, mode="determinate", length=300)
        progress.pack(padx=10, pady=10)

        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress["value"] = (downloaded_size / total_size) * 100
                    else:
                        progress["value"] = 100
                    progress_window.update_idletasks()

        progress["value"] = 100
        progress_window.destroy()
        ms.showinfo("Éxito", f"Backup de '{repo_name}' guardado en {save_path}")

    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"No se pudo crear el backup: {e}")

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

        progress_window = tk.Toplevel(root)
        progress_window.title("Descargando...")
        ttk.Label(progress_window, text=f"Descargando {file_path}...").pack(pady=5)
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
        ms.showinfo("Éxito", f"Archivo '{file_path}' descargado correctamente.")

    except requests.exceptions.RequestException as e:
        ms.showerror("Error", f"No se pudo descargar el archivo: {e}")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    except Exception:
        base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

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
    
    search_context_menu = tk.Menu(root, tearoff=0)
    search_context_menu.add_command(label="⭐ Agregar a Favoritos", command=lambda: star_repository(search_tree.item(search_tree.selection()[0], "values")[0], search_tree.item(search_tree.selection()[0], "values")[1]))
    #search_context_menu.add_command(label="🛠️ Clonar Repositorio", command=lambda: clone_repository_from_search())

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

        file_window = tk.Toplevel(root)
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

def create_issue(repo_name):
    issue_title = simpledialog.askstring("🐞 New Issue", "Enter issue title:")
    issue_body = simpledialog.askstring("🐞 Issue Description", "Enter issue description:")

    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/issues"
    response = requests.post(url, json={"title": issue_title, "body": issue_body},
                             headers={"Authorization": f"token {GITHUB_TOKEN}"})

    if response.status_code == 201:
        ms.showinfo("✅ Success", "Issue created successfully!")
    else:
        ms.showerror("❌ Error", "Failed to create issue.")
   
def show_help():
    help_window = tk.Toplevel(root)
    help_window.iconbitmap(path)
    
    ttk.Label(help_window, text="📖 Ayuda - Cómo Usar la Aplicación", font=("Arial", 14, "bold")).pack(pady=5)

    # Verificar si el archivo existe
    if os.path.exists("Help.md"):
        with open("Help.md", "r", encoding="utf-8") as f:
            md_content = f.read()
    else:
        md_content = "# ❌ Error\nNo se encontró el archivo 'Help.md'."

    # Convertir Markdown a HTML
    html_content = markdown2.markdown(md_content)

    # Mostrar el contenido en un Label HTML
    html_label = HTMLLabel(help_window, html=html_content, background="white", padx=10, pady=10)
    html_label.pack(expand=True, fill="both", padx=10, pady=10)

path = resource_path("github_control.ico")
root = ttk.Window(title=f"Github Control{str_title_version}", themename="darkly")
root.iconbitmap(path)
root.resizable(True, True)

menu = tk.Menu(root, tearoff=0)
root.config(menu=menu)
help_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label='help', menu=help_menu)
help_menu.add_cascade(label='Help', command=show_help)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

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

columns = ("Name", "Description", "Language", "URL", "Visibility", "Clone URL")
projectstree = ttk.Treeview(mygithub_frame, columns=columns, show="headings", height=20, bootstyle='primary')
projectstree.heading("Name", text="Name")
projectstree.heading("Description", text="Description")
projectstree.heading("Language", text="Language")
projectstree.heading("URL", text="URL")
projectstree.heading("Visibility", text="Visibility")
projectstree.heading("Clone URL", text="Clone URL")

scrollb = ttk.Scrollbar(mygithub_frame, orient="vertical", command=projectstree.yview, bootstyle='primary-rounded')
projectstree.configure(yscrollcommand=scrollb.set)
scrollb.pack(side=RIGHT, fill=Y, padx=5)

projectstree.pack(expand=True, fill="both", padx=5, pady=5)
projectstree.bind("<Double-1>", open_repository)
projectstree.bind("<Button-3>", menu_contextual)

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="🗑️Delete Repository", command=lambda: delete_repository_github(projectstree.item(projectstree.selection(), "values")[0]))
context_menu.add_command(label="✏️ Edit Repository", command=lambda: edit_repository1(projectstree.item(projectstree.selection()[0], "values")[0]))
context_menu.add_command(label="🚀 Github Releases", command=lambda: manage_github_release1(projectstree.item(projectstree.selection(), "values")[0]))
context_menu.add_command(label="🔄 Commits History", command=lambda: show_github_comits1(projectstree.item(projectstree.selection()[0], "values")[0]))
context_menu.add_command(label="⭐ Quit Star", command=lambda: unstar_repository(projectstree.item(projectstree.selection()[0], "values")[0], projectstree.item(projectstree.selection()[0], "values")[3].split('/')[-2]))
context_menu.add_command(label="➕ Create New Repository", command=create_repository_github)
context_menu.add_command(label="📂 Clone Repository", command=clone_repository)
context_menu.add_command(label="🗂️View Files", command=lambda: open_repo_files1(projectstree.item(projectstree.selection()[0], "values")[0]))
context_menu.add_command(label="📊 View Statistics", command=lambda: show_repo_stats(projectstree.item(projectstree.selection()[0], "values")[0]))
context_menu.add_command(label="📦 Create Backup", command=lambda: backup_repository(projectstree.item(projectstree.selection()[0], "values")[0]))
context_menu.add_command(label="🐞 View Issues", command=lambda: show_repo_issues(projectstree.item(projectstree.selection()[0], "values")[0]))

search_var = tk.StringVar()
search_entry = ttk.Entry(mygithub_frame, textvariable=search_var, width=40)
search_entry.pack(pady=5)
search_entry.bind("<KeyRelease>", filter_repositories)

version_label = ttk.Label(root, text=f'{version}', bootstyle='info')
version_label.pack(side='bottom', fill='x', padx=5, pady=5)

show_github_repos()
search_repositories()
search_code_on_github()
root.mainloop()
