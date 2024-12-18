

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins, ND_Position

import lib_nadisplay as nd

from lib_snake import Snake

from scene_main_menu import center_game_camera
from scene_bots_training_menu import at_traning_epoch_end

import random
import time


#
def on_pause_pressed(main_app: nd.ND_MainApp) -> None:
    #
    if main_app.display is None:
        return
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
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
def put_new_apple_on_grid(main_app: nd.ND_MainApp, grid: nd.ND_RectGrid, food_1_grid_id: int, food_2_grid_id: int, food_3_grid_id: int, rect_area: nd.ND_Rect) -> None:
    #
    apples_multiple_values: bool = main_app.global_vars_get_default("apples_multiple_values", True)
    #
    p: Optional[ND_Point] = grid.get_empty_case_in_range(rect_area.x, rect_area.x + rect_area.w, rect_area.y, rect_area.y + rect_area.h)
    #
    if p is not None:
        #
        food_grid_id: int = food_1_grid_id
        #
        if apples_multiple_values:
            food_grid_id = random.choice([food_1_grid_id, food_2_grid_id, food_3_grid_id])
        #
        grid.set_transformations_to_position(p, ND_Transformations())
        grid.add_element_position(food_grid_id, p)
        #
        main_app.global_vars_list_append("apples_positions", p)

#
def update_physic(main_app: nd.ND_MainApp, delta_time: float) -> None:
    #
    if main_app.display is None:
        return
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    win: Optional[nd.ND_Window] = main_app.display.windows[MAIN_WINDOW_ID]
    #
    if win is None or win.state != "game":
        return

    #
    grid: nd.ND_RectGrid = main_app.global_vars_get("grid")
    snakes: Optional[dict[int, Snake]] = main_app.global_vars_get_optional("snakes")
    dead_snakes: Optional[dict[int, Snake]] = main_app.global_vars_get_optional("dead_snakes")
    wall_grid_id: Optional[int] = main_app.global_vars_get_optional("wall_grid_id")
    food_1_grid_id: Optional[int] = main_app.global_vars_get_optional("food_1_grid_id")
    food_2_grid_id: Optional[int] = main_app.global_vars_get_optional("food_2_grid_id")
    food_3_grid_id: Optional[int] = main_app.global_vars_get_optional("food_3_grid_id")

    #
    if snakes is None or dead_snakes is None or\
       wall_grid_id is None or\
       food_1_grid_id is None or food_2_grid_id is None or food_3_grid_id is None:
        return

    #
    now: float = time.time()

    #
    game_pause: float = cast(float, win.main_app.global_vars_get("game_pause"))
    win.main_app.global_vars_set("game_pause", 0)

    #
    snak: Snake
    for snak in snakes.values():
        #
        snak.last_update += game_pause

    #
    snaks_to_die: list[int] = []

    #
    updates: bool = True
    #
    while updates:
        #
        updates=False
        #
        snak_items = list(snakes.items())
        #
        for snak_idx, snak in snak_items:
            #
            if snak.dead:
                continue
            #
            if now - snak.last_update < snak.speed:
                continue

            #
            updates = True
            #
            snak.last_update += snak.speed
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

                    #
                    win.main_app.global_vars_list_remove("apples_positions", nhp)

                    # On rajoute une nouvelle pomme
                    put_new_apple_on_grid(win.main_app, grid, food_1_grid_id, food_2_grid_id, food_3_grid_id, snak.map_area)

                else:

                    # COLLISION : Le serpent meurt, on remplace son corps par des murs
                    pos: nd.ND_Point
                    for pos in snak.cases:
                        grid.remove_at_position(pos)
                        grid.add_element_position(wall_grid_id, pos)

                    #
                    snak.dead = True

                    #
                    if snak.bot is not None:
                        snak.bot.add_to_score(snak.score)

                    #
                    snaks_to_die.append(snak_idx)

                    #
                    continue

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
            if snak.bot is not None:
                #
                new_dir: Optional[ND_Point] = snak.bot.predict_next_direction(snake=snak, grid=grid, main_app=main_app)
                #
                if new_dir is not None:
                    snak.direction = new_dir

        #
        if snaks_to_die:
            #
            for snak_idx in snaks_to_die:
                #
                if snak_idx in snakes:
                    #
                    dead_snakes[snak_idx] = snakes[snak_idx]
                    del snakes[snak_idx]

            #
            snaks_to_die = []

            #
            if not snakes:  # Plus de serpents en vie => Partie finie
                #
                updates = False
                #
                break

    # Game end
    if not snakes:
        #
        gtype: str = win.main_app.global_vars_get("game_type")
        #
        if gtype == "standard_game":
            win.state = "end_menu"
        elif gtype == "training_bots":
            at_traning_epoch_end(win)


