
import numpy as np  # type:ignore



def get_rendering_buffer(xpos: float, ypos: float, w: float, h: float, zfix: float = 0.0) -> np.ndarray:
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


