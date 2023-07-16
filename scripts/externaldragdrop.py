import os
import re
import logging
import hou
import common.hou_utils
logger = logging.getLogger(__name__)


# TODO: Pouvoir drop une image pour faire une refimage dans /obj/ ou une background image dans /obj/geo


IMAGES = ['.als', '.bmp', '.cin', '.dds', '.dsm', '.exr', '.hdr', '.ies', '.jpeg', '.jpg', '.kdk', '.pic', '.pic.gz', '.pic.z', '.pix', '.png', '.psb', '.psd', '.ptex', '.ptx', '.qtl', '.rat', '.rgb', '.rgba', '.rla', '.rla16', '.rlb', '.rlb16', '.sgi', '.si', '.tbf', '.tga']
DISPLACE_TYPES = {'_bump': 0, '_bmp': 0, '_normal': 1, '_displace':2, '_displacen':2, '_displacev':3}
REGEX = re.compile('{}'.format('|'.join(DISPLACE_TYPES.keys())))



FILETYPES = {
    '.txt': {'nodetype': 'font', 'params': {'text': '%CONTENT%', 'usefile': 1, 'file': '%FILEPATH%'}},
    '.abc': {'nodetype': 'alembic', 'params': {'fileName': '%FILEPATH%'}},
    '.usd': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.usda': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.usdc': {'nodetype': 'usdimport', 'params': {'filepath1': '%FILEPATH%'}},
    '.obj': {'nodetype': 'obj_importer', 'params': {'sObjFile': '%FILEPATH%'}},
    '.fbx': {'nodetype': 'usdimport', 'params': {'input': 2, 'fbxfile': '%FILEPATH%'}},
    '.mdd': {'nodetype': 'mdd', 'params': {'file': '%FILEPATH%'}},
    '.ass': {'nodetype': 'arnold_asstoc', 'params': {'ass_file': '%FILEPATH%'}},
    '.rs': {'nodetype': 'redshift_packedProxySOP', 'params': {'RS_proxy_file': '%FILEPATH%'}}
}


NODE_CATEGORIES = {
    hou.chopNodeTypeCategory(): {'incontext': 'chopnet', 'root': '/ch', 'nodetype': 'file', 'params': {'file': '%FILEPATH%'}},
    hou.cop2NodeTypeCategory(): {'incontext': 'cop2net', 'root': '/obj', 'nodetype': 'file', 'params': {'filename1': '%FILEPATH%'}, 'get_sequence': True},
    hou.dopNodeTypeCategory(): {'incontext': 'dopnet', 'root': '/obj'},
    hou.lopNodeTypeCategory(): {'incontext': 'lopnet', 'root': '/stage', 'nodetype': 'reference', 'params': {'filepath1': '%FILEPATH%'}},
    hou.objNodeTypeCategory(): {'incontext': 'objnet', 'root': '/obj'},
    hou.ropNodeTypeCategory(): {'incontext': 'ropnet', 'root': '/out'},
    hou.shopNodeTypeCategory(): {'incontext': 'shopnet', 'root': '/shop', 'nodetype': 'texture', 'params': {'map': '%FILEPATH%'}},
    hou.sopNodeTypeCategory(): {'incontext': 'geo', 'root': '/obj'},
    hou.topNodeTypeCategory(): {'incontext': 'topnet', 'root': '/tasks'},
    hou.vopNodeTypeCategory(): {'incontext': 'matnet', 'root': '/mat'}
}


