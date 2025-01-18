import hou
import common.hou_utils
import common.sceneviewer

if hou.getPreference('custom.regnareb.on_open_go_manual'):
    common.hou_utils.toggle_update_mode(hou.updateMode.Manual)

# if hou.getPreference('custom.regnareb.on_open_hide_other_objects'):
#     common.sceneviewer.hide_other_objects()

if hou.getPreference('custom.regnareb.on_open_sopviewmode'):
    hou.setPreference('tools.sopviewmode.val', '0')

if hou.getPreference('custom.regnareb.on_open_change_desktop'):
    for i in hou.ui.desktops():
        if i.name() == hou.getPreference('general.desk.val'):
            i.setAsCurrent()
            break