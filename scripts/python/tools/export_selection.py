"""Module for exporting selected Houdini network items to .cpio archives or standalone .hip scenes."""

import os
import sys
import json
import subprocess
import tempfile
import logging
import hou
import lib.pythonlib.iopath as iopath
import common.hou_utils

logger = logging.getLogger(__name__)


FLASHMESSAGE_DURATION = 3
HYTHON_TIMEOUT = 120
HYTHON_RUNNER = """
import json
import sys

import hou

with open(sys.argv[1], encoding='utf-8') as f:
    job = json.load(f)

hou.hipFile.clear(suppress_save_prompt=True)

# Reconstruct intermediate hierarchy
for parent_path, type_name, node_name in job['ancestry']:
    full_path = parent_path.rstrip('/') + '/' + node_name
    if hou.node(full_path) is not None:
        continue
    parent = hou.node(parent_path)
    if parent is None:
        raise RuntimeError('Cannot recreate hierarchy, parent not found: ' + parent_path)
    parent.createNode(type_name, node_name, run_init_scripts=False, exact_type_name=True)

target_context = hou.node(job['target_parent'])
if target_context is None:
    raise RuntimeError('Target parent not found: ' + job['target_parent'])

target_context.loadItemsFromFile(job['cpio'], ignore_load_warnings=True)
hou.hipFile.save(job['target_hip'])
"""


def _build_ancestry(parent_node: hou.Node) -> list[tuple[str, str, str]]:
    """Builds an ordered chain from root down to parent_node to recreate hierarchy."""
    ancestry = []
    curr = parent_node
    parent = curr.parent()
    # The root node ('/') is the only one without a parent, so the loop stops right below it.
    while parent is not None:
        ancestry.append((parent.path(), curr.type().name(), curr.name()))
        curr, parent = parent, parent.parent()
    ancestry.reverse()
    return ancestry


def export_nodes_to_file(items: list[hou.NetworkMovableItem], extension: str = '', editor: hou.PaneTab | None = None) -> None:
    """Exports the selection to a native Houdini .cpio or .hip network file."""
    if not common.hou_utils.validate_same_parent(items):
        return

    if extension != '.cpio':
        extension = common.hou_utils.get_allowed_extensions()['scene']

    chosen = hou.ui.selectFile(title=f'Export Selection to {extension}', pattern=f'*{extension}', chooser_mode=hou.fileChooserMode.Write)
    if not chosen:
        return
    chosen = iopath.normpath(hou.text.expandString(chosen))


    root, ext = os.path.splitext(chosen)
    if ext.lower() == extension:
        filepath = chosen
    elif ext.lower() in {'.cpio', '.hip', '.hiplc', '.hipnc'}:
        filepath = root + extension
    else:
        filepath = chosen + extension

    # Houdini's own overwrite prompt only covered the name typed in the dialog, not the fixed-up one.
    if os.path.exists(filepath):
        answer = hou.ui.displayMessage(
            f'{filepath}\nalready exists. Overwrite?',
            buttons=('Overwrite', 'Cancel'),
            severity=hou.severityType.Warning,
            default_choice=1,
            close_choice=1,
            title='Export Selection',
        )
        if answer != 0:
            return

    if extension == '.cpio':
        ok, error = export_to_cpio(filepath, items)
    else:
        ok, error = export_to_hip(filepath, items)

    if ok:
        image = 'STATUS_yes'
        message = f'Successfully exported selection to:\n{filepath}'
        severity = hou.severityType.Message
    else:
        image = 'DIALOG_error'
        message = 'Failed to export items'
        severity = hou.severityType.Error
        logger.error(f'Export failed:\n{error}')

    if editor is not None:
        editor.flashMessage(image, message, FLASHMESSAGE_DURATION)
    else:
        hou.ui.setStatusMessage(message.replace('\n', ' '), severity=severity)


def export_to_cpio(filepath: str, items: list[hou.Node]) -> tuple[bool, str]:
    try:
        parent_node = next((i.parent() for i in items))
        parent_node.saveItemsToFile(items, filepath, save_hda_fallbacks=True)
        return True, ''
    except (hou.OperationFailed, hou.PermissionError, OSError) as err:
        return False, str(err)


def export_to_hip(filepath: str, items: list[hou.Node]) -> tuple[bool, str]:
    """Exports the items to a clean, standalone .hip file using background hython."""
    try:
        parent_node = next((i.parent() for i in items))
        ancestry = _build_ancestry(parent_node)

        # The temporary directory (cpio bridge, runner script and job file) is removed on exit.
        with tempfile.TemporaryDirectory(prefix='hou_export_') as temp_dir:
            temp_cpio = os.path.join(temp_dir, 'selection.cpio').replace('\\', '/')
            runner_path = os.path.join(temp_dir, 'runner.py')
            job_path = os.path.join(temp_dir, 'job.json')

            # 1. Dump nodes to temporary cpio
            parent_node.saveItemsToFile(items, temp_cpio, save_hda_fallbacks=True)

            # 2. Write the static runner script and its job parameters
            with open(runner_path, 'w', encoding='utf-8') as f:
                f.write(HYTHON_RUNNER)
            with open(job_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'ancestry': ancestry,
                        'cpio': temp_cpio,
                        'target_hip': filepath,
                        'target_parent': parent_node.path(),
                    },
                    f,
                )

            # 3. Launch hython silently
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if sys.platform == 'win32' else 0
            result = subprocess.run(
                [common.hou_utils.get_hython_binary(), runner_path, job_path],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags,
                timeout=HYTHON_TIMEOUT,
            )
    except subprocess.TimeoutExpired:
        return False, f'hython did not finish within {HYTHON_TIMEOUT} seconds and was killed'
    except (hou.OperationFailed, hou.PermissionError, OSError, subprocess.SubprocessError) as err:
        return False, str(err)

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        return False, f'hython exited with code {result.returncode}:\n{details}'
    if not os.path.isfile(filepath) or os.stat(filepath).st_size == 0:
        return False, 'hython finished without errors but the scene file was not written'
    return True, ''
