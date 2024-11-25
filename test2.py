import sys
import sdl2
import sdl2.ext
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from typing import Tuple

# Utility function to initialize OpenGL
def init_opengl(width: int, height: int) -> None:
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width, height, 0.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0.1, 0.1, 0.1, 1.0)

# Function to draw a filled rectangle
def draw_filled_rect(x: int, y: int, w: int, h: int, color: Tuple[float, float, float]) -> None:
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

# Function to handle main window with button
def main_window() -> None:
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

    window: sdl2.SDL_Window = sdl2.SDL_CreateWindow(b"Main Window", sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
                                   800, 600, sdl2.SDL_WINDOW_OPENGL)
    win_ctx = sdl2.SDL_GL_CreateContext(window)
    init_opengl(800, 600)

    running: bool = True
    button_rect: Tuple[int, int, int, int] = (300, 250, 200, 100)  # x, y, width, height
    button_color: Tuple[float, float, float] = (0.2, 0.6, 0.8)  # RGB color

    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x: int = event.button.x
                y: int = event.button.y
                if (button_rect[0] <= x <= button_rect[0] + button_rect[2] and
                        button_rect[1] <= y <= button_rect[1] + button_rect[3]):
                    create_popup()  # Create pop-up window when button is clicked


        sdl2.SDL_GL_MakeCurrent(window, win_ctx)
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw button
        draw_filled_rect(*button_rect, button_color)

        sdl2.SDL_GL_SwapWindow(window)

    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    sys.exit(0)

# Function to create a pop-up window with an OK button
def create_popup() -> None:
    popup_window: sdl2.SDL_Window = sdl2.SDL_CreateWindow(b"Popup Window", sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
                                         300, 200, sdl2.SDL_WINDOW_OPENGL)
    pop_context = sdl2.SDL_GL_CreateContext(popup_window)
    init_opengl(300, 200)

    ok_button_rect: Tuple[int, int, int, int] = (100, 75, 100, 50)  # x, y, width, height
    ok_button_color: Tuple[float, float, float] = (0.8, 0.2, 0.2)  # RGB color

    running: bool = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                x: int = event.button.x
                y: int = event.button.y
                if (ok_button_rect[0] <= x <= ok_button_rect[0] + ok_button_rect[2] and
                        ok_button_rect[1] <= y <= ok_button_rect[1] + ok_button_rect[3]):
                    running = False  # Close the pop-up when the OK button is clicked


        sdl2.SDL_GL_MakeCurrent(popup_window, pop_context)
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw OK button
        draw_filled_rect(*ok_button_rect, ok_button_color)

        sdl2.SDL_GL_SwapWindow(popup_window)

    sdl2.SDL_DestroyWindow(popup_window)

if __name__ == "__main__":
    main_window()
