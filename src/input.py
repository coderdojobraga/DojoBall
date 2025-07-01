class Input:
    def __init__(self, up: bool = False, down: bool = False, left: bool = False, right: bool = False, kick: bool = False, window_width: int = 1920, window_height: int = 1080) -> None:
        self.up: bool = up
        self.down: bool = down
        self.left: bool = left
        self.right: bool = right
        self.kick: bool = kick
        self.window_width: int = window_width
        self.window_height: int = window_height
