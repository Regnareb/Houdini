import logging
import functools
import collections
from PySide2 import QtCore, QtGui, QtWidgets
import hou
import lib.pythonlib.qt as qt
import common.sceneviewer
logger = logging.getLogger(__name__)


def set_preference(name, value):
    if not hou.getPreference(name):
        hou.addPreference(name, value)
    else:
        hou.setPreference(name, value)


class FirstLaunch(QtWidgets.QDialog):
    def __init__(self):
        super(FirstLaunch, self).__init__(hou.ui.mainQtWindow())
        self.setWindowTitle('First Launch Initialisation')
        self.row_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.row_layout)

        self.interface = collections.defaultdict(qt.RowLayout)
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

        shortcuts = {
            'copy_parm': {'label': 'Copy Parameter', 'default_shortcut': 'Ctrl+Shift+C'},
            'paste_refs': {'label': 'Paste Parameter Reference', 'default_shortcut': 'Ctrl+Shift+V'},
            'paste_object_merge': {'label': 'Paste Object Merge', 'default_shortcut': 'Alt+V'},  # Remove existing shortcut
            'cycle_display_flag': {'label': 'Cycle Display Flag', 'default_shortcut': 'R'},  # Remove existing shortcut
            'display_next_output': {'label': 'Display Next Output', 'default_shortcut': 'Alt+X'},  # Remove existing shortcut
            'show_dependancy_links': {'label': 'Show dependancy Links', 'default_shortcut': 'Ctrl+D'},  # Remove existing shortcut
            'connect_selected_nodes': {'label': 'Connect Selected Nodes', 'default_shortcut': 'Shift+Y'},
            'scrub_timeline': {'label': 'Scrub Timeline', 'default_shortcut': 'K'},
            'switch_viewport_background': {'label': 'Switch Viewports Background', 'default_shortcut': 'Alt+B'},
            'switch_viewport_background_current': {'label': 'Switch Current Viewport Background', 'default_shortcut': 'Ctrl+Alt+B'},
            'change_particles_display': {'label': 'Change Particles Display', 'default_shortcut': ''},
            'toggle_cooking_mode': {'label': 'Toggle Cooking Mode', 'default_shortcut': ''},
            'triggerupdate_viewport': {'label': 'Trigger update Viewport', 'default_shortcut': ''},
            'create_node_preview': {'label': 'Create Node Preview', 'default_shortcut': ''},
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

    def save_prefs(self):
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

        set_preference('custom.regnareb.scrub_timeline_mode', 'relative')
        set_preference('custom.regnareb.scrub_timeline_keep_pressed', '1')
        self.save_shortcuts()

        set_preference('custom.regnareb.firstlaunch', '1')  # Set this custom preference so that the window is only displayed once
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
        self.interface['networkeditor.shownodeshapes'].setToolTip('Use rectangular node shapes only')
        self.interface['networkeditor.showsimpleshape'].setToolTip("In the network editor's View menu, you can turn off display of custom node shapes. If that option and this option are both on, Houdini uses an even simpler default node shape (a simple rectangle instead of a rounded rectangle). This may speed up the display of extremely complex networks.")
        self.interface['networkeditor.doautomovenodes'].setToolTip("Won't auto move nodes when connecting a node in between closed ")
        self.interface['networkeditor.showanimations'].setToolTip('Animates certain changes and transitions in the network editor for clarity (for example, moving nodes out the way when a new node is placed). Turn this off to disable animations.')
        self.interface['networkeditor.maxflyoutscale'].setToolTip('When opening a scene, change the Desktop panel arrangement to the one selected.')
        self.interface['tools.createincontext.val'].setToolTip('Geometry will be created within the current context (eg. another piece of geometry in the same object).')
        self.interface['tools.sopviewmode.val'].setToolTip('Geometry is displayed from the node with the display flag enabled.')
        self.interface['compact_mode'].setToolTip('Change the playbar and UI icon size to compact.')
        self.interface['general.ui.scale'].setToolTip('Change the UI scale globally.')
        self.interface['general.desk.val'].setToolTip('Always force this Desktop when launching Houdini or opening a new scene.')



class Preferences(QtWidgets.QDialog):
    def __init__(self):
        super(Preferences, self).__init__(hou.ui.mainQtWindow())
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.setWindowTitle('Regnareb Preferences')

        self.onnewscene = collections.defaultdict(qt.RowLayout)
        self.onnewscene['on_open_go_manual'].addCheckbox('Set cooking to Manual', True)
        self.onnewscene['on_open_sopviewmode'].addCheckbox('Set view to "Show Display Operator"', True)
        self.onnewscene['on_open_hide_other_objects'].addCheckbox('Set view to "Hide other objects"', True)
        self.onnewscene['on_open_use_color_scheme'].addCheckbox('Use Default Color Scheme', True)
        # self.onnewscene['on_open_disable_nodes_shapes'].addCheckbox('Disable nodes shapes', True)

        self.network = collections.defaultdict(qt.RowLayout)
        self.network['transfer_display_node'].addCheckbox('Transfer Display Flag on child connection', True)
        self.network['create_null_shift_click'].addCheckbox('Create a NULL when Ctrl+Shift clicking with a node selected', True)
        self.network['drag_and_drop'].addCheckbox('Enable Drag And Drop of files from File Explorer', True)
        self.network['drag_and_drop_in_context'].addCheckbox('Always try to create drag and dropped files in the current context', True)

        self.viewport = collections.defaultdict(qt.RowLayout)
        self.viewport['scrub_timeline_keep_pressed'].addCheckbox('Scrub Timeline tool shortcut needs to be kept pressed', True)
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

    def load_prefs(self):
        all_prefs_ui = dict(list(self.onnewscene.items()) + list(self.network.items()) + [('scrub_timeline_keep_pressed', self.viewport['scrub_timeline_keep_pressed'])])  # Merge all UI with checkboxes
        # all_prefs_ui = {**self.onnewscene, **self.network, 'scrub_timeline_keep_pressed': self.viewport['scrub_timeline_keep_pressed']}  # python 3
        for name, values in all_prefs_ui.items():
            name = 'custom.regnareb.{}'.format(name)
            value = hou.getPreference(name) or '1'  # set default state if the pref does not exists
            value = QtCore.Qt.Checked if value=='1' else QtCore.Qt.Unchecked
            values.checkbox.setCheckState(value)
        index = self.viewport['scrub_timeline_mode'].combobox.findText(hou.getPreference('custom.regnareb.scrub_timeline_mode') or 'Relative')
        self.viewport['scrub_timeline_mode'].combobox.setCurrentIndex(index)
        self.load_prefs_viewportcolors()

    def load_prefs_viewportcolors(self, scheme=None):
        self.viewport_colors = common.sceneviewer.ViewportColor(scheme)
        index = self.viewport['viewport_colors'].combobox.findText(self.viewport_colors.scheme.name())
        self.viewport['viewport_colors'].combobox.setCurrentIndex(index)
        top = self.viewport_colors.colors.get('BackgroundColor', None)
        bottom = self.viewport_colors.colors.get('BackgroundBottomColor', None)
        self.update_colors_ui(top, bottom)

    def save_prefs(self):
        all_prefs_ui = dict(list(self.onnewscene.items()) + list(self.network.items()) + [('scrub_timeline_keep_pressed', self.viewport['scrub_timeline_keep_pressed'])])  # Merge all UI with checkboxes
        # all_prefs_ui = {**self.onnewscene, **self.network, 'scrub_timeline_keep_pressed': self.viewport['scrub_timeline_keep_pressed']}  # python 3
        for name, values in all_prefs_ui.items():
            name = 'custom.regnareb.{}'.format(name)
            state = values.checkbox.checkState()
            value = '1' if state==QtCore.Qt.Checked else '0'
            set_preference(name, value)
        set_preference('custom.regnareb.scrub_timeline_mode', self.viewport['scrub_timeline_mode'].combobox.currentText())
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
    ui.show()
    return ui

def show_firstlaunch():
    """Houdini need several launches to get initialised correctly.
    The pref 'networkeditor.shownodeshapes' is checked in case it is the very first time Houdini is launched and basic prefs are not set yet.
    In that case lots of the settings can't be set, that's why we delay the display of the UI"""
    if not hou.getPreference('custom.regnareb.firstlaunch') and hou.getPreference('networkeditor.shownodeshapes'):
        ui = FirstLaunch()
        ui.show()
        return ui
