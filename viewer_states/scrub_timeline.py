import hou


class ScrubTimelineState(object):
    def __init__(self, scene_viewer, state_name):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        self._base_x = self._base_frame = None

    def onCommand(self, kwargs):
        args = kwargs['command_args']
        self.previous_viewer_state = args['viewer_state']

    def onExit(self, kwargs):
        if hou.getPreference('custom.regnareb.scrub_timeline.keep_pressed'):
            self.scene_viewer.clearPromptMessage()
            scene_viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
            scene_viewer.setCurrentState(self.previous_viewer_state)

    def _scrub_abs(self, x):
        # Take the absolute position of the mouse pointer (as a percentage
        # of the total viewer width) and move that far along the current
        # frame range
        width, _ = self.scene_viewer.contentSize()
        pct = x / float(width)
        start_frame, end_frame = hou.playbar.frameRange()
        frame = int((end_frame - start_frame) * pct + start_frame)
        hou.setFrame(frame)

    def _scrub_rel(self, x):
        # Use the difference between the mouse pointer's current position
        # and the previous position to calculate how many frames to move
        # forward/back
        if self._base_x is not None:
            delta = int((x - self._base_x) / 10.0)
            frame = max(0, self._base_frame + delta)
            hou.setFrame(frame)
        else:
            self._base_x = x
            self._base_frame = hou.intFrame()

    def onMouseEvent(self, kwargs):
        print(kwargs["mode"])
        device = kwargs["ui_event"].device()
        if device.isLeftButton():
            x = device.mouseX()
            if kwargs["mode"] == "relative":
                self._scrub_rel(x)
            elif kwargs["mode"] == "absolute":
                self._scrub_abs(x)
        elif device.isMiddleButton():
            x = device.mouseX()
            self._scrub_abs(x)
        else:
            self._base_x = None

    def onKeyEvent(self, kwargs):
        ui_event = kwargs['ui_event']
        # self.key_pressed = ui_event.device().keyString()
        if ui_event.device().isKeyDown():
            return True
        # if not ui_event.device().isKeyDown():
        #     self.onExit(kwargs)
        #     return True
        return False

    def onKeyTransitEvent(self, kwargs):
        ui_event = kwargs['ui_event']
        if not ui_event.device().isKeyDown():
            self.onExit(kwargs)
            return True
        return False

    def onParmChangeEvent(self, kwargs):
        print(kwargs)



nodecategories = [hou.chopNodeTypeCategory(), hou.cop2NodeTypeCategory(), hou.dopNodeTypeCategory(), hou.sopNodeTypeCategory(), hou.topNodeTypeCategory()]
template = hou.ViewerStateTemplate("br_scrub_timeline", "br_Scrub_timeline", hou.objNodeTypeCategory(), nodecategories)
template.bindFactory(ScrubTimelineState)

menu = hou.ViewerStateMenu("br_scrub_timeline", "Scrub Timeline")
menu.addRadioStrip("mode", "Mode", hou.getPreference('custom.regnareb.scrub_timeline.mode'))
menu.addRadioStripItem("mode", "relative", "Relative")
menu.addRadioStripItem("mode", "absolute", "Absolute")
template.bindMenu(menu)

hou.ui.registerViewerState(template)