import os
import logging
import platform
import contextlib
from PySide6 import QtWidgets
import hou
import toolutils
import nodegraphutils
import lib.pythonlib.iopath
import lib.pythonlib.network
import lib.pythonlib.common as pythonlib
import common.hou_utils
import common.constants
logger = logging.getLogger(__name__)


SELECTION = []
INDEX = 0


@contextlib.contextmanager
def restore_display_flag():
    display_node = get_display_node()
    yield
    if display_node:
        display_node.setDisplayFlag(True)


def get_display_node(pane=None):
    """Return the node with a display flag in the network editor under the mouse"""
    if not pane:
        pane = hou.ui.paneTabUnderCursor()
    if not isinstance(pane, hou.NetworkEditor):
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    display = pane.pwd().displayNode()
    return display


def display_next_output():
    selection = hou.selectedNodes()
    for node in selection:
        total = len(node.subnetOutputs())
        current = node.outputForViewFlag()
        cycle = pythonlib.Enum(list(range(total)))
        node.setOutputForViewFlag(cycle.next(current))


def cycle_display_flag():
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
        return cycle_display_flag()
    except IndexError:  # If the new list is smaller than the new one
        INDEX = 0
        return cycle_display_flag()
    except ZeroDivisionError:  # If no node is selected and no STATE is set
        return False
    return True


def paste_objectmerge():
    """Create an Object Merge node with the path to the nodes in the clipboard"""
    pane = hou.ui.paneTabUnderCursor()
    if isinstance(pane, hou.NetworkEditor):
        position = pane.cursorPosition()
    else:
        return None, False
    parent = pane.pwd()
    clipboard = hou.ui.getTextFromClipboard().split()
    merge = None
    for index, path in enumerate(clipboard):
        if hou.node(path):
            name = os.path.basename(os.path.normpath(path))
            if not merge:
                merge = common.hou_utils.create_node(parent, 'object_merge', name, {'objpath1': '%FILEPATH%'}, position, path)
            else:
                parm = merge.parm('numobj')
                parm.insertMultiParmInstance(index)
                merge.setParms({'objpath{}'.format(str(index+1)): path})
    return merge, True


def connect_selected_nodes():
    # TODO: Create a merge if nodes have the same height
    nodes = sorted(hou.selectedNodes(), key=lambda x: x.position()[1], reverse=True)
    for index, node in enumerate(nodes):
        if not index or index==len(nodes) - 1: # To check
            continue
        node.setInput(0, nodes[index-1], 0)


def toggle_dependancy_links(mode=None):
    editor = hou.ui.paneTabUnderCursor()
    if isinstance(editor, hou.NetworkEditor):
        modes = pythonlib.Enum(['0', '1', '2'])
        mode = mode if mode is not None else modes.next(editor.getPref('showdep'))
        editor.setPref('showdep', mode)


@contextlib.contextmanager
def modify_linked_networkimage(node):
    images = nodegraphutils.loadBackgroundImages(node.parent())
    for i in images:
        if i.relativeToPath() == node.path():
            yield i
            break
    nodegraphutils.saveBackgroundImages(node.parent(), images)


def take_screenshot(filepath, frame=None, viewername='', resolution=[640, 640]):
    pane = toolutils.sceneViewer()
    if not viewername:
        desktop = hou.ui.curDesktop()
        panename = pane.name()
        camera = pane.curViewport().name()
        desktop = desktop.name()
        viewername = '.'.join([desktop, panename, 'world', camera])
    if not frame:
        frame = hou.frame()
    refplane = pane.referencePlane()
    current = refplane.isVisible()
    refplane.setIsVisible(False)
    lib.pythonlib.iopath.create_dir(os.path.dirname(filepath))
    hou.hscript("viewwrite -r {3} {4} -R beauty -f {0} {0} {1} '{2}'".format(frame, viewername, filepath, resolution[0], resolution[1]))
    refplane.setIsVisible(current)