def dropAccept(files):
    merge = hou.getPreference('custom.regnareb.dragndrop.always_merge')
    pane = hou.ui.paneTabUnderCursor()
    if isinstance(pane, hou.NetworkEditor):
        position = pane.cursorPosition()
    elif isinstance(pane, hou.SceneViewer):
        position = hou.Vector2(0, 0)
    else:
        return False


    if pane.pwd().path() in ['/ch', '/img', '/tasks']:
        # Some contexts do not allow the creation of other managers, change panel path to /obj
        pane.cd('/obj')

    for filepath in files:
        root = pane.pwd()
        filename = os.path.basename(filepath)
        name = filename.split('.')[0]
        if hou.node(filepath):
            common.hou_utils.create_node(root, 'object_merge', name, {'objpath1': '%FILEPATH%'}, position, filepath)
        elif filename.endswith('.hip'):
            if merge or hou.ui.displayMessage('Do you want to open the .hip file or merge into the current one?', buttons=('Open', 'Merge')):
                hou.hipFile.merge(filepath)
                merge = True  # Don't ask again for all consecutive files
                continue
            else:
                hou.hipFile.load(filepath)
                return True

        extension = filter(filepath.lower().endswith, FILETYPES.keys() + IMAGES)
        for ext in extension:
            if ext in IMAGES:
                categories = [hou.vopNodeTypeCategory()]
                displace = re.search(REGEX, filename.lower())
                if displace:
                    nodetype = 'displacetexture'
                    params = {'texture': '%FILEPATH%', 'type': displace.group(0)}
                else:
                    nodetype = 'texture'
                    params = {'map': '%FILEPATH%'}
            else:
                categories = common.hou_utils.get_node_parent_categories(FILETYPES[ext]['nodetype'])
                nodetype = FILETYPES[ext]['nodetype']
                params = FILETYPES[ext]['params']


            if root.childTypeCategory() in categories:
                logger.debug('Compatible with current context')
                parent = root
            else:
                # If the node can't be created in the current context, create a context manager compatible with it
                logger.debug('Not compatible with current context {} {}'.format(ext, root.childTypeCategory()))
                if hou.getPreference('tools.createincontext.val'):
                    if len(categories) > 1:
                        index = hou.ui.displayMessage('The current context is not compatible with the "{}" extension.\nMultiple context manager are compatible, which one do you want to create?'.format(ext), buttons=([i.name().upper() for i in categories]))
                    else:
                        index = 0
                    parent_type = NODE_CATEGORIES[categories[index]]['incontext']
                    logger.debug('Create node: {}'.format(parent_type))
                    parent = root.createNode(parent_type)
                    parent.setPosition(position)
                else:
                    parent = hou.node(NODE_CATEGORIES[root.childTypeCategory()]['root'])

            common.hou_utils.create_node(parent, nodetype, name, params, position, filepath)
            break
        else:
            # If it's not a supported extension, try to create generic nodes for each context
            if root.childTypeCategory() == hou.objNodeTypeCategory():
                parent = root.createNode('geo', 'Geo')
                parent.setPosition(position)
                common.hou_utils.create_node(parent, 'file', name, {'file': '%FILEPATH%'}, position, filepath, get_sequence=True)
            # elif root.type().name() in ['mat', 'vopmaterial', 'materialbuilder', 'materiallibrary']:
            #     common.hou_utils.create_node(root, 'texture', name, {'map': '%FILEPATH%'}, position, filepath, get_sequence=True)
            # elif root.type().name() in ['chopnet']:
            #     common.hou_utils.create_node(root, 'file', name, {'file': '%FILEPATH%'}, position, filepath)
            # elif root.type().name() in ['img', 'cop2net']:
            #     common.hou_utils.create_node(root, 'file', name, {'filename1': '%FILEPATH%'}, position, filepath, get_sequence=True)
            # elif root.type().name() in ['stage', 'lopnet']:
            #     common.hou_utils.create_node(root, 'reference', name, {'filepath1': '%FILEPATH%'}, position, filepath)
            elif root.type().name() in ['redshift_vopnet']:
                common.hou_utils.create_node(root, 'redshift::TextureSampler', name, {'tex0': '%FILEPATH%'}, position, filepath)
            elif root.type().name() in ['arnold_materialbuilder', 'arnold_vopnet']:
                common.hou_utils.create_node(root, 'arnold::image', name, {'filename': '%FILEPATH%'}, position, filepath, get_sequence=True)
            elif NODE_CATEGORIES[root.childTypeCategory()].get('nodetype'):
                common.hou_utils.create_node(root, NODE_CATEGORIES[root.childTypeCategory()]['nodetype'], name, NODE_CATEGORIES[root.childTypeCategory()]['params'], position, filepath, get_sequence=NODE_CATEGORIES[root.childTypeCategory()].get('get_sequence'))
            else:
                common.hou_utils.create_node(root, 'file', name, {'file': '%FILEPATH%'}, position, filepath, get_sequence=True)

    return True
