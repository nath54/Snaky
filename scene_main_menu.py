

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color
from lib_nadisplay_rects import ND_Point, ND_Rect, ND_Position_Margins, ND_Position_Constraints

import lib_nadisplay as nd

import math
import random
import time

from lib_snake import SnakePlayerSetting, Snake, SnakeBot, SnakeBot_Version1, SnakeBot_Version2, SnakeBot_PerfectButSlowAndBoring, create_map1, snake_skin_1, snake_skin_2


#
controls_names_to_keys: dict[str, tuple[str, str, str, str]] = {
    "fleches": ("keydown_up arrow", "keydown_left arrow", "keydown_down arrow", "keydown_right arrow"),
    "zqsd": ("keydown_z", "keydown_q", "keydown_s", "keydown_d"),
    "tfgh": ("keydown_t", "keydown_f", "keydown_g", "keydown_h"),
    "ijkl": ("keydown_i", "keydown_j", "keydown_k", "keydown_l")
}

#
colors_idx_to_colors: dict[int, ND_Color] = {
    0: ND_Color(255, 255, 255),
    1: ND_Color(255, 0, 0),
    2: ND_Color(0, 255, 0),
    3: ND_Color(0, 0, 255),
    4: ND_Color(255, 255, 0),
    5: ND_Color(255, 0, 255),
    6: ND_Color(0, 255, 255),
    7: cl("orange"),
    8: cl("purple")
}

#
def event_set_snake_direction(main_app: nd.ND_MainApp, direction: ND_Point, snake_idx: int) -> None:
    #
    snakes: Optional[dict[int, Snake]] = main_app.global_vars_get_optional("snakes")

    #
    if snakes is None:
        return

    #
    if snake_idx not in snakes:
        return

    #
    if snakes[snake_idx].last_applied_direction != -direction:
        snakes[snake_idx].direction = direction

#
def animate_main_menu(main_app: nd.ND_MainApp, delta_time: float) -> None:
    #
    game_title: Optional[nd.ND_Text] = main_app.global_vars_get_optional("main_menu_title")
    t: float = main_app.get_time_msec()
    #
    if game_title is not None:
        #
        game_title.font_color.r = int(((math.sin(0.0002 * t ) + 1) / 2 ) * 255)
        game_title.font_color.g = int(((math.sin(0.002 * t + 0.023 * (t ** 0.1)) + 1) / 2 ) * 255)
        game_title.font_color.b = int(((math.sin(0.0004 * t - 0.0121 * (t ** 0.1)) + 1) / 2 ) * 255)
        #
        game_title.text = "Snaky" + "." * ( round(((math.sin(0.00002 * t ) + 1) / 2 ) * 255) % 4)
    #
    if False and main_app.display is not None:
        #
        game_window: Optional[nd.ND_Window] = None
        for win in main_app.display.windows.values():
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
def center_game_camera(main_app: nd.ND_MainApp) -> None:

    #
    map_mode: str = main_app.global_vars_get_default("map_mode", "together")
    cam_mode: str = main_app.global_vars_get_default("cam_mode", "fixed")
    cam_grid: nd.ND_CameraGrid = main_app.global_vars_get("cam_grid")

    maps_areas: Optional[list[nd.ND_Rect]] = main_app.global_vars_get_optional("maps_areas")
    #
    if not maps_areas:
        return

    #
    if cam_mode == "fixed":

        #
        if map_mode == "together":

            #
            rect_area = maps_areas[0]

            # center camera on grid area
            cam_grid.move_camera_to_grid_area(
                nd.ND_Rect(rect_area.x+1, rect_area.y+1, rect_area.w-1, rect_area.h-1)
            )

        #
        else:

            min_x: int = maps_areas[0].x
            min_y: int = maps_areas[0].y
            max_x: int = maps_areas[0].x + maps_areas[0].w
            max_y: int = maps_areas[0].y + maps_areas[0].h

            #
            marea: ND_Rect
            for marea in maps_areas:
                if marea.x < min_x:
                    min_x = marea.x
                if marea.y < min_y:
                    min_y = marea.y
                if marea.x + marea.w > max_x:
                    max_x = marea.x + marea.w
                if marea.y + marea.h > max_y:
                    max_y = marea.y + marea.h

            #
            to_rect: ND_Rect = ND_Rect(min_x + 1, min_y + 1, (max_x - min_x) - 1, (max_y - min_y) - 1)

            #
            cam_grid.move_camera_to_grid_area(to_rect)

    #
    elif cam_mode == "follow_player":

        # TODO
        pass

    #
    elif cam_mode == "follow_players":

        # TODO
        pass

    # TODO
    pass

