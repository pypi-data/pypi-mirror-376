"""
a tkinter extension for 3d displaying
"""

from .core import Tk3d
from .tools import scale, change_color, rotate_x, rotate_y, rotate_z, read_obj, write_obj

__all__ = ["Tk3d", "scale", "change_color", "rotate_x", "rotate_y", "rotate_z", "read_obj", "write_obj"]