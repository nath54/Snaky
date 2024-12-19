

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins, ND_Position, ND_Position_Constraints

import lib_nadisplay as nd

from scene_game_set_up import on_bt_back_clicked
from scene_main_menu import map_modes

#
def create_game_settings(win: nd.ND_Window) -> None:

    #
    margin_center: ND_Position_Margins = ND_Position_Margins(margin_left="50%", margin_right="50%", margin_top="50%", margin_bottom="50%")

    #
    game_settings_menu_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="game_settings_menu",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="game_settings_menu"
    )

    #
    game_settings_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="game_settings_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )
    game_settings_menu_scene.add_element(0, game_settings_menu_container)

    # HEADER
    #
    header_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="header_row",
        position=nd.ND_Position_Container(w="100%", h="8%", container=game_settings_menu_container),
        element_alignment="row"
    )
    game_settings_menu_container.add_element(header_row)

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
        text="Game settings Menu"
    )
    header_row.add_element(page_title)


    # BODY
    #
    body_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="body_row",
        position=nd.ND_Position_Container(w="100%", h="92%", container=game_settings_menu_container),
        element_alignment="row"
    )
    game_settings_menu_container.add_element(body_row)

    ### LEFT COLUMN
    #
    left_col: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="left_col",
        position=nd.ND_Position_Container(w="50%", h="100%", container=body_row),
        element_alignment="col",
        inverse_z_order=True
    )
    body_row.add_element(left_col)


    ##### MAP Mode
    row_map_mode: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_map_mode",
        position=nd.ND_Position_Container(w="100%", h=50, container=left_col),
        element_alignment="row"
    )
    left_col.add_element(row_map_mode)

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
        value=win.main_app.global_vars_get_default("game_map_mode", "together"),
        options=map_modes,
        option_list_buttons_height=300,
        font_name="FreeSans",
        on_value_selected=lambda elt, new_val: elt.window.main_app.global_vars_set("game_map_mode", new_val)
    )
    row_map_mode.add_element(input_map_mode)


    ##### Nb apples
    row_nb_apples: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_nb_apples",
        position=nd.ND_Position_Container(w="100%", h=50, container=left_col),
        element_alignment="row"
    )
    left_col.add_element(row_nb_apples)

    #
    text_nb_apples: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_nb_apples",
        position=nd.ND_Position_Container(w=320, h=40, container=row_nb_apples),
        text="nb apples : "
    )
    row_nb_apples.add_element(text_nb_apples)

    #
    input_nb_apples: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_nb_apples",
        position=nd.ND_Position_Container(w=400, h=40, container=row_nb_apples),
        value=win.main_app.global_vars_get_default("game_nb_init_apples", 1),
        min_value=1,
        max_value=100,
        on_new_value_validated=lambda elt, new_val: elt.window.main_app.global_vars_set("game_nb_init_apples", new_val)
    )
    row_nb_apples.add_element(input_nb_apples)


    ##### Init Snakes Size
    row_init_snakes_size: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_init_snakes_size",
        position=nd.ND_Position_Container(w="100%", h=50, container=left_col),
        element_alignment="row"
    )
    left_col.add_element(row_init_snakes_size)

    #
    text_init_snakes_size: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="text_init_snakes_size",
        position=nd.ND_Position_Container(w=320, h=40, container=row_init_snakes_size),
        text="init snakes size : "
    )
    row_init_snakes_size.add_element(text_init_snakes_size)

    #
    input_init_snakes_size: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="input_init_snakes_size",
        position=nd.ND_Position_Container(w=400, h=40, container=row_init_snakes_size),
        value=win.main_app.global_vars_get_default("game_init_snakes_size", 0),
        min_value=0,
        max_value=100,
        on_new_value_validated=lambda elt, new_val: elt.window.main_app.global_vars_set("game_init_snakes_size", new_val)
    )
    row_init_snakes_size.add_element(input_init_snakes_size)


    ##### Snakes Speed
    row_snakes_speed: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_snakes_speed",
        position=nd.ND_Position_Container(w="100%", h=50, container=left_col),
        element_alignment="row"
    )
    left_col.add_element(row_snakes_speed)

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
        value=win.main_app.global_vars_get_default("game_snakes_speed", 0.1),
        min_value=0,
        max_value=0.5,
        step=0.001,
        digits_after_comma=6,
        on_new_value_validated=lambda elt, new_val: elt.window.main_app.global_vars_set("game_snakes_speed", new_val)
    )
    row_snakes_speed.add_element(input_snakes_speed)


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

    #
    win.add_scene( game_settings_menu_scene )
