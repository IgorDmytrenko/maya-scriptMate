# Script function: foo

import maya.cmds as cmds

OPERATOR = {
    "name": "Create CUBICAL",
    "category": "Modeling",
}

def create_polycube():
    cmds.polyCube()
    return None

def execute() -> None:
    create_polycube()
    return None