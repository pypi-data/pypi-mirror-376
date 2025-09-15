from .color import BaseColor

class HSL(BaseColor):
    def __init__(self, h: float, s: float, l: float) -> None:
        """
        Initialize HSL color.
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            l: Lightness (0-100)
        """
        self.h = max(0.0, min(360.0, h))
        self.s = max(0.0, min(100.0, s))
        self.l = max(0.0, min(100.0, l))