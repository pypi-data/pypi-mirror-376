from .color import BaseColor
from typing import Tuple, Iterable, Union, overload, TypeVar

def lighten(color : BaseColor, factor: float) -> BaseColor:
        """
        Return lightened version of color.
        
        Args:
            factor: Lightening factor (0.0 to 1.0)
            
        Returns:
            New color instance of same type, lightened
        """
        factor = max(0.0, min(1.0, factor))
        new_r = min(255, int(color._r + (255 - color._r) * factor))
        new_g = min(255, int(color._g + (255 - color._g) * factor))
        new_b = min(255, int(color._b + (255 - color._b) * factor))
        
        # Return same type as caller
        return color.__class__(new_r, new_g, new_b)

def darken(color : BaseColor, factor: float) -> BaseColor:
    """
    Return darkened version of color.
    
    Args:
        factor: Darkening factor (0.0 to 1.0)
        
    Returns:
        New color instance of same type, darkened
    """
    factor = max(0.0, min(1.0, factor))
    new_r = int(color._r * (1.0 - factor))
    new_g = int(color._g * (1.0 - factor))
    new_b = int(color._b * (1.0 - factor))
    
    return color.__class__(new_r, new_g, new_b)

def invert(color : BaseColor) -> BaseColor:
    """Return inverted (complement) color."""
    return color.__class__(255 - color._r, 255 - color._g, 255 - color._b)

def grayscale(color : BaseColor) -> BaseColor:
    """Convert to grayscale using luminance formula (ITU-R BT.709)."""
    # Using ITU-R BT.709 luma coefficients
    gray = int(0.2126 * color._r + 0.7152 * color._g + 0.0722 * color._b)
    return color.__class__(gray, gray, gray)

def saturate(color : BaseColor, factor: float) -> BaseColor:
    """
    Increase saturation by factor.
    
    Args:
        factor: Saturation increase factor (0.0 to 1.0)
    """
    hsl = color.to_hsl()
    new_saturation = min(100, hsl.s + (hsl.s * factor))
    return color.__class__(hsl.__class__(hsl.h, new_saturation, hsl.l))

def desaturate(color : BaseColor, factor: float) -> BaseColor:
    """
    Decrease saturation by factor.
    
    Args:
        factor: Saturation decrease factor (0.0 to 1.0)
    """
    hsl = color.to_hsl()
    new_saturation = max(0, hsl.s - (hsl.s * factor))
    return color.__class__(hsl.__class__(hsl.h, new_saturation, hsl.l))

def adjust_hue(color : BaseColor, degrees: float) -> BaseColor:
    """
    Adjust hue by specified degrees.
    
    Args:
        degrees: Degrees to adjust hue (-360 to 360)
    """
    hsl = color.to_hsl()
    new_hue = (hsl.h + degrees) % 360
    return color.__class__(hsl.__class__(new_hue, hsl.s, hsl.l))

def blend(color1 : BaseColor, color2 : BaseColor, factor: float) -> BaseColor:
    """
    Blend two colors together by a specified factor.
    
    Args:
        color1: First color
        color2: Second color
        factor: Blend factor (0.0 to 1.0), where 0.0 is all color1 and 1.0 is all color2
        
    Returns:
        New blended color instance of same type as color1
    """
    factor = max(0.0, min(1.0, factor))
    new_r = int(color1._r * (1 - factor) + color2._r * factor)
    new_g = int(color1._g * (1 - factor) + color2._g * factor)
    new_b = int(color1._b * (1 - factor) + color2._b * factor)
    
    return color1.__class__(new_r, new_g, new_b)