
from typing import Optional, Any, Callable, cast, Type
from threading import Lock

import os
import math

# To improve speed for non development code:
#
#   import OpenGL
#   OpenGL.ERROR_LCHECKING = False
#   OpenGL.ERROR_LOGGING = False

import OpenGL.GL as gl  # type: ignore
import glfw  # type: ignore
import freetype  # type: ignore
import glm  # type: ignore
import ctypes

from lib_nadisplay_colors import ND_Color, ND_Transformations
from lib_nadisplay_rects import ND_Rect, ND_Point
from lib_nadisplay import ND_MainApp, ND_Display, ND_Window, ND_Scene
from lib_nadisplay_glfw import get_display_info
from lib_nadisplay_opengl import create_and_validate_gl_shader_program
from lib_nadisplay_np import get_rendering_buffer



VERTEX_GEOMETRY_SHADER_SRC: str = """
    #version 330 core
    layout (location = 0) in vec2 position;
    layout (location = 1) in vec4 color;
    out vec4 frag_color;
    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
        frag_color = color;
    }
"""

FRAGMENT_GEOMETRY_SHADER_SRC: str = """
    #version 330 core
    in vec4 frag_color;
    out vec4 out_color;
    void main() {
        out_color = frag_color;
    }
"""


VERTEX_TEXTURES_SHADER_SRC = """
    #version 330 core
    layout (location = 0) in vec2 position;  // Position of the vertex
    layout (location = 1) in vec2 texCoord;  // Texture coordinates
    out vec2 fragTexCoord;  // Output to fragment shader

    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
        fragTexCoord = texCoord;  // Pass texture coordinates to fragment shader
    }
"""

FRAGMENT_TEXTURES_SHADER_SRC = """
    #version 330 core
    in vec2 fragTexCoord;  // Input from vertex shader
    out vec4 outColor;     // Output color
    uniform sampler2D textureSampler;  // The texture sampler

    void main() {
        outColor = texture(textureSampler, fragTexCoord);  // Sample the texture
    }
"""


# Vertex Shader code
VERTEX_FONTS_SHADER_SRC = """
    #version 330 core
    layout (location = 0) in vec4 vertex; // <vec2 pos, vec2 tex>
    out vec2 TexCoords;

    uniform mat4 projection;

    void main()
    {
        gl_Position = projection * vec4(vertex.xy, 0.0, 1.0);
        TexCoords = vertex.zw;
    }
"""

# Fragment Shader code
FRAGMENT_FONTS_SHADER_SRC = """
    #version 330 core
    in vec2 TexCoords;
    out vec4 color;

    uniform sampler2D text;
    uniform vec4 textColor;

    void main()
    {
        vec4 sampled = vec4(1.0, 1.0, 1.0, texture(text, TexCoords).r);
        color = textColor * sampled;
    }
"""


class CharacterSlot:
    """Store information about each character, including its texture and size."""

    def __init__(self, texture: int, glyph: freetype.GlyphSlot) -> None:
        """
        Initialize a CharacterSlot with a texture and the associated glyph data.

        :param texture: The OpenGL texture ID for the character.
        :param glyph: The glyph object containing character data.
        """
        self.texture = texture
        self.textureSize = (glyph.bitmap.width, glyph.bitmap.rows)

        if isinstance(glyph, freetype.GlyphSlot):
            # Glyph has bitmap_left and bitmap_top attributes
            self.bearing = (glyph.bitmap_left, glyph.bitmap_top)
            self.advance = glyph.advance.x
        elif isinstance(glyph, freetype.BitmapGlyph):
            # BitmapGlyph has left and top attributes
            self.bearing = (glyph.left, glyph.top)
            self.advance = None
        else:
            raise RuntimeError('Unknown glyph type')



