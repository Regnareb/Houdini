import os
import hou
import nodegraphutils
import lib.pythonlib.iopath
import common.networkeditor


def toggle_node_preview(image_path=None):
    """Create a screenshot for all selected nodes."""
    with common.networkeditor.restore_display_flag():  #TODO replace as a decorator when python2 is far away
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
                event_remove_background_image(node)
            else:
                resolutionX = int(hou.getPreference('custom.regnareb.preview_resolutionX'))
                resolutionY = int(hou.getPreference('custom.regnareb.preview_resolutionY'))
                resolution = [resolutionX, resolutionY]
                widthratio = int(hou.getPreference('custom.regnareb.preview_widthratio'))

                common.networkeditor.take_screenshot(filepath, resolution=resolution)
                common.networkeditor.add_background_image(editor, filepath, node=node, relative=True, width_ratio=widthratio)
                node.addEventCallback((hou.nodeEventType.InputDataChanged, hou.nodeEventType.InputRewired, hou.nodeEventType.ParmTupleChanged), event_update_background_image)
                node.addEventCallback((hou.nodeEventType.BeingDeleted,), event_remove_background_image)
                node.addEventCallback((hou.nodeEventType.FlagChanged,), event_visibility_background_image)


def event_update_background_image(node, event_type=None, **kwargs):
    """Update all linked images of the node
    Only update the image when the node is activated"""
    if not node.isBypassed():
        with common.networkeditor.restore_display_flag():  #TODO replace as a decorator when python2 is far away
            editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            images = editor.backgroundImages()
            for i in images:
                if i.relativeToPath() == node.path():
                    path = i.path()
                    i.setPath('')
                    node.setDisplayFlag(True)
                    common.networkeditor.take_screenshot(path)
                    editor.setBackgroundImages(images)
                    nodegraphutils.saveBackgroundImages(editor.pwd(), images, editor=editor)
                    i.setPath(path)
                    break
            editor.setBackgroundImages(images)
            nodegraphutils.saveBackgroundImages(editor.pwd(), images, editor=editor)


def event_visibility_background_image(node, event_type=None):
    if event_type == hou.nodeEventType.FlagChanged:  # This is needed because it get also called with event InputDataChanged
        try:
            with common.networkeditor.modify_linked_networkimage(node) as i:
                i.setBrightness(int(not node.isBypassed()))
        except RuntimeError:
            pass  # When duplicating a node with alt+click, its name is 'original0_of_' and modify_linked_networkimage() raise an exception


def event_remove_background_image(node, event_type=None):
    callbacks = {
        event_update_background_image: (hou.nodeEventType.InputDataChanged, hou.nodeEventType.InputRewired, hou.nodeEventType.ParmTupleChanged),
        event_visibility_background_image: (hou.nodeEventType.FlagChanged,),
        event_remove_background_image: (hou.nodeEventType.BeingDeleted,)
    }
    for func in callbacks:
        try:
            node.removeEventCallback(callbacks[func], func)
        except hou.OperationFailed:
            pass
    common.networkeditor.remove_background_image(node)