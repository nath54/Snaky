
from dataclasses import dataclass
from typing import Optional, Callable, cast

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
    def __init__(self, main_app: nd.ND_MainApp, security: bool = True, radius: int = 5, include_direction_of_apples_to_context: bool = False, random_weights: int = 3) -> None:
        #
        super().__init__(main_app=main_app, security=security)
        #
        self.grid_tot_size: int = (2*radius ) ** 2
        #
        self.random_weights: int = 3
        #
        self.dim_in: int = self.grid_tot_size + self.random_weights
        #
        self.nb_apples_to_include: int = 0
        self.include_direction_of_apples_to_context: int = include_direction_of_apples_to_context
        if include_direction_of_apples_to_context:
            self.nb_apples_to_include = main_app.global_vars_get_default("nb_init_apples", 3)
            self.dim_in += 2 * self.nb_apples_to_include
        #
        self.dim_out: int = 4
        #
        self.dtype: type = np.float32
        #
        self.weigths: np.ndarray = np.random.normal(loc=0.0, scale=0.5, size=(self.dim_in, self.dim_out)).astype(self.dtype)
        #
        self.radius: int = radius
        #
        self.name: str = self.create_name()

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
        self.weigths = arr
        #
        self.name = self.create_name()

    #
    def create_name(self) -> str:
        #
        name: str = ""
        #
        chars: str = "0123456789abcdefgijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
        one_char_for_nb_params: int = 10
        #
        min_vals: float = -3
        max_vals: float = 3
        #
        # points_per_params: int = len(chars) // one_char_for_nb_params
        #
        currents_params_batch: list[float] = []
        #
        def study_batch() -> None:
            nonlocal name
            if not currents_params_batch:
                return

            # Normalize the batch average to a range [0, len(chars)-1]
            avg_value: float = sum(currents_params_batch) / len(currents_params_batch)
            normalized_value: float = max(min(avg_value, max_vals), min_vals)  # Clamp within min_vals and max_vals
            normalized_index: int = int(((normalized_value - min_vals) / (max_vals - min_vals)) * (len(chars) - 1))
            #
            char_for_batch: str = chars[normalized_index]  # Map to a character
            name += char_for_batch  # Append to the name
        #
        i: int = 0
        for x in range(self.weigths.shape[0]):
            for y in range(self.weigths.shape[1]):
                #
                currents_params_batch.append(self.weigths[x, y])
                i += 1
                #
                if i >= one_char_for_nb_params:
                    #
                    study_batch()
                    i = 0
                    currents_params_batch = []
        #
        if len(currents_params_batch) > 0:
            study_batch()
            i = 0
            currents_params_batch = []
        #
        return name

    #
    def fn_grid_elt_to_matrix_vision_value(self, elt: Optional[nd.ND_Elt], elt_id: Optional[int]) -> float:
        #
        # vide = 0, apple = valeur de la pomme (valeur positive), obstacle (mur ou snake) = -2
        #
        if elt is None or elt_id is None or elt_id < 0:
            return 0.0
        #
        elif elt_id in self.food_ids:  # TODO: food value?
            return 1.0
        #
        return -1.0

    #
    def predict_next_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> Optional[ND_Point]:
        #
        possible_directions: list[int] = self.possible_direction(snake, grid, main_app)
        if not possible_directions or not snake.cases:
            return None
        #

        # CONTEXT INITIALIZATION
        context: np.ndarray = np.zeros((self.dim_in), dtype=self.dtype)

        # FILLING CONTEXT WITH GRID
        grid_center: ND_Point = snake.cases[0]
        grid_x0: int = grid_center.x - self.radius
        grid_x1: int = grid_center.x + self.radius
        grid_y0: int = grid_center.y - self.radius
        grid_y1: int = grid_center.y + self.radius
        #
        grid_vision: np.ndarray = grid.export_chunk_of_grid_to_numpy(x_0=grid_x0, y_0=grid_y0, x_1=grid_x1, y_1=grid_y1, fn_elt_to_value=self.fn_grid_elt_to_matrix_vision_value)
        context[0: self.grid_tot_size] = grid_vision.flatten()

        # FILLING CONTEXT WITH APPLE POSITIONS
        i_apple: int = 0
        i_tot_apples: int = 0
        length_tot_apples: int = main_app.global_vars_list_length("apples_position")
        #
        while i_apple < self.nb_apples_to_include and i_tot_apples < length_tot_apples:
            #
            current_tot_apples_point: ND_Point = cast(ND_Point, main_app.global_vars_list_get_at_idx("apples_position", i_tot_apples))
            while i_tot_apples < length_tot_apples and not snake.map_area.contains_point(current_tot_apples_point):
                i_tot_apples += 1
            #
            context[self.grid_tot_size+2*i_apple: self.grid_tot_size+2*(i_apple+1)] = (current_tot_apples_point-grid_center).np_normalize()

        # PREDICTING OUTPUT
        output: np.ndarray = context @ self.weigths

        # CHOOSING BEST DIRECTION FROM OUTPUT PREDICTIONS
        max_chosen_direction: int = possible_directions[0]
        max_chosen_direction_value: float = output[possible_directions[0]]
        #
        for i in range(1, len(possible_directions)):
            if output[possible_directions[i]] > max_chosen_direction_value:
                max_chosen_direction_value = output[possible_directions[i]]
                max_chosen_direction = possible_directions[i]

        # RETURNING THE BEST CHOSEN DIRECTION
        return self.all_directions[max_chosen_direction]



