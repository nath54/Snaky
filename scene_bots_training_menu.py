

from typing import Optional, cast

import random
import os

import numpy as np

from lib_nadisplay_rects import ND_Point, ND_Position_Margins

import lib_nadisplay as nd

from lib_snake import Snake, SnakePlayerSetting, SnakeBot_Version1, SnakeBot_Version2, create_bot_from_bot_dict

from scene_main_menu import init_really_game, colors_idx_to_colors, snake_base_types, map_modes


#
def on_bt_black_to_menu_clicked(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    new_options: set[str] = set(snake_base_types + list(win.main_app.global_vars_get("bots").keys()))
    #
    n: int = win.main_app.global_vars_list_length("game_init_snakes")
    #
    for i in range(n):
        #
        row_elt_id: str = f"player_row_{i}"
        #
        sel_opt: nd.ND_SelectOptions = cast(nd.ND_SelectOptions, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", f"{row_elt_id}_player_type"))
        #
        if i > 0 or sel_opt.options != new_options:
            sel_opt.update_options(new_options)
        else:  # Ils sont sensé avoir tous les mêmes options, donc s'il y en a un qui est à jour, on est bon, pas besoin de tous les voir
            break
    #
    win.set_state("main_menu")

#
def new_genes_from_bot_dict(bots: dict[str, dict], bot_dict: dict, main_app: nd.ND_MainApp) -> str:
    #
    learning_step: float = 0.01
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    learning_step_opt: Optional[float] = cast(Optional[float], main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_learning_step"))
    if learning_step_opt is not None:
        learning_step = learning_step_opt
    #
    if bot_dict["type"] == "bot_v1":
        #
        bot1: SnakeBot_Version1 = cast(SnakeBot_Version1, create_bot_from_bot_dict(bot_dict=bot_dict, main_app=main_app, ignore_food_grid_id=True))
        #
        new_bot1: SnakeBot_Version1 = SnakeBot_Version1(main_app=main_app, security=bot1.security, radius=bot1.radius, nb_apples_to_context=bot1.nb_apples_to_include, random_weights=bot1.random_weights, ignore_food_grid_id=True)
        #
        w_shape: tuple[int, int] = bot1.weigths.shape
        #
        delta: np.ndarray = np.random.normal(loc=0.0, scale=learning_step, size=w_shape).astype(bot1.dtype)
        #
        new_bot1.weigths = bot1.weigths + delta
        #
        new_bot1.set_name( new_bot1.create_name() )
        #
        while new_bot1.name in bots:
            new_bot1.set_name( new_bot1.create_name() )
        #
        new_bot1.save_bot()
        #
        return new_bot1.name

    #
    elif bot_dict["type"] == "bot_v2":
        #
        bot2: SnakeBot_Version2 = cast(SnakeBot_Version2, create_bot_from_bot_dict(bot_dict=bot_dict, main_app=main_app, ignore_food_grid_id=True))
        #
        new_bot2: SnakeBot_Version2 = SnakeBot_Version2(main_app=main_app, security=bot2.security, radius=bot2.radius, nb_apples_to_context=bot2.nb_apples_to_include, random_weights=bot2.random_weights, ignore_food_grid_id=True)
        #
        w1_shape: tuple[int, int] = bot2.weigths_1.shape
        w2_shape: tuple[int, int] = bot2.weigths_2.shape
        #
        delta1: np.ndarray = np.random.normal(loc=0.0, scale=learning_step, size=w1_shape).astype(bot2.dtype)
        delta2: np.ndarray = np.random.normal(loc=0.0, scale=learning_step, size=w2_shape).astype(bot2.dtype)
        #
        new_bot2.weigths_1 = bot2.weigths_1 + delta1
        new_bot2.weigths_2 = bot2.weigths_2 + delta2
        #
        new_bot2.set_name( new_bot2.create_name() )
        #
        while new_bot2.name in bots:
            new_bot2.set_name( new_bot2.create_name() )
        #
        new_bot2.save_bot()
        #
        return new_bot2.name
    #
    new_bot_version: Optional[str] = cast(Optional[str], main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_new_bots_version"))
    if new_bot_version is None:
        #
        return "new_bot_v1"
    #
    return new_bot_version

#
def new_genes_from_fusion_of_two_bot_dict(bots: dict[str, dict], bot1_dict: dict, bot2_dict: dict, main_app: nd.ND_MainApp) -> str:
    #
    fusion_factor: float = random.uniform(0.05, 0.95)
    #
    if bot1_dict["type"] == "bot_v1":
        #
        bot1_a: SnakeBot_Version1 = cast(SnakeBot_Version1, create_bot_from_bot_dict(bot_dict=bot1_dict, main_app=main_app, ignore_food_grid_id=True))
        bot1_b: SnakeBot_Version1 = cast(SnakeBot_Version1, create_bot_from_bot_dict(bot_dict=bot2_dict, main_app=main_app, ignore_food_grid_id=True))
        #
        new_bot1: SnakeBot_Version1 = SnakeBot_Version1(main_app=main_app, security=bot1_a.security, radius=bot1_a.radius, nb_apples_to_context=bot1_a.nb_apples_to_include, random_weights=bot1_a.random_weights, ignore_food_grid_id=True)
        #
        new_bot1.weigths = bot1_a.weigths * fusion_factor + bot1_b.weigths * (1.0 - fusion_factor)
        #
        new_bot1.set_name( new_bot1.create_name() )
        #
        while new_bot1.name in bots:
            new_bot1.set_name( new_bot1.create_name() )
        #
        new_bot1.save_bot()
        #
        return new_bot1.name

    #
    elif bot1_dict["type"] == "bot_v2":
        #
        bot2_a: SnakeBot_Version2 = cast(SnakeBot_Version2, create_bot_from_bot_dict(bot_dict=bot1_dict, main_app=main_app, ignore_food_grid_id=True))
        bot2_b: SnakeBot_Version2 = cast(SnakeBot_Version2, create_bot_from_bot_dict(bot_dict=bot2_dict, main_app=main_app, ignore_food_grid_id=True))
        #
        new_bot2: SnakeBot_Version2 = SnakeBot_Version2(main_app=main_app, security=bot2_a.security, radius=bot2_a.radius, nb_apples_to_context=bot2_a.nb_apples_to_include, random_weights=bot2_a.random_weights, ignore_food_grid_id=True)
        #
        new_bot2.weigths_1 = bot2_a.weigths_1 * fusion_factor + bot2_b.weigths_1 * (1.0 - fusion_factor)
        new_bot2.weigths_2 = bot2_a.weigths_2 * fusion_factor + bot2_b.weigths_2 * (1.0 - fusion_factor)
        #
        new_bot2.set_name( new_bot2.create_name() )
        #
        while new_bot2.name in bots:
            new_bot2.set_name( new_bot2.create_name() )
        #
        new_bot2.save_bot()
        #
        return new_bot2.name
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    new_bot_version: Optional[str] = cast(Optional[str], main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_new_bots_version"))
    if new_bot_version is None:
        #
        return "new_bot_v1"
    #
    return new_bot_version

#
def are_two_bots_dict_compatible(bot1_dict: dict, bot2_dict: dict) -> bool:
    #
    if bot1_dict["type"] != bot2_dict["type"]:
        return False
    #
    if bot1_dict["type"] == "bot_v1" or bot1_dict == "bot_b2":
        #
        if bot1_dict["radius"] != bot2_dict["radius"]:
            return False
        #
        if bot1_dict["random_weights"] != bot2_dict["random_weights"]:
            return False
        #
        if bot1_dict["nb_apples"] != bot2_dict["nb_apples"]:
            return False
    #
    return True

#
def reproduce_bots_v2(bots: dict[str, dict], bots_to_reproduce: list[str], main_app: nd.ND_MainApp) -> str:
    #
    nb_possibilities: int = 1
    #
    if len(bots_to_reproduce) >= 2:
        nb_possibilities += 1
    #
    a = random.randint(1, nb_possibilities)
    #
    if a == 1:  # On prend un serpent et on modifie un peu ses paramètres
        #
        bot_name: str = random.choice(bots_to_reproduce)
        bot_dict: dict = bots[bot_name]
        #
        return new_genes_from_bot_dict(bots, bot_dict, main_app)
    #
    else:       # On prend deux serpents et on les fusionne entre eux
        #
        bot1_name: str = random.choice(bots_to_reproduce)
        bot1_dict: dict = bots[bot1_name]
        #
        bot2_name: str = random.choice(bots_to_reproduce)
        bot2_dict: dict = bots[bot2_name]
        #
        if bot1_name == bot2_name or not are_two_bots_dict_compatible(bot1_dict, bot2_dict):
            #
            return new_genes_from_bot_dict(bots, bot1_dict, main_app)
        #
        return new_genes_from_fusion_of_two_bot_dict(bots, bot1_dict, bot2_dict, main_app)

    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    new_bot_version: Optional[str] = cast(Optional[str], main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_new_bots_version"))
    if new_bot_version is None:
        #
        return "new_bot_v1"
    #
    return new_bot_version

#
def really_init_training_mode(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")

    #
    nb_bots: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_nb_bots"))
    min_random_bots_per_epoch: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_random_bots_per_epoch"))
    min_score_to_reproduce: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_score_to_reproduce"))


    #
    init_snakes: list[SnakePlayerSetting] = [
        SnakePlayerSetting(name=f"bot {i}", color_idx=i%len(colors_idx_to_colors), init_size=win.main_app.global_vars_get("init_snake_size"), skin_idx=1, player_type="new_bot_v1", control_name="fleches")
        for i in range(min(nb_bots, min_random_bots_per_epoch))
    ]

    #
    bots: dict[str, dict] = win.main_app.global_vars_get("bots")
    #
    bots_to_reproduce: list[str] = []
    #
    for bot_name in bots:
        #
        if bots[bot_name]["max_score"] >= min_score_to_reproduce:  # C'est ici qu'on fait de l'eugénisme !
            bots_to_reproduce.append(bot_name)

    #
    new_bot_version: str = "new_bot_v1"
    new_bot_version_opt: Optional[str] = cast(Optional[str], win.main_app.get_element_value(win.window_id, "training_menu", "input_new_bots_version"))
    if new_bot_version_opt is not None:
        #
        new_bot_version = new_bot_version_opt
    #
    for i in range(len(init_snakes), nb_bots):
        #
        if bots_to_reproduce:
            init_snakes.append( SnakePlayerSetting(name=f"bot {i}", color_idx=i%len(colors_idx_to_colors), init_size=win.main_app.global_vars_get("init_snake_size"), skin_idx=1, player_type=reproduce_bots_v2(bots=bots, bots_to_reproduce=bots_to_reproduce, main_app=win.main_app), control_name="fleches") )
        #
        else:
            init_snakes.append( SnakePlayerSetting(name=f"bot {i}", color_idx=i%len(colors_idx_to_colors), init_size=win.main_app.global_vars_get("init_snake_size"), skin_idx=1, player_type=new_bot_version, control_name="fleches") )

    #
    win.main_app.global_vars_set("init_snakes", init_snakes)

    #
    init_really_game(win)

#
def get_best_bots_score(main_app: nd.ND_MainApp) -> int:
    #
    bots: dict[str, dict] = main_app.global_vars_get("bots")
    #
    max_score: int = 0
    #
    bot_dict: dict
    for bot_dict in bots.values():
        #
        if bot_dict["max_score"] > max_score:
            max_score = bot_dict["max_score"]
    #
    return max_score

#
def get_average_batch_bots_score(main_app: nd.ND_MainApp) -> float:
    #
    snakes: list[Snake] = list(main_app.global_vars_get("snakes").values()) + list(main_app.global_vars_get("dead_snakes").values())
    #
    sum_scores: float = 0
    #
    snake: Snake
    for snake in snakes:
        #
        sum_scores += snake.score
    #
    if len(snakes) == 0:
        return 0
    #
    return sum_scores / float(len(snakes))

#
def on_bt_training_click(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    win.main_app.global_vars_set("snakes_speed", 0.002)
    win.main_app.global_vars_set("game_mode", "training_bots")
    win.main_app.global_vars_set("apples_multiple_values", False)
    win.main_app.global_vars_set("init_snake_size", 0)

    #
    map_mode: str = cast(str, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_map_mode"))
    max_nb_steps: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_max_steps"))
    grid_size: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_grid_size"))
    nb_epochs: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_nb_epochs"))
    min_score_to_reproduce: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_score_to_reproduce"))

    #
    win.main_app.global_vars_set("map_mode", map_mode)
    win.main_app.global_vars_set("min_score_to_reproduce", min_score_to_reproduce)
    win.main_app.global_vars_set("max_nb_steps", max_nb_steps)
    win.main_app.global_vars_set("nb_steps", 0)
    win.main_app.global_vars_set("terrain_w", grid_size)
    win.main_app.global_vars_set("terrain_h", grid_size)
    win.main_app.global_vars_set("nb_epoch_tot", nb_epochs)
    win.main_app.global_vars_set("nb_epoch_cur", 1)

    #
    print(f"\nBegin Bots Training. (Current global max bot score:  {get_best_bots_score(main_app=win.main_app)}, nb_bots = {len(win.main_app.global_vars_get("bots"))})")

    #
    really_init_training_mode(win)

#
def continue_training_bots(win: nd.ND_Window) -> None:
    #
    win.main_app.global_vars_set("nb_steps", 0)
    #
    really_init_training_mode(win)

#
def at_traning_epoch_end(win: nd.ND_Window) -> None:
    #
    print(f"Training epoch {win.main_app.global_vars_get("nb_epoch_cur")} / {win.main_app.global_vars_get("nb_epoch_tot")}.  (Current max bot score:  {get_best_bots_score(main_app=win.main_app)}, nb_bots = {len(win.main_app.global_vars_get("bots"))})")
    print(f"  -> Batch done : (average_score = {get_average_batch_bots_score(win.main_app)})")
    #
    min_score_to_reproduce: int = cast(int, win.main_app.get_element_value(win.window_id, "training_menu", "input_min_score_to_reproduce"))
    #
    # Saving bots
    for snakes in list(win.main_app.global_vars_get("dead_snakes").values()) + list(win.main_app.global_vars_get("snakes").values()):
        #
        if snakes.score >= min_score_to_reproduce:
            #
            print(f"Saving bot : {snakes.bot.name} of score : {snakes.score} > {min_score_to_reproduce}")
            snakes.bot.add_to_score(snakes.score)
            snakes.bot.save_bot()
            #
        elif snakes.bot.max_score < min_score_to_reproduce:
            #
            snakes.bot.delete_all_data()

    #
    if win.main_app.global_vars_get("nb_epoch_cur") >= win.main_app.global_vars_get("nb_epoch_tot"):
        #
        # TODO: update display of new created bots
        #
        win.set_state("training_menu")
        #
        return
    #
    win.main_app.global_vars_set("nb_epoch_cur", win.main_app.global_vars_get("nb_epoch_cur")+1)
    #
    continue_training_bots(win)

#
def on_bt_del_bad_bots_clicked(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    min_score_to_reproduce: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_score_to_reproduce"))
    #
    print(f"\nDeleting all the bots that have a max score < to {min_score_to_reproduce}", end="")
    #
    bots: dict[str, dict] = win.main_app.global_vars_get("bots")
    #
    bots_to_remove: list[str] = []
    #
    snakes_bot_paths: str = win.main_app.global_vars_get("snakes_bot_paths")
    #
    bot_name: str
    bot_dict: dict
    for bot_dict in bots.values():
        #
        bot_name = bot_dict["name"]
        #
        if bot_dict["max_score"] < min_score_to_reproduce:
            #
            bots_to_remove.append( bot_name )
    #
    nb_bots_deleted: int = 0
    #
    for bot_name in bots_to_remove:
        #
        bot_dict = bots[bot_name]
        #
        if bot_dict["type"] == "bot_v1":
            if os.path.exists(bot_dict["weights_path"]+".npy"):
                os.remove(bot_dict["weights_path"]+".npy")
        elif bot_dict["type"] == "bot_v2":
            if os.path.exists(bot_dict["weights_path"]+"_1.npy"):
                os.remove(bot_dict["weights_path"]+"_1.npy")
            if os.path.exists(bot_dict["weights_path"]+"_2.npy"):
                os.remove(bot_dict["weights_path"]+"_2.npy")
        #
        if os.path.exists(snakes_bot_paths+bot_name+".json"):
            os.remove(snakes_bot_paths+bot_name+".json")
        #
        del bots[bot_name]
        #
        nb_bots_deleted += 1
        #
        print(".", end="")
    #
    print(f"\nDone. {nb_bots_deleted} bots deleted.\nThere are now {len(bots)} left.\n")

#
def create_training_menu_scene(win: nd.ND_Window) -> None:

    #
    margin_center: ND_Position_Margins = ND_Position_Margins(margin_left="50%", margin_right="50%", margin_top="50%", margin_bottom="50%")

    #
    training_menu_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="training_menu",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="training_menu"
    )

    #
    training_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="training_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )
    training_menu_scene.add_element(0, training_menu_container)

    # HEADER
    #
    header_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="header_row",
        position=nd.ND_Position_Container(w="100%", h="8%", container=training_menu_container),
        element_alignment="row"
    )
    training_menu_container.add_element(header_row)

    #

    #
    bt_back: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_back",
        position=nd.ND_Position_Container(w=150, h=40, container=header_row, position_margins=ND_Position_Margins(margin_left=15, margin_top="50%", margin_bottom="50%", margin_right=15)),
        onclick=on_bt_black_to_menu_clicked,
        text="back"
    )
    header_row.add_element(bt_back)

    #
    page_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="page_title",
        position=nd.ND_Position_Container(w=100, h="100%", container=header_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        text="Training bots"
    )
    header_row.add_element(page_title)


    # BODY
    #
    body_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="body_row",
        position=nd.ND_Position_Container(w="100%", h="92%", container=training_menu_container),
        element_alignment="row"
    )
    training_menu_container.add_element(body_row)

    ### LEFT COLUMN
    #
    left_col: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="left_col",
        position=nd.ND_Position_Container(w="50%", h="100%", container=body_row),
        element_alignment="col"
    )
    body_row.add_element(left_col)

    #
    bots_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="",
        position=nd.ND_Position_Container(w="100%", h=30, container=left_col, position_margins=margin_center),
        text="Bots"
    )
    left_col.add_element(bots_title)

    #
    bots_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bots_container",
        position=nd.ND_Position_Container(w="100%", h="70%", container=left_col, position_margins=margin_center),
        element_alignment="col"
    )
    left_col.add_element(bots_container)

    #
    bt_del_bad_bots: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_del_bad_bots",
        position=nd.ND_Position_Container(w=350, h=40, container=left_col, position_margins=margin_center),
        onclick=on_bt_del_bad_bots_clicked,
        text="Delete bad bots"
    )
    left_col.add_element(bt_del_bad_bots)

    #
    bt_start_training: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_start_training",
        position=nd.ND_Position_Container(w=350, h=40, container=left_col, position_margins=margin_center),
        onclick=on_bt_training_click,
        text="Start Training"
    )
    left_col.add_element(bt_start_training)

    ### RIGHT COLUMN
    #
    right_col: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="right_col",
        position=nd.ND_Position_Container(w="50%", h="auto", container=body_row, position_margins=nd.ND_Position_Margins(margin_top=50)),
        element_alignment="col",
        inverse_z_order=True
    )
    body_row.add_element(right_col)

    ##### MAP Mode
    row_map_mode: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_map_mode",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_map_mode)

    #
    text_map_mode: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_map_mode",
        position=nd.ND_Position_Container(w=320, h=40, container=row_map_mode),
        text="map mode : "
    )
    row_map_mode.add_element(text_map_mode)

    #
    input_map_mode: nd.ND_SelectOptions = nd.ND_SelectOptions(
        window=win,
        elt_id="input_map_mode",
        position=nd.ND_Position_Container(w=400, h=40, container=row_map_mode),
        value=win.main_app.global_vars_get_default("training_bots_map_mode", "separate_close"),
        options=map_modes,
        option_list_buttons_height=300,
        font_name="FreeSans"
    )
    row_map_mode.add_element(input_map_mode)


    ##### Min Score to reproduce
    row_min_score_to_reproduce: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_min_score_to_reproduce",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_min_score_to_reproduce)

    #
    text_min_score_to_reproduce: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_min_score_to_reproduce",
        position=nd.ND_Position_Container(w=320, h=40, container=row_min_score_to_reproduce),
        text="min score to reproduce : "
    )
    row_min_score_to_reproduce.add_element(text_min_score_to_reproduce)

    #
    input_min_score_to_reproduce: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_min_score_to_reproduce",
        position=nd.ND_Position_Container(w=400, h=40, container=row_min_score_to_reproduce),
        value=win.main_app.global_vars_get_default("training_bots_min_score_to_reproduce", 6),
        min_value=0,
        max_value=1000
    )
    row_min_score_to_reproduce.add_element(input_min_score_to_reproduce)


    ##### Max steps
    row_max_steps: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_max_steps",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_max_steps)

    #
    text_max_steps: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_max_steps",
        position=nd.ND_Position_Container(w=320, h=40, container=row_max_steps),
        text="max steps : "
    )
    row_max_steps.add_element(text_max_steps)

    #
    input_max_steps: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_max_steps",
        position=nd.ND_Position_Container(w=400, h=40, container=row_max_steps),
        value=win.main_app.global_vars_get_default("training_bots_max_steps", 300),
        min_value=50,
        max_value=10000
    )
    row_max_steps.add_element(input_max_steps)


    ##### Grid Size
    row_grid_size: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_grid_size",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_grid_size)

    #
    text_grid_size: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_grid_size",
        position=nd.ND_Position_Container(w=320, h=40, container=row_grid_size),
        text="grid size : "
    )
    row_grid_size.add_element(text_grid_size)

    #
    input_grid_size: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_grid_size",
        position=nd.ND_Position_Container(w=400, h=40, container=row_grid_size),
        value=win.main_app.global_vars_get_default("training_bots_grid_size", 11),
        min_value=5,
        max_value=100
    )
    row_grid_size.add_element(input_grid_size)


    ##### Nb bots
    row_nb_bots: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_nb_bots",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_nb_bots)

    #
    text_nb_bots: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_nb_bots",
        position=nd.ND_Position_Container(w=320, h=40, container=row_nb_bots),
        text="nb bots : "
    )
    row_nb_bots.add_element(text_nb_bots)

    #
    input_nb_bots: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_nb_bots",
        position=nd.ND_Position_Container(w=400, h=40, container=row_nb_bots),
        value=win.main_app.global_vars_get_default("training_bots_nb_bots", 9),
        min_value=1,
        max_value=100
    )
    row_nb_bots.add_element(input_nb_bots)

    ##### Nb Epochs
    row_nb_epochs: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_nb_epochs",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_nb_epochs)

    #
    text_nb_epochs: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_nb_epochs",
        position=nd.ND_Position_Container(w=320, h=40, container=row_nb_epochs),
        text="nb epochs : "
    )
    row_nb_epochs.add_element(text_nb_epochs)

    #
    input_nb_epochs: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_nb_epochs",
        position=nd.ND_Position_Container(w=400, h=40, container=row_nb_epochs),
        value=win.main_app.global_vars_get_default("training_bots_nb_epochs", 20),
        min_value=1,
        max_value=1000
    )
    row_nb_epochs.add_element(input_nb_epochs)

    ##### Min random bots per steps
    row_min_random_bots_per_epoch: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_min_random_bots_per_epoch",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_min_random_bots_per_epoch)

    #
    text_min_random_bots_per_epoch: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_min_random_bots_per_epoch",
        position=nd.ND_Position_Container(w=320, h=40, container=row_min_random_bots_per_epoch),
        text="min random bots per steps :"
    )
    row_min_random_bots_per_epoch.add_element(text_min_random_bots_per_epoch)

    #
    input_min_random_bots_per_epoch: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_min_random_bots_per_epoch",
        position=nd.ND_Position_Container(w=400, h=40, container=row_min_random_bots_per_epoch),
        value=win.main_app.global_vars_get_default("training_bots_min_random_bots_per_epoch", 4),
        min_value=0,
        max_value=100
    )
    row_min_random_bots_per_epoch.add_element(input_min_random_bots_per_epoch)


    ##### Learning Step
    row_learning_step: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_learning_step",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_learning_step)

    #
    text_learning_step: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_learning_step",
        position=nd.ND_Position_Container(w=320, h=40, container=row_learning_step),
        text="learning step :"
    )
    row_learning_step.add_element(text_learning_step)

    #
    input_learning_step: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_learning_step",
        position=nd.ND_Position_Container(w=400, h=40, container=row_learning_step),
        value=win.main_app.global_vars_get_default("training_bots_learning_step", 0.001),
        min_value=0,
        max_value=0.5,
        step=0.00001,
        digits_after_comma=4
    )
    row_learning_step.add_element(input_learning_step)


    ##### Snakes Speed
    row_snakes_speed: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_snakes_speed",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_snakes_speed)

    #
    text_snakes_speed: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_snakes_speed",
        position=nd.ND_Position_Container(w=320, h=40, container=row_snakes_speed),
        text="snakes speed :"
    )
    row_snakes_speed.add_element(text_snakes_speed)

    #
    input_snakes_speed: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_snakes_speed",
        position=nd.ND_Position_Container(w=400, h=40, container=row_snakes_speed),
        value=win.main_app.global_vars_get_default("training_bots_snakes_speed", 0.001),
        min_value=0,
        max_value=0.5,
        step=0.00001,
        digits_after_comma=6
    )
    row_snakes_speed.add_element(input_snakes_speed)


    ##### New Bots version
    row_new_bots_version: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_new_bots_version",
        position=nd.ND_Position_Container(w="100%", h=50, container=right_col),
        element_alignment="row"
    )
    right_col.add_element(row_new_bots_version)

    #
    text_new_bots_version: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_new_bots_version",
        position=nd.ND_Position_Container(w=320, h=40, container=row_new_bots_version),
        text="new bots version : "
    )
    row_new_bots_version.add_element(text_new_bots_version)

    #
    input_new_bots_version: nd.ND_SelectOptions = nd.ND_SelectOptions(
        window=win,
        elt_id="input_new_bots_version",
        position=nd.ND_Position_Container(w=400, h=40, container=row_new_bots_version),
        value=win.main_app.global_vars_get_default("training_bots_new_bots_version", "new_bot_v1"),
        options=set(["new_bot_v1", "new_bot_v2"]),
        option_list_buttons_height=300,
        font_name="FreeSans"
    )
    row_new_bots_version.add_element(input_new_bots_version)

    #
    win.add_scene( training_menu_scene )

