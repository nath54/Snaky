
from typing import Optional
from math import sqrt

import numpy as np

from dataclasses import dataclass


#
class ND_Point:
    #
    def __init__(self, x: int, y: int) -> None:
        #
        self.x: int = x
        self.y: int = y


    #
    def __hash__(self) -> int:
        return hash(f"{self.x}_{self.y}")


    #
    def __repr__(self) -> str:
        #
        return f"ND_Point(x={self.x}, y={self.y})"


    #
    def __eq__(self, other: object) -> bool:
        #
        if not isinstance(other, ND_Point):
            return NotImplemented
        #
        return self.x == other.x and self.y == other.y


    #
    def __add__(self, other: 'ND_Point') -> 'ND_Point':
        #
        return ND_Point(self.x + other.x, self.y + other.y)


    #
    def __sub__(self, other: 'ND_Point') -> 'ND_Point':
        #
        return ND_Point(self.x - other.x, self.y - other.y)


    #
    def __neg__(self) -> 'ND_Point':
        return ND_Point(-self.x, -self.y)


    #
    def distance_to(self, other: 'ND_Point') -> float:
        #
        return sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


    #
    def in_rect(self, rect: 'ND_Rect') -> bool:
        #
        return (rect.left <= self.x < rect.right and
                rect.top <= self.y < rect.bottom)


    #
    def np_normalize(self) -> np.ndarray:
        #
        norm: float = self.x + self.y
        return np.array([self.x / norm, self.y / norm])


    #
    @staticmethod
    def from_tuple(t: tuple[int, int]) -> 'ND_Point':
        #
        return ND_Point(t[0], t[1])


    #
    def to_tuple(self) -> tuple[int, int]:
        #
        return (self.x, self.y)


#
class ND_Rect:
    #
    def __init__(self, x: int, y: int, w: int = 1, h: int = 1) -> None:
        #
        self.x: int = x
        self.y: int = y
        self.w: int = w
        self.h: int = h


    #
    def __hash__(self) -> int:
        return hash(f"{self.x}_{self.y}_{self.w}_{self.h}")


    #
    def __repr__(self) -> str:
        #
        return f"ND_Rect(x={self.x}, y={self.y}, w={self.w}, h={self.h})"


    #
    @property
    def left(self) -> int:
        #
        return self.x


    #
    @property
    def right(self) -> int:
        #
        return self.x + self.w


    #
    @property
    def top(self) -> int:
        #
        return self.y


    #
    @property
    def bottom(self) -> int:
        #
        return self.y + self.h


    #
    def intersects_with_other_rect(self, other: "ND_Rect") -> bool:
        #
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)


    #
    def get_intersection_area_with_other_rect(self, other: "ND_Rect") -> Optional["ND_Rect"]:
        #
        if not self.intersects_with_other_rect(other):
            return None

        #
        x: int = max(self.left, other.left)
        y: int = max(self.top, other.top)
        w: int = min(self.right, other.right) - x
        h: int = min(self.bottom, other.bottom) - y

        #
        return ND_Rect(x, y, w, h)


    #
    def union(self, other: "ND_Rect") -> "ND_Rect":
        #
        x: int = min(self.left, other.left)
        y: int = min(self.top, other.top)
        w: int = max(self.right, other.right) - x
        h: int = max(self.bottom, other.bottom) - y

        #
        return ND_Rect(x, y, w, h)


    #
    @staticmethod
    def enclose_points(points: list[tuple[int, int] | ND_Point]) -> Optional["ND_Rect"]:
        #
        if not points:
            return None

        #
        def get_x(p: tuple[int, int] | ND_Point):
            return p[0] if isinstance(p, tuple) else p.x

        #
        def get_y(p: tuple[int, int] | ND_Point):
            return p[1] if isinstance(p, tuple) else p.y

        #
        x_min: int = get_x(min(points, key=get_x))
        y_min: int = get_y(min(points, key=get_y))
        x_max: int = get_x(max(points, key=get_x))
        y_max: int = get_y(max(points, key=get_y))

        #
        return ND_Rect(x_min, y_min, x_max - x_min, y_max - y_min)


    #
    def contains_point(self, point: ND_Point) -> bool:
        #
        return point.in_rect(self)


#
@dataclass
class ND_Position_Margins:
    """
    if is int, it is pixel value, else if is string, is "value_float%",
    where it indicates the repartition of available empty space between the element to share between his sides.
    """

    margin: Optional[int | str] = None
    margin_left: Optional[int | str] = None
    margin_right: Optional[int | str] = None
    margin_top: Optional[int | str] = None
    margin_bottom: Optional[int | str] = None
    #
    min_margin_left: int = 0
    min_margin_right: int = 0
    min_margin_top: int = 0
    min_margin_bottom: int = 0
    #
    width_stretch_ratio: float = 1.0
    height_stretch_ratio: float = 1.0


#
@dataclass
class ND_Position_Constraints:
    """
    If is int, it is pixel value, else if is string, it is "value_float%" where it indicates the percentage of the containers row or column size.
    If the min and max values are both specified and of the same value, it forces the size to be that value.
    """
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None


#
class ND_Position:
    #
    def __init__(self, x: int = 0, y: int = 0, w: int = -1, h: int = -1) -> None:
        """
        With or Height with negative value is like auto width and height.
        In a grid it will take the maximum grid size.
        If a min and max value are specified, and a maximum column/row size are specified to, it will try to adjust to the best while beeing clamped.
        If a min and max value are specified, and no other constraints, it will just sit in the middle of the min and max values.
        """
        #
        self._x: int = x
        self._y: int = y
        self._w: int = w
        self._h: int = h

    #
    @property
    def x(self) -> int:
        #
        return self._x

    #
    @x.setter
    def x(self, value: int) -> None:
        #
        self._x = value

    #
    @property
    def y(self) -> int:
        #
        return self._y

    #
    @y.setter
    def y(self, value: int) -> None:
        #
        self._y = value

    #
    @property
    def w(self) -> int:
        #
        return self._w

    #
    @w.setter
    def w(self, value: int) -> None:
        #
        self._w = value

    #
    @property
    def h(self) -> int:
        #
        return self._h

    #
    @h.setter
    def h(self, value: int) -> None:
        #
        self._h = value

    #
    @property
    def rect(self) -> ND_Rect:
        #
        return ND_Rect(self.x, self.y, self.w, self.h)

    #
    def __repr__(self) -> str:
        return f"Position(x={self.x}, y={self.y}, w={self.w}, h={self.h})"

    #
    def set_x(self, new_x: int) -> None:
        self._x = new_x

    #
    def set_y(self, new_y: int) -> None:
        self._y = new_y

    #
    def set_w(self, new_w: int) -> None:
        self._w = new_w

    #
    def set_h(self, new_h: int) -> None:
        self._h = new_h


