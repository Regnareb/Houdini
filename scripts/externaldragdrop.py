import os
import re
import logging
import hou
logger = logging.getLogger(__name__)


FILETYPES = {
    '.txt': {'nodetype': 'font', 'params': {'text': '%CONTENT%'}},
    '.abc': {'nodetype': 'alembic', 'params': {'fileName': '%FILEPATH%'}},
    '.usd': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.usda': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.usdc': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.fbx': {'nodetype': 'usdimport', 'params': {'input': 2, 'fbxfile': '%FILEPATH%'}},
    '.mdd': {'nodetype': 'mdd', 'params': {'file': '%FILEPATH%'}},
    '.ass': {'nodetype': 'arnold_asstoc', 'params': {'ass_file': '%FILEPATH%'}},
    '.rs': {'nodetype': 'redshift_packedProxySOP', 'params': {'RS_proxy_file': '%FILEPATH%'}}
}


def toNumber(s):
    """Convert a string to an int or a float depending of their types"""
    try:
        return int(s)
    except ValueError:
        return float(s)


def get_file_sequence(filepath):
    """Detect if the filepath is a single file or a sequence"""
    folder, filename = os.path.split(filepath)
    mo = re.findall('\d+', filename)
    mo = list(re.finditer('\d+', filename))
    for i in mo[::-1]:
        num = toNumber(i.group())
        decremented = os.path.join(folder, filename[:i.start()] + str(num - 1) + filename[i.end():])
        incremented = os.path.join(folder, filename[:i.start()] + str(num + 1) + filename[i.end():])
        if os.path.exists(decremented) or os.path.exists(incremented):
            return True, os.path.join(folder, filename[:i.start()] + '$F' + str(len(i.group())) + filename[i.end():])
    return False, filepath


def parse_strings(filepath, params):
    result = {}
    relpath = filepath.replace(hou.getenv('HIP'), '$HIP')  # Convert to relative path
    for i in params:
        result[i] = params[i].replace('%FILEPATH%', relpath)
        if '%CONTENT%' in result[i]:
            with open(filepath) as f:
                result[i] = result[i].replace('%CONTENT%', f.read())
    return result


def create_node(parent, nodetype, params, filepath, name, position, get_sequence=False):
    try:
        if get_sequence:
            _, filepath = get_file_sequence(filepath)
        params = parse_strings(filepath, params)
        logger.debug(parent, nodetype, params, filepath, name, position)
        node = parent.createNode(nodetype, name, force_valid_node_name=True)
        node.setPosition(position)
        node.setParms(params)
        return node
    except hou.OperationFailed:
        return False


def dropAccept(files):
    pane = hou.ui.paneTabUnderCursor()
    if pane.type() != hou.paneTabType.NetworkEditor:
        return False
    parent = pane.pwd()
    position = pane.cursorPosition()

    # Create a geo only if some files can be imported
    extensions = [os.path.splitext(os.path.basename(i))[-1] for i in files]
    if parent.type().name() == 'obj' and any(x in extensions for x in FILETYPES.keys()):
        parent = parent.createNode('geo', 'Geo')
        parent.setPosition(position)

    for i, filepath in enumerate(files):
        name, ext = os.path.splitext(os.path.basename(filepath))

        if ext == '.hip':
            hou.hipFile.load(filepath)
        elif hou.node(filepath):
            create_node(parent, 'object_merge', {'objpath1': '%FILEPATH%'}, filepath, name, position)
        elif parent.type().name() == 'geo':
            infos = FILETYPES.get(ext, {'nodetype': 'file', 'params': {'file': '%FILEPATH%'}})  # Create a file node if the extension is not in the list
            nodetype, params = infos['nodetype'], infos['params']
            create_node(parent, nodetype, params, filepath, name, position)
        elif parent.type().name() in ['mat', 'vopmaterial', 'materialbuilder', 'materiallibrary']:
            create_node(parent, 'texture', {'map': '%FILEPATH%'}, filepath, name, position, get_sequence=True)
        elif parent.type().name() == 'chopnet':
            create_node(parent, 'file', {'file': '%FILEPATH%'}, filepath, name, position)
        elif parent.type().name() in ['img', 'cop2net']:
            create_node(parent, 'file', {'filename1': '%FILEPATH%'}, filepath, name, position, get_sequence=True)
        elif parent.type().name() in ['stage', 'lopnet']:
            create_node(parent, 'reference', {'filepath1': '%FILEPATH%'}, filepath, name, position)
        elif parent.type().name() == 'redshift_vopnet':
            create_node(parent, 'redshift::TextureSampler', {'tex0': '%FILEPATH%'}, filepath, name, position)
        elif parent.type().name() in ['arnold_materialbuilder', 'arnold_vopnet']:
            create_node(parent, 'arnold::image', {'filename': '%FILEPATH%'}, filepath, name, position, get_sequence=True)
        # position += hou.Vector2(0, i)
    return True