#
class SnakeBot_Version2(SnakeBot):
    #
    def __init__(self, main_app: nd.ND_MainApp, security: bool = True, radius: int = 4, include_direction_of_apples_to_context: bool = True, random_weights: int = 2) -> None:
        #
        super().__init__(main_app=main_app, security=security)
        #
        self.grid_tot_size: int = (2*radius ) ** 2
        #
        self.random_weights: int = random_weights
        #
        self.dim_in: int = self.grid_tot_size + self.random_weights
        #
        self.nb_apples_to_include: int = 0
        self.include_direction_of_apples_to_context: int = include_direction_of_apples_to_context
        if include_direction_of_apples_to_context:
            self.nb_apples_to_include = main_app.global_vars_get_default("nb_init_apples", 5)
            self.dim_in += 2 * self.nb_apples_to_include
        #
        self.dim_out: int = 4
        #
        self.dim_intermediaire: int = 16
        #
        self.dtype: type = np.float32
        #
        self.weigths_1: np.ndarray = np.random.normal(loc=0.0, scale=3.0, size=(self.dim_in, self.dim_intermediaire)).astype(self.dtype)
        self.weigths_2: np.ndarray = np.random.normal(loc=0.0, scale=3.0, size=(self.dim_intermediaire, self.dim_out)).astype(self.dtype)
        #
        self.radius: int = radius
        #
        self.name: str = self.create_name()

    #
    def save_weights_to_path(self, path: str) -> None:
        #
        self.weigths_1.tofile(path+"_1.dat")
        self.weigths_2.tofile(path+"_2.dat")

    #
    def load_weights_from_path(self, path: str) -> None:
        #
        arr_1: np.ndarray = np.fromfile(path+"_1.dat", dtype=self.dtype)
        arr_2: np.ndarray = np.fromfile(path+"_2.dat", dtype=self.dtype)
        #
        if arr_1.shape != self.weigths_1.shape:
            raise UserWarning(f"Error: the matrix from file \"{path}_1.dat\" has shape {arr_1.shape} while expected shape was {self.weigths_1.shape} !")
        #
        self.weigths_1 = arr_1
        #
        if arr_2.shape != self.weigths_2.shape:
            raise UserWarning(f"Error: the matrix from file \"{path}_2.dat\" has shape {arr_2.shape} while expected shape was {self.weigths_2.shape} !")
        #
        self.weigths_2 = arr_2
        #
        self.name = self.create_name()

    #
    def create_name(self) -> str:
        #
        name: str = ""
        #
        chars: str = "0123456789abcdefgijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
        one_char_for_nb_params: int = 10
        #
        min_vals: float = -3
        max_vals: float = 3
        #
        # points_per_params: int = len(chars) // one_char_for_nb_params
        #
        currents_params_batch: list[float] = []
        #
        def study_batch() -> None:
            nonlocal name
            if not currents_params_batch:
                return

            # Normalize the batch average to a range [0, len(chars)-1]
            avg_value: float = sum(currents_params_batch) / len(currents_params_batch)
            normalized_value: float = max(min(avg_value, max_vals), min_vals)  # Clamp within min_vals and max_vals
            normalized_index: int = int(((normalized_value - min_vals) / (max_vals - min_vals)) * (len(chars) - 1))
            #
            char_for_batch: str = chars[normalized_index]  # Map to a character
            name += char_for_batch  # Append to the name
        #
        i: int = 0
        for x in range(self.weigths_1.shape[0]):
            for y in range(self.weigths_1.shape[1]):
                #
                currents_params_batch.append(self.weigths_1[x, y])
                i += 1
                #
                if i >= one_char_for_nb_params:
                    #
                    study_batch()
                    i = 0
                    currents_params_batch = []
        #
        for x in range(self.weigths_2.shape[0]):
            for y in range(self.weigths_2.shape[1]):
                #
                currents_params_batch.append(self.weigths_2[x, y])
                i += 1
                #
                if i >= one_char_for_nb_params:
                    #
                    study_batch()
                    i = 0
                    currents_params_batch = []
        #
        if len(currents_params_batch) > 0:
            study_batch()
            i = 0
            currents_params_batch = []
        #
        return name

    #
    def fn_grid_elt_to_matrix_vision_value(self, elt: Optional[nd.ND_Elt], elt_id: Optional[int]) -> float:
        #
        # vide = 0, apple = valeur de la pomme (valeur positive), obstacle (mur ou snake) = -2
        #
        if elt is None or elt_id is None or elt_id < 0:
            return 0.0
        #
        elif elt_id in self.food_ids:  # TODO: food value?
            return 1.0
        #
        return -1.0

    #
    def predict_next_direction(self, snake: "Snake", grid: nd.ND_RectGrid, main_app: nd.ND_MainApp) -> Optional[ND_Point]:
        #
        possible_directions: list[int] = self.possible_direction(snake, grid, main_app)
        if not possible_directions or not snake.cases:
            return None
        #

        # CONTEXT INITIALIZATION
        context: np.ndarray = np.zeros((self.dim_in,), dtype=self.dtype)

        # FILLING CONTEXT WITH GRID
        grid_center: ND_Point = snake.cases[0]
        grid_x0: int = grid_center.x - self.radius
        grid_x1: int = grid_center.x + self.radius
        grid_y0: int = grid_center.y - self.radius
        grid_y1: int = grid_center.y + self.radius
        #
        grid_vision: np.ndarray = grid.export_chunk_of_grid_to_numpy(x_0=grid_x0, y_0=grid_y0, x_1=grid_x1, y_1=grid_y1, fn_elt_to_value=self.fn_grid_elt_to_matrix_vision_value)
        context[0: self.grid_tot_size] = grid_vision.flatten()

        # FILLING CONTEXT WITH APPLE POSITIONS
        i_apple: int = 0
        i_tot_apples: int = 0
        length_tot_apples: int = main_app.global_vars_list_length("apples_position")
        #
        while i_apple < self.nb_apples_to_include and i_tot_apples < length_tot_apples:
            #
            current_tot_apples_point: ND_Point = cast(ND_Point, main_app.global_vars_list_get_at_idx("apples_position", i_tot_apples))
            while i_tot_apples < length_tot_apples and not snake.map_area.contains_point(current_tot_apples_point):
                i_tot_apples += 1
            #
            context[self.grid_tot_size+2*i_apple: self.grid_tot_size+2*(i_apple+1)] = (current_tot_apples_point-grid_center).np_normalize()

        # FILLING RANDOM CONTEXT
        a: int = self.grid_tot_size+2*(i_apple+1)
        context[a:a+self.random_weights] = np.random.normal(loc=0.0, scale=1.0, size=(self.random_weights,)).astype(self.dtype)

        # PREDICTING OUTPUT
        output: np.ndarray = context @ self.weigths_1  # First Weight matrix multiplication
        output = output * (output > 0)  # ReLU Gate
        output = output @ self.weigths_2  # Second Weight matrix multiplication

        # CHOOSING BEST DIRECTION FROM OUTPUT PREDICTIONS
        max_chosen_direction: int = possible_directions[0]
        max_chosen_direction_value: float = output[possible_directions[0]]
        #
        for i in range(1, len(possible_directions)):
            if output[possible_directions[i]] > max_chosen_direction_value:
                max_chosen_direction_value = output[possible_directions[i]]
                max_chosen_direction = possible_directions[i]

        # RETURNING THE BEST CHOSEN DIRECTION
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
        maps_row_size: int = round(math.sqrt(nb_snakes))
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
        maps_row_size = round(math.sqrt(nb_snakes))
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
        # if sprite_pos_id not in bg_garden_sprites_dict:
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


