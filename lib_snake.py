
from dataclasses import dataclass
from typing import Optional, Callable

import random
import math

import numpy as np

from lib_nadisplay_colors import ND_Color, cl
from lib_nadisplay_rects import ND_Point, ND_Position
import lib_nadisplay as nd


#
@dataclass
class SnakePlayerSetting:
    #
    name: str
    color_idx: int
    init_size: int
    skin_idx: int
    player_type: str
    control_name: str


#
class SnakeBot:  # Default base class is full random bot
    #
    def __init__(self, main_app: nd.ND_MainApp, security: bool = True) -> None:
        #
        self.security: bool = security
        #
        self.all_directions: tuple[ND_Point, ND_Point, ND_Point, ND_Point] = (ND_Point(1, 0), ND_Point(0, 1), ND_Point(-1, 0), ND_Point(0, -1))
        #
        self.food_ids: set[int] = set()

        # Au moment où des instances de cette classe sont créées, les variables globales sont normalement déjà déterminées
        self.food_ids.add( main_app.global_vars_get("food_1_grid_id") )
        self.food_ids.add( main_app.global_vars_get("food_2_grid_id") )
        self.food_ids.add( main_app.global_vars_get("food_3_grid_id") )

    #
    def possible_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> list[int]:
        #
        possible_directions: list[int] = list(range(len(self.all_directions)))
        # On enlève l'inverse de la dernière direction utilisée
        # idx: int = self.all_directions.index(snake.last_applied_direction)
        # possible_directions.remove(idx)
        #
        if self.security and snake.cases:
            #
            to_remove: list[int] = []
            #
            for idx in possible_directions:
                #
                grid_elt_id: Optional[int] = grid.get_element_id_at_grid_case(snake.cases[0] + self.all_directions[idx])
                #
                if grid_elt_id is None or grid_elt_id < 0:  # Case vide
                    continue
                #
                elif grid_elt_id in self.food_ids:  # Nourriture, donc c'est bon
                    continue

                # Sinon, c'est un truc mortel
                to_remove.append(idx)

            #
            for idx in to_remove:
                #
                possible_directions.remove(idx)
        #
        return possible_directions

    #
    def predict_next_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> Optional[ND_Point]:
        # Default bot is random
        possible_directions: list[int] = self.possible_direction(snake, grid, main_app)
        if not possible_directions:
            return None
        #
        chosen_direction: int = random.choice(possible_directions)
        # chosen_direction: int = possible_directions[0]
        #
        return self.all_directions[chosen_direction]


#
class SnakeBot_PerfectButSlowAndBoring(SnakeBot):  # Default base class is full random bot
    #
    def __init__(self, main_app: nd.ND_MainApp, security: bool = True) -> None:
        #
        super().__init__(main_app=main_app, security=security)
        #
        self.state = 0  # 0 : Global direction = droite, 1 = retour vers la gauche

    #
    def predict_next_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> Optional[ND_Point]:
        # Default bot is random
        possible_directions: list[int] = self.possible_direction(snake, grid, main_app)
        if not possible_directions or not snake.cases:
            return None
        #
        chosen_direction: int = random.choice(possible_directions)
        #
        # Idxs:
        #  0 : ND_Point(1, 0) - droite
        #  1 : ND_Point(0, 1) - bas
        #  2 : ND_Point(-1, 0) - gauche
        #  3 : ND_Point(0, -1) - haut
        #

        if snake.cases[0].y <= snake.map_area.y:
            if 2 in possible_directions:
                chosen_direction = 2
        #
        elif snake.cases[0].x % 2 == 0:  # Case paire, on descend
            if 1 in possible_directions:
                chosen_direction = 1
            elif 0 in possible_directions:
                chosen_direction = 0
        #
        elif snake.cases[0].x % 2 == 1:  # Case paire, on remonte
            #
            if snake.cases[0].y - 1 > snake.map_area.y or snake.cases[0].x >= snake.map_area.x + snake.map_area.w - 1:
                if 3 in possible_directions:
                    chosen_direction = 3
                elif 0 in possible_directions:
                    chosen_direction = 0
            #
            else:
                if 0 in possible_directions:
                    chosen_direction = 0
        #


        #
        return self.all_directions[chosen_direction]


