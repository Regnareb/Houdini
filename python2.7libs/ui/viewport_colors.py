import os
import re
import shutil

import hou
import toolutils

import utils
# Test which file has priority if there is one in $HOME and one in $REGNAREB


COLORSCHEMES = {
    hou.viewportColorScheme.Light: "config/3DSceneColors.light",
    hou.viewportColorScheme.Dark: "config/3DSceneColors.dark",
    hou.viewportColorScheme.Grey: "config/3DSceneColors.bw"
    }
colorscheme_enum = lib.utils.Enum(COLORSCHEMES.keys())


def switch_viewports_colorscheme(current_viewport=False):
    if current_viewport:
        under_cursor = hou.ui.paneTabUnderCursor()
        viewports = [under_cursor.curViewport()]
    else:
        viewports = toolutils.sceneViewer().viewports()

    new_scheme = ''
    for viewport in viewports:
        scheme = viewport.settings().colorScheme()
        new_scheme = new_scheme if new_scheme else colorscheme_enum.next(scheme)
        viewport.settings().setColorScheme(new_scheme)


def get_current_colorscheme():
    scene_viewer = toolutils.sceneViewer()
    viewports = scene_viewer.viewports()
    for viewport in viewports:
        return viewport.settings().colorScheme().name()
    else:
        return hou.viewportColorScheme.Light


class ViewportColor():
    def __init__(self):
        self.regex = re.compile(r'(BackgroundBottomColor|BackgroundColor):\s([\s|\d|\.]*)')
        self.get_colors(get_current_colorscheme())

    def replace_values(self, match_obj):
        """Replace values from a regex pattern to the custom color values"""
        return '{}:\t{}\t'.format(match_obj.group(1), self.values[match_obj.group(1)])

    def get_colors(self, scheme):
        """Retrieve viewport colors from the corresponding UI file"""
        try:
            self.colorfilepath = os.path.join(hou.text.expandString("$REGNAREB"), COLORSCHEMES[scheme])
            with open(self.colorfilepath, "r") as f:
                content = f.read()
                values = re.findall(self.regex, content)
                self.values = {i[0]: i[1].strip() for i in values}
        except IOError:  # Copy the original color scheme from Houdini install if it doesn't exists
            originalpath = os.path.join(hou.text.expandString("$HFS"), 'houdini', COLORSCHEMES[scheme])
            shutil.copyfile(originalpath, self.colorfilepath)
            self.get_colors(scheme)

    def save_colors(self):
        """Save viewport colors to the corresponding UI file"""
        with open(self.colorfilepath, "r+") as f:
            content = f.read()
            content = re.sub(self.regex, self.replace_values, content)
            f.seek(0)
            f.write(content)
            f.truncate()
        hou.ui.reloadViewportColorSchemes()
