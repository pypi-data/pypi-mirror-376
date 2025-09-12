"""tintelligence-color-utils package."""

__version__ = "0.1.3"

from .conversion import (
    brightness_from_hex,
    hex_midpoint,
    hex_to_hsv,
    hex_to_rgb,
    lab_to_lch,
    normalize_lab,
    rgb_to_hex,
    rgb_to_hsl,
    rgb_to_lab,
)
from .family import get_color_family
from .shades import get_darker_shades
from .sorting import (
    sort_hex_by_brightness,
    sort_paints_by_color,
    sort_paints_by_family_lab_brightness,
    sort_paints_by_family_value_hue,
)

# Backwards-compatible alias for the previous longer name
sort_paints_by_family_lab_brightness_hue = sort_paints_by_family_lab_brightness

__all__ = [
    "__version__",
    # conversion
    "hex_to_rgb",
    "hex_to_hsv",
    "rgb_to_hex",
    "hex_midpoint",
    "rgb_to_lab",
    "normalize_lab",
    "rgb_to_hsl",
    "lab_to_lch",
    "brightness_from_hex",
    # family
    "get_color_family",
    # sorting
    "sort_paints_by_color",
    "sort_paints_by_family_value_hue",
    "sort_paints_by_family_lab_brightness",
    "sort_paints_by_family_lab_brightness_hue",
    "sort_hex_by_brightness",
    # shades
    "get_darker_shades",
]
