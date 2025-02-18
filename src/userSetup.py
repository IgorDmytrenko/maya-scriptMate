# Load main.py file
# This wrapper needed to load plugin
# only when maya fully loaded
import maya.cmds as cmds
cmds.evalDeferred("import crudo_sm.main")
