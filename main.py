
from typing import Optional

import os
import json

import lib_nadisplay as nd

from lib_nadisplay_sdl_sdlgfx import ND_Display_SDL_SDLGFX as DisplayClass, ND_Window_SDL_SDLGFX as WindowClass
# from lib_nadisplay_sdl_opengl import ND_Display_SDL_OPENGL as DisplayClass, ND_Window_SDL_OPENGL as WindowClass  # Not working at all
# from lib_nadisplay_glfw_opengl import ND_Display_GLFW_OPENGL as DisplayClass, ND_Window_GLFW_OPENGL as WindowClass  # Not working at all
# from lib_nadisplay_glfw_vulkan import ND_Display_GLFW_VULKAN as DisplayClass, ND_Window_GLFW_VULKAN as WindowClass  # Not working at all
from lib_nadisplay_sdl import ND_EventsManager_SDL as EventsManagerClass
# from lib_nadisplay_glfw import ND_EventsManager_GLFW as EventsManagerClass  # Not working at all
# from lib_nadisplay_pygame import ND_Display_Pygame as DisplayClass, ND_Window_Pygame as WindowClass, ND_EventsManager_Pygame as EventsManagerClass  # Working a little

from lib_snake import SnakePlayerSetting

from scene_main_menu import create_main_menu_scene
from scene_game import create_game_scene
from scene_game_end import create_end_menu
from scene_game_set_up import create_game_setup_scene
from scene_pause_screen import create_pause_menu
from scene_bots_training_menu import create_training_menu_scene


#
MAIN_WINDOW_ID: int = 0


#
bots_types_keys: dict[str, list[str]] = {
    "bot_v1": ["path_weights", "radius", "nb_apples", "random_weights"],
    "bot_v2": ["path_weights_1", "path_weights_2", "radius", "nb_apples", "random_weights"]
}


<<<<<<< HEAD
# Update the snake direction (checking if the new direction is not the opposite of the current one)
def event_set_snake_direction(main_app: nd.ND_MainApp, direction: ND_Point, snake_idx: int) -> None:

    snakes: Optional[dict[int, Snake]] = main_app.global_vars_get("snakes")

    if snakes is None:
        return

    if snake_idx not in snakes:
        return

    if snakes[snake_idx].last_applied_direction != -direction:
        snakes[snake_idx].direction = direction


