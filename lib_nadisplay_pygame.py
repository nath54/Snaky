

from typing import Optional, Any, Callable, cast, Type
from threading import Lock

import os

import pygame

from lib_nadisplay_colors import ND_Color
from lib_nadisplay_colors import ND_Transformations
from lib_nadisplay_rects import ND_Rect, ND_Point
from lib_nadisplay import ND_MainApp, ND_Display, ND_EventsManager, ND_Window, ND_Scene
import lib_nadisplay_events as nd_event


#
def pycl(color: ND_Color) -> pygame.Color:
    return pygame.Color(color.r, color.g, color.b, color.a)

#
def pyrect(rect: ND_Rect) -> pygame.Rect:
    return pygame.Rect(rect.x, rect.y, rect.w, rect.h)


#
class ND_Display_Pygame(ND_Display):

    #
    def __init__(self, main_app: ND_MainApp, WindowClass: Type[ND_Window]) -> None:
        # TODO: super()
        # super().__init__()
        #
        self.main_not_threading: bool = True
        self.events_thread_in_main_thread: bool = True
        self.display_thread_in_main_thread: bool = True
        #
        self.WindowClass: Type[ND_Window] = WindowClass
        #
        self.main_app: ND_MainApp = main_app
        #
        self.font_names: dict[str, str] = {}
        self.pygame_fonts: dict[str, dict[int, pygame.font.Font]] = {}
        self.default_font: str = "FreeSans"
        #
        self.windows: dict[int, Optional[ND_Window]] = {}
        self.thread_create_window: Lock = Lock()
        #
        self.shader_program: int = -1
        self.shader_program_textures: int = -1
        #
        self.nb_windows: int = 0


    #
    def get_time_msec(self) -> float:
        return pygame.time.get_ticks()


    #
    def wait_time_msec(self, delay_in_msec: float) -> None:
        pygame.time.delay(int(delay_in_msec))


    #
    def load_system_fonts(self) -> None:
        """Scans system directories for fonts and adds them to the font_names dictionary."""

        #
        font_dirs = []

        #
        if os.name == "nt":  # Windows
            font_dirs.append("C:/Windows/Fonts/")
        elif os.name == "posix":  # macOS, Linux
            if "darwin" in os.uname().sysname.lower():  # macOS
                font_dirs.extend([
                    "/Library/Fonts/",
                    "/System/Library/Fonts/",
                    os.path.expanduser("~/Library/Fonts/")
                ])
            else:  # Linux
                font_dirs.extend([
                    "/usr/share/fonts/",
                    "/usr/local/share/fonts/",
                    os.path.expanduser("~/.fonts/")
                ])

        # Scan directories for .ttf and .otf files
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for root, _, files in os.walk(font_dir):
                    for file in files:
                        if file.endswith((".ttf", ".otf")):
                            font_path = os.path.join(root, file)
                            font_name = os.path.splitext(file)[0]  # Use file name without extension as font name
                            self.font_names[font_name] = font_path

        #
        # print(f"DEBUG | system fonts added : {', '.join(self.font_names.keys())}")


    #
    def init_display(self) -> None:

        # Initialize SDL2 and TTF
        pygame.init()
        pygame.display.init()
        pygame.font.init()

        # Init system fonts
        self.load_system_fonts()

        #
        # print(f"System fonts availables: {self.font_names.keys()}")


    #
    def destroy_display(self) -> None:

        # Cleanup

        #
        w: Optional[ND_Window] = None
        #
        for w in self.windows.values():
            #
            if not w:
                continue
            #
            w.destroy_window()

        #
        pygame.quit()


    #
    def add_font(self, font_path: str, font_name: str) -> None:
        #
        self.font_names[font_name] = font_path


    #
    def get_font(self, font: str, font_size: int) -> Optional[pygame.font.Font]:
        #
        if font not in self.pygame_fonts:
            self.pygame_fonts[font] = {}
        #
        if font_size < 8:
            font_size = 8
        #
        if font_size not in self.pygame_fonts[font]:
            #
            font_path: str = self.font_names[font]
            #
            if (font_path.endswith(".ttf") or font_path.endswith(".otf")) and os.path.exists(font_path):
                #
                self.pygame_fonts[font][font_size] = pygame.font.Font(font_path.encode(encoding="utf-8"), size=font_size)
                #
            else:
                return None
        #
        return self.pygame_fonts[font][font_size]


    #
    def update_display(self) -> None:

        #
        if not pygame.display.get_init():
            return

        #
        for window in list(self.windows.values()):
            #
            if window is not None:
                window.update_display()


    #
    def get_focused_window_id(self) -> int:
        # By default, the unique pygame windows will always be considered as focused, because there are not other windows to focus else
        for win_id in self.windows:
            #
            if self.windows[win_id] is not None:
                return win_id
        #
        return -1


    #
    def create_window(self, window_params: dict[str, Any], error_if_win_id_not_available: bool = False) -> int:
        #
        if self.nb_windows >= 1:
            raise UserWarning("Cannot create more than 1 window in pygame !!!")

        #
        win_id: int = -1
        if "window_id" in window_params:
            win_id = window_params["window_id"]
        #
        with self.thread_create_window:
            #
            if len(self.windows) == 0:
                self.main_app.start_events_thread()
            #
            if win_id == -1:
                win_id = len(self.windows)
                #
            elif win_id in self.windows and error_if_win_id_not_available:
                raise UserWarning(f"Window id {win_id} isn't available!")
            #
            while win_id in self.windows:
                win_id += 1
            #
            window_params["window_id"] = win_id
            #
            self.windows[win_id] = self.WindowClass(self, **window_params)

        #
        self.nb_windows += 1

        #
        return win_id


    #
    def destroy_window(self, win_id: int) -> None:
        #
        with self.thread_create_window:
            #
            if win_id not in self.windows:
                return
            #
            if self.windows[win_id] is not None:
                #
                win: ND_Window = cast(ND_Window, self.windows[win_id])
                #
                win.destroy_window()
                #
                self.nb_windows -= 1
            #
            del(self.windows[win_id])


