bl_info = {
    "name": "Funciones Útiles",
    "author": "Norte",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "Properties > Material",
    "description": "Herramientas rápidas de materiales, UVs y atajos de transformación",
    "category": "World of Warcraft",
}

import bpy
import os
import re
from math import radians
from mathutils import Matrix, Vector

addon_keymaps = []

# =====================================================
# OPERADOR 1 – Materiales opacos
# =====================================================

class MATERIAL_OT_opacos(bpy.types.Operator):
    bl_idname = "material.materiales_opacos"
    bl_label = "¿Tu material se transparenta? Arreglar"
    bl_description = "Cambia todos los materiales a OPAQUE"

    def execute(self, context):
        count = 0

        for mat in bpy.data.materials:
            if mat and mat.use_nodes:
                if mat.blend_method != 'OPAQUE':
                    mat.blend_method = 'OPAQUE'
                    count += 1

        self.report({'INFO'}, f"Materiales cambiados a OPAQUE: {count}")
        return {'FINISHED'}


# =====================================================
# OPERADOR 2 – Materiales sin brillo
# =====================================================

class MATERIAL_OT_sin_brillo(bpy.types.Operator):
    bl_idname = "material.materiales_sin_brillo"
    bl_label = "Materiales sin brillo, como en el WoW"
    bl_description = "Quita brillo a todos los Principled BSDF"

    def execute(self, context):
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        node.inputs['Specular'].default_value = 0.0
                        node.inputs['Roughness'].default_value = 1.0
                        node.inputs['Specular Tint'].default_value = 0.0
                        node.inputs['Metallic'].default_value = 0.0

        return {'FINISHED'}


# =====================================================
# OPERADOR 3 – Renombrar UVMap
# =====================================================

class OBJECT_OT_renombrar_uv(bpy.types.Operator):
    bl_idname = "object.renombrar_uvmap"
    bl_label = "Renombrar todas las UV a UVMap"
    bl_description = "Renombra todas las UVs a UVMap"

    def execute(self, context):
        new_name = "UVMap"

        total_objs = 0
        total_uvs = 0
        sin_uv = []

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                total_objs += 1
                uvl = obj.data.uv_layers
                if not uvl:
                    sin_uv.append(obj.name)
                    continue
                for uv in uvl:
                    uv.name = new_name
                    total_uvs += 1

        def draw(self, context):
            self.layout.label(text=f"Objetos procesados: {total_objs}")
            self.layout.label(text=f"UV maps renombradas: {total_uvs}")
            if sin_uv:
                self.layout.label(text=f"Sin UVs: {', '.join(sin_uv[:5])}...")
                self.layout.label(text=f"({len(sin_uv)} objetos sin UVs)")

        context.window_manager.popup_menu(
            draw,
            title="Renombrado UVs completado ✅",
            icon='INFO'
        )

        return {'FINISHED'}


# =====================================================
# OPERADOR 4 – Quitar prefijo mat_
# =====================================================

class MATERIAL_OT_quitar_prefijo(bpy.types.Operator):
    bl_idname = "material.quitar_prefijo_mat"
    bl_label = "Quitar prefijo mat_ de los materiales"
    bl_description = "Elimina el prefijo 'mat_' del nombre de todos los materiales."

    def execute(self, context):
        PREFIX = "mat_"
        count = 0

        for mat in bpy.data.materials:
            if mat.name.startswith(PREFIX):
                mat.name = mat.name[len(PREFIX):]
                count += 1

        self.report({'INFO'}, f"Materiales renombrados: {count}")
        return {'FINISHED'}


# =====================================================
# OPERADOR 5 – Nombre según textura
# =====================================================

