import hou
import common.events
import common.hou_utils


node = kwargs['node']
objs = hou.objNodeTypeCategory()
sops = hou.sopNodeTypeCategory()
lights = [objs.nodeType(i) for i in ['hlight::2.0', 'ambient', 'indirectlight', 'envlight', 'rslight', 'rslightdome', 'rslightsun']]


if kwargs['type'] in lights:
    # Light nodes will show the "enabled" status by changing the background color of the node
    node.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), common.events.event_light_enabled)
elif kwargs['type'] in [sops.nodeType('color')]:
    # The background color of the Color node reflect the color selected
    node.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), common.events.event_color_changed)
elif kwargs['type'] in [sops.nodeType('rop_alembic')]:
    # Add a version parameter to Rop Alembic nodes. Each version is in its own folder
    parm_group = node.parmTemplateGroup()
    parm_template = hou.IntParmTemplate(name="version", label="Version", num_components=1, min=1, default_value=(1, 1, 1))
    parm_insert = parm_group.find('trange')
    parm_group.insertBefore(parm_insert, parm_template)
    node.setParmTemplateGroup(parm_group)
    path = node.parm('filename').unexpandedString().replace('.abc', '_`padzero(3, ch("version"))`.abc')
    node.parm('filename').set(path)


# Add callback to add a background image for animated nodes
node.addEventCallback((hou.nodeEventType.ParmTupleAnimated, ), common.events.event_is_animated)
common.hou_utils.save_node_stats(kwargs['type'].name())
