import sdl2  # type: ignore
import sdl2.ext  # type: ignore
import sdl2.sdlttf as sdlttf  # type: ignore
import sdl2.sdlimage as sdlimage  # type: ignore
import sdl2.sdlgfx as sdlgfx  # type: ignore
import vulkan as vk  # type: ignore
from PIL import Image
import ctypes

# Initialize SDL2 and TTF
sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
sdlttf.TTF_Init()

# Create two windows
window1 = sdl2.SDL_CreateWindow(b"Window 1", sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED, 640, 480, sdl2.SDL_WINDOW_VULKAN)
window2 = sdl2.SDL_CreateWindow(b"Window 2", sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED, 640, 480, sdl2.SDL_WINDOW_VULKAN)

# Initialize Vulkan (for future Vulkan handling)
# Here you would normally create a Vulkan instance, physical device, etc.
# This is just a placeholder to indicate Vulkan setup.
def init_vulkan():
    app_info = vk.VkApplicationInfo(
        pApplicationName='SDL2-Vulkan Example',
        applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
        pEngineName='No Engine',
        engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
        apiVersion=vk.VK_API_VERSION_1_0,
    )
    create_info = vk.VkInstanceCreateInfo(
        pApplicationInfo=app_info,
    )
    instance = vk.vkCreateInstance(create_info, None)
    return instance

# Vulkan Initialization
vulkan_instance = init_vulkan()

# Load system font and custom font
system_font = sdlttf.TTF_OpenFont(b"/home/nathan/Downloads/lemon_milk/LEMONMILK-Regular.otf", 24)  # Provide path to a system font
custom_font = sdlttf.TTF_OpenFont(b"/home/nathan/Downloads/dragon_hunter/DRAGON HUNTER.otf", 24)  # Provide path to a custom font

# Create renderer for each window
renderer1 = sdl2.SDL_CreateRenderer(window1, -1, sdl2.SDL_RENDERER_ACCELERATED)
renderer2 = sdl2.SDL_CreateRenderer(window2, -1, sdl2.SDL_RENDERER_ACCELERATED)

# Load and render text with system font
def render_text(renderer, font, text, color, x, y):
    surface = sdlttf.TTF_RenderText_Blended(font, text.encode('utf-8'), color)
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    dst_rect = sdl2.SDL_Rect(x, y, surface.contents.w, surface.contents.h)
    sdl2.SDL_RenderCopy(renderer, texture, None, dst_rect)
    sdl2.SDL_FreeSurface(surface)
    sdl2.SDL_DestroyTexture(texture)

# Define text color (white)
white = sdl2.SDL_Color(255, 255, 255, 255)

# Render system font text in window 1
render_text(renderer1, system_font, "Hello, System Font!", white, 50, 50)
# Render custom font text in window 2
render_text(renderer2, custom_font, "Hello, Custom Font!", white, 50, 50)

# Load and display an image using Pillow and SDL2
def render_image(renderer, img_path, x, y, width, height):
    image_surface = sdlimage.IMG_Load(img_path.encode('utf-8'))
    if not image_surface:
        print(f"Failed to load image: {img_path}")
        return
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, image_surface)
    dst_rect = sdl2.SDL_Rect(x, y, width, height)
    sdl2.SDL_RenderCopy(renderer, texture, None, dst_rect)
    sdl2.SDL_FreeSurface(image_surface)
    sdl2.SDL_DestroyTexture(texture)

# Render an image
render_image(renderer1, "/home/nathan/Downloads/dragon_hunter/Preview Font Dragon Hunter.png", 100, 100, 200, 150)  # Specify the path to an image


def color_to_int(color):
    # Convert SDL_Color to 32-bit ARGB integer
    return (color.a << 24) | (color.r << 16) | (color.g << 8) | color.b

def draw_rounded_rect(renderer, x, y, width, height, radius, border_color, fill_color):
    # Convert SDL_Color to ARGB integer
    fill_color_int = color_to_int(fill_color)
    border_color_int = color_to_int(border_color)

    # Draw filled rounded rectangle
    sdlgfx.roundedBoxColor(renderer, x, y, x + width, y + height, radius, fill_color_int)
    # Draw border with rounded corners
    sdlgfx.roundedRectangleColor(renderer, x, y, x + width, y + height, radius, border_color_int)


# Define colors (ARGB format)
border_color = sdl2.SDL_Color(255, 0, 0, 255)  # Red border
fill_color = sdl2.SDL_Color(0, 255, 0, 255)    # Green fill

# Draw a rectangle with border and rounded corners
draw_rounded_rect(renderer1, 300, 300, 200, 100, 20, border_color, fill_color)

# Present the rendered content to both windows
sdl2.SDL_RenderPresent(renderer1)
sdl2.SDL_RenderPresent(renderer2)

# Event loop
running = True
event = sdl2.SDL_Event()
while running:

    sdl2.SDL_RenderPresent(renderer1)
    sdl2.SDL_RenderPresent(renderer2)

    while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
        if event.type == sdl2.SDL_QUIT:
            running = False
            break

# Cleanup
sdl2.SDL_DestroyRenderer(renderer1)
sdl2.SDL_DestroyRenderer(renderer2)
sdl2.SDL_DestroyWindow(window1)
sdl2.SDL_DestroyWindow(window2)
sdlttf.TTF_Quit()
sdl2.SDL_Quit()
