

from typing import Optional, Any, Callable, cast, Type
from threading import Lock

import os

import numpy as np  # type: ignore

import sdl2  # type: ignore
import sdl2.sdlttf as sdlttf  # type: ignore
import sdl2.sdlimage as sdlimage  # type: ignore

# To improve speed for non development code:
#
#   import OpenGL
#   OpenGL.ERROR_LCHECKING = False
#   OpenGL.ERROR_LOGGING = False

import OpenGL.GL as gl  # type: ignore
# from OpenGL.GLUT import glutInit, glutCreateWindow, glutInitDisplayMode, GLUT_RGB, glutInitWindowSize

import ctypes

from lib_nadisplay_colors import ND_Color
from lib_nadisplay_colors import ND_Transformations
from lib_nadisplay_rects import ND_Rect, ND_Point
from lib_nadisplay import ND_MainApp, ND_Display, ND_Window, ND_Scene
from lib_nadisplay_sdl import to_sdl_color, get_display_info
from lib_nadisplay_opengl import create_and_validate_gl_shader_program


#
VERTEX_SHADER_SRC: str = """
    #version 330 core
    layout (location = 0) in vec2 position;
    layout (location = 1) in vec4 color;
    out vec4 frag_color;
    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
        frag_color = color;
    }
"""

#
FRAGMENT_SHADER_SRC: str = """
    #version 330 core
    in vec4 frag_color;
    out vec4 out_color;
    void main() {
        out_color = frag_color;

    }
"""

#
VERTEX_SHADER_TEXTURES_SRC: str = """
    #version 330 core
    layout (location = 0) in vec2 position;  // Position of the vertex
    layout (location = 1) in vec2 texCoord;  // Texture coordinates
    out vec2 fragTexCoord;  // Output to fragment shader

    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
        fragTexCoord = texCoord;  // Pass texture coordinates to fragment shader
    }
"""

#
FRAGMENT_SHADER_TEXTURES_SRC: str = """
    #version 330 core
    in vec2 fragTexCoord;  // Input from vertex shader
    out vec4 outColor;     // Output color
    uniform sampler2D textureSampler;  // The texture sampler

    void main() {
        outColor = texture(textureSampler, fragTexCoord);  // Sample the texture
    }
"""


