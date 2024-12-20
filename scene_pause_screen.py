

from lib_nadisplay_colors import cl
from lib_nadisplay_rects import ND_Point, ND_Position_Margins

import lib_nadisplay as nd

from scene_main_menu import on_bt_click_quit, on_bt_click_init_game


#
def on_bt_go_to_menu(elt: nd.ND_Clickable) -> None:
    #
    elt.window.set_state("main_menu")

#
def create_pause_menu(win: nd.ND_Window) -> None:
    #
    game_pause_menu_scene: nd.ND_Scene = nd.ND_Scene(
        window=win,
        scene_id="game_pause",
        origin=ND_Point(0, 0),
        elements_layers = {},
        on_window_state="game_pause"
    )

    #
    pause_menu_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="pause_menu_container",
        position=nd.ND_Position_FullWindow(win),
        element_alignment="col"
    )

    #
    bts_container: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="bts_container",
        position=nd.ND_Position_Container(w="100%", h="50%", container=pause_menu_container),
        element_alignment="row"
    )

    #
    text1: nd.ND_Text = nd.ND_Text(
                            window=win,
                            elt_id="game_title",
                            position=nd.ND_Position_Container(w="100%", h="33%", container=pause_menu_container, position_margins=ND_Position_Margins(margin_top=25, margin_bottom=25)),
                            text="The game is paused ! - press 'p' to replay",
                            font_size=40,
                            font_color=cl("orange"),
    )

    #
    bt_go_to_menu: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_go_to_menu",
        position=nd.ND_Position_Container(w=150, h=75, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_go_to_menu,
        text="Go to menu !",
        font_size=20
    )

    #
    bt_replay: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_replay",
        position=nd.ND_Position_Container(w=150, h=75, container=bts_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top=25, margin_bottom=25)),
        onclick=on_bt_click_init_game,
        text="Restart a new game !",
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
    bts_container.add_element(bt_go_to_menu)
    bts_container.add_element(bt_replay)
    bts_container.add_element(bt_quit)

    #
    pause_menu_container.add_element(text1)
    pause_menu_container.add_element(bts_container)

    #
    game_pause_menu_scene.add_element(0, pause_menu_container)

    #
    win.add_scene( game_pause_menu_scene )

