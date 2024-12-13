

import OpenGL.GL as gl  # type: ignore



#
def compile_gl_shader(source: str, shader_type: gl.GLenum | int) -> int:
    """
    Compile un shader à partir de son code source.

    :param source: Code source GLSL du shader
    :param shader_type: Type du shader (GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, etc.)
    :return: ID du shader compilé
    :raises RuntimeError: Si la compilation échoue
    """
    shader: int = gl.glCreateShader(shader_type)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)

    # Vérification d'erreurs
    if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
        error: bytes | str = gl.glGetShaderInfoLog(shader)
        if isinstance(error, bytes):
            error = error.decode('utf-8')
        raise RuntimeError(f"Shader compilation failed: {error}")

    return shader


#
def create_gl_shader_program(vertex_src: str, fragment_src: str) -> int:
    """
    Creates a shader program from vertex and fragment source code.
    Adds error handling for compilation and linking errors.
    """
    try:
        vertex_shader: int = compile_gl_shader(vertex_src, gl.GL_VERTEX_SHADER)
        fragment_shader: int = compile_gl_shader(fragment_src, gl.GL_FRAGMENT_SHADER)

        program: int = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)

        # Check for linking errors
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            error: bytes | str = gl.glGetProgramInfoLog(program)
            if isinstance(error, bytes):
                error = error.decode('utf-8')
            raise RuntimeError(f"Shader linking failed: {error}")

        # Delete shaders after linking
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)

        return program
    except RuntimeError as e:
        print(f"Error in shader program creation: {e}")
        return 0


def create_and_validate_gl_shader_program(vertex_shader_src: str, fragment_shader_src: str) -> int:

    shader_program: int = create_gl_shader_program(vertex_shader_src, fragment_shader_src)
    print(f"Shader program created: {shader_program}")

    # Check if shader program is valid
    if shader_program <= 0:
        print("Failed to create shader program!")
        return 0
    else:
        print(f"Shader program created successfully with ID: {shader_program}")

    gl.glValidateProgram(shader_program)
    if not gl.glGetProgramiv(shader_program, gl.GL_VALIDATE_STATUS):
        error: bytes | str = gl.glGetProgramInfoLog(shader_program)
        if isinstance(error, bytes):
            error = error.decode('utf-8')
        print(f"Shader program validation failed: {error}")
        #
        return 0

    #
    return shader_program




# def create_and_validate_gl_shader_program(vertex_shader_src: str, fragment_shader_src: str) -> int:
#     # Create vertex shader
#     vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
#     gl.glShaderSource(vertex_shader, vertex_shader_src)
#     gl.glCompileShader(vertex_shader)

#     # Check vertex shader compilation
#     if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
#         error = gl.glGetShaderInfoLog(vertex_shader)
#         if isinstance(error, bytes):
#             error = error.decode('utf-8')
#         print(f"Vertex shader compilation failed: {error}")
#         gl.glDeleteShader(vertex_shader)
#         return 0

#     # Create fragment shader
#     fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
#     gl.glShaderSource(fragment_shader, fragment_shader_src)
#     gl.glCompileShader(fragment_shader)

#     # Check fragment shader compilation
#     if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
#         error = gl.glGetShaderInfoLog(fragment_shader)
#         if isinstance(error, bytes):
#             error = error.decode('utf-8')
#         print(f"Fragment shader compilation failed: {error}")
#         gl.glDeleteShader(vertex_shader)
#         gl.glDeleteShader(fragment_shader)
#         return 0

#     # Create program and attach shaders
#     program = gl.glCreateProgram()
#     gl.glAttachShader(program, vertex_shader)
#     gl.glAttachShader(program, fragment_shader)

#     # Link program
#     gl.glLinkProgram(program)

#     # Check linking status
#     if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
#         error = gl.glGetProgramInfoLog(program)
#         if isinstance(error, bytes):
#             error = error.decode('utf-8')
#         print(f"Error in shader program linking: {error}")
#         gl.glDeleteShader(vertex_shader)
#         gl.glDeleteShader(fragment_shader)
#         gl.glDeleteProgram(program)
#         return 0

#     # Clean up individual shaders (they're now linked into the program)
#     gl.glDeleteShader(vertex_shader)
#     gl.glDeleteShader(fragment_shader)