#
def on_bt_play_clicked(win: nd.ND_Window) -> None:
    #
    win.set_state("game_setup")

#
def init_really_game(win: nd.ND_Window) -> None:

    # Cleaning and initialisation
    win.main_app.global_vars_set("snakes", {})
    win.main_app.global_vars_set("dead_snakes", {})
    win.main_app.global_vars_set("game_pause", 0.0)
    win.main_app.global_vars_set("game_debut_pause", 0.0)
    win.main_app.global_vars_set("apples_positions", [])

    #
    """
    List of game modes:

        - together: All the snakes in the same map
        - separate far: All the snakes have their own map, far away each others
        - separate close: All the snakes have their own map, but they can see each others maps
    """

    map_mode: str = win.main_app.global_vars_get_default("map_mode", "together")  # "together", "separate_far", "separate_close"
    terrain_w: int = win.main_app.global_vars_get_default("terrain_w", 29)
    terrain_h: int = win.main_app.global_vars_get_default("terrain_h", 29)
    snakes_speed: float = win.main_app.global_vars_get_default("snakes_speed", 0.1) # Time between each snakes update
    init_snake_size: int = win.main_app.global_vars_get_default("init_snake_size", 0)  #
    apples_multiple_values: bool = win.main_app.global_vars_get_default("apples_multiple_values", True)

    # Getting Settings
    a: list[SnakePlayerSetting] = win.main_app.global_vars_get("init_snakes")
    #
    init_snakes: list[SnakePlayerSetting] = \
        a if a is not None else [
            SnakePlayerSetting(name="humain1", color_idx=0, init_size=init_snake_size, skin_idx=0, player_type="human", control_name="zqsd"),
            SnakePlayerSetting(name="humain2", color_idx=1, init_size=init_snake_size, skin_idx=0, player_type="human", control_name="fleches"),
            SnakePlayerSetting(name="humain3", color_idx=2, init_size=init_snake_size, skin_idx=0, player_type="human", control_name="ijkk")
        ]
    #
    nb_init_apples: int = win.main_app.global_vars_get_default("nb_init_apples", 3)
    #
    grid: nd.ND_RectGrid = win.main_app.global_vars_get("grid")
    bg_grid: nd.ND_RectGrid = win.main_app.global_vars_get("bg_grid")
    game_infos_container: nd.ND_Container = win.main_app.global_vars_get("game_infos_container")

    # On nettoie les scorebox des anciennes parties
    trash: list[Optional[nd.ND_Container]] = cast(list[Optional[nd.ND_Container]], game_infos_container.elements)
    game_infos_container.elements = []
    game_infos_container.elements_by_id = {}
    i: int
    sb: Optional[nd.ND_Container]
    for (i, sb) in enumerate(trash):
        del sb
        trash[i] = None
    del trash

    # On nettoie la grille
    grid.clean()
    bg_grid.clean()

    # New Game

    # Init grid

    #
    init_snake_positions: list[ND_Point]
    maps_areas: list[nd.ND_Rect]
    maps_areas, init_snake_positions = create_map1(win, terrain_w, terrain_h, map_mode, len(init_snakes))

    win.main_app.global_vars_set("maps_areas", maps_areas)


    # Food
    food_1_elt_name: str = win.main_app.global_vars_get("food_1_elt_name")
    food_2_elt_name: str = win.main_app.global_vars_get("food_2_elt_name")
    food_3_elt_name: str = win.main_app.global_vars_get("food_3_elt_name")
    #
    food_1_elt: nd.ND_Elt = win.main_app.global_vars_get(food_1_elt_name)
    food_2_elt: nd.ND_Elt = win.main_app.global_vars_get(food_2_elt_name)
    food_3_elt: nd.ND_Elt = win.main_app.global_vars_get(food_3_elt_name)

    #
    food_1_grid_id: int = grid.add_element_to_grid(food_1_elt, [])
    food_2_grid_id: int = grid.add_element_to_grid(food_2_elt, [])
    food_3_grid_id: int = grid.add_element_to_grid(food_3_elt, [])

    #
    win.main_app.global_vars_set("food_1_grid_id", food_1_grid_id)
    win.main_app.global_vars_set("food_2_grid_id", food_2_grid_id)
    win.main_app.global_vars_set("food_3_grid_id", food_3_grid_id)


    #
    snk_idx: int
    snk: SnakePlayerSetting
    for (snk_idx, snk) in enumerate(init_snakes):

        #
        snk_color: ND_Color = colors_idx_to_colors[snk.color_idx]

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
        snake_icon.transformations = nd.ND_Transformations(color_modulation=snk_color)
        #
        snake_name: nd.ND_Text = nd.ND_Text(window=win,
                                            elt_id=f"snake_{snk_idx}_scorebox_name",
                                            position=nd.ND_Position_Container("50%", "100%", container=scorebox_row, position_margins=ND_Position_Margins(margin_left=15, margin_right=15)),
                                            text=snk.name,
                                            font_size=28,
                                            font_color=snk_color,
                                            text_h_align="left")
        #
        snake_score: nd.ND_Text = nd.ND_Text(window=win,
                                            elt_id=f"snake_{snk_idx}_scorebox_score",
                                            position=nd.ND_Position_Container("20%", "100%", container=scorebox_row),
                                            text="0",
                                            font_size=28,
                                            font_color=snk_color,
                                            text_h_align="left")
        #
        scorebox_row.add_element(snake_icon)
        scorebox_row.add_element(snake_name)
        scorebox_row.add_element(snake_score)
        #
        game_infos_container.add_element(scorebox_row)

        # Create Snake
        init_pos: ND_Point = init_snake_positions[snk_idx]
        map_area: nd.ND_Rect = maps_areas[0] if map_mode == "together" else maps_areas[snk_idx]
        snake: Snake = Snake( pseudo=snk.name, init_position=init_pos, color=snk_color, init_size=snk.init_size, score_elt=snake_score, map_area=map_area, speed=snakes_speed )
        snake.last_update = time.time()

        #
        win.main_app.global_vars_dict_set("snakes", snk_idx, snake)

        #
        if snk.skin_idx == 1:
            #
            snake_skin_1(win, snake, snk_idx, grid)
        #
        elif snk.skin_idx == 2:
            #
            snake_skin_2(win, snake, snk_idx, grid)

        #
        dir_angle: int = min(0, snake.direction.x) * 180 + 90 * snake.direction.y

        #
        snake.cases.append((init_pos))
        snake.cases_angles.append(dir_angle)
        grid.add_element_position(snake.sprites["head"][1], init_pos)
        grid.set_transformations_to_position(init_pos, nd.ND_Transformations(rotation=dir_angle))
        #
        pos_tail: ND_Point = init_pos - snake.direction
        #
        snake.cases.append(pos_tail)
        snake.cases_angles.append(dir_angle)
        grid.add_element_position(snake.sprites["tail"][1], pos_tail)
        grid.set_transformations_to_position(pos_tail, nd.ND_Transformations(rotation=dir_angle))

        #
        if snk.player_type == "human" and snk.control_name in controls_names_to_keys:
            #
            control_keys: tuple[str, str, str, str] = controls_names_to_keys[snk.control_name]
            #
            win.main_app.add_function_to_event_fns_queue(control_keys[0],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(0, -1), snk_idx))
            #
            win.main_app.add_function_to_event_fns_queue(control_keys[1],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(-1, 0), snk_idx))
            #
            win.main_app.add_function_to_event_fns_queue(control_keys[2],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(0, 1), snk_idx))
            #
            win.main_app.add_function_to_event_fns_queue(control_keys[3],
                lambda main_app, snk_idx=snk_idx: event_set_snake_direction(main_app, ND_Point(1, 0), snk_idx))

        # TODO: bots
        elif snk.player_type == "bot":
            # snake.bot = SnakeBot_PerfectButSlowAndBoring(main_app=win.main_app)
            snake.bot = SnakeBot_Version2(main_app=win.main_app)
            #
            # print(f"DEBUG  | Bot name : {snake.bot.name}")


    # Init Food
    rect_area: nd.ND_Rect
    for rect_area in maps_areas:
        p: Optional[ND_Point]
        for _ in range(nb_init_apples):
            #
            p = grid.get_empty_case_in_range(rect_area.x, rect_area.x + rect_area.w, rect_area.y, rect_area.y + rect_area.h)
            #
            if p is not None:
                #
                food_grid_id: int = food_1_grid_id
                #
                if apples_multiple_values:
                    food_grid_id = random.choice([food_1_grid_id, food_2_grid_id, food_3_grid_id])
                #
                grid.add_element_position(food_grid_id, p)
                #
                win.main_app.global_vars_list_append("apples_positions", p)

    #
    center_game_camera(win.main_app)

    # Setting New State
    win.set_state("game")