class MATERIAL_OT_nombre_por_textura(bpy.types.Operator):
    bl_idname = "material.nombre_por_textura"
    bl_label = "Nombrar material como su Imagen"
    bl_description = "Renombra todos los materiales según su textura (sin extensión)."

    def execute(self, context):
        count = 0

        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    filepath = node.image.filepath
                    filename = os.path.basename(filepath)
                    name_without_ext = os.path.splitext(filename)[0]
                    mat.name = name_without_ext
                    count += 1
                    break

        self.report({'INFO'}, f"Materiales renombrados por textura: {count}")
        return {'FINISHED'}


# =====================================================
# OPERADOR 6 – Eliminar .001 .002 etc de materiales
# =====================================================

class MATERIAL_OT_eliminar_duplicados(bpy.types.Operator):
    bl_idname = "material.eliminar_duplicados_001"
    bl_label = "Eliminar los .001 de los materiales"
    bl_description = "Unifica materiales con sufijos .001/.002/etc y elimina duplicados"

    def execute(self, context):

        pattern = re.compile(r"^(.*)\.(\d+)$")
        groups = {}

        for mat in bpy.data.materials:
            match = pattern.match(mat.name)
            if match:
                base_name = match.group(1)
                number = int(match.group(2))
                groups.setdefault(base_name, []).append((number, mat))

        total_removed = 0

        for base_name, mats in groups.items():

            base_material = bpy.data.materials.get(base_name)

            if base_material is None:
                mats.sort(key=lambda x: x[0])
                lowest_number, lowest_mat = mats.pop(0)
                lowest_mat.name = base_name
                base_material = lowest_mat

            for number, mat in mats:

                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        for slot in obj.material_slots:
                            if slot.material == mat:
                                slot.material = base_material

                bpy.data.materials.remove(mat, do_unlink=True)
                total_removed += 1

        self.report({'INFO'}, f"Materiales duplicados eliminados: {total_removed}")
        return {'FINISHED'}


# =====================================================
# PANEL – ARRIBA DEL TODO
# =====================================================

class MATERIAL_PT_tools_norte(bpy.types.Panel):
    bl_label = "WoW: Atajos Útiles"
    bl_idname = "MATERIAL_PT_tools_norte"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_order = -100

    def draw(self, context):
        layout = self.layout
        layout.operator("material.materiales_opacos", icon='MATERIAL')
        layout.operator("material.materiales_sin_brillo", icon='SHADING_RENDERED')
        layout.separator()
        layout.operator("object.renombrar_uvmap", icon='UV')
        layout.separator()
        layout.operator("material.quitar_prefijo_mat", icon='SORTALPHA')
        layout.operator("material.nombre_por_textura", icon='FILE_IMAGE')
        layout.separator()
        layout.operator("material.eliminar_duplicados_001", icon='TRASH')


# =====================================================
# OPERADOR EXTRA – Rotar 90° en Z (Shift + R)
# =====================================================

class NORTE_OT_rotate_90_z(bpy.types.Operator):
    bl_idname = "norte.rotate_90_z"
    bl_label = "Rotar 90° en Z"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = context.selected_objects
        if not objs:
            return {'CANCELLED'}

        center = Vector((0.0, 0.0, 0.0))
        for obj in objs:
            center += obj.location
        center /= len(objs)

        rot = Matrix.Rotation(radians(90), 4, 'Z')

        for obj in objs:
            obj.location -= center
            obj.location = rot @ obj.location
            obj.location += center
            obj.rotation_euler.rotate(rot)

        return {'FINISHED'}


# =====================================================
# REGISTER
# =====================================================

classes = (
    MATERIAL_OT_opacos,
    MATERIAL_OT_sin_brillo,
    OBJECT_OT_renombrar_uv,
    MATERIAL_OT_quitar_prefijo,
    MATERIAL_OT_nombre_por_textura,
    MATERIAL_OT_eliminar_duplicados,
    MATERIAL_PT_tools_norte,
    NORTE_OT_rotate_90_z,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(
            NORTE_OT_rotate_90_z.bl_idname,
            type='R',
            value='PRESS',
            shift=True
        )
        addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()