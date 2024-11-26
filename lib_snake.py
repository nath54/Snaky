
from typing import Optional

import random
import math

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
def create_map1(win: nd.ND_Window, tx: int = 30, ty: int = 30) -> None:
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
    bg_garden_sprites_dict: Optional[dict[str, tuple[nd.ND_Sprite_of_AtlasTexture, int]]] = win.main_app.global_vars_get("bg_garden_sprites_dict")
    #
    if bg_garden_sprites_dict is None:
        #
        bg_garden_sprites_dict = {}
        #
        win.main_app.global_vars_set("bg_garden_sprites_dict", bg_garden_sprites_dict)

    #
    def create_sprite_of_bg_garden(eid: str, atlas_x: int, atlas_y: int) -> tuple[nd.ND_Sprite_of_AtlasTexture, int]:
        #
        sprite: nd.ND_Sprite_of_AtlasTexture =  nd.ND_Sprite_of_AtlasTexture(
                window=win,
                elt_id=f"bg_garden_{eid}",
                position=nd.ND_Position_RectGrid(rect_grid=bg_grid),
                atlas_texture=bg_garden_atlas,
                tile_x=atlas_x,
                tile_y=atlas_y
        )
        #
        bg_sprite_id: int = bg_grid.add_element_to_grid(sprite, [])
        #
        return (sprite, bg_sprite_id)

    # Create all the sprites we need
    SPRITE_POSITIONS: dict[str, tuple[int, int]] = {
        "left_border": (0, 1),
        "top_border": (1, 0),
        "right_border": (2, 1),
        "bottom_border": (1, 2),
        "top_left_corner": (0, 0),
        "top_right_corner": (2, 0),
        "bottom_left_corner": (0, 2),
        "bottom_right_corner": (2, 2),
        "fill_niv_0_1": (1, 1),
        "fill_niv_0_2": (1, 1),
        "fill_niv_0_3": (1, 1),
        "fill_niv_1_1": (3, 2),
        "fill_niv_1_2": (4, 2),
        "fill_niv_1_3": (5, 2),
        "fill_niv_2_1": (3, 1),
        "fill_niv_2_2": (4, 1),
        "fill_niv_2_3": (5, 1),
        "fill_niv_3_1": (3, 0),
        "fill_niv_3_2": (4, 0),
        "fill_niv_3_3": (5, 0),
    }

    #
    sprite_pos_id: str
    for sprite_pos_id in SPRITE_POSITIONS:
        if sprite_pos_id not in bg_garden_sprites_dict:
            bg_garden_sprites_dict[sprite_pos_id] = create_sprite_of_bg_garden(sprite_pos_id, *SPRITE_POSITIONS[sprite_pos_id])

    #
    map_start_x: int = 0
    map_start_y: int = 0
    map_end_x: int = tx
    map_end_y: int = ty
    x: int
    y: int

    # Bordure gauche
    bg_grid.add_element_position(bg_garden_sprites_dict["left_border"][1],
                                 [ND_Point(map_start_x, y) for y in range(map_start_y, map_end_y)] )
    # Bordure droite
    bg_grid.add_element_position(bg_garden_sprites_dict["right_border"][1],
                                 [ND_Point(map_end_x, y) for y in range(map_start_y, map_end_y)] )
    # Bordure haut
    bg_grid.add_element_position(bg_garden_sprites_dict["top_border"][1],
                                 [ND_Point(x, map_start_y) for x in range(map_start_x, map_end_x)] )
    # Bordure bas
    bg_grid.add_element_position(bg_garden_sprites_dict["bottom_border"][1],
                                 [ND_Point(x, map_end_y) for x in range(map_start_x, map_end_x)] )
    # Coins
    bg_grid.add_element_position(bg_garden_sprites_dict["top_left_corner"][1],
                                 ND_Point(map_start_x, map_start_y))
    bg_grid.add_element_position(bg_garden_sprites_dict["top_right_corner"][1],
                                 ND_Point(map_end_x, map_start_y))
    bg_grid.add_element_position(bg_garden_sprites_dict["bottom_left_corner"][1],
                                 ND_Point(map_start_x, map_end_y))
    bg_grid.add_element_position(bg_garden_sprites_dict["bottom_right_corner"][1],
                                 ND_Point(map_end_x, map_end_y))

    """
    e^x - 1 = 3
    <=> e^x = 4
    <=> x = ln(4)
    """

    # Remplir le carré aléatoirement avec moins de chance d'avoir les sprites avec pleins de fleurs.
    for x in range(map_start_x+1, map_end_x):
        for y in range(map_start_y+1, map_end_y):
            #
            a: float = random.uniform(0, 1)
            b: int = random.randint(1, 3)
            #
            grass_niv: int = math.floor( math.exp(a * math.log(4)) - 1)
            #
            bg_grid.add_element_position(bg_garden_sprites_dict[f"fill_niv_{grass_niv}_{b}"][1],
                                         ND_Point(x, y))



#
def create_map2(mainApp: nd.ND_MainApp, n: int = 30) -> None:
    """
    Donut map, Donut shape

    Args:
        mainApp (nd.ND_MainApp): _description_
    """

    # TODO
    pass




