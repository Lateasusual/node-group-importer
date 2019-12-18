import os
import bpy

# TODO GPL block

bl_info = {
    "name": "node group importer",
    "description": "Auto-import node groups from specified library file(s)",
    "author": "Lateasusual",
    "version": (0, 0, 1),
    "blender": (2, 80, 1),
    "location": "Node Editor",
    "warning": '',
    "wiki_url": '',
    "category": "Nodes"
}


class NOD_OT_update_groups(bpy.types.Operator):
    """ Updates node groups linked using the importer addon """
    bl_label = "Update Node Groups"
    bl_idname = "wm.update_linked_node_groups"

    def execute(self, context):
        import_groups_from_library("NodeTemplates.blend", addon_relative=True, override=True)
        return {'FINISHED'}


def import_groups_from_library(path, addon_relative=False, override=False):
    # Path is relative to addon install (next to __init__.py)
    if addon_relative:
        path = os.path.join(os.path.dirname(path), path)

    # Load only node groups from library file as new blocks
    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.node_groups = [x for x in data_from.node_groups
                               if override or x not in bpy.data.node_groups]

        # Keep our groups please
        for data in data_to.node_groups:
            data.use_fake_user = True



classes = {
    NOD_OT_update_groups
}


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == '__main__':
    register()
