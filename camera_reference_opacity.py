import bpy
import rna_keymap_ui
from bpy.types import CameraBackgroundImage

bl_info = {
    "name": "Reference Opacity",
    "author": "MarshmallowCirno",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "Shortcut in the addon preferences",
    "description": "Adjust camera background reference image opacity",
    "warning": "",
    "doc_url": "https://gumroad.com/l/omgit",
    "tracker_url": "https://blenderartists.org/t/references-matching-setting-transforms-and-opacity-of-backgroud"
                   "-images/1417682",
    "category": "Camera",
}


class CAMERA_OT_background_opacity(bpy.types.Operator):
    """Adjust camera background opacity"""

    bl_idname = "camera.background_opacity"
    bl_label = "Background Opacity"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.region_3d.view_perspective == 'CAMERA'

    def __init__(self):
        self.cam_backgrounds: list[CameraBackgroundImage, float] = []
        self.last_mouse_x: int = 0

    def invoke(self, context, event):
        view = context.space_data
        scene = context.scene

        self.last_mouse_x = event.mouse_region_x
        cam = view.camera if view.use_local_camera else scene.camera
        self.cam_backgrounds = [
            (bg, bg.alpha)
            for bg in bpy.data.cameras[cam.data.name].background_images
            if bg.image and bg.show_background_image
        ]
        if not any(self.cam_backgrounds):
            self.report({'WARNING'}, "No visible backgrounds")
            return {'CANCELLED'}

        context.workspace.status_text_set(text="LMB, ENTER: Confirm | RMB, ESC: Cancel")
        context.window.cursor_modal_set('MOVE_X')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if event.type == 'MOUSEMOVE':
            mouse_x = event.mouse_region_x  # mouse position
            divisor = 3000 if event.shift else 500  # sensitivity divisor
            offset_x = mouse_x - self.last_mouse_x  # offset of cursor

            alpha_offset = offset_x / divisor

            for bg, alpha in self.cam_backgrounds:
                bg.alpha = bg.alpha + alpha_offset

            master_bg = self.cam_backgrounds[0][0]
            context.area.header_text_set("Background Opacity: {:.3f}".format(master_bg.alpha))
            self.last_mouse_x = event.mouse_region_x

        elif event.value == 'PRESS':

            if event.type in ('ESC', 'RIGHTMOUSE'):
                self.restore()
                self.finish(context)
                return {'CANCELLED'}

            elif event.type in ('SPACE', 'LEFTMOUSE'):
                self.finish(context)
                return {'FINISHED'}

        return {"RUNNING_MODAL"}

    def restore(self):
        for bg, alpha in self.cam_backgrounds:
            bg.alpha = alpha

    @staticmethod
    def finish(context):
        context.area.header_text_set(text=None)
        context.workspace.status_text_set(text=None)
        context.window.cursor_modal_restore()


class BackgroundOpacityPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="How to Use:")
        col.label(text="Activate a camera with a background, use the addon shortcut and move the mouse cursor in "
                       "horizontal directions.")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Shortcut:")
        self.draw_keymap_items(col, "3D View", addon_keymaps, False)

    @staticmethod
    def draw_keymap_items(col, km_name, keymap, allow_remove):
        kc = bpy.context.window_manager.keyconfigs.user
        km = kc.keymaps.get(km_name)
        kmi_idnames = [km_tuple[1].idname for km_tuple in keymap]
        if allow_remove:
            col.context_pointer_set("keymap", km)

        kmis = [kmi for kmi in km.keymap_items if
                kmi.idname in kmi_idnames]
        for kmi in kmis:
            rna_keymap_ui.draw_kmi(['ADDON', 'USER', 'DEFAULT'], kc, km, kmi, col, 0)


classes = (
    CAMERA_OT_background_opacity,
    BackgroundOpacityPreferences,
)

addon_keymaps = []


def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        kmi = km.keymap_items.new("camera.background_opacity", 'V', 'PRESS')
        addon_keymaps.append((km, kmi))


def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    register_keymaps()


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    unregister_keymap()


if __name__ == '__main__':
    register()
