bl_info = {
    "name": "Copy Bone Transforms",
    "author": "Deez nuts",
    "blender": (4, 0, 0),
    "category": "Rigging",
}

from copy import deepcopy
from typing import cast
import bpy as blender

class CopyBoneTransforms(blender.types.Operator):
    """Copy transforms to pose bones from an object"""
    bl_idname="object.copybonetransforms"
    bl_label="Copy bone transforms"
    bl_options={'REGISTER', 'UNDO'}
    
    def execute(self, context):
        start_mode = context.mode

        pose_obj = context.scene.objects.get("rig_pose")
        edit_obj = context.scene.objects.get("rig_edit")

        # Assign pose and edit objects if cannot find in scene by name
        if pose_obj is None or edit_obj is None:
            pose_obj = context.active_object
            selected = context.selected_objects
            for object in selected:
                if pose_obj.as_pointer() != object.as_pointer():
                    edit_obj = object

        pose_obj = cast(blender.types.Object, pose_obj)
        edit_obj = cast(blender.types.Object, edit_obj)

        context.view_layer.objects.active = edit_obj
        blender.ops.object.mode_set(mode="POSE")
        
        # Add bone transform constraints
        for bone in edit_obj.pose.bones.items():
            bone = cast(blender.types.PoseBone, bone[1])
            constraint = bone.constraints.new("COPY_TRANSFORMS")
            constraint = cast(blender.types.CopyTransformsConstraint, constraint)
            constraint.target = pose_obj
            constraint.subtarget = bone.name
            constraint.target_space = "POSE"
            constraint.owner_space = "POSE"

            blender.ops.pose.select_all(action="DESELECT")
            context.active_object.data.bones.active = bone.bone # type: ignore
            bone.bone.select = True

            blender.ops.constraint.apply(constraint=constraint.name, owner="BONE")

        for child in edit_obj.children:
            blender.ops.object.mode_set(mode="OBJECT")

            old_modifier = child.modifiers.get("Armature")
            if old_modifier is None:
                break
            old_modifier = cast(blender.types.ArmatureModifier, old_modifier)

            new_modifier = child.modifiers.new("Armature", "ARMATURE")
            new_modifier = cast(blender.types.ArmatureModifier, new_modifier)
            new_modifier.object = old_modifier.object
            new_modifier.vertex_group = old_modifier.vertex_group

            context.view_layer.objects.active = child
            blender.ops.object.modifier_apply(modifier="Armature.001")

            context.view_layer.objects.active = edit_obj
            blender.ops.object.mode_set(mode="POSE")

            blender.ops.pose.armature_apply(selected=False)

        blender.ops.object.mode_set(mode=start_mode)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(CopyBoneTransforms.bl_idname)

def register():
    blender.utils.register_class(CopyBoneTransforms)
    blender.types.VIEW3D_MT_object.append(menu_func)
    blender.types.VIEW3D_MT_pose.append(menu_func)

def unregister():
    blender.utils.unregister_class(CopyBoneTransforms)

if __name__ == "__main__":
    register()