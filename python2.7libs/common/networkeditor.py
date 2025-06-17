import os
import logging
import contextlib
import hou
import toolutils
import nodegraphutils
import lib.pythonlib.iopath
import lib.pythonlib.common as pythonlib
import common.hou_utils
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


def toggle_dependancy_links(mode=None):
    editor = hou.ui.paneTabUnderCursor()
    if isinstance(editor, hou.NetworkEditor):
        modes = pythonlib.Enum(['0', '1', '2'])
        mode = mode if mode is not None else modes.next(editor.getPref('showdep'))
        editor.setPref('showdep', mode)


def remove_background_image(node):
    """Remove Callbacks of the node and all linked images"""
    try:
        node.removeEventCallback((hou.nodeEventType.BeingDeleted,), event_remove_background_image)
        node.removeEventCallback((hou.nodeEventType.FlagChanged,), event_visibility_background_image)
    except hou.OperationFailed:
        pass
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    images = tuple(i for i in editor.backgroundImages() if i.relativeToPath() != node.path())
    editor.setBackgroundImages(images)
    nodegraphutils.saveBackgroundImages(editor.pwd(), images)


@contextlib.contextmanager
def modify_linked_networkimage(node):
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    images = editor.backgroundImages()
    for i in images:
        if i.relativeToPath() == node.path():
            yield i
            break
    editor.setBackgroundImages(images)
    nodegraphutils.saveBackgroundImages(editor.pwd(), images)


def event_update_background_image(node, event_type, **kwargs):
    """Update all linked images of the node
    Only update the image when the node is activated"""
    if not node.isBypassed():
        with restore_display_flag():  #TODO replace as a decorator when python2 is far away
            editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            images = editor.backgroundImages()
            for i in images:
                if i.relativeToPath() == node.path():
                    path = i.path()
                    i.setPath('')
                    node.setDisplayFlag(True)
                    take_screenshot(path)
                    editor.setBackgroundImages(images)
                    nodegraphutils.saveBackgroundImages(editor.pwd(), images)
                    i.setPath(path)
                    break
            editor.setBackgroundImages(images)
            if images:
                nodegraphutils.saveBackgroundImages(editor.pwd(), images)


def event_visibility_background_image(node, event_type):
    if event_type == hou.nodeEventType.FlagChanged:  # This is needed because it get also called with event InputDataChanged
        try:
            with modify_linked_networkimage(node) as i:
                i.setBrightness(int(not node.isBypassed()))
        except RuntimeError:
            pass  # When duplicating a node with alt+click, its name is 'original0_of_' and modify_linked_networkimage() raise an exception


def event_remove_background_image(node, event_type):
    remove_background_image(node)


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


def toggle_node_preview(image_path=None):
    """Create a screenshot for all selected nodes."""
    with restore_display_flag():  #TODO replace as a decorator when python2 is far away
        if not image_path:
            image_path = os.path.join(hou.text.expandString('$HIP'), 'screenshots', '%NODE%.png')
        image_path = lib.pythonlib.iopath.normpath(image_path)
        editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        selection = hou.selectedNodes()
        for node in selection:
            node.setDisplayFlag(True)
            filepath = image_path.replace('%NODE%', node.name())
            image_exists = [i for i in editor.backgroundImages() if lib.pythonlib.iopath.normpath(i.path())==filepath]
            if image_exists:
                remove_background_image(node)
            else:
                resolutionX = int(hou.getPreference('custom.regnareb.preview_resolutionX'))
                resolutionY = int(hou.getPreference('custom.regnareb.preview_resolutionY'))
                resolution = [resolutionX, resolutionY]
                widthratio = int(hou.getPreference('custom.regnareb.preview_widthratio'))

                take_screenshot(filepath, resolution=resolution)
                add_background_image(editor, filepath, node=node, relative=True, widthratio=widthratio)


def add_background_image(editor, image_path, rect=None, node=None, relative=True, widthratio=1):
    image = hou.NetworkImage()
    image.setPath(image_path)
    rez = hou.imageResolution(image_path)
    ratio = 1.0 * rez[1] / rez[0]

    if node:
        rect = hou.BoundingRect(0, -node.size()[1], widthratio, -widthratio*ratio-node.size()[1]*1.2)
        if relative:
            image.setRelativeToPath(node.path())
        node.addEventCallback((hou.nodeEventType.InputDataChanged, hou.nodeEventType.InputRewired, hou.nodeEventType.ParmTupleChanged), event_update_background_image)
        node.addEventCallback((hou.nodeEventType.BeingDeleted,), event_remove_background_image)
        node.addEventCallback((hou.nodeEventType.FlagChanged,), event_visibility_background_image)
    if not rect:
        rect = hou.BoundingRect(0, -2, widthratio*2, -widthratio*ratio)
    image.setRect(rect)
    images = editor.backgroundImages() + (image,)
    editor.setBackgroundImages(images)
    nodegraphutils.saveBackgroundImages(editor.pwd(), images)

    return image


def connect_selected_nodes():
    # TODO: Create a merge if nodes have the same height
    nodes = sorted(hou.selectedNodes(), key=lambda x: x.position()[1], reverse=True)
    for index, node in enumerate(nodes):
        if not index or index==len(nodes):
            continue
        node.setInput(0, nodes[index-1], 0)