#
class SnakeBot_Version1(SnakeBot):
    #
    def __init__(self, main_app: nd.ND_MainApp, security: bool = True, radius: int = 5, direction_of_apples: bool = False) -> None:
        #
        super().__init__(main_app=main_app, security=security)
        #
        self.dim_in: int = radius * radius + direction_of_apples * main_app.global_vars_get_default("nb_init_apples", 3)
        self.dim_out: int = 4
        #
        self.dtype: type = np.float32
        #
        self.weigths: np.ndarray = np.random.normal(loc=0.0, scale=2.0, size=(self.dim_in, self.dim_out)).astype(self.dtype)

    #
    def save_weights_to_path(self, path: str) -> None:
        #
        self.weigths.tofile(path)

    #
    def load_weights_from_path(self, path: str) -> None:
        #
        arr: np.ndarray = np.fromfile(path, dtype=self.dtype)
        #
        if arr.shape != self.weigths.shape:
            raise UserWarning(f"Error: the matrix from file \"{path}\" has shape {arr.shape} while expected shape was {self.weigths.shape} !")

    #
    def predict_next_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> Optional[ND_Point]:
        #
        possible_directions: list[int] = self.possible_direction(snake, grid, main_app)
        if not possible_directions:
            return None
        #

        context: np.ndarray = np.zeros((self.dim_in, 1), dtype=self.dtype)



        # TODO: fill context

        output: np.ndarray = context @ self.weigths

        #
        max_chosen_direction: int = possible_directions[0]
        max_chosen_direction_value: float = output[possible_directions[0]]

        for i in range(1, len(possible_directions)):
            if output[possible_directions[i]] > max_chosen_direction_value:
                max_chosen_direction_value = output[possible_directions[i]]
                max_chosen_direction = possible_directions[i]

        #
        return self.all_directions[max_chosen_direction]



#
class Snake:
    #
    def __init__(self, pseudo: str, init_position: ND_Point, color: ND_Color, score_elt: nd.ND_Text, map_area: nd.ND_Rect, speed: float, init_direction: ND_Point = ND_Point(1, 0), init_size: int = 4) -> None:
        #
        self.dead: bool = False
        #
        self.color: ND_Color = color
        self.hidding_size: int = init_size  # Taille cachée qu'il faut ajouter au snake quand il avance
        self.direction: ND_Point = init_direction  # A ajouter à la position de la tête
        #
        self.cases: list[ND_Point] = []  # La tête est le premier élément de la liste
        self.cases_angles: list[int] = []
        #
        self.map_area: nd.ND_Rect = map_area
        #
        self.speed: float = speed
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
        self.bot: Optional[SnakeBot] = None


#
def distribute_points(X: int, Y: int, W: int, H: int, N: int) -> list[ND_Point]:
    """
    Distribute N points on a rectangle with integer coordinates.

    Args:
        W (int): Width of the rectangle.
        H (int): Height of the rectangle.
        N (int): Number of points to distribute.

    Returns:
        List[Tuple[int, int]]: List of (x, y) coordinates.
    """
    # Compute optimal grid dimensions
    aspect_ratio: float = W / H
    C: int = math.ceil(math.sqrt(N * aspect_ratio))
    R: int = math.ceil(N / C)

    # Ensure the grid fits within the rectangle
    C = min(C, W)
    R = min(R, H)

    # Compute the points
    points: list[ND_Point] = []
    x_spacing = W / C
    y_spacing = H / R

    for r in range(R):
        for c in range(C):
            if len(points) < N:
                # Round coordinates to nearest integers
                x = round(c * x_spacing + x_spacing / 2)
                y = round(r * y_spacing + y_spacing / 2)
                points.append(ND_Point(x + X, y + Y))

    return points