# Initialize the game
def on_bt_click_init_game(win: nd.ND_Window) -> None:

    # Cleaning
    win.main_app.global_vars_set("snakes", {})
    win.main_app.global_vars_set("dead_snakes", {})
    win.main_app.global_vars_set("snakes_speed", 0.215)  # Time between each snakes update
    win.main_app.global_vars_set("game_pause", 0.0)
    win.main_app.global_vars_set("game_debut_pause", 0.0)


    # Getting Settings
    # (x, y, cl, size, id, player, (key_up, key_left, key_bottom, key_right))
    a: Optional[list[tuple[str, ND_Point, ND_Color, int, int, str, Optional[tuple[str, str, str, str]]]]] = win.main_app.global_vars_get("init_snakes")
    
    init_snakes: list[tuple[str, ND_Point, ND_Color, int, int, str, Optional[tuple[str, str, str, str]]]] = \
        a if a is not None else [
            ("humain1", ND_Point(TERRAIN_X + TERRAIN_W // 3, TERRAIN_Y + (TERRAIN_H * 2) //3), ND_Color(255, 0, 0), 4, 0, "human", ("keydown_z", "keydown_q", "keydown_s", "keydown_d")),
            ("humain2", ND_Point(TERRAIN_X + (TERRAIN_W * 2) // 3, TERRAIN_Y + TERRAIN_H //3), ND_Color(0, 255, 0), 4, 0, "human", ("keydown_up arrow", "keydown_left arrow", "keydown_down arrow", "keydown_right arrow")),
            # ("humain3", ND_Point(TERRAIN_X + TERRAIN_W // 3, TERRAIN_Y + TERRAIN_H //3), ND_Color(0, 0, 255), 4, 0, "human", ("keydown_u", "keydown_h", "keydown_j", "keydown_k"))
        ]

    nb_init_apples: int = 3

    grid: Optional[nd.ND_RectGrid] = win.main_app.global_vars_get("grid")
    cam_grid: Optional[nd.ND_CameraGrid] = win.main_app.global_vars_get("cam_grid")
    game_infos_container: Optional[nd.ND_Container] = win.main_app.global_vars_get("game_infos_container")

    # Food
    food_1_elt_name: Optional[str] = win.main_app.global_vars_get("food_1_elt_name")
    food_2_elt_name: Optional[str] = win.main_app.global_vars_get("food_2_elt_name")
    food_3_elt_name: Optional[str] = win.main_app.global_vars_get("food_3_elt_name")
    #
    if food_1_elt_name is None or food_2_elt_name is None or food_3_elt_name is None:
        raise UserWarning("Error: no food elt to use !")
    #
    food_1_elt: Optional[nd.ND_Elt] = win.main_app.global_vars_get(food_1_elt_name)
    food_2_elt: Optional[nd.ND_Elt] = win.main_app.global_vars_get(food_2_elt_name)
    food_3_elt: Optional[nd.ND_Elt] = win.main_app.global_vars_get(food_3_elt_name)

    # Snake Atlas
    snake_atlas: Optional[nd.ND_AtlasTexture] = win.main_app.global_vars_get("snake_atlas")

    # Errors
    if grid is None or cam_grid is None:
        raise UserWarning("Error: no grid, cannot initialise the game !")
    #
    if snake_atlas is None or food_1_elt is None or food_2_elt is None or food_3_elt is None:
        raise UserWarning("Error: Snakes and/or Food textures are not correctly initialized !")
    #
    if game_infos_container is None:
        raise UserWarning("Error: no game_infos_container !")

    # On nettoie les scorebox des anciennes parties
    trash: list[Optional[nd.ND_Container]] = cast(list[Optional[nd.ND_Container]], game_infos_container.elements)
    game_infos_container.elements = []
    i: int
    sb: Optional[nd.ND_Container]
    for (i, sb) in enumerate(trash):
        del sb
        trash[i] = None
    del trash

    grid.clean()

    # Wall grid
    wall_grid_elt: Optional[nd.ND_Rectangle] = win.main_app.global_vars_get("wall_grid_elt")

    if not wall_grid_elt:
        wall_grid_elt = nd.ND_Rectangle(
            window=win,
            elt_id="wall_grid",
            position=nd.ND_Position_RectGrid(rect_grid=grid),
            base_bg_color=cl("black")
        )
        win.main_app.global_vars_set("wall_grid_elt", wall_grid_elt)

    wall_grid_id: int = grid.add_element_to_grid(wall_grid_elt, [])

    win.main_app.global_vars_set("wall_grid_id", wall_grid_id)

    #
    food_1_grid_id: int = grid.add_element_to_grid(food_1_elt, [])
    food_2_grid_id: int = grid.add_element_to_grid(food_2_elt, [])
    food_3_grid_id: int = grid.add_element_to_grid(food_3_elt, [])

    #
    win.main_app.global_vars_set("food_1_grid_id", food_1_grid_id)
    win.main_app.global_vars_set("food_2_grid_id", food_2_grid_id)
    win.main_app.global_vars_set("food_3_grid_id", food_3_grid_id)


    # New Game

    # Init grid

    xx: int
    yy: int

    for yy in range(TERRAIN_Y-1, TERRAIN_Y+TERRAIN_H+1):

        grid.add_element_position(wall_grid_id, ND_Point(TERRAIN_X-1, yy))
        grid.add_element_position(wall_grid_id, ND_Point(TERRAIN_X+TERRAIN_W+1, yy))


    for xx in range(TERRAIN_X-1, TERRAIN_X+TERRAIN_W+2):

        grid.add_element_position(wall_grid_id, ND_Point(xx, TERRAIN_Y-1))
        grid.add_element_position(wall_grid_id, ND_Point(xx, TERRAIN_Y+TERRAIN_H+1))

    #
    create_map1(win, TERRAIN_W, TERRAIN_H)

    #
    snk_idx: int
    snk: tuple[str, ND_Point, ND_Color, int, int, str, Optional[tuple[str, str, str, str]]]
    for (snk_idx, snk) in enumerate(init_snakes):

        # Create score box for snake
        scorebox_row: nd.ND_Container = nd.ND_Container(
            window=win,
            elt_id=f"snake_{snk_idx}_scorebox_row",
            position=nd.ND_Position_Container("90%", "15%", container=game_infos_container,
                                position_margins=ND_Position_Margins(margin_left="50%", margin_right="50%", margin_top=15),
                                position_constraints=ND_Position_Constraints(max_height=40)),
            element_alignment="row"
        )
        #
        snake_icon: nd.ND_Sprite = nd.ND_Sprite(window=win,
                                                elt_id=f"snake_{snk_idx}_scorebox_icon",
                                                position=nd.ND_Position_Container("square", "100%", container=scorebox_row),
                                                base_texture="res/sprites/snake_icon.png")
        #
        snake_icon.transformations = nd.ND_Transformations(color_modulation=snk[2])
        #
        snake_name: nd.ND_Text = nd.ND_Text(window=win,
                                            elt_id=f"snake_{snk_idx}_scorebox_name",
                                            position=nd.ND_Position_Container("50%", "100%", container=scorebox_row, position_margins=ND_Position_Margins(margin_left=15, margin_right=15)),
                                            text=snk[0],
                                            font_size=28,
                                            font_color=snk[2],
                                            text_h_align="left")
        #
        snake_score: nd.ND_Text = nd.ND_Text(window=win,
                                            elt_id=f"snake_{snk_idx}_scorebox_score",
                                            position=nd.ND_Position_Container("20%", "100%", container=scorebox_row),
                                            text="0",
                                            font_size=28,
                                            font_color=snk[2],
                                            text_h_align="left")
        #
        scorebox_row.add_element(snake_icon)
        scorebox_row.add_element(snake_name)
        scorebox_row.add_element(snake_score)
        #
        game_infos_container.add_element(scorebox_row)

        # Create Snake
        snake: Snake = Snake( pseudo=snk[0], init_position=snk[1], color=snk[2], init_size=snk[3], score_elt=snake_score )
        snake.last_update = time.time()


        win.main_app.global_vars_dict_set("snakes", snk_idx, snake)


        # Snake head
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
        snake.sprites["head"] = (sprite_head, grid.add_element_to_grid(sprite_head, []))

        # Snake tail
        sprite_tail: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
            window=win,
            elt_id=f"snake_{snk_idx}_tail",
            position=nd.ND_Position_RectGrid(rect_grid=grid),
            atlas_texture=snake_atlas,
            tile_x=0, tile_y=0
        )
        sprite_tail.transformations.color_modulation = snake.color
        snake.sprites["tail"] = (sprite_tail, grid.add_element_to_grid(sprite_tail, []))

        # Snake body
        sprite_body: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
            window=win,
            elt_id=f"snake_{snk_idx}_body",
            position=nd.ND_Position_RectGrid(rect_grid=grid),
            atlas_texture=snake_atlas,
            tile_x=1, tile_y=0
        )
        sprite_body.transformations.color_modulation = snake.color
        snake.sprites["body"] = (sprite_body, grid.add_element_to_grid(sprite_body, []))

        # Snake body (corner edition)
        sprite_body_corner: nd.ND_Sprite_of_AtlasTexture = nd.ND_Sprite_of_AtlasTexture(
            window=win,
            elt_id=f"snake_{snk_idx}_body_corner",
            position=nd.ND_Position_RectGrid(rect_grid=grid),
            atlas_texture=snake_atlas,
            tile_x=2, tile_y=0
        )
        sprite_body_corner.transformations.color_modulation = snake.color
        snake.sprites["body_corner"] = (sprite_body_corner, grid.add_element_to_grid(sprite_body_corner, []))

        #
        dir_angle: int = min(0, snake.direction.x) * 180 + 90 * snake.direction.y

        #
        snake.cases.append((snk[1]))
        snake.cases_angles.append(dir_angle)
        grid.add_element_position(snake.sprites["head"][1], snk[1])
        grid.set_transformations_to_position(snk[1], nd.ND_Transformations(rotation=dir_angle))
        #
        pos_tail: ND_Point = snk[1] - snake.direction
        #
        snake.cases.append(pos_tail)
        snake.cases_angles.append(dir_angle)
        grid.add_element_position(snake.sprites["tail"][1], pos_tail)
        grid.set_transformations_to_position(pos_tail, nd.ND_Transformations(rotation=dir_angle))

        #
        if snk[5] == "human" and snk[6] is not None:
    
            win.main_app.add_function_to_event_fns_queue(snk[6][0],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(0, -1), snk_idx))

            win.main_app.add_function_to_event_fns_queue(snk[6][1],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(-1, 0), snk_idx))

            win.main_app.add_function_to_event_fns_queue(snk[6][2],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(0, 1), snk_idx))

            win.main_app.add_function_to_event_fns_queue(snk[6][3],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(1, 0), snk_idx))

        # TODO: bots

    # Init Food
    p: Optional[ND_Point]
    for _ in range(nb_init_apples):

        p = grid.get_empty_case_in_range(TERRAIN_X, TERRAIN_X + TERRAIN_W, TERRAIN_Y, TERRAIN_Y + TERRAIN_H)

        if p is not None:
            #
            food_grid_id: int = random.choice([food_1_grid_id, food_2_grid_id, food_3_grid_id])
            #
            grid.add_element_position(food_grid_id, p)

    # center camera on grid area
    cam_grid.move_camera_to_grid_area(
        nd.ND_Rect(TERRAIN_X+1, TERRAIN_Y+1, TERRAIN_W-2, TERRAIN_H-2)
    )

    # Setting New State
    win.set_state("game")


