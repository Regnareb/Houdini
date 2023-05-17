
# Do not activate the follow display flag for heavy nodes
IGNORED_NODES = {'subdivide', 'remesh', 'dopnet', 'particlefluidsurface'}


def automatic_display_flag(node, index):
    """When connecting input, this script will change the display flag if the input connected has the display flag on"""
    try:
        if node.type().name() in IGNORED_NODES:
            return
            # TODO: Pass Houdini cook mode to manual? Preferences?
            # TODO: Display a message
            # TODO: Colorize the manual/auto update button on the bottom right
        if node.input(index):
            if node.input(index).isDisplayFlagSet():
                node.setDisplayFlag(True)
            if node.input(index).isRenderFlagSet():
                node.setRenderFlag(True)
    except Exception:
        pass



automatic_display_flag(kwargs["node"], kwargs["input_index"])
