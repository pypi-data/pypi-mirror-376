from django.utils.translation import gettext_lazy as _
from wagtail.blocks import (
    CharBlock, StructBlock,
    BooleanBlock, DecimalBlock, IntegerBlock
)
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock

class ThreeDisplayBlock(StructBlock):
    """
    A block for embedding a 3D model viewer with customizable settings.
    """

    file = DocumentChooserBlock(required=True, help_text=_("Document for the 3D model file."))
    envhdr = CharBlock(required=False, help_text=_("Name of the environment HDR file."))
    envhdr_path = DocumentChooserBlock(required=False, help_text=_("Document for the environment HDR file."))
    autospin = DecimalBlock(required=False, default=0.01, help_text=_("Auto-spin speed for the model, negative values change direction."))
    offset = DecimalBlock(required=False, default=1.25, help_text=_("Offset for the model position."))
    ambient_light_level = DecimalBlock(required=False, default=0.8, help_text=_("Ambient light level for the scene."))
    
    room_static_background = BooleanBlock(required=False, default=False, help_text=_("Whether to use a static background."))
    room_texture_url = ImageChooserBlock(required=False, help_text=_("Image for the room texture, if not using individual wall textures."))
    room_back_wall_url = ImageChooserBlock(required=False, help_text=_("Image for the back wall texture."))
    room_texture_repeat = IntegerBlock(required=False, default=1, help_text=_("Tiling factor for the room texture."))
    room_size_multiplier = DecimalBlock(required=False, default=60, help_text=_("Multiplier for the room size."))

    room_walls_px = ImageChooserBlock(required=False, help_text=_("Image for the positive X wall texture."))
    room_walls_nx = ImageChooserBlock(required=False, help_text=_("Image for the negative X wall texture."))
    room_walls_py = ImageChooserBlock(required=False, help_text=_("Image for the positive Y wall texture."))
    room_walls_ny = ImageChooserBlock(required=False, help_text=_("Image for the negative Y wall texture."))
    room_walls_pz = ImageChooserBlock(required=False, help_text=_("Image for the positive Z wall texture."))
    room_walls_nz = ImageChooserBlock(required=False, help_text=_("Image for the negative Z wall texture."))
    room_walls_x = ImageChooserBlock(required=False, help_text=_("Image for the X wall texture."))
    room_walls_y = ImageChooserBlock(required=False, help_text=_("Image for the Y wall texture."))
    room_walls_z = ImageChooserBlock(required=False, help_text=_("Image for the Z wall texture."))

    class Meta:
        template = "wagtail_3display/blocks/threedisplay.html"
        icon = "media"
        label = _("3D Model Viewer")
        help_text = _("Embed a 3D GLB file viwewer with customizable settings.")