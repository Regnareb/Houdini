import hou
import common.events


node = kwargs['node']
objs = hou.objNodeTypeCategory()
sops = hou.sopNodeTypeCategory()
lights = [objs.nodeType(i) for i in ['hlight::2.0', 'ambient', 'indirectlight', 'envlight', 'rslight', 'rslightdome', 'rslightsun']]


if kwargs['type'] in lights:
    # Light nodes will show the "enabled" status by changing the background color of the node
    # common.events.event_light_enabled(node)
    node.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), common.events.event_light_enabled)
elif kwargs['type'] in [sops.nodeType('color')]:
    # The background color of the Color node reflect the color selected
    node.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), common.events.event_color_changed)



# Add callback to add a background image for animated nodes
node.addEventCallback((hou.nodeEventType.ParmTupleAnimated, ), common.events.event_is_animated)