import os
import re
import logging
import contextlib
import hou
import lib.pythonlib.iopath as iopath

logger = logging.getLogger(__name__)


UPDATEMODE = hou.updateMode.AutoUpdate


def create_node(parent, nodetype, name, params={}, position=None, filepath='', get_sequence=False):
    """Create a node with """
    if filepath:
        if get_sequence:
            _, filepath = iopath.get_file_sequence(filepath, '$F')
        parse_strings(filepath, params)
    logger.debug(parent, nodetype, name, params, filepath, position)
    node = parent.createNode(nodetype, name, force_valid_node_name=True)
    for k, v in params.items():
        try:
            node.setParms({k: v})
        except hou.OperationFailed:
            pass
    if position:
        node.setPosition(position)
    return node


def get_shelf(label='', name=''):
    """Return shelf by name or label"""
    for shelf in hou.shelves.shelves().values():
        if shelf.label() == label or shelf.name() == name:
            return shelf
    return None


def get_tabs_type(tab_type, desktop=None):
    """Return a list of ALL the tabs of the type passed as argument."""
    if not desktop:
        desktop = hou.ui.curDesktop()
    return [t for t in desktop.paneTabs() if t.type() == tab_type]


def get_node_parent_categories(node_type):
    result = []
    for cat in hou.nodeTypeCategories().values():
        if hou.nodeType(cat, node_type):
            result.append(cat)
    return result


def toggle_update_mode(mode=None):
    """Use a global variable to be able to set the setting back to the users one instead of choosing arbitrarily between Auto Update or On Mouse Up"""
    global UPDATEMODE
    if not mode:
        mode = hou.updateModeSetting()
    if mode == hou.updateMode.Manual:
        hou.setUpdateMode(UPDATEMODE)
    else:
        UPDATEMODE = mode
        hou.setUpdateMode(hou.updateMode.Manual)


def parse_strings(filepath, params):
    """Convert all the data to the final one
    The filepath argument can have an environment variable as path which will be converted to an absolute path.
    Every %FILEPATH% text will be replaced with that path.
    Every %CONTENT% text will be replaced by the content of the file at that path.
    """
    path = iopath.get_absolute_path(filepath)
    for i in params:
        try:
            params[i] = params[i].replace('%FILEPATH%', path)
            if '%CONTENT%' in params[i]:
                with open(path) as f:
                    params[i] = params[i].replace('%CONTENT%', f.read())
        except AttributeError:
            pass  # If the attribute is not a string
    return params


@contextlib.contextmanager
def temporary_cooking_mode(mode):
    """Set the cooking mode to the specified one and revert back to what it was.
    Accepted values: hou.updateMode.AutoUpdate / hou.updateMode.OnMouseUp / hou.updateMode.Manual
    """
    current = hou.updateModeSetting()
    hou.setUpdateMode(mode)
    yield
    hou.setUpdateMode(current)


def save_nodes_to_file(filepath, nodes=[]):
    """Save the selected nodes to the corresponding filepath
    Useful for sharing nodes over network. Use .cpio as file extension"""
    if not nodes:
        nodes = hou.selectedNodes()
    nodes[0].parent().saveItemsToFile(nodes, filepath)


def load_nodes_from_file(filepath):
    """Load the nodes from filepath into the current context"""
    pane = hou.ui.paneTabUnderCursor() or hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor) or hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    pane.pwd().loadItemsFromFile(filepath)


def netclipboard(copy):
    """Copy/paste a node from a network/shared location. Usefull for exchanging data between users without hassle.
    The path of the file is specified with the environment variable 'HOU_NETCLIPBOARD'
    """
    path = hou.getenv('HOU_NETCLIPBOARD')
    if copy:
        save_nodes_to_file(path)
    else:
        load_nodes_from_file(path)
