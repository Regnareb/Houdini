import logging
import functools
import collections
from PySide2 import QtCore, QtGui, QtWidgets
import hou
import lib.pythonlib.qt as qt
import common.sceneviewer
logger = logging.getLogger(__name__)

VERSION = 1

def set_preference(name, value):
    if not hou.getPreference(name):
        return hou.addPreference(name, value)
    else:
        return hou.setPreference(name, value)


class FirstLaunch(QtWidgets.QDialog):
    def __init__(self, check):
        super(FirstLaunch, self).__init__(hou.ui.mainQtWindow())
        self.setWindowTitle('First Launch Initialisation')
        self.row_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.row_layout)

        self.check = check
        if not self.is_there_new_prefs(VERSION):
            return

        self.interface = collections.defaultdict(qt.RowLayout)
        if self.is_there_new_prefs(1):
            self.interface['networkeditor.shownodeshapes'].addCheckbox('Disable Nodes Shapes', True)
            self.interface['networkeditor.showsimpleshape'].addCheckbox('Use Simple Node Shapes', True)
            self.interface['networkeditor.doautomovenodes'].addCheckbox('Disable Auto Move Nodes', True)
            self.interface['networkeditor.showanimations'].addCheckbox('Disable Nodes Animations', True)
            self.interface['networkeditor.maxflyoutscale'].addCheckbox('Set Low Size to Show Ring ', True)
            self.interface['tools.createincontext.val'].addCheckbox('Create Tools In Context', True)
            self.interface['tools.sopviewmode.val'].addCheckbox('Show Displayed Node instead of Selected node', True)
            self.interface['compact_mode'].addCheckbox('Set UI to Compact Mode', True)
            self.interface['general.ui.scale'].addCheckbox(state=True)
            self.interface['general.ui.scale'].addLabel('General UI Scale')
            self.interface['general.ui.scale'].addField(0.95, validator='float', minimum=0.75, maximum=3, decimals=2)
            self.interface['general.ui.scale'].addSlider(0.95, mode='float', minimum=0.75, maximum=3)
            self.interface['general.ui.scale'].connectFieldSlider()
            self.interface['general.desk.val'].addCheckbox('Startup In Desktop', True)
            self.interface['general.desk.val'].addCombobox([i.name() for i in hou.ui.desktops()])
            self.interface['general.desk.val'].combobox.setCurrentIndex(self.interface['general.desk.val'].combobox.findText('Compact'))
            self.interface['general.desk.val'].checkbox.toggled.connect(self.interface['general.desk.val'].connectCheckboxState)
            for i in ['networkeditor.shownodeshapes', 'networkeditor.showsimpleshape', 'networkeditor.doautomovenodes', 'networkeditor.showanimations', 'networkeditor.maxflyoutscale', 'tools.sopviewmode.val', 'tools.createincontext.val', 'compact_mode', 'general.desk.val']:  # , 'general.ui.scale'
                self.row_layout.addLayout(self.interface[i])

        self.shortcuts = collections.defaultdict(qt.RowLayout)
        self.shortcuts_groupbox = QtWidgets.QGroupBox('Set Shortcuts')
        self.shortcuts_groupbox.setCheckable(True)
        self.shortcuts_vbox = QtWidgets.QVBoxLayout()
        self.shortcuts_groupbox.setLayout(self.shortcuts_vbox)
        if self.is_there_new_prefs(1):
            shortcuts = {
                'copy_parm': {'label': 'Copy Parameter', 'default_shortcut': 'Ctrl+Shift+C', 'command': 'h.pane.parms.copy_parm'},
                'paste_refs': {'label': 'Paste Parameter Reference', 'default_shortcut': 'Ctrl+Shift+V', 'command': 'h.pane.parms.paste_refs'},
                'paste_object_merge': {'label': 'Paste Object Merge', 'default_shortcut': 'Alt+V', 'command': ''},  # Remove existing shortcut
                'cycle_display_flag': {'label': 'Cycle Display Flag', 'default_shortcut': 'R', 'command': ''},  # Remove existing shortcut
                'display_next_output': {'label': 'Display Next Output', 'default_shortcut': 'Alt+X', 'command': ''},  # Remove existing shortcut
                'toggle_dependancy_links': {'label': 'Toggle dependancy Links', 'default_shortcut': 'Ctrl+D', 'command': ''},  # Remove existing shortcut
                'connect_selected_nodes': {'label': 'Connect Selected Nodes', 'default_shortcut': 'Shift+Y', 'command': ''},
                'scrub_timeline': {'label': 'Scrub Timeline', 'default_shortcut': 'K', 'command': ''},
                'switch_viewport_background': {'label': 'Switch Viewports Background', 'default_shortcut': 'Alt+B', 'command': ''},
                'switch_viewport_background_current': {'label': 'Switch Current Viewport Background', 'default_shortcut': 'Ctrl+Alt+B', 'command': ''},
                'change_particles_display': {'label': 'Change Particles Display', 'default_shortcut': '', 'command': ''},
                'toggle_cooking_mode': {'label': 'Toggle Cooking Mode', 'default_shortcut': '', 'command': ''},
                'triggerupdate_viewport': {'label': 'Trigger update Viewport', 'default_shortcut': '', 'command': ''},
                'create_node_preview': {'label': 'Create Node Preview', 'default_shortcut': '', 'command': ''},
                }
            for shortcut, values in shortcuts.items():
                self.shortcuts[shortcut].addLabel(values['label'])
                self.shortcuts[shortcut].addSpacer()
                self.shortcuts[shortcut].addWidget(qt.KeySequenceRecorder(values['default_shortcut']))
                self.shortcuts_vbox.addLayout(self.shortcuts[shortcut])
        self.row_layout.addWidget(self.shortcuts_groupbox)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.row_layout.addItem(spacer)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_prefs)
        self.buttons.rejected.connect(self.reject)
        self.row_layout.addWidget(self.buttons)
        self.set_tooltips()
        self.show()


    def is_there_new_prefs(self, version):
        """Houdini need several launches to get initialised correctly.
        The pref 'networkeditor.shownodeshapes' is checked in case it is the very first time Houdini is launched and basic prefs are not set yet.
        In that case lots of the settings can't be set, that's why we delay the display of the UI"""
        return not self.check or not hou.getPreference('networkeditor.shownodeshapes') or int(hou.getPreference('custom.regnareb.firstlaunch') or 0) < version

    def save_prefs(self):
        if self.is_there_new_prefs(1):
            settings = {'networkeditor.shownodeshapes': '0', 'networkeditor.showsimpleshape': '1', 'networkeditor.doautomovenodes': '0', 'networkeditor.showanimations': '0', 'networkeditor.maxflyoutscale': '5', 'tools.createincontext.val': '1', 'tools.sopviewmode.val': '0', 'general.desk.val': self.interface['general.desk.val'].combobox.currentText()}
            for setting, val in settings.items():
                if self.interface[setting].checkbox.checkState():
                    hou.setPreference(setting, val)

            if self.interface['compact_mode'].checkbox.checkState():
                hou.setPreference('general.ui.icon_size', 'Compact')  # DOESNT WORK
                hou.setPreference('general.uiplaybar.menu', '1')  # Set the playbar to compact mode

            if self.interface['general.ui.scale'].checkbox.checkState():
                hou.setPreference('ui.scale', str(self.interface['general.ui.scale'].field.value()))  # DOESNT WORK
                hou.setPreference('general.ui.scale', str(self.interface['general.ui.scale'].field.value()))  # DOESNT WORK

            # Custom Tools Default Preferences
            set_preference('custom.regnareb.scrub_timeline_mode', 'relative')
            set_preference('custom.regnareb.scrub_timeline_keep_pressed', '1')
            set_preference('custom.regnareb.preview_resolutionX', '640')
            set_preference('custom.regnareb.preview_resolutionY', '640')
            set_preference('custom.regnareb.preview_widthratio', '1')

        self.save_shortcuts()
        # Set this custom preference so that the window is only displayed once or when new settings are implemented
        set_preference('custom.regnareb.firstlaunch', str(VERSION))
        self.close()

    def save_shortcuts(self):
        # hou.hotkeys.addAssignment("h.pane.parms.copy_parm", "ctrl+C")  # Set shortcuts for copy/paste parameters
        # hou.hotkeys.addAssignment("h.pane.parms.paste_refs", "ctrl+V")
        # for each shortcut :
        # - check if it exists and is in the same scope as the current tool
        # - unassign it if it already exists
        # - assigne the new shortcut
        pass

    def check_shortcut(self):
        # check if the shortcut exists and is in the same scope as the current tool
        pass

    def set_tooltips(self):
        tooltips = {
            'networkeditor.shownodeshapes': 'Use rectangular node shapes only',
            'networkeditor.showsimpleshape': "In the network editor's View menu, you can turn off display of custom node shapes. If that option and this option are both on, Houdini uses an even simpler default node shape (a simple rectangle instead of a rounded rectangle). This may speed up the display of extremely complex networks.",
            'networkeditor.doautomovenodes': "Won't auto move nodes when connecting a node in between closed ",
            'networkeditor.showanimations': 'Animates certain changes and transitions in the network editor for clarity (for example, moving nodes out the way when a new node is placed). Turn this off to disable animations.',
            'networkeditor.maxflyoutscale': 'When opening a scene, change the Desktop panel arrangement to the one selected.',
            'tools.createincontext.val': 'Geometry will be created within the current context (eg. another piece of geometry in the same object).',
            'tools.sopviewmode.val': 'Geometry is displayed from the node with the display flag enabled.',
            'compact_mode': 'Change the playbar and UI icon size to compact.',
            'general.ui.scale': 'Change the UI scale globally.',
            'general.desk.val': 'Always force this Desktop when launching Houdini or opening a new scene.',
        }
        for key, tooltip in tooltips.items():
            self.interface[key].setToolTip(tooltip)