#
def finish_map_creation(map_mode: str, create_map_square: Callable[[int, int, int, int], None], tx: int, ty: int, nb_snakes: int) -> tuple[list[nd.ND_Rect], list[ND_Point]]:
    #

    #
    snak_init_positions: list[ND_Point] = []
    maps_areas: list[nd.ND_Rect] = []

    #
    if map_mode == "together":
        #
        maps_areas.append( nd.ND_Rect(0, 0, tx, ty) )
        create_map_square(0, 0, tx, ty)
        #
        snak_init_positions = distribute_points(0, 0, tx, ty, nb_snakes)

    #
    elif map_mode == "separete_far":
        #
        maps_row_size: int = math.floor(math.sqrt(nb_snakes))
        #
        maps_origin: ND_Point = ND_Point(0, 0)
        #
        nb_in_current_row: int = 0
        #
        for i in range(nb_snakes):
            #
            maps_areas.append( nd.ND_Rect(maps_origin.x, maps_origin.y, tx, ty) )
            create_map_square(maps_origin.x, maps_origin.y, maps_origin.x+tx, maps_origin.y+ty)
            snak_init_positions.append(maps_origin + ND_Point(tx//2, ty//2))
            #
            nb_in_current_row += 1
            #
            if nb_in_current_row >= maps_row_size:
                #
                maps_origin.x = 0
                maps_origin.y += ty*2 + 2
                nb_in_current_row = 0
            #
            else:
                #
                maps_origin.x += tx*2 + 2

    #
    elif map_mode == "separate_close":
        #
        maps_row_size = math.floor(math.sqrt(nb_snakes))
        #
        maps_origin = ND_Point(0, 0)
        #
        nb_in_current_row = 0
        #
        for i in range(nb_snakes):
            #
            maps_areas.append( nd.ND_Rect(maps_origin.x, maps_origin.y, tx, ty) )
            create_map_square(maps_origin.x, maps_origin.y, maps_origin.x+tx, maps_origin.y+ty)
            snak_init_positions.append(maps_origin + ND_Point(tx//2, ty//2))
            #
            nb_in_current_row += 1
            #
            if nb_in_current_row >= maps_row_size:
                #
                maps_origin.x = 0
                maps_origin.y += ty + 3
                nb_in_current_row = 0
            #
            else:
                #
                maps_origin.x += tx + 3

    #
    print(f"DEBUG || maps_areas = {maps_areas} | snak_init_positions = {snak_init_positions} | nb_snakes = {nb_snakes} | tx = {tx} , ty = {ty}")

    #
    return maps_areas, snak_init_positions



#
def create_map1(win: nd.ND_Window, tx: int, ty: int, map_mode: str, nb_snakes: int) -> tuple[list[nd.ND_Rect], list[ND_Point]]:
    """
    Garden Map, a large square

    Args:
        main_app (nd.ND_MainApp): _description_
    """

    grid: nd.ND_RectGrid = win.main_app.global_vars_get("grid")
    bg_grid: nd.ND_RectGrid = win.main_app.global_vars_get("bg_grid")

    # Wall grid
    wall_grid_elt: Optional[nd.ND_Rectangle] = win.main_app.global_vars_get_optional("wall_grid_elt")

    if not wall_grid_elt:
        wall_grid_elt = nd.ND_Rectangle(
            window=win,
            elt_id="wall_grid",
            position=nd.ND_Position_RectGrid(rect_grid=grid),
            base_bg_color=cl("black")
        )
        win.main_app.global_vars_set("wall_grid_elt", wall_grid_elt)

    #
    wall_grid_id: int = grid.add_element_to_grid(wall_grid_elt, [])

    #
    win.main_app.global_vars_set("wall_grid_id", wall_grid_id)

    # Bg Garden Atlas
    bg_garden_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get_optional("bg_garden_atlas")
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

    #None
    bg_garden_sprites_dict: Optional[dict[str, tuple[nd.ND_Sprite_of_AtlasTexture, int]]] = win.main_app.global_vars_get_optional("bg_garden_sprites_dict")
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
    def create_map_square(map_start_x: int, map_start_y: int, map_end_x: int, map_end_y: int) -> None:
        #
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


        # Remplir les murs
        #
        for y in range(map_start_y-1, map_end_y+1):
            #
            grid.add_element_position(wall_grid_id, ND_Point(map_start_x-1, y))
            grid.add_element_position(wall_grid_id, ND_Point(map_end_x+1, y))

        #
        for x in range(map_start_x-1, map_end_x+2):
            #
            grid.add_element_position(wall_grid_id, ND_Point(x, map_start_y-1))
            grid.add_element_position(wall_grid_id, ND_Point(x, map_end_y+1))

    #
    return finish_map_creation(map_mode, create_map_square, tx, ty, nb_snakes)


#
def create_map2(win: nd.ND_Window, tx: int, ty: int, map_mode: str, nb_snakes: int) -> tuple[list[nd.ND_Rect], list[ND_Point]]:
    """
    Donut map, Donut shape

    Args:
        main_app (nd.ND_MainApp): _description_
    """

    # TODO
    pass

    # TODO
    return [], []



def snake_skin_1(win: nd.ND_Window, snake: Snake, snk_idx: int, grid: nd.ND_RectGrid) -> None:

    #
    snake_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get_optional("snake_atlas")

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
    worm_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get_optional("worm_atlas")

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


