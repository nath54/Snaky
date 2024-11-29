import sys
import sdl2
import sdl2.ext
import time

# Constants for the grid and animation
TILE_SIZE = 32  # Size of each tile in the atlas
ANIMATION_FRAMES = [(0, 1), (1, 1), (2, 1)]  # Tile positions in (x, y)
FRAME_DELAY = 200  # Milliseconds between frames

def run():
    # Initialize SDL2
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(f"SDL_Init Error: {sdl2.SDL_GetError().decode()}")
        return -1

    # Create a window
    window = sdl2.SDL_CreateWindow(
        b"PySDL2 Texture Atlas Animation",
        sdl2.SDL_WINDOWPOS_CENTERED,
        sdl2.SDL_WINDOWPOS_CENTERED,
        800, 600,
        sdl2.SDL_WINDOW_SHOWN
    )
    if not window:
        print(f"SDL_CreateWindow Error: {sdl2.SDL_GetError().decode()}")
        sdl2.SDL_Quit()
        return -1

    # Create a renderer
    renderer = sdl2.SDL_CreateRenderer(window, -1, sdl2.SDL_RENDERER_ACCELERATED)
    if not renderer:
        print(f"SDL_CreateRenderer Error: {sdl2.SDL_GetError().decode()}")
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
        return -1

    # Load the texture atlas
    img_path = b"res/sprites/snakes_sprites.png"  # Update this to your texture atlas file
    surface = sdl2.sdlimage.IMG_Load(img_path)
    if not surface:
        print(f"sdlimage.Load_IMG Error: {sdl2.SDL_GetError().decode()}")
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
        return -1

    # Create a texture from the surface
    texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
    sdl2.SDL_FreeSurface(surface)
    if not texture:
        print(f"SDL_CreateTextureFromSurface Error: {sdl2.SDL_GetError().decode()}")
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
        return -1

    # Main loop
    running = True
    event = sdl2.SDL_Event()
    frame_index = 0  # Current frame index for the animation
    last_time = sdl2.SDL_GetTicks()

    while running:
        # Handle events
        while sdl2.SDL_PollEvent(event) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False

        # Get the current time
        current_time = sdl2.SDL_GetTicks()
        if current_time - last_time > FRAME_DELAY:
            # Advance to the next frame
            frame_index = (frame_index + 1) % len(ANIMATION_FRAMES)
            last_time = current_time

        # Get the current frame's tile position
        tile_x, tile_y = ANIMATION_FRAMES[frame_index]

        # Define the source rectangle (crop from the atlas)
        src_rect = sdl2.SDL_Rect(
            tile_x * TILE_SIZE,  # x-coordinate in the atlas
            tile_y * TILE_SIZE,  # y-coordinate in the atlas
            TILE_SIZE,           # Width of the tile
            TILE_SIZE            # Height of the tile
        )

        # Define the destination rectangle (where to draw on the screen)
        dest_rect = sdl2.SDL_Rect(
            384, 284,  # Center of a 800x600 window
            TILE_SIZE, TILE_SIZE
        )

        # Clear the renderer
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        # Copy the current frame from the atlas to the screen
        sdl2.SDL_RenderCopy(renderer, texture, src_rect, dest_rect)

        # Present the renderer
        sdl2.SDL_RenderPresent(renderer)

        # Limit CPU usage
        sdl2.SDL_Delay(10)

    # Clean up
    sdl2.SDL_DestroyTexture(texture)
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0

if __name__ == "__main__":
    sys.exit(run())
