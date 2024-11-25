
from lib_nadisplay_colors import ND_Color
from lib_nadisplay_rects import ND_Point
import lib_nadisplay as nd


class Snake:
    #
    def __init__(self, pseudo: str, init_position: ND_Point, color: ND_Color, init_direction: ND_Point = ND_Point(1, 0), init_size: int = 4) -> None:
        #
        self.color: ND_Color = color
        self.hidding_size: int = init_size  # Taille cachée qu'il faut ajouter au snake quand il avance
        self.direction: ND_Point = init_direction  # A ajouter à la position de la tête
        #
        self.cases: list[ND_Point] = []  # La tête est le premier élément de la liste
        self.cases_angles: list[int] = []
        #
        self.last_update: float = 0
        self.last_applied_direction: ND_Point = init_direction
        #
        self.score: int = 0
        #
        self.pseudo: str = pseudo
        #
        self.sprites: dict[str, tuple[nd.ND_AnimatedSprite | nd.ND_Sprite_of_AtlasTexture, int]] = {}

