import os
import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.app.handlers import persistent

bl_info = {
    "name": "node group importer",
    "description": "Auto-import node groups from specified library file(s)",
    "author": "Lateasusual",
    "version": (1, 0, 0),
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

    # Skip importing this file if it's the currently open one
    fp = bpy.data.filepath
    if fp is not None and fp != '' and os.path.samefile(fp, path):
        print("Skipped import of node groups from active file", fp)
        return

    if overwrite:
        names, overrides = import_override(path)
        if len(names):
            print("Node groups loaded from" + (" included" if relative else ""), os.path.abspath(path), ":",
                  names)
        if len(overrides):
            print("Node groups overwritten from" + (" included" if relative else ""), os.path.abspath(path), ":",
                  overrides)
    else:
        names = import_keep(path, relative=relative)
        if len(names):
            print("Node groups loaded from" + (" included" if relative else ""), os.path.abspath(path), ":",
                  names)


def import_override(path_abs):
    D = bpy.data

    def appender(name):
        return "_DELETE_ME_" + name

    current_file = bpy.data.node_groups
    with bpy.data.libraries.load(path_abs) as (data_from, data_to):
        # Pass 1, non-overriden groups
        data_to.node_groups = [x for x in data_from.node_groups if x not in D.node_groups]
        names = [x for x in data_from.node_groups if x not in D.node_groups]
        override_names = set([x for x in data_from.node_groups if x in D.node_groups])
        ret_names = [x for x in data_from.node_groups if x in D.node_groups]

    mapping = dict([(appender(g.name), g.name) for g in D.node_groups if g.name in override_names])

    # "Backup" groups
    for g in D.node_groups:
        if g.name in override_names:
            g.name = appender(g.name)

    with D.libraries.load(path_abs) as (data_from, data_to):
        data_to.node_groups = [x for x in data_from.node_groups if x in override_names]

    for g in D.node_groups:
        if g.name in override_names:

            old = D.node_groups[appender(g.name)]
            for mat in bpy.data.materials:

                for node in mat.node_tree.nodes:
                    if node.type == 'GROUP':
                        if node.node_tree.name in mapping.keys():
                            node.node_tree = g

            D.node_groups.remove(old)

    return names, ret_names


def import_keep(path, relative=True):
    names = []
    # Load only node groups from library file as new blocks
    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.node_groups = [x for x in data_from.node_groups
                               if x not in bpy.data.node_groups]
        names.append(data_to.node_groups)
        # Keep our groups please
        for datablock in data_to.node_groups:
            if datablock in bpy.data.node_groups:
                bpy.data.node_groups[datablock].use_fake_user = True
    return names

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
