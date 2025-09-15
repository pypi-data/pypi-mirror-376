from typing import Union, Iterable, Tuple
import numbers

from abc import ABC, abstractmethod
from typing import Tuple, Union, Iterator, Any, TYPE_CHECKING
import numbers
import math

if TYPE_CHECKING:
    from .rgb import RGB
    from .hex import Hex
    from .hsv import HSV
    from .hsl import HSL

class BaseColor(ABC):
    """
    Abstract base class for all color representations.
    
    Provides common color operations, conversions, and validation.
    All color classes (RGB, Hex, HSL, HSV, etc.) should inherit from this.
    """
    
    # Color space bounds
    RGB_MIN = 0
    RGB_MAX = 255
    
    def __init__(self):
        """Base constructor - subclasses should call super().__init__()"""
        self._r: int = 0
        self._g: int = 0  
        self._b: int = 0
    
    # === ABSTRACT METHODS (must be implemented by subclasses) ===
    
    @abstractmethod
    def to_rgb(self) -> 'RGB':
        """Convert to RGB representation."""
        pass
    
    @abstractmethod
    def to_hex(self) -> 'Hex':
        """Convert to Hex representation."""
        pass

    @classmethod
    @abstractmethod
    def random(cls) -> 'RGB':
        """Generate a random color in this color space."""
        pass
    
    # === RGB COMPONENT ACCESS (common to all color types) ===
    
    @property
    def r(self) -> int:
        """Red component (0-255)."""
        return self._r
    
    @property
    def g(self) -> int:
        """Green component (0-255)."""
        return self._g
    
    @property
    def b(self) -> int:
        """Blue component (0-255)."""
        return self._b
    
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """RGB components as tuple."""
        return (self._r, self._g, self._b)
    
    # === COLOR VALIDATION ===
    
    @staticmethod
    def _validate_color_value(value: Any, color_name: str = "color") -> int:
        """
        Validate and convert color value to integer in range [0, 255].
        
        Args:
            value: The color value to validate
            color_name: Name of the color component for error messages
            
        Returns:
            int: Valid color value
            
        Raises:
            TypeError: If value is not numeric
            ValueError: If value is outside valid range
        """
        if not isinstance(value, numbers.Real):
            raise TypeError(f"{color_name} value must be numeric, got {type(value).__name__}")
        
        int_value = int(value)
        
        if not (BaseColor.RGB_MIN <= int_value <= BaseColor.RGB_MAX):
            raise ValueError(f"{color_name} value must be in range [{BaseColor.RGB_MIN}, {BaseColor.RGB_MAX}], got {int_value}")
        
        return int_value
    
    @staticmethod
    def _validate_normalized_value(value: Any, color_name: str = "color") -> float:
        """
        Validate normalized color value in range [0.0, 1.0].
        
        Args:
            value: The normalized color value to validate
            color_name: Name of the color component for error messages
            
        Returns:
            float: Valid normalized color value
        """
        if not isinstance(value, numbers.Real):
            raise TypeError(f"{color_name} value must be numeric, got {type(value).__name__}")
        
        float_value = float(value)
        
        if not (0.0 <= float_value <= 1.0):
            raise ValueError(f"{color_name} value must be in range [0.0, 1.0], got {float_value}")
        
        return float_value
    
    # === COLOR SPACE CONVERSIONS ===
    def to_hsl(self) -> 'HSL':
        """Convert to HSL (Hue, Saturation, Lightness)."""
        r, g, b = self.normalized()
        
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Lightness
        lightness = (max_val + min_val) / 2.0
        
        if diff == 0:
            # Achromatic (gray)
            hue = saturation = 0.0
        else:
            # Saturation
            if lightness < 0.5:
                saturation = diff / (max_val + min_val)
            else:
                saturation = diff / (2.0 - max_val - min_val)
            
            # Hue
            if max_val == r:
                hue = ((g - b) / diff) % 6
            elif max_val == g:
                hue = (b - r) / diff + 2
            else:  # max_val == b
                hue = (r - g) / diff + 4
            
            hue *= 60  # Convert to degrees
        
        # Import here to avoid circular imports
        from .hsv import HSL
        return HSL(hue, saturation * 100, lightness * 100)

    def to_hsv(self) -> 'HSV':
        """Convert to HSV (Hue, Saturation, Value)."""
        r, g, b = self.normalized()
        
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Value
        value = max_val
        
        # Saturation
        saturation = 0.0 if max_val == 0 else diff / max_val
        
        # Hue
        if diff == 0:
            hue = 0.0
        elif max_val == r:
            hue = ((g - b) / diff) % 6
        elif max_val == g:
            hue = (b - r) / diff + 2
        else:  # max_val == b
            hue = (r - g) / diff + 4
        
        hue *= 60  # Convert to degrees
        
        # Import here to avoid circular imports
        from .hsv import HSV
        return HSV(hue, saturation * 100, value * 100)
    
    def normalized(self) -> Tuple[float, float, float]:
        """Return RGB values normalized to [0.0, 1.0] range."""
        return (
            self._r / 255.0,
            self._g / 255.0, 
            self._b / 255.0
        )
    
    # === COLOR ANALYSIS ===
    @property
    def luminance(self) -> float:
        """
        Calculate relative luminance (0.0 to 1.0).
        Uses sRGB colorimetric definition.
        """
        def linearize(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r_lin = linearize(self._r)
        g_lin = linearize(self._g)
        b_lin = linearize(self._b)
        
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    # === SEQUENCE PROTOCOL ===
    
    def __iter__(self) -> Iterator[int]:
        """Iterate over RGB components."""
        yield self._r
        yield self._g
        yield self._b
    
    def __getitem__(self, index: int) -> int:
        """Support indexing for RGB components."""
        if index == 0:
            return self._r
        elif index == 1:
            return self._g
        elif index == 2:
            return self._b
        else:
            raise IndexError("Color index out of range (0-2)")
    
    def __len__(self) -> int:
        """Return length of 3 for RGB components."""
        return 3
    
    # === EQUALITY AND COMPARISON ===
    
    def __eq__(self, other: Any) -> bool:
        """Check equality based on RGB values."""
        if not isinstance(other, BaseColor):
            return NotImplemented
        return (self._r, self._g, self._b) == (other._r, other._g, other._b)
    
    def __hash__(self) -> int:
        """Make color hashable based on RGB values."""
        return hash((self._r, self._g, self._b))
    
    # === STRING REPRESENTATIONS ===
    
    def __str__(self) -> str:
        """Default string representation - subclasses should override."""
        return f"{self.__class__.__name__}({self._r}, {self._g}, {self._b})"
    
    def __repr__(self) -> str:
        """Developer representation - subclasses should override."""
        return f"{self.__class__.__name__}({self._r}, {self._g}, {self._b})"
    
    # === CONVERSION UTILITIES ===
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to RGB tuple."""
        return (self._r, self._g, self._b)
    
    def to_list(self) -> list:
        """Convert to RGB list."""
        return [self._r, self._g, self._b]
    
    def to_dict(self) -> dict:
        """Convert to dictionary with RGB keys."""
        return {'r': self._r, 'g': self._g, 'b': self._b}
    
    # === CSS/WEB FORMATS ===
    
    def css_rgb(self) -> str:
        """CSS rgb() format: rgb(255, 128, 64)"""
        return f"rgb({self._r}, {self._g}, {self._b})"
    
    def css_rgba(self, alpha: float = 1.0) -> str:
        """CSS rgba() format: rgba(255, 128, 64, 1.0)"""
        alpha = max(0.0, min(1.0, alpha))
        return f"rgba({self._r}, {self._g}, {self._b}, {alpha})"

    # === TERMINAL COLORS ===
    def _supports_truecolor_env(self) -> bool:
        import os
        colorterm = os.environ.get("COLORTERM", "").lower()
        return colorterm in ("truecolor", "24bit")

    def _supports_256color(self) -> bool:
        import os
        term = os.environ.get("TERM", "").lower()
        return "256color" in term

    @property
    def ansi256(self) -> int:
        """
        Convert 24-bit RGB to the closest 256-color ANSI code.
        """
        # Clamp values
        r = max(0, min(255, self._r))
        g = max(0, min(255, self._g))
        b = max(0, min(255, self._b))

        # Map RGB to 0-5
        def to_ansi_level(c):
            if c < 48:
                return 0
            elif c < 114:
                return 1
            else:
                return (c - 35) // 40
        
        r_level = to_ansi_level(r)
        g_level = to_ansi_level(g)
        b_level = to_ansi_level(b)
        
        return 16 + 36*r_level + 6*g_level + b_level

    def color_text_foreground(self, text: str) -> str:
        """Wrap text with ANSI escape codes for foreground color."""
        if self._supports_truecolor_env():
            return f"\033[38;2;{self._r};{self._g};{self._b}m{text}\033[0m"
        elif self._supports_256color():
            return f"\033[38;5;{self.ansi256}m{text}\033[0m"
        else:
            return text
        
    def color_text_background(self, text: str) -> str:
        """Wrap text with ANSI escape codes for background color."""
        if self._supports_truecolor_env():
            return f"\033[48;2;{self._r};{self._g};{self._b}m{text}\033[0m"
        elif self._supports_256color():
            return f"\033[48;5;{self.ansi256}m{text}\033[0m"
        else:
            return text