# Quit the game
def on_bt_click_quit(win: nd.ND_Window) -> None:

    win.main_app.quit()


#
def on_pause_pressed(main_app: nd.ND_MainApp) -> None:
    #
    if main_app.display is None:
        return
    #
    win: Optional[nd.ND_Window] = main_app.display.windows[MAIN_WINDOW_ID]
    #
    if not win:
        return
    #
    if win.state == "game":
        #
        main_app.global_vars_set("game_pause", time.time())
        #
        win.set_state("game_pause")
    #
    elif win.state == "game_pause":
        #
        gg: float = cast(float, main_app.global_vars_get("game_pause"))
        main_app.global_vars_set("game_pause", time.time() - gg)
        #
        win.set_state("game")


#
def update_physic(mainApp: nd.ND_MainApp, delta_time: float) -> None:

    if mainApp.display is None:
        return

    win: Optional[nd.ND_Window] = mainApp.display.windows[MAIN_WINDOW_ID]

    if win is None or win.state != "game":
        return


    grid: Optional[nd.ND_RectGrid] = mainApp.global_vars_get("grid")
    snakes: Optional[dict[int, Snake]] = mainApp.global_vars_get("snakes")
    dead_snakes: Optional[dict[int, Snake]] = mainApp.global_vars_get("dead_snakes")
    snakes_speed: Optional[float] = mainApp.global_vars_get("snakes_speed")
    wall_grid_id: Optional[int] = mainApp.global_vars_get("wall_grid_id")
    food_1_grid_id: Optional[int] = mainApp.global_vars_get("food_1_grid_id")
    food_2_grid_id: Optional[int] = mainApp.global_vars_get("food_2_grid_id")
    food_3_grid_id: Optional[int] = mainApp.global_vars_get("food_3_grid_id")

    #
    if grid is None or snakes is None or dead_snakes is None or\
       snakes_speed is None or wall_grid_id is None or\
       food_1_grid_id is None or food_2_grid_id is None or food_3_grid_id is None:
        return


    now: float = time.time()

    game_pause: float = cast(float, win.main_app.global_vars_get("game_pause"))
    win.main_app.global_vars_set("game_pause", 0)


    snaks_to_die: list[int] = []

    snak: Snake
    for snak_idx, snak in snakes.items():
        #
        snak.last_update += game_pause
        #
        while now - snak.last_update >= snakes_speed:
            #
            snak.last_update += snakes_speed
            #
            nhp: ND_Point = snak.cases[0] + snak.direction
            snak.last_applied_direction = snak.direction


            # Test de collision
            elt_id_col: Optional[int] = grid.get_element_id_at_grid_case(nhp)

            #
            if elt_id_col is not None:
                #
                foods: list[int] = [food_1_grid_id, food_2_grid_id, food_3_grid_id]
                #
                fi: int = foods.index(elt_id_col) if elt_id_col in foods else -1
                if fi != -1:

                    snak.score += fi + 1
                    snak.score_elt.text = str(snak.score)
                    snak.hidding_size += 1

                    # On rajoute une nouvelle pomme
                    p: Optional[ND_Point] = grid.get_empty_case_in_range(TERRAIN_X, TERRAIN_X + TERRAIN_W, TERRAIN_Y, TERRAIN_Y + TERRAIN_H)
                    #
                    if p is not None:
                        #
                        food_grid_id: int = random.choice([food_1_grid_id, food_2_grid_id, food_3_grid_id])
                        #
                        grid.add_element_position(food_grid_id, p)

                else:

                    # COLLISION : Le serpent meurt, on remplace son corps par des murs
                    pos: nd.ND_Point
                    for pos in snak.cases:
                        grid.remove_at_position(pos)
                        grid.add_element_position(wall_grid_id, pos)

                    #
                    snaks_to_die.append(snak_idx)
                    break
            #
            dir_angle: int = min(0, snak.direction.x) * 180 + 90 * snak.direction.y

            #
            snak.cases.insert(0, nhp)
            snak.cases_angles.insert(0, dir_angle)
            grid.add_element_position(snak.sprites["head"][1], nhp)
            grid.set_transformations_to_position(nhp, nd.ND_Transformations(rotation=dir_angle))
            #
            if len(snak.cases) > 2:
                #
                c0: ND_Point = snak.cases[0] - snak.cases[1]
                c2: ND_Point = snak.cases[2] - snak.cases[1]
                #
                grid.remove_at_position(snak.cases[1])
                #
                if c0.x == c2.x or c0.y == c2.y:
                    grid.add_element_position(snak.sprites["body"][1], snak.cases[1])
                else:
                    angle: int = 0
                    #
                    if c0 == ND_Point(0, -1):
                        #
                        if c2 == ND_Point(-1, 0):
                            angle = 90
                        #
                        elif c2 == ND_Point(1, 0):
                            angle = 180
                    #
                    elif c0 == ND_Point(1, 0):
                        #
                        if c2 == ND_Point(0, 1):
                            angle = 270
                        #
                        elif c2 == ND_Point(0, -1):
                            angle = 180
                    #
                    elif c0 == ND_Point(0, 1):
                        #
                        if c2 == ND_Point(1, 0):
                            angle = 270
                    #
                    elif c0 == ND_Point(-1, 0):
                        #
                        if c2 == ND_Point(0, -1):
                            angle = 90
                    #
                    grid.add_element_position(snak.sprites["body_corner"][1], snak.cases[1])
                    grid.set_transformations_to_position(snak.cases[1], nd.ND_Transformations(rotation=angle))

            #
            if snak.hidding_size > 0:  # En avancant, le serpent augmente sa taille
                #
                snak.hidding_size -= 1
            #
            else:
                #
                grid.remove_at_position(snak.cases[-2])
                grid.add_element_position(snak.sprites["tail"][1], snak.cases[-2])
                #
                c0 = snak.cases[-3] - snak.cases[-2]
                #
                if c0 == ND_Point(1, 0):
                    grid.set_transformations_to_position(snak.cases[-2], nd.ND_Transformations(rotation=0))
                elif c0 == ND_Point(0, 1):
                    grid.set_transformations_to_position(snak.cases[-2], nd.ND_Transformations(rotation=90))
                elif c0 == ND_Point(-1, 0):
                    grid.set_transformations_to_position(snak.cases[-2], nd.ND_Transformations(rotation=180))
                elif c0 == ND_Point(0, -1):
                    grid.set_transformations_to_position(snak.cases[-2], nd.ND_Transformations(rotation=270))
                #
                grid.remove_at_position(snak.cases[-1])
                grid.set_transformations_to_position(snak.cases[-1], None)
                #
                snak.cases.pop(-1)


    #
    for snak_idx in snaks_to_die:
        dead_snakes[snak_idx] = snakes[snak_idx]
        del snakes[snak_idx]

    #
    if len(snakes) == 0:  # Plus de serpents en vie => Partie finie
        #
        win.state = "end_menu"