class FontRenderer:

    def __init__(self, font_shader_program: int, font_path: str, font_size: int) -> None:
        #
        self.font_shader_program: int = font_shader_program
        #
        self.font_path: str = font_path
        self.font_size: int = font_size
        #
        self.font_face: Optional[freetype.Face] = None
        self.characters: dict[str, CharacterSlot] = {}
        #
        self.VBO = None
        self.VAO = None

    #
    def load_and_init(self) -> bool:
        #
        self.font_face = freetype.Face(self.font_path)
        self.font_face.set_char_size(int(float(self.font_size) * 3.0 / 4.0) * self.font_size)
        #
        gl.glUseProgram(self.font_shader_program)

        # Set up the projection matrix
        shader_projection = gl.glGetUniformLocation(self.font_shader_program, "projection")
        projection = glm.ortho(0, 640, 640, 0, -100000, 100000)
        gl.glUniformMatrix4fv(shader_projection, 1, gl.GL_FALSE, glm.value_ptr(projection))

        # Disable byte-alignment restriction for texture
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        # Load the first 128 characters of ASCII set
        for i in range(0, 128):
            self.font_face.load_char(chr(i))
            glyph = self.font_face.glyph

            # Generate texture for the glyph
            texture = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RED, glyph.bitmap.width, glyph.bitmap.rows, 0,
                            gl.GL_RED, gl.GL_UNSIGNED_BYTE, glyph.bitmap.buffer)

            # Texture options
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

            # Store the character in the dictionary
            self.characters[chr(i)] = CharacterSlot(texture, glyph)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        # Configure VAO and VBO for texture quads
        self.VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.VAO)

        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, 6 * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        #
        return True

    #
    def render_text(self, text: str, x: float, y: float, scale: float, color: ND_Color) -> None:
        """
        Render text on the window using OpenGL.

        :param window: The GLFW window where the text will be rendered.
        :param text: The text to be rendered.
        :param x: X position of the text's starting point.
        :param y: Y position of the text's starting point.
        :param scale: The scaling factor for the text size.
        :param color: The color of the text (R, G, B).
        """

        # Set text color
        gl.glUniform4f(gl.glGetUniformLocation(self.font_shader_program, "textColor"),
                       color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)

        gl.glActiveTexture(gl.GL_TEXTURE0)

        # Enable blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Bind the VAO
        gl.glBindVertexArray(self.VAO)

        # Render each character in the text
        for c in text:
            ch = self.characters[c]
            w, h = ch.textureSize
            w = w * scale
            h = h * scale
            vertices = get_rendering_buffer(x, y, w, h)

            # Render the glyph texture over a quad
            gl.glBindTexture(gl.GL_TEXTURE_2D, ch.texture)

            # Update the VBO with new vertex data
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            # Draw the quad
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

            # Advance the cursor to the next position (in pixels)
            x += (ch.advance >> 6) * scale

        # Unbind the VAO and texture
        gl.glBindVertexArray(0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


#
class ND_Display_GLFW_OPENGL(ND_Display):

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
        self.fonts_renderers: dict[str, dict[int, Optional[FontRenderer]]] = {}
        self.default_font: str = "FreeSans"
        #
        self.windows: dict[int, Optional[ND_Window]] = {}
        self.thread_create_window: Lock = Lock()
        #
        self.shader_geometry_program: int = -1
        self.shader_textures_program: int = -1
        self.shader_fonts_program: int = -1
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

        # Init glfw
        if not glfw.init():
            raise Exception("GLFW can't be initialized")

        # Compile shaders and create a program
        self.shader_geometry_program = create_and_validate_gl_shader_program(
                                            VERTEX_GEOMETRY_SHADER_SRC, FRAGMENT_GEOMETRY_SHADER_SRC)

        # Compile shaders and create a program for textures
        self.shader_textures_program = create_and_validate_gl_shader_program(
                                            VERTEX_TEXTURES_SHADER_SRC, FRAGMENT_TEXTURES_SHADER_SRC)

        # Compile shaders and create a program for textures
        self.shader_fonts_program = create_and_validate_gl_shader_program(
                                            VERTEX_FONTS_SHADER_SRC, FRAGMENT_FONTS_SHADER_SRC)

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
    def get_font(self, font: str, font_size: int) -> Optional[FontRenderer]:
        #
        if font not in self.fonts_renderers:
            self.fonts_renderers[font] = {}
        #
        if font_size < 8:
            font_size = 8
        #
        if font_size not in self.fonts_renderers[font]:
            #
            font_path: str = self.font_names[font]
            #
            if (font_path.endswith(".ttf") or font_path.endswith(".otf")) and os.path.exists(font_path):
                #
                if font not in self.fonts_renderers:
                    self.fonts_renderers[font] = {}
                #
                font_renderer: Optional[FontRenderer] = FontRenderer(self.shader_fonts_program, font_path, font_size)
                self.fonts_renderers[font][font_size] = font_renderer
                #
                if font_renderer is not None:
                    if not font_renderer.load_and_init():
                        self.fonts_renderers[font][font_size] = None
            else:
                return None
        #
        return self.fonts_renderers[font][font_size]


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
class ND_Window_GLFW_OPENGL(ND_Window):
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
                screen_width: int = infos.size.width
                screen_height: int = infos.size.height
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
        self.glw_window: glfw._GLFWwindow = glfw.create_window(
                                                self.width,
                                                self.height,
                                                title,
                                                None,
                                                None
        )


        # sdl_or_glfw_window_id is int and has been initialized to -1 in parent class
        self.sdl_or_glfw_window_id = id(self.glw_window)

        #
        self.next_texture_id: int = 0
        self.sdl_textures: dict[int, object] = {}
        self.gl_textures: dict[int, int] = {}
        self.sdl_textures_surfaces: dict[int, object] = {}
        self.mutex_sdl_textures: Lock = Lock()


    #
    def destroy_window(self) -> None:
        #
        for texture_id in self.sdl_textures:
            #
            self.destroy_prepared_texture(texture_id)

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
    def blit_texture(self, texture, dst_rect: ND_Rect) -> None:

        # Bind the OpenGL texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

        # Enable 2D texturing
        gl.glEnable(gl.GL_TEXTURE_2D)

        # Set up the quad vertices and texture coordinates
        gl.glBegin(gl.GL_QUADS)

        # Bottom-left corner
        gl.glTexCoord2f(0.0, 0.0)
        gl.glVertex2f(dst_rect.x, dst_rect.y + dst_rect.h)

        # Bottom-right corner
        gl.glTexCoord2f(1.0, 0.0)
        gl.glVertex2f(dst_rect.x + dst_rect.w, dst_rect.y + dst_rect.h)

        # Top-right corner
        gl.glTexCoord2f(1.0, 1.0)
        gl.glVertex2f(dst_rect.x + dst_rect.w, dst_rect.y)

        # Top-left corner
        gl.glTexCoord2f(0.0, 1.0)
        gl.glVertex2f(dst_rect.x, dst_rect.y)

        gl.glEnd()

        # Disable texturing and unbind the texture
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


    #
    def draw_text(self, txt: str, x: int, y: int, font_size: int, font_color: ND_Color, font_name: Optional[str] = None) -> None:
        #
        if font_name is None:
            font_name = self.display.default_font
        #
        font_renderer: Optional[FontRenderer] = cast(Optional[FontRenderer], self.display.get_font(font_name, font_size))
        #
        if font_renderer is None:
            return
        #
        font_renderer.render_text(txt, float(x), float(y), 1.0, font_color)


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

        # Convert the SDL surface into an OpenGL texture
        texture = self._create_opengl_texture_from_surface(image_surface)

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

        #
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.sdl_textures[texture_id])

        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBegin(gl.GL_QUADS)
        # Define the texture coordinates and vertices to map the texture onto a rectangle
        gl.glTexCoord2f(0.0, 1.0)
        gl.glVertex2f(x, y)

        gl.glTexCoord2f(1.0, 1.0)
        gl.glVertex2f(x + width, y)

        gl.glTexCoord2f(1.0, 0.0)
        gl.glVertex2f(x + width, y + height)

        gl.glTexCoord2f(0.0, 0.0)
        gl.glVertex2f(x, y + height)
        gl.glEnd()

        gl.glDisable(gl.GL_TEXTURE_2D)


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
    def _create_opengl_texture_from_surface(self, surface) -> int:

        #
        gl_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, gl_texture)

        width = surface.contents.w
        height = surface.contents.h

        # Convert SDL surface into a format OpenGL can use (RGBA)
        surface_pixels = ctypes.cast(surface.contents.pixels, ctypes.POINTER(ctypes.c_ubyte))

        # Upload the pixel data from the SDL_Surface to the OpenGL texture
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, surface_pixels)

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        #
        texture_id: int = -1
        with self.mutex_sdl_textures:
            #
            texture_id = self.next_texture_id
            self.next_texture_id += 1
            #
            self.sdl_textures[texture_id] = gl_texture
            self.sdl_textures_surfaces[texture_id] = surface

        #
        return texture_id


    #
    def draw_pixel(self, x: int, y: int, color: ND_Color) -> None:

        #
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex2f(x, y)
        gl.glEnd()


    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:

        #
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(x1, y)
        gl.glVertex2f(x2, y)
        gl.glEnd()


    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:

        #
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(x, y1)
        gl.glVertex2f(x, y2)
        gl.glEnd()


    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:

        #
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(x1, y1)
        gl.glVertex2f(x2, y2)
        gl.glEnd()


    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:

        # Set the color for the line
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)

        # Calculate the direction vector (dx, dy) of the line
        dx = x2 - x1
        dy = y2 - y1

        # Normalize the direction vector to find the perpendicular
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return  # Avoid division by zero in case of zero-length line

        # Perpendicular vector (normal to the line)
        nx = -dy / length
        ny = dx / length

        # Half thickness offset
        half_thickness = line_thickness / 2.0

        # Calculate the four vertices of the thick line (a quad)
        x1_offset1 = x1 + nx * half_thickness
        y1_offset1 = y1 + ny * half_thickness
        x1_offset2 = x1 - nx * half_thickness
        y1_offset2 = y1 - ny * half_thickness

        x2_offset1 = x2 + nx * half_thickness
        y2_offset1 = y2 + ny * half_thickness
        x2_offset2 = x2 - nx * half_thickness
        y2_offset2 = y2 - ny * half_thickness

        # Draw the thick line as a quad using two triangles
        gl.glBegin(gl.GL_TRIANGLES)

        # First triangle
        gl.glVertex2f(x1_offset1, y1_offset1)
        gl.glVertex2f(x2_offset1, y2_offset1)
        gl.glVertex2f(x1_offset2, y1_offset2)

        # Second triangle
        gl.glVertex2f(x1_offset2, y1_offset2)
        gl.glVertex2f(x2_offset1, y2_offset1)
        gl.glVertex2f(x2_offset2, y2_offset2)

        #
        gl.glEnd()


    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color) -> None:

        #
        gl.glColor4f(fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0)
        # You would implement the corner drawing using triangle fans here.
        # For now, just drawing the filled rectangle part
        self.draw_filled_rect(x + radius, y, width - 2 * radius, height, fill_color)
        self.draw_filled_rect(x, y + radius, width, height - 2 * radius, fill_color)
        # To draw borders, you can draw line loops or thin rectangles at the borders


    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:

        #
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x + width, y)
        gl.glVertex2f(x + width, y + height)
        gl.glVertex2f(x, y + height)
        gl.glEnd()


    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:

        #
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x + width, y)
        gl.glVertex2f(x + width, y + height)
        gl.glVertex2f(x, y + height)
        gl.glEnd()


    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, outline_color: ND_Color, steps: int = 1) -> None:

        #
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        for i in range(0, 360, steps):
            theta = 2.0 * math.pi * i / 360  # Get the current angle
            dx = radius * math.cos(theta)  # Calculate the x component
            dy = radius * math.sin(theta)  # Calculate the y component
            gl.glVertex2f(x + dx, y + dy)
        gl.glEnd()


    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color, steps: int = 1) -> None:

        #
        gl.glColor4f(fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0)
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glVertex2f(x, y)  # Center of the circle
        for i in range(0, 360, steps):
            theta = 2.0 * math.pi * i / 360  # Get the current angle
            dx = radius * math.cos(theta)  # Calculate the x component
            dy = radius * math.sin(theta)  # Calculate the y component
            gl.glVertex2f(x + dx, y + dy)
        gl.glEnd()


    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, outline_color: ND_Color) -> None:

        # Set the color using SDL_Color (normalize to 0-1 for OpenGL)
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)

        # Begin drawing the unfilled ellipse with GL_LINE_LOOP
        gl.glBegin(gl.GL_LINE_LOOP)

        # Generate points around the ellipse
        num_segments = 100  # Number of segments to approximate the ellipse
        for i in range(num_segments):
            theta = 2.0 * math.pi * i / num_segments  # Current angle
            x_pos = x + rx * math.cos(theta)  # X position
            y_pos = y + ry * math.sin(theta)  # Y position
            gl.glVertex2f(x_pos, y_pos)

        gl.glEnd()


    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:

        # Set the color using SDL_Color (normalize to 0-1 for OpenGL)
        gl.glColor4f(fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0)

        # Begin drawing the filled ellipse with GL_TRIANGLE_FAN
        gl.glBegin(gl.GL_TRIANGLE_FAN)

        # Center point of the ellipse (fan center)
        gl.glVertex2f(x, y)

        # Generate points around the ellipse
        num_segments = 100  # Number of segments to approximate the ellipse
        for i in range(num_segments + 1):  # One extra point to complete the loop
            theta = 2.0 * math.pi * i / num_segments  # Current angle
            x_pos = x + rx * math.cos(theta)  # X position
            y_pos = y + ry * math.sin(theta)  # Y position
            gl.glVertex2f(x_pos, y_pos)

        gl.glEnd()


    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color) -> None:

        # Set the color using SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)

        # Begin drawing the unfilled arc with GL_LINE_STRIP
        gl.glBegin(gl.GL_LINE_STRIP)

        # Number of segments to approximate the arc
        num_segments = 100
        for i in range(num_segments + 1):
            theta = angle_start + (angle_end - angle_start) * i / num_segments  # Current angle in radians
            x_pos = x + radius * math.cos(theta)  # X position
            y_pos = y + radius * math.sin(theta)  # Y position
            gl.glVertex2f(x_pos, y_pos)  # Add the vertex

        gl.glEnd()


    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, outline_color: ND_Color) -> None:

        # Set the color using SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)

        # Begin drawing the unfilled pie with GL_LINE_LOOP
        gl.glBegin(gl.GL_LINE_LOOP)

        # Number of segments to approximate the arc (the pie slice)
        num_segments = 100
        for i in range(num_segments + 1):
            theta = angle_start + (angle_end - angle_start) * i / num_segments  # Current angle in radians
            x_pos = x + radius * math.cos(theta)  # X position
            y_pos = y + radius * math.sin(theta)  # Y position
            gl.glVertex2f(x_pos, y_pos)  # Add the perimeter vertex

        # Connect back to the center of the pie
        gl.glVertex2f(x, y)  # Connect the last point to the center to complete the unfilled slice

        gl.glEnd()


    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:

        # Set the color using SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0)

        # Begin drawing the filled pie with GL_TRIANGLE_FAN
        gl.glBegin(gl.GL_TRIANGLE_FAN)

        # Center of the pie (fan center)
        gl.glVertex2f(x, y)

        # Number of segments to approximate the pie (the slice)
        num_segments = 100
        for i in range(num_segments + 1):  # One extra point to complete the loop
            theta = angle_start + (angle_end - angle_start) * i / num_segments  # Current angle in radians
            x_pos = x + radius * math.cos(theta)  # X position
            y_pos = y + radius * math.sin(theta)  # Y position
            gl.glVertex2f(x_pos, y_pos)  # Add the perimeter vertex

        gl.glEnd()


    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, outline_color: ND_Color) -> None:

        # Set the color using the SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)

        # Begin drawing an unfilled triangle using GL_LINE_LOOP
        gl.glBegin(gl.GL_LINE_LOOP)

        # Specify the vertices of the triangle
        gl.glVertex2f(x1, y1)  # First vertex
        gl.glVertex2f(x2, y2)  # Second vertex
        gl.glVertex2f(x3, y3)  # Third vertex

        # End drawing
        gl.glEnd()


    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, filled_color: ND_Color) -> None:

        # Set the color using the SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(filled_color.r / 255.0, filled_color.g / 255.0, filled_color.b / 255.0, filled_color.a / 255.0)

        # Begin drawing an unfilled triangle using GL_LINE_LOOP
        gl.glBegin(gl.GL_TRIANGLE)

        # Specify the vertices of the triangle
        gl.glVertex2f(x1, y1)  # First vertex
        gl.glVertex2f(x2, y2)  # Second vertex
        gl.glVertex2f(x3, y3)  # Third vertex

        # End drawing
        gl.glEnd()


    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], outline_color: ND_Color) -> None:

        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        # Set the color using SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(outline_color.r / 255.0, outline_color.g / 255.0, outline_color.b / 255.0, outline_color.a / 255.0)

        # Begin drawing the unfilled polygon with GL_LINE_LOOP
        gl.glBegin(gl.GL_LINE_LOOP)

        # Iterate over the vertices and draw the polygon
        for i in range(n):
            gl.glVertex2f(x_coords[i], y_coords[i])

        # End the drawing
        gl.glEnd()


    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < 3:
            return

        #
        n: int = len(x_coords)

        # Set the color using SDL_Color (normalize the values to 0-1 for OpenGL)
        gl.glColor4f(fill_color.r / 255.0, fill_color.g / 255.0, fill_color.b / 255.0, fill_color.a / 255.0)

        # Begin drawing the unfilled polygon with GL_LINE_LOOP
        gl.glBegin(gl.GL_POLYGON)

        # Iterate over the vertices and draw the polygon
        for i in range(n):
            gl.glVertex2f(x_coords[i], y_coords[i])

        # End the drawing
        gl.glEnd()


    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:
        #
        if texture_id not in self.sdl_textures:
            return
        #
        ts: ND_Point = self.get_prepared_texture_size(texture_id)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.sdl_textures[texture_id])
        gl.glBegin(gl.GL_POLYGON)
        for i in range(len(x_coords)):
            gl.glTexCoord2f((x_coords[i] + texture_dx) / ts.x, (y_coords[i] + texture_dy) / ts.y)
            gl.glVertex2f(x_coords[i], y_coords[i])
        gl.glEnd()
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:
        #
        if len(x_coords) != len(y_coords) or len(x_coords) < nb_interpolations:
            return

        # TODO
        pass


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
        # sdl2.SDL_GL_MakeCurrent(self.sdl_window, self.gl_context)

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
        # sdl2.SDL_GL_SwapWindow(self.sdl_window)
        # TODO
        pass