#
class ND_Display_SDL_OPENGL(ND_Display):

    #
    def __init__(self, main_app: ND_MainApp, WindowClass: Type[ND_Window]) -> None:
        #
        self.main_not_threading: bool = False
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
    def init_display(self) -> None:

        # Initialize SDL2 and TTF
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        sdlttf.TTF_Init()

        # Request an OpenGL 3.3 context
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK, sdl2.SDL_GL_CONTEXT_PROFILE_CORE)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)

        # Load system fonts
        self.load_system_fonts()


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
        for window in self.windows.values():
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
class ND_Window_SDL_OPENGL(ND_Window):
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
        self.sdl_window: sdl2.SDL_Window = sdl2.SDL_CreateWindow(
                                    title.encode('utf-8'),
                                    sdl2.SDL_WINDOWPOS_CENTERED,
                                    sdl2.SDL_WINDOWPOS_CENTERED,
                                    self.width,
                                    self.height,
                                    sdl2.SDL_WINDOW_OPENGL
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
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK, sdl2.SDL_GL_CONTEXT_PROFILE_CORE)
        self.gl_context: Optional[sdl2.SDL_GL_Context] = sdl2.SDL_GL_CreateContext(self.sdl_window)
        sdl2.SDL_GL_SetSwapInterval(1)  # Enable vsync
        gl.glDisable(gl.GL_DEPTH_TEST)  # Disable depth test
        gl.glDisable(gl.GL_CULL_FACE)   #

        if not self.gl_context:
            print(f"ERROR: GL context is invalid : {self.gl_context} !!!")

        # sdl_or_glfw_window_id is int and has been initialized to -1 in parent class
        self.sdl_or_glfw_window_id = sdl2.SDL_GetWindowID(self.sdl_window)

        #
        self.next_texture_id: int = 0
        self.textures_dimensions: dict[int, tuple[int, int]] = {}
        self.gl_textures: dict[int, int] = {}
        self.sdl_textures_surfaces: dict[int, object] = {}
        self.mutex_sdl_textures: Lock = Lock()
        #
        self.prepared_font_textures: dict[str, int] = {}
        #


        # Compile shaders and create a program
        self.shader_program: int = create_and_validate_gl_shader_program(
                                    VERTEX_SHADER_SRC, FRAGMENT_SHADER_SRC)

        # Compile shaders and create a program for textures
        self.shader_program_textures: int = create_and_validate_gl_shader_program(
                                            VERTEX_SHADER_TEXTURES_SRC, FRAGMENT_SHADER_TEXTURES_SRC)


    #
    def destroy_window(self) -> None:
        #
        for texture_id in self.gl_textures:
            #
            self.destroy_prepared_texture(texture_id)

        #
        sdl2.SDL_GL_DeleteContext(self.gl_context)
        sdl2.SDL_DestroyWindow(self.sdl_window)


    #
    def add_display_state(self, state: str, state_display_function: Callable, erase_if_state_already_exists: bool = False) -> None:
        #
        if (state not in self.display_states) or (state in self.display_states and erase_if_state_already_exists):
            self.display_states[state] = state_display_function


    #
    def remove_display_state(self, state: str) -> None:
        #
        if state in self.display_states:
            del self.display_states[state]


    #
    def set_title(self, new_title: str) -> None:
        #
        sdl2.SDL_SetWindowTitle(self.sdl_window, new_title.encode('utf-8'))


    #
    def set_position(self, new_x: int, new_y: int) -> None:
        #
        sdl2.SDL_SetWindowPosition(self.sdl_window, new_x, new_y)


    #
    def set_size(self, new_width: int, new_height: int) -> None:
        #
        sdl2.SDL_SetWindowSize(self.sdl_window, new_width, new_height)


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
    def blit_texture(self, texture_id: int, dst_rect: ND_Rect) -> None:
        """
        Renders a 2D texture onto a quad using VBOs and a shader program.

        :param texture_id: texture ID.
        :param dst_rect: Destination rectangle where the texture will be drawn (x, y, width, height).
        """

        if texture_id not in self.gl_textures:
            return

        if self.shader_program_textures <= 0:
            print("Error: Shader program for textures hasn't been initialized !")
            return

        # Vertex data for the textured quad (x, y, u, v)
        vertices = np.array([
            # Position      # Texture coordinates
            dst_rect.x, dst_rect.y,            0.0, 0.0,  # Bottom-left
            dst_rect.x + dst_rect.w, dst_rect.y,            1.0, 0.0,  # Bottom-right
            dst_rect.x + dst_rect.w, dst_rect.y + dst_rect.h, 1.0, 1.0,  # Top-right
            dst_rect.x, dst_rect.y + dst_rect.h,            0.0, 1.0   # Top-left
        ], dtype=np.float32)

        # Create VBO for the vertices
        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        # Create the EBO (Element Buffer Object) to define the indices of the quad
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)  # Two triangles
        EBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, EBO)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

        # Use the shader program (ensure it has been set up beforehand)
        gl.glUseProgram(self.shader_program_textures)

        # Enable the vertex attributes
        # Position attribute
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 4 * 4, ctypes.c_void_p(0))  # Position is in the first 2 floats (x, y)

        # Texture coordinate attribute
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, False, 4 * 4, ctypes.c_void_p(2 * 4))  # TexCoord is in the next 2 floats (u, v)

        # Bind the texture
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.gl_textures[texture_id])

        # Set the texture sampler to use texture unit 0
        gl.glUniform1i(gl.glGetUniformLocation(self.shader_program_textures, "textureSampler"), 0)

        # Draw the textured quad using the indices
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, ctypes.c_void_p(0))

        # Cleanup: Unbind VBO, EBO, and texture
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        # Delete the buffers after use
        gl.glDeleteBuffers(1, [VBO])
        gl.glDeleteBuffers(1, [EBO])


    #
    def prepare_text_to_render(self, text: str, color: ND_Color, font_size: int, font_name: Optional[str] = None) -> int:

        #
        if font_name is None:
            font_name = self.display.default_font

        # Get font
        font: Optional[sdlttf.TTF_OpenFont] = self.display.get_font(font_name, font_size)

        # Do nothing if not font got
        if font is None:
            return -1

        #
        color_sdl: sdl2.SDL_Color = to_sdl_color(color)

        # Create rendered text surface
        surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color_sdl)

        # Convert the SDL surface into an OpenGL texture
        texture_id: int = self._create_opengl_texture_from_surface(surface)

        #
        return texture_id


    #
    def prepare_image_to_render(self, img_path: str) -> int:

        # Chargement de l'image
        image_surface = sdlimage.IMG_Load(img_path.encode('utf-8'))

        # Si l'image n'a pas bien été chargée, erreur est abandon
        if not image_surface:
            print(f"Failed to load image: {img_path}")
            return -1

        # Convert the SDL surface into an OpenGL texture
        texture_id: int = self._create_opengl_texture_from_surface(image_surface)

        #
        return texture_id


    #
    def render_prepared_texture(self, texture_id: int, x: int, y: int, width: int, height, transformations: ND_Transformations = ND_Transformations()) -> None:

        #
        if texture_id not in self.gl_textures:
            return

        #
        self.blit_texture(texture_id, ND_Rect(x, y, width, height))


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
            if texture_id in self.gl_textures:
                gl.glDeleteTextures(1, [self.gl_textures[texture_id]])
                sdl2.SDL_FreeSurface(self.sdl_textures_surfaces[texture_id])
                del self.sdl_textures_surfaces[texture_id]
                del self.gl_textures[texture_id]


    #
    def _create_opengl_texture_from_surface(self, surface: sdl2.SDL_Surface) -> int:
        # Generate OpenGL texture
        gl_texture_id: int = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, gl_texture_id)

        width = surface.contents.w
        height = surface.contents.h

        # Convert SDL surface into a format OpenGL can use (RGBA)
        surface_pixels = ctypes.cast(surface.contents.pixels, ctypes.POINTER(ctypes.c_ubyte))

        # Upload the pixel data from the SDL_Surface to the OpenGL texture
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, surface_pixels)

        # Set texture parameters
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        # Generate a unique texture ID
        texture_id: int = -1
        with self.mutex_sdl_textures:
            texture_id = self.next_texture_id
            self.next_texture_id += 1

            # Store both OpenGL and SDL textures
            self.gl_textures[texture_id] = gl_texture_id
            self.sdl_textures_surfaces[texture_id] = surface
            self.textures_dimensions[texture_id] = (width, height)

        return texture_id


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

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertex_data: np.ndarray = np.array([
            # Position (x, y)    ND_Color (r, g, b, a)
            x, y,                color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0
        ], dtype=np.float32)

        # Create and bind the VBO
        VBO: int = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

        # Use the shader program
        gl.glUseProgram(self.shader_program)

        # Set vertex attributes
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        # Draw the point
        gl.glDrawArrays(gl.GL_POINTS, 0, 1)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertices = np.array([
            # Position        ND_Color
            x1, y, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x2, y, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINES, 0, 2)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertices = np.array([
            # Position         ND_Color
            x, y1, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x, y2, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINES, 0, 2)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        #
        vertices = np.array([
            # Position         ND_Color
            x1, y1, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x2, y2, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINES, 0, 2)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        #
        dx = x2 - x1
        dy = y2 - y1
        length = np.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        # Perpendicular vector to the line
        nx = -dy / length
        ny = dx / length
        half_thickness = line_thickness / 2.0

        vertices = np.array([
            # First triangle
            x1 + nx * half_thickness, y1 + ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x2 + nx * half_thickness, y2 + ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x2 - nx * half_thickness, y2 - ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            # Second triangle
            x2 - nx * half_thickness, y2 - ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x1 - nx * half_thickness, y1 - ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
            x1 + nx * half_thickness, y1 + ny * half_thickness, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0,
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return


        # First, draw the filled center rectangle without the corners
        self.draw_filled_rect(x + radius, y, width - 2 * radius, height, fill_color)
        self.draw_filled_rect(x, y + radius, width, height - 2 * radius, fill_color)

        # Now draw the corners (quarter circles)
        segments = 20
        for i in range(4):
            # For each corner, compute the angle offset and center position
            cx = x + (width - radius if i % 2 == 1 else radius)
            cy = y + (height - radius if i // 2 == 1 else radius)
            angle_offset = i * np.pi / 2

            vertices = []
            for j in range(segments + 1):
                theta = angle_offset + j * np.pi / 2 / segments
                dx = radius * np.cos(theta)
                dy = radius * np.sin(theta)
                vertices.extend([cx + dx, cy + dy, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0])

            vertices_np = np.array(vertices, dtype=np.float32)

            VBO = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

            gl.glUseProgram(self.shader_program)

            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
            gl.glEnableVertexAttribArray(1)
            gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

            gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, segments + 1)

            gl.glDisableVertexAttribArray(0)
            gl.glDisableVertexAttribArray(1)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glDeleteBuffers(1, [VBO])

        # Optionally, add a border if required
        if border_color:
            self.draw_unfilled_rect(x, y, width, height, border_color)


    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertices = np.array([
            # Position         ND_Color
            x, y, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
            x + width, y, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
            x + width, y + height, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
            x, y + height, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, 4)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, fill_color: ND_Color) -> None:
        #
        if self.shader_program <= 0:
            print(f"Error: shader program hasn't been initialized (={self.shader_program}).")
            return

        # Vertex data for two triangles forming a rectangle
        vertices = np.array([
            # First Triangle
            x, y,                fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Bottom-left
            x + width, y,        fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Bottom-right
            x, y + height,       fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Top-left

            # Second Triangle
            x + width, y,        fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Bottom-right
            x + width, y + height, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Top-right
            x, y + height,       fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0,  # Top-left
        ], dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        VAO = gl.glGenVertexArrays(1)

        gl.glBindVertexArray(VAO)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        # Set up position attribute (index 0)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position

        # Set up color attribute (index 1)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # Color

        # Draw the two triangles (6 vertices)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])



    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = []

        for i in range(segments):
            theta = 2.0 * np.pi * i / segments
            dx = radius * np.cos(theta)
            dy = radius * np.sin(theta)
            vertices.extend([x + dx, y + dy, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, segments)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = [x, y, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0]

        for i in range(segments + 1):
            theta = 2.0 * np.pi * i / segments
            dx = radius * np.cos(theta)
            dy = radius * np.sin(theta)
            vertices.extend([x + dx, y + dy, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, segments + 1)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = []

        for i in range(segments):
            theta = 2.0 * np.pi * i / segments
            dx = rx * np.cos(theta)
            dy = ry * np.sin(theta)
            vertices.extend([x + dx, y + dy, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, segments)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = [x, y, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0]

        for i in range(segments + 1):
            theta = 2.0 * np.pi * i / segments
            dx = rx * np.cos(theta)
            dy = ry * np.sin(theta)
            vertices.extend([x + dx, y + dy, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, segments + 1)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = []

        for i in range(segments + 1):
            theta = angle_start + (angle_end - angle_start) * i / segments
            dx = radius * np.cos(theta)
            dy = radius * np.sin(theta)
            vertices.extend([x + dx, y + dy, color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_STRIP, 0, segments + 1)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = []

        for i in range(segments + 1):
            theta = angle_start + (angle_end - angle_start) * i / segments
            dx = radius * np.cos(theta)
            dy = radius * np.sin(theta)
            vertices.extend([x + dx, y + dy, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, segments)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        segments = 100
        vertices = [x, y, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0]

        for i in range(segments + 1):
            theta = angle_start + (angle_end - angle_start) * i / segments
            dx = radius * np.cos(theta)
            dy = radius * np.sin(theta)
            vertices.extend([x + dx, y + dy, fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, segments + 1)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertices = [
            # Vertex 1
            x1, y1, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
            # Vertex 2
            x2, y2, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
            # Vertex 3
            x3, y3, outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0,
        ]

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, 3)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, filled_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        vertices = [
            # Vertex 1
            x1, y1, filled_color.r / 255.0, filled_color.g / 255.0, filled_color.b / 255.0, filled_color.a / 255.0,
            # Vertex 2
            x2, y2, filled_color.r / 255.0, filled_color.g / 255.0, filled_color.b / 255.0, filled_color.a / 255.0,
            # Vertex 3
            x3, y3, filled_color.r / 255.0, filled_color.g / 255.0, filled_color.b / 255.0, filled_color.a / 255.0,
        ]

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], outline_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        vertices = []
        for i in range(len(x_coords)):
            vertices.extend([x_coords[i], y_coords[i], outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_LOOP, 0, len(x_coords))

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        vertices = []
        for i in range(len(x_coords)):
            vertices.extend([x_coords[i], y_coords[i], fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_POLYGON, 0, len(x_coords))

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:

        if self.shader_program_textures <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        if texture_id not in self.gl_textures:
            return

        texture_size = self.get_prepared_texture_size(texture_id)
        vertices = []

        # Build vertex and texture coordinates
        for i in range(len(x_coords)):
            tx = (x_coords[i] + texture_dx) / texture_size.x
            ty = (y_coords[i] + texture_dy) / texture_size.y
            vertices.extend([x_coords[i], y_coords[i], tx, ty])

        vertices_np = np.array(vertices, dtype=np.float32)

        # Create VBO
        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.gl_textures[texture_id])

        # Use shader program and enable vertex attributes
        gl.glUseProgram(self.shader_program_textures)

        # Enable vertex attribute for position
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 4 * 4, ctypes.c_void_p(0))  # Position

        # Enable vertex attribute for texture coordinates
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, False, 4 * 4, ctypes.c_void_p(2 * 4))  # Texture coordinates

        # Draw the polygon
        gl.glDrawArrays(gl.GL_POLYGON, 0, len(x_coords))

        # Cleanup
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:

        if self.shader_program <= 0:
            print("Error: shader program hasn't been initialized.")
            return

        if len(x_coords) != 4 or len(y_coords) != 4:
            raise ValueError("Bezier curve requires exactly 4 control points.")

        vertices = []
        for t in np.linspace(0, 1, nb_interpolations):
            # Cubic Bezier formula
            x = (1 - t) ** 3 * x_coords[0] + 3 * (1 - t) ** 2 * t * x_coords[1] + 3 * (1 - t) * t ** 2 * x_coords[2] + t ** 3 * x_coords[3]
            y = (1 - t) ** 3 * y_coords[0] + 3 * (1 - t) ** 2 * t * y_coords[1] + 3 * (1 - t) * t ** 2 * y_coords[2] + t ** 3 * y_coords[3]
            vertices.extend([x, y, line_color.r / 255.0, line_color.g / 255.0, line_color.b / 255.0, line_color.a / 255.0])

        vertices_np = np.array(vertices, dtype=np.float32)

        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, gl.GL_STATIC_DRAW)

        gl.glUseProgram(self.shader_program)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))  # Position
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, False, 6 * 4, ctypes.c_void_p(2 * 4))  # ND_Color

        gl.glDrawArrays(gl.GL_LINE_STRIP, 0, nb_interpolations)

        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDeleteBuffers(1, [VBO])


    #
    def enable_area_drawing_constraints(self, x: int, y: int, width: int, height: int) -> None:

        # Apply OpenGL viewport or scissor test for clipping
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(x, self.height - (y + width), width, height)  # OpenGL's Y axis is inverted


    #
    def disable_area_drawing_constraints(self) -> None:
        #
        gl.glDisable(gl.GL_SCISSOR_TEST)


    #
    def update_display(self) -> None:

        #
        sdl2.SDL_GL_MakeCurrent(self.sdl_window, self.gl_context)
        gl.glViewport(0, 0, self.width, self.height)

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
        sdl2.SDL_GL_SwapWindow(self.sdl_window)