#
def animate_main_menu(mainApp: nd.ND_MainApp, delta_time: float) -> None:
    #
    game_title: Optional[nd.ND_Text] = mainApp.global_vars_get("main_menu_title")
    t: float = mainApp.get_time_msec()
    #
    if game_title is not None:
        #
        game_title.font_color.r = int(((math.sin(0.0002 * t ) + 1) / 2 ) * 255)
        game_title.font_color.g = int(((math.sin(0.002 * t + 0.023 * (t ** 0.1)) + 1) / 2 ) * 255)
        game_title.font_color.b = int(((math.sin(0.0004 * t - 0.0121 * (t ** 0.1)) + 1) / 2 ) * 255)
        #
        game_title.text = "Snaky" + "." * ( round(((math.sin(0.00002 * t ) + 1) / 2 ) * 255) % 4)
    #
    if False and mainApp.display is not None:
        #
        game_window: Optional[nd.ND_Window] = None
        for win in mainApp.display.windows.values():
            #
            if win is not None:
                game_window = win
                break
        #
        if game_window is not None:
            #
            m: int = round(((math.sin(0.001 * t ) + 1) / 2 ) * 300)
            #
            game_window.set_size(400 + m, 300 + m)


#
def create_main_menu_scene(win: nd.ND_Window) -> nd.ND_Scene:
    #
    main_menu_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="main_menu",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="main_menu"
    )

    main_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )

    bottom_row_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bottom_row_container",
        position=nd.ND_Position_Container(w="100%", h="75%", container=main_menu_container),
        element_alignment="row"
    )

    bts_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bts_container",
        position=nd.ND_Position_Container(w="30%", h="100%", container=bottom_row_container),
        element_alignment="col"
    )

    game_title: nd.ND_Text = nd.ND_Text(
                            window=win,
                            elt_id="game_title",
                            position=nd.ND_Position_Container(w="100%", h="20%", container=main_menu_container, position_margins=ND_Position_Margins(margin_top=25, margin_bottom=25)),
                            text="Snaky",
                            font_size=50,
                            font_color=cl("violet"),
    )

    win.main_app.global_vars_set("main_menu_title", game_title)
    win.main_app.add_function_to_mainloop_fns_queue("physics", animate_main_menu)

    bt_play: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_play",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_init_game,
        text="Play !",
        font_size=35
    )

    bt_train: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_train",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=None,
        text="Train Bots",
        font_size=35
    )

    bt_settings: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_settings",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=None,
        text="Settings",
        font_size=35
    )

    bt_quit: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_quit",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_quit,
        text="Quit",
        font_size=35
    )

    bts_container.add_element(bt_play)
    bts_container.add_element(bt_train)
    bts_container.add_element(bt_settings)
    bts_container.add_element(bt_quit)

    main_menu_container.add_element(game_title)
    main_menu_container.add_element(bottom_row_container)

    bottom_row_container.add_element(bts_container)

    main_menu_scene.add_element(0, main_menu_container)

    return main_menu_scene


