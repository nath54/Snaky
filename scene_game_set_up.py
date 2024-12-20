

from typing import Optional, cast

from lib_nadisplay_colors import cl, ND_Transformations
from lib_nadisplay_rects import ND_Point, ND_Position_Margins

import lib_nadisplay as nd

from lib_snake import SnakePlayerSetting

from scene_main_menu import on_bt_click_init_game, controls_names_to_keys, colors_idx_to_colors, snake_base_types, snakes_skins_to_skin_idx


#
def on_player_name_escaped(line_edit: nd.ND_LineEdit, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    line_edit.text = player_setting.name

#
def on_player_name_changed(_, new_name: str, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    player_setting.name = new_name
    #

#
def on_player_color_clicked(bt: nd.ND_Button, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    player_setting.color_idx = (player_setting.color_idx + 1) % len(colors_idx_to_colors)
    #
    bt.texture_transformations.color_modulation = colors_idx_to_colors[player_setting.color_idx]

#
def on_player_type_changed(_, new_type: str, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    player_setting.player_type = new_type

#
def on_player_skin_changed(_, new_skin: str, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    player_setting.skin_idx = snakes_skins_to_skin_idx[new_skin]

#
def on_player_controls_changed(_, new_controls_name: str, player_idx: int, main_app: nd.ND_MainApp) -> None:
    #
    player_setting: Optional[SnakePlayerSetting] = main_app.global_vars_list_get_at_idx("game_init_snakes", player_idx)
    #
    if player_setting is None:
        return
    #
    player_setting.control_name = new_controls_name

#
def add_player_row_to_set_up_player_menu(win: nd.ND_Window, players_container: nd.ND_Container, player_lst_idx: int) -> None:
    #
    if players_container is None:
        return

    player_setting: Optional[SnakePlayerSetting] = win.main_app.global_vars_list_get_at_idx("game_init_snakes", player_lst_idx)
    #
    if player_setting is None:
        return

    #
    margin_center: ND_Position_Margins = ND_Position_Margins(margin_top="50%", margin_left="50%", margin_right="50%", margin_bottom="50%")
    #
    row_elt_id: str = f"player_row_{player_lst_idx}"

    #
    player_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id=row_elt_id,
        position=nd.ND_Position_Container(w="100%", h=45, container=players_container, position_margins=ND_Position_Margins(margin_top=5, margin_bottom=5))
    )

    #
    player_name: nd.ND_LineEdit = nd.ND_LineEdit(
        window=win,
        elt_id=f"{row_elt_id}_player_name",
        position=nd.ND_Position_Container(w="25%", h=40, container=player_row, position_margins=margin_center),
        text=player_setting.name,
        place_holder="player name",
        max_text_length=20,
        font_size=20,
        font_name="FreeSans",
        on_line_edit_escaped=lambda line_edit, idx=player_lst_idx, main_app=win.main_app: on_player_name_escaped(line_edit, idx, main_app),  # type: ignore
        on_line_edit_validated=lambda line_edit, new_value, idx=player_lst_idx, main_app=win.main_app: on_player_name_changed(line_edit, new_value, idx, main_app)  # type: ignore
    )
    player_row.add_element(player_name)

    #
    ptypes: set[str] = set(snake_base_types + list(win.main_app.global_vars_get("bots").keys()))
    #
    player_type: nd.ND_SelectOptions = nd.ND_SelectOptions(
        window=win,
        elt_id=f"{row_elt_id}_player_type",
        position=nd.ND_Position_Container(w="20%", h=40, container=player_row, position_margins=margin_center),
        value=player_setting.player_type,
        options=ptypes,
        on_value_selected=lambda elt, new_value, idx=player_lst_idx, main_app=win.main_app: on_player_type_changed(elt, new_value, idx, main_app),  # type: ignore
        font_name="FreeSans"
    )
    player_row.add_element(player_type)

    #
    player_skin: nd.ND_SelectOptions = nd.ND_SelectOptions(
        window=win,
        elt_id=f"{row_elt_id}_player_skin",
        position=nd.ND_Position_Container(w="20%", h=40, container=player_row, position_margins=margin_center),
        value="snake",
        options=set(list(snakes_skins_to_skin_idx.keys())),
        on_value_selected=lambda elt, new_value, idx=player_lst_idx, main_app=win.main_app: on_player_skin_changed(elt, new_value, idx, main_app),  # type: ignore
        font_name="FreeSans"
    )
    player_row.add_element(player_skin)

    #
    player_icon: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id=f"{row_elt_id}_player_icon",
        position=nd.ND_Position_Container(w=40, h=40, container=player_row, position_margins=margin_center),
        onclick=None,
        text="",
        base_bg_texture="res/sprites/snake_icon.png",
        texture_transformations=ND_Transformations(color_modulation=colors_idx_to_colors[player_setting.color_idx])
    )
    #
    player_icon.onclick = lambda win, bt=player_icon, idx=player_lst_idx, main_app=win.main_app: on_player_color_clicked(bt, idx, main_app)  # type: ignore
    #
    player_row.add_element(player_icon)

    #
    player_controls: nd.ND_SelectOptions = nd.ND_SelectOptions(
        window=win,
        elt_id=f"{row_elt_id}_player_controls",
        position=nd.ND_Position_Container(w="10%", h=40, container=player_row, position_margins=margin_center),
        value=player_setting.control_name,
        options=set(controls_names_to_keys.keys()),
        on_value_selected=lambda elt, new_value, idx=player_lst_idx, main_app=win.main_app: on_player_controls_changed(elt, new_value, idx, main_app), # type: ignore
        font_name="FreeSans"
    )
    player_row.add_element(player_controls)

    #
    players_container.add_element(player_row)

#
def on_bt_add_player_button(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "players_container") )
    #
    if players_container is None:
        return

    #
    cnks: list[str] = list(controls_names_to_keys.keys())

    #
    n: int = win.main_app.global_vars_list_length("game_init_snakes")
    init_snake_size: int = win.main_app.global_vars_get_default("game_init_snake_size", 0)
    win.main_app.global_vars_list_append("game_init_snakes", SnakePlayerSetting(name=f"player {n+1}", color_idx=n % len(colors_idx_to_colors), init_size=init_snake_size, skin_idx=1, player_type="human", control_name=cnks[n % len(cnks)]))
    #
    add_player_row_to_set_up_player_menu(win, players_container, n)

#
def on_bt_remove_player_button(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    players_container: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "players_container") )
    #
    if players_container is None:
        return
    #
    n: int = win.main_app.global_vars_list_length("game_init_snakes")

    #
    if n <= 1:
        return

    #
    win.main_app.global_vars_list_del_at_idx("game_init_snakes", n-1)

    #
    row_elt_id: str = f"player_row_{n-1}"

    #
    row_elt: Optional[nd.ND_Container] = cast(Optional[nd.ND_Container], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", row_elt_id) )

    #
    if not row_elt:
        return

    #
    players_container.remove_element(row_elt)

    # TODO: assure that row_elt is well destroyed properly

#
def on_bt_game_settings_click(elt: nd.ND_Clickable) -> None:
    #
    elt.window.set_state("game_settings_menu")

#
def on_bt_back_clicked(elt: nd.ND_Clickable) -> None:
    #
    elt.window.set_state("main_menu")

#
def on_bt_map_size_change_clicked(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    map_width_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_width_multilayer") )
    map_height_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_height_multilayer") )
    #
    if map_width_multilayer is None or map_height_multilayer is None:
        return
    #
    map_width_bt: nd.ND_Button = cast(nd.ND_Button, map_width_multilayer.elements_by_id["map_width_bt"])
    map_height_bt: nd.ND_Button = cast(nd.ND_Button, map_height_multilayer.elements_by_id["map_height_bt"])
    #
    map_width_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_width_multilayer.elements_by_id["map_width_line_edit"])
    map_height_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_height_multilayer.elements_by_id["map_height_line_edit"])
    #
    map_width_bt.visible = False
    map_height_bt.visible = False
    #
    map_width_line_edit.value = int(map_width_bt.text)
    map_height_line_edit.value = int(map_height_bt.text)
    #
    map_width_line_edit.visible = True
    map_height_line_edit.visible = True
    #
    map_utils_edit_size_row: nd.ND_Container = cast(nd.ND_Container, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_utils_edit_size_row"))
    map_reset_size_bt: nd.ND_Button = cast(nd.ND_Button, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_reset_size_bt"))
    #
    map_reset_size_bt.visible = False
    map_utils_edit_size_row.visible = True
    #

#
def on_bt_map_size_validate_clicked(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    map_width_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_width_multilayer") )
    map_height_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_height_multilayer") )
    #
    if map_width_multilayer is None or map_height_multilayer is None:
        return
    #
    map_width_bt: nd.ND_Button = cast(nd.ND_Button, map_width_multilayer.elements_by_id["map_width_bt"])
    map_height_bt: nd.ND_Button = cast(nd.ND_Button, map_height_multilayer.elements_by_id["map_height_bt"])
    #
    map_width_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_width_multilayer.elements_by_id["map_width_line_edit"])
    map_height_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_height_multilayer.elements_by_id["map_height_line_edit"])
    #
    map_width_bt.visible = True
    map_height_bt.visible = True
    #
    new_w: int = map_width_line_edit.value
    new_h: int = map_height_line_edit.value
    #
    map_width_bt.text = str(new_w)
    map_height_bt.text = str(new_h)
    #
    win.main_app.global_vars_set("game_terrain_w", int(new_w))
    win.main_app.global_vars_set("game_terrain_h", int(new_h))
    #
    map_width_line_edit.visible = False
    map_height_line_edit.visible = False
    #
    map_utils_edit_size_row: nd.ND_Container = cast(nd.ND_Container, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_utils_edit_size_row"))
    map_reset_size_bt: nd.ND_Button = cast(nd.ND_Button, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_reset_size_bt"))
    #
    map_reset_size_bt.visible = True
    map_utils_edit_size_row.visible = False

#
def on_bt_map_size_reset_clicked(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    map_width_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_width_multilayer") )
    map_height_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_height_multilayer") )
    #
    if map_width_multilayer is None or map_height_multilayer is None:
        return
    #
    map_width_bt: nd.ND_Button = cast(nd.ND_Button, map_width_multilayer.elements_by_id["map_width_bt"])
    map_height_bt: nd.ND_Button = cast(nd.ND_Button, map_height_multilayer.elements_by_id["map_height_bt"])
    #
    map_width_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_width_multilayer.elements_by_id["map_width_line_edit"])
    map_height_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_height_multilayer.elements_by_id["map_height_line_edit"])
    #
    map_width_bt.visible = True
    map_height_bt.visible = True
    #
    map_width_bt.text = "30"
    map_height_bt.text = "30"
    #
    map_width_line_edit.visible = False
    map_height_line_edit.visible = False
    #
    map_utils_edit_size_row: nd.ND_Container = cast(nd.ND_Container, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_utils_edit_size_row"))
    map_reset_size_bt: nd.ND_Button = cast(nd.ND_Button, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_reset_size_bt"))
    #
    map_reset_size_bt.visible = True
    map_utils_edit_size_row.visible = False

#
def on_bt_map_size_cancel_clicked(elt: nd.ND_Clickable) -> None:
    #
    win: nd.ND_Window = elt.window
    #
    MAIN_WINDOW_ID: int = win.window_id
    #
    map_width_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_width_multilayer") )
    map_height_multilayer: Optional[nd.ND_MultiLayer] = cast(Optional[nd.ND_MultiLayer], win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_height_multilayer") )
    #
    if map_width_multilayer is None or map_height_multilayer is None:
        return
    #
    map_width_bt: nd.ND_Button = cast(nd.ND_Button, map_width_multilayer.elements_by_id["map_width_bt"])
    map_height_bt: nd.ND_Button = cast(nd.ND_Button, map_height_multilayer.elements_by_id["map_height_bt"])
    #
    map_width_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_width_multilayer.elements_by_id["map_width_line_edit"])
    map_height_line_edit: nd.ND_NumberInput = cast(nd.ND_NumberInput, map_height_multilayer.elements_by_id["map_height_line_edit"])
    #
    map_width_bt.visible = True
    map_height_bt.visible = True
    #
    map_width_line_edit.visible = False
    map_height_line_edit.visible = False
    #
    map_utils_edit_size_row: nd.ND_Container = cast(nd.ND_Container, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_utils_edit_size_row"))
    map_reset_size_bt: nd.ND_Button = cast(nd.ND_Button, win.main_app.get_element(MAIN_WINDOW_ID, "game_setup", "map_reset_size_bt"))
    #
    map_reset_size_bt.visible = True
    map_utils_edit_size_row.visible = False

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
        position=nd.ND_Position_Container(w="45%", h="75%", container=main_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
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
        position=nd.ND_Position_Container(w="100%", h="65%", container=main_players_container),
        element_alignment="col",
        inverse_z_order=True,
        overflow_hidden=True,
        scroll_h=True
    )
    main_players_container.add_element(players_container)

    #
    nb_players_configs: int = win.main_app.global_vars_list_length("game_init_snakes")
    for payer_idx in range(nb_players_configs):
        add_player_row_to_set_up_player_menu(win, players_container, payer_idx)

    #
    row_bts_manage_players: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="row_bts_manage_players",
        position=nd.ND_Position_Container(w="100%", h="10%", container=main_players_container),
        overflow_hidden=False,
        element_alignment="row_wrap"
    )
    main_players_container.add_element(row_bts_manage_players)

    #
    bt_add_player: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_add_player",
        position=nd.ND_Position_Container(w="40%", h=30, container=row_bts_manage_players, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_add_player_button,
        text="add"
    )
    row_bts_manage_players.add_element(bt_add_player)

    #
    bt_del_player: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="bt_del_player",
        position=nd.ND_Position_Container(w="40%", h=30, container=row_bts_manage_players, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_remove_player_button,
        text="del"
    )
    row_bts_manage_players.add_element(bt_del_player)



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
        text="<",
        font_name="FreeSans"
    )
    map_change_row.add_element(map_left_arrow)

    #
    map_icon: nd.ND_Rectangle = nd.ND_Rectangle(
        window=win,
        elt_id="map_icon",
        position=nd.ND_Position_Container(w="50%", h="square", container=map_change_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        base_bg_color=cl("dark green"),
        mouse_active=False
    )
    map_change_row.add_element(map_icon)

    #
    map_right_arrow: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_right_arrow",
        position=nd.ND_Position_Container(w=20, h="90%", container=map_change_row, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=None,
        text=">",
        font_name="FreeSans"
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
    map_width_multilayer: nd.ND_MultiLayer = nd.ND_MultiLayer(
        window=win,
        elt_id="map_width_multilayer",
        position=nd.ND_Position_Container(100, 40, container=map_size_row, position_margins=ND_Position_Margins(margin_left="100%", margin_top="50%", margin_bottom="50%", margin_right=5)),
        elements_layers={}
    )
    map_size_row.add_element(map_width_multilayer)
    #
    map_width_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_width_bt",
        position=nd.ND_Position_MultiLayer(multilayer=map_width_multilayer, w="100%", h="100%"),
        onclick=on_bt_map_size_change_clicked,
        text=str(win.main_app.global_vars_get_default("game_terrain_w", 29))
    )
    map_width_multilayer.add_element(1, map_width_bt)
    #
    map_width_line_edit: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="map_width_line_edit",
        position=nd.ND_Position_MultiLayer(multilayer=map_width_multilayer, w="100%", h="100%"),
        value=win.main_app.global_vars_get_default("game_terrain_w", 29),
        min_value=5,
        max_value=200,
        digits_after_comma=0,
        step=1
    )
    map_width_line_edit.visible = False
    #
    map_width_multilayer.add_element(0, map_width_line_edit)

    #
    map_size_cross_text: nd.ND_Text = nd.ND_Text(
        window=win,
        elt_id="map_size_cross_text",
        position=nd.ND_Position_Container(w=40, h=40, container=map_size_row, position_margins=ND_Position_Margins(margin_left=5, margin_top="50%", margin_bottom="50%", margin_right=5)),
        text="x"
    )
    map_size_row.add_element(map_size_cross_text)

    #
    map_height_multilayer: nd.ND_MultiLayer = nd.ND_MultiLayer(
        window=win,
        elt_id="map_height_multilayer",
        position=nd.ND_Position_Container(w=100, h=40, container=map_size_row, position_margins=ND_Position_Margins(margin_left=5, margin_top="50%", margin_bottom="50%", margin_right=15)),
        elements_layers={}
    )
    map_size_row.add_element(map_height_multilayer)
    #
    map_height_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_height_bt",
        position=nd.ND_Position_MultiLayer(multilayer=map_height_multilayer, w="100%", h="100%"),
        onclick=on_bt_map_size_change_clicked,
        text=str(win.main_app.global_vars_get_default("game_terrain_h", 29))
    )
    map_height_multilayer.add_element(1, map_height_bt)
    #
    map_height_line_edit: nd.ND_NumberInput = nd.ND_NumberInput(
        window=win,
        elt_id="map_height_line_edit",
        position=nd.ND_Position_MultiLayer(multilayer=map_height_multilayer, w="100%", h="100%"),
        value=win.main_app.global_vars_get_default("game_terrain_h", 29),
        min_value=5,
        max_value=200,
        digits_after_comma=0,
        step=1
    )
    map_height_line_edit.visible = False
    # #
    map_height_multilayer.add_element(0, map_height_line_edit)

    #
    map_size_utils_bt_multilayer: nd.ND_MultiLayer = nd.ND_MultiLayer(
        window=win,
        elt_id="map_size_utils_bt_multilayer",
        position=nd.ND_Position_Container(100, 40, container=map_size_row, position_margins=ND_Position_Margins(margin_left=15, margin_top="50%", margin_bottom="50%", margin_right="60%")),
        elements_layers={}
    )
    map_size_row.add_element(map_size_utils_bt_multilayer)
    #
    map_reset_size_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_reset_size_bt",
        position=nd.ND_Position_MultiLayer(multilayer=map_height_multilayer, w=100, h=40, position_margins=ND_Position_Margins(margin_left=15, margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_map_size_reset_clicked,
        text="reset"
    )
    map_size_utils_bt_multilayer.add_element(1, map_reset_size_bt)
    #
    map_utils_edit_size_row: nd.ND_Container = nd.ND_Container(
        window=win,
        elt_id="map_utils_edit_size_row",
        position=nd.ND_Position_MultiLayer(multilayer=map_size_utils_bt_multilayer, w="100%", h="100%"),
        element_alignment="row",
        overflow_hidden=False
    )
    map_utils_edit_size_row.visible = False
    map_size_utils_bt_multilayer.add_element(0, map_utils_edit_size_row)
    #
    map_size_change_validate_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_size_change_validate_bt",
        position=nd.ND_Position_Container(container=map_utils_edit_size_row, w=100, h=40, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_map_size_validate_clicked,
        text="ok"
    )
    map_utils_edit_size_row.add_element(map_size_change_validate_bt)
    #
    map_size_change_cancel_bt: nd.ND_Button = nd.ND_Button(
        window=win,
        elt_id="map_size_change_cancel_bt",
        position=nd.ND_Position_Container(container=map_utils_edit_size_row, w=100, h=40, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
        onclick=on_bt_map_size_cancel_clicked,
        text="cancel"
    )
    map_utils_edit_size_row.add_element(map_size_change_cancel_bt)
    #

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
        position=nd.ND_Position_Container(w=200, h=40, container=footer_container, position_margins=ND_Position_Margins(margin_left="50%", margin_top="50%", margin_bottom="50%", margin_right="50%")),
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

