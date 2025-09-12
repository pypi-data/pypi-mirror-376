from trame_client.widgets.core import AbstractElement
from .. import module


class HtmlElement(AbstractElement):
    def __init__(self, _elem_name, children=None, **kwargs):
        super().__init__(_elem_name, children, **kwargs)
        if self.server:
            self.server.enable_module(module)


__all__ = [
    "ImageDetection",
]


# Expose your vue component(s)
class ImageDetection(HtmlElement):
    def __init__(self, **kwargs):
        super().__init__(
            "image-detection",
            **kwargs,
        )
        self._attr_names += [
            "src",
            "identifier",
            "annotations",
            "categories",
            "models",
            "selected",
            ("container_selector", "containerSelector"),
            ("line_width", "lineWidth"),
            ("line_opacity", "lineOpacity"),
            ("score_threshold", "scoreThreshold"),
            ("color_by", "colorBy"),
        ]
        self._event_names += [
            "hover",
        ]
