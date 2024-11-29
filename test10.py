import sys
import sdl2
import sdl2.ext

def run():
    # Initialize SDL2
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(f"SDL_Init Error: {sdl2.SDL_GetError().decode()}")
        return -1

    # Create a window
    window = sdl2.SDL_CreateWindow(
        b"PySDL2 Image Loader",
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

    # Load an image using SDL2_image
    img_path = b"res/sprites/apple1.png"  # Update this with the path to your image
    surface = sdl2.sdlimage.IMG_Load(img_path)
    if not surface:
        print(f"SDL_LoadBMP Error: {sdl2.SDL_GetError().decode()}")
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
    while running:
        while sdl2.SDL_PollEvent(event) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False

        # Clear the renderer
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        # Copy the texture to the renderer
        sdl2.SDL_RenderCopy(renderer, texture, None, sdl2.SDL_Rect(0, 0, 32, 32))

        # Present the renderer
        sdl2.SDL_RenderPresent(renderer)

    # Clean up
    sdl2.SDL_DestroyTexture(texture)
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0

if __name__ == "__main__":
    sys.exit(run())
