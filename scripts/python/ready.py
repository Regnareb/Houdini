import hou
import hdefereval
import common
import common.hou_utils
import common.sceneviewer
import common.preferences as prefs

def scene_event_callback(event_type):
    if event_type in [hou.hipFileEventType.BeforeLoad, hou.hipFileEventType.BeforeMerge]:
        if hou.getPreference('custom.regnareb.on_open_go_manual') == '1':
            common.hou_utils.toggle_update_mode(hou.updateMode.Manual)
        if hou.getPreference('custom.regnareb.on_open_change_desktop') == '1':
            hou.ui.desktop(hou.getPreference('general.desk.val')).setAsCurrent()
        # if hou.getPreference('custom.regnareb.on_open_hide_other_objects'):
        #     common.sceneviewer.hide_other_objects()
    if event_type in [hou.hipFileEventType.AfterLoad, hou.hipFileEventType.AfterSave, hou.hipFileEventType.AfterMerge]:
        if hou.getPreference('custom.regnareb.add_animated_badge') == '1':
            hdefereval.executeDeferred(common.events.event_add_all_animated_badges)
    if event_type == hou.hipFileEventType.BeforeSave:
        if hou.getPreference('custom.regnareb.add_animated_badge') == '1':
            common.events.event_delete_all_animated_badges()


hdefereval.executeDeferred(prefs.show_firstlaunch)
hou.hipFile.addEventCallback(scene_event_callback)