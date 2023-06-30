import hou

hou.setUpdateMode(hou.updateMode.Manual)

# Force Desktop
for i in hou.ui.desktops():
    if i.name() == hou.getPreference('general.desk.val'):
        i.setAsCurrent()
        break