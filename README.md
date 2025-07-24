# 📁 Organizer

Organizer is a free, open-source project management application built in Python, focused on helping developers centralize, organize, and manage all their programming projects in one place.
From project creation to task tracking, version history, and integrated code analysis — everything is at your fingertips.

![Captura de pantalla 2025-03-26 031655](https://github.com/user-attachments/assets/143898df-5730-4e97-8d78-d61f43c00aac)

---

## 🚀 Features

* **🎯 Multi-language project support**
    * Create or import projects in Python, JavaScript, Java, C++, TypeScript, and more.

* **🧠 Smart project scanner**
    * Automatically detects tasks from your source code via `TODO`, `FIX`, or `BUG` comments.

* **✅ Task manager**
    * Add, complete, or delete manual or code-detected tasks.

* **📋 Kanban board**
    * Visual task organization with customizable priority levels (To Do, In Progress, Done).

* **🔍 Fuzzy Finder**
    * Search for files within your project with real-time previews and syntax highlighting.

* **📦 Dependencies viewer**
    * Detects and displays project dependencies from files like requirements.txt, package.json, pyproject.toml, etc.

* **🧪 Language breakdown**
    * Displays a visual breakdown of file extensions and programming languages used per project.

* **🔗 Resources panel**
    * Save external links or references per project.

* **🕓 Versioning**
    * Restore old snapshots of your project structure and files.

* **🌿 Git integration**
    * Detect active branch, changed/untracked files, and recent commit messages.

* **🧩 Plugin support**
    * Easily extend the app with custom features using the built-in Plugin API.

* **📝 Quick notes (Sticky Notes)**
    * Leave short notes per project with auto-save.

* **🖥️ Favorite editor launcher**
    * Define a default editor (e.g., VS Code) to open projects instantly.

* **🧰 Customizable sidebar**
    * Choose what panels appear in your sidebar view.

* **🎨 Theme support**
    * Built-in support for custom themes using chlorophyll and ttkbootstrap.

* **📦 Organizer CLI**
    * Support for CLI commands instead of having to use the UI

---

## 📦 Organizer CLI Usage

Organizer includes a command-line interface to manage and interact with your projects directly from the terminal — ideal for scripting, automation, or power users.

> 🖥️ Available in both the Python script version and the compiled `.exe` version (In the `.exe` version you have to add it to the **PATH**)


**✅ Basic Usage**
```bash
organizer [COMMAND] [SUBCOMMAND] [OPTIONS]
```

### 📚 Available Commands

🔍 `list-projects`
List all registered projects.
```bash
organizer list-projects
```

➕ `add-project`
Add new project.
```bash
organizer add-project <NAME> <PATH> [--desc TEXT] [--lang LANG] [--repo URL]
```
Example:
```bash
organizer add-project MyApp "c:/Users/Me/Projects/MyApp" --desc "Internal Tool" --lang Python --repo https://github.com/me/myapp
```

🚀 `open-project`
Open a project by its name.
```bash
organizer open-project <NAME>
```

🗒️ `version`
Show the current version of Organizer.
```bash
organizer version
```

✅ `task` (Task Management)
```bash
organizer task [list|add|complete] <PROJECT> [ARGS...]
```
> `PROJECT` can be the full path or the project name stored in organizer

* **List task**
```bash
organizer task list <PROJECT>
```

* **Add task**
```bash
organizer task add <PROJECT> "<TASK TEXT>"
```

* **Complete task**
```bash
organizer task complete <PROJECT> <TASK_INDEX>
```

📊 `get-language`
Analyzer programing lenguages used in a project
```bash
organizer get-language <PROJECT>
```

🕑 `list-versions`
List all saved version of a project.
```bash
organizer list-versions <PROJECT>
```

🔎 Notes
* Any argument marked as `<PROJECT>` can be either:
    * The full path to a project directory, or
    * The name of a registered project.
* If a project name is ambiguous or not found, you'll get a helpful error.

💡 Examples
```bash
organizer list-projects
organizer add-project BlogApp "C:/Users/User/BlogApp" --desc "Blog CMS"
organizer open-project BlogApp
organizer task add BlogApp "Fix authentication bug"
organizer task complete BlogApp 0
organizer get-language BlogApp
organizer list-versions BlogApp
```

---

## 🔌 Plugin API

You can build and register your own extensions via the PluginAPI. Features include:

```python
api.add_menu_command(label, callback)
api.add_sidebar_widget(widget)
api.register_command("name", func, "description")
api.get_selected_project_path()
```
You can also hook into:
    * Sidebar rendering
    * Settings panel integration
    * Custom command palette entries(Ctrl + Shift + P)

---

## 🧩 Plugin System – Create and manage custom plugins

The application includes a **modular plugin system**, allowing users to enhance its functionality by writing simple Python scripts. Plugins are managed visually and use the built-in `PluginAPI`.

---

### 📁 Folder Structure

```pgsql
Organizer/
|-- plugins/
|    |-- my_plugin.py
|    |-- my_plugin_meta.json
|-- plugin_config.json
```
- All plugins go in the `plugins/` folder.
- Each plugin must implement a `register(api)` function.
- Optionally, it can have an `unregister(api)` function to clean up resources (💡 **Recommended** when disabling the plugin).

---

### ✅ Create a Basic Plugin
```python
# plugins/my_plugin.py

def register(api):
    def hello():
        print("👋 Hello from the plugin!")

    api.add_menu_command("Say Hello", hello)

def unregister(api):
    api.remove_menu_command("Say Hello")
```

---

### 📄 Add metadata (optional)
Create a metadata file named `<plugin_name>_meta.json` to display details in the visual manager:

```json
// plugins/my_plugin_meta.json
{
    "description": "Adds a greeting to the main menu.",
    "version": "1.0",
    "author": "Juan Dev"
}
```

---

### 🔄 Plugin lifecycle

| Método            | Descripción                                                                   |
| ----------------- | ----------------------------------------------------------------------------- |
| `register(api)`   | Called when the plugin loads. Here you register buttons, commands, widgets, etc. |
| `unregister(api)` | (Optional) Clean up resources, remove menus, widgets, etc.                      |

---

### 🧠 PluginAPI Reference

Available methods in the `api` object passed to your plugin:

```python
# Project access
api.get_selected_project_path()    # Returns the selected project's path
api.get_selected_node()            # Returns the selected tree node

# UI manipulation
api.add_menu_command("Label", function)
api.remove_menu_command("Label")

api.add_sidebar_widget(widget_tk)
api.add_main_button("Text", function)

# Settings integration
api.register_settings_section("Name", frame_builder)
api.unregister_settings_section("Name")

# Custom commands
api.register_command("name", function)
api.run_command("name")
```

---

### ⚙️ Tips for Plugin Development

- Always use `try/except` to avoid crashing the app

- Hot reload supported: **disable and re-enable** plugins to apply changes

- No app restart needed to test new or updated plugins

---

### 💡 Full Plugin Example
```python
# plugins/plugin_demo.py
PLUGIN_NAME = "Plugin Development Guide"
PLUGIN_DESCRIPTION = "Explains how to create plugins for Organizer with full examples."

plugin_config = {
    "enabled": True
}

_widgets = {
    "main_button": None,
    "sidebar_label": None,
    "settings_section": None,
    "doc_window": None
}

def register(api):
    from tkinter import Toplevel
    from tkinter import ttk
    from tkinterweb import HtmlFrame
    import markdown2
    from pygments.formatters import HtmlFormatter
    from pygments import highlight
    from pygments.lexers import PythonLexer
    import re

    def highlight_code_blocks(md_text):
        code_block_pattern = r"```python(.*?)```"
        matches = re.finditer(code_block_pattern, md_text, re.DOTALL)
        for match in matches:
            code = match.group(1).strip()
            highlighted = highlight(code, PythonLexer(), HtmlFormatter(nowrap=True))
            md_text = md_text.replace(match.group(0), f"<pre><code>{highlighted}</code></pre>")
        return md_text

    def open_documentation():
        if _widgets["doc_window"] and _widgets["doc_window"].winfo_exists():
            _widgets["doc_window"].lift()
            return

        top = Toplevel(api.main_window)
        top.title("How to Create a Plugin")
        top.geometry("800x600")
        _widgets["doc_window"] = top

        top.grid_rowconfigure(0, weight=1)
        top.grid_columnconfigure(0, weight=1)

        frame = HtmlFrame(top, messages_enabled = False)
        frame.grid(row=0, column=0, sticky="nsew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

def unregister(api):
    if _widgets["sidebar_label"]:
        _widgets["sidebar_label"].destroy()
        _widgets["sidebar_label"] = None

    if _widgets["main_button"]:
        _widgets["main_button"].destroy()
        _widgets["main_button"] = None

    if _widgets["doc_window"] and _widgets["doc_window"].winfo_exists():
        _widgets["doc_window"].destroy()
        _widgets["doc_window"] = None

    if _widgets["settings_section"]:
        api.unregister_settings_section(_widgets["settings_section"])
        _widgets["settings_section"] = None
```

## 🧩 Available PluginAPI Functions
```Python

api.get_selected_project_path()
  # → Get the path of the selected project in the tree.

```

```python

api.get_selected_node()
  # → Get all data of the selected tree node.

```

```python

api.add_menu_command(label, callback)
  # → Add a new command to the menu.

```

```python

api.remove_menu_command(label)
  # → Remove a command added previously to the menu.

```

```python

api.add_sidebar_widget(widget)
  # → Add a widget to the left sidebar.

```

```python

api.add_main_button(text, callback, row=20, column=0)
  # → Add a button to the main frame.

```

```python

api.register_settings_section(name, builder_fn)
  # → Add a new section to the app’s settings window.

```

```python

api.unregister_settings_section(name)
  # → Remove a section from the settings window.

```

## ✅ Best Practices

• Use `grid()` instead of `pack()` to avoid layout conflicts.
• Always implement `unregister(api)` to remove all added widgets or commands.
• Keep your plugin self-contained and stable.

```python
        html = markdown2.markdown(content, extras=["fenced-code-blocks", "code-friendly"])
        highlighted_html = highlight_code_blocks(html)
        full_html = f"<html><head>{github_css}</head><body>{highlighted_html}</body></html>"
        frame.load_html(full_html)

    sidebar_label = ttk.Label(text="🧪 Plugin Guide Active", padding=5)
    api.add_sidebar_widget(sidebar_label)
    _widgets["sidebar_label"] = sidebar_label

    btn = api.add_main_button("📘 How to Create Plugins", open_documentation, row=22, column=0)
    _widgets["main_button"] = btn

    def build_settings(parent):
        ttk.Label(parent, text="📘 Plugin Creation Guide", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(
            parent,
            text="This section explains how to create and manage plugins for Organizer.",
            wraplength=380,
            justify="left"
        ).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Button(parent, text="📖 Open Full Guide", command=open_documentation).grid(row=2, column=0, pady=10, sticky="w")

    api.register_settings_section("Plugin Development", build_settings)
    _widgets["settings_section"] = "Plugin Development"

def unregister(api):
    if _widgets["sidebar_label"]:
        _widgets["sidebar_label"].destroy()
        _widgets["sidebar_label"] = None

    if _widgets["main_button"]:
        _widgets["main_button"].destroy()
        _widgets["main_button"] = None

    if _widgets["doc_window"] and _widgets["doc_window"].winfo_exists():
        _widgets["doc_window"].destroy()
        _widgets["doc_window"] = None

    if _widgets["settings_section"]:
        api.unregister_settings_section(_widgets["settings_section"])
        _widgets["settings_section"] = None

```
```json
// plugins/plugin_demo_meta.json
{
    "description": "This plugin shows a complete integration example.",
    "version": "1.0",
    "author": "Nooch98"
}
```

---

## 🎨 Theme Configuration (Editor)

The integrated code editor supports custom themes via chlorophyll.

**📝 Important:**
* 🐍 If you're using the script version (running the `.py` files directly), you must manually set up the theme system.
* 📦 If you're using the compiled `.exe` version, no additional configuration is required — Organizer already includes all theme files.

**Manual Setup (for script version only)**

1. Download the full `chlorophyll` folder on the repository.
2. Copy it into your development environment’s `Lib/site-packages` **AND** into:
```bash
src/_internal/chlorophyll/
```
3. Create a subfolder
```bash
src/_internal/chlorophyll/colorscheme/
```
4. Inside `colorscheme/`, copy or create your `.toml` theme files or use the theme creator include on the editor.

**Example Paths**
*Windows:*
```makefile
C:\Users\YourUser\Desktop\Organizer\src\_internal\chlorophyll\colorscheme\
```
*Linux:*
```swift
~/Desktop/Organizer/src/_internal/chlorophyll/colorscheme/
```

---

## 🧪 System Requirements

* Python 3.13
* Windows or Linux
* ttkbootstrap, ttkthemes and tkinter(Include with python)
* Recomended IDE: VSCode

---

## 🔨 Building the Executable

You can package Organizer using PyInstaller or auto-py-to-exe(Recomended use auto-py-to-exe).

Make sure to include:
* `_internal/`
* `plugins/`
* `chlorophyll/`
* `software.ico`
* `software.png`

---

## 📦 Latest Release: `v2.0`

The **Organizer 2.0** release brings major improvements:
* Rewritten sidebar with section toggles
* Floating sidebar (pop-out support)
* Dependency parsing
* Git integration
* Full command palette (`Ctrl+Shift+P`)
* Advanced fuzzy file search with preview
* Sticky notes per project
* Global search inside files (multi-threaded)
* Plugin API enhancements
* Favorite/default editor configuration
* More stability and cleaner UI
See full changelog in [Releases](https://github.com/Nooch98/Organizer/releases/lastest)

---

## ✨ Why Organizer?

I built this app out of personal need to manage my programming projects, which had become scattered across folders and tools.
Now, Organizer has evolved into a powerful and extensible tool that anyone can use.

It’s open-source, flexible, and designed by a developer for developers.

---

## 📃 License

This project is licensed under the **MIT License** — do whatever you want with it. Just give credit where it's due.