class Preferences(QtWidgets.QDialog):
    def __init__(self):
        super(Preferences, self).__init__(hou.ui.mainQtWindow())
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.setWindowTitle('Regnareb Preferences')

        self.onnewscene = collections.defaultdict(qt.RowLayout)
        self.onnewscene['on_open_go_manual'].addCheckbox('Set cooking to Manual')
        self.onnewscene['on_open_sopviewmode'].addCheckbox('Set view to "Show Display Operator"')
        self.onnewscene['on_open_hide_other_objects'].addCheckbox('Set view to "Hide other objects"')
        self.onnewscene['on_open_use_color_scheme'].addCheckbox('Use Default Color Scheme')
        # self.onnewscene['on_open_disable_nodes_shapes'].addCheckbox('Disable nodes shapes', True)

        self.network = collections.defaultdict(qt.RowLayout)
        self.network['transfer_display_node'].addCheckbox('Transfer Display Flag on child connection')
        self.network['create_null_shift_click'].addCheckbox('Create a NULL when Ctrl+Shift clicking with a node selected')
        self.network['drag_and_drop'].addCheckbox('Enable Drag And Drop of files from File Explorer')
        self.network['drag_and_drop_in_context'].addCheckbox('Always try to create drag and dropped files in the current context')
        self.network['nodepreview_resolution'].addLabel('Node Preview Resolution')
        self.network['nodepreview_resolution'].addField(maximum=1000)
        self.network['nodepreview_resolution'].addField(maximum=1000)
        self.network['nodepreview_widthratio'].addLabel('Node Preview Width Ratio')
        self.network['nodepreview_widthratio'].addField()

        self.viewport = collections.defaultdict(qt.RowLayout)
        self.viewport['scrub_timeline_keep_pressed'].addCheckbox('Scrub Timeline tool shortcut needs to be kept pressed')
        self.viewport['scrub_timeline_mode'].addLabel('Scrub Timeline mode: ')  # 'Scrub Timeline tool relative mode'
        self.viewport['scrub_timeline_mode'].addSpacer()
        self.viewport['scrub_timeline_mode'].addCombobox(['Relative', 'Absolute'])  # 'Scrub Timeline tool relative mode'
        self.viewport['viewport_colors'].addLabel('Viewport Colors')
        # self.viewport['viewport_colors'].addSpacer()
        scheme = self.viewport['viewport_colors'].addCombobox(['Light', 'Dark', 'Grey'])
        topcolor = self.viewport['viewport_colors'].addButton('Top')
        bottomcolor = self.viewport['viewport_colors'].addButton('Bot')
        # previewcolor = self.viewport['viewport_colors'].addButton()
        # previewcolor.setMaximumWidth(35)
        scheme.currentIndexChanged.connect(self.get_scheme)
        topcolor.clicked.connect(functools.partial(self.choose_color, topcolor))
        bottomcolor.clicked.connect(functools.partial(self.choose_color, bottomcolor))
        self.row_layout = QtWidgets.QVBoxLayout()

        self.onnewscene_groupbox = QtWidgets.QGroupBox('On Scene Open')
        self.onnewscene_vbox = QtWidgets.QVBoxLayout()
        self.onnewscene_groupbox.setLayout(self.onnewscene_vbox)
        for i in self.onnewscene.values():
            self.onnewscene_vbox.addLayout(i)

        self.network_groupbox = QtWidgets.QGroupBox('Network View')
        self.network_vbox = QtWidgets.QVBoxLayout()
        self.network_groupbox.setLayout(self.network_vbox)
        for i in self.network.values():
            self.network_vbox.addLayout(i)

        self.viewport_groupbox = QtWidgets.QGroupBox('Viewport View')
        self.viewport_vbox = QtWidgets.QVBoxLayout()
        self.viewport_groupbox.setLayout(self.viewport_vbox)
        for i in self.viewport.values():
            self.viewport_vbox.addLayout(i)

        self.row_layout.addWidget(self.onnewscene_groupbox)
        self.row_layout.addWidget(self.network_groupbox)
        self.row_layout.addWidget(self.viewport_groupbox)
        self.row_layout.addStretch()

        self.buttons_layout = qt.RowLayout()
        self.buttons_layout.addSpacer()
        for i in ['apply', 'accept', 'close']:
            btn = self.buttons_layout.addButton(i.capitalize())
            btn.clicked.connect(functools.partial(self.buttons, i))
        self.row_layout.addLayout(self.buttons_layout)

        self.setLayout(self.row_layout)
        self.setContentsMargins(0, 0, 0, 0)
        # self.set_tooltips()
        self.load_prefs()
        self.show()

    def get_allcheckoxes_ui(self):
        all_checkboxes = {}
        all_checkboxes.update(self.onnewscene)
        all_checkboxes.update({k:v for k,v in self.network.items() if 'nodepreview' not in k})
        all_checkboxes.update({'scrub_timeline_keep_pressed': self.viewport['scrub_timeline_keep_pressed']})
        return all_checkboxes

    def load_prefs(self):
        all_checkboxes = self.get_allcheckoxes_ui()
        for name, values in all_checkboxes.items():
            name = 'custom.regnareb.{}'.format(name)
            value = hou.getPreference(name) or '1'  # set default state if the pref does not exists
            value = QtCore.Qt.Checked if value=='1' else QtCore.Qt.Unchecked
            values.checkbox.setCheckState(value)
        index = self.viewport['scrub_timeline_mode'].combobox.findText(hou.getPreference('custom.regnareb.scrub_timeline_mode') or 'Relative')
        self.viewport['scrub_timeline_mode'].combobox.setCurrentIndex(index)
        self.network['nodepreview_resolution'].setValues([int(hou.getPreference('custom.regnareb.preview_resolutionX')), int(hou.getPreference('custom.regnareb.preview_resolutionY'))])
        self.network['nodepreview_widthratio'].setValues([int(hou.getPreference('custom.regnareb.preview_widthratio'))])
        self.load_prefs_viewportcolors()

    def load_prefs_viewportcolors(self, scheme=None):
        self.viewport_colors = common.sceneviewer.ViewportColor(scheme)
        index = self.viewport['viewport_colors'].combobox.findText(self.viewport_colors.scheme.name())
        self.viewport['viewport_colors'].combobox.setCurrentIndex(index)
        top = self.viewport_colors.colors.get('BackgroundColor', None)
        bottom = self.viewport_colors.colors.get('BackgroundBottomColor', None)
        self.update_colors_ui(top, bottom)

    def save_prefs(self):
        all_checkboxes = self.get_allcheckoxes_ui()
        for name, values in all_checkboxes.items():
            name = 'custom.regnareb.{}'.format(name)
            state = values.checkbox.checkState()
            value = '1' if state==QtCore.Qt.Checked else '0'
            set_preference(name, value)
        set_preference('custom.regnareb.scrub_timeline_mode', self.viewport['scrub_timeline_mode'].combobox.currentText())
        set_preference('custom.regnareb.preview_resolutionX', str(self.network['nodepreview_resolution'].fields[0].value()))
        set_preference('custom.regnareb.preview_resolutionY', str(self.network['nodepreview_resolution'].fields[1].value()))
        set_preference('custom.regnareb.preview_widthratio', str(self.network['nodepreview_widthratio'].field.value()))
        self.viewport_colors.save_colors()

    def buttons(self, action):
        if action in ['accept', 'apply']:
            self.save_prefs()
            self.load_prefs()
        if action in ['accept', 'close']:
            self.close()

    def get_scheme(self):
        text = self.viewport['viewport_colors'].combobox.currentText()
        scheme = getattr(hou.viewportColorScheme, text)
        self.load_prefs_viewportcolors(scheme)

    def update_colors_ui(self, top=None, bot=None):
        if top and 'ALPHA' not in top:
            if '@' in top:
                top = self.viewport_colors.colors[top.replace('@', '')]
            self.viewport['viewport_colors'].buttons[0].setStyleSheet('background-color: rgba({}); border: none;'.format(','.join(str(i) for i in top)))
        if bot and '@' and 'ALPHA' not in bot:
            if '@' in bot:
                bot = self.viewport_colors.colors[bot.replace('@', '')]
            self.viewport['viewport_colors'].buttons[1].setStyleSheet('background-color: rgba({}); border: none;'.format(','.join(str(i) for i in bot)))
        # self.viewport['viewport_colors'].buttons[2].setStyleSheet('background: qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 {}, stop:1 {});; border: none;'.format(top, bottom))

    def choose_color(self, btn):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            btn.setStyleSheet('background-color: rgb({}); border: none;'.format(','.join(str(i) for i in color.toTuple())))
            kwarg = {btn.text().lower(): list(color.toTuple())}

            self.update_colors_ui(**kwarg)
            self.viewport_colors.set_backgroundcolors(**kwarg)

    def set_tooltips(self):
        self.onnewscene['on_open_go_manual'].setToolTip('When opening a scene, the cooking will be set to Manual to prevent the loading of a heavy scene.')
        self.onnewscene['on_open_hide_other_objects'].setToolTip('When opening a scene the viewports will be set to "Hide other obects" to prevent the loading of all objects.')
        self.network['transfer_display_node'].setToolTip("When connecting a child node to a Displayed one, the connected node will inherit the Display flag unless the child is on the ignore list (in case it's aheavy node)")
        self.network['create_null_shift_click'].setToolTip('If you have a node selected in the network view and shift click on an empty area, it will create a NULL node connected to that selected node.')
        self.network['drag_and_drop_in_context'].setToolTip('If this is checked, drag and dropping a file in Houdini will always create the nodes in the current context. Otherwise it follows the Houdini preference.')
        self.viewport['scrub_timeline_keep_pressed'].setToolTip('You need to keep the shortcut pressed then click on the viewport to change the current time like in Maya.\nOtherwise it is used as a classic shortcut.')
        self.viewport['scrub_timeline_mode'].setToolTip('Relative mode means the timeline moves with mouse movement.\nAbsolute mode means the horizontal axis of the viewport is the same as the timline,\nif you click on the left you are set to the beginning, on the right at the end.')
        self.viewport['viewport_colors'].setToolTip('Set your viewport color sceme and background colors.')

def show_prefs():
    ui = Preferences()
    return ui

def show_firstlaunch(check=True):
    ui = FirstLaunch(check)
    return ui
