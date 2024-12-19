
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
from scene_game_settings import create_game_settings


#
MAIN_WINDOW_ID: int = 0


#
bots_types_keys: dict[str, list[str]] = {
    "bot_v1": ["weights_path", "radius", "nb_apples", "random_weights"],
    "bot_v2": ["weights_path", "radius", "nb_apples", "random_weights"]
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
    for key in bots_types_keys[bot_dict["type"]]:
        if key not in bot_dict:
            return False
    #
    if bot_dict["type"] == "bot_v1":
        if not os.path.exists(bot_dict["weights_path"]+".npy"):
            return False
    elif bot_dict["type"] == "bot_v2":
        if not os.path.exists(bot_dict["weights_path"]+"_1.npy"):
            return False
        if not os.path.exists(bot_dict["weights_path"]+"_2.npy"):
            return False
    #
    return True



#
if __name__ == "__main__":

    #
    snakes_bot_paths: str = "bots/"
    #
    if not os.path.exists(snakes_bot_paths):
        os.makedirs(snakes_bot_paths)

    #
    app: nd.ND_MainApp = nd.ND_MainApp(
                            DisplayClass=DisplayClass,
                            WindowClass=WindowClass,
                            EventsManagerClass=EventsManagerClass,
                            global_vars_to_save=[
                                "game_nb_init_apples",
                                "game_init_snake_size",
                                "game_map_mode",
                                "game_terrain_w",
                                "game_terrain_h",
                                "game_snakes_speed",
                                "training_bots_new_bots_version",
                                "training_bots_snakes_speed",
                                "training_bots_learning_step",
                                "training_bots_min_random_bots_per_epoch",
                                "training_bots_nb_epochs",
                                "training_init_snakes_size",
                                "training_bots_nb_apples",
                                "training_bots_nb_bots",
                                "training_bots_grid_size",
                                "training_bots_max_steps",
                                "training_bots_min_score_to_reproduce",
                                "training_bots_map_mode"
                            ],
                            path_to_global_vars_save_file=".global_vars"
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
    app.global_vars_set("snakes_bot_paths", snakes_bot_paths)

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
            print(f"DEBUG | {filepath} is not a valid bot config | (keys = {bot_dict.keys()})")
            #
            continue
        #
        app.global_vars_dict_set("bots", bot_dict["name"], bot_dict)

    bots: dict[str, dict] = app.global_vars_get("bots")
    print(f"Loaded {len(bots)} bots.")

    # On peut facilement remplacer quelques paramètres par défaut ici:
    if "game_nb_init_apples" not in app.global_vars:
        app.global_vars_set("game_nb_init_apples", 10)
    if "game_init_snake_size" not in app.global_vars:
        app.global_vars_set("game_init_snake_size", 0)
    if "game_map_mode" not in app.global_vars:
        app.global_vars_set("game_map_mode", "separate_close")  # "together", "separate_far", "separate_close"
    if "game_terrain_w" not in app.global_vars:
        app.global_vars_set("game_terrain_w", 11)
    if "game_terrain_h" not in app.global_vars:
        app.global_vars_set("game_terrain_h", 11)
    if "game_snakes_speed" not in app.global_vars:
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
    create_game_settings(win)

    #
    # win.set_fullscreen(2)

    #
    app.run()
