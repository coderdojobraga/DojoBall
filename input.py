class Input:
    def __init__(self) -> None:
        self.up: bool = False
        self.down: bool = False
        self.left: bool = False
        self.right: bool = False
        self.kick: bool = False

    def __repr__(self) -> str:
        return f"Input(up={self.up}, down={self.down}, left={self.left}, right={self.right}, kick={self.kick})"
