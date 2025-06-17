import os
import errno
import shutil
import urllib
import zipfile
import tempfile
import pathlib

import hou
import requests


def create_dir(path):
    """Creates a directory"""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def delete_dir(path):
    """Delete a directory"""
    try:
        shutil.rmtree(path)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise


def delete_file(path):
    """Delete a file"""
    try:
        os.remove(path)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise


def normpath(path):
    """Replace double escaped anti-slash to fix some problems on Windows"""
    return os.path.normpath(path).replace('\\', '/')





class Installer():

    def __init__(self):
        self.tmp_folder = tempfile.gettempdir()
        self.tmp_zip = os.path.join(self.tmp_folder, 'regnareb-tools.zip')
        self.tmp_unzipped = os.path.join(self.tmp_folder, 'regnareb-tools')
        self.packages_folder = os.path.join(hou.homeHoudiniDirectory(), 'packages')
        self.package_json = os.path.join(self.packages_folder, 'REGNAREB.json')
        self.response = requests.get("https://api.github.com/repos/regnareb/Houdini/releases/latest")
        self.version = self.response.json()['name']
        self.tool_folder = os.path.join(hou.homeHoudiniDirectory(), 'REGNAREB-TOOLS', self.version)

    def install(self, update=False):
        newversion = self.is_there_newversion()
        if update and not newversion:
            return
        if not newversion:
            donothing = hou.ui.displayCustomConfirmation('This version of the tool already exists.\nDelete the current one and replace it from Github?', buttons=('Replace', 'Do Nothing'), default_choice=1, close_choice=1)
            if donothing:
                return True

        urllib.request.urlretrieve(self.response.json()['assets'][0]['browser_download_url'], self.tmp_zip)  # Does this always overwrite the current file?

        with zipfile.ZipFile(self.tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(self.tmp_unzipped)

        delete_dir(self.tool_folder)
        shutil.move(os.path.join(self.tmp_unzipped, 'Houdini-tools'), self.tool_folder)

        create_dir(self.packages_folder)
        shutil.move(os.path.join(self.tool_folder, 'REGNAREB.json'), self.package_json)

        path = pathlib.Path(self.package_json)
        text = path.read_text()
        text = text.replace('%TOOLSPATH%', normpath(self.tool_folder))
        path.write_text(text)

        self.clean_temp()

        if update:
            hou.ui.displayMessage(f'The tools have been updated to version "{self.version}"\n\nChangelog:', details_expanded=True, details=self.response.json()['body'])
        else:
            hou.ui.displayMessage(f'The tools ({self.version}) have been installed in the folder "{self.tool_folder}"')

    def is_there_newversion(self):
        """Check if the last version on Github is present on the local disk"""
        return not os.path.isdir(self.tool_folder)

    def update_ui(self):
        newversion = self.is_there_newversion()
        if newversion:
            update = hou.ui.displayMessage(f'There is a new version of the Regnareb tools. Do you want to update to version "{self.version}"\n\nChangelog:', details_expanded=True, details=self.response.json()['body'])
        if update:
            self.install(update)

    def clean_temp(self):
        delete_file(self.tmp_zip)
        delete_dir(self.tmp_unzipped)


if __name__ in ['__main__', 'hou.session']:
    Installer().install()