#
def create_game_scene(win: nd.ND_Window) -> nd.ND_Scene:
    #
    scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="game",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state=set(["game", "game_pause", "end_menu"])
    )

    #
    game_row_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="game_row_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="row"
    )

    #
    grid: nd.ND_RectGrid = nd.ND_RectGrid(
        window=win,
        elt_id="game_grid",
        position=ND_Position(0, 0),
        grid_tx=32,
        grid_ty=32,
        grid_lines_width=0,
        grid_lines_color=ND_Color(255, 255, 255)
    )
    #
    win.main_app.global_vars_set("grid", grid)

    #
    bg_grid: nd.ND_RectGrid = nd.ND_RectGrid(
        window=win,
        elt_id="game_bg_grid",
        position=ND_Position(0, 0),
        grid_tx=32,
        grid_ty=32,
        grid_lines_width=0,
        grid_lines_color=ND_Color(255, 255, 255)
    )
    #
    win.main_app.global_vars_set("bg_grid", bg_grid)


    #
    camera_grid: nd.ND_CameraGrid = nd.ND_CameraGrid(
        window=win,
        elt_id="camera_grid",
        position=nd.ND_Position_Container(
            w="60%", h="90%", container=game_row_container,
            position_margins=ND_Position_Margins(
                margin_top="50%", margin_bottom="50%", margin_left="50%", margin_right="50%"
            )
        ),
        grids_to_render=[bg_grid, grid]
    )
    #
    game_row_container.add_element(camera_grid)
    #
    win.main_app.global_vars_set("cam_grid", camera_grid)
    #
    win.main_app.add_function_to_event_fns_queue("window_resized",
                lambda main_app: camera_grid.move_camera_to_grid_area(
                    nd.ND_Rect(TERRAIN_X+1, TERRAIN_Y+1, TERRAIN_W-1, TERRAIN_H-1)
                )
    )

    #
    multilayer_infos: nd.ND_MultiLayer = nd.ND_MultiLayer(
        window=win,
        elt_id="game_infos_box",
        position=nd.ND_Position_Container(
            w="35%", h="90%",
            container=game_row_container,
            position_margins=ND_Position_Margins(
                margin_top="50%", margin_bottom="50%", margin_left="50%", margin_right="50%"
            )
        ),
        elements_layers={}
    )

    #
    game_row_container.add_element(multilayer_infos)

    #
    background_infos: nd.ND_Rectangle = nd.ND_Rectangle(
        window=win,
        elt_id="background_infos",
        position=nd.ND_Position_MultiLayer(multilayer=multilayer_infos),
        base_bg_color = cl((30, 1, 20)),
        hover_bg_color = cl((32, 3, 22)),
        clicked_bg_color = cl((28, 0, 18))
    )

    #
    game_infos_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="game_infos",
        position=nd.ND_Position_MultiLayer(multilayer=multilayer_infos),
        element_alignment="col"
    )
    #
    win.main_app.global_vars_set("game_infos_container", game_infos_container)

    #
    multilayer_infos.add_element(0, background_infos)
    multilayer_infos.add_element(1, game_infos_container)

    #
    scene.add_element(0, game_row_container)

    #
    coin_atlas: nd.ND_AtlasTexture = nd.ND_AtlasTexture(
        window=win,
        texture_atlas_path="res/sprites/coin_grayscale.png",
        tiles_size=ND_Point(31, 31)
    )
    coin_3: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="spinning coin",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "spinning": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"spinning_coin_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=coin_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(8)
            ]
        },
        animations_speed={},
        default_animation_speed=0.1,
        default_animation="spinning"
    )
    coin_2: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="spinning coin",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "spinning": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"spinning_coin_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=coin_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(8)
            ]
        },
        animations_speed={},
        default_animation_speed=0.1,
        default_animation="spinning"
    )
    coin_1: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="spinning coin",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "spinning": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"spinning_coin_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=coin_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(8)
            ]
        },
        animations_speed={},
        default_animation_speed=0.1,
        default_animation="spinning"
    )
    #
    coin_1.transformations = ND_Transformations(color_modulation=cl("copper"))
    coin_2.transformations = ND_Transformations(color_modulation=cl("silver"))
    coin_3.transformations = ND_Transformations(color_modulation=cl("gold web golden"))
    #
    snake_atlas: nd.ND_AtlasTexture = nd.ND_AtlasTexture(
        window=win,
        texture_atlas_path="res/sprites/snakes_sprites4.png",
        tiles_size=ND_Point(32, 32)
    )

    #
    win.main_app.global_vars_set("coin_3_elt", coin_3)
    win.main_app.global_vars_set("coin_2_elt", coin_2)
    win.main_app.global_vars_set("coin_1_elt", coin_1)
    #
    win.main_app.global_vars_set("food_3_elt_name", "coin_3_elt")
    win.main_app.global_vars_set("food_2_elt_name", "coin_2_elt")
    win.main_app.global_vars_set("food_1_elt_name", "coin_1_elt")
    #
    win.main_app.global_vars_set("snake_atlas", snake_atlas)

    #
    win.main_app.add_function_to_event_fns_queue("keydown_p", on_pause_pressed)

    #
    return scene


