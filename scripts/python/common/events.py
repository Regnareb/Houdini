import hou
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


def event_is_animated(node, event_type=None, **kwargs):
    # If you delete the node and undo, the callbacks are deleted and it won't reinstate the behaviour unless you reload the scene
    def delete_background_image(node, **kwargs):
        try:
            common.networkeditor.remove_background_image(node)
            node.removeEventCallback((hou.nodeEventType.BeingDeleted,), delete_background_image)
        except hou.OperationFailed:
            pass  # If no background image is linked to the node

    children = node.children()
    node_time_dependent = any([parm.isTimeDependent() for parm in node.parms()])
    children_time_dependent = any([parm.isTimeDependent() for node in children for parm in node.parms()])
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not any((node_time_dependent, children_time_dependent)):
        delete_background_image(node)
        return
    elif node_time_dependent and children_time_dependent:
        filepath = '$REGNAREB/images/keyed_both.png'
    elif node_time_dependent:
        filepath = '$REGNAREB/images/keyed_node.png'
    elif children_time_dependent:
        filepath = '$REGNAREB/images/keyed_children.png'
    common.networkeditor.add_background_image(editor, hou.text.expandString(filepath), rect=None, node=node, relative=True, width_ratio=0.6, stick_to_side='right', offset=hou.Vector2(0.3, -0.3))
    node.addEventCallback((hou.nodeEventType.BeingDeleted,), delete_background_image)
