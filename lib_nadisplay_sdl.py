
from typing import Optional
from lib_nadisplay_colors import ND_Color
from lib_nadisplay_rects import ND_Point
import lib_nadisplay_events as nd_event
from lib_nadisplay import ND_EventsManager, ND_MainApp, ND_Window
import ctypes  # type: ignore
import sdl2  # type: ignore


#
SDLK_ATTRIBUTES_TO_KEYNAME: dict[str, str] = {
    "SDLK_TAB"               : "tab",
    "SDLK_CLEAR"             : "clear",
    "SDLK_RETURN"            : "return",
    "SDLK_PAUSE"             : "pause",
    "SDLK_ESCAPE"            : "escape",
    "SDLK_SPACE"             : "space",
    "SDLK_BACKSPACE"         : "backspace",
    "SDLK_EXCLAIM"           : "exclaim",
    "SDLK_QUOTEDBL"          : "quotedbl",
    "SDLK_HASH"              : "hash",
    "SDLK_DOLLAR"            : "dollar",
    "SDLK_AMPERSAND"         : "ampersand",
    "SDLK_QUOTE"             : "quote",
    "SDLK_LEFTPAREN"         : "left parenthesis",
    "SDLK_RIGHTPAREN"        : "right parenthesis",
    "SDLK_ASTERISK"          : "asterisk",
    "SDLK_PLUS"              : "plus sign",
    "SDLK_COMMA"             : "comma",
    "SDLK_MINUS"             : "minus sign",
    "SDLK_PERIOD"            : "period",
    "SDLK_SLASH"             : "forward slash",
    "SDLK_0"                 : "0",
    "SDLK_1"                 : "1",
    "SDLK_2"                 : "2",
    "SDLK_3"                 : "3",
    "SDLK_4"                 : "4",
    "SDLK_5"                 : "5",
    "SDLK_6"                 : "6",
    "SDLK_7"                 : "7",
    "SDLK_8"                 : "8",
    "SDLK_9"                 : "9",
    "SDLK_COLON"             : "colon",
    "SDLK_SEMICOLON"         : "semicolon",
    "SDLK_LESS"              : "less-than sign",
    "SDLK_EQUALS"            : "equals sign",
    "SDLK_GREATER"           : "greater-than sign",
    "SDLK_QUESTION"          : "question mark",
    "SDLK_AT"                : "at",
    "SDLK_LEFTBRACKET"       : "left bracket",
    "SDLK_BACKSLASH"         : "backslash",
    "SDLK_RIGHTBRACKET"      : "right bracket",
    "SDLK_CARET"             : "caret",
    "SDLK_UNDERSCORE"        : "underscore",
    "SDLK_BACKQUOTE"         : "grave",
    "SDLK_a"                 : "a",
    "SDLK_b"                 : "b",
    "SDLK_c"                 : "c",
    "SDLK_d"                 : "d",
    "SDLK_e"                 : "e",
    "SDLK_f"                 : "f",
    "SDLK_g"                 : "g",
    "SDLK_h"                 : "h",
    "SDLK_i"                 : "i",
    "SDLK_j"                 : "j",
    "SDLK_k"                 : "k",
    "SDLK_l"                 : "l",
    "SDLK_m"                 : "m",
    "SDLK_n"                 : "n",
    "SDLK_o"                 : "o",
    "SDLK_p"                 : "p",
    "SDLK_q"                 : "q",
    "SDLK_r"                 : "r",
    "SDLK_s"                 : "s",
    "SDLK_t"                 : "t",
    "SDLK_u"                 : "u",
    "SDLK_v"                 : "v",
    "SDLK_w"                 : "w",
    "SDLK_x"                 : "x",
    "SDLK_y"                 : "y",
    "SDLK_z"                 : "z",
    "SDLK_DELETE"            : "delete",
    "SDLK_KP0"               : "keypad 0",
    "SDLK_KP1"               : "keypad 1",
    "SDLK_KP2"               : "keypad 2",
    "SDLK_KP3"               : "keypad 3",
    "SDLK_KP4"               : "keypad 4",
    "SDLK_KP5"               : "keypad 5",
    "SDLK_KP6"               : "keypad 6",
    "SDLK_KP7"               : "keypad 7",
    "SDLK_KP8"               : "keypad 8",
    "SDLK_KP9"               : "keypad 9",
    "SDLK_UP"                : "up arrow",
    "SDLK_DOWN"              : "down arrow",
    "SDLK_RIGHT"             : "right arrow",
    "SDLK_LEFT"              : "left arrow",
    "SDLK_INSERT"            : "insert",
    "SDLK_HOME"              : "home",
    "SDLK_END"               : "end",
    "SDLK_PAGEUP"            : "page up",
    "SDLK_PAGEDOWN"          : "page down",
    "SDLK_F1"                : "F1",
    "SDLK_F2"                : "F2",
    "SDLK_F3"                : "F3",
    "SDLK_F4"                : "F4",
    "SDLK_F5"                : "F5",
    "SDLK_F6"                : "F6",
    "SDLK_F7"                : "F7",
    "SDLK_F8"                : "F8",
    "SDLK_F9"                : "F9",
    "SDLK_F10"               : "F10",
    "SDLK_F11"               : "F11",
    "SDLK_F12"               : "F12",
    "SDLK_F13"               : "F13",
    "SDLK_F14"               : "F14",
    "SDLK_F15"               : "F15",
    "SDLK_NUMLOCK"           : "numlock",
    "SDLK_CAPSLOCK"          : "capslock",
    "SDLK_SCROLLOCK"         : "scrollock",
    "SDLK_RSHIFT"            : "right shift",
    "SDLK_LSHIFT"            : "left shift",
    "SDLK_RCTRL"             : "right ctrl",
    "SDLK_LCTRL"             : "left ctrl",
    "SDLK_RALT"              : "right alt",
    "SDLK_LALT"              : "left alt",
    "SDLK_RMETA"             : "right meta",
    "SDLK_LMETA"             : "left meta",
    "SDLK_LSUPER"            : "left windows key",
    "SDLK_RSUPER"            : "right windows key",
    "SDLK_MODE"              : "mode shift",
    "SDLK_HELP"              : "help",
    "SDLK_PRINT"             : "print-screen",
    "SDLK_SYSREQ"            : "SysRq",
    "SDLK_BREAK"             : "break",
    "SDLK_MENU"              : "menu",
    "SDLK_POWER"             : "power",
    "SDLK_EURO"              : "euro"
}

