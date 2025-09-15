from .color import BaseColor

class HSV(BaseColor):
    def __init__(self, h: float, s: float, v: float) -> None:
        """
        Initialize HSV color.

        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            v: Value (0-100)
        """
        self.h = max(0.0, min(360.0, h))
        self.s = max(0.0, min(100.0, s))
        self.v = max(0.0, min(100.0, v))