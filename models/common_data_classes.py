from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from .color_data_class import Color

class SwatchType(Enum):
    SPOT = "Spot"
    PROCESS = "Process"

class ColorMode(Enum):
    RGB = "RGB"
    LAB = "LAB"
    CMYK = "CMYK"

@dataclass
class Swatch:
    name: str
    type: SwatchType
    mode: ColorMode
    color: Color
