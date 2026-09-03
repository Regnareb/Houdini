"""Some IO functions are duplicated so that we can use this module outside of the environment"""

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




class PackageInstaller():

    def __init__(self):
        response = requests.get('https://api.github.com/repos/regnareb/Houdini/releases/latest')
        self.version = response.json()['name']
        self.download_url = response.json()['assets'][0]['browser_download_url']
        self.changelog = requests.get('https://raw.githubusercontent.com/Regnareb/Houdini/refs/heads/main/CHANGELOG.md').text.replace('<sup><sub><sup><sub>', '')
        self.tool_folder = os.path.join(hou.homeHoudiniDirectory(), 'REGNAREB-TOOLS', self.version)
        self.package_json = 'REGNAREB.json'
        self.replace_string = '%TOOLSPATH%'

    def install(self, update=False):
        newversion = self.is_there_newversion()
        if update and not newversion:
            return False
        if not newversion:
            donothing = hou.ui.displayCustomConfirmation('This version of the tool already exists.\nDelete the current one and replace it from Github?', buttons=('Replace', 'Do Nothing'), default_choice=1, close_choice=1)
            if donothing:
                return False

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_folder:
            package_folder = os.path.join(hou.homeHoudiniDirectory(), 'packages')
            tmp_zip = os.path.join(tmp_folder, 'download.zip')
            tmp_unzipped = os.path.join(tmp_folder, 'download')

            urllib.request.urlretrieve(self.download_url, tmp_zip)

            with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
                zip_ref.extractall(tmp_unzipped)
                folder = [i for i in os.scandir(tmp_unzipped) if i.is_dir()][0].path

            delete_dir(self.tool_folder)
            shutil.move(folder, self.tool_folder)

            create_dir(package_folder)
            shutil.move(os.path.join(self.tool_folder, self.package_json), os.path.join(package_folder, self.package_json))

            if self.replace_string:
                path = pathlib.Path(os.path.join(package_folder, self.package_json))
                text = path.read_text()
                text = text.replace(self.replace_string, normpath(self.tool_folder))
                path.write_text(text)

        if update:
            hou.ui.displayMessage(f'The tools have been updated to version "{self.version}"\n\nChangelog:', details_expanded=True, details=self.changelog)
        else:
            hou.ui.displayMessage(f'The tools ({self.version}) have been installed in the folder "{self.tool_folder}"')
        return True

    def is_there_newversion(self):
        """Check if the last version is present on the local disk"""
        return not os.path.isdir(self.tool_folder)

    def update_ui(self):
        newversion = self.is_there_newversion()
        if newversion:
            update = hou.ui.displayMessage(f'There is a new version of the Regnareb tools. Do you want to update to version "{self.version}"\n\nChangelog:', details_expanded=True, details=self.changelog)
        if update:
            self.install(update)


class QLibPackageInstaller(PackageInstaller):
    def __init__(self):
        self.version = 'qLib'
        self.download_url = 'https://github.com/qLab/qLib/archive/refs/heads/dev.zip'
        self.changelog = 'No Changelog Available - https://qlab.github.io/qLib/'
        self.tool_folder = os.path.join(hou.homeHoudiniDirectory(), 'qLib-master')
        self.package_json = 'qLib_package.json'
        self.replace_string = ''


class AELibPackageInstaller(PackageInstaller):
    def __init__(self):
        self.version = 'Aelib'
        self.download_url = 'https://github.com/Aeoll/Aelib/archive/refs/heads/master.zip'
        self.changelog = 'No Changelog Available - https://github.com/Aeoll/Aelib'
        self.tool_folder = os.path.join(hou.homeHoudiniDirectory(), 'AeLib')
        self.package_json = 'Aelib.json'
        self.replace_string = 'PATH/TO/aelib'


if __name__ in ['__main__', 'hou.session']:
    PackageInstaller().install()
