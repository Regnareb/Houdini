import hou

if hou.getPreference('custom.regnareb.on_open_go_manual'):
    hou.setUpdateMode(hou.updateMode.Manual)

# Force Desktop
for i in hou.ui.desktops():
    if i.name() == hou.getPreference('general.desk.val'):
        i.setAsCurrent()
        break