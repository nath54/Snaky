

from typing import Optional, Any, Callable, cast, Type
from threading import Lock

import os


import sdl2  # type: ignore
import sdl2.sdlttf as sdlttf  # type: ignore
import sdl2.sdlimage as sdlimage  # type: ignore
import sdl2.sdlgfx as sdlgfx  # type: ignore
import ctypes

from ctypes import c_int, byref

from lib_nadisplay_colors import ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Rect, ND_Point
from lib_nadisplay import ND_MainApp, ND_Display, ND_Window, ND_Scene
from lib_nadisplay_sdl import to_sdl_color, get_display_info


#
class ND_Display_SDL_SDLGFX(ND_Display):

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
        self.ttf_fonts: dict[str, dict[int, sdlttf.TTF_OpenFont]] = {}
        self.default_font: str = "FreeSans"
        #
        self.windows: dict[int, Optional[ND_Window]] = {}
        self.thread_create_window: Lock = Lock()
        #
        self.shader_program: int = -1
        self.shader_program_textures: int = -1


    #
    def get_time_msec(self) -> float:
        return sdl2.SDL_GetTicks()


    #
    def wait_time_msec(self, delay_in_msec: float) -> None:
        sdl2.SDL_Delay(int(delay_in_msec))


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
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        sdlttf.TTF_Init()

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

        # Destroy fonts
        font: str
        font_size: int
        ttf_fonts_keys: list[str] = list(self.ttf_fonts.keys())
        for font in ttf_fonts_keys:
            font_sizes_keys: list[int] = list(self.ttf_fonts[font].keys())
            for font_size in font_sizes_keys:
                sdlttf.TTF_CloseFont(self.ttf_fonts[font][font_size])
                del self.ttf_fonts[font][font_size]

        #
        sdlttf.TTF_Quit()
        sdl2.SDL_Quit()


    #
    def add_font(self, font_path: str, font_name: str) -> None:
        #
        self.font_names[font_name] = font_path


    #
    def get_font(self, font: str, font_size: int) -> Optional[sdlttf.TTF_OpenFont]:
        #
        if font not in self.ttf_fonts:
            self.ttf_fonts[font] = {}
        #
        if font not in self.font_names:
            return None
        #
        if font_size < 8:
            font_size = 8
        #
        if font_size not in self.ttf_fonts[font]:
            #
            font_path: str = self.font_names[font]
            #
            if (font_path.endswith(".ttf") or font_path.endswith(".otf")) and os.path.exists(font_path):

                self.ttf_fonts[font][font_size] = sdlttf.TTF_OpenFont(font_path.encode(encoding="utf-8"), font_size)
            else:
                return None
        #
        return self.ttf_fonts[font][font_size]


    #
    def update_display(self) -> None:
        #
        for window in list(self.windows.values()):
            #
            if window is not None:
                window.update_display()


    #
    def get_focused_window_id(self) -> int:
        # Get the focused window
        focused_window: Optional[object] = sdl2.SDL_GetKeyboardFocus()

        # Check if a window is focused
        if focused_window is not None:
            # Get the window ID
            window_id: int = sdl2.SDL_GetWindowID(focused_window)
            return window_id
        else:
            return -1  # Indicate that no window is focused


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
class ND_Window_SDL_SDLGFX(ND_Window):
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
        self.clip_rect_stack: list[sdl2.SDL_Rect] = []

        #
        if isinstance(size, str):
            #
            infos: Optional[sdl2.SDL_DisplayMode] = get_display_info()
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
        self.sdl_window: Optional[sdl2.SDL_Window] = None

        #
        self.sdl_window = sdl2.SDL_CreateWindow(
                                    title.encode('utf-8'),
                                    sdl2.SDL_WINDOWPOS_CENTERED,
                                    sdl2.SDL_WINDOWPOS_CENTERED,
                                    self.width,
                                    self.height,
                                    sdl2.SDL_WINDOW_RESIZABLE
        )

        #
        x_c, y_c, w_c, h_c = ctypes.c_int(0), ctypes.c_int(0), ctypes.c_int(0), ctypes.c_int(0)
        sdl2.SDL_GetWindowPosition(self.sdl_window, ctypes.byref(x_c), ctypes.byref(y_c))
        sdl2.SDL_GetWindowSize(self.sdl_window, ctypes.byref(w_c), ctypes.byref(h_c))
        #
        self.x, self.y, self.width, self.height = x_c.value, y_c.value, w_c.value, h_c.value
        #
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)

        #
        self.renderer: sdl2.SDL_Renderer = sdl2.SDL_CreateRenderer(self.sdl_window, -1, sdl2.SDL_RENDERER_ACCELERATED)

        # sdl_or_glfw_window_id is int and has been initialized to -1 in parent class
        self.sdl_or_glfw_window_id = sdl2.SDL_GetWindowID(self.sdl_window)

        #
        self.next_texture_id: int = 1
        self.textures_dimensions: dict[int, tuple[int, int]] = {}
        self.texture_moduled: set[int] = set()
        self.sdl_textures: dict[int, object] = {}
        self.mutex_sdl_textures: Lock = Lock()
        #
        self.prepared_font_textures: dict[str, int] = {}


    #
    def destroy_window(self) -> None:
        #
        self.display.main_app.delete_mainloop_fns_queue(f"window_{self.window_id}")
        #
        for texture_id in list(self.sdl_textures.keys()):
            #
            self.destroy_prepared_texture(texture_id)

        #
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.sdl_window)


    #
    def set_title(self, new_title: str) -> None:
        #
        sdl2.SDL_SetWindowTitle(self.sdl_window, new_title.encode('utf-8'))


    #
    def set_position(self, new_x: int, new_y: int) -> None:
        #
        sdl2.SDL_SetWindowPosition(self.sdl_window, new_x, new_y)
        #
        self.update_position(new_x, new_y)


    #
    def set_size(self, new_width: int, new_height: int) -> None:
        #
        sdl2.SDL_SetWindowSize(self.sdl_window, new_width, new_height)
        #
        self.update_size(new_width, new_height)
        #
        self.update_scene_sizes()


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

        if mode == 0:
            sdl2.SDL_SetWindowFullscreen(self.sdl_window, 0)
        elif mode == 1:
            sdl2.SDL_SetWindowFullscreen(self.sdl_window, sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
        elif mode == 2:
            sdl2.SDL_SetWindowFullscreen(self.sdl_window, sdl2.SDL_WINDOW_FULLSCREEN)


    #
    def blit_texture(self, texture, dst_rect) -> None:
        # Copy the texture into the window display buffer thanks to the renderer
        sdl2.SDL_RenderCopy(self.renderer, texture, None, dst_rect)


    #
    def prepare_text_to_render(self, text: str, color: ND_Color, font_size: int, font_name: Optional[str] = None) -> int:
        #
        return -1
        #
        if font_name is None:
            font_name = self.display.default_font

        # Get font
        font: Optional[sdlttf.TTF_OpenFont] = self.display.get_font(font_name, font_size)

        # Do nothing if not font got
        if font is None:
            return -1

        # Create rendered text surface
        surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), to_sdl_color(color))
        #
        if not surface:
            print(f"Warning error : sdlttf.TTF_RenderText_Blended couldn't not create a surface for the font : {font} and the text {text} !")
            return -1

        width: int = surface.contents.w
        height: int = surface.contents.h

        # Convert surface into texture
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)
        #
        if not texture:
            print(f"Warning error : sdl2.SDL_CreateTextureFromSurface couldn't not create a texture for the surface : {surface} that was rendered with the font {font} and the text {text} !")
            return -1

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.sdl_textures[texture_id] = texture
            self.textures_dimensions[texture_id] = (width, height)

        #
        return texture_id


    #
    def prepare_image_to_render(self, img_path: str) -> int:

        #
        # return -1

        # Chargement de l'image
        image_surface = sdlimage.IMG_Load(img_path.encode('utf-8'))

        # Si l'image n'a pas bien été chargée, erreur est abandon
        if not image_surface:
            print(f"Failed to load image: {img_path}")
            print(sdl2.SDL_GetError().decode())
            return -1

        #
        width: int = image_surface.contents.w
        height: int = image_surface.contents.h

        # Sinon, on convertit l'image en une texture

        #
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, image_surface)
        sdl2.SDL_FreeSurface(image_surface)

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.sdl_textures[texture_id] = texture
            self.textures_dimensions[texture_id] = (width, height)

        #
        return texture_id


    #
    def render_prepared_texture(self, texture_id: int, x: int, y: int, width: int, height: int, transformations: ND_Transformations = ND_Transformations()) -> None:

        #
        if texture_id not in self.sdl_textures:
            return

        #
        if transformations.color_modulation is not None:
            #
            cm: ND_Color = transformations.color_modulation
            #
            sdl2.SDL_SetTextureColorMod(self.sdl_textures[texture_id], cm.r, cm.g, cm.b)
            sdl2.SDL_SetTextureAlphaMod(self.sdl_textures[texture_id], cm.a)
            #
            self.texture_moduled.add(texture_id)
        #
        elif texture_id in self.texture_moduled:
            #
            sdl2.SDL_SetTextureColorMod(self.sdl_textures[texture_id], 255, 255, 255)
            sdl2.SDL_SetTextureAlphaMod(self.sdl_textures[texture_id], 255)
            #
            self.texture_moduled.remove(texture_id)

        #
        if transformations.rotation is not None or transformations.flip_x or transformations.flip_y:

            #
            angle: float = transformations.rotation if transformations.rotation is not None else 0

            #
            flip_tag: sdl2.SDL_RendererFlip = sdl2.SDL_FLIP_NONE
            #
            if transformations.flip_x:
                flip_tag |= sdl2.SDL_FLIP_HORIZONTAL
            if transformations.flip_y:
                flip_tag |= sdl2.SDL_FLIP_VERTICAL


            # Copy the texture into the window display buffer thanks to the renderer
            sdl2.SDL_RenderCopyEx(
                        self.renderer,
                        self.sdl_textures[texture_id],
                        None,
                        sdl2.SDL_Rect(x, y, width, height),
                        angle,
                        None,
                        flip_tag
            )

        else:
            # Copy the texture into the window display buffer thanks to the renderer
            sdl2.SDL_RenderCopy(self.renderer, self.sdl_textures[texture_id], None, sdl2.SDL_Rect(x, y, width, height))


    #
    def render_part_of_prepared_texture(self, texture_id: int, x: int, y: int, w: int, h: int, src_x: int, src_y: int, src_w: int, src_h: int, transformations: ND_Transformations = ND_Transformations()) -> None:

        #
        if texture_id not in self.sdl_textures:
            return

        #
        if transformations.color_modulation is not None:
            #
            cm: ND_Color = transformations.color_modulation
            #
            sdl2.SDL_SetTextureColorMod(self.sdl_textures[texture_id], cm.r, cm.g, cm.b)
            sdl2.SDL_SetTextureAlphaMod(self.sdl_textures[texture_id], cm.a)
            #
            self.texture_moduled.add(texture_id)
        #
        elif texture_id in self.texture_moduled:
            #
            sdl2.SDL_SetTextureColorMod(self.sdl_textures[texture_id], 255, 255, 255)
            sdl2.SDL_SetTextureAlphaMod(self.sdl_textures[texture_id], 255)
            #
            self.texture_moduled.remove(texture_id)

        #
        if transformations.rotation is not None or transformations.flip_x or transformations.flip_y:

            #
            angle: float = transformations.rotation if transformations.rotation is not None else 0

            #
            flip_tag: sdl2.SDL_RendererFlip = sdl2.SDL_FLIP_NONE
            #
            if transformations.flip_x:
                flip_tag |= sdl2.SDL_FLIP_HORIZONTAL
            if transformations.flip_y:
                flip_tag |= sdl2.SDL_FLIP_VERTICAL

            dcx: int = 0
            dcy: int = 0
            new_w, new_h = w, h  # Default dimensions

            if angle == 90:
                new_w, new_h = h, w
                dcx = (w - h) // 2
                dcy = (h - w) // 2
            elif angle == 270:
                new_w, new_h = h, w
                dcx = (w - h) // 2
                dcy = (h - w) // 2


            # Copy the texture into the window display buffer thanks to the renderer
            sdl2.SDL_RenderCopyEx(
                        self.renderer,
                        self.sdl_textures[texture_id],
                        sdl2.SDL_Rect(src_x, src_y, src_w, src_h),
                        sdl2.SDL_Rect(x+dcx, y+dcy, new_w, new_h),
                        angle,
                        None,  # Centre de la rotation
                        flip_tag
            )

        else:

            # Copy the texture into the window display buffer thanks to the renderer
            sdl2.SDL_RenderCopy(self.renderer, self.sdl_textures[texture_id], sdl2.SDL_Rect(src_x, src_y, src_w, src_h), sdl2.SDL_Rect(x, y, w, h))


    #
    def get_prepared_texture_size(self, texture_id: int) -> ND_Point:
        #
        if texture_id not in self.textures_dimensions:
            return ND_Point(0, 0)
        #
        return ND_Point(*self.textures_dimensions[texture_id])


    #
    def destroy_prepared_texture(self, texture_id: int) -> None:
        with self.mutex_sdl_textures:
            if texture_id in self.sdl_textures:
                sdl2.SDL_DestroyTexture(self.sdl_textures[texture_id])
                del self.sdl_textures[texture_id]
                del self.textures_dimensions[texture_id]


    #
    def draw_text(self, txt: str, x: int, y: int, font_size: int, font_color: ND_Color, font_name: Optional[str] = None) -> None:
        #
        # return  # There are other parts of the code that cause malloc / realloc errors, because still getting without rendering any text
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        if not txt:
            return

        #
        font: Optional[sdlttf.TTF_OpenFont] = self.display.get_font(font_name, font_size)

        #
        if not font:
            return

        #
        # tid: str = f"{txt}_|||_{font}_|||_{font_size}_|||_{font_color}"
        # #
        # if tid not in self.prepared_font_textures:
        #     self.prepared_font_textures[tid] = self.prepare_text_to_render(text=txt, color=font_color, font_name=font, font_size=font_size)
        # #
        # tsize: ND_Point = self.get_prepared_texture_size(self.prepared_font_textures[tid])
        # self.render_prepared_texture(self.prepared_font_textures[tid], x, y, tsize.x, tsize.y)

        # TODO: render directly text instead of creating texture, and etc...
        surface: sdl2.SDL_Surface = sdlttf.TTF_RenderUTF8_Blended(font, txt.encode("utf-8"), to_sdl_color(font_color))
        #
        if not surface:
            print(f"Warning error : sdlttf.TTF_RenderUTF8_Blended couldn't not create a surface for the font : {font} and the text {txt} !")
            return
        #
        width: int = surface.contents.w
        height: int = surface.contents.h
        #
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)
        #
        if not texture:
            print(f"Warning error : sdl2.SDL_CreateTextureFromSurface couldn't not create a texture for the surface : {surface} that was rendered with the font {font_name} and the text {txt} !")
            return
        #
        sdl2.SDL_RenderCopy(self.renderer, texture, None, sdl2.SDL_Rect(x, y, width, height))


    #
    def get_text_size_with_font(self, txt: str, font_size: int, font_name: Optional[str] = None) -> ND_Point:
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        if not txt:
            return ND_Point(0, 0)

        #
        font: Optional[sdlttf.TTF_OpenFont] = self.display.get_font(font_name, font_size)

        #
        if font is None:
            # print(f"DEBUG ERROR | error : no fonts found with font_name={font_name} and font_size={font_size} ")
            return ND_Point(-1, -1)
        #
        if sdlttf.TTF_WasInit() == 0:
            print("DEBUG ERROR | SDL_ttf is not initialized")
            return ND_Point(-1, -1)
        #
        text_w, text_h = c_int(0), c_int(0)
        sdlttf.TTF_SizeUTF8(font, txt.encode("utf-8"), byref(text_w), byref(text_h))
        text_size = [x.value for x in (text_w, text_h)]
        #
        return ND_Point(*text_size)


    #
    def get_count_of_renderable_chars_fitting_given_width(self, txt: str, given_width: int, font_size: int, font_name: Optional[str] = None) -> tuple[int, int]:
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        if not txt:
            return 0, 0

        #
        font: Optional[sdlttf.TTF_OpenFont] = self.display.get_font(font_name, font_size)

        #
        if font is None:
            # print(f"DEBUG ERROR | error : no fonts found with font_name={font_name} and font_size={font_size} ")
            return -1, -1

        #
        if sdlttf.TTF_WasInit() == 0:
            # print("DEBUG ERROR | SDL_ttf is not initialized")
            return (-1, -1)
        #
        extent, count = c_int(0), c_int(0)
        sdlttf.TTF_MeasureUTF8(font, txt.encode("utf-8"), byref(extent), byref(count))
        return extent.value, count.value


    #
    def draw_pixel(self, x: int, y: int, color: ND_Color) -> None:
        #
        sdlgfx.pixelRGBA(self.renderer, x, y, color.r, color.g, color.b, color.a)


    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:
        #
        sdlgfx.hlineRGBA(self.renderer, x1, x2, y, color.r, color.g, color.b, color.a)


    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        sdlgfx.vlineRGBA(self.renderer, x, y1, y2, color.r, color.g, color.b, color.a)


    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        sdlgfx.lineRGBA(self.renderer, x1, x2, y1, y2, color.r, color.g, color.b, color.a)


    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:
        #
        sdlgfx.thickLineRGBA(self.renderer, x1, y1, x2, y2, line_thickness, color.r, color.g, color.b, color.a)


    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color) -> None:

        # Draw filled rounded rectangle
        sdlgfx.roundedBoxRGBA(self.renderer, x, y, x + width, y + height, radius, fill_color.r, fill_color.g, fill_color.b, fill_color.a)

        # Draw border with rounded corners
        sdlgfx.roundedRectangleRGBA(self.renderer, x, y, x + width, y + height, radius, border_color.r, border_color.g, border_color.b, border_color.a)


    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, line_color: ND_Color) -> None:
        #
        sdlgfx.rectangleRGBA(self.renderer, x, y, x+width, y+height, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, fill_color: ND_Color) -> None:
        #
        sdlgfx.boxRGBA(self.renderer, x, y, x+width, y+height, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, line_color: ND_Color) -> None:
        #
        sdlgfx.CircleRGBA(self.renderer, x, y, radius, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color) -> None:
        #
        sdlgfx.filledCircleRGBA(self.renderer, x, y, radius, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, line_color: ND_Color) -> None:
        #
        sdlgfx.ellipseRGBA(self.renderer, x, y, rx, ry, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:
        #
        sdlgfx.filledEllipseRGBA(self.renderer, x, y, rx, ry, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color) -> None:
        #
        sdlgfx.arcRGBA(self.renderer, x, y, radius, angle_start, angle_end, color.r, color.g, color.b, color.a)


    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, line_color: ND_Color) -> None:
        #
        sdlgfx.pieRGBA(self.renderer, x, y, radius, angle_start, angle_end, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:
        #
        sdlgfx.filledPieRGBA(self.renderer, x, y, radius, angle_start, angle_end, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, line_color: ND_Color) -> None:
        #
        sdlgfx.trigonRGBA(self.renderer, x1, y1, x2, y2, x3, y3, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: ND_Color) -> None:
        #
        sdlgfx.filledTrigonRGBA(self.renderer, x1, y1, x2, y2, x3, y3, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color) -> None:

        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        #
        for i in range(n):
            #
            x1: int = x_coords[i]
            x2: int = x_coords[(i+1)%n]
            y1: int = y_coords[i]
            y2: int = y_coords[(i+1)%n]
            #
            self.draw_line(x1, y1, x2, y2, line_color)
        #
        # sdlgfx.polygonRGBA(self.renderer, vx, vy, n, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        #
        vx: object = (ctypes.c_int16 * n)(*x_coords)
        vy: object = (ctypes.c_int16 * n)(*y_coords)

        #
        sdlgfx.polygonRGBA(self.renderer, vx, vy, n, fill_color.r, fill_color.g, fill_color.b, fill_color.a)


    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:
        #
        if texture_id not in self.sdl_textures:
            return
        #
        n: int = len(x_coords)
        vx: object = (ctypes.c_int16 * n)(*x_coords)
        vy: object = (ctypes.c_int16 * n)(*y_coords)

        #
        sdlgfx.texturedPolygon(self.renderer, vx, vy, n, self.sdl_textures[texture_id], texture_dx, texture_dy)


    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < nb_interpolations:
            return

        #
        n: int = len(x_coords)
        vx: object = (ctypes.c_int16 * n)(*x_coords)
        vy: object = (ctypes.c_int16 * n)(*y_coords)

        #
        sdlgfx.bezierRGBA(self.renderer, vx, vy, n, nb_interpolations, line_color.r, line_color.g, line_color.b, line_color.a)


    #
    def enable_area_drawing_constraints(self, x: int, y: int, width: int, height: int) -> None:

        # Define a clipping area
        clip_rect: sdl2.SDL_Rect = sdl2.SDL_Rect(x, y, width, height)

        #
        self.clip_rect_stack.append(clip_rect)

        # Enable clipping area
        sdl2.SDL_RenderSetClipRect(self.renderer, clip_rect)


    #
    def disable_area_drawing_constraints(self) -> None:

        #
        self.clip_rect_stack.pop(-1)

        #
        if not self.clip_rect_stack:

            # Reset clipping (disable clipping by passing None)
            sdl2.SDL_RenderSetClipRect(self.renderer, None)

        else:

            # If there was another clip rect
            sdl2.SDL_RenderSetClipRect(self.renderer, self.clip_rect_stack[-1])


    #
    def update_display(self) -> None:

        #
        # print(f"DEBUG | update window {self.window_id} that has current state {self.state}.")

        #
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)

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
        sdl2.SDL_RenderPresent(self.renderer)

