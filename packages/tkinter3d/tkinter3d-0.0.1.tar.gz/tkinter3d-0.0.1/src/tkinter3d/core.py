from tkinter import Tk, Canvas
from typing import Dict, Tuple, List, Optional, Union

class Tk3d:
    """
    A 3-dimensional Tk object
    """

    def __init__(
        self,
        size: Tuple[int, int],
        *,
        screenName: Optional[str] = None,
        baseName: Optional[str] = None,
        className: str = "Tk",
        useTk: bool = True,
        sync: bool = False,
        use: Optional[str] = None,
        background: str = "#ffffff"
    ):
        self.tk: Tk = Tk(
            screenName=screenName,
            baseName=baseName,
            className=className,
            useTk=useTk,
            sync=sync,
            use=use
        )
        self.canvas: Canvas = Canvas(self.tk, width=size[0], height=size[1], bg=background)
        self.canvas.pack()
        self.ids: Dict[int, List[int]] = {}

    def __str__(self):
        return "3-dimensional Tk object"

    def __repr__(self):
        return "Tk3d"

    def loop(self):
        """Runs Tkinter's mainloop."""
        self.tk.mainloop()

    def shape(
        self,
        dots: Dict[int, Tuple[float, float, float]],
        lines: List[Tuple[int, int]],
        *,
        color: str = "black",
        camera: float = 100.0,
        width: int = 2,
        tags: Optional[str] = None
    ) -> int:
        """
        Adds a 3D shape to the canvas.

        dots: dict[int, tuple[x, y, z]] -- keys are identifiers, values are 3D coordinates.
        lines: list[tuple[int, int]] -- each tuple contains two dot identifiers.
        """
        gen_id = max(self.ids.keys(), default=0) + 1

        # 3D -> 2D perspective projection
        twoD_gen = {}
        for dot_id, (x, y, z) in dots.items():
            twoDx = x * camera / (z + camera)
            twoDy = y * camera / (z + camera)
            twoD_gen[dot_id] = (twoDx, twoDy)

        # Draw lines
        idlist = []
        for start, end in lines:
            id_2d = self.canvas.create_line(
                twoD_gen[start][0], twoD_gen[start][1],
                twoD_gen[end][0], twoD_gen[end][1],
                fill=color, width=width, tags=tags
            )
            idlist.append(id_2d)

        self.ids[gen_id] = idlist
        return gen_id

    def delete(self, shape_id: int):
        """
        Deletes a shape by its identifier.
        """
        if shape_id in self.ids:
            for id_2d in self.ids[shape_id]:
                self.canvas.delete(id_2d)
            del self.ids[shape_id]