import hou
import common.hou_utils

TOOL_parameters = ['label', 'icon', 'script', 'language', 'help', 'helpURL']



def update_shelf(data):
    """Update a shelf based on a dict() constructed from build_json_from_shelf() useful for iterating shelves while letting the user customise their shelves
    All tools will be forced updated with the dict() data even if the user modified it. Other tools or attributes of a tool won't be updated if it's not in the dict()
    You can add pre/post scripts when updating a tool, one use for that could be to add behaviour to modifiers (ctrl/shift/alt) when invoking the tool
    Do not change the "name" of a shelf/tool or you will have several references for the same tool. It can bypass PermissionErrors when files are write restricted.
    """
    try:
        hou.shelves.beginChangeBlock()
        shelf = common.hou_utils.get_shelf(name=data['name']) or hou.shelves.newShelf(file_path='', name=data['name'], label=data['label'])
        for name, parameters in data['tools'].items():
            t = hou.shelves.tool(name)
            if t:  # Update already existing tools with parameters in dict but keep already existing parameters
                t.setLabel(parameters.pop('label', t.label()))  # There are no label argument in hou.Tool.setData()
                parameters.setdefault('help_url', parameters.pop('helpURL', t.helpURL()))  # The attribute helpURL and argument for tool.setData(help_url) have not the same nomenclature
                for parm in [i for i in TOOL_parameters if i not in ['label', 'helpURL']]:
                    parameters.setdefault(parm, getattr(t, parm)())

                #  Give the ability to add post/pre scripts to an existing script
                prescript = parameters.pop('prescript', '')
                postscript = parameters.pop('postscript', '')
                if parameters.get('script') and (prescript or postscript):
                    parameters['script'] = '\n'.join([prescript, parameters['script'], postscript])

                t.setData(**parameters)
            else:  # Create new tool
                parameters['help_url'] = parameters.pop('helpURL', '')
                t = hou.shelves.newTool(name=name, **parameters)
            if t not in shelf.tools():  # Add it to the shelf
                shelf.setTools(list(shelf.tools()) + [t])

            tools = [y for x in data['order'] for y in shelf.tools() if x == y.name()]  # For Python 2.7 (dict unordered)
            diff = [i for i in shelf.tools() if i.name() not in data['order']]  # Add tools who were in the shelf, but are not in the initial dict order
            shelf.setTools(tools + diff)
        hou.shelves.endChangeBlock()
    except hou.PermissionError:
        # If the shelf files are not accessible, houdini will raise an exception.
        # Because of hou.shelves.endChangeBlock() the UI will still be updated even though it won't be saved on disk
        pass
    finally:
        return shelf


def build_json_from_shelf(shelf):
    """Build a json with all the data of a corresponding shelf. This way we can rebuild it procedurally with update_shelf()"""
    if isinstance(shelf, str):
        shelf = common.hou_utils.get_shelf(name=shelf) or common.hou_utils.get_shelf(label=shelf)
    result = {'label': shelf.label(), 'name': shelf.name(), 'tools': {}, 'order': []}
    for tool in shelf.tools():
        t = {}
        for parm in TOOL_parameters:
            attrib = getattr(tool, parm)()
            if attrib:
                t[parm] = attrib
        if t:
            result['order'].append(tool.name())  # For Python 2.7 (dict unordered)
            result['tools'][tool.name()] = t
    return result