#
def on_bt_click_init_game(win: nd.ND_Window) -> None:

    #
    win.main_app.global_vars_set("game_mode", "standard_game")
    win.main_app.global_vars_set("apples_multiple_values", True)

    #
    init_snake_size: int = win.main_app.global_vars_get_default("game_init_snake_size", 0)
    win.main_app.global_vars_set("init_snakes", win.main_app.global_vars_get_default("game_init_snakes", [SnakePlayerSetting(name="player1", color_idx=0, init_size=init_snake_size, skin_idx=1, player_type="human", control_name="zqsd")]))
    win.main_app.global_vars_set("nb_init_apples", win.main_app.global_vars_get_default("game_nb_init_apples", 3))
    win.main_app.global_vars_set("init_snake_size", init_snake_size)
    win.main_app.global_vars_set("map_mode", win.main_app.global_vars_get_default("game_map_mode", "together"))
    win.main_app.global_vars_set("terrain_w", win.main_app.global_vars_get_default("game_terrain_w", 29))
    win.main_app.global_vars_set("terrain_h", win.main_app.global_vars_get_default("game_terrain_h", 29))
    win.main_app.global_vars_set("snakes_speed", win.main_app.global_vars_get_default("game_snakes_speed", 0.1))

    #
    init_really_game(win)

