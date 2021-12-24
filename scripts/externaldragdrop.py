import os
import hou


FILETYPES = {
    '.txt': {'nodetype': 'font', 'param': 'fileName'},
    '.abc': {'nodetype': 'alembic', 'param': 'fileName'},
    '.usd': {'nodetype': 'usdimport', 'param': 'filepath1'},
    '.usda': {'nodetype': 'usdimport', 'param': 'filepath1'},
    '.usdc': {'nodetype': 'usdimport', 'param': 'filepath1'},
    '.ass': {'nodetype': 'arnold_asstoc', 'param': 'ass_file'},
    '.rs': {'nodetype': 'redshift_packedProxySOP', 'param': 'RS_proxy_file'}
}


def create_node(parent, nodetype, param, filepath, name, position):
    try:
        print(parent, nodetype, param, filepath, name, position)
        node = parent.createNode(nodetype, name, force_valid_node_name=True)
        node.setPosition(position)
        node.setParms({param: filepath})
        return node
    except hou.OperationFailed:
        return False


def dropAccept(files):
    print(files)
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
        filepath = filepath.replace(hou.getenv('HIP'), '$HIP')  # Convert to relative path
        position += hou.Vector2(i * 3, 0)

        if ext == '.hip':
            hou.hipFile.load(filepath)
        elif hou.node(filepath):
            create_node(parent, 'object_merge', 'objpath1', filepath, name, position)
        elif parent.type().name() == 'geo':
            infos = FILETYPES.get(ext, {'nodetype': 'file', 'param': 'file'})  # Create a file node if the extension is not in the list
            nodetype, param = infos['nodetype'], infos['param']
            create_node(parent, nodetype, param, filepath, name, position)
        elif parent.type().name() in ['mat', 'vopmaterial', 'materialbuilder', 'materiallibrary']:
            create_node(parent, 'texture::2.0', 'map', filepath, name, position)
        elif parent.type().name() == 'chopnet':
            create_node(parent, 'file', 'file', filepath, name, position)
        elif parent.type().name() in ['img', 'cop2net']:
            create_node(parent, 'file', 'filename1', filepath, name, position)
        elif parent.type().name() in ['stage', 'lopnet']:
            create_node(parent, 'reference', 'filepath1', filepath, name, position)
        elif parent.type().name() == 'redshift_vopnet':
            create_node(parent, 'redshift::TextureSampler', 'tex0', filepath, name, position)
        elif parent.type().name() in ['arnold_materialbuilder', 'arnold_vopnet']:
            create_node(parent, 'arnold::image', 'filename', filepath, name, position)
    return True
