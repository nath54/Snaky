
from typing import Optional

from lib_nadisplay_colors import ND_Color
from lib_nadisplay_rects import ND_Point
import lib_nadisplay as nd


class Snake:
    #
    def __init__(self, pseudo: str, init_position: ND_Point, color: ND_Color, init_direction: ND_Point = ND_Point(1, 0), init_size: int = 4) -> None:
        #
        self.color: ND_Color = color
        self.hidding_size: int = init_size  # Taille cachée qu'il faut ajouter au snake quand il avance
        self.direction: ND_Point = init_direction  # A ajouter à la position de la tête
        #
        self.cases: list[ND_Point] = []  # La tête est le premier élément de la liste
        self.cases_angles: list[int] = []
        #
        self.last_update: float = 0
        self.last_applied_direction: ND_Point = init_direction
        #
        self.score: int = 0
        #
        self.pseudo: str = pseudo
        #
        self.sprites: dict[str, tuple[nd.ND_AnimatedSprite | nd.ND_Sprite_of_AtlasTexture, int]] = {}






#
def create_map1(win: nd.ND_Window, n: int = 30) -> None:
    """
    Garden Map, a large square

    Args:
        mainApp (nd.ND_MainApp): _description_
    """

    grid: Optional[nd.ND_RectGrid] = win.main_app.global_vars_get("grid")
    bg_grid: Optional[nd.ND_RectGrid] = win.main_app.global_vars_get("bg_grid")

    if grid is None or bg_grid is None:
        return

    #
    bg_garden_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get("bg_garden_atlas")
    #
    if bg_garden_atlas is None:
        #
        bg_garden_atlas = nd.ND_AtlasTexture(
                                window=win,
                                texture_atlas_path="res/terrain1.png",
                                tiles_size=ND_Point(32, 32)
        )
        #
        win.main_app.global_vars_set("bg_garden_atlas", bg_garden_atlas)

    #
    

    # TODO
    pass





#
def create_map2(mainApp: nd.ND_MainApp, n: int = 30) -> None:
    """
    Donut map, Donut shape

    Args:
        mainApp (nd.ND_MainApp): _description_
    """

    # TODO
    pass