#     # Validate program
#     gl.glValidateProgram(program)
#     if not gl.glGetProgramiv(program, gl.GL_VALIDATE_STATUS):
#         error = gl.glGetProgramInfoLog(program)
#         if isinstance(error, bytes):
#             error = error.decode('utf-8')
#         print(f"Shader program validation failed: {error}")
#         gl.glDeleteProgram(program)
#         return 0

#     return program

# def create_and_validate_gl_shader_program(vertex_shader_src: str, fragment_shader_src: str) -> int:
#     # Create vertex shader
#     vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
#     if not vertex_shader:
#         print("Failed to create vertex shader!")
#         return 0

#     # Convert source to bytes if it isn't already
#     if isinstance(vertex_shader_src, str):
#         vertex_shader_src = vertex_shader_src.encode('utf-8')

#     # Set source and compile
#     gl.glShaderSource(vertex_shader, vertex_shader_src)
#     gl.glCompileShader(vertex_shader)

#     # Check compilation
#     compile_status = gl.GLint(0)
#     gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS, ctypes.byref(compile_status))
#     if not compile_status:
#         # Get error message
#         log_length = gl.GLint(0)
#         gl.glGetShaderiv(vertex_shader, gl.GL_INFO_LOG_LENGTH, ctypes.byref(log_length))
#         log = (gl.GLchar * log_length.value)()
#         gl.glGetShaderInfoLog(vertex_shader, log_length, None, log)
#         print(f"Vertex shader compilation failed: {bytes(log).decode('utf-8')}")
#         gl.glDeleteShader(vertex_shader)
#         return 0

#     # Create fragment shader
#     fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
#     if not fragment_shader:
#         print("Failed to create fragment shader!")
#         gl.glDeleteShader(vertex_shader)
#         return 0

#     # Convert source to bytes if it isn't already
#     if isinstance(fragment_shader_src, str):
#         fragment_shader_src = fragment_shader_src.encode('utf-8')

#     # Set source and compile
#     gl.glShaderSource(fragment_shader, fragment_shader_src)
#     gl.glCompileShader(fragment_shader)

#     # Check compilation
#     gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS, ctypes.byref(compile_status))
#     if not compile_status:
#         # Get error message
#         log_length = gl.GLint(0)
#         gl.glGetShaderiv(fragment_shader, gl.GL_INFO_LOG_LENGTH, ctypes.byref(log_length))
#         log = (gl.GLchar * log_length.value)()
#         gl.glGetShaderInfoLog(fragment_shader, log_length, None, log)
#         print(f"Fragment shader compilation failed: {bytes(log).decode('utf-8')}")
#         gl.glDeleteShader(vertex_shader)
#         gl.glDeleteShader(fragment_shader)
#         return 0

#     # Create program
#     program = gl.glCreateProgram()
#     if not program:
#         print("Failed to create shader program!")
#         gl.glDeleteShader(vertex_shader)
#         gl.glDeleteShader(fragment_shader)
#         return 0

#     # Attach shaders and link
#     gl.glAttachShader(program, vertex_shader)
#     gl.glAttachShader(program, fragment_shader)
#     gl.glLinkProgram(program)

#     # Check linking
#     link_status = gl.GLint(0)
#     gl.glGetProgramiv(program, gl.GL_LINK_STATUS, ctypes.byref(link_status))
#     if not link_status:
#         # Get error message
#         log_length = gl.GLint(0)
#         gl.glGetProgramiv(program, gl.GL_INFO_LOG_LENGTH, ctypes.byref(log_length))
#         log = (gl.GLchar * log_length.value)()
#         gl.glGetProgramInfoLog(program, log_length, None, log)
#         print(f"Shader linking failed: {bytes(log).decode('utf-8')}")
#         gl.glDeleteShader(vertex_shader)
#         gl.glDeleteShader(fragment_shader)
#         gl.glDeleteProgram(program)
#         return 0

#     # Clean up shaders
#     gl.glDetachShader(program, vertex_shader)
#     gl.glDetachShader(program, fragment_shader)
#     gl.glDeleteShader(vertex_shader)
#     gl.glDeleteShader(fragment_shader)

#     return program


