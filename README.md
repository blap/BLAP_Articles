# Scholar-Core

Scholar-Core is a powerful, local-first reference and paper management tool designed for researchers and students. It helps you organize your academic library, keep track of your reading, and discover new versions of articles. It features a plugin system to extend its functionality.

## Features

*   **Local-First Storage:** All your data is stored on your machine, ensuring privacy and accessibility.
*   **Organize Your Library:** Add papers, books, and other items to your library. Organize them with collections and tags.
*   **Attachments:** Attach PDF files and other documents to your library items.
*   **Cross-Platform:** The core application and its test suite are designed to run on both Windows and Linux.
*   **Extensible via Plugins:** Add new features and integrations through a simple plugin system.
*   **Browser Extension:** (Work in Progress) Includes a Chrome extension for easily adding articles from the web.

## Setup and Installation

To get started with Scholar-Core, you need Python 3.8+ installed on your system.

### 1. Install Dependencies

All required Python packages are listed in `scholar-core/requirements.txt`. You can install them using pip:

```bash
pip install -r scholar-core/requirements.txt
```

### 2. Running the Application

To run the main GUI application, execute the `run.py` script:

```bash
python scholar-core/run.py
```

## Running Tests

The project uses `pytest` for testing. We have included a cross-platform test runner script that handles dependency installation and test execution automatically.

To run the entire test suite, simply execute:

```bash
python run_tests.py
```

This will ensure all dependencies are installed and then run all tests located in the `scholar-core/tests` directory.

## Building from Source

You can package Scholar-Core into a standalone executable for your operating system. We provide build scripts for both Windows and Linux/macOS.

### On Windows

Use the `build.bat` batch script:

```batch
build.bat
```

This script will:
1.  Run the test suite.
2.  Package the application into a folder in the `dist/` directory using PyInstaller.
3.  Copy necessary files (like plugins) into the distribution folder.

### On Linux and macOS

Use the `build.sh` shell script:

```bash
./build.sh
```

This script performs the same steps as the Windows version and also creates a compressed archive (`.tar.gz` for Linux, `.zip` for macOS) of the final application.

---

## Creating a Plugin

The plugin system allows you to extend the functionality of Scholar-Core. Here is a step-by-step guide to creating your own plugin.

### 1. Plugin Structure

First, create a new directory for your plugin inside `scholar-core/plugins/`. For example, `scholar-core/plugins/my_awesome_plugin/`.

Your plugin directory must contain at least two files:
*   `__init__.py`: This file registers your plugin with the application.
*   A Python file for your main logic (e.g., `main.py`).

Your directory should look like this:

```
scholar-core/
└── plugins/
    └── my_awesome_plugin/
        ├── __init__.py
        └── main.py
```

### 2. The Main Plugin Class

In `main.py`, create the class that will contain your plugin's logic. This class can implement several methods (hooks) that the `PluginManager` will call at different points in the application's lifecycle.

**Example `main.py`:**
```python
from core import api

class MyAwesomePlugin:
    def get_name(self):
        return "My Awesome Plugin"

    # Hook: Called when the plugin is first loaded
    def setup(self, app_gui):
        self.app_gui = app_gui
        print(f"Plugin '{self.get_name()}' has been loaded!")
        # You can now interact with the GUI, e.g., add a new button
        # self.app_gui.add_menu_item("My Plugin Action", self.my_action)

    # Hook: Called when a new item is added to the library
    def on_item_added(self, item_id):
        item = api.get_item(item_id)
        print(f"Plugin saw that item '{item.title}' was added!")

    def my_action(self):
        # Logic for when your menu item is clicked
        self.app_gui.show_popup("Plugin Action!", "My Awesome Plugin")

```

### 3. Registering the Plugin

In your `__init__.py` file, you must define a `register()` function. This function should import your main class and return an instance of it.

**Example `__init__.py`:**
```python
from .main import MyAwesomePlugin

def register():
    """This registration function is called by the PluginManager."""
    return MyAwesomePlugin()
```

### 4. Available Plugin Hooks

Your plugin class can implement any of the following methods:

*   `setup(self, app_gui)`: Called on startup. Use this to get a reference to the main GUI application and add UI elements.
*   `on_item_added(self, item_id)`: Called after a new item is successfully added to the database.
*   `on_item_updated(self, item_id)`: Called after an item's metadata has been updated.
*   `on_item_deleted(self, item_id)`: Called after an item has been deleted.
*   `check_all_items(self)`: A method for running background tasks, like checking for updates across all library items. This can be triggered from the GUI.

By following these steps, you can create powerful plugins that integrate seamlessly with Scholar-Core.