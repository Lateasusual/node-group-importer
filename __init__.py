import os
import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.app.handlers import persistent

bl_info = {
    "name": "node group importer",
    "description": "Auto-import node groups from specified library file(s)",
    "author": "Lateasusual",
    "version": (0, 0, 3),
    "blender": (2, 80, 1),
    "location": "Node Editor",
    "warning": '',
    "wiki_url": '',
    "category": "Node"
}


class NodeImporterAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    folder: StringProperty(
        name="Folder",
        subtype='FILE_PATH'
    )

    on_load: BoolProperty(
        name="Import Automatically",
        description="Imports node groups on file load"
    )

    overwrite: BoolProperty(
        name="Overwrite Existing",
        description="Overwrite node groups in current file with the same name"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Library folder (Leave blank to use addon directory)")
        layout.prop(self, 'folder')
        row = layout.row()
        row.prop(self, 'on_load')
        row.prop(self, 'overwrite')


class NOD_PT_NodeGroupImporterPanel(bpy.types.Panel):
    bl_label = "Node group importer"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Misc'

    def draw(self, context):
        layout = self.layout
        op = layout.operator("wm.update_linked_node_groups")
        op.overwrite = True



class NOD_OT_update_groups(bpy.types.Operator):
    """ Updates node groups linked using the importer addon """
    bl_label = "Reload Auto-Imported Node Groups"
    bl_idname = "wm.update_linked_node_groups"
    bl_options = {'REGISTER', 'UNDO'}

    overwrite: BoolProperty(
        name="Overwrite Existing"
    )

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if prefs.folder != "" and prefs.folder is not None:
            for file in get_files(path=prefs.folder):
                try:
                    import_groups_from_library(os.path.join(prefs.folder, file),
                                               relative=False, overwrite=self.overwrite)
                except:
                    print("Could not load file", os.path.join(prefs.folder, file))
        for file in get_files():
            import_groups_from_library(file, overwrite=self.overwrite)
        return {'FINISHED'}


def get_files(path=None):
    if path is None:
        path = os.path.dirname(__file__)

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".blend")]
    return files


def import_groups_from_library(path_arg, relative=True, overwrite=False):
    # Path is relative to addon install (next to __init__.py)
    if relative:
        path = os.path.join(os.path.dirname(__file__), path_arg)
    else:
        path = path_arg

    # Load only node groups from library file as new blocks
    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.node_groups = [x for x in data_from.node_groups
                               if overwrite or x not in bpy.data.node_groups]

        print("Node groups loaded from" + (" included" if relative else ""), path_arg, ":", data_to.node_groups)

        # Keep our groups please
        for datablock in data_to.node_groups:
            if datablock in bpy.data.node_groups:
                bpy.data.node_groups[datablock].use_fake_user = True


@persistent
def load_handler(dummy):
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.on_load:
        bpy.ops.wm.update_linked_node_groups(overwrite=prefs.overwrite)


classes = {
    NOD_OT_update_groups,
    NodeImporterAddonPreferences,
    NOD_PT_NodeGroupImporterPanel
}


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.app.handlers.load_post.remove(load_handler)


if __name__ == '__main__':
    register()