#
def create_end_menu(win: nd.ND_Window) -> nd.ND_Scene:
    #
    scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="end_menu",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="end_menu"
    )

    #
    end_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="end_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )

    #
    bts_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bts_container",
        position=nd.ND_Position_Container(w="100%", h="50%", container=end_menu_container),
        element_alignment="row"
    )

    #
    text1: nd.ND_Text = nd.ND_Text(
                            window=win,
                            elt_id="game_title",
                            position=nd.ND_Position_Container(w="100%", h="33%", container=end_menu_container, position_margins=ND_Position_Margins(margin_top=25, margin_bottom=25)),
                            text="The game has finished !",
                            font_size=40,
                            font_color=cl("red"),
    )

    #
    bt_replay: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_replay",
        position=nd.ND_Position_Container(w=150, h=75, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_init_game,
        text="Play again !",
        font_size=20
    )

    #
    bt_quit: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_quit",
        position=nd.ND_Position_Container(w=150, h=75, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_quit,
        text="Quit !",
        font_size=20
    )

    #
    bts_container.add_element(bt_replay)
    bts_container.add_element(bt_quit)

    #
    end_menu_container.add_element(text1)
    end_menu_container.add_element(bts_container)

    #
    scene.add_element(0, end_menu_container)

    #
    return scene
