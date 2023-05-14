
import hou
import common.hou_utils

if not hou.getPreference('custom.regnareb.firstlaunch'):
    hou.hotkeys.addAssignment("h.pane.parms.copy_parm", "ctrl+C")  # Set shortcuts for copy/paste parameters
    hou.hotkeys.addAssignment("h.pane.parms.paste_refs", "ctrl+V")
    common.hou_utils.set_preference('delayinactiveviewports', '1')  # Delay updating secondaries viewports when manipulating one
    common.hou_utils.set_preference('networkeditor.shownodeshapes', '0')  # Disable node shapes
    common.hou_utils.set_preference('networkeditor.showsimpleshape', '1')  # Use simple node shapes
    common.hou_utils.set_preference('networkeditor.doautomovenodes', '0')  # Do not make room for new connected nodes
    common.hou_utils.set_preference('general.ui.scale', '0.95')  # Scale down the text in the UI
    common.hou_utils.set_preference('general.uiplaybar.menu', '1')  # Set the playbar to compact mode
    common.hou_utils.set_preference('tools.createincontext.val', '1')  # Create tools in context

    common.hou_utils.set_preference('custom.regnareb.firstlaunch', '1')  # Set this custom preference so that we set those only once


common.hou_utils.set_preference('custom.regnareb.scrub_timeline.mode', 'relative')
common.hou_utils.set_preference('custom.regnareb.scrub_timeline.keep_pressed', '1')
