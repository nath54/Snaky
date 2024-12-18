

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins, ND_Position, ND_Position_Constraints

import lib_nadisplay as nd

from lib_snake import SnakePlayerSetting

from scene_game_set_up import on_bt_back_clicked
from scene_main_menu import init_really_game, colors_idx_to_colors


#
def on_bt_training_click(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    win.main_app.global_vars_set("snakes_speed", 0.001)
    win.main_app.global_vars_set("game_mode", "training_bots")
    win.main_app.global_vars_set("apples_multiple_values", False)
    win.main_app.global_vars_set("init_snake_size", 0)

    #
    map_mode: str = cast(str, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_map_mode"))
    min_score_to_reproduce: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_score_to_reproduce"))
    max_nb_steps: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_max_nb_steps"))
    grid_size: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_grid_size"))
    nb_bots: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_nb_bots"))
    nb_epochs: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_nb_bots"))
    min_random_bots_per_epoch: int = cast(int, win.main_app.get_element_value(MAIN_WINDOW_ID, "training_menu", "input_min_random_bots_per_epoch"))

    # TODO: fusion and reproduction between the best snakes that can reproduce
    init_snakes: list[SnakePlayerSetting] = [
        SnakePlayerSetting(name=f"bot {i}", color_idx=i%len(colors_idx_to_colors), init_size=win.main_app.global_vars_get("init_snake_size"), skin_idx=1, player_type="bot", control_name="fleches")
        for i in range(nb_bots)
    ]

    #
    win.main_app.global_vars_set("map_mode", map_mode)
    win.main_app.global_vars_set("min_score_to_reproduce", min_score_to_reproduce)
    win.main_app.global_vars_set("max_nb_steps", max_nb_steps)
    win.main_app.global_vars_set("terrain_w", grid_size)
    win.main_app.global_vars_set("terrain_h", grid_size)
    win.main_app.global_vars_set("init_snakes", init_snakes)
    win.main_app.global_vars_set("nb_epochs_tot", nb_epochs)
    win.main_app.global_vars_set("nb_epochs_cur", 1)

    #
    init_really_game(win)


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
        onclick=on_bt_back_clicked,
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
        options=set(["together", "separate_close", "separate_far"]),
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
        value=win.main_app.global_vars_get_default("training_bots_min_score_to_reproduce", 10),
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
        value=win.main_app.global_vars_get_default("training_bots_max_steps", 1000),
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
        value=win.main_app.global_vars_get_default("training_bots_nb_bots", 11),
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
        value=win.main_app.global_vars_get_default("training_bots_nb_epochs", 10),
        min_value=1,
        max_value=100
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
        value=win.main_app.global_vars_get_default("training_bots_min_random_bots_per_epoch", 5),
        min_value=0,
        max_value=100
    )
    row_min_random_bots_per_epoch.add_element(input_min_random_bots_per_epoch)



    #
    win.add_scene( training_menu_scene )


