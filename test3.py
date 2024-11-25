import glfw
from OpenGL.GL import *
import numpy as np

# Function to initialize GLFW, create a window and an OpenGL context
def init_glfw_window(width, height, title):
    if not glfw.init():
        raise Exception("GLFW can't be initialized")

    # Create a GLFW window
    window = glfw.create_window(width, height, title, None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFW window creation failed")

    # Set the current OpenGL context
    glfw.make_context_current(window)

    # Enable vsync (1 = enable, 0 = disable)
    glfw.swap_interval(1)

    return window

# Function to compile shaders
def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        error = glGetShaderInfoLog(shader).decode()
        raise Exception(f"Shader compilation failed: {error}")

    return shader

# Function to create and link shaders into a program
def create_shader_program(vertex_code, fragment_code):
    # Compile the shaders
    vertex_shader = compile_shader(vertex_code, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_code, GL_FRAGMENT_SHADER)

    # Create a program and attach shaders
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    # Check if the linking was successful
    if not glGetProgramiv(program, GL_LINK_STATUS):
        error = glGetProgramInfoLog(program).decode()
        raise Exception(f"Program linking failed: {error}")

    return program

# Function to render a simple triangle
def render_triangle():
    # Vertex data for a triangle (x, y, r, g, b)
    vertices = np.array([
        -0.5, -0.5, 0.0, 1.0, 0.0, 1.0,  # Bottom-left vertex (red)
         0.5, -0.5, 1.0, 0.0, 1.0, 1.0,  # Bottom-right vertex (green)
         0.0,  0.5, 0.0, 1.0, 0.0, 1.0   # Top vertex (blue)
    ], dtype=np.float32)

    # Create a Vertex Buffer Object (VBO)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Specify the layout of the vertex data
    position = glGetAttribLocation(shader_program, "position")
    glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 6 * vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(position)

    color = glGetAttribLocation(shader_program, "color")
    glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 6 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
    glEnableVertexAttribArray(color)

    # Use the shader program and draw the triangle
    glUseProgram(shader_program)
    glDrawArrays(GL_TRIANGLES, 0, 3)


def draw_line(x1: int, x2: int, y1: int, y2: int, color: tuple[int, int, int, int]) -> None:
    """
    Draw a line between (x1, y1) and (x2, y2) with the specified color.

    :param x1: x-coordinate of the first point
    :param y1: y-coordinate of the first point
    :param x2: x-coordinate of the second point
    :param y2: y-coordinate of the second point
    :param color: Color of the line (RGBA)
    """
    vertices: np.ndarray = np.array([
        x1 / 400.0 - 1.0, y1 / 300.0 - 1.0, color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0,
        x2 / 400.0 - 1.0, y2 / 300.0 - 1.0, color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0
    ], dtype=np.float32)

    # Create a Vertex Buffer Object (VBO)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Specify the layout of the vertex data
    position = glGetAttribLocation(shader_program, "position")
    glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 6 * vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(position)

    color_location = glGetAttribLocation(shader_program, "color")
    glVertexAttribPointer(color_location, 4, GL_FLOAT, GL_FALSE, 6 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
    glEnableVertexAttribArray(color_location)

    # Use the shader program and draw the line
    glUseProgram(shader_program)
    glDrawArrays(GL_LINES, 0, 2)

    glBindBuffer(GL_ARRAY_BUFFER, 0)


# Define vertex and fragment shaders
vertex_shader_code = """
#version 330
in vec2 position;
in vec4 color;  // Change this to vec4 to pass RGBA
out vec4 newColor;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    newColor = color;
}
"""

fragment_shader_code = """
#version 330
in vec4 newColor;  // Updated to handle alpha as well
out vec4 outColor;
void main() {
    outColor = newColor;  // Now we pass RGBA
}
"""

# Main code
if __name__ == "__main__":
    # Initialize GLFW window
    window = init_glfw_window(800, 600, "OpenGL Window with GLFW")

    # Compile shaders and create a shader program
    shader_program = create_shader_program(vertex_shader_code, fragment_shader_code)

    # Main render loop
    while not glfw.window_should_close(window):
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT)

        # Render the triangle
        render_triangle()

        #
        draw_line(10, 40, 10, 0, (150, 0, 50, 255))

        # Swap buffers
        glfw.swap_buffers(window)

        # Poll for events
        glfw.poll_events()

    # Clean up and terminate
    glfw.terminate()