#
def on_bt_click_quit(win: nd.ND_Window) -> None:
    #
    win.main_app.quit()

#
def on_bt_click_training_bots(win: nd.ND_Window) -> None:
    #
    win.set_state("training_menu")

#
def create_main_menu_scene(win: nd.ND_Window) -> None:
    #
    main_menu_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="main_menu",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="main_menu"
    )

    #
    main_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )

    #
    bottom_row_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bottom_row_container",
        position=nd.ND_Position_Container(w="100%", h="75%", container=main_menu_container),
        element_alignment="row"
    )

    #
    bts_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bts_container",
        position=nd.ND_Position_Container(w="30%", h="100%", container=bottom_row_container),
        element_alignment="col"
    )

    #
    game_title: nd.ND_Text = nd.ND_Text(
                            window=win,
                            elt_id="game_title",
                            position=nd.ND_Position_Container(w="100%", h="20%", container=main_menu_container, position_margins=ND_Position_Margins(margin_top=25, margin_bottom=25)),
                            text="Snaky",
                            font_size=50,
                            font_color=cl("violet"),
    )

    #
    win.main_app.global_vars_set("main_menu_title", game_title)
    win.main_app.add_function_to_mainloop_fns_queue("physics", animate_main_menu)

    #
    bt_play: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_play",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_play_clicked,
        text="Play !",
        font_size=35
    )
    #
    bt_train: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_train",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_training_bots,
        text="Train Bots",
        font_size=35
    )
    #
    bt_settings: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_settings",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=None,
        text="Settings",
        font_size=35
    )
    #
    bt_quit: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_quit",
        position=nd.ND_Position_Container(w=250, h=100, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_quit,
        text="Quit",
        font_size=35
    )

    #
    bts_container.add_element(bt_play)
    bts_container.add_element(bt_train)
    bts_container.add_element(bt_settings)
    bts_container.add_element(bt_quit)

    #
    main_menu_container.add_element(game_title)
    main_menu_container.add_element(bottom_row_container)
    #
    bottom_row_container.add_element(bts_container)

    #
    main_menu_scene.add_element(0, main_menu_container)

    #
    win.add_scene( main_menu_scene )
