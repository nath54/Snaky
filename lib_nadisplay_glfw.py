
from typing import Optional
from lib_nadisplay_rects import ND_Point
import lib_nadisplay_events as nd_event
from lib_nadisplay import ND_EventsManager
import glfw  # type: ignore



#
def get_display_info() -> Optional[glfw._GLFWvidmode]:
    # Initialize GLFW
    if not glfw.init():
        return None

    # Get the primary monitor
    monitor = glfw.get_primary_monitor()
    if not monitor:
        glfw.terminate()
        return None

    # Get video mode of the primary monitor
    video_mode = glfw.get_video_mode(monitor)
    if not video_mode:
        glfw.terminate()
        return None

    return video_mode





#
class ND_EventsManager_GLFW(ND_EventsManager):
    #
    def __init__(self) -> None:
        self.key_pressed: set[int | str] = set()
        self.events_waiting_too_poll: list[nd_event.ND_Event] = []

    #
    def poll_next_event(self) -> Optional[nd_event.ND_Event]:
        return None

    #
    def get_mouse_position(self) -> ND_Point:
        # TODO
        return ND_Point(0, 0)

    #
    def get_global_mouse_position(self) -> ND_Point:
        # TODO
        return ND_Point(0, 0)

