import os
import tkinter
import logging
import hou
import houlib
logger = logging.getLogger(__name__)


SELECTION = []
INDEX = 0
TOOL_parameters = ['label', 'icon', 'script', 'language', 'help', 'helpURL']


def set_display_flag():
    """Cycle between selected nodes to set the display flag
    If only one node is selected it will cycle between the current displayed node and the selected one"""
    try:
        global SELECTION
        global INDEX
        selected = list(set(hou.selectedNodes()))
        if len(selected) == 1:  # Alternate between the last display flag and the current selection
            current = lib.houlib.get_display_node()
            if selected[0] != current:
                SELECTION = list(set(selected + [current]))
                INDEX = SELECTION.index(selected[0])
            elif not SELECTION:
                return False  # If there is no selection list already, do nothing
            else:
                INDEX = (INDEX + 1) % len(SELECTION)

        elif selected and not SELECTION or selected and selected != SELECTION:  # Same thing but with several nodes selected
            SELECTION = selected
        else:
            INDEX = (INDEX + 1) % len(SELECTION)
        SELECTION[INDEX].setDisplayFlag(True)
    except hou.ObjectWasDeleted:
        SELECTION.pop(INDEX)
        INDEX = (INDEX - 1) % len(SELECTION)
        return set_display_flag()
    except IndexError:  # If the new list is smaller than the new one
        INDEX = 0
        return set_display_flag()
    except ZeroDivisionError:  # If no node is selected and no STATE is set
        return False
    return True


def paste_objectmerge():
    """Create an Object Merge node with the path to the nodes in the clipboard"""
    result = []
    pane = hou.ui.paneTabUnderCursor()
    if isinstance(pane, hou.NetworkEditor):
        position = pane.cursorPosition()
    else:
        return None, False
    parent = pane.pwd()
    clipboard = tkinter.Tk().clipboard_get().split(' ')
    for path in clipboard:
        if hou.node(path):
            name = os.path.basename(os.path.normpath(path))
            new = houlib.create_node(parent, 'object_merge', name, {'objpath1': '%FILEPATH%'}, position, path)
            result.append(new)
    return result