#
def create_game_scene(win: nd.ND_Window) -> None:
    #
    game_scene: nd.ND_Scene = nd.ND_Scene(
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
    win.main_app.add_function_to_event_fns_queue("window_resized", center_game_camera)

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
        clicked_bg_color = cl((28, 0, 18)),
        mouse_active=False
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
    game_scene.add_element(0, game_row_container)

    #
    coin_atlas: nd.ND_AtlasTexture = nd.ND_AtlasTexture(
        window=win,
        texture_atlas_path="res/sprites/coin_grayscale.png",
        tiles_size=ND_Point(31, 31)
    )
    coin_3: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="spinning coin 3",
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
        elt_id="spinning coin 2",
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
        elt_id="spinning coin 1",
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
    win.main_app.global_vars_set("coin_3_elt", coin_3)
    win.main_app.global_vars_set("coin_2_elt", coin_2)
    win.main_app.global_vars_set("coin_1_elt", coin_1)


    apples_atlas: nd.ND_AtlasTexture = nd.ND_AtlasTexture(
        window=win,
        texture_atlas_path="res/sprites/apples.png",
        tiles_size=ND_Point(32, 32)
    )
    apples_silver_atlas: nd.ND_AtlasTexture = nd.ND_AtlasTexture(
        window=win,
        texture_atlas_path="res/sprites/apples_silver.png",
        tiles_size=ND_Point(32, 32)
    )
    #
    apple_3: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="floating apple 3",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "floating": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"floating_appele_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=apples_silver_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(6)
            ]
        },
        animations_speed={},
        default_animation_speed=0.15,
        default_animation="floating"
    )
    apple_2: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="floating apple 2",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "floating": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"floating_appele_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=apples_silver_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(6)
            ]
        },
        animations_speed={},
        default_animation_speed=0.15,
        default_animation="floating"
    )
    apple_1: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="floating apple 1",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "floating": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"floating_appele_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=apples_silver_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(6)
            ]
        },
        animations_speed={},
        default_animation_speed=0.15,
        default_animation="floating"
    )
    apple_base: nd.ND_AnimatedSprite = nd.ND_AnimatedSprite(
        window=win,
        elt_id="floating apple 1",
        position=nd.ND_Position_RectGrid(rect_grid=grid),
        animations={
            "floating": [
                nd.ND_Sprite_of_AtlasTexture(
                    window=win,
                    elt_id=f"floating_appele_anim_{i}",
                    position=ND_Position(),
                    atlas_texture=apples_atlas,
                    tile_x=i, tile_y=0
                )

                for i in range(6)
            ]
        },
        animations_speed={},
        default_animation_speed=0.15,
        default_animation="floating"
    )
    #
    apple_1.transformations = ND_Transformations(color_modulation=cl("red"))
    apple_2.transformations = ND_Transformations(color_modulation=cl("silver"))
    apple_3.transformations = ND_Transformations(color_modulation=cl("gold web golden"))

    #
    win.main_app.global_vars_set("apple_3_elt", apple_3)
    win.main_app.global_vars_set("apple_2_elt", apple_2)
    win.main_app.global_vars_set("apple_1_elt", apple_base)

    #
    win.main_app.global_vars_set("food_3_elt_name", "apple_3_elt")
    win.main_app.global_vars_set("food_2_elt_name", "apple_2_elt")
    win.main_app.global_vars_set("food_1_elt_name", "apple_1_elt")

    #
    win.main_app.add_function_to_event_fns_queue("keydown_p", on_pause_pressed)
    win.main_app.add_function_to_event_fns_queue("keydown_escape", on_pause_pressed)

    #
    win.main_app.add_function_to_mainloop_fns_queue("physics", update_physic)

    #
    win.add_scene( game_scene )
