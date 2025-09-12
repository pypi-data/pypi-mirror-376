from .core import Tk3d
from typing import Dict, Tuple
import math

def scale(
    dots: Dict[int, Tuple[float, float, float]],
    multiplier: float
) -> Dict[int, Tuple[float, float, float]]:
    """
    Scales up/down the dots around their center.
    
    dots: dict of {id: (x, y, z)}
    multiplier: scale factor
    """
    if not dots:
        return {}

    xs, ys, zs = zip(*dots.values())
    mid = (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))

    new_dots = {}
    for id, (x, y, z) in dots.items():
        dx = (x - mid[0]) * multiplier
        dy = (y - mid[1]) * multiplier
        dz = (z - mid[2]) * multiplier
        new_dots[id] = (mid[0] + dx, mid[1] + dy, mid[2] + dz)

    return new_dots


def change_color(tk3d: Tk3d, shape_id: int, color: str) -> None:
    """
    Changes the color of a shape on the canvas.
    
    tk3d: Tk3d instance
    shape_id: ID of the shape returned by Tk3d.shape()
    color: new color string
    """
    if shape_id not in tk3d.ids:
        raise ValueError(f"Shape ID {shape_id} not found.")
    
    for tkid in tk3d.ids[shape_id]:
        tk3d.canvas.itemconfig(tkid, fill=color)


def rotate_x(
    dots: Dict[int, Tuple[float, float, float]],
    angle_deg: float
) -> Dict[int, Tuple[float, float, float]]:
    """Rotate points around the X-axis by angle in degrees."""
    angle = math.radians(angle_deg)
    new_dots = {}
    for id, (x, y, z) in dots.items():
        y_new = y * math.cos(angle) - z * math.sin(angle)
        z_new = y * math.sin(angle) + z * math.cos(angle)
        new_dots[id] = (x, y_new, z_new)
    return new_dots


def rotate_y(
    dots: Dict[int, Tuple[float, float, float]],
    angle_deg: float
) -> Dict[int, Tuple[float, float, float]]:
    """Rotate points around the Y-axis by angle in degrees."""
    angle = math.radians(angle_deg)
    new_dots = {}
    for id, (x, y, z) in dots.items():
        x_new = x * math.cos(angle) + z * math.sin(angle)
        z_new = -x * math.sin(angle) + z * math.cos(angle)
        new_dots[id] = (x_new, y, z_new)
    return new_dots


def rotate_z(
    dots: Dict[int, Tuple[float, float, float]],
    angle_deg: float
) -> Dict[int, Tuple[float, float, float]]:
    """Rotate points around the Z-axis by angle in degrees."""
    angle = math.radians(angle_deg)
    new_dots = {}
    for id, (x, y, z) in dots.items():
        x_new = x * math.cos(angle) - y * math.sin(angle)
        y_new = x * math.sin(angle) + y * math.cos(angle)
        new_dots[id] = (x_new, y_new, z)
    return new_dots
