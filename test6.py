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

# Path to the font file
fontfile = "/usr/share/fonts/gnu-free/FreeSans.otf"
# fontfile = r'C:\source\resource\fonts\gnu-freefont_freesans\freesans.ttf'

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

def _get_rendering_buffer(xpos: float, ypos: float, w: float, h: float, zfix: float = 0.0) -> np.ndarray:
    """
    Generate the vertex data for rendering a textured quad.

    :param xpos: X position of the bottom-left corner of the quad.
    :param ypos: Y position of the bottom-left corner of the quad.
    :param w: Width of the quad.
    :param h: Height of the quad.
    :param zfix: Z position fix (usually 0.0).
    :return: A NumPy array representing the vertices of the quad.
    """
    return np.asarray([
        xpos,     ypos - h, 0, 0,  # Bottom-left vertex
        xpos,     ypos,     0, 1,  # Top-left vertex
        xpos + w, ypos,     1, 1,  # Top-right vertex
        xpos,     ypos - h, 0, 0,  # Bottom-left vertex again
        xpos + w, ypos,     1, 1,  # Top-right vertex
        xpos + w, ypos - h, 1, 0   # Bottom-right vertex
    ], np.float32)

# Vertex Shader code
VERTEX_SHADER = """
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
FRAGMENT_SHADER = """
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

# Global variables for OpenGL resources
shaderProgram: int = 0
Characters: dict[str, CharacterSlot] = dict()
VBO: int = 0
VAO: int = 0

def initialize() -> None:
    """
    Initialize OpenGL resources, shaders, and load font characters.
    """
    global shaderProgram
    global Characters
    global VBO
    global VAO

    # Compile shaders
    vertexshader = shaders.compileShader(VERTEX_SHADER, gl.GL_VERTEX_SHADER)
    fragmentshader = shaders.compileShader(FRAGMENT_SHADER, gl.GL_FRAGMENT_SHADER)

    # Create the shader program
    shaderProgram = shaders.compileProgram(vertexshader, fragmentshader)
    gl.glUseProgram(shaderProgram)

    # Set up the projection matrix
    shader_projection = gl.glGetUniformLocation(shaderProgram, "projection")
    projection = glm.ortho(0, 640, 640, 0, -100000, 100000)
    gl.glUniformMatrix4fv(shader_projection, 1, gl.GL_FALSE, glm.value_ptr(projection))

    # Disable byte-alignment restriction for texture
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

    # Load font using FreeType
    face = freetype.Face(fontfile)
    face.set_char_size(48 * 64)

    # Load the first 128 characters of ASCII set
    for i in range(0, 128):
        face.load_char(chr(i))
        glyph = face.glyph

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
        Characters[chr(i)] = CharacterSlot(texture, glyph)

    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # Configure VAO and VBO for texture quads
    VAO = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(VAO)

    VBO = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 6 * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glBindVertexArray(0)

def render_text(window: glfw._GLFWwindow, text: str, x: float, y: float, scale: float, color: tuple[int, int, int]) -> None:
    """
    Render text on the window using OpenGL.

    :param window: The GLFW window where the text will be rendered.
    :param text: The text to be rendered.
    :param x: X position of the text's starting point.
    :param y: Y position of the text's starting point.
    :param scale: The scaling factor for the text size.
    :param color: The color of the text (R, G, B).
    """
    global shaderProgram
    global Characters
    global VBO
    global VAO

    # Set text color
    gl.glUniform3f(gl.glGetUniformLocation(shaderProgram, "textColor"),
                   color[0] / 255, color[1] / 255, color[2] / 255)

    gl.glActiveTexture(gl.GL_TEXTURE0)

    # Enable blending for transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    # Bind the VAO
    gl.glBindVertexArray(VAO)

    # Render each character in the text
    for c in text:
        ch = Characters[c]
        w, h = ch.textureSize
        w = w * scale
        h = h * scale
        vertices = _get_rendering_buffer(x, y, w, h)

        # Render the glyph texture over a quad
        gl.glBindTexture(gl.GL_TEXTURE_2D, ch.texture)

        # Update the VBO with new vertex data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        # Draw the quad
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        # Advance the cursor to the next position (in pixels)
        x += (ch.advance >> 6) * scale

    # Unbind the VAO and texture
    gl.glBindVertexArray(0)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # Swap buffers and poll events
    glfw.swap_buffers(window)
    glfw.poll_events()


def main() -> None:
    """
    Main function to initialize the window, OpenGL, and run the rendering loop.
    """
    # Initialize GLFW
    if not glfw.init():
        raise RuntimeError("GLFW could not be initialized")

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(640, 640, "Example Program", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("GLFW window could not be created")

    glfw.make_context_current(window)

    # Initialize OpenGL resources
    initialize()

    # Main rendering loop
    while not glfw.window_should_close(window):
        glfw.poll_events()
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Render text on screen
        render_text(window, 'hello', 40, 100, 0.5 + ((1.0 + math.sin(10.0 * time.time())) / 2.0), (255, 100, 100))

    glfw.terminate()

# Entry point of the program
if __name__ == '__main__':
    main()
