import hou
import hdefereval
import common
import common.hou_utils
import common.sceneviewer
import common.preferences as prefs

def scene_event_callback(event_type):
    if event_type in [hou.hipFileEventType.BeforeLoad, hou.hipFileEventType.BeforeMerge]:
        if hou.getPreference('custom.regnareb.on_open_go_manual'):
            common.hou_utils.toggle_update_mode(hou.updateMode.Manual)
        if hou.getPreference('custom.regnareb.on_open_sopviewmode'):
            hou.setPreference('tools.sopviewmode.val', '0')
        if hou.getPreference('custom.regnareb.on_open_change_desktop'):
            hou.ui.desktop(hou.getPreference('general.desk.val')).setAsCurrent()
        # if hou.getPreference('custom.regnareb.on_open_hide_other_objects'):
        #     common.sceneviewer.hide_other_objects()

hdefereval.executeDeferred(prefs.show_firstlaunch)
hou.hipFile.addEventCallback(scene_event_callback)