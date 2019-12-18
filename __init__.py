import os
import bpy

# TODO GPL block

bl_info = {
    "name": "node group importer",
    "description": "Auto-import node groups from specified library file(s)",
    "author": "Lateasusual",
    "version": (0, 0, 2),
    "blender": (2, 80, 1),
    "location": "Node Editor",
    "warning": '',
    "wiki_url": '',
    "category": "Nodes"
}


class NodeImporterAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    folder: bpy.props.StringProperty(
        name="Folder",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Library folder (Leave blank to use addon directory)")
        layout.prop(self, 'folder')


class NOD_PT_NodeGroupImporterPanel(bpy.types.Panel):
    bl_label = "Node group importer"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Misc'

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.update_linked_node_groups")


class NOD_OT_update_groups(bpy.types.Operator):
    """ Updates node groups linked using the importer addon """
    bl_label = "Update Node Groups"
    bl_idname = "wm.update_linked_node_groups"

    def execute(self, context):
        preferences = context.preferences.addons[__name__].preferences
        if preferences.folder != "" and preferences.folder is not None:
            for file in get_files(path=preferences.folder):
                try:
                    import_groups_from_library(file)
                except:
                    print("File not found", file)
        for file in get_files():
            import_groups_from_library(file)
        return {'FINISHED'}


def get_files(path=None):
    if path is None:
        path = os.path.dirname(__file__)

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".blend")]
    return files


def import_groups_from_library(path, relative=True, override=False):
    # Path is relative to addon install (next to __init__.py)
    if relative:
        path = os.path.join(os.path.dirname(__file__), path)

    # Load only node groups from library file as new blocks
    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.node_groups = [x for x in data_from.node_groups
                               if override or x not in bpy.data.node_groups]

        # Keep our groups please
        for datablock in data_to.node_groups:
            if datablock in bpy.data.node_groups:
                bpy.data.node_groups[datablock].use_fake_user = True;



classes = {
    NOD_OT_update_groups,
    NodeImporterAddonPreferences,
    NOD_PT_NodeGroupImporterPanel
}


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == '__main__':
    register()
