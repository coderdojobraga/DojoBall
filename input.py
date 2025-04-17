class Input:
    def __init__(self, up: bool = False, down: bool = False, left: bool = False, right: bool = False, kick: bool = False) -> None:
        self.up: bool = up
        self.down: bool = down
        self.left: bool = left
        self.right: bool = right
        self.kick: bool = kick

    def __repr__(self) -> str:
        return f"Input(up={self.up}, down={self.down}, left={self.left}, right={self.right}, kick={self.kick})"
