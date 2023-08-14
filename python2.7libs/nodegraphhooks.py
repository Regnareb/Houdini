import hou
import canvaseventtypes


def create_null(parent, position):
    null = parent.parent().createNode('null')
    null.setName('OUT_' + parent.name().upper(), unique_name=True)
    null.setInput(0, parent, 0)
    null.setPosition(position)
    return null


def createEventHandler(uievent, pending_actions):
    if isinstance(uievent, canvaseventtypes.MouseEvent) and \
       uievent.eventtype == 'mousedown' and \
       uievent.mousestate.lmb and \
       uievent.modifierstate == canvaseventtypes.ModifierState(alt=1, ctrl=0, shift=0):
        if uievent.selected.item:
            return None, False  # Let the user duplicate nodes with alt+click
        if uievent.editor.pwd().path()=='/obj':
            geo = uievent.editor.pwd().createNode('geo')
            geo.setPosition(uievent.editor.cursorPosition() - hou.Vector2(0.5, 0.2))
            uievent.editor.setPwd(geo)
            return None, True

        mousepos = uievent.editor.posFromScreen(uievent.mousepos) - hou.Vector2(0.5, 0.2)
        selected = hou.selectedNodes()
        if len(selected) == 1:
            parent = selected[0]
            create_null(parent, mousepos)
            return None, True
        for parent in selected:
            position = parent.position()
            position[1] = mousepos[1]
            create_null(parent, position)
        return None, True
    return None, False
