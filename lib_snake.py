
from typing import Optional

import random
import math

from lib_nadisplay_colors import ND_Color
from lib_nadisplay_rects import ND_Point, ND_Position
import lib_nadisplay as nd


class Snake:
    #
    def __init__(self, pseudo: str, init_position: ND_Point, color: ND_Color, score_elt: nd.ND_Text, init_direction: ND_Point = ND_Point(1, 0), init_size: int = 4) -> None:
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
        self.score_elt: nd.ND_Text = score_elt
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
                                texture_atlas_path="res/sprites/terrain1.png",
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




def snake_skin_1(win: nd.ND_Window, snake: Snake, snk_idx: int, grid: nd.ND_RectGrid) -> None:

    #
    snake_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get("snake_atlas")

    if snake_atlas is None:
        #
        snake_atlas = nd.ND_AtlasTexture(
            window=win,
            texture_atlas_path="res/sprites/snakes_sprites4.png",
            tiles_size=ND_Point(32, 32)
        )
        #
        win.main_app.global_vars_set("snake_atlas", snake_atlas)


    # Snake head
    #
    sprite_head: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id=f"snake_{snk_idx}_head",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"snake_{snk_idx}_head_{i}",
                    position=ND_Position(),
                    atlas_texture=snake_atlas,
                    tile_x=i, tile_y=1
                )

                for i in range(3)
            ]
        },
        animations_speed={},
        default_animation_speed=0.5
    )
    sprite_head.transformations.rotation = 270
    sprite_head.transformations.color_modulation = snake.color
    #
    snake.sprites["head"] = (sprite_head, grid.add_element_to_grid(sprite_head, []))

    #
    sprite_tail: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
        window=win,
        elt_id=f"snake_{snk_idx}_tail",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        atlas_texture=snake_atlas,
        tile_x=0, tile_y=0
    )
    sprite_tail.transformations.color_modulation = snake.color
    snake.sprites["tail"] = (sprite_tail, grid.add_element_to_grid(sprite_tail, []))

    #
    sprite_body: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
        window=win,
        elt_id=f"snake_{snk_idx}_body",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        atlas_texture=snake_atlas,
        tile_x=1, tile_y=0
    )
    sprite_body.transformations.color_modulation = snake.color
    snake.sprites["body"] = (sprite_body, grid.add_element_to_grid(sprite_body, []))

    #
    sprite_body_corner: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
        window=win,
        elt_id=f"snake_{snk_idx}_body_corner",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        atlas_texture=snake_atlas,
        tile_x=2, tile_y=0
    )
    sprite_body_corner.transformations.color_modulation = snake.color
    snake.sprites["body_corner"] = (sprite_body_corner, grid.add_element_to_grid(sprite_body_corner, []))



def snake_skin_2(win: nd.ND_Window, snake: Snake, snk_idx: int, grid: nd.ND_RectGrid) -> None:

    #
    anim_speed: float = 0.2

    #
    worm_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get("worm_atlas")

    if worm_atlas is None:
        #
        worm_atlas = nd.ND_AtlasTexture(
            window=win,
            texture_atlas_path="res/sprites/worm.png",
            tiles_size=ND_Point(32, 32)
        )
        #
        win.main_app.global_vars_set("worm_atlas", worm_atlas)


    # Snake head
    #
    sprite_head: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id=f"snake_{snk_idx}_head",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"snake_{snk_idx}_head_{i}",
                    position=ND_Position(),
                    atlas_texture=worm_atlas,
                    tile_x=i, tile_y=2
                )

                for i in range(3)
            ]
        },
        animations_speed={},
        default_animation_speed=anim_speed
    )
    sprite_head.transformations.rotation = 270
    # sprite_head.transformations.color_modulation = snake.color
    #
    snake.sprites["head"] = (sprite_head, grid.add_element_to_grid(sprite_head, []))

    #
    sprite_tail: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id=f"snake_{snk_idx}_tail",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"snake_{snk_idx}_tail_{i}",
                    position=ND_Position(),
                    atlas_texture=worm_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(3)
            ]
        },
        animations_speed={},
        default_animation_speed=anim_speed
    )
    sprite_tail.transformations.rotation = 270
    # sprite_tail.transformations.color_modulation = snake.color
    snake.sprites["tail"] = (sprite_tail, grid.add_element_to_grid(sprite_tail, []))

    #
    sprite_body: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id=f"snake_{snk_idx}_body",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"snake_{snk_idx}_body_{i}",
                    position=ND_Position(),
                    atlas_texture=worm_atlas,
                    tile_x=i, tile_y=1
                )

                for i in range(3)
            ]
        },
        animations_speed={},
        default_animation_speed=anim_speed
    )
    sprite_body.transformations.rotation = 270
    # sprite_body.transformations.color_modulation = snake.color
    snake.sprites["body"] = (sprite_body, grid.add_element_to_grid(sprite_body, []))

    #
    sprite_body_corner: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id=f"snake_{snk_idx}_body_corner",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"snake_{snk_idx}_body_corner_{i}",
                    position=ND_Position(),
                    atlas_texture=worm_atlas,
                    tile_x=3, tile_y=i
                )

                for i in range(3)
            ]
        },
        animations_speed={},
        default_animation_speed=anim_speed
    )
    sprite_body_corner.transformations.rotation = 0
    # sprite_body_corner.transformations.color_modulation = snake.color
    snake.sprites["body_corner"] = (sprite_body_corner, grid.add_element_to_grid(sprite_body_corner, []))


