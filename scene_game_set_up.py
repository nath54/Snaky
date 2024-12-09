

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins, ND_Position, ND_Position_Constraints

import lib_nadisplay as nd




#
def on_bt_add_player_button(main_app: nd.ND_MainApp) -> None:
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], main_app.get_element(MAIN_WINDOW_ID, "game_set_up", "players_containers") )
    #
    if not players_container:
        return

    # TODO
    pass




#
def on_bt_remove_player_button(main_app: nd.ND_MainApp, player_idx: int) -> None:
    #
    MAIN_WINDOW_ID: int = main_app.global_vars_get("MAIN_WINDOW_ID")
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], main_app.get_element(MAIN_WINDOW_ID, "game_set_up", "players_containers") )
    #
    if not players_container:
        return

    # TODO
    pass





def create_game_set_up_scene(win: nd.ND_Window) -> None:
    #
    game_set_up_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="game_set_up",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="game_set_up"
    )

    #
    main_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )

    ### Header ###

    #
    header_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="header_container",
        position=nd.ND_Position_Container(w="100%", h="15%", container=main_container),
        element_alignment="row"
    )

    ### Mid ###

    #
    mid_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="mid_container",
        position=nd.ND_Position_Container(w="100%", h="60%", container=main_container),
        element_alignment="row"
    )

    ## Players ##

    #
    main_players_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_players_container",
        position=nd.ND_Position_Container(w="45%", h="95%", container=main_container),
        element_alignment="col"
    )

    #
    players_title: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="players_title",
        position=nd.ND_Position_Container(w="100%", h="25px", container=main_players_container),
        text="Players"
    )

    #
    players_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="players_container",
        position=nd.ND_Position_Container(w="100%", h="auto", container=main_container),
        element_alignment="col"
    )

    #
    bt_add_player: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_add_player",
        position=nd.ND_Position_Container("60%", "30px", container=main_players_container),
        onclick=on_bt_add_player_button,
        text="+"
    )



    ## Map selection ##

    #
    main_maps_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="main_maps_container",
        position=nd.ND_Position_Container(w="45%", h="95%", container=main_container),
        element_alignment="col"
    )


    ### Footer ###

    #
    footer_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="footer_container",
        position=nd.ND_Position_Container(w="100%", h="25%", container=main_container),
        element_alignment="row"
    )


    #
    win.add_scene( game_set_up_scene )

