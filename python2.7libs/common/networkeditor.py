import os
import tkinter
import logging
import hou
import nodegraphutils
import common.hou_utils
logger = logging.getLogger(__name__)


SELECTION = []
INDEX = 0



def get_display_node(pane=None):
    """Return the node with a display flag in the network editor under the mouse"""
    if not pane:
        pane = hou.ui.paneTabUnderCursor() or hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not isinstance(pane, hou.NetworkEditor):
        return False
    display = pane.pwd().displayNode()
    return display



def set_display_flag():
    """Cycle between selected nodes to set the display flag
    If only one node is selected it will cycle between the current displayed node and the selected one"""
    try:
        global SELECTION
        global INDEX
        selected = list(set(hou.selectedNodes()))
        if len(selected) == 1:  # Alternate between the last display flag and the current selection
            current = get_display_node()
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
            new = common.hou_utils.create_node(parent, 'object_merge', name, {'objpath1': '%FILEPATH%'}, position, path)
            result.append(new)
    return result


def toggle_dependancy_links():
    pass


def remove_background_image(editor, image_path):
    images = editor.backgroundImages()
    images = [x for x in images if x.path() != image_path]
    editor.setBackgroundImages(images)
    nodegraphutils.saveBackgroundImages(editor.pwd(), images)


def add_background_image(editor, image_path):
    image = hou.NetworkImage()
    image.setPath(image_path)
    images = editor.backgroundImages() + (image,)
    editor.setBackgroundImages([image])
    nodegraphutils.saveBackgroundImages(editor.pwd(), images)
    return image


def create_param(node):
    try:
        template = node.parmTemplateGroup()
        parm = hou.StringParmTemplate("screenshot_path", "Screenshot Path", 1, is_hidden=False)
        template.append(parm)
        node.setParmTemplateGroup(template)
        return parm
    except hou.OperationFailed:
        pass


def create_screenshots(image_path=None):
    """Create a screenshot for all selected nodes."""
    widthRatio = 40
    display_node = get_display_node()
    selection = hou.selectedNodes()
    for node in selection:
        node.setDisplayFlag(True)
        create_param(node)
        frame = hou.frame()
        desktop = hou.ui.curDesktop()
        panetab = desktop.paneTabOfType(hou.paneTabType.SceneViewer).name()
        camera = desktop.paneTabOfType(hou.paneTabType.SceneViewer).curViewport().name()
        desktop = desktop.name()
        viewername = '.'.join([desktop, panetab, 'world', camera])
        path = image_path.replace('%NODE%': node.name())
        hou.hscript("viewwrite -R beauty -f {0} {0} {1} '{2}'".format(frame, viewername, path))
        node.setParms({'screenshot_path': path})

        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        image = add_background_image(editor, path)
        rez = hou.imageResolution(path)
        ratio = 1.0*rez[1]/rez[0]
        rect = hou.BoundingRect(0, -node.size()[1]*1.1, widthRatio, -widthRatio*ratio-node.size()[1]*1.1)
        # image.setRelativeToPath(node.path())
        image.setRect(rect)
    display_node.setDisplayFlag(True)
