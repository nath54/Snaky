import glfw  # type: ignore
import OpenGL.GL as gl  # type: ignore
import freetype  # type: ignore
import numpy as np

# You'll need to install the PyGLM package for matrix handling
import glm  # type: ignore


def create_ortho_projection_matrix(screen_width: int, screen_height: int):
    return glm.ortho(0.0, screen_width, 0.0, screen_height, -1.0, 1.0)



# Vertex Shader (basic shader for handling text rendering)
vertex_shader_code = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

uniform mat4 projection;

void main() {
    gl_Position = projection * vec4(aPos, 0.0, 1.0);
    TexCoord = aTexCoord;
}
"""



# Fragment Shader (for drawing textures)
fragment_shader_code = """
#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D textTexture;
uniform vec4 textColor;

void main() {
    vec4 texColor = texture(textTexture, TexCoord);
    FragColor = texColor * textColor;
}
"""



# Compile and link shaders
def create_shader_program():
    vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(vertex_shader, vertex_shader_code)
    gl.glCompileShader(vertex_shader)

    if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
        raise RuntimeError(gl.glGetShaderInfoLog(vertex_shader))

    fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(fragment_shader, fragment_shader_code)
    gl.glCompileShader(fragment_shader)

    if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
        raise RuntimeError(gl.glGetShaderInfoLog(fragment_shader))

    shader_program = gl.glCreateProgram()
    gl.glAttachShader(shader_program, vertex_shader)
    gl.glAttachShader(shader_program, fragment_shader)
    gl.glLinkProgram(shader_program)

    if not gl.glGetProgramiv(shader_program, gl.GL_LINK_STATUS):
        raise RuntimeError(gl.glGetProgramInfoLog(shader_program))

    gl.glDeleteShader(vertex_shader)
    gl.glDeleteShader(fragment_shader)

    return shader_program




class TextRenderer:
    def __init__(self) -> None:
        self.characters: dict[str, dict[str, int | tuple[int, int] | tuple[int, int] | int]] = {}

    def load_font(self, font_path: str, font_size: int) -> None:
        self.face: freetype.Face = freetype.Face(font_path)
        self.face.set_char_size(font_size * 64)

        for c in range(128):
            self.face.load_char(chr(c))
            bitmap: freetype.Bitmap = self.face.glyph.bitmap

            texture: int = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D,
                0,
                gl.GL_RED,
                bitmap.width,
                bitmap.rows,
                0,
                gl.GL_RED,
                gl.GL_UNSIGNED_BYTE,
                bitmap.buffer
            )

            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

            self.characters[chr(c)] = {
                'texture': texture,
                'size': (bitmap.width, bitmap.rows),
                'bearing': (self.face.glyph.bitmap_left, self.face.glyph.bitmap_top),
                'advance': self.face.glyph.advance.x
            }

    def prepare_text_to_render(self, text: str, color: tuple[float, float, float, float]) -> tuple[np.ndarray, np.ndarray]:
        vertices: list[float] = []
        texture_coords: list[float] = []

        x: float = 0
        y: float = 0

        for c in text:
            ch: dict[str, int | tuple[int, int]] = self.characters[c]

            bearing: int | tuple[int, int] = ch['bearing']
            size: int | tuple[int, int] = ch['bearing']

            xpos: float = 0
            ypos: float = 0
            w: int = 0
            h: int = 0

            if isinstance(bearing, tuple) and isinstance(size, tuple):

                xpos = x + bearing[0]
                ypos = y - (size[1] - bearing[1])
                w = size[0]
                h = size[1]

            elif isinstance(bearing, int) and isinstance(size, int):
                # Assuming 'bearing' is an int (horizontal only) and 'size' is an int (square size)
                xpos = x + bearing
                ypos = y  # Adjust as necessary for vertical alignment
                w = h = size  # Assuming the character is square in this case

            vertices.extend([
                xpos, ypos + h,
                xpos, ypos,
                xpos + w, ypos,
                xpos + w, ypos + h
            ])

            texture_coords.extend([
                0, 0,
                0, 1,
                1, 1,
                1, 0
            ])


            advance: int | tuple[int, int] = ch['advance']

            if isinstance(advance, int):
                x += (advance >> 6)
            else:
                x += (advance[0] >> 6)

        vertices_array: np.ndarray = np.array(vertices, dtype=np.float32)
        texture_coords_array: np.ndarray = np.array(texture_coords, dtype=np.float32)

        return vertices_array, texture_coords_array

   # def render_text(self, text: str, x: float, y: float, scale: float, color: tuple[float, float, float, float]) -> None:
        # gl.glActiveTexture(gl.GL_TEXTURE0)
        # gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # vertices: np.ndarray
        # texture_coords: np.ndarray
        # vertices, texture_coords = self.prepare_text_to_render(text, color)

        # vao: int = gl.glGenVertexArrays(1)
        # gl.glBindVertexArray(vao)

        # vbo: int = gl.glGenBuffers(1)
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        # gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        # gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        # gl.glEnableVertexAttribArray(0)

        # tbo: int = gl.glGenBuffers(1)
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, tbo)
        # gl.glBufferData(gl.GL_ARRAY_BUFFER, texture_coords.nbytes, texture_coords, gl.GL_STATIC_DRAW)
        # gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        # gl.glEnableVertexAttribArray(1)

        # for i, c in enumerate(text):
        #     ch: dict[str, int | tuple[int, int] | tuple[int, int] | int] = self.characters[c]
        #     gl.glBindTexture(gl.GL_TEXTURE_2D, ch['texture'])
        #     gl.glDrawArrays(gl.GL_QUADS, i * 4, 4)

        # gl.glDeleteBuffers(1, [vbo])
        # gl.glDeleteBuffers(1, [tbo])
        # gl.glDeleteVertexArrays(1, [vao])

    def render_text(self, text: str, x: float, y: float, scale: float, color: tuple[float, float, float, float]) -> None:
        # Create and use the shader program
        shader: int = create_shader_program()
        gl.glUseProgram(shader)

        # Set projection matrix (assuming a window of size 800x600)
        projection = create_ortho_projection_matrix(800, 600)
        projection_loc = gl.glGetUniformLocation(shader, "projection")
        gl.glUniformMatrix4fv(projection_loc, 1, gl.GL_TRUE, glm.value_ptr(projection))

        # Set the text color uniform
        color_loc = gl.glGetUniformLocation(shader, "textColor")
        gl.glUniform4fv(color_loc, 1, color)

        # Enable blending for transparent text
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Bind VAO, VBO, TBO and draw the text using quads for each character
        for i, c in enumerate(text):
            ch = self.characters[c]
            gl.glBindTexture(gl.GL_TEXTURE_2D, ch['texture'])

            # Set up the vertex array and buffers as in the original code
            # Then draw the quads for each character
            gl.glDrawArrays(gl.GL_QUADS, i * 4, 4)

        # Clean up
        gl.glDisable(gl.GL_BLEND)
        gl.glDeleteProgram(shader)




# Usage example
def main() -> None:
    if not glfw.init():
        return

    window: glfw.Window = glfw.create_window(800, 600, "Text Rendering with GLFW and FreeType", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    text_renderer: TextRenderer = TextRenderer()
    text_renderer.load_font("/usr/share/fonts/gnu-free/FreeSans.otf", 48)

    while not glfw.window_should_close(window):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        text_renderer.render_text("Hello, World!", 100, 100, 1, (1, 1, 1, 1))

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()