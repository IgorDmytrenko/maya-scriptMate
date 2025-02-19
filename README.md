# **ScriptMate - Micro Framework for Managing Maya Scripts**  

**ScriptMate** is a lightweight framework for organizing and executing Python scripts in **Autodesk Maya**. It eliminates the frustration of Maya's **unreliable shelves** and simplifies script management with **folder-based menus, security checks, and hot-reloading.**  

🚀 **Full Documentation:** [crudo.dev/docs/maya/scriptmate-maya-plugin](https://crudo.dev/docs/maya/scriptmate-maya-plugin/)  

---

## **✨ Features**  

✅ **Folder-Based Menus** – Organize scripts using simple directory names (`menu_`, `sub_`).  
✅ **Script Wrapping (Templates)** – Ensures only properly structured scripts are executed.  
✅ **Hot-Reloading** – No need to restart Maya—just click **Update Scripts** to refresh.  
✅ **Security Checks** – Blocks execution of scripts that import risky modules (`os`, `subprocess`, etc.).  
✅ **Error Handling & Logging** – Faulty scripts are skipped, not crashing the plugin.  
✅ **Supports Local & Network Directories** – Sync scripts between users effortlessly.  

---

## **📂 Folder Structure**  

Scripts are **automatically** turned into Maya menus based on directory names:  

```
scriptLibrary/
│── menu_Tools/
│   ├── script_cleanScene.py
│   ├── sub_Modeling/
│   │   ├── script_optimizeMesh.py
```

This results in a **Tools** menu in Maya with a **Modeling** submenu inside it.  

---

## **📌 Example Script Template**  

All scripts must follow a simple format:  

```python
OPERATOR = {
    "name": "My Script",
    "category": "Tools"
}

def user_script():
    print("Hello, ScriptMate!")

def execute() -> None:
    user_script()
```

---

## **🔐 Security & Safety**  

- **Blocks unsafe imports** like `os`, `sys`, `subprocess`, preventing harmful execution.  
- Customize the **security rules** in `config.json`.  
- If a script is safe, **override restrictions** with an `@unsafe` decorator:  

```python
@unsafe(reason="Loading files from disk")
def execute() -> None:
    user_script()
```

---

## **⚡ Installation**  

1️⃣ **Download & Extract** the plugin files.  
2️⃣ **Copy to Maya’s module directory:**  

📌 **Windows:**  
```sh
C:\Users\USERNAME\Documents\maya\2025\modules\
```  
📌 **MacOS:**  
```sh
/Users/USERNAME/Library/Preferences/Autodesk/maya/2025/modules/
```  
3️⃣ **Restart Maya**, and ScriptMate will appear in the menu!  

---

## **🛠 Preventing Plugin Conflicts**  

Maya plugins often clash when using common module names like `utils`. ScriptMate prevents this by dynamically **registering each package under its own namespace**:  

```python
import PluginA.utils  # Loads PluginA's utils
import PluginB.utils  # Loads PluginB's utils
```

📌 **Follow these rules to avoid conflicts:**  
- Use **absolute imports** (`from PluginA.tools import rig`).  
- Keep **relative imports** within your package (`from . import helpers`).  
- If two plugins have the same name, only the first will load.  

---

## ** Full Documentation**  

For detailed instructions, **visit the full guide:**  
🔗 [crudo.dev/docs/maya/scriptmate-maya-plugin](https://crudo.dev/docs/maya/scriptmate-maya-plugin/)  

🚀 **Try it out and streamline your Maya scripting workflow!**  

---

## LICENSE

---

MIT
