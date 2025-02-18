
# General
from os import path
# Maya imports
import maya.OpenMayaUI as omui
import maya.cmds as cmds

maya_version = cmds.about(version=True)
if not maya_version.startswith('2025'):
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
else:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance

# Modules imports
from crudo_sm.user_interface import context_tab
from crudo_sm.settings.common import CONFIG

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class PreferencesWindow(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(PreferencesWindow, self).__init__(parent)
        self.config = CONFIG
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(600)
        self.setWindowFlags(self.windowFlags())

        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.load_preferences()  # Load the settings when the window is initialized

    def create_widgets(self):
        self.user_scripts_le = QtWidgets.QLineEdit()
        self.local_scripts_le = QtWidgets.QLineEdit()

        self.browse_btn = QtWidgets.QPushButton()
        self.browse_local_btn = QtWidgets.QPushButton()

        self.browse_btn.setIcon(QtGui.QIcon('path_to_icon'))  # Replace 'path_to_icon' with the path to your icon file
        self.browse_local_btn.setIcon(QtGui.QIcon('path_to_icon'))

        self.save_btn = QtWidgets.QPushButton("Save")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):
        browse_network_layout = QtWidgets.QHBoxLayout()
        browse_network_layout.addWidget(self.user_scripts_le)
        browse_network_layout.addWidget(self.browse_btn)

        browse_local_layout = QtWidgets.QHBoxLayout()
        browse_local_layout.addWidget(self.local_scripts_le)
        browse_local_layout.addWidget(self.browse_local_btn)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Global scripts directory:", browse_network_layout)
        form_layout.addRow("Local scripts directory:", browse_local_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.browse_btn.clicked.connect(lambda: self.browse(self.user_scripts_le))
        self.browse_local_btn.clicked.connect(lambda: self.browse(self.local_scripts_le))
        self.save_btn.clicked.connect(self.save_preferences)
        self.close_btn.clicked.connect(self.close)

    def load_preferences(self):
        """Load the saved preferences"""
        data = self.config.get_local_config_data()
        if data:
            user_scripts = data.get('userScripts', [{}])[0]
            self.user_scripts_le.setText(user_scripts.get('network_path', ''))
            self.local_scripts_le.setText(user_scripts.get('local_path', ''))


    def browse(self, line_edit):
        """Open a directory dialog for the given QLineEdit."""
        current_directory = line_edit.text()
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            current_directory if path.exists(current_directory) else QtCore.QDir.homePath()
        )
        if directory:
            line_edit.setText(directory)


    def save_preferences(self):
        """Save the preferences"""
        network_path = self.user_scripts_le.text()
        local_path = self.local_scripts_le.text()

        if self.config.update_user_scripts_paths(network_path, local_path):
            # Update the menu with the new settings
            context_tab.add_menus()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save preferences. Please check the configuration file."
            )


def show():
    try:
        preferencesWin.close()
        preferencesWin.deleteLater()
    except:
        pass

    preferencesWin = PreferencesWindow()
    preferencesWin.show()