#
class ND_Window_Pygame(ND_Window):
    #
    def __init__(
            self,
            display: ND_Display,
            window_id: int,
            size: tuple[int, int] | str,
            title: str = "Pygame App",
            fullscreen: bool = False,
            init_state: Optional[str] = None
        ):

        #
        super().__init__(display=display, window_id=window_id, init_state=init_state)

        #
        if isinstance(size, str):
            #
            infos: Optional[Any] = pygame.display.Info()
            #
            if infos is not None:
                #
                screen_width: int = infos.current_w
                screen_height: int = infos.current_h
                #
                if size == "max":
                    self.width = screen_width
                    self.height = screen_height
                elif size == "max/1.5":
                    self.width = int(float(screen_width) / 1.5)
                    self.height = int(float(screen_height) / 1.5)
        #
        elif isinstance(size, tuple):
            self.width = size[0]
            self.height = size[1]

        #
        self.base_width: int = self.width
        self.base_height: int = self.height

        #
        self.mutex_display: Lock = Lock()

        #
        self.current_window_flags: int = 0 # pygame.RESIZABLE -> Do not work !!!
        with self.mutex_display:
            self.pygame_screen: pygame.Surface = pygame.display.set_mode([self.width, self.height], self.current_window_flags)
            pygame.display.set_caption(title)

        #
        self.x = 0
        self.y = 0
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)

        # sdl_or_glfw_window_id is int and has been initialized to -1 in parent class
        self.sdl_or_glfw_window_id = self.window_id

        #
        self.next_texture_id: int = 0
        #
        self.pygame_surfaces: dict[int, pygame.Surface] = {}
        self.mutex_sdl_textures: Lock = Lock()
        #
        self.prepared_font_textures: dict[str, int] = {}


    #
    def destroy_window(self) -> None:
        #
        with self.mutex_display:
            #
            self.display.main_app.delete_mainloop_fns_queue(f"window_{self.window_id}")
            #
            for texture_id in list(self.pygame_surfaces.keys()):
                #
                self.destroy_prepared_texture(texture_id)

            #
            pygame.display.quit()


    #
    def set_title(self, new_title: str) -> None:
        #
        with self.mutex_display:
            pygame.display.set_caption(new_title)


    #
    def set_size(self, new_width: int, new_height: int) -> None:
        #
        self.base_width, self.base_height = new_width, new_height
        self.width, self.height = new_width, new_height
        #
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)
        #
        # with self.mutex_display:
            # self.pygame_screen = pygame.display.set_mode([self.width, self.height], self.current_window_flags)


    #
    def update_size(self, new_w: int, new_h: int) -> None:
        #
        self.width, self.height = new_w, new_h
        self.base_width, self.base_height = new_w, new_h
        #
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)
        #
        # with self.mutex_display:
        #     self.pygame_screen = pygame.display.set_mode([self.width, self.height], self.current_window_flags)


    #
    def set_fullscreen(self, mode: int) -> None:
        """
        Set window fullscreen state:

        modes:
            - 0 = WINDOWED_MODE
            - 1 = BORDERLESS_FULLSCREEN
            - 2 = FULLSCREEN

        Args:
            mode (int): 0, 1, or 2 (see above)
        """

        #
        if mode == 1:
            self.current_window_flags &= ~ pygame.FULLSCREEN
            self.current_window_flags |= pygame.NOFRAME
            #
            screen_info: Any = pygame.display.Info()
            self.width, self.height = screen_info.current_w, screen_info.current_h
            #
        elif mode == 2:
            self.current_window_flags &= ~ pygame.NOFRAME
            self.current_window_flags |= pygame.FULLSCREEN
            #
            screen_info = pygame.display.Info()
            self.width, self.height = screen_info.current_w, screen_info.current_h
            #
        else:
            self.current_window_flags &= ~ pygame.FULLSCREEN
            self.current_window_flags &= ~ pygame.NOFRAME
            #
            self.width, self.height = self.base_width, self.base_height
        #
        # with self.mutex_display:
        #     self.pygame_screen = pygame.display.set_mode([self.width, self.height], self.current_window_flags)


    #
    def blit_texture(self, surface: pygame.Surface, dst_rect: ND_Rect) -> None:
        # Copy the texture into the window display buffer thanks to the renderer

        # Get surface size
        surf_width: int
        surf_height: int
        surf_width, surf_height = surface.get_size()

        # Resize surface if needed
        if (dst_rect.w > 0 and surf_width != dst_rect.w) or (dst_rect.h > 0 and surf_height != dst_rect.h):
            #
            resize_w: int = dst_rect.w if dst_rect.w > 0 else surf_width
            resize_h: int = dst_rect.h if dst_rect.h > 0 else surf_height
            #
            surface = pygame.transform.scale(surface, (resize_w, resize_h))

        # Then blit texture
        self.pygame_screen.blit(surface, pyrect(dst_rect))


    #
    def prepare_text_to_render(self, text: str, color: ND_Color, font_size: int, font_name: Optional[str] = None) -> int:

        #
        if font_name is None:
            font_name = self.display.default_font

        # Get font
        font: Optional[pygame.font.Font] = cast(pygame.font.Font, self.display.get_font(font_name, font_size))

        # Do nothing if not font got
        if font is None:
            return -1

        # Convert surface into texture
        surf: pygame.Surface = font.render(text, True, pycl(color))

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.pygame_surfaces[texture_id] = surf

        #
        return texture_id


    #
    def prepare_image_to_render(self, img_path: str) -> int:

        # Chargement de l'image
        image_surface: Optional[pygame.Surface] = pygame.image.load(img_path)

        # Si l'image n'a pas bien été chargée, erreur et abandon
        if not image_surface:
            print(f"Failed to load image: {img_path}")
            return -1

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.pygame_surfaces[texture_id] = image_surface

        #
        return texture_id


    #
    def render_prepared_texture(self, texture_id: int, x: int, y: int, width: int = -1, height: int = -1, transformations: ND_Transformations = ND_Transformations()) -> None:
        #
        # TODO: add Transformations

        #
        if texture_id not in self.pygame_surfaces:
            return

        #
        surface_to_render: pygame.Surface = self.pygame_surfaces[texture_id]

        #
        self.blit_texture(surface_to_render, ND_Rect(x, y, width, height))


    #
    def get_prepared_texture_size(self, texture_id: int) -> ND_Point:
        #
        if texture_id not in self.pygame_surfaces:
            return ND_Point(0, 0)
        #
        return ND_Point(*self.pygame_surfaces[texture_id].get_size())


    #
    def destroy_prepared_texture(self, texture_id: int) -> None:
        with self.mutex_sdl_textures:
            if texture_id in self.pygame_surfaces:
                del self.pygame_surfaces[texture_id]


    #
    def draw_text(self, txt: str, x: int, y: int, font_size: int, font_color: ND_Color, font_name: Optional[str] = None) -> None:
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        tid: str = f"{txt}_|||_{font_name}_|||_{font_size}_|||_{font_color}"
        #
        if tid not in self.prepared_font_textures:
            self.prepared_font_textures[tid] = self.prepare_text_to_render(text=txt, color=font_color, font_name=font_name, font_size=font_size)
        #
        tsize: ND_Point = self.get_prepared_texture_size(self.prepared_font_textures[tid])
        self.render_prepared_texture(self.prepared_font_textures[tid], x, y, tsize.x, tsize.y)


    #
    def draw_pixel(self, x: int, y: int, color: ND_Color) -> None:
        #
        pygame.draw.rect(self.pygame_screen, color=pycl(color), rect=pygame.Rect(x, y, 1, 1))


    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:
        #
        self.draw_line(x1, x2, y, y, color)


    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        self.draw_line(x, x, y1, y2, color)


    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        pygame.draw.line(self.pygame_screen, pycl(color), (x1, y1), (x2, y2))


    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:
        #
        pygame.draw.line(self.pygame_screen, pycl(color), (x1, y1), (x2, y2), line_thickness)


    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color, border_thickness: int=1) -> None:

        #
        pygame.draw.rect(self.pygame_screen, pycl(fill_color), (x, y, width, height), 0, radius)
        pygame.draw.rect(self.pygame_screen, pycl(border_color), (x, y, width, height), border_thickness, radius)


    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, line_color: ND_Color, border_thickness: int=1) -> None:
        #
        pygame.draw.rect(self.pygame_screen, pycl(line_color), (x, y, width, height), border_thickness)


    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, fill_color: ND_Color) -> None:
        #
        pygame.draw.rect(self.pygame_screen, pycl(fill_color), (x, y, width, height))


    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, line_color: ND_Color, border_thickness: int=1) -> None:
        #
        pygame.draw.circle(self.pygame_screen, pycl(line_color), (x, y), radius, border_thickness)


    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color) -> None:
        #
        pygame.draw.circle(self.pygame_screen, pycl(fill_color), (x, y), radius)


    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, line_color: ND_Color, border_thickness: int = 1) -> None:
        #
        pygame.draw.ellipse(self.pygame_screen, pycl(line_color), (x-rx, y-ry, x+rx, y+rx), border_thickness)


    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:
        #
        pygame.draw.ellipse(self.pygame_screen, pycl(fill_color), (x-rx, y-ry, x+rx, y+rx))


    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color, line_thickness: int = 1) -> None:
        #
        pygame.draw.arc(self.pygame_screen, pycl(color), (x-radius, y-radius, x+radius, y+radius), angle_start, angle_end, line_thickness)


    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, line_color: ND_Color, line_thickness: int = 1) -> None:
        #
        self.draw_arc(x, y, radius, angle_start, angle_end, line_color, line_thickness)

        # TODO: lines


    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:
        #
        self.draw_arc(x, y, radius, angle_start, angle_end, fill_color, -1)


    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, line_color: ND_Color, border_thickness: int = 1) -> None:
        #
        self.draw_unfilled_polygon([x1, x2, x3], [y1, y2, y3], line_color, border_thickness)


    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: ND_Color) -> None:
        #
        self.draw_filled_polygon([x1, x2, x3], [y1, y2, y3], fill_color)


    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, border_thickness: int = 1) -> None:

        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        #
        pygame.draw.polygon(self.pygame_screen, pycl(line_color), [(x_coords[i], y_coords[i]) for i in range(n)], border_thickness)


    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        #
        pygame.draw.polygon(self.pygame_screen, pycl(fill_color), [(x_coords[i], y_coords[i]) for i in range(n)])


    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:
        #
        if texture_id not in self.pygame_surfaces:
            return

        #
        texture: pygame.Surface = self.pygame_surfaces[texture_id]

        #
        n: int = len(x_coords)

        #
        x_min: int = min(x_coords)
        x_max: int = max(x_coords)
        y_min: int = min(y_coords)
        y_max: int = max(y_coords)
        tx: int = x_max - x_min
        ty: int = y_max - y_min

        #
        polygon_surface: pygame.Surface = pygame.Surface((tx, ty), pygame.SRCALPHA)

        #
        pygame.draw.polygon(polygon_surface, (255, 255, 255), [(x_coords[i]-x_min, y_coords[i]-y_min) for i in range(n)])  # White polygon (for visibility)

        # Create a new surface to apply the texture
        textured_surface = pygame.Surface(polygon_surface.get_size(), pygame.SRCALPHA)
        textured_surface.fill((0, 0, 0, 0))  # Transparent background

        texture_scaled = pygame.transform.scale(texture, (tx, ty))  # Resize the texture to match the wanted size
        textured_surface.blit(texture_scaled, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.blit_texture(textured_surface, ND_Rect(x_min, y_min, tx, ty))



    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < nb_interpolations:
            return

        #
        # n: int = len(x_coords)

        # TODO
        pass


    #
    def enable_area_drawing_constraints(self, x: int, y: int, width: int, height: int) -> None:
        self.pygame_screen.set_clip(pygame.Rect(x, y, width, height))


    #
    def disable_area_drawing_constraints(self) -> None:
        self.pygame_screen.set_clip(None)


    #
    def update_display(self) -> None:

        #
        # print(f"DEBUG | update window {self.window_id} that has current state {self.state}.")
        self.width, self.height = self.pygame_screen.get_size()
        # print(f"DEBUG | update window {self.window_id}, x : {self.x}, y : {self.y}, w: {self.width}, h: {self.height}, screen : {self.pygame_screen}")

        #
        self.pygame_screen.fill(pygame.Color(0, 0, 0))

        #
        if self.state is not None and self.state in self.display_states:
            #
            if self.display_states[self.state] is not None:
                #
                display_fn: Callable[[ND_Window], None] = cast(Callable[[ND_Window], None], self.display_states[self.state])
                display_fn(self)

        #
        scene: ND_Scene
        for scene in list(self.scenes.values()):
            scene.render()

        #
        try:
            with self.mutex_display:
                # pygame.display.flip()
                pygame.display.update()
        except Exception as e:
            print(f"Warning: could not update the screen with pygame.display.update().\n{e}")






#
PYGAME_ATTRIBUTES_TO_KEYNAME: dict[str, str] = {
    "K_TAB"               : "tab",
    "K_CLEAR"             : "clear",
    "K_RETURN"            : "return",
    "K_PAUSE"             : "pause",
    "K_ESCAPE"            : "escape",
    "K_SPACE"             : "space",
    "K_BACKSPACE"         : "backspace",
    "K_EXCLAIM"           : "exclaim",
    "K_QUOTEDBL"          : "quotedbl",
    "K_HASH"              : "hash",
    "K_DOLLAR"            : "dollar",
    "K_AMPERSAND"         : "ampersand",
    "K_QUOTE"             : "quote",
    "K_LEFTPAREN"         : "left parenthesis",
    "K_RIGHTPAREN"        : "right parenthesis",
    "K_ASTERISK"          : "asterisk",
    "K_PLUS"              : "plus sign",
    "K_COMMA"             : "comma",
    "K_MINUS"             : "minus sign",
    "K_PERIOD"            : "period",
    "K_SLASH"             : "forward slash",
    "K_0"                 : "0",
    "K_1"                 : "1",
    "K_2"                 : "2",
    "K_3"                 : "3",
    "K_4"                 : "4",
    "K_5"                 : "5",
    "K_6"                 : "6",
    "K_7"                 : "7",
    "K_8"                 : "8",
    "K_9"                 : "9",
    "K_COLON"             : "colon",
    "K_SEMICOLON"         : "semicolon",
    "K_LESS"              : "less-than sign",
    "K_EQUALS"            : "equals sign",
    "K_GREATER"           : "greater-than sign",
    "K_QUESTION"          : "question mark",
    "K_AT"                : "at",
    "K_LEFTBRACKET"       : "left bracket",
    "K_BACKSLASH"         : "backslash",
    "K_RIGHTBRACKET"      : "right bracket",
    "K_CARET"             : "caret",
    "K_UNDERSCORE"        : "underscore",
    "K_BACKQUOTE"         : "grave",
    "K_a"                 : "a",
    "K_b"                 : "b",
    "K_c"                 : "c",
    "K_d"                 : "d",
    "K_e"                 : "e",
    "K_f"                 : "f",
    "K_g"                 : "g",
    "K_h"                 : "h",
    "K_i"                 : "i",
    "K_j"                 : "j",
    "K_k"                 : "k",
    "K_l"                 : "l",
    "K_m"                 : "m",
    "K_n"                 : "n",
    "K_o"                 : "o",
    "K_p"                 : "p",
    "K_q"                 : "q",
    "K_r"                 : "r",
    "K_s"                 : "s",
    "K_t"                 : "t",
    "K_u"                 : "u",
    "K_v"                 : "v",
    "K_w"                 : "w",
    "K_x"                 : "x",
    "K_y"                 : "y",
    "K_z"                 : "z",
    "K_DELETE"            : "delete",
    "K_KP0"               : "keypad 0",
    "K_KP1"               : "keypad 1",
    "K_KP2"               : "keypad 2",
    "K_KP3"               : "keypad 3",
    "K_KP4"               : "keypad 4",
    "K_KP5"               : "keypad 5",
    "K_KP6"               : "keypad 6",
    "K_KP7"               : "keypad 7",
    "K_KP8"               : "keypad 8",
    "K_KP9"               : "keypad 9",
    "K_UP"                : "up arrow",
    "K_DOWN"              : "down arrow",
    "K_RIGHT"             : "right arrow",
    "K_LEFT"              : "left arrow",
    "K_INSERT"            : "insert",
    "K_HOME"              : "home",
    "K_END"               : "end",
    "K_PAGEUP"            : "page up",
    "K_PAGEDOWN"          : "page down",
    "K_F1"                : "F1",
    "K_F2"                : "F2",
    "K_F3"                : "F3",
    "K_F4"                : "F4",
    "K_F5"                : "F5",
    "K_F6"                : "F6",
    "K_F7"                : "F7",
    "K_F8"                : "F8",
    "K_F9"                : "F9",
    "K_F10"               : "F10",
    "K_F11"               : "F11",
    "K_F12"               : "F12",
    "K_F13"               : "F13",
    "K_F14"               : "F14",
    "K_F15"               : "F15",
    "K_NUMLOCK"           : "numlock",
    "K_CAPSLOCK"          : "capslock",
    "K_SCROLLOCK"         : "scrollock",
    "K_RSHIFT"            : "right shift",
    "K_LSHIFT"            : "left shift",
    "K_RCTRL"             : "right ctrl",
    "K_LCTRL"             : "left ctrl",
    "K_RALT"              : "right alt",
    "K_LALT"              : "left alt",
    "K_RMETA"             : "right meta",
    "K_LMETA"             : "left meta",
    "K_LSUPER"            : "left windows key",
    "K_RSUPER"            : "right windows key",
    "K_MODE"              : "mode shift",
    "K_HELP"              : "help",
    "K_PRINT"             : "print-screen",
    "K_SYSREQ"            : "SysRq",
    "K_BREAK"             : "break",
    "K_MENU"              : "menu",
    "K_POWER"             : "power",
    "K_EURO"              : "euro"
}

#
SDL_KEYCODES_TO_STR: dict[int, str] = {}

#
k_code: Optional[int] = None
#
for K_attr in PYGAME_ATTRIBUTES_TO_KEYNAME:
    #
    k_code = getattr(pygame, K_attr, None)
    #
    if k_code is not None:
        SDL_KEYCODES_TO_STR[k_code] = PYGAME_ATTRIBUTES_TO_KEYNAME[K_attr]



PYGAME_WINDOW_EVENTS: set[int] = {
    pygame.WINDOWCLOSE,
    pygame.WINDOWDISPLAYCHANGED,
    pygame.WINDOWENTER,
    pygame.WINDOWEXPOSED,
    pygame.WINDOWFOCUSGAINED,
    pygame.WINDOWFOCUSLOST,
    pygame.WINDOWHIDDEN,
    pygame.WINDOWLEAVE,
    pygame.WINDOWMAXIMIZED,
    pygame.WINDOWMINIMIZED,
    pygame.WINDOWMOVED,
    pygame.VIDEORESIZE,
    pygame.WINDOWRESTORED,
    pygame.WINDOWSHOWN,
    pygame.WINDOWSIZECHANGED
}


#
class ND_EventsManager_Pygame(ND_EventsManager):
    #
    def __init__(self, main_app: ND_MainApp) -> None:
        #
        super().__init__(main_app)

    #
    def poll_next_event(self) -> Optional[nd_event.ND_Event]:

        #
        pygame_event: pygame.event.Event = pygame.event.poll()

        # If no events are polled
        if pygame_event.type == pygame.NOEVENT:
            #
            return None

        # -- APP QUIT EVENT --
        if pygame_event.type == pygame.QUIT:
            return nd_event.ND_EventQuit()

        # -- WINDOW EVENT --
        elif pygame_event.type in PYGAME_WINDOW_EVENTS:
            #
            nd_window_id: int = -1
            #
            if self.main_app.display is not None:
                #
                window_id: int
                window: Optional[ND_Window]
                for window_id, window in self.main_app.display.windows.items():
                    if window is not None:
                        nd_window_id = window_id
                        break
            #
            if pygame_event.type == pygame.WINDOWCLOSE:
                #
                return nd_event.ND_EventWindowClose(window_id=nd_window_id)
            #
            # elif pygame_event.type == pygame.WINDOWEVENT_SHOWN:
            #     #
            #     return nd_event.ND_EventWindowShown(nd_window_id)

            # elif pygame_event.type == pygame.WINDOWEVENT_HIDDEN:
            #     #
            #     return nd_event.ND_EventWindowHidden(nd_window_id)

            elif pygame_event.type == pygame.VIDEORESIZE:
                #
                new_window_width: int = pygame_event.w  # width
                new_window_height: int = pygame_event.h  # height
                #
                return nd_event.ND_EventWindowResized(window_id=nd_window_id, w=new_window_width, h=new_window_height)
            #
            elif pygame_event.type == pygame.WINDOWMOVED:
                #
                new_window_x: int = pygame_event.x
                new_window_y: int = pygame_event.y
                #
                return nd_event.ND_EventWindowMoved(window_id=nd_window_id, x=new_window_x, y=new_window_y)
            #
            # elif pygame_event.type == pygame.WINDOWFOCUSGAINED:
            #     #
            #     return nd_event.ND_EventWindowFocusGained(nd_window_id)
            # #
            # elif pygame_event.type == pygame.WINDOWFOCUSLOST:
            #     #
            #     return nd_event.ND_EventWindowFocusLost(nd_window_id)

        # -- KEYBOARD EVENT --
        elif pygame_event.type == pygame.KEYDOWN:
            #
            if pygame_event.key in SDL_KEYCODES_TO_STR:
                #
                self.keys_pressed.add(SDL_KEYCODES_TO_STR[pygame_event.key])
                #
                return nd_event.ND_EventKeyDown(
                                    key=SDL_KEYCODES_TO_STR[pygame_event.key]
                                )
            #
            else:
                #
                return nd_event.ND_EventKeyDown()
        #
        elif pygame_event.type == pygame.KEYUP:
            #
            if pygame_event.key in SDL_KEYCODES_TO_STR:
                #
                self.keys_pressed.remove(SDL_KEYCODES_TO_STR[pygame_event.key])
                #
                return nd_event.ND_EventKeyUp(
                                    key=SDL_KEYCODES_TO_STR[pygame_event.key]
                                )
            #
            else:
                #
                return nd_event.ND_EventKeyUp()

        # -- MOUSE EVENT --
        elif pygame_event.type == pygame.MOUSEBUTTONDOWN:
            #
            return nd_event.ND_EventMouseButtonDown(
                                button_id=pygame_event.button,
                                x=pygame_event.pos[0],
                                y=pygame_event.pos[1]
            )
        #
        elif pygame_event.type == pygame.MOUSEBUTTONUP:
            #
            return nd_event.ND_EventMouseButtonUp(
                                button_id=pygame_event.button,
                                x=pygame_event.pos[0],
                                y=pygame_event.pos[1]
            )
        #
        elif pygame_event.type == pygame.MOUSEMOTION:
            #
            if pygame_event.rel[0] == 0 and pygame_event.rel[1] == 0:
                return nd_event.ND_EmptyEvent()
            #
            return nd_event.ND_EventMouseMotion(
                                x=pygame_event.pos[0],
                                y=pygame_event.pos[1],
                                rel_x=pygame_event.rel[0],
                                rel_y=pygame_event.rel[1]
            )
        #
        elif pygame_event.type == pygame.MOUSEWHEEL:
            #
            return nd_event.ND_EventMouseWheelScrolled(
                                scroll_x=pygame_event.x,
                                scroll_y=pygame_event.y
            )

        # If it is an unsupported event
        return nd_event.ND_EmptyEvent()


    #
    def get_mouse_position(self) -> ND_Point:
        #
        return ND_Point(*(pygame.mouse.get_pos()))


    #
    def get_global_mouse_position(self) -> ND_Point:
        #
        return ND_Point(*(pygame.mouse.get_pos()))