#
SDL_KEYCODES_TO_STR: dict[int, str] = {}

#
k_code: Optional[int] = None
#
for sdlk_attr in SDLK_ATTRIBUTES_TO_KEYNAME:
    #
    k_code = getattr(sdl2, sdlk_attr, None)
    #
    if k_code is not None:
        SDL_KEYCODES_TO_STR[k_code] = SDLK_ATTRIBUTES_TO_KEYNAME[sdlk_attr]


#
def to_sdl_color(c: ND_Color) -> sdl2.SDL_Color:
    return sdl2.SDL_Color(c.r, c.g, c.b, c.a)


#
def get_display_info() -> Optional[sdl2.SDL_DisplayMode]:
    # Initialize SDL
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        return None

    display_mode = sdl2.SDL_DisplayMode()

    # Get current display mode for the primary display (index 0)
    if sdl2.SDL_GetCurrentDisplayMode(0, display_mode) != 0:
        sdl2.SDL_Quit()
        return None

    return display_mode


#
class ND_EventsManager_SDL(ND_EventsManager):
    #
    def __init__(self, main_app: ND_MainApp) -> None:
        #
        super().__init__(main_app)

    #
    def poll_next_event(self) -> Optional[nd_event.ND_Event]:

        #
        sdl_event: sdl2.SDL_Event = sdl2.SDL_Event()

        # If no events are polled
        if sdl2.SDL_PollEvent(ctypes.byref(sdl_event)) == 0:
            #
            return None

        # -- APP QUIT EVENT --
        if sdl_event.type == sdl2.SDL_QUIT:
            return nd_event.ND_EventQuit()

        # -- WINDOW EVENT --
        elif sdl_event.type == sdl2.SDL_WINDOWEVENT:
            #
            sdl_event_window_id: int = sdl_event.window.windowID
            #
            nd_window_id: int = -1
            #
            if self.main_app.display is not None:
                #
                window_id: int
                window: Optional[ND_Window]
                for window_id, window in self.main_app.display.windows.items():
                    if window is not None and window.sdl_or_glfw_window_id == sdl_event_window_id:
                        nd_window_id = window_id
            #
            if sdl_event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                #
                return nd_event.ND_EventWindowClose(window_id=nd_window_id)
            #
            # elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_SHOWN:
            #     #
            #     return nd_event.ND_EventWindowShown(nd_window_id)

            # elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_HIDDEN:
            #     #
            #     return nd_event.ND_EventWindowHidden(nd_window_id)

            elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                #
                new_window_width: int = sdl_event.window.data1  # width
                new_window_height: int = sdl_event.window.data2  # height
                #
                return nd_event.ND_EventWindowResized(window_id=nd_window_id, w=new_window_width, h=new_window_height)
            #
            elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_MOVED:
                #
                new_window_x: int = sdl_event.window.data1
                new_window_y: int = sdl_event.window.data2
                #
                return nd_event.ND_EventWindowMoved(window_id=nd_window_id, x=new_window_x, y=new_window_y)
            #
            # elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_ENTER:
            #     #
            #     return nd_event.ND_EventWindowFocusGained(nd_window_id)
            # #
            # elif sdl_event.window.event == sdl2.SDL_WINDOWEVENT_LEAVE:
            #     #
            #     return nd_event.ND_EventWindowFocusLost(nd_window_id)

        # -- KEYBOARD EVENT --
        elif sdl_event.type == sdl2.SDL_KEYDOWN:
            #
            if sdl_event.key.keysym.sym in SDL_KEYCODES_TO_STR:
                #
                self.keys_pressed.add(SDL_KEYCODES_TO_STR[sdl_event.key.keysym.sym])
                #
                return nd_event.ND_EventKeyDown(
                                    key=SDL_KEYCODES_TO_STR[sdl_event.key.keysym.sym]
                                )
            #
            else:
                #
                return nd_event.ND_EventKeyDown()
        #
        elif sdl_event.type == sdl2.SDL_KEYUP:
            #
            if sdl_event.key.keysym.sym in SDL_KEYCODES_TO_STR:
                #
                self.keys_pressed.remove(SDL_KEYCODES_TO_STR[sdl_event.key.keysym.sym])
                #
                return nd_event.ND_EventKeyUp(
                                    key=SDL_KEYCODES_TO_STR[sdl_event.key.keysym.sym]
                                )
            #
            else:
                #
                return nd_event.ND_EventKeyUp()

        # -- MOUSE EVENT --
        elif sdl_event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            #
            self.mouse_buttons_pressed.add(sdl_event.button.button)
            #
            return nd_event.ND_EventMouseButtonDown(
                                button_id=sdl_event.button.button,
                                x=sdl_event.button.x,
                                y=sdl_event.button.y
            )
        #
        elif sdl_event.type == sdl2.SDL_MOUSEBUTTONUP:
            #
            self.mouse_buttons_pressed.remove(sdl_event.button.button)
            #
            return nd_event.ND_EventMouseButtonUp(
                                button_id=sdl_event.button.button,
                                x=sdl_event.button.x,
                                y=sdl_event.button.y
            )
        #
        elif sdl_event.type == sdl2.SDL_MOUSEMOTION:
            #
            if sdl_event.motion.xrel == 0 and sdl_event.motion.yrel == 0:
                return nd_event.ND_EmptyEvent()
            #
            return nd_event.ND_EventMouseMotion(
                                x=sdl_event.motion.x,
                                y=sdl_event.motion.y,
                                rel_x=sdl_event.motion.xrel,
                                rel_y=sdl_event.motion.yrel
            )
        #
        elif sdl_event.type == sdl2.SDL_MOUSEWHEEL:
            #
            return nd_event.ND_EventMouseWheelScrolled(
                                scroll_x=sdl_event.wheel.x,
                                scroll_y=sdl_event.wheel.y
            )

        # If it is an unsupported event
        return nd_event.ND_EmptyEvent()


    #
    def get_mouse_position(self) -> ND_Point:
        #
        mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
        #
        sdl2.mouse.SDL_GetMouseState(ctypes.byref(mouse_x), ctypes.byref(mouse_y))
        #
        return ND_Point(mouse_x.value, mouse_y.value)


    #
    def get_global_mouse_position(self) -> ND_Point:
        #
        mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
        #
        sdl2.SDL_GetGlobalMouseState(ctypes.byref(mouse_x), ctypes.byref(mouse_y))
        #
        return ND_Point(mouse_x.value, mouse_y.value)

