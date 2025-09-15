from .color import Color
from .util import lighten, darken, invert, grayscale, blend, clamp, distance, color_text, highlight_text

# === Constant Colors ===
BLACK           = Color(0, 0, 0)
WHITE           = Color(255, 255, 255)
RED             = Color(255, 0, 0)
GREEN           = Color(0, 255, 0)
BLUE            = Color(0, 0, 255)
YELLOW          = Color(255, 255, 0)
CYAN            = Color(0, 255, 255)
MAGENTA         = Color(255, 0, 255)
GRAY            = Color(128, 128, 128)
LIGHT_GRAY      = Color(192, 192, 192)
DARK_GRAY       = Color(64, 64, 64)
ORANGE          = Color(255, 165, 0)
PINK            = Color(255, 192, 203)
PURPLE          = Color(128, 0, 128)
BROWN           = Color(165, 42, 42)
LIME            = Color(0, 255, 0)
TEAL            = Color(0, 128, 128)
NAVY            = Color(0, 0, 128)
OLIVE           = Color(128, 128, 0)
MAROON          = Color(128, 0, 0)
AQUA            = Color(0, 255, 255)
CRIMSON         = Color(220, 20, 60)
CORNFLOWER_BLUE = Color(100, 149, 237)
DARK_ORANGE     = Color(255, 140, 0)
DARK_GREEN      = Color(0, 100, 0)
DARK_RED        = Color(139, 0, 0)
STEEL_BLUE      = Color(70, 130, 180)
DARK_SLATE_GRAY = Color(47, 79, 79)
MEDIUM_PURPLE   = Color(147, 112, 219)
FIREBRICK       = Color(178, 34, 34)
SALMON          = Color(250, 128, 114)
LIME_GREEN = Color(50, 205, 50)
SKY_BLUE = Color(135, 206, 235)
GOLD = Color(255, 215, 0)
SILVER = Color(192, 192, 192)

__all__ = [
    'Color', 'lighten', 'darken', 'invert', 'grayscale', 'blend', 'clamp', 'distance', 'color_text', 'highlight_text',
    
    'BLACK', 'WHITE', 'RED', 'GREEN', 'BLUE', 'YELLOW', 'CYAN', 'MAGENTA', 'GRAY',
    'LIGHT_GRAY', 'DARK_GRAY', 'ORANGE', 'PINK', 'PURPLE', 'BROWN', 'LIME', 'TEAL',
    'NAVY', 'OLIVE', 'MAROON', 'AQUA', 'CRIMSON', 'CORNFLOWER_BLUE', 'DARK_ORANGE',
    'DARK_GREEN', 'DARK_RED', 'STEEL_BLUE', 'DARK_SLATE_GRAY', 'MEDIUM_PURPLE',
    'FIREBRICK', 'SALMON', 'LIME_GREEN', 'SKY_BLUE', 'GOLD', 'SILVER'
]