@common.hou_utils.wrong_image_format
def add_background_image_to_node(node, image_path, rect=None, relative=True, width_ratio=1, stick_to_side='bottom', offset=hou.Vector2(0, 0)):
    image = hou.NetworkImage()
    image.setPath(image_path)
    rez = hou.imageResolution(image_path)
    ratio = 1.0 * rez[1] / rez[0]
    if relative:
        image.setRelativeToPath(node.path())
    if stick_to_side and not rect:
        if stick_to_side=='bottom':
            rect = hou.BoundingRect(0, -node.size()[1], width_ratio, -node.size()[1] - ratio * width_ratio)
        if stick_to_side=='left':
            rect = hou.BoundingRect(0, 0, -node.size()[1] / ratio, -node.size()[1] * 1.08)
        if stick_to_side=='top':
            rect = hou.BoundingRect(0, 0, width_ratio, width_ratio * ratio)
        if stick_to_side=='right':
            rect = hou.BoundingRect(1, 0, 1 + node.size()[1] / ratio * width_ratio, -node.size()[1] * width_ratio * 1.08)
        rect.translate(offset)
    if not rect:
        rect = hou.BoundingRect(0, 0, width_ratio, width_ratio * ratio)

    image.setRect(rect)
    images = nodegraphutils.loadBackgroundImages(node.parent()) + [image]
    nodegraphutils.saveBackgroundImages(node.parent(), images)
    return image


@common.hou_utils.wrong_image_format
def add_background_image_to_editor(editor, image_path, position, rect=None, width_ratio=5):
    image = hou.NetworkImage()
    image.setPath(image_path)
    if not rect:
        rez = hou.imageResolution(image_path)
        ratio = 1.0 * rez[1] / rez[0]
        rect = hou.BoundingRect(position[0] - width_ratio/2, position[1] - width_ratio*ratio/2, position[0] + width_ratio/2, position[1] + width_ratio*ratio/2)
    image.setRect(rect)
    images = editor.backgroundImages() + (image,)
    nodegraphutils.saveBackgroundImages(editor.pwd(), images, editor)
    return image


def remove_background_image(node):
    """Remove all linked images of a node"""
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    images = tuple(i for i in editor.backgroundImages() if i.relativeToPath() != node.path())
    nodegraphutils.saveBackgroundImages(node.parent(), images)


def paste_clipboard_images(editor, position):
    """Check the clipboard and create background images accordingly.
    It checks for local file paths, URL to download, or image directly in the clipboard"""
    clipboard = QtWidgets.QApplication.clipboard()
    hip = lib.pythonlib.iopath.normpath(hou.expandString('$HIP'))
    # Local Files
    result = []
    if platform.system() == "Windows":
        pattern = common.constants.REGEX_WINDOWS_PATH
    else:
        pattern = common.constants.REGEX_UNIX_PATH
    matches = pattern.finditer(clipboard.text())
    for match in matches:
        path = lib.pythonlib.iopath.normpath(match.group())
        if hou.node(path):
            continue
        if filename.lower().endswith(common.constants.IMAGE_FORMATS) and os.path.isfile(path):
            logger.debug('Paste local image: ' + path)
            add_background_image_to_editor(editor, path, position)
            result.append(path)

    # Clipboard
    if image := clipboard.image():
        path = lib.pythonlib.iopath.pathjoin(hip, 'pasted.jpg')
        if not image.save(path):
            return []
        else:
            logger.debug('Paste clipboard image: ' + path)
            add_background_image_to_editor(editor, path, position)
            return [path]

    # URLs
    pattern = common.constants.REGEX_URL
    matches = pattern.finditer(clipboard.text())
    for match in matches:
        url = match.group()
        filename = lib.pythonlib.network.get_filename_from_url(url) or 'downloaded.jpg'  # Get the next available file name in $HIP
        lib.pythonlib.iopath.create_dir(os.path.join(hip, 'images'))
        path = hou.expandString(os.path.join(hip, 'images', filename))
        path = lib.pythonlib.iopath.normpath(path)
        if filename.lower().endswith(common.constants.IMAGE_FORMATS) and lib.pythonlib.network.download_file(url, path): # download and put in $HIP/images/filename
            logger.debug('Paste url image: ' + url)
            add_background_image_to_editor(editor, path, position)
            result.append(path)
    return result
