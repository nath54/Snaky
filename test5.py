import OpenGL.GL as gl  # type: ignore
import OpenGL.GLU as glu  # type: ignore
from OpenGL.GL import shaders
import glfw  # type: ignore
import freetype  # type: ignore
import glm
import numpy as np
from PIL import Image
import math
import time


class CharacterSlot:
    """
    Holds the data for a single character's texture and glyph information.
    """
    def __init__(self, texture: int, glyph: freetype.GlyphSlot):
        """
        Initializes the character slot with a texture and glyph data.

        :param texture: OpenGL texture ID for the character.
        :param glyph: Freetype glyph containing character metrics.
        """
        self.texture: int = texture
        self.textureSize: tuple[int, int] = (glyph.bitmap.width, glyph.bitmap.rows)

        self.bearing: tuple[int, int]
        self.advance: int

        if isinstance(glyph, freetype.GlyphSlot):
            self.bearing = (glyph.bitmap_left, glyph.bitmap_top)
            self.advance = glyph.advance.x
        elif isinstance(glyph, freetype.BitmapGlyph):
            self.bearing = (glyph.left, glyph.top)
            self.advance = 0
        else:
            raise RuntimeError('Unknown glyph type')


def _get_rendering_buffer(xpos: float, ypos: float, w: float, h: float, zfix: float = 0.0) -> np.ndarray:
    """
    Generates a buffer for rendering a rectangle to display a character texture.

    :param xpos: X position of the lower-left corner of the rectangle.
    :param ypos: Y position of the lower-left corner of the rectangle.
    :param w: Width of the rectangle.
    :param h: Height of the rectangle.
    :param zfix: Z-coordinate for depth. Defaults to 0.0.
    :return: A numpy array representing vertex positions and texture coordinates.
    """
    return np.asarray([
        xpos,     ypos - h, 0, 0,
        xpos,     ypos,     0, 1,
        xpos + w, ypos,     1, 1,
        xpos,     ypos - h, 0, 0,
        xpos + w, ypos,     1, 1,
        xpos + w, ypos - h, 1, 0
    ], np.float32)


# Shaders as strings
VERTEX_SHADER: str = """
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

FRAGMENT_SHADER: str = """
    #version 330 core
    in vec2 TexCoords;
    out vec4 color;

    uniform sampler2D text;
    uniform vec3 textColor;

    void main()
    {
        vec4 sampled = vec4(1.0, 1.0, 1.0, texture(text, TexCoords).r);
        color = vec4(textColor, 1.0) * sampled;
    }
"""

# Global variables
shaderProgram: int = 0
Characters: dict[str, CharacterSlot] = dict()
VBO: int = 0
VAO: int = 0


def initialize() -> None:
    """
    Initializes the OpenGL context, shaders, and texture for the font characters.
    """
    global shaderProgram, Characters, VBO, VAO

    # Compiling vertex and fragment shaders
    vertex_shader = shaders.compileShader(VERTEX_SHADER, gl.GL_VERTEX_SHADER)
    fragment_shader = shaders.compileShader(FRAGMENT_SHADER, gl.GL_FRAGMENT_SHADER)

    # Creating shader program
    shaderProgram = shaders.compileProgram(vertex_shader, fragment_shader)
    gl.glUseProgram(shaderProgram) # <---

    # Setting projection matrix
    shader_projection = gl.glGetUniformLocation(shaderProgram, "projection")
    projection = glm.ortho(0, 640, 640, 0, -100000, 100000)
    gl.glUniformMatrix4fv(shader_projection, 1, gl.GL_FALSE, glm.value_ptr(projection))

    # Disable byte-alignment restriction
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

    # Load font face using freetype
    face = freetype.Face("/usr/share/fonts/gnu-free/FreeSans.otf")
    face.set_char_size(48 * 64)

    # Load first 128 characters of ASCII set
    for i in range(128):
        face.load_char(chr(i))
        glyph = face.glyph

        # Generate texture for each character
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RED, glyph.bitmap.width, glyph.bitmap.rows, 0,
             gl.GL_RED, gl.GL_UNSIGNED_BYTE, glyph.bitmap.buffer)

        # Set texture parameters
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        # Store character in the global dictionary
        Characters[chr(i)] = CharacterSlot(texture, glyph)

    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # Configure VAO/VBO for rendering texture quads
    VAO = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(VAO)

    VBO = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 6 * 4, None, gl.GL_DYNAMIC_DRAW)
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glBindVertexArray(0)
    #
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)


def render_text(window: glfw._GLFWwindow, text: str, x: float, y: float, scale: float, color: tuple[int, int, int]) -> None:
    """
    Renders the given text on the window using OpenGL.

    :param window: The GLFW window to render text onto.
    :param text: The text string to render.
    :param x: The starting X position to render the text.
    :param y: The starting Y position to render the text.
    :param scale: The scaling factor for the text size.
    :param color: A tuple representing the RGB color of the text.
    """
    global shaderProgram, Characters, VBO, VAO

    print(f"Scale : {scale}")

    # Set the color for the text
    gl.glUniform3f(gl.glGetUniformLocation(shaderProgram, "textColor"), color[0] / 255, color[1] / 255, color[2] / 255)

    # Activate the texture unit for rendering
    gl.glActiveTexture(gl.GL_TEXTURE0)

    # Iterate over each character in the text
    gl.glBindVertexArray(VAO)
    for c in text:
        ch = Characters[c]
        w, h = ch.textureSize
        w = int(w * scale)
        h = int(h * scale)

        # Generate vertex data for the character's quad
        vertices = _get_rendering_buffer(x, y, w, h)

        # Bind the character's texture
        gl.glBindTexture(gl.GL_TEXTURE_2D, ch.texture)

        # Update the VBO with new vertex data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        # Render the character as a textured quad
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        # Advance the cursor to the next character
        x += (ch.advance >> 6)*scale

    # Unbind VAO and texture
    gl.glBindVertexArray(0)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # Swap buffers and process events
    glfw.swap_buffers(window)
    glfw.poll_events()


def main() -> None:
    """
    Main function to initialize GLFW, OpenGL context, and render the text.
    """
    glfw.init()
    window = glfw.create_window(640, 640, "EXAMPLE PROGRAM", None, None)
    glfw.make_context_current(window)

    # Initialize the text rendering
    initialize()

    # Main render loop
    while not glfw.window_should_close(window):
        glfw.poll_events()
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Render the text "hello" at position (1, 1) with scale 1 and color (100, 100, 100)
        render_text(window,'hello', 20, 50, 0.5 + ((1.0 + math.sin(time.time())) / 2.0), (255, 100, 100))

    glfw.terminate()


if __name__ == '__main__':
    main()
