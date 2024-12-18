
from dataclasses import dataclass


@dataclass
class ND_Event:
    blocked: bool = False


@dataclass
class ND_EventQuit(ND_Event):
    pass


@dataclass
class ND_EventKeyboard(ND_Event):
    keyboard_id: int = 0
    key: str = ""


@dataclass
class ND_EventKeyDown(ND_EventKeyboard):
    pass


@dataclass
class ND_EventKeyUp(ND_EventKeyboard):
    pass


@dataclass
class ND_EventMouse(ND_Event):
    mouse_id: int = 0
    x: int = 0
    y: int = 0


@dataclass
class ND_EventMouseButtonDown(ND_EventMouse):
    button_id: int = 0


@dataclass
class ND_EventMouseButtonUp(ND_EventMouse):
    button_id: int = 0


@dataclass
class ND_EventMouseMotion(ND_EventMouse):
    rel_x: int = 0
    rel_y: int = 0


@dataclass
class ND_EventMouseWheelScrolled(ND_EventMouse):
    scroll_x: int = 0
    scroll_y: int = 0


@dataclass
class ND_EventWindow(ND_Event):
    window_id: int = 0


@dataclass
class ND_EventWindowMoved(ND_EventWindow):
    x: int = 0
    y: int = 0


@dataclass
class ND_EventWindowResized(ND_EventWindow):
    w: int = 0
    h: int = 0


@dataclass
class ND_EventWindowHidden(ND_EventWindow):
    pass


@dataclass
class ND_EventWindowShown(ND_EventWindow):
    pass


@dataclass
class ND_EventWindowFocusGained(ND_EventWindow):
    pass


@dataclass
class ND_EventWindowFocusLost(ND_EventWindow):
    pass


@dataclass
class ND_EventWindowClose(ND_EventWindow):
    pass


@dataclass
class ND_EmptyEvent(ND_Event):
    pass
