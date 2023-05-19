import os
import re
import logging
import hou
import lib.pythonlib.iopath as iopath

logger = logging.getLogger(__name__)


def create_node(parent, nodetype, name, params=[], position=None, filepath='', get_sequence=False):
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


def get_node_parent_categories(node_type):
    result = []
    for cat in hou.nodeTypeCategories().values():
        if hou.nodeType(cat, node_type):
            result.append(cat)
    return result


def toggle_updatemode():
    mode = hou.updateModeSetting()
    if mode == hou.updateMode.AutoUpdate:
        hou.setUpdateMode(hou.updateMode.Manual)
    if mode == hou.updateMode.Manual:
        hou.setUpdateMode(hou.updateMode.AutoUpdate)


def parse_strings(filepath, params):
    """Convert all the data to the final one"""
    path = iopath.get_absolute_path(filepath)
    for i in params:
        try:
            params[i] = params[i].replace('%FILEPATH%', path)
            if '%CONTENT%' in params[i]:
                with open(filepath) as f:
                    params[i] = params[i].replace('%CONTENT%', f.read())
        except AttributeError:
            pass  # If the attribute is not a string
    return params
