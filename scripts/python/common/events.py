import re
import hou
import nodegraphutils
import common.hou_utils
import common.networkeditor


def event_light_enabled(node, event_type=None, **kwargs):
    if kwargs['parm_tuple'] and kwargs['parm_tuple'].name() != "light_enable":
        return  # Small optimization
    parm = node.parmTuple('light_enable') # or node.parmTuple("light_enabled") or node.parmTuple("enabled")
    if not parm:
        return
    colors = [hou.Color((0.0, 0.0, 0.0)), hou.Color((1.0, 0.725, 0.0))]
    state = parm.eval()[0]
    node.setColor(colors[state])


def event_color_changed(node, event_type=None, **kwargs):
    if kwargs['parm_tuple'] and kwargs['parm_tuple'].name() != "color":
        return  # Small optimization
    parm = node.parmTuple('color')
    if not parm:
        return
    color = parm.eval()
    hcolor = hou.Color(color)
    node.setColor(hcolor)


@common.hou_utils.check_preference('custom.regnareb.add_animated_badge', '1')
def event_is_animated(node, event_type=None, **kwargs):
    # If you delete the node and undo, the callbacks are deleted and it won't reinstate the behaviour unless you reload the scene
    if node.path() == '/' or node.parent().path() == '/':
        return False  # Don't check top nodes
    children = node.children()
    node_time_dependent = any([parm.isTimeDependent() for parm in node.parms()])
    children_time_dependent = any([parm.isTimeDependent() for node in children for parm in node.parms()])
    image = has_linked_animated_badge(node)
    if not any((node_time_dependent, children_time_dependent)):
        if image:
            event_delete_animated_badge(node)
        return False
    elif node_time_dependent and children_time_dependent:
        filepath = hou.text.expandString('$REGNAREB/images/keyed_both.png')
    elif node_time_dependent:
        filepath = hou.text.expandString('$REGNAREB/images/keyed_node.png')
    elif children_time_dependent:
        filepath = hou.text.expandString('$REGNAREB/images/keyed_children.png')

    if image and filepath == image.path():
        return True
    if image:
        event_delete_animated_badge(node)
    common.networkeditor.add_background_image(node, hou.text.expandString(filepath), rect=None, relative=True, width_ratio=0.7, stick_to_side='right', offset=hou.Vector2(0.1, -0.55))
    return True


def event_delete_animated_badge(node, **kwargs):
    images = nodegraphutils.loadBackgroundImages(node.parent())
    if image := has_linked_animated_badge(node):
        images.remove(image)
        nodegraphutils.saveBackgroundImages(node.parent(), images)


def event_delete_all_animated_badges(**kwargs):
    nodes = hou.node("/").allSubChildren()
    for node in nodes:
        event_delete_animated_badge(node)


def event_add_all_animated_badges(**kwargs):
    nodes = hou.node("/").allSubChildren()
    for node in nodes:
        event_is_animated(node)


def has_linked_animated_badge(node):
    images = nodegraphutils.loadBackgroundImages(node.parent())
    images = [i for i in images if (i.relativeToPath() == node.path() and re.search(r'keyed_(children|node|both)\.png$', i.path()))]
    for i in images:
        return i
    else:
        return None


# import common.events
# common.events.event_clear_all_animated()
# common.events.event_add_all_animated()