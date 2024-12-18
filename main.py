
from typing import Optional

import os
import json

import lib_nadisplay as nd

from lib_nadisplay_sdl_sdlgfx import ND_Display_SDL_SDLGFX as DisplayClass, ND_Window_SDL_SDLGFX as WindowClass
# from lib_nadisplay_sdl_opengl import ND_Display_SDL_OPENGL as DisplayClass, ND_Window_SDL_OPENGL as WindowClass  # Not working at all
# from lib_nadisplay_glfw_opengl import ND_Display_GLFW_OPENGL as DisplayClass, ND_Window_GLFW_OPENGL as WindowClass  # Not working at all
# from lib_nadisplay_glfw_vulkan import ND_Display_GLFW_VULKAN as DisplayClass, ND_Window_GLFW_VULKAN as WindowClass  # Not working at all
from lib_nadisplay_sdl import ND_EventsManager_SDL as EventsManagerClass
# from lib_nadisplay_glfw import ND_EventsManager_GLFW as EventsManagerClass  # Not working at all
# from lib_nadisplay_pygame import ND_Display_Pygame as DisplayClass, ND_Window_Pygame as WindowClass, ND_EventsManager_Pygame as EventsManagerClass  # Working a little

from lib_snake import SnakePlayerSetting

from scene_main_menu import create_main_menu_scene
from scene_game import create_game_scene
from scene_game_end import create_end_menu
from scene_game_set_up import create_game_setup_scene
from scene_pause_screen import create_pause_menu
from scene_bots_training_menu import create_training_menu_scene


#
MAIN_WINDOW_ID: int = 0


#
bots_types_keys: dict[str, list[str]] = {
    "bot_v1": ["path_weights", "radius", "nb_apples", "random_weights"],
    "bot_v2": ["path_weights_1", "path_weights_2", "radius", "nb_apples", "random_weights"]
}


#
def verify_json_dict_is_bot(bot_dict: dict) -> bool:
    #
    if "name" not in bot_dict:
        return False
    #
    if "type" not in bot_dict:
        return False
    #
    if "max_score" not in bot_dict:
        return False
    #
    if "scores" not in bot_dict:
        return False
    #
    if bot_dict["type"] not in bots_types_keys:
        return False
    #
    key: str
    for key in bots_types_keys:
        if key not in bot_dict:
            return False
    #
    return True



#
if __name__ == "__main__":

    #
    snakes_bot_paths: str = "./bots/"
    #
    if not os.path.exists(snakes_bot_paths):
        os.makedirs(snakes_bot_paths)

    #
    app: nd.ND_MainApp = nd.ND_MainApp(
                        DisplayClass=DisplayClass,
                        WindowClass=WindowClass,
                        EventsManagerClass=EventsManagerClass
    )
    #
    if app.display is None:
        exit(1)

    # Init fonts
    app.display.add_font("res/fonts/aAsianNinja.otf", "AsianNinja")
    app.display.add_font("res/fonts/HIROMISAKE.ttf", "Hiromisake")
    app.display.add_font("res/fonts/Korean_Calligraphy.ttf", "KoreanCalligraphy")
    app.display.default_font = "KoreanCalligraphy"

    #
    win_id: int = app.display.create_window({
        "title": "Super Snaky",
        "size": (1750, 950),
        "window_id": MAIN_WINDOW_ID,
        "init_state": "main_menu"
    }, True)
    #
    win: Optional[nd.ND_Window] = app.display.get_window(win_id)
    #
    if win is None:
        exit(1)

    #
    app.global_vars_set("MAIN_WINDOW_ID", 0)

    # Chargement des bots qui ont déjà été sauvegardés
    app.global_vars_set("bots", {})

    #
    bot_dict: dict
    for filepath in os.listdir(snakes_bot_paths):
        #
        if not filepath.endswith(".json"):
            continue

        # Les bots seront enregistrés dans un fichier json

        #
        with open(f"{snakes_bot_paths}{filepath}", "r", encoding="utf-8") as f:
            bot_dict = json.load(f)
        #
        if not verify_json_dict_is_bot(bot_dict):
            #
            continue
        #
        app.global_vars_dict_set("bots", bot_dict["name"], bot_dict)

    # On peut facilement remplacer quelques paramètres par défaut ici:
    app.global_vars_set("game_nb_init_apples", 10)
    app.global_vars_set("game_init_snake_size", 0)
    app.global_vars_set("game_map_mode", "separate_close")  # "together", "separate_far", "separate_close"
    app.global_vars_set("game_terrain_w", 11)
    app.global_vars_set("game_terrain_h", 11)
    app.global_vars_set("game_snakes_speed", 0.1)

    #
    init_snake_size: int = win.main_app.global_vars_get_default("game_init_snake_size", 0)  #
    app.global_vars_set("game_init_snakes",
        [SnakePlayerSetting(name="player1", color_idx=0, init_size=init_snake_size, skin_idx=1, player_type="human", control_name="zqsd")]
    )

    #
    create_main_menu_scene(win)
    create_game_scene(win)
    create_end_menu(win)
    create_game_setup_scene(win)
    create_pause_menu(win)
    create_training_menu_scene(win)

    #
    # win.set_fullscreen(2)

    #
    app.run()
