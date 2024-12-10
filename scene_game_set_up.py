

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins, ND_Position, ND_Position_Constraints

import lib_nadisplay as nd

from scene_main_menu import on_bt_click_init_game


#
def add_player_row_to_set_up_player_menu(main_app: nd.ND_MainApp, players_container: Optional[nd.ND_Container]) -> None:

    # TODO
    pass




#
def on_bt_add_player_button(win: nd.ND_Window) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "players_containers") )
    #
    if not players_container:
        return

    # TODO
    pass




#
def on_bt_remove_player_button(win: nd.ND_Window, player_idx: int) -> None:
    #
    MAIN_WINDOW_ID: int = win.main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "players_containers") )
    #
    if not players_container:
        return

    # TODO
    pass


#
def on_bt_game_settings_click(win: nd.ND_Window) -> None:
    # TODO
    pass


#
def on_bt_back_clicked(win: nd.ND_Window) -> None:
    #
    win.set_state("main_menu")


#
def create_game_setup_scene(win: nd.ND_Window) -> None:
    #
    game_setup_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="game_setup",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="game_setup"
    )

    #
    main_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )
    game_setup_scene.add_element(0, main_container)

    ### Header ###

    #
    header_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="header_container",
        position=nd.ND_Position_Container(w="100%", h="15%", container=main_container),
        element_alignment="row"
    )
    main_container.add_element(header_container)

    #
    bt_back: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_back",
        position=nd.ND_Position_Container(w=150, h=40, container=header_container, position_margins=ND_Position_Margins(margin_left=15, margin_top="50%", margin_bottom="50%", margin_right=15)),
        onclick=on_bt_back_clicked,
        text="back"
    )
    header_container.add_element(bt_back)

    #
    page_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="page_title",
        position=nd.ND_Position_Container(w=100, h="100%", container=header_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        text="Game setup"
    )
    header_container.add_element(page_title)

    ### Mid ###

    #
    mid_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="mid_container",
        position=nd.ND_Position_Container(w="100%", h="60%", container=main_container),
        element_alignment="row"
    )
    main_container.add_element(mid_container)

    ## Players ##

    #
    main_players_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_players_container",
        position=nd.ND_Position_Container(w="45%", h="95%", container=main_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        element_alignment="col"
    )
    mid_container.add_element(main_players_container)

    #
    players_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="players_title",
        position=nd.ND_Position_Container(w="100%", h=25, container=main_players_container),
        text="Players"
    )
    main_players_container.add_element(players_title)

    #
    players_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="players_container",
        position=nd.ND_Position_Container(w="100%", h="auto", container=main_container),
        element_alignment="col"
    )
    main_players_container.add_element(players_container)

    # TODO: add players

    #
    bt_add_player: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_add_player",
        position=nd.ND_Position_Container(w="60%", h=30, container=main_players_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_add_player_button,
        text="add"
    )
    main_players_container.add_element(bt_add_player)



    ## Map selection ##

    #
    main_maps_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_maps_container",
        position=nd.ND_Position_Container(w="45%", h="95%", container=mid_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        element_alignment="col"
    )
    mid_container.add_element(main_maps_container)

    #
    map_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="map_title",
        position=nd.ND_Position_Container(w=100, h=25, container=main_maps_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        text="Map"
    )
    main_maps_container.add_element(map_title)

    #
    map_name: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="map_name",
        position=nd.ND_Position_Container(w="100%", h=25, container=main_maps_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        text="map name",
        font_size=18
    )
    main_maps_container.add_element(map_name)

    #
    map_change_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="map_change_row",
        position=nd.ND_Position_Container(w="100%", h="50%", container=main_maps_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        element_alignment="row"
    )
    main_maps_container.add_element(map_change_row)

    #
    map_left_arrow: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_left_arrow",
        position=nd.ND_Position_Container(w=20, h="90%", container=map_change_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=None,
        text="<"
    )
    map_change_row.add_element(map_left_arrow)

    #
    map_icon: nd.ND_Rectangle = nd.ND_Rectangle(
        window=win,
        elt_id="map_icon",
        position=nd.ND_Position_Container(w="50%", h="square", container=map_change_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        base_bg_color=cl("dark green")
    )
    map_change_row.add_element(map_icon)

    #
    map_right_arrow: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_right_arrow",
        position=nd.ND_Position_Container(w=20, h="90%", container=map_change_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=None,
        text=">"
    )
    map_change_row.add_element(map_right_arrow)

    #
    map_size_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="map_size_row",
        position=nd.ND_Position_Container(w="100%", h=40, container=main_maps_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        element_alignment="row"
    )
    main_maps_container.add_element(map_size_row)

    #
    map_width_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_width_bt",
        position=nd.ND_Position_Container(100, 40, container=map_size_row, position_margins=ND_Position_Margins(margin_left="100%", margin_top="50%", margin_bottom="50%", margin_right=5)),
        onclick=None,
        text="30"
    )
    map_size_row.add_element(map_width_bt)

    #
    map_size_cross_text: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="map_size_cross_text",
        position=nd.ND_Position_Container(w=40, h=40, container=map_size_row, position_margins=ND_Position_Margins(margin_left=5, margin_top="50%", margin_bottom="50%", margin_right=5)),
        text="x"
    )
    map_size_row.add_element(map_size_cross_text)

    #
    map_height_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_height_bt",
        position=nd.ND_Position_Container(w=100, h=40, container=map_size_row, position_margins=ND_Position_Margins(margin_left=5, margin_top="50%", margin_bottom="50%", margin_right="100%")),
        onclick=None,
        text="30"
    )
    map_size_row.add_element(map_height_bt)

    #
    map_reset_size_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_reset_size_bt",
        position=nd.ND_Position_Container(w=100, h=40, container=map_size_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=None,
        text="reset"
    )
    map_size_row.add_element(map_reset_size_bt)



    ### Footer ###

    #
    footer_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="footer_container",
        position=nd.ND_Position_Container(w="100%", h="25%", container=main_container),
        element_alignment="row"
    )
    main_container.add_element(footer_container)

    #
    bt_game_settings: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_game_settings",
        position=nd.ND_Position_Container(w=150, h=40, container=footer_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_game_settings_click,
        text="game settings"
    )
    footer_container.add_element(bt_game_settings)

    #
    bt_play: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_play",
        position=nd.ND_Position_Container(w=150, h=40, container=footer_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_click_init_game,
        text="play"
    )
    footer_container.add_element(bt_play)

    #
    win.add_scene( game_setup_scene )

