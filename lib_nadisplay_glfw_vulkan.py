

from typing import Optional, Any, Callable, cast, Type
from threading import Lock

import os
import ctypes

import glfw  # type: ignore
import vulkan as vk  # type: ignore

from lib_nadisplay_rects import ND_Point
from lib_nadisplay_colors import ND_Transformations
from lib_nadisplay_colors import ND_Color
from lib_nadisplay import ND_MainApp, ND_Display, ND_Window, ND_Scene
from lib_nadisplay_glfw import get_display_info
from lib_nadisplay_vulkan import init_vulkan


#
class ND_Display_GLFW_VULKAN(ND_Display):

    #
    def __init__(self, main_app: ND_MainApp, WindowClass: Type[ND_Window]) -> None:
        #
        self.main_not_threading: bool = False
        self.events_thread_in_main_thread: bool = True
        self.display_thread_in_main_thread: bool = False
        #
        self.WindowClass: Type[ND_Window] = WindowClass
        #
        self.main_app: ND_MainApp = main_app
        #
        self.font_names: dict[str, str] = {}
        self.ttf_fonts: dict[str, dict[int, object]] = {}
        self.default_font: str = "FreeSans"
        #
        self.windows: dict[int, Optional[ND_Window]] = {}
        self.thread_create_window: Lock = Lock()
        #
        self.vulkan_instance: Optional[object] = None
        #
        self.shader_program: int = -1
        self.shader_program_textures: int = -1
        #


    #
    def get_time_msec(self) -> float:
        return glfw.get_time() * 1000.0


    #
    def wait_time_msec(self, delay_in_msec: float) -> None:
        glfw.wait_events_timeout(delay_in_msec / 1000.0)


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
    def init_display(self) -> None:

        if not glfw.init():
            raise Exception("GLFW can't be initialized")

        # Vulkan Initialization
        self.vulkan_instance = init_vulkan()

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
        glfw.terminate()


    #
    def add_font(self, font_path: str, font_name: str) -> None:
        #
        self.font_names[font_name] = font_path


    #
    def get_font(self, font: str, font_size: int) -> Optional[object]:
        #
        if font not in self.ttf_fonts:
            self.ttf_fonts[font] = {}
        #
        if font_size < 8:
            font_size = 8
        #
        if font_size not in self.ttf_fonts[font]:
            #
            font_path: str = self.font_names[font]
            #
            if (font_path.endswith(".ttf") or font_path.endswith(".otf")) and os.path.exists(font_path):
                # TODO
                pass
                # self.ttf_fonts[font][font_size] = object(font_path.encode(encoding="utf-8"), font_size)
            else:
                return None
        #
        return self.ttf_fonts[font][font_size]


    #
    def update_display(self) -> None:
        #
        for window in self.windows.values():
            #
            if window is not None:
                window.update_display()


    #
    def create_window(self, window_params: dict[str, Any], error_if_win_id_not_available: bool = False) -> int:
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
            del(self.windows[win_id])


