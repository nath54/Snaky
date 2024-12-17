
from typing import Optional

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
if __name__ == "__main__":
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

    # On peut facilement remplacer quelques paramètres par défaut ici:
    app.global_vars_set("nb_init_apples", 1)
    app.global_vars_set("init_snake_size", 0)
    app.global_vars_set("map_mode", "separate_close")  # "together", "separate_far", "separate_close"
    app.global_vars_set("terrain_w", 11)
    app.global_vars_set("terrain_h", 11)
    app.global_vars_set("snakes_speed", 0.01)

    #
    init_snake_size: int = win.main_app.global_vars_get_default("init_snake_size", 0)  #
    app.global_vars_set("init_snakes",
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
