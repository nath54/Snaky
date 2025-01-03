

from lib_nadisplay_colors import cl
from lib_nadisplay_rects import ND_Point, ND_Position_Margins

import lib_nadisplay as nd


from scene_main_menu import on_bt_click_init_game, on_bt_click_quit

from scene_pause_screen import on_bt_go_to_menu


#
def create_end_menu(win: nd.ND_Window) -> None:
    #
    end_game_menu_scene: nd.ND_Scene = nd.ND_Scene(
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
    bts_container.add_element(bt_go_to_menu)
    bts_container.add_element(bt_replay)
    bts_container.add_element(bt_quit)

    #
    end_menu_container.add_element(text1)
    end_menu_container.add_element(bts_container)

    #
    end_game_menu_scene.add_element(0, end_menu_container)

    #
    win.add_scene( end_game_menu_scene )