=======
#
def verify_json_dict_is_bot(bot_dict: dict) -> bool:
    #
    if "name" not in bot_dict:
        return False
    #
    if "type" not in bot_dict:
        return False
    #
    if "max_score" not in bot_dict:
        return False
    #
    if "scores" not in bot_dict:
        return False
    #
    if bot_dict["type"] not in bots_types_keys:
        return False
    #
    key: str
    for key in bots_types_keys:
        if key not in bot_dict:
            return False
    #
    return True
>>>>>>> 9f8ad6394a4b763153e1ac1067d070ad71177fd2



#
if __name__ == "__main__":

    #
    snakes_bot_paths: str = "./bots/"
    #
    if not os.path.exists(snakes_bot_paths):
        os.makedirs(snakes_bot_paths)

    #
    app: nd.ND_MainApp = nd.ND_MainApp(
                        DisplayClass=DisplayClass,
                        WindowClass=WindowClass,
                        EventsManagerClass=EventsManagerClass
    )
    #
    if app.display is None:
        exit(1)

    # Init fonts
    app.display.add_font("res/fonts/aAsianNinja.otf", "AsianNinja")
    app.display.add_font("res/fonts/HIROMISAKE.ttf", "Hiromisake")
    app.display.add_font("res/fonts/Korean_Calligraphy.ttf", "KoreanCalligraphy")
    app.display.default_font = "KoreanCalligraphy"

    #
    win_id: int = app.display.create_window({
        "title": "Super Snaky",
        "size": (1750, 950),
        "window_id": MAIN_WINDOW_ID,
        "init_state": "main_menu"
    }, True)
    #
    win: Optional[nd.ND_Window] = app.display.get_window(win_id)
    #
    if win is None:
        exit(1)

    #
    app.global_vars_set("MAIN_WINDOW_ID", 0)

    # Chargement des bots qui ont déjà été sauvegardés
    app.global_vars_set("bots", {})

    #
    bot_dict: dict
    for filepath in os.listdir(snakes_bot_paths):
        #
        if not filepath.endswith(".json"):
            continue

        # Les bots seront enregistrés dans un fichier json

        #
        with open(f"{snakes_bot_paths}{filepath}", "r", encoding="utf-8") as f:
            bot_dict = json.load(f)
        #
        if not verify_json_dict_is_bot(bot_dict):
            #
            continue
        #
        app.global_vars_dict_set("bots", bot_dict["name"], bot_dict)

    # On peut facilement remplacer quelques paramètres par défaut ici:
    app.global_vars_set("game_nb_init_apples", 1)
    app.global_vars_set("game_init_snake_size", 0)
    app.global_vars_set("game_map_mode", "separate_close")  # "together", "separate_far", "separate_close"
    app.global_vars_set("game_terrain_w", 11)
    app.global_vars_set("game_terrain_h", 11)
    app.global_vars_set("game_snakes_speed", 0.01)

    #
    init_snake_size: int = win.main_app.global_vars_get_default("game_init_snake_size", 0)  #
    app.global_vars_set("game_init_snakes",
        [SnakePlayerSetting(name="player1", color_idx=0, init_size=init_snake_size, skin_idx=1, player_type="human", control_name="zqsd")]
    )

    #
    create_main_menu_scene(win)
    create_game_scene(win)
    create_end_menu(win)
    create_game_setup_scene(win)
    create_pause_menu(win)
    create_training_menu_scene(win)

    #
    # win.set_fullscreen(2)

    #
    app.run()