#
class ND_Window_GLFW_VULKAN(ND_Window):
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
            infos: Optional[glfw._GLFWvidmode] = get_display_info()
            #
            if infos is not None:
                #
                screen_width: int = infos.w
                screen_height: int = infos.h
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
        self.glw_window: Optional[object] = None

        #
        self.glw_window = glfw.create_window(
                                    self.width,
                                    self.height,
                                    title,
                                    None,
                                    None
        )

        # TODO: vulkan instance



        # sdl_or_glfw_window_id is int and has been initialized to -1 in parent class
        self.sdl_or_glfw_window_id = id(self.glw_window)

        #
        self.next_texture_id: int = 0
        self.sdl_textures: dict[int, object] = {}
        self.sdl_textures_surfaces: dict[int, object] = {}
        self.mutex_sdl_textures: Lock = Lock()


    #
    def destroy_window(self) -> None:
        #
        for texture_id in self.sdl_textures:
            #
            self.destroy_prepared_texture(texture_id)

        # vulkan
        # TODO
        pass


    #
    def set_title(self, new_title: str) -> None:
        # TODO
        return


    #
    def set_position(self, new_x: int, new_y: int) -> None:
        # TODO
        return


    #
    def set_size(self, new_width: int, new_height: int) -> None:
        # TODO
        return


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

        # TODO
        return


    #
    def blit_texture(self, texture, dst_rect) -> None:
        # TODO
        pass


    #
    def prepare_text_to_render(self, text: str, color: ND_Color, font_size: int, font_name: Optional[str] = None) -> int:

        #
        if font_name is None:
            font_name = self.display.default_font

        # Get font
        font: Optional[object] = self.display.get_font(font_name, font_size)

        # Do nothing if not font got
        if font is None:
            return -1

        # Create rendered text surface
        # surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color)
        surface = None
        # TODO
        pass

        # Convert the SDL surface into an OpenGL texture
        texture = self._create_vulkan_texture_from_surface(surface)

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.sdl_textures[texture_id] = texture
            self.sdl_textures_surfaces[texture_id] = surface

        #
        return texture_id


    #
    def draw_text(self, txt: str, x: int, y: int, font_size: int, font_color: ND_Color, font_name: Optional[str] = None) -> None:
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        # TODO
        #
        return


    #
    def prepare_image_to_render(self, img_path: str) -> int:

        # Chargement de l'image
        # image_surface = sdlimage.IMG_Load(img_path.encode('utf-8'))
        image_surface = None
        # TODO
        pass

        # Si l'image n'a pas bien été chargée, erreur est abandon
        if not image_surface:
            print(f"Failed to load image: {img_path}")
            return -1

        # Sinon, on convertit l'image en une texture
        texture = self._create_vulkan_texture_from_surface(image_surface)

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.sdl_textures[texture_id] = texture
            self.sdl_textures_surfaces[texture_id] = image_surface

        #
        return texture_id


    #
    def render_prepared_texture(self, texture_id: int, x: int, y: int, width: int, height: int, transformations: ND_Transformations = ND_Transformations()) -> None:

        #
        if texture_id not in self.sdl_textures:
            return

        # TODO
        pass


    #
    def get_prepared_texture_size(self, texture_id: int) -> ND_Point:
        #
        if texture_id not in self.sdl_textures:
            #
            return ND_Point(0, 0)
        #
        else:
            #
            w_c, h_c = ctypes.c_int(0), ctypes.c_int(0)
            # TODO
            # sdl2.SDL_QueryTexture(self.sdl_textures[texture_id], None, None, ctypes.byref(w), ctypes.byref(h))
            #
            w: int = w_c.value
            h: int = h_c.value
            #
            return ND_Point(w, h)


    #
    def destroy_prepared_texture(self, texture_id: int) -> None:
        with self.mutex_sdl_textures:
            if texture_id in self.sdl_textures:
                # TODO
                pass
                del self.sdl_textures[texture_id]


    #
    def _create_vulkan_texture_from_surface(self, surface) -> int:

        # TODO
        pass

        return -1


    #
    def draw_pixel(self, x: int, y: int, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, outline_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, filled_color: ND_Color) -> None:

        # TODO
        pass


    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], outline_color: ND_Color) -> None:

        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        # n: int = len(x_coords)

        # TODO
        pass


    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        # n: int = len(x_coords)

        # TODO
        pass


    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:
        #
        if texture_id not in self.sdl_textures:
            return
        #
        # n: int = len(x_coords)

        # TODO
        pass


    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < nb_interpolations:
            return

        # TODO
        pass


    #
    def enable_area_drawing_constraints(self, x: int, y: int, width: int, height: int) -> None:
        # TODO
        pass


    #
    def disable_area_drawing_constraints(self) -> None:
        # TODO
        pass


    #
    def update_display(self) -> None:

        #
        # sdl2.SDL_GL_MakeCurrent(self.sdl_window, self.gl_context)
        # TODO
        pass

        #
        if self.state is not None and self.state in self.display_states:
            #
            if self.display_states[self.state] is not None:
                #
                display_fn: Callable[[ND_Window], None] = cast(Callable[[ND_Window], None], self.display_states[self.state])
                display_fn(self)

        #
        scene: ND_Scene
        for scene in self.scenes.values():
            scene.render()

        #
        # sdl2.SDL_RenderPresent(self.renderer)
        # TODO
        pass

